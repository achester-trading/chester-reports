"""
Run snapshots — the memory layer that makes "What Changed Since Last Report"
possible.

The problem this solves: GitHub Actions runners are ephemeral. Each run checks
out the repo, fetches fresh data into the container, writes the report, and
then the container is destroyed. Nothing the run fetched survives. Without a
persisted snapshot there is no prior state to compare against, so the
"What Changed" lines can never be anything but placeholders.

The fix is deliberately small: after each run, write one compact JSON file
capturing the latest value of every configured series, and commit it. A
snapshot is a few KB, diffs cleanly in git, and accumulates into a genuine
month-over-month history without duplicating the CSV store.

Design notes:
- Snapshots are keyed by report date: snapshots/2026-08-25.json
- Comparison always uses the most recent snapshot STRICTLY BEFORE the current
  report date, so re-running on the same day compares to last month, not to
  the run you just did five minutes ago.
- Everything degrades quietly: no snapshots directory on the first run means
  "no prior snapshot" rather than a crash.
"""

from __future__ import annotations
import json
import logging
import os
import datetime as dt
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

SNAPSHOT_DIR = Path(os.environ.get("SNAPSHOT_DIR", "snapshots"))

# Percent-point metrics: report deltas in basis points rather than percent-of-percent.
# A move in HY OAS from 2.70% to 3.10% is "+40bp", not "+14.8%".
PCT_UNITS = {"%", "bp"}

# Below this relative move, treat a metric as unchanged rather than noise.
MATERIAL_REL = 0.005   # 0.5%
MATERIAL_BP = 5.0      # 5 basis points for percent-unit series


def _ensure_dir() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def write_snapshot(store, report_date: dt.date, specs) -> Path:
    """Capture the latest value of every series into snapshots/<date>.json."""
    _ensure_dir()
    payload = {
        "report_date": report_date.isoformat(),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "series": {},
    }
    for s in specs:
        latest = store.latest(s.key)
        if not latest:
            continue
        payload["series"][s.key] = {
            "value": latest["value"],
            "date": latest["date"],
            "units": s.units,
            "description": s.description,
            "pillar": s.pillar,
        }
    path = SNAPSHOT_DIR / f"{report_date.isoformat()}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    log.info("Wrote snapshot: %s (%d series)", path, len(payload["series"]))
    return path


def load_prior_snapshot(report_date: dt.date) -> Optional[dict]:
    """Most recent snapshot strictly before report_date, or None."""
    if not SNAPSHOT_DIR.exists():
        log.info("No snapshots directory — this is the first run with memory enabled")
        return None
    candidates = []
    for p in SNAPSHOT_DIR.glob("*.json"):
        try:
            d = dt.date.fromisoformat(p.stem)
        except ValueError:
            continue
        if d < report_date:
            candidates.append((d, p))
    if not candidates:
        log.info("No prior snapshot before %s", report_date)
        return None
    d, p = max(candidates)
    try:
        data = json.loads(p.read_text())
        log.info("Comparing against prior snapshot: %s", p.name)
        return data
    except Exception:
        log.exception("Prior snapshot %s unreadable; proceeding without comparison", p)
        return None


def _fmt_delta(key: str, cur: dict, prev: dict) -> Optional[str]:
    """Render one change line, or None if unchanged/immaterial/uncomparable."""
    cv, pv = cur.get("value"), prev.get("value")
    if cv is None or pv is None:
        return None
    try:
        cv, pv = float(cv), float(pv)
    except (TypeError, ValueError):
        return None

    units = cur.get("units", "")
    desc = cur.get("description", key)
    diff = cv - pv

    if units in PCT_UNITS:
        bp = diff * 100.0
        if abs(bp) < MATERIAL_BP:
            return None
        arrow = "▲" if bp > 0 else "▼"
        return f"- **{desc}**: {pv:.2f}% → {cv:.2f}% ({arrow} {abs(bp):.0f}bp)"

    if pv == 0:
        return None
    rel = diff / abs(pv)
    if abs(rel) < MATERIAL_REL:
        return None
    arrow = "▲" if diff > 0 else "▼"
    return f"- **{desc}**: {pv:,.2f} → {cv:,.2f} ({arrow} {abs(rel) * 100:.1f}%)"


def changes_for_pillar(pillar: str, current: dict, prior: Optional[dict],
                       limit: int = 6) -> list[str]:
    """Ranked 'what changed' lines for one pillar, largest move first."""
    if not prior:
        return ["- *No prior snapshot available — this is the baseline run.*"]

    cur_series = current.get("series", {})
    prev_series = prior.get("series", {})
    scored: list[tuple[float, str]] = []

    for key, cur in cur_series.items():
        if str(cur.get("pillar")) != str(pillar):
            continue
        prev = prev_series.get(key)
        if not prev:
            continue
        line = _fmt_delta(key, cur, prev)
        if not line:
            continue
        try:
            cv, pv = float(cur["value"]), float(prev["value"])
            magnitude = abs(cv - pv) * 100 if cur.get("units") in PCT_UNITS else \
                abs((cv - pv) / pv) if pv else 0.0
        except (TypeError, ValueError, ZeroDivisionError):
            magnitude = 0.0
        scored.append((magnitude, line))

    if not scored:
        return [f"- *No material moves this period (threshold: "
                f"{MATERIAL_BP:.0f}bp / {MATERIAL_REL * 100:.1f}%).*"]

    scored.sort(reverse=True, key=lambda x: x[0])
    lines = [line for _, line in scored[:limit]]
    if prior.get("report_date"):
        lines.append(f"- *Compared to {prior['report_date']}.*")
    return lines


def build_current(store, specs) -> dict:
    """In-memory snapshot of the current run, for comparison before writing."""
    series = {}
    for s in specs:
        latest = store.latest(s.key)
        if not latest:
            continue
        series[s.key] = {
            "value": latest["value"], "date": latest["date"],
            "units": s.units, "description": s.description, "pillar": s.pillar,
        }
    return {"series": series}

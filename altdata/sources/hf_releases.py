"""
The Hugging Face model-release watch: the count and dates of new public model
repositories per week for a declared list of organisations (rulings of 24 Oct
2026, D26; b59-trigger-sources). Report only.

    python -m altdata.sources.hf_releases daily [--dry-run]      # the basket's run
    python -m altdata.sources.hf_releases backfill [--dry-run]   # the operator's
    python -m altdata.sources.hf_releases show [--as-of D]

THE SOURCE (config/ai_release_watch.yaml carries the check of 24 Oct 2026): the
public API's model listing, keyless, within its stated limit of 500 requests per
300 seconds; robots.txt allows everything. One listing per organisation, newest
first by `createdAt`, paged by the Link header only as far back as the weeks it
recounts. A refused or failed request marks that organisation STALE with its
reason and the week's total is not written; nothing is filled.

COUNTS AND DATES ONLY. Each repository's id and creation date; never its weights,
card, files, likes or downloads.

THE KEYS:
  ai.model_releases_week        instrument = organisation; observed_at = the ISO
                                week's Monday (UTC); the repositories created in
                                that week. Complete weeks only, recounted for the
                                last `reread_weeks` (a new vintage where a count
                                moved: a repository made public late lands in an
                                older week)
  ai.model_releases_week_total  the same over every declared organisation
  ai.model_release_event        instrument = the repository id; observed_at = its
                                creation date; available_at = THE PULL THAT FIRST
                                SAW IT, never createdAt (a repository can be
                                created private and published later)

The backfill's weekly rows are reconstructed from createdAt (available the Monday
after the week, labelled), so the history before the first daily pull is not
point in time; the lines say so. Nothing here enters a composite or the
market-state object.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config" / "ai_release_watch.yaml"
ROSTER = "ai_releases"
ORG_KEY = "ai.model_releases_week"
TOTAL_KEY = "ai.model_releases_week_total"
EVENT_KEY = "ai.model_release_event"
ROSTER_KEYS = [ORG_KEY, TOTAL_KEY]
SOURCE = "huggingface"
TITLE = "Factor I-b: open model releases (Hugging Face)"
_NEXT = re.compile(r'<([^>]+)>\s*;\s*rel="next"')


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


def monday(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def last_complete_week(today: dt.date) -> dt.date:
    """The Monday of the newest ISO week that has ended (UTC)."""
    return monday(today) - dt.timedelta(days=7)


def created_day(repo: dict) -> Optional[str]:
    s = str(repo.get("createdAt") or "")[:10]
    try:
        return dt.date.fromisoformat(s).isoformat()
    except ValueError:
        return None


def weekly_counts(days: list[str], weeks: list[str]) -> dict[str, int]:
    """{Monday: repositories created that week} for the given Mondays, zeros kept."""
    out = {w: 0 for w in weeks}
    for d in days:
        w = monday(dt.date.fromisoformat(d)).isoformat()
        if w in out:
            out[w] += 1
    return out


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------
def _get(url: str, params: Optional[dict] = None) -> tuple[Any, dict]:
    from ._base import http_get_response                        # noqa: PLC0415
    body, headers = http_get_response(url, params=params, timeout=60)
    return json.loads(body), headers


def list_org(org: str, cfg: dict, fetch: Callable = None, sleep: Callable = time.sleep,
             stop_before: Optional[str] = None) -> list[dict]:
    """The organisation's repositories, newest first: [{id, created}]. Paged by the
    Link header until a page reaches a creation day before `stop_before` (or the
    listing ends)."""
    fetch = fetch or _get
    url: Optional[str] = cfg["api"]
    params: Optional[dict] = {"author": org, "sort": "createdAt", "direction": -1,
                              "limit": int(cfg.get("page_size") or 100)}
    out: list[dict] = []
    while url:
        page, headers = fetch(url, params)
        for r in page or []:
            d = created_day(r)
            if d and str(r.get("id") or "").split("/", 1)[0] == org:
                out.append({"id": str(r["id"]), "created": d})
        m = _NEXT.search(str((headers or {}).get("link") or ""))
        last = created_day(page[-1]) if page else None
        if not m or (stop_before and last and last < stop_before):
            break
        url, params = m.group(1), None
        sleep(float(cfg.get("pause_seconds") or 0.5))
    return out


# ---------------------------------------------------------------------------
# The rows
# ---------------------------------------------------------------------------
def _row(key: str, inst: Optional[str], day: str, at: str, value: Any,
         kind: str = "ingest_instant") -> dict:
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": at, "value": value, "source": SOURCE,
            "availability_kind": kind}


def _stored_counts(st, key: str, inst: Optional[str], cutoff: str) -> dict[str, float]:
    return {str(r["observed_at"])[:10]: float(r["value_num"])
            for r in st.as_of(key, cutoff, inst) if r.get("value_num") is not None}


def daily(dry_run: bool = False, today: Optional[str] = None, cfg: Optional[dict] = None,
          fetch: Callable = None, sleep: Callable = time.sleep, db=None,
          record: bool = True) -> dict:
    """A step of the crypto basket's 17:25 run (no new timer)."""
    from .. import observations, session                        # noqa: PLC0415
    cfg = cfg or config()
    day = dt.date.fromisoformat((today or dt.datetime.now(dt.timezone.utc).date()
                                 .isoformat())[:10])
    last = last_complete_week(day)
    weeks = [(last - dt.timedelta(days=7 * i)).isoformat()
             for i in range(int(cfg.get("reread_weeks") or 4))][::-1]
    out: dict[str, Any] = {"step": "daily", "dry_run": dry_run, "failed": {},
                           "weeks": [weeks[0], weeks[-1]]}
    own = db is None and not dry_run
    st = db or (observations.open_writer(__name__) if not dry_run else None)
    try:
        at = session.utc_iso(timespec="microseconds")
        seen = set(st.instruments(EVENT_KEY)) if st is not None else set()
        rows: list[dict] = []
        total = {w: 0 for w in weeks}
        new_events = []
        for i, o in enumerate(cfg["organisations"]):
            if i:
                sleep(float(cfg.get("pause_seconds") or 0.5))
            try:
                repos = list_org(o["id"], cfg, fetch, sleep, stop_before=weeks[0])
            except Exception as exc:                            # noqa: BLE001
                out["failed"][o["id"]] = (f"STALE: huggingface {o['id']}: "
                                          f"{type(exc).__name__}: {str(exc)[:100]}")
                continue
            counts = weekly_counts([r["created"] for r in repos], weeks)
            known = _stored_counts(st, ORG_KEY, o["id"], at) if st is not None else {}
            rows += [_row(ORG_KEY, o["id"], w, at, n) for w, n in counts.items()
                     if known.get(w) != float(n)]
            for w, n in counts.items():
                total[w] += n
            for r in repos:
                if r["id"] not in seen and r["created"] >= weeks[0]:
                    new_events.append(r)
                    rows.append(_row(EVENT_KEY, r["id"], r["created"], at,
                                     json.dumps({"org": o["id"], "created": r["created"],
                                                 "first_seen": at}, sort_keys=True)))
        if out["failed"]:
            out["total"] = ("not written: " + "; ".join(sorted(out["failed"])) +
                            " not read")
        else:
            known = _stored_counts(st, TOTAL_KEY, None, at) if st is not None else {}
            rows += [_row(TOTAL_KEY, None, w, at, n) for w, n in total.items()
                     if known.get(w) != float(n)]
            out["total"] = total
        out["new_events"] = [f"{r['id']} ({r['created']})" for r in new_events][:20]
        out["rows"] = len(rows)
        if dry_run:
            return out
        out["written"] = st.write_many(rows) if rows else 0
    finally:
        if own and st is not None:
            st.close()
    if record:
        from .. import feeds                                    # noqa: PLC0415
        failed = ({TOTAL_KEY: out["total"]} if out["failed"] else None)
        feeds.record_attempted(ROSTER, ROSTER_KEYS, merge=True, failed=failed)
    return out


def backfill(dry_run: bool = False, today: Optional[str] = None, cfg: Optional[dict] = None,
             fetch: Callable = None, sleep: Callable = time.sleep, db=None) -> dict:
    """The operator's, once: every organisation's whole listing, weekly counts from
    its first repository to the last complete week, RECONSTRUCTED from createdAt
    (available the Monday after the week); each repository an event first seen now."""
    from .. import observations, session                        # noqa: PLC0415
    cfg = cfg or config()
    day = dt.date.fromisoformat((today or dt.datetime.now(dt.timezone.utc).date()
                                 .isoformat())[:10])
    last = last_complete_week(day)
    at = session.utc_iso(timespec="microseconds")
    by_org: dict[str, list[dict]] = {}
    out: dict[str, Any] = {"step": "backfill", "dry_run": dry_run, "failed": {}}
    for i, o in enumerate(cfg["organisations"]):
        if i:
            sleep(float(cfg.get("pause_seconds") or 0.5))
        try:
            by_org[o["id"]] = list_org(o["id"], cfg, fetch, sleep)
        except Exception as exc:                                # noqa: BLE001
            out["failed"][o["id"]] = f"{type(exc).__name__}: {str(exc)[:100]}"
    firsts = [min(r["created"] for r in rs) for rs in by_org.values() if rs]
    rows: list[dict] = []
    if firsts:
        start = monday(dt.date.fromisoformat(min(firsts)))
        weeks, w = [], start
        while w <= last:
            weeks.append(w.isoformat())
            w += dt.timedelta(days=7)

        def week_at(wk: str) -> str:
            nxt = dt.date.fromisoformat(wk) + dt.timedelta(days=7)
            return observations.canonical_instant(dt.datetime.combine(
                nxt, dt.time(12, 0), tzinfo=dt.timezone.utc).isoformat())
        total = {w: 0 for w in weeks}
        for org, rs in by_org.items():
            first = monday(dt.date.fromisoformat(min(r["created"] for r in rs))).isoformat() \
                if rs else None
            counts = weekly_counts([r["created"] for r in rs], weeks)
            for wk, n in counts.items():
                total[wk] += n
                if first and wk >= first:
                    rows.append(_row(ORG_KEY, org, wk, week_at(wk), n, "reconstructed"))
            rows += [_row(EVENT_KEY, r["id"], r["created"], at,
                          json.dumps({"org": org, "created": r["created"],
                                      "first_seen": at}, sort_keys=True)) for r in rs]
        if not out["failed"]:
            rows += [_row(TOTAL_KEY, None, wk, week_at(wk), n, "reconstructed")
                     for wk, n in total.items()]
        out["weeks"] = [weeks[0], weeks[-1]] if weeks else []
    out["repositories"] = {o: len(rs) for o, rs in by_org.items()}
    out["rows"] = len(rows)
    if dry_run:
        return out
    own = db is None
    st = db or observations.open_writer(__name__)
    try:
        out["written"] = st.write_many(rows)
    finally:
        if own:
            st.close()
    return out


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------
def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    cfg = cfg or config()
    tot = rt._pts(st, TOTAL_KEY, cutoff)                        # noqa: SLF001
    out: dict[str, Any] = {"as_of": cutoff, "orgs": [], "events": []}
    if not tot:
        out["state"] = "absent"
        return out
    kinds = {str(r["observed_at"])[:10]: r.get("availability_kind")
             for r in st.as_of(TOTAL_KEY, cutoff)}
    live = sorted(d for d, k in kinds.items() if k != "reconstructed")
    out.update(state="computed", week=tot[-1][0], count=int(tot[-1][1]),
               mean4=round(sum(v for _, v in tot[-5:-1]) / max(1, len(tot[-5:-1])), 1),
               lens=rt.lens(tot, int(cfg.get("lens_years") or 2)), first=tot[0][0],
               live_from=live[0] if live else None)
    for o in cfg["organisations"]:
        p = rt._pts(st, ORG_KEY, cutoff, o["id"])               # noqa: SLF001
        out["orgs"].append({"id": o["id"], "group": o["group"],
                            "week": int(p[-1][1]) if p and p[-1][0] == out["week"] else None,
                            "four": int(sum(v for _, v in p[-4:])) if p else None})
    out["events"] = recent_events(st, cutoff, out["week"])
    return out


def recent_events(st, cutoff: str, week: str) -> list[tuple[str, str]]:
    """[(creation day, repository id)] created since the Monday before `week` and
    first seen by `cutoff`, newest first: one query across the event key's
    instruments (as_of() reads one instrument at a time)."""
    from .. import observations                                 # noqa: PLC0415
    lo = (dt.date.fromisoformat(week) - dt.timedelta(days=7)).isoformat()
    cur = st.conn.execute(
        "SELECT instrument, MIN(substr(observed_at, 1, 10)) FROM observations "
        " WHERE registry_key = ? AND observed_at >= ? AND available_at <= ? "
        "   AND instrument IS NOT NULL GROUP BY instrument",
        (EVENT_KEY, lo, observations.canonical_instant(cutoff)))
    return sorted(((str(d), str(i)) for i, d in cur.fetchall()), reverse=True)


def weekly_line(r: dict) -> str:
    """The Weekly's AI line in the narratives section."""
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    if r.get("state") != "computed":
        return ("Open model releases (Hugging Face): not read (ai.model_releases_week_total; "
                "the first pull has not run).")
    newest = ", ".join(f"{i} ({d})" for d, i in r["events"][:3])
    return (f"Open model releases (Hugging Face, {len(r['orgs'])} organisations): "
            f"{r['count']} new public repositories in the week of {r['week']} (the four "
            f"weeks before averaged {r['mean4']:.1f}; {rt.lens_text(r['lens'])})"
            + (f"; the newest: {newest}" if newest else "") + ". Report only.")


def factor_block(r: dict) -> dict:
    """The Monthly's Factor I-b block: one row per organisation and the line."""
    sub: dict[str, Any] = {"title": TITLE, "paragraph_wanted": False}
    if r.get("state") != "computed":
        sub["lines"] = [weekly_line(r)]
        return sub
    sub["table"] = {"columns": ["Organisation", "Group", f"Week of {r['week']}",
                                "Last four weeks"],
                    "rows": [[o["id"], o["group"], "—" if o["week"] is None else o["week"],
                              "—" if o["four"] is None else o["four"]] for o in r["orgs"]]}
    hist = (f"Weekly history from {r['first']}; reconstructed from creation dates before "
            f"{r['live_from'] or 'the first daily pull'}, point in time after.")
    sub["lines"] = [weekly_line(r), hist,
                    "Each release is a dated event in the AI thread (Factor I-b): counts "
                    "and dates only, no composite, no market-state input (D26)."]
    return sub


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415

    from .. import observations, session                        # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.hf_releases")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("daily", "backfill"):
        p = sub.add_parser(name)
        p.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "daily":
        print(json.dumps(daily(dry_run=a.dry_run), indent=1, default=str))
        return 0
    if a.cmd == "backfill":
        print(json.dumps(backfill(dry_run=a.dry_run), indent=1, default=str))
        return 0
    with observations.ObservationStore() as st:
        r = read(st, a.as_of or session.utc_iso())
    b = factor_block(r)
    for ln in b["lines"]:
        print(ln)
    for row in (b.get("table") or {}).get("rows") or []:
        print("  " + " | ".join(str(x) for x in row))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

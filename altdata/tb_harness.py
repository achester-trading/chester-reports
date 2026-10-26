"""
The Top & Bottom calibration harness, its core (6i-2; A77, 26 Oct 2026).

    python -m altdata.tb_harness show   [--db PATH] [--date D]
    python -m altdata.tb_harness ledger [--db PATH] [--edition laptop|box]
                                        [--out-dir DIR] [--dry-run]

The brief (docs/briefs/6i-spec-draft-2026-10-25.md, section 2), ruled 25 Oct 2026
with its decisions as recommended: the 3 Sep thirteen as the base, the extended
set flagged beside it (decision 2), no composite stored (decision 3), and the
credit leg on both proxies (decision 6) -- HY OAS where the store holds it, and
before that "pending 6i-3: Baa less the 10-year", the series 6i-3 adds.

WHAT IT COMPUTES. config/tb_episodes.yaml holds the episodes, the inputs and the
three overlays of the architecture's Part 23 (Concentration & Complacency, HY
Spread Acceleration, Liquidity & Funding Stress), each firing at three or more
of its triggers. For every episode and each of its decision dates the harness
reads each trigger's input AS OF that date's close and states the overlay:

  FIRES    at least `fires_at` triggers fire
  CLEAR    too few could fire even if every unread trigger did
  UNREAD   neither: enough triggers are unread that the overlay might fire
  NOT EXISTENT  fewer triggers existed at the date than it needs to fire

A trigger reads one of: its value and whether it fires; "not existent" (the date
is before the series exists -- never back-filled from a later series); "not
stored as of D" (the series existed and the store holds nothing knowable then);
or the input's pending text. A top is called when an overlay FIRES at its date; a
control is refused when none FIRES at either of its dates; a bottom is not scored
(the overlays are top-side, and the composite that scored bottoms is not stored).

POINT IN TIME. The store's available_at decides what was knowable: FRED rows carry
ALFRED's first vintage where AUD-3d's backfill wrote them, a price its close.
Shiller's workbook has no vintages, so its months are read from the current file
and lagged by the config's `shiller_lag_months` (session-set; the ledger says so).

WHAT IT NEVER DOES. It opens the store read-only (mode=ro) and writes nothing to
it; it stores no composite and registers no key; it calls no model and fetches
nothing. Its one output is the dated ledger and its episodes CSV, which a re-run
never overwrites (a new date is a new edition). Report-only: nothing enters a
composite, the market-state object, a dial, a band or a packet.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import sqlite3
import sys
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "tb_episodes.yaml"
LEDGER_DIR = REPO / "docs" / "ledgers"
ET = ZoneInfo("America/New_York")

NOT_EXISTENT = "not existent"
FIRES, CLEAR, UNREAD = "FIRES", "CLEAR", "UNREAD"
# An overlay too few of whose triggers existed at the date to reach `fires_at`:
# it could not have fired, and is not scored (Base Rates, chapter 12).
OVERLAY_NOT_EXISTENT = "NOT EXISTENT"
# The 3 Sep record (the architecture's Part 23), the composite's with the
# original weights. The ledger's first question is whether the harness
# reproduces it.
RECORD = {"top": (0, 3), "bottom": (4, 6), "control": (4, 4)}


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8"))


def rule_hash(cfg: dict) -> str:
    """The SHA-256 of the pre-registered pass rule's text, as the ledger prints it."""
    return hashlib.sha256(" ".join(str(cfg["pass_rule"]).split()).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# The store, read-only
# ---------------------------------------------------------------------------
class Reader:
    """The observation store's canonical as-of join over a read-only connection."""

    def __init__(self, path: Optional[str] = None) -> None:
        from altdata import observations                       # noqa: PLC0415
        self._obs = observations
        self.path = Path(path or observations.DEFAULT_DB)
        if not self.path.exists():
            raise FileNotFoundError(str(self.path))
        self.conn = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def as_of(self, key: str, as_of: Optional[str] = None, instrument: Optional[str] = None,
              observed_from: Optional[str] = None) -> list[dict]:
        o = self._obs
        cutoff = o.canonical_instant(as_of or dt.datetime.now(dt.timezone.utc).isoformat())
        args = {"key": key, "instrument": instrument, "as_of": cutoff}
        if observed_from:
            args["observed_from"] = str(observed_from)
        sql = o.AS_OF_FROM_SQL if observed_from else o.AS_OF_SQL
        return o.prefer_tier([dict(r) for r in self.conn.execute(sql, args).fetchall()], key)

    def close(self) -> None:
        self.conn.close()


def cutoff(day: str, cfg: dict) -> str:
    """The instant a decision date's close is knowable: the configured ET time."""
    h, m = (int(x) for x in str(cfg["point_in_time"]["cutoff_time_et"]).split(":"))
    t = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m, 59, 999999), ET)
    return t.astimezone(dt.timezone.utc).isoformat()


def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(str(s)[:10])


def _add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    return dt.date(d.year + y, m + 1, 1)


# ---------------------------------------------------------------------------
# One input, as of one date
# ---------------------------------------------------------------------------
def read_input(st, cfg: dict, name: str, day: str, now: str,
               lookback_days: int = 0) -> dict:
    """{state: read | not existent | not stored | pending, pts, text} for one input
    at one decision date. `pts` is [(day, value)] knowable at the date's close,
    observed in the lookback before it; the latest is within the input's max age."""
    inp = cfg["inputs"][name]
    pit = cfg["point_in_time"]
    ef = inp.get("exists_from")

    def unread(state: str, text: str) -> dict:
        if inp.get("pending"):
            # The credit leg (decision 6): before HY OAS is read, its long proxy
            # is named as pending, whichever reason HY OAS is unread for.
            return {"state": "pending", "pts": [], "text": f"{inp['pending']} ({text})"}
        return {"state": state, "pts": [], "text": text}

    if ef and day < str(ef):
        return unread(NOT_EXISTENT, f"{name} {NOT_EXISTENT} before {ef}")
    if inp.get("reader") == "concentration_twin":
        return _read_top10(st, cfg, day, unread)
    max_age = int(pit["max_age_days"][inp["freq"]])
    since = (_d(day) - dt.timedelta(days=lookback_days + max_age + 7)).isoformat()
    if inp.get("shiller"):
        # No vintages: the current file, each month lagged (session-set).
        lag = int(pit["shiller_lag_months"])
        since = (_d(since) - dt.timedelta(days=31 * lag)).isoformat()
        rows = st.as_of(inp["key"], now, None, since)
        pts = [(_add_months(_d(r["observed_at"]), lag).isoformat(), float(r["value_num"]))
               for r in rows if r.get("value_num") is not None]
        pts = sorted(p for p in pts if p[0] <= day)
    else:
        rows = st.as_of(inp["key"], cutoff(day, cfg), inp.get("instrument"), since)
        pts = sorted((str(r["observed_at"])[:10], float(r["value_num"])) for r in rows
                     if r.get("value_num") is not None and str(r["observed_at"])[:10] <= day)
    if not pts or (_d(day) - _d(pts[-1][0])).days > max_age:
        return unread("not stored", f"{inp['key']} not stored as of {day}")
    return {"state": "read", "pts": pts, "text": ""}


def _read_top10(st, cfg: dict, day: str, unread) -> dict:
    try:
        from altdata import gtm_equities                       # noqa: PLC0415
        tw = gtm_equities.concentration_twin(st, cutoff(day, cfg))
    except Exception as exc:                                    # noqa: BLE001
        return unread("not stored", f"top-10 share not stored as of {day} "
                                    f"({type(exc).__name__})")
    share = ((tw or {}).get("latest") or {}).get("cap_share")
    if (tw or {}).get("state") != "ok" or share is None:
        return unread("not stored", f"top-10 share not stored as of {day} "
                                    f"({(tw or {}).get('absent_reason') or 'no holdings'})")
    return {"state": "read", "pts": [(tw["day"], float(share))], "text": ""}


def _on_or_before(pts: list, day: str) -> Optional[tuple[str, float]]:
    best = None
    for p in pts:
        if p[0] <= day:
            best = p
    return best


# ---------------------------------------------------------------------------
# Triggers and overlays
# ---------------------------------------------------------------------------
def trigger(st, cfg: dict, t: dict, day: str, now: str) -> dict:
    """One trigger at one date: {id, text, state: fires | quiet | <unread>, value, shown}."""
    names = t["input"] if isinstance(t["input"], list) else [t["input"]]
    look = int(t.get("window_days") or 0) + (365 if t["rule"] == "yoy_at_most" else 0) \
        + 7 * int(t.get("sessions") or 0)
    got = {n: read_input(st, cfg, n, day, now, look) for n in names}
    bad = [g for g in got.values() if g["state"] != "read"]
    out = {"id": t["id"], "text": t["text"], "value": None}
    if bad:
        return {**out, "state": bad[0]["state"], "shown": "; ".join(g["text"] for g in bad)}
    a = got[names[0]]["pts"]
    scale = float(cfg["inputs"][names[0]].get("units_to_bp") or 1)
    r, thr = t["rule"], float(t["threshold"])
    v: Optional[float] = None
    if r in ("at_least", "at_most"):
        v = a[-1][1] * scale
    elif r == "erp_at_most":
        g = got[names[1]]["pts"]
        v = 100.0 / a[-1][1] - g[-1][1] if a[-1][1] else None
    elif r == "pct_off_low":
        since = (_d(day) - dt.timedelta(days=int(t["window_days"]))).isoformat()
        low = min(x[1] for x in a if x[0] >= since)
        v = 100.0 * (a[-1][1] / low - 1.0) if low else None
    elif r in ("change_at_least", "abs_change_at_least", "yoy_at_most"):
        days = 365 if r == "yoy_at_most" else int(t["window_days"])
        prev = _on_or_before(a, (_d(a[-1][0]) - dt.timedelta(days=days)).isoformat())
        if prev is None:
            return {**out, "state": "not stored",
                    "shown": f"{cfg['inputs'][names[0]]['key']}: no reading {days} days "
                             f"before {a[-1][0]}"}
        if r == "yoy_at_most":
            v = 100.0 * (a[-1][1] / prev[1] - 1.0) if prev[1] else None
        else:
            v = (a[-1][1] - prev[1]) * scale
            v = abs(v) if r == "abs_change_at_least" else v
    elif r == "spread_avg_at_least":
        b = dict(got[names[1]]["pts"])
        both = [(d, x - b[d]) for d, x in a if d in b][-int(t["sessions"]):]
        if len(both) < int(t["sessions"]):
            return {**out, "state": "not stored",
                    "shown": f"{len(both)} of {t['sessions']} common sessions stored"}
        v = 100.0 * sum(x for _, x in both) / len(both)
    if v is None:
        return {**out, "state": "not stored", "shown": "a zero divisor"}
    fires = v >= thr if r in ("at_least", "pct_off_low", "change_at_least",
                              "abs_change_at_least", "spread_avg_at_least") else v <= thr
    return {**out, "state": "fires" if fires else "quiet", "value": v,
            "shown": f"{v:,.2f} ({a[-1][0]})"}


def overlay(st, cfg: dict, ov: dict, day: str, now: str) -> dict:
    trs = [trigger(st, cfg, t, day, now) for t in ov["triggers"]]
    k = sum(1 for t in trs if t["state"] == "fires")
    read = sum(1 for t in trs if t["state"] in ("fires", "quiet"))
    ne = sum(1 for t in trs if t["state"] == NOT_EXISTENT)
    n, need = len(trs), int(ov["fires_at"])
    state = (FIRES if k >= need else CLEAR if k + (n - read) < need
             else OVERLAY_NOT_EXISTENT if n - ne < need else UNREAD)
    return {"id": ov["id"], "title": ov["title"], "state": state, "fired": k,
            "read": read, "not_existent": ne, "n": n, "triggers": trs}


def overlays_at(st, cfg: dict, day: str, now: str) -> list[dict]:
    return [overlay(st, cfg, ov, day, now) for ov in cfg["overlays"]]


def state_text(o: dict) -> str:
    ne = f", {o['not_existent']} not existent" if o.get("not_existent") else ""
    return f"{o['state']} {o['fired']}/{o['n']} ({o['read']} read{ne})"


# ---------------------------------------------------------------------------
# Episodes
# ---------------------------------------------------------------------------
def spx_extreme(st, cfg: dict, day: str, kind: str, now: str) -> str:
    """The store's own S&P 500 extreme within the window around a decision date,
    so a session-set day is checked against the closes, not asserted."""
    w = int(cfg["point_in_time"]["extreme_window_days"])
    if day < str(cfg["inputs"]["spx"]["exists_from"]):
        return NOT_EXISTENT
    lo, hi = (_d(day) - dt.timedelta(days=w)).isoformat(), (_d(day) + dt.timedelta(days=w)).isoformat()
    rows = [(str(r["observed_at"])[:10], float(r["value_num"]))
            for r in st.as_of(cfg["inputs"]["spx"]["key"], now, None, lo)
            if r.get("value_num") is not None and str(r["observed_at"])[:10] <= hi]
    if not rows:
        return "not stored"
    best = (max if kind == "high" else min)(rows, key=lambda x: x[1])
    return ("agrees" if best[0] == day else f"store's {kind} {best[0]}") + f" ({best[1]:,.2f})"


def classify(cls: str, per_date: list[list[dict]]) -> str:
    states = [o["state"] for ovs in per_date for o in ovs]
    if cls == "bottom":
        return "not scored"
    if cls == "top":
        return ("called" if FIRES in states else "unread" if UNREAD in states
                else "not existent" if set(states) == {OVERLAY_NOT_EXISTENT} else "missed")
    return ("false call" if FIRES in states else "unread" if UNREAD in states
            else "not existent" if set(states) == {OVERLAY_NOT_EXISTENT} else "refused")


def hand_keyed(st, cfg: dict, ep: dict, day: str, now: str) -> list[dict]:
    """The harness's point-in-time reading beside each value the papers hand-keyed."""
    out = []
    tol = float(cfg["point_in_time"]["differs_pct"])
    for m, paper in (ep.get("hand_keyed") or {}).items():
        if m == "erp":
            t = next(x for o in cfg["overlays"] for x in o["triggers"] if x["id"] == "erp")
            r = trigger(st, cfg, t, day, now)
            got, why = r["value"], r["shown"]
        else:
            name = "hy_oas" if m == "hy_oas_bp" else m
            g = read_input(st, cfg, name, day, now)
            scale = float(cfg["inputs"][name].get("units_to_bp") or 1)
            got = g["pts"][-1][1] * scale if g["state"] == "read" else None
            why = g["text"]
        if got is None:
            verdict = f"harness unread: {why}"
        elif abs(got - float(paper)) > tol / 100.0 * abs(float(paper)):
            verdict = "differs"
        else:
            verdict = "agrees"
        out.append({"metric": m, "paper": paper, "harness": got, "verdict": verdict})
    return out


def run_calibration(st, cfg: dict, now: str) -> list[dict]:
    out = []
    for ep in cfg["calibration"]:
        kinds = (["high", "low"] if ep["class"] == "control" else
                 ["high"] if ep["class"] == "top" else ["low"])
        per = [overlays_at(st, cfg, d, now) for d in ep["dates"]]
        out.append({**ep, "per_date": per,
                    "extremes": [spx_extreme(st, cfg, d, k, now)
                                 for d, k in zip(ep["dates"], kinds)],
                    "classification": classify(ep["class"], per),
                    "hand": hand_keyed(st, cfg, ep, ep["dates"][-1], now)})
    return out


def extended_dates(cfg: dict) -> list[dict]:
    """The extended set flattened to (set, id, class, date, kind): never pooled."""
    ex, out = cfg["extended"], []
    for e in ex["bears"]["episodes"]:
        out += [{"set": "bears", "id": e["id"], "class": "top", "date": e["top"], "kind": "high"},
                {"set": "bears", "id": e["id"], "class": "bottom", "date": e["bottom"], "kind": "low"}]
    for e in ex["near_misses"]["episodes"]:
        out += [{"set": "near_misses", "id": e["id"], "class": "control", "date": e["high"], "kind": "high"},
                {"set": "near_misses", "id": e["id"], "class": "control", "date": e["low"], "kind": "low"}]
    for e in ex["pre_1970"]["episodes"]:
        out += [{"set": "pre_1970", "id": e["id"], "class": "top", "date": e["top"], "kind": "high"},
                {"set": "pre_1970", "id": e["id"], "class": "bottom", "date": e["bottom"], "kind": "low"}]
    for e in ex["false_bottoms"]["episodes"]:
        out.append({"set": "false_bottoms", "id": e["id"], "class": "false bottom",
                    "date": e["trough"], "kind": "low"})
    return out


def run_extended(st, cfg: dict, now: str) -> list[dict]:
    return [{**x, "overlays": overlays_at(st, cfg, x["date"], now),
             "extreme": spx_extreme(st, cfg, x["date"], x["kind"], now)}
            for x in extended_dates(cfg)]


def record(cal: list[dict]) -> dict:
    """k of n per class, with the unread count: the harness's own record."""
    out = {}
    for cls, hit in (("top", "called"), ("control", "refused"), ("bottom", None)):
        eps = [e for e in cal if e["class"] == cls]
        out[cls] = {"n": len(eps),
                    "k": sum(1 for e in eps if e["classification"] == hit) if hit else None,
                    "unread": sum(1 for e in eps if e["classification"] in ("unread", "not scored"))}
    return out


def verdicts(rec: dict) -> tuple[str, str]:
    """(the reproduction answer, the pass rule's verdict), by the registered rule."""
    unread = [c for c, r in rec.items() if r["unread"] or r["k"] is None]
    if not unread and all((rec[c]["k"], rec[c]["n"]) == RECORD[c] for c in RECORD):
        repro = "REPRODUCED"
    else:
        named = ", ".join(f"{c}s ({'not scored by the overlays' if rec[c]['k'] is None else str(rec[c]['unread']) + ' unread'})"
                          for c in unread) or "none unread; the counts differ"
        repro = f"NOT REPRODUCIBLE ON THIS BUILD -- {named}"
    t, c = rec["top"], rec["control"]
    if t["unread"] or c["unread"]:
        v = f"INSUFFICIENT ({t['unread']} of 3 tops and {c['unread']} of 4 controls unread)"
    elif t["k"] >= 2 and c["k"] >= 3:
        v = f"PASS (tops {t['k']}/3 called, controls {c['k']}/4 refused)"
    else:
        v = f"FAIL (tops {t['k']}/3 called, controls {c['k']}/4 refused)"
    return repro, v


# ---------------------------------------------------------------------------
# The ledger
# ---------------------------------------------------------------------------
def ledger(st, cfg: dict, edition: str, now: str, run_date: str) -> tuple[str, str]:
    cal = run_calibration(st, cfg, now)
    ext = run_extended(st, cfg, now)
    rec = record(cal)
    repro, verdict = verdicts(rec)
    pit = cfg["point_in_time"]
    rec_line = ", ".join(f"{c}s {r['k'] if r['k'] is not None else '—'}/{r['n']}"
                         + (f" ({r['unread']} unread)" if r['unread'] and r['k'] is not None else "")
                         for c, r in rec.items())
    L = [f"# T&B harness ledger -- the 3 Sep thirteen through Part 23's overlays (6i-2)", "",
         f"**Edition:** {run_date}, {edition} run over the observation store, read-only, "
         f"as of each decision date. A re-run against "
         + ("the box's store" if edition == "laptop" else "a later store")
         + " supersedes it (a new dated file); this one is never edited.", "",
         "**The pass rule is pre-registered** (the calibration-ledger convention of 17 Oct "
         "2026): written in config/tb_episodes.yaml before this edition ran, printed here "
         "verbatim with its SHA-256, held equal by tools/validate_tb_harness.py. A re-run "
         "may apply it, never change it.", "",
         f"> {' '.join(str(cfg['pass_rule']).split())}", "",
         "| | |", "|---|---|",
         f"| As of | each decision date's close ({pit['cutoff_time_et']} ET), by available_at; "
         f"Shiller's months lagged {pit['shiller_lag_months']} months; run {now[:16]} UTC |",
         f"| Window | the 3 Sep thirteen, {min(d for e in cal for d in e['dates'])} to "
         f"{max(d for e in cal for d in e['dates'])}; the extended set beside it, never pooled |",
         f"| n | 13 episodes, {sum(len(e['dates']) for e in cal)} decision dates; extended "
         f"{len(ext)} dates |",
         f"| Statistic | the overlays' record: {rec_line} |",
         "| Pass rule | as quoted above |",
         f"| Pass rule SHA-256 | `{rule_hash(cfg)}` |",
         f"| Verdict | **{verdict}** |",
         "| Rights consequence | None. Report-only (the brief, 2.5): nothing enters a "
         "composite, the market-state object, a dial, a band or a packet; no composite is "
         "stored (decision 3). |", "",
         "## The ledger's own question", "",
         "**Does the harness reproduce \"tops 0/3, bottoms 4/6, controls 4/4\"?** "
         f"**{repro}.** The record was the composite's under the original weights "
         "(the architecture's Part 23); the composite and its hand-keyed table stayed in "
         "the 3 Sep session and decision 3 stores none, so the harness reads Part 23's "
         "three overlays instead. They are top-side: a bottom is not scored by them. "
         f"The overlays' own record: {rec_line}.", "",
         "## The thirteen", "",
         "| Episode | Class | Date | S&P 500 in the store | Concentration | HY acceleration "
         "| Liquidity | Classification | Session-set |",
         "|---|---|---|---|---|---|---|---|---|"]
    for e in cal:
        for i, (d, ovs) in enumerate(zip(e["dates"], e["per_date"])):
            L.append(f"| {e['id'] if i == 0 else ''} | {e['class'] if i == 0 else ''} | {d} "
                     f"| {e['extremes'][i]} | " + " | ".join(state_text(o) for o in ovs)
                     + f" | {e['classification'] if i == 0 else ''} "
                     f"| {('yes' if e.get('session_set') else 'no') if i == 0 else ''} |")
    L += ["", "Each episode's source passage, and the basis of every session-set date or "
              "class, is in config/tb_episodes.yaml and the notes (docs/briefs/a77-6i-notes.md).",
          "", "## Point in time against the papers' hand-keyed values", "",
          "The papers' figures were \"hand-compiled for this study, not machine-extracted "
          "from a point-in-time database\" (Tops and Bottoms, \"Caveats restated\"). Beside "
          f"each, the harness's reading as of the date; \"differs\" past {pit['differs_pct']}% "
          "of the paper's value.", "",
          "| Episode | Date | Metric | Paper | Harness | Reading |", "|---|---|---|---|---|---|"]
    for e in cal:
        for h in e["hand"]:
            got = "—" if h["harness"] is None else f"{h['harness']:,.2f}"
            L.append(f"| {e['id']} | {e['dates'][-1]} | {h['metric']} | {h['paper']} | {got} "
                     f"| {h['verdict']} |")
    L += ["", "## The trigger readings at the thirteen's dates", "",
          "| Episode | Date | Overlay | Trigger | Reading |", "|---|---|---|---|---|"]
    for e in cal:
        for d, ovs in zip(e["dates"], e["per_date"]):
            for o in ovs:
                for t in o["triggers"]:
                    shown = (t["shown"] if t["shown"].startswith(t["state"])
                             else f"{t['state']}: {t['shown']}")
                    L.append(f"| {e['id']} | {d} | {o['title']} | {t['text']} | {shown} |")
    L += ["", "## The extended set (flagged; never pooled with the thirteen)", "",
          "Base Rates, chapter 12's first amendment: \"the harness must not score a signal "
          "that could not have existed\". A date before a series begins reads it as not "
          "existent.", "",
          "| Set | Episode | Class | Date | S&P 500 in the store | Concentration "
          "| HY acceleration | Liquidity |", "|---|---|---|---|---|---|---|---|"]
    for x in ext:
        L.append(f"| {x['set']} | {x['id']} | {x['class']} | {x['date']} | {x['extreme']} | "
                 + " | ".join(state_text(o) for o in x["overlays"]) + " |")
    L += ["", "## Caveats", "",
          f"- Shiller's CAPE and 10-year rate are the current file's values, each month "
          f"treated as knowable {pit['shiller_lag_months']} months after it begins "
          f"({pit['shiller_lag_source']}). They are not first prints.",
          "- The credit leg reads fred.hy_oas where the store holds it; before that it "
          "prints \"pending 6i-3: Baa less the 10-year\" (decision 6). 6i-3 adds DBAA and BAA.",
          "- Part 23's ERP, the SOFR−IORB window, the TGA window and the net-liquidity "
          "\"accel\" are not defined there; their definitions here are session-set and "
          "named in config/tb_episodes.yaml.",
          "- The continuous false-positive rate (Part 23's deferred item 3) is 6i-3, not "
          "this edition.",
          "- A laptop edition reads a partial store: a reading it cannot make is printed "
          "as such, and the box's run supersedes it.", ""]
    md = "\n".join(L)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["set", "episode", "class", "date", "spx_check", "concentration",
                "hy_accel", "liquidity", "classification"])
    for e in cal:
        for i, (d, ovs) in enumerate(zip(e["dates"], e["per_date"])):
            w.writerow(["calibration", e["id"], e["class"], d, e["extremes"][i]]
                       + [state_text(o) for o in ovs] + [e["classification"]])
    for x in ext:
        w.writerow([f"extended:{x['set']}", x["id"], x["class"], x["date"], x["extreme"]]
                   + [state_text(o) for o in x["overlays"]] + [""])
    return md, buf.getvalue()


def _today_et() -> str:
    return dt.datetime.now(ET).date().isoformat()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.tb_harness")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="the three overlays as of one date")
    s.add_argument("--db")
    s.add_argument("--date", default=None)
    g = sub.add_parser("ledger", help="the dated ledger and its episodes CSV")
    g.add_argument("--db")
    g.add_argument("--edition", default="laptop", choices=["laptop", "box"])
    g.add_argument("--out-dir", default=str(LEDGER_DIR))
    g.add_argument("--dry-run", action="store_true",
                   help="print the ledger; write nothing")
    a = ap.parse_args(argv)
    cfg = config()
    st = Reader(a.db)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        if a.cmd == "show":
            day = a.date or _today_et()
            for o in overlays_at(st, cfg, day, now):
                print(f"{o['title']}: {state_text(o)}")
                for t in o["triggers"]:
                    print(f"    {t['text']:<28} {t['state']}: {t['shown']}")
            return 0
        run_date = _today_et()
        md, rows = ledger(st, cfg, a.edition, now, run_date)
        if a.dry_run:
            print(md)
            return 0
        out = Path(a.out_dir)
        path = out / f"tb-harness-{run_date}.md"
        if path.exists():
            print(f"{path} exists: a ledger is never edited; re-run on another day "
                  f"for a new edition")
            return 2
        out.mkdir(parents=True, exist_ok=True)
        path.write_bytes(md.encode("utf-8"))
        (out / f"tb-harness-{run_date}-episodes.csv").write_bytes(rows.encode("utf-8"))
        print(f"wrote {path} and its episodes CSV")
        return 0
    finally:
        st.close()


if __name__ == "__main__":
    sys.exit(main())

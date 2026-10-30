"""
6f tranche 2: the market-state object's calibration -- the dials' transition
counts, the "uncalibrated (n = k of 30)" rendering, and the ledger rows for a
calibrated dial row (rulings 7a and 8a of 24 Oct 2026; the spec,
docs/briefs/6f-spec-draft-2026-10-24.md section 3).

    from altdata import state_calibration as sc
    m = sc.matrices(store, as_of)          # every dial (and dimension) x horizon
    sc.close_line(m, obj); sc.table(m, obj)
    sc.write_ledger(obj, m, ledger)        # calibrated dial rows only
    sc.resolve_due(store, ledger, as_of)   # each due row against the stored object
    python -m altdata.state_calibration show [--as-of ...] [--db ...]

THE METHOD (section 3.1). For a dial, the published state at session t and the
published state at t + h, both READ from stored objects -- never recomputed with
today's code -- make one pair. P(s' | s, h) is the share of the pairs starting
in s that end in s', counted, not modelled. Horizons 5, 20 and 63 sessions (Books
C, B and A).

POINT IN TIME (section 3.3). A read as of a cutoff uses only objects whose
available_at is at or before it (the latest such vintage per session), and only
objects under the current method version. A pair needs both ends: its t + h
object must be knowable at the cutoff too. A pair across a session whose object
is absent, a fault or not stored is skipped and counted as skipped.

THE SAMPLE (section 3.2). A row prints only when its state has at least
MIN_STARTS INDEPENDENT starts -- start sessions at least h sessions apart, taken
greedily from the earliest. Below it the row is the literal
"uncalibrated (n = k of 30)", never a number and never an empty field (7a).

THE LEDGER (section 3.4; 8a). Dial rows only, at the three horizons, and only
once a row is calibrated: one binary row per state of the scenario set
state:<dial>:<h>s:<session>, each with its resolution criterion. The
probabilities are the counts ADD-HALF SMOOTHED (each state's count plus one half,
over the row's pairs plus half the states) so none is 0 or 1 -- the ledger refuses
certainty -- and the set still sums to 1 for coherence(). Dimensions are never
ledgered; their tables print in the Monthly, unledgered.

Reads the store and writes only the ledger the caller hands it. Not in regime's
method hash: the object's content does not change.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

from . import observations, session

MIN_STARTS = 30
HORIZONS = (5, 20, 63)
DIALS = ("macro", "vol", "gamma")
SOURCE = "market_state"
SMOOTH = 0.5                     # add-half smoothing (SESSION-SET; the docstring)
STORE_KEY = "market_state"


def _method() -> str:
    import regime                                               # noqa: PLC0415
    return regime.METHOD_VERSION


def stored_objects(store, as_of: Optional[str] = None,
                   method: Optional[str] = None) -> dict[str, dict]:
    """{session: object} -- for each session, the latest vintage with
    available_at at or before `as_of`, under `method` (the current one)."""
    # One width on both sides (observations.canonical_instant): a second-resolution
    # cutoff against microsecond rows would hide an object computed at it.
    cut = observations.canonical_instant(as_of or session.utc_iso(timespec="microseconds"))
    want = method or _method()
    out: dict[str, tuple[str, dict]] = {}
    rows = store.conn.execute(
        "SELECT observed_at, available_at, value_text FROM observations "
        "WHERE registry_key = ? AND available_at <= ? ORDER BY available_at",
        (STORE_KEY, cut)).fetchall()
    for obs_at, avail, text in rows:
        try:
            obj = json.loads(text)
        except (TypeError, ValueError):
            continue
        if obj.get("method_version") != want:
            continue
        day = str(obs_at)[:10]
        if day not in out or str(avail) >= out[day][0]:
            out[day] = (str(avail), obj)
    return {d: o for d, (_, o) in sorted(out.items())}


def dial_state(obj: dict, dial: str) -> Optional[str]:
    d = (obj.get("dials") or {}).get(dial) or {}
    return None if d.get("fault") else d.get("state")


def dimension_state(obj: dict, dim: str) -> Optional[str]:
    d = (obj.get("dimensions") or {}).get(dim) or {}
    return None if d.get("fault") else d.get("state")


def _calendar(first: str, last: str) -> list[str]:
    import regime                                               # noqa: PLC0415
    return regime.session_days(first, last)


def transitions(states: dict[str, Optional[str]], h: int,
                calendar: list[str]) -> dict:
    """{state: {"pairs": {s': n}, "n_pairs": n, "starts": [sessions], "independent": k},
    "_skipped": n} over the calendar's sessions."""
    idx = {d: i for i, d in enumerate(calendar)}
    rows: dict[str, Any] = {}
    skipped = 0
    for d in calendar:
        s = states.get(d)
        if s is None:
            continue
        i = idx[d]
        if i + h >= len(calendar):
            continue
        s2 = states.get(calendar[i + h])
        if s2 is None:
            skipped += 1
            continue
        r = rows.setdefault(s, {"pairs": {}, "n_pairs": 0, "starts": []})
        r["pairs"][s2] = r["pairs"].get(s2, 0) + 1
        r["n_pairs"] += 1
        r["starts"].append(i)
    for s, r in rows.items():
        k, last = 0, None
        for i in r["starts"]:
            if last is None or i - last >= h:
                k, last = k + 1, i
        r["independent"] = k
        r["starts"] = [calendar[i] for i in r["starts"]]
    rows["_skipped"] = skipped
    return rows


def matrices(store, as_of: Optional[str] = None, dimensions: bool = True) -> dict:
    """{"dials": {dial: {h: transitions}}, "dimensions": {...}, "sessions": n,
    "as_of": cut, "method": m} from the objects knowable at the cutoff."""
    cut = as_of or session.utc_iso(timespec="microseconds")
    objs = stored_objects(store, cut)
    out: dict[str, Any] = {"as_of": cut, "method": _method(), "sessions": len(objs),
                           "dials": {}, "dimensions": {}}
    if not objs:
        return out
    days = sorted(objs)
    cal = _calendar(days[0], days[-1])
    for dial in DIALS:
        st = {d: dial_state(o, dial) for d, o in objs.items()}
        out["dials"][dial] = {h: transitions(st, h, cal) for h in HORIZONS}
    if dimensions:
        names = sorted({n for o in objs.values() for n in (o.get("dimensions") or {})})
        for n in names:
            st = {d: dimension_state(o, n) for d, o in objs.items()}
            out["dimensions"][n] = {h: transitions(st, h, cal) for h in HORIZONS}
    return out


def row_for(trans: dict, state: Optional[str], states: list[str]) -> dict:
    """The row for the current state: calibrated with its smoothed probabilities,
    or uncalibrated with k."""
    r = (trans or {}).get(state) or {}
    k = int(r.get("independent") or 0)
    if state is None:
        return {"calibrated": False, "k": 0,
                "text": f"no current state; uncalibrated (n = 0 of {MIN_STARTS})"}
    if k < MIN_STARTS:
        return {"calibrated": False, "k": k,
                "text": f"uncalibrated (n = {k} of {MIN_STARTS})"}
    states = sorted(set(states) | set(r["pairs"]))
    tot = r["n_pairs"] + SMOOTH * len(states)
    probs = {s: (r["pairs"].get(s, 0) + SMOOTH) / tot for s in states}
    text = ", ".join(f"{s} {p:.2f}" for s, p in sorted(probs.items(), key=lambda x: -x[1]))
    return {"calibrated": True, "k": k, "n_pairs": r["n_pairs"], "probs": probs,
            "text": f"{text} (n = {k} independent starts, {r['n_pairs']} pairs)"}


def dial_states_declared(dial: str) -> list[str]:
    import regime                                               # noqa: PLC0415
    cfg = regime.load_config()
    d = (cfg.get("dials") or {}).get(dial) or {}
    if dial == "macro":
        return sorted({r.get("state") for r in d.get("rules") or [] if r.get("state")})
    if dial == "vol":
        return [b.get("state") for b in d.get("level_bands") or []]
    return list(d.get("states") or ["positive", "negative", "flat"])


def reads(m: dict, obj: Optional[dict]) -> dict:
    """{dial: {h: row}} for the object's current dial states."""
    out: dict[str, dict] = {}
    for dial in DIALS:
        cur = dial_state(obj or {}, dial)
        out[dial] = {h: row_for(m.get("dials", {}).get(dial, {}).get(h), cur,
                                dial_states_declared(dial)) for h in HORIZONS}
    return out


def close_line(m: dict, obj: Optional[dict]) -> str:
    """The daily close's one line."""
    r = reads(m, obj)
    parts = []
    for dial in DIALS:
        cur = dial_state(obj or {}, dial) or "absent"
        hs = "; ".join(f"{h}s {r[dial][h]['text']}" for h in HORIZONS)
        parts.append(f"{dial} ({cur}): {hs}")
    return "Dial transitions -- " + " | ".join(parts) + "."


def table(m: dict, obj: Optional[dict]) -> dict:
    """The Weekly's and the Monthly's table: dial x horizon."""
    r = reads(m, obj)
    rows = [[dial, dial_state(obj or {}, dial) or "absent", f"{h} sessions",
             r[dial][h]["text"]] for dial in DIALS for h in HORIZONS]
    return {"columns": ["Dial", "Now", "Horizon", "Where it stood h sessions later"],
            "rows": rows}


def dimension_table(m: dict, obj: Optional[dict]) -> dict:
    """The Monthly's dimension table, UNLEDGERED (8a): k per dimension x horizon."""
    rows = []
    for n, by_h in sorted((m.get("dimensions") or {}).items()):
        cur = dimension_state(obj or {}, n)
        cells = [row_for(by_h.get(h), cur, [])["text"] for h in HORIZONS]
        rows.append([n, cur or "absent"] + cells)
    return {"columns": ["Dimension", "Now"] + [f"{h} sessions" for h in HORIZONS],
            "rows": rows}


def horizon_date(day: str, h: int) -> str:
    """The session h sessions after `day`."""
    import datetime as dt
    import regime                                               # noqa: PLC0415
    d = dt.date.fromisoformat(day)
    cal = regime.session_days(day, (d + dt.timedelta(days=h * 2 + 14)).isoformat())
    return cal[h] if len(cal) > h else cal[-1]


def criterion(dial: str, hd: str) -> str:
    return (f"the published state of the {dial} dial on the market_state object "
            f"for {hd}, latest vintage")


def write_ledger(obj: dict, m: dict, ledger, emitted_at: Optional[str] = None) -> int:
    """Calibrated DIAL rows only (8a): one binary row per state of the set. An
    uncalibrated row writes nothing. Returns the rows written."""
    n = 0
    day = obj.get("session")
    r = reads(m, obj)
    for dial in DIALS:
        for h in HORIZONS:
            row = r[dial][h]
            if not row.get("calibrated"):
                continue
            hd = horizon_date(day, h)
            for s, p in sorted(row["probs"].items()):
                ledger.record(source=SOURCE,
                              claim=f"the {dial} dial is {s} at {hd}",
                              probability=p, horizon_date=hd,
                              resolution_criterion=criterion(dial, hd),
                              scenario_set=f"state:{dial}:{h}s:{day}",
                              emitted_at=emitted_at,
                              emitted_by=f"regime:{obj.get('method_version')}",
                              # LL-3: the object's absent dimensions at emission
                              missing_inputs=obj.get("absent_dimensions") or [])
                n += 1
    return n


def resolve_due(store, ledger, as_of: Optional[str] = None) -> int:
    """Each due market_state row against the stored object for its horizon date
    (latest vintage knowable at `as_of`). A row whose object is absent waits."""
    objs = stored_objects(store, as_of)
    n = 0
    for row in ledger.due(as_of):
        if row["source"] != SOURCE:
            continue
        obj = objs.get(row["horizon_date"])
        dial = str(row["scenario_set"] or "").split(":")[1] if row["scenario_set"] else None
        if obj is None or dial not in DIALS:
            continue
        got = dial_state(obj, dial)
        if got is None:
            continue
        claimed = str(row["claim"]).rsplit(" is ", 1)[-1].split(" at ", 1)[0]
        ledger.resolve(row["probability_id"], 1 if got == claimed else 0,
                       note=f"the stored object for {row['horizon_date']}: {dial} {got}")
        n += 1
    return n


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.state_calibration")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="the dial transition reads, read-only")
    s.add_argument("--as-of")
    s.add_argument("--db")
    a = ap.parse_args(argv)
    with observations.ObservationStore(a.db) as st:
        m = matrices(st, a.as_of)
        import regime                                           # noqa: PLC0415
        obj = regime.latest(as_of=a.as_of, store=st)
    print(f"{m['sessions']} objects under {m['method']} knowable at {m['as_of']}")
    print(close_line(m, obj))
    for row in table(m, obj)["rows"]:
        print(" | ".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

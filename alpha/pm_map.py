"""
The draft of engine 3's contract map (ruling 18, 14 Oct 2026).

    python -m alpha.pm_map draft [--store PATH] [--as-of ISO]

Reads the observation store READ-ONLY (alpha.store.ReadOnlyStore: a mode=ro
connection, query_only on) and PRINTS candidate entries for
config/alpha_pm_map.yaml to the screen. It writes nothing -- not the map, not
the store, not a file anywhere. The operator reads the draft, pastes it back,
and a later session commits the lines he confirms with `confirmed: true`.

WHAT IT DRAFTS. One entry per stored prediction-market contract (a pm.market
row, instrument `<venue>:<market id>`) that:

  - belongs to the FOMC-decision watch (watch_id fomc_decision -- Kalshi's
    KXFEDDECISION series, Polymarket's fed-decision-in-* events);
  - has a STORED resolution rule (the pm.market row's `criteria`, the venue's own
    text; W-1.1 item 1.5). No stored rule, no entry: the contract is listed under
    "not drafted" with the reason;
  - resolves on a stored FOMC decision day (cal.fomc_*'s decision_days);
  - names an outcome engine 3 prices -- a 25 bp cut, a 25 bp hike, or a hold --
    read from the venue's own outcome label. Anything else (a 50 bp move, "cut
    > 25 bps") is listed as not drafted, because the futures path prices one 25
    bp step per meeting.

Every drafted entry carries `confirmed: false` and `drafted_from`: the stored
rule quoted in full, the outcome label and question it was read from, the rules
page, the pm.market row's observed_at. Engine 3 (alpha/engines/pm_futures.py)
reads ONLY entries with `confirmed: true`, so a draft pasted in unreviewed
trades nothing.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Optional

WATCH = "fomc_decision"

_HOLD = re.compile(r"\b(hold|no change|unchanged|maintain(s|ed)?|pause)\b", re.I)
_CUT = re.compile(r"\b(cut|decrease|lower|reduc)", re.I)
_HIKE = re.compile(r"\b(hike|increase|raise|higher)\b", re.I)
_BIG = re.compile(r"(>\s*25|50\s*(bps?|basis)|75\s*(bps?|basis)|100\s*(bps?|basis)|"
                  r"more than 25|at least 50|over 25)", re.I)


def outcome_of(label: str) -> Optional[str]:
    """cut | hike | hold from a venue's outcome label, or None where the label
    names a move engine 3 does not price (anything beyond one 25 bp step) or
    nothing recognisable."""
    t = str(label or "")
    if _BIG.search(t):
        return None
    hits = [o for o, rx in (("hold", _HOLD), ("cut", _CUT), ("hike", _HIKE))
            if rx.search(t)]
    return hits[0] if len(hits) == 1 else None


def draft(store, as_of: Optional[str] = None, meetings: Optional[list[str]] = None
          ) -> tuple[list[dict], list[dict]]:
    """(entries, not_drafted) over every stored pm.market contract."""
    if meetings is None:
        from altdata import fed_funds                           # noqa: PLC0415
        meetings = [d.isoformat() for d in fed_funds.meeting_days()]
    days = set(meetings)
    entries, skipped = [], []
    for inst in sorted(store.instruments("pm.market")):
        r = store.latest_as_of("pm.market", as_of, inst)
        try:
            meta = json.loads((r or {}).get("value_text") or "{}")
        except ValueError:
            meta = {}
        if meta.get("watch_id") != WATCH:
            continue                                   # not an FOMC-decision market
        why = None
        rule = str(meta.get("criteria") or "").strip()
        meeting = str(meta.get("decision_date") or "")[:10]
        outcome = outcome_of(meta.get("outcome") or "")
        if not rule:
            why = "no resolution rule stored"
        elif meeting not in days:
            why = f"decision date {meeting or '(none)'} is not a stored FOMC decision day"
        elif outcome is None:
            why = (f"outcome {meta.get('outcome')!r} is not a 25 bp cut, a 25 bp "
                   f"hike or a hold")
        if why:
            skipped.append({"contract": inst, "why": why})
            continue
        entries.append({
            "contract": inst, "venue": meta.get("venue") or inst.split(":", 1)[0],
            "meeting": meeting, "outcome": outcome, "confirmed": False,
            "resolution": rule,
            "drafted_from": {"stored_rule": rule,
                             "outcome_label": meta.get("outcome"),
                             "question": meta.get("question"),
                             "rules_url": meta.get("rules_url"),
                             "pm_market_observed_at": (r or {}).get("observed_at")},
        })
    return entries, skipped


def _scalar(v) -> str:
    """A YAML scalar: JSON's double-quoted string is valid YAML, so the venue's
    text is quoted exactly, escapes and all."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return json.dumps(str(v), ensure_ascii=False)


def render(entries: list[dict], skipped: list[dict]) -> str:
    """The draft as YAML text for config/alpha_pm_map.yaml's `contracts:`,
    built as text (nothing in alpha/ dumps or writes)."""
    out = ["# DRAFT -- python -m alpha.pm_map draft. Nothing here trades until a",
           "# line is reviewed and committed with confirmed: true (ruling 18).",
           f"# {len(entries)} drafted, {len(skipped)} not drafted."]
    out.append("contracts:" if entries else "contracts: []")
    for e in entries:
        first = True
        for k, v in e.items():
            lead = "  - " if first else "    "
            first = False
            if isinstance(v, dict):
                out.append(f"{lead}{k}:")
                out += [f"      {k2}: {_scalar(v2)}" for k2, v2 in v.items()]
            else:
                out.append(f"{lead}{k}: {_scalar(v)}")
    if skipped:
        out += ["", "# NOT DRAFTED:"] + [f"#   {s['contract']}: {s['why']}" for s in skipped]
    return "\n".join(out) + "\n"


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from .store import ReadOnlyStore                            # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m alpha.pm_map",
                                 description="Print a draft of engine 3's contract map")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft", help="read the store read-only; print the draft")
    d.add_argument("--store")
    d.add_argument("--as-of")
    a = ap.parse_args(argv)
    st = ReadOnlyStore(a.store)
    try:
        entries, skipped = draft(st, a.as_of)
    finally:
        st.close()
    sys.stdout.write(render(entries, skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))


"""
The rates attribution block -- descriptive, no state (signal-triage ST-3, re-scoped).

    python -m altdata.rates_attribution show
    python -m altdata.rates_attribution show --as-of 2026-09-29T21:30:00+00:00
    python -m altdata.rates_attribution show --json

WHAT IT IS. Each decomposition model's split of the recent yield move into PATH
(expected short rates) and PREMIUM (term premium), over 20 and 60 of the model's
own observations, each with the date it is as of; the move and SR-6's two cuts
beside them; and whether the models that are present lean the same way. It reads
the stored calc.* shares (altdata/market_features.py) as-of the cutoff and
computes no delta of its own.

WHAT IT IS NOT, by ruling of 30 Sep 2026. It is not a state. The four-cell
`rates.driver` it replaces failed its calibration gate twice
(docs/ledgers/rates-driver-2026-09.md, rates-driver-2026-09-30-r2.md) and was
withdrawn: no cell, no tuned threshold, nothing in the market-state object, no
contradiction row. regime.py does not import this module and this module does not
import regime. SR-6 and SR-17 stay `DEFERRED -- gate failed`; a cell that labels
only when two or more models agree is a backlog item needing its own
pre-registration.

THE ONE NUMBER IN IT IS A DEFINITION, NOT A THRESHOLD. A model "leans path" when
its path share exceeds its premium share -- path > 0.5 of the two -- and "leans
premium" the other way. That is which leg is larger, the question the block
answers; it is not tuned and no calibration can move it. It does NOT say the lean
is decisive: 0.51 and 0.95 both lean path, and the shares are printed so a reader
sees which.

THE THREE SPLITS ARE NOT THE SAME QUANTITY. DKW splits the REAL yield (the TIPS
liquidity premium left out); Kim-Wright and ACM split the NOMINAL yield. Their
agreeing is two different decompositions of related moves pointing the same way
-- worth printing, and not three confirmations: all three are model outputs of one
market (registry mechanism_group rates_decomposition), re-estimated as they go.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from . import derived, observations, session

log = logging.getLogger(__name__)

WINDOWS = (20, 60)
STALENESS_MULTIPLE = 3          # the market-state object's own default
MOVE = "calc.attr_d10y_{w}d"
REAL = "calc.attr_real_share_{w}d"
CURVE = "calc.attr_curve_share_{w}d"

# model, label, which yield it splits, the share key and whether it is the path
# share (DKW) or the premium share (KW, ACM), and the model's own series -- read
# only to say when a share has not been written since the model last printed.
MODELS = (
    {"model": "dkw", "label": "DKW", "split": "real",
     "share": "calc.attr_dkw_path_share_{w}d", "is_path": True,
     "source": "dkw.real_term_premium_10y"},
    {"model": "kw", "label": "Kim-Wright", "split": "nominal",
     "share": "calc.attr_kw_tp_share_{w}d", "is_path": False,
     "source": "fred.term_premium_kw"},
    {"model": "acm", "label": "ACM", "split": "nominal",
     "share": "calc.attr_acm_tp_share_{w}d", "is_path": False,
     "source": "acm.term_premium_10y"},
)


def _read(metric: str, as_of: str,
          store: observations.ObservationStore) -> dict:
    """One stored series at the cutoff: level and date, or absent with a reason
    that cites data. A reader that raises records `fault`, never a reason."""
    out: dict[str, Any] = {"metric": metric, "level": None}
    try:
        d = derived.derived_forms(metric, as_of, store=store)
    except Exception as exc:                                  # noqa: BLE001
        out["fault"] = f"{type(exc).__name__}: {exc}"
        return out
    out["as_of"] = d.get("observed_at")
    if d.get("level") is None:
        out["absent_reason"] = f"no observation for {metric} knowable at {as_of}"
        return out
    stale, own = d.get("staleness_sessions"), d.get("staleness_allowance_sessions")
    if stale is not None and own is not None and stale > own * STALENESS_MULTIPLE:
        out["absent_reason"] = (
            f"{metric} was last observed {d.get('observed_at')}, {stale} sessions "
            f"before this cutoff; its own allowance is {own} x{STALENESS_MULTIPLE}")
        return out
    out["level"] = d["level"]
    return out


def _lean(path: float) -> str:
    return "path" if path > 0.5 else ("premium" if path < 0.5 else "even")


def build(as_of: Optional[str] = None,
          store: Optional[observations.ObservationStore] = None) -> dict:
    """The block's payload, as-of the cutoff. Descriptive: nothing in it is a state."""
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    own = store is None
    st = store or observations.ObservationStore()
    try:
        windows: dict[str, Any] = {}
        for w in WINDOWS:
            move = _read(MOVE.format(w=w), cutoff, st)
            cuts = {}
            for name, key in (("real_share", REAL), ("curve_share", CURVE)):
                r = _read(key.format(w=w), cutoff, st)
                # A cut from another session is another window's number.
                if r["level"] is not None and r.get("as_of") != move.get("as_of"):
                    r["level"] = None
                    r["absent_reason"] = (
                        f"{r['metric']} was last written {r.get('as_of')}, not on "
                        f"the move's session {move.get('as_of')} (a move under "
                        f"5bp writes no share)")
                cuts[name] = r
            models = []
            for m in MODELS:
                r = _read(m["share"].format(w=w), cutoff, st)
                row: dict[str, Any] = {"model": m["model"], "label": m["label"],
                                       "split": m["split"], "metric": r["metric"],
                                       "as_of": r.get("as_of")}
                if r["level"] is None:
                    row["absent_reason"] = r.get("absent_reason")
                    if r.get("fault"):
                        row["fault"] = r["fault"]
                else:
                    path = r["level"] if m["is_path"] else 1.0 - r["level"]
                    row.update({"path_share": round(path, 4),
                                "premium_share": round(1.0 - path, 4),
                                "lean": _lean(path)})
                    src = _read(m["source"], cutoff, st)
                    if src.get("as_of") and r.get("as_of") \
                            and src["as_of"] > r["as_of"]:
                        row["note"] = (
                            f"not written since {r['as_of']}; {m['label']} printed "
                            f"through {src['as_of']} (its {w}-observation move since "
                            f"has been under 5bp, or an input was missing)")
                models.append(row)
            present = [r for r in models if r.get("lean")]
            leans = {r["lean"] for r in present}
            if len(present) < 2:
                agreement = {"assessable": False, "models_present": len(present),
                             "text": (f"agreement not assessable: "
                                      f"{len(present)} model(s) present")}
            elif len(leans) == 1 and "even" not in leans:
                side = leans.pop()
                agreement = {"assessable": True, "agree": True, "lean": side,
                             "models_present": len(present),
                             "text": f"models agree: {side}-led "
                                     f"({len(present)} of {len(MODELS)})"}
            else:
                agreement = {"assessable": True, "agree": False,
                             "models_present": len(present),
                             "text": "models disagree: " + ", ".join(
                                 f"{r['label']} {r['lean']}" for r in present)}
            windows[str(w)] = {"window": w, "move": move, **cuts,
                               "models": models, "agreement": agreement}
        return {"block": "rates_attribution", "as_of": cutoff,
                "descriptive": True, "windows": windows}
    finally:
        if own:
            st.close()


def _f(x: Any, fmt: str) -> str:
    return "—" if x is None else fmt.format(x)


def render(block: dict) -> list[str]:
    """The block as printed lines. Every absence says why; every share its date."""
    L = [f"RATES ATTRIBUTION — descriptive, no state (as of {block['as_of'][:10]})"]
    for w, win in block["windows"].items():
        mv, rs, cs = win["move"], win["real_share"], win["curve_share"]
        head = f"  {w} sessions: "
        if mv["level"] is None:
            head += f"10y move absent — {mv.get('absent_reason') or 'fault recorded'}"
        else:
            head += (f"10y {mv['level']:+.0f}bp to {mv.get('as_of')}"
                     f" · real share {_f(rs['level'], '{:.2f}')}"
                     f" · curve share {_f(cs['level'], '{:.2f}')}")
        L.append(head)
        for r in win["models"]:
            name = f"{r['label']} ({r['split']})"
            if r.get("lean"):
                line = (f"    {name:22} path {r['path_share']:.2f} / premium "
                        f"{r['premium_share']:.2f}   as of {r['as_of']}   "
                        f"leans {r['lean']}")
                if r.get("note"):
                    line += f"   [{r['note']}]"
            else:
                why = r.get("absent_reason") or "a reader fault, see its `fault` field"
                line = f"    {name:22} absent — {why}"
            L.append(line)
        L.append(f"    {win['agreement']['text']}")
    return L


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="The rates attribution block.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("--as-of", default=None)
    s.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    b = build(as_of=a.as_of)
    if a.json:
        print(json.dumps(b, indent=2, sort_keys=True, default=str))
    else:
        print("\n".join(render(b)))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))

"""
Cross-check: our computed profile against FlashAlpha Basic's published levels.

FlashAlpha is the *independent check* on our own computation, not a data
source. Its Basic tier serves no per-strike data at all (see TODO.md, probe
verdict 4 Sep), so it cannot feed the logger -- but /v1/exposure/levels returns
a handful of derived levels computed from its own settled-OI book, which is
exactly what an independent check needs: same question, different data, different
code.

WHAT DIVERGENCE MEANS. These two numbers are not expected to be identical and a
gap is not automatically our bug:

  - different OI vintage (theirs settled from their feed; ours from the yfinance
    chain at fetch time)
  - different spot at computation time
  - different greeks (ours Black-Scholes from chain IV, theirs undisclosed)
  - possibly different sign convention -- theirs is not published

So this logs divergence, in strike points and percent, and never "corrects"
our number toward theirs. A persistent gap is a question to investigate, and
the log is what makes "persistent" visible instead of anecdotal.

FIELD MAPPING is empirical, not documented. Observed on the 4 Sep snapshot:
our call_wall / put_wall equal their max_positive_gamma / max_negative_gamma,
while their separately-named call_wall / put_wall track different levels. Both
readings are compared, and the mapping note travels with every record, because
guessing which of their fields means what is the most likely way to draw a
false conclusion here.

THEIR PER-STRIKE TABLE IS NOT A REFERENCE FOR ANYTHING. The Basic tier serves no
per-strike data the logger could use, and what it does show cannot be trusted as a
yardstick: the observed table carried a strike of 8000 on SPY, an instrument
trading near 760. That is an index-scale strike on an ETF, so either the table
mixes SPX-scale contracts into an SPY view or it is simply wrong -- and either way
nothing here may treat it as the reference. Only the derived LEVELS are compared,
and even those are compared as an independent opinion rather than as truth.

DEX IS COMPARED AND FLAGGED UNRECONCILED, WHICH IS NOT THE SAME AS BROKEN.
A divergence is only interpretable once both sides agree on what the number
MEANS, and for delta exposure neither side's definition is pinned down on any of
the four axes that change the answer -- sign convention, which contracts are
included, any moneyness filter, and the OI vintage. DEFINITION_AUDIT below records
the state of each axis. Until all four close, every DEX row carries
`definition_unreconciled` so nobody reads a gap as a finding, and the
reconciliation itself is the work rather than the number.

Our own sign convention is the clearest case: under `dealers-hand-v1` customers
sell calls and buy puts, so dealers are long calls and short puts -- and BOTH legs
carry positive delta. Net DEX is therefore positive for every symbol, bucket and
expiry by construction (269 of 269 rows on the first backfill, with no negative
possible in principle). Magnitude, dating and day-over-day change are the signal;
direction is not. Whether the vendor signs the same way is undisclosed, so a
sign-level agreement between us would prove nothing anyway.

Cost: one API call per symbol per run, against a 250/day Basic quota.

Usage:
    python tools/cross_check.py                    # SPY, QQQ
    python tools/cross_check.py --symbols SPY QQQ IWM
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from altdata import config   # noqa: E402
from altdata import session  # noqa: E402
import exposure_compute     # noqa: E402

log = logging.getLogger(__name__)

DEFAULT_SYMBOLS = ["SPY", "QQQ"]
LEVELS_PATH = "/v1/exposure/levels/{symbol}"
CROSS_CHECK_DIR = "data/cross_check"
TIMEOUT = 30

# ours (dotted, within the computed profile) -> theirs (within levels{})
# Two comparisons per wall: their identically-named field, and the field that
# empirically matches ours. Both are logged; neither is assumed correct.
COMPARISONS = [
    ("gamma_flip",      "overall.gamma_flip",       "gamma_flip"),
    ("call_wall",       "overall.call_wall",        "call_wall"),
    ("call_wall_maxpos", "overall.call_wall",       "max_positive_gamma"),
    ("put_wall",        "overall.put_wall",         "put_wall"),
    ("put_wall_maxneg", "overall.put_wall",         "max_negative_gamma"),
    # Which definition does their put_wall actually track?
    ("put_wall_gamma",  "overall.put_wall_gamma",   "put_wall"),
    ("put_wall_oi",     "overall.put_wall_oi",      "put_wall"),
    ("put_wall_otm",    "overall.put_wall_otm",     "put_wall"),
    ("call_wall_otm",   "overall.call_wall_otm",    "call_wall"),
    ("magnet",          "max_pain",                 "zero_dte_magnet"),
    ("peak_gex_vs_oi",  "overall.peak_abs_gex_strike", "highest_oi_strike"),
    # DELTA EXPOSURE. Two shapes, because a vendor may publish either and the
    # two are not interchangeable: shares is the hedge in units of underlying,
    # notional is that times spot. Comparing one against the other would produce
    # a divergence of the size of the spot price and read as a catastrophic
    # disagreement rather than as a units mistake.
    ("dex_shares",      "overall.dex_shares",       "dex_shares"),
    ("dex_notional",    "overall.dex_notional",     "dex_notional"),
]

# THE DEFINITIONAL AUDIT. Four axes, because each one independently changes the
# number, and a divergence is uninterpretable until all four are pinned on both
# sides. `ours` is knowable from our own code; `theirs` is knowable only if the
# vendor documents it, and Basic documents none of this. A level with any axis
# unresolved is reported `definition_unreconciled` and its divergence is NOT a
# finding.
#
# Written as data rather than prose so the flag is computed from the same thing a
# human reads, and closing an axis is a one-line edit that immediately shows up in
# the output.
DEFINITION_AUDIT = {
    "dex_shares": {
        "sign_convention": {
            "ours": "dealers-hand-v1: dealers long calls, short puts. BOTH legs "
                    "carry positive delta, so net DEX is positive by "
                    "construction -- direction is uninformative, magnitude is "
                    "the signal.",
            "theirs": "undisclosed on Basic.",
            "state": "unresolved",
        },
        "contracts_included": {
            "ours": "settled_0dte_rule = exclude_dte0_from_exposure_aggregates_v1"
                    " -- a settled profile computes no 0DTE greeks at all, so "
                    "same-day expiries are out of the aggregate entirely.",
            "theirs": "undisclosed; unknown whether 0DTE is included.",
            "state": "unresolved",
        },
        "moneyness_filter": {
            "ours": "none applied to DEX. (Our *_otm wall variants exist for the "
                    "walls, not for delta.)",
            "theirs": "undisclosed.",
            "state": "unresolved",
        },
        "oi_vintage": {
            "ours": "the settled 16:10 yfinance chain snapshot; fetched_at is on "
                    "every profile.",
            "theirs": "their own settled-OI feed at their node; as_of and node are "
                      "logged per record but the feed is not described.",
            "state": "unresolved",
        },
    },
}
# dex_notional inherits the audit: it is dex_shares times spot, so every axis
# that governs one governs the other, and duplicating the table would let the two
# drift into disagreeing about their own definition.
DEFINITION_AUDIT["dex_notional"] = DEFINITION_AUDIT["dex_shares"]

PER_STRIKE_CAVEAT = (
    "FlashAlpha Basic's per-strike table is NOT the reference: the observed "
    "table carried a strike of 8000 on SPY, an instrument trading near 760. "
    "Only derived levels are compared here, and only as an independent opinion.")


def definition_state(level: str) -> tuple[bool, list[str]]:
    """(unreconciled, the axes still open) for one compared level."""
    audit = DEFINITION_AUDIT.get(level)
    if not audit:
        # No audit entry means no axis was ever in question for this level --
        # a strike price is a strike price. Absence is not an open question.
        return False, []
    open_axes = [k for k, v in audit.items() if v.get("state") != "resolved"]
    return bool(open_axes), open_axes

MAPPING_NOTE = ("Field mapping is empirical, not vendor-documented. Their "
                "call_wall/put_wall and max_positive_gamma/max_negative_gamma "
                "are compared separately against our single call_wall/put_wall.")


def _dig(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _creds() -> tuple[Optional[str], Optional[str]]:
    """(key, base) through the one loader. A placeholder counts as unconfigured.

    This was a FIFTH copy of the .env parser -- the gate found it after I had
    already "found them all" by grepping for the obvious shapes, which is the
    argument for the gate rather than for the grep.
    """
    from altdata import secrets
    if not secrets.present("FLASHALPHA_API_KEY") or not secrets.present(
            "FLASHALPHA_BASE_URL"):
        return None, None
    return secrets.get("FLASHALPHA_API_KEY"), secrets.get(
        "FLASHALPHA_BASE_URL").rstrip("/")


def fetch_levels(symbol: str, key: str, base: str) -> dict:
    """One vendor call. Never raises -- a failed check is a logged gap."""
    url = f"{base}{LEVELS_PATH.format(symbol=symbol)}"
    try:
        r = requests.get(url, headers={"X-Api-Key": key, "Accept": "application/json"},
                         timeout=TIMEOUT)
        out = {"status": r.status_code,
               "quota_remaining": r.headers.get("X-RateLimit-Remaining"),
               "quota_limit": r.headers.get("X-RateLimit-Limit")}
        try:
            out["body"] = r.json()
        except ValueError:
            out["body"] = {"__non_json__": r.text[:500]}
        return out
    except Exception as e:  # noqa: BLE001
        return {"status": None, "error": f"{type(e).__name__}: {e}", "body": {}}


def compare(symbol: str, ours: dict, theirs: dict) -> dict:
    """Divergence per level, in strike points and percent of our spot."""
    body = theirs.get("body") or {}
    levels = body.get("levels") or {}
    our_spot = ours.get("spot")
    their_spot = body.get("underlying_price")

    rows = []
    for name, our_path, their_key in COMPARISONS:
        o, t = _dig(ours, our_path), levels.get(their_key)
        o = o if isinstance(o, (int, float)) else None
        t = t if isinstance(t, (int, float)) else None
        diff = pct = None
        if o is not None and t is not None:
            diff = round(o - t, 4)
            ref = our_spot or o
            pct = round((o - t) / ref * 100.0, 4) if ref else None
        unreconciled, open_axes = definition_state(name)
        rows.append({
            "level": name, "ours": o, "theirs": t,
            "diff_strike_points": diff, "diff_pct_of_spot": pct,
            "agree": (None if o is None or t is None else abs(diff) < 1e-9),
            "missing": ("ours" if o is None and t is not None else
                        "theirs" if t is None and o is not None else
                        "both" if o is None and t is None else None),
            # A divergence on an unreconciled definition is not a finding, and
            # the flag travels on the ROW so it cannot be separated from the
            # number it qualifies.
            "definition_unreconciled": unreconciled,
            "definition_open_axes": ";".join(open_axes) if open_axes else None,
        })

    return {
        "symbol": symbol,
        "checked_at": session.utc_iso(),
        "our_spot": our_spot,
        "their_spot": their_spot,
        "spot_diff": (round(our_spot - their_spot, 4)
                      if isinstance(our_spot, (int, float))
                      and isinstance(their_spot, (int, float)) else None),
        "our_fetched_at": ours.get("fetched_at"),
        "their_as_of": body.get("as_of"),
        "their_node": (body.get("data_as_of") or {}).get("node"),
        "their_oi_feed": (body.get("data_as_of") or {}).get("oi_feed"),
        "our_convention": ours.get("convention_version"),
        "vendor_status": theirs.get("status"),
        "quota_remaining": theirs.get("quota_remaining"),
        "mapping_note": MAPPING_NOTE,
        "per_strike_caveat": PER_STRIKE_CAVEAT,
        "definition_audit": DEFINITION_AUDIT,
        "levels": rows,
    }


def write_results(results: list[dict], out_dir: Optional[str] = None) -> tuple[Path, Path]:
    day = session.session_date()
    d = Path(out_dir or CROSS_CHECK_DIR) / day
    d.mkdir(parents=True, exist_ok=True)
    stamp = session.utc_stamp("%H%M%SZ")

    json_path = d / f"cross_check_{stamp}.json"
    json_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    csv_path = Path(out_dir or CROSS_CHECK_DIR) / "divergence_log.csv"
    cols = ["checked_at", "symbol", "level", "ours", "theirs",
            "diff_strike_points", "diff_pct_of_spot", "agree", "missing",
            "our_spot", "their_spot", "spot_diff", "their_node", "vendor_status",
            # Appended, never inserted: the log is append-only and a reader of
            # the old rows must not have its columns shift underneath it. Rows
            # written before this lands carry empty cells, which is the honest
            # reading -- the flag did not exist then.
            "definition_unreconciled", "definition_open_axes"]
    exists = csv_path.exists()
    with csv_path.open("a", encoding="utf-8", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=cols, extrasaction="ignore")
        if not exists:
            w.writeheader()
        for res in results:
            for lv in res["levels"]:
                w.writerow({**{k: res.get(k) for k in cols}, **lv})
    return json_path, csv_path


def run(symbols: Optional[list[str]] = None, out_dir: Optional[str] = None) -> list[dict]:
    key, base = _creds()
    if not key:
        log.warning("FlashAlpha credentials unavailable -- cross-check skipped")
        return []
    syms = symbols or DEFAULT_SYMBOLS
    computed = {s: c for s, c in exposure_compute.run(symbols=syms).items()}
    results = []
    for s in syms:
        ours = computed.get(s)
        if not ours or ours.get("error"):
            log.warning("no computed profile for %s -- skipping", s)
            continue
        results.append(compare(s, ours, fetch_levels(s, key, base)))
    if results:
        write_results(results, out_dir)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-check our GEX vs FlashAlpha")
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    for st in (sys.stdout, sys.stderr):
        if hasattr(st, "reconfigure"):
            st.reconfigure(encoding="utf-8", errors="replace")

    results = run(args.symbols, args.out_dir)
    if not results:
        print("No cross-check produced (missing credentials or computed profiles).")
        return 1

    for res in results:
        print(f"\n{res['symbol']}  our spot {res['our_spot']}  "
              f"their spot {res['their_spot']}  (diff {res['spot_diff']})")
        print(f"  their node={res['their_node']} oi_feed={res['their_oi_feed']} "
              f"quota_left={res['quota_remaining']}")
        print(f"  {'level':<18} {'ours':>10} {'theirs':>10} {'diff':>10} {'%spot':>8}")
        for lv in res["levels"]:
            f = lambda v, w=10: (f"{v:>{w},.2f}" if isinstance(v, (int, float)) else f"{'-':>{w}}")
            flag = "" if lv["agree"] is not False else "  <-- diverges"
            if lv["missing"]:
                flag = f"  <-- missing: {lv['missing']}"
            # THE FLAG OUTRANKS THE DIVERGENCE NOTE, because it changes what the
            # divergence MEANS. "diverges" invites investigation of the numbers;
            # "definition unreconciled" says the numbers are not yet comparable
            # and the work is the definition, not the gap.
            if lv.get("definition_unreconciled"):
                flag = "  <-- DEFINITION UNRECONCILED"
            print(f"  {lv['level']:<18} {f(lv['ours'])} {f(lv['theirs'])} "
                  f"{f(lv['diff_strike_points'])} {f(lv['diff_pct_of_spot'], 8)}{flag}")

        open_now = sorted({a for lv in res["levels"]
                           for a in (lv.get("definition_open_axes") or "").split(";")
                           if a})
        if open_now:
            print(f"\n  DEFINITION AUDIT -- {len(open_now)} axis/axes still open, "
                  f"so any DEX gap above is NOT a finding:")
            for axis, v in DEFINITION_AUDIT["dex_shares"].items():
                mark = "OK  " if v.get("state") == "resolved" else "OPEN"
                print(f"    [{mark}] {axis}")
                print(f"           ours  : {v['ours']}")
                print(f"           theirs: {v['theirs']}")
        print(f"\n  {PER_STRIKE_CAVEAT}")
    print(f"\n  written: {CROSS_CHECK_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

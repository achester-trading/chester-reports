"""
Signal-triage Batch 15, item 74 (written as 67; ST-R6.74a, 74b): the hedge-fund
positioning line, the squeeze-risk flag and the short-extremes ledger -- report
only.

    from altdata import hf_positioning as hf
    r = hf.read(st, cutoff)
    hf.lines(r); hf.table(r)
    f = hf.squeeze(r, depth)          # depth: item 71's read (altdata/fragility.py)
    hf.es_line(f)
    python -m altdata.hf_positioning show [--as-of D]

THE LINE. The CFTC's Traders in Financial Futures, leveraged funds, net, in the
E-mini S&P 500 (ES) and Nasdaq-100 (NQ) futures, weekly, as altdata/sources/cftc.py
stores them: net contracts, the net as a share of open interest, and the NET SHORT
share's dual percentiles (five years and the full stored history, each with its
n). FINRA's short interest as a share of float and a performance proxy failed the
source checks and print as listed gaps; the prime-book figures are a dated record,
never a line (G3).

THE FLAG. ES's net short at or above its 90th percentile of five years while item
71's depth is below its 10th -- its stand-in, SPY's Amihud illiquidity, at or
above its 90th. Either arm unread prints "not read". A flag's rights only: no
composite and no market-state object reads it.

THE LEDGER (ST-R6.74b), pre-registered in
docs/ledgers/short-extremes-preregistration-2026-10.md before this code:
`ledger(net_oi, spx)` applies that file's rule to stored series; the script
tools/calibration/st_r6_74b_short_extremes.py writes each edition.
"""

from __future__ import annotations

import datetime as dt
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

from . import st_r5_rates as rt

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "hf_positioning.yaml"
PREREG = REPO / "docs" / "ledgers" / "short-extremes-preregistration-2026-10.md"
PREREG_SHA256 = "584442322783b3cf85ca6bb16c4a08b705ec36c8360f8323dcb4233273f90211"

# The pre-registered rule (the file above; never changed here without a new one).
RULE = {"window": 260, "min_ranked": 156, "extreme_pct": 90.0, "quiet_weeks": 4,
        "horizons": (5, 20), "min_episodes": 12, "median_lift_pp": 1.0,
        "share_positive": 0.60}


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def _gap(text: str) -> str:
    return " ".join(str(text).split())


# ---------------------------------------------------------------------------
# The line
# ---------------------------------------------------------------------------
def contract_read(net: list, net_oi: list, years: int) -> dict:
    """One contract's latest report: net contracts, net share of OI and the net
    short share's dual percentiles."""
    if not net_oi:
        return {"state": "absent", "reason": "not stored yet (the TFF pull adds ES "
                                             "and NQ from this build)"}
    day, share = net_oi[-1]
    short = [(d, -v) for d, v in net_oi]
    lz = rt.lens(short, years)
    nd = dict(net)
    return {"state": "computed", "as_of": day, "net": nd.get(day),
            "net_oi_pct": share, "short_oi_pct": -share, "lens": lz,
            "lens_text": rt.lens_text(lz)}


def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    years = int(cfg.get("lens_years", 5))
    out = []
    for c in cfg["contracts"]:
        net = rt._pts(st, cfg["net_key"], cutoff, c["instrument"])       # noqa: SLF001
        oi = rt._pts(st, cfg["net_oi_key"], cutoff, c["instrument"])     # noqa: SLF001
        out.append({**c, **contract_read(net, oi, years)})
    return {"as_of": cutoff, "contracts": out, "years": years,
            "gaps": {k: _gap(v) for k, v in (cfg.get("gaps") or {}).items()},
            "squeeze_cfg": cfg.get("squeeze") or {}}


def contract_line(c: dict) -> str:
    if c["state"] != "computed":
        return f"{c['label']} ({c['instrument']}): leveraged funds {c['reason']}."
    net = "—" if c.get("net") is None else f"{c['net']:+,.0f} contracts"
    return (f"{c['label']} ({c['instrument']}): leveraged funds net {net} "
            f"({c['net_oi_pct']:+.1f}% of open interest, report of {c['as_of']}); "
            f"the net short share at the {c['lens_text']}.")


def lines(r: dict) -> list[str]:
    out = [contract_line(c) for c in r["contracts"]]
    out.append(r["gaps"]["short_interest"] + ".")
    out.append(r["gaps"]["performance"] + ".")
    return out


def table(r: dict) -> dict:
    rows = []
    for c in r["contracts"]:
        if c["state"] != "computed":
            rows.append([c["label"], "—", "—", c["reason"], "—"])
            continue
        lz = c["lens"]
        rows.append([c["label"],
                     "—" if c.get("net") is None else f"{c['net']:+,.0f}",
                     f"{c['net_oi_pct']:+.1f}%",
                     f"{rt.ordinal(lz['percentile_window'])} of {r['years']} years "
                     f"(n={lz['n_window']:,}); {rt.ordinal(lz['percentile_full'])} "
                     f"since {lz['from']} (n={lz['n_full']:,})",
                     c["as_of"]])
    return {"columns": ["Contract", "Leveraged funds, net contracts",
                        "Net, share of open interest", "Net short share, percentile",
                        "Report"], "rows": rows}


# ---------------------------------------------------------------------------
# The squeeze-risk flag
# ---------------------------------------------------------------------------
def squeeze(r: dict, depth: Optional[dict]) -> dict:
    """ES's net short arm and item 71's depth arm (the Amihud stand-in, where a
    higher reading is less depth). `depth` is fragility's depth read (its
    "amihud" entry), or None."""
    sc = r["squeeze_cfg"]
    nsp, dp = float(sc.get("net_short_pct", 90)), float(sc.get("depth_pct", 10))
    c = next((x for x in r["contracts"] if x["instrument"] == sc.get("arm_instrument", "ES")),
             None)
    arm_s = (None if not c or c["state"] != "computed" else
             (c["lens"].get("percentile_window") or 0) >= nsp)
    am = (depth or {}).get("amihud") or {}
    am_p = (am.get("lens") or {}).get("percentile_window") if am.get("state") == "computed" else None
    arm_d = None if am_p is None else am_p >= 100.0 - dp
    state = ("not read" if arm_s is None or arm_d is None else
             "on" if arm_s and arm_d else "off")
    s_txt = ("not read" if arm_s is None else
             f"ES's net short at the {rt.ordinal(c['lens']['percentile_window'])} "
             f"percentile of {r['years']} years ({'at or above' if arm_s else 'below'} "
             f"the {rt.ordinal(nsp)})")
    d_txt = ("not read" if arm_d is None else
             f"depth (the Amihud measure, standing in for it) at its "
             f"{rt.ordinal(100.0 - am_p if am_p is not None else None)} percentile "
             f"({'below' if arm_d else 'not below'} the {rt.ordinal(dp)})")
    word = {"on": "ON", "off": "off", "not read": "not read"}[state]
    return {"state": state, "on": state == "on", "short_arm": arm_s, "depth_arm": arm_d,
            "line": (f"The squeeze-risk flag is {word}: {s_txt}; {d_txt}. Report only; "
                     f"no composite, and no right before the short-extremes ledger.")}


def es_line(f: dict) -> str:
    """Item 45's levels read: one context line."""
    return f"Squeeze risk: {f['line']}"


# ---------------------------------------------------------------------------
# The ledger (ST-R6.74b), the pre-registered rule
# ---------------------------------------------------------------------------
def release_day(tuesday: str) -> str:
    return (dt.date.fromisoformat(tuesday) + dt.timedelta(days=3)).isoformat()


def _percentile_at(vals: list[float], x: float) -> float:
    from . import derived                                       # noqa: PLC0415
    return derived.percentile_of(vals, x)


def episodes(net_oi: list[tuple[str, float]], spx: list[tuple[str, float]],
             rule: Optional[dict] = None) -> dict:
    """The ranked weeks, the episodes and every ranked week's outcomes, by the
    pre-registered rule. Inputs are (day, value) sorted ascending."""
    rule = rule or RULE
    w, mr = int(rule["window"]), int(rule["min_ranked"])
    short = [(d, -v) for d, v in net_oi]
    days = [d for d, _ in spx]
    closes = [v for _, v in spx]
    import bisect                                               # noqa: PLC0415

    def outcome(entry_idx: int, h: int) -> Optional[float]:
        j = entry_idx + h
        if j >= len(closes):
            return None
        return round((closes[j] / closes[entry_idx] - 1) * 100.0, 4)

    ranked, eps = [], []
    quiet = 0
    for i in range(len(short)):
        if i + 1 < mr:
            continue
        d, x = short[i]
        win = [v for _, v in short[max(0, i + 1 - w):i + 1]]
        p = _percentile_at(win, x)
        extreme = p >= float(rule["extreme_pct"])
        rel = release_day(d)
        k = bisect.bisect_left(days, rel)
        row = {"week": d, "release": rel, "short_oi_pct": round(x, 4),
               "percentile": p, "extreme": extreme,
               "entry": days[k] if k < len(days) else None}
        for h in rule["horizons"]:
            row[f"r{h}"] = outcome(k, h) if k < len(days) else None
        ranked.append(row)
        if extreme and quiet >= int(rule["quiet_weeks"]):
            eps.append(row)
        quiet = 0 if extreme else quiet + 1
    return {"ranked": ranked, "episodes": eps}


def verdict(ev: dict, rule: Optional[dict] = None) -> dict:
    rule = rule or RULE
    hl = max(rule["horizons"])
    hs = min(rule["horizons"])
    counted = [e for e in ev["episodes"] if e.get(f"r{hl}") is not None]
    pending = len(ev["episodes"]) - len(counted)
    base = [r for r in ev["ranked"] if r.get(f"r{hl}") is not None]

    def med(xs, h):
        v = [x[f"r{h}"] for x in xs if x.get(f"r{h}") is not None]
        return None if not v else round(statistics.median(v), 4)

    out: dict[str, Any] = {
        "n": len(counted), "pending": pending, "baseline_n": len(base),
        "median_long": med(counted, hl), "median_short": med(counted, hs),
        "baseline_long": med(base, hl), "baseline_short": med(base, hs),
        "share_positive": (None if not counted else
                           round(sum(1 for e in counted if e[f"r{hl}"] > 0) / len(counted), 4)),
        "window": (ev["ranked"][0]["week"], ev["ranked"][-1]["week"]) if ev["ranked"] else None}
    if len(counted) < int(rule["min_episodes"]):
        out["verdict"] = "INSUFFICIENT"
    else:
        lift = out["median_long"] - out["baseline_long"]
        out["lift_pp"] = round(lift, 4)
        ok = lift >= float(rule["median_lift_pp"]) and \
            out["share_positive"] >= float(rule["share_positive"])
        out["verdict"] = "PASS" if ok else "FAIL"
    return out


def ledger(net_oi: list, spx: list, rule: Optional[dict] = None) -> dict:
    ev = episodes(net_oi, spx, rule)
    return {**ev, "result": verdict(ev, rule)}


def prereg_sha256(path: Optional[Path] = None) -> str:
    import hashlib                                              # noqa: PLC0415
    b = Path(path or PREREG).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415

    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.hf_positioning")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="print the line and the flag as of a cutoff (read-only)")
    s.add_argument("--as-of")
    s.add_argument("--db")
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso()
    with observations.ObservationStore(a.db) as st:
        r = read(st, cutoff)
        from . import fragility                                 # noqa: PLC0415
        spy = rt._pts(st, fragility.config()["spy"]["close"], cutoff)  # noqa: SLF001
        depth = (fragility.build(st, spy[-1][0], cutoff)["depth"] if spy else None)
    for ln in lines(r) + [squeeze(r, depth)["line"]]:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

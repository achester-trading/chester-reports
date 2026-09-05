"""
Data-quality gates over a stored option chain.

The architecture is blunt about why these exist: "Nothing else in the system
catches a bad options day." Every number downstream -- GEX, flip, walls, max
pain, and the pin rate they all feed -- is computed from whatever the free feed
returned that night. Without a gate, a night of stale or illiquid quotes enters
the base rate looking identical to a clean one, and the base rate is the entire
point of the exercise.

Four gates, all computable from the stored chain. No new data.

    liquidity_floor    HARD RULE. Total OI and total volume must clear declared
                       thresholds. Below them the symbol is excluded, not
                       downgraded: "confident-looking percentiles on thin books
                       are worse than no metric."

    iv_dispersion      Surface roughness. A well-quoted surface is smooth across
                       adjacent strikes; a jagged one means stale or illiquid
                       marks. Measured as the mean absolute second difference of
                       IV across adjacent strikes within an expiry, normalised by
                       mean IV, then taken as the median across expiries. This is
                       a DATA-QUALITY gate, not an analytic -- a rough surface
                       downgrades confidence in everything derived that day.

    oi_concentration   Herfindahl index over per-strike OI share. High values
                       mean positioning sits in few strikes, so the regime
                       changes discontinuously rather than decaying. Reported as
                       a value, not a pass/fail: concentration is a property of
                       the book, not a defect in the data.

    oi_weighted_dte    OI-weighted days to expiry. One number for whether
                       positioning is short or long dated. Informational.

VERDICT, written onto every symbol:

    ok         both gates pass
    degraded   liquidity passes, IV surface is rough -- usable, trust less
    excluded   liquidity floor failed; the symbol must not enter skew or
               OI-percentile work at all

THRESHOLD HONESTY. The liquidity thresholds are declared a priori in config.
The IV-roughness threshold is provisional: a normalised roughness figure has no
natural scale, and calibrating it against the same 13 symbols it will judge
would be circular. It is set to a defensible starting value and the observed
distribution is reported, so it can be calibrated once a real sample exists.
Until then a `degraded` verdict is a prompt to look, not a proof of a bad day.

Usage:
    python tools/quality_gates.py                 # newest stored chains
    python tools/quality_gates.py --date 2026-09-04 --write-manifests
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from altdata import config   # noqa: E402
from altdata import session  # noqa: E402

log = logging.getLogger(__name__)

MIN_STRIKES_FOR_ROUGHNESS = 5      # below this a curvature estimate is noise


# ---------------------------------------------------------------------------
# Individual gates
# ---------------------------------------------------------------------------

def liquidity_floor(rows: list[dict]) -> dict:
    """HARD RULE. Total OI and volume against declared thresholds.

    Also reports median relative bid/ask spread, which the architecture prefers
    as a tightness measure, so the gate can be moved onto spread once there is
    enough history to set a threshold for it.
    """
    total_oi = sum(r.get("open_interest") or 0.0 for r in rows)
    total_vol = sum(r.get("volume") or 0.0 for r in rows)

    spreads = []
    for r in rows:
        bid, ask = r.get("bid"), r.get("ask")
        if bid and ask and ask > 0 and ask >= bid:
            mid = (bid + ask) / 2.0
            if mid > 0:
                spreads.append((ask - bid) / mid)
    med_spread = round(statistics.median(spreads), 4) if spreads else None

    oi_ok = total_oi >= config.LIQUIDITY_MIN_TOTAL_OI
    vol_ok = total_vol >= config.LIQUIDITY_MIN_TOTAL_VOLUME
    reasons = []
    if not oi_ok:
        reasons.append(f"total OI {total_oi:,.0f} < {config.LIQUIDITY_MIN_TOTAL_OI:,}")
    if not vol_ok:
        reasons.append(f"total volume {total_vol:,.0f} < {config.LIQUIDITY_MIN_TOTAL_VOLUME:,}")

    return {
        "pass": oi_ok and vol_ok,
        "total_oi": total_oi,
        "total_volume": total_vol,
        "median_rel_spread": med_spread,
        "thresholds": {"min_total_oi": config.LIQUIDITY_MIN_TOTAL_OI,
                       "min_total_volume": config.LIQUIDITY_MIN_TOTAL_VOLUME},
        "reasons": reasons,
    }


def iv_dispersion(rows: list[dict]) -> dict:
    """Surface roughness: normalised mean |second difference| of IV by strike.

    Computed per expiry over calls and puts separately (their skews differ, so
    mixing them manufactures roughness that is not there), then the median
    across all series is taken as the symbol's figure.
    """
    series: dict[tuple, list[tuple[float, float]]] = defaultdict(list)
    for r in rows:
        iv, k = r.get("implied_vol"), r.get("strike")
        if iv and k and 0 < iv < 5.0:
            series[(r.get("expiry"), r.get("right"))].append((k, iv))

    per_series = []
    for key, pts in series.items():
        if len(pts) < MIN_STRIKES_FOR_ROUGHNESS:
            continue
        pts.sort()
        ivs = [v for _, v in pts]
        mean_iv = sum(ivs) / len(ivs)
        if mean_iv <= 0:
            continue
        second = [abs(ivs[i - 1] - 2 * ivs[i] + ivs[i + 1])
                  for i in range(1, len(ivs) - 1)]
        if second:
            per_series.append((sum(second) / len(second)) / mean_iv)

    if not per_series:
        return {"pass": None, "roughness": None, "series_measured": 0,
                "threshold": config.IV_ROUGHNESS_MAX,
                "reason": "too few strikes per expiry to measure"}

    rough = round(statistics.median(per_series), 5)
    return {
        "pass": rough <= config.IV_ROUGHNESS_MAX,
        "roughness": rough,
        "roughness_p90": round(statistics.quantiles(per_series, n=10)[-1], 5)
                         if len(per_series) >= 10 else None,
        "series_measured": len(per_series),
        "threshold": config.IV_ROUGHNESS_MAX,
        "threshold_status": "provisional -- needs calibration against a real sample",
    }


def oi_concentration(rows: list[dict]) -> dict:
    """Herfindahl index over per-strike OI share (1/N .. 1)."""
    by_strike: dict[float, float] = defaultdict(float)
    for r in rows:
        oi, k = r.get("open_interest") or 0.0, r.get("strike")
        if k and oi > 0:
            by_strike[k] += oi
    total = sum(by_strike.values())
    if total <= 0 or not by_strike:
        return {"hhi": None, "strikes": 0, "top_strike": None}
    shares = [v / total for v in by_strike.values()]
    hhi = round(sum(s * s for s in shares), 6)
    top = max(by_strike.items(), key=lambda kv: kv[1])
    return {
        "hhi": hhi,
        "strikes": len(by_strike),
        "effective_strikes": round(1.0 / hhi, 2) if hhi else None,
        "top_strike": top[0],
        "top_strike_oi_share": round(top[1] / total, 4),
    }


def oi_weighted_dte(rows: list[dict]) -> dict:
    """OI-weighted days to expiry."""
    num = den = 0.0
    for r in rows:
        oi, d = r.get("open_interest") or 0.0, r.get("dte")
        if oi > 0 and d is not None:
            num += oi * max(d, 0)
            den += oi
    return {"oi_weighted_dte": round(num / den, 2) if den else None,
            "oi_total": den}


# ---------------------------------------------------------------------------
# Combined verdict
# ---------------------------------------------------------------------------

def evaluate(rows: list[dict]) -> dict:
    """Run all four gates and return the combined record."""
    liq = liquidity_floor(rows)
    ivd = iv_dispersion(rows)
    hhi = oi_concentration(rows)
    wdte = oi_weighted_dte(rows)

    if not liq["pass"]:
        verdict = "excluded"
    elif ivd.get("pass") is False:
        verdict = "degraded"
    else:
        verdict = "ok"

    return {
        "evaluated_at": session.utc_iso(),
        "data_quality": verdict,
        "usable_for_percentiles": liq["pass"],
        "liquidity_floor": liq,
        "iv_dispersion": ivd,
        "oi_concentration": hhi,
        "oi_weighted_dte": wdte,
    }


# ---------------------------------------------------------------------------
# CLI / backfill
# ---------------------------------------------------------------------------

def _f(v):
    try:
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def load_chain(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fp:
        for rec in csv.DictReader(fp):
            rows.append({
                "expiry": rec.get("expiry"),
                "right": rec.get("right"),
                "dte": int(_f(rec.get("dte")) or 0),
                "strike": _f(rec.get("strike")),
                "bid": _f(rec.get("bid")),
                "ask": _f(rec.get("ask")),
                "volume": _f(rec.get("volume")),
                "open_interest": _f(rec.get("open_interest")),
                "implied_vol": _f(rec.get("implied_vol")),
            })
    return rows


def newest_chains(date: Optional[str] = None,
                  base_dir: Optional[str] = None) -> dict[str, Path]:
    root = Path(base_dir or config.CHAIN_DIR)
    if not root.exists():
        return {}
    days = sorted(p for p in root.iterdir() if p.is_dir())
    if not days:
        return {}
    day = (root / date) if date else days[-1]
    if not day.exists():
        return {}
    out: dict[str, Path] = {}
    for p in sorted(day.glob("*.csv"), key=lambda q: q.stat().st_mtime):
        out[p.name.split("_")[0]] = p
    return out


def write_manifest_gates(chain_path: Path, gates: dict) -> Optional[Path]:
    """Add the gate record to the fetch-time quality manifest beside the chain."""
    manifest = chain_path.with_name(chain_path.stem + "_quality.json")
    if not manifest.exists():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    data["gates"] = gates
    manifest.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return manifest


def run(date: Optional[str] = None, base_dir: Optional[str] = None,
        write_manifests: bool = False) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for sym, path in newest_chains(date, base_dir).items():
        try:
            gates = evaluate(load_chain(path))
            gates["source_chain"] = str(path)
            if write_manifests:
                m = write_manifest_gates(path, gates)
                gates["manifest"] = str(m) if m else None
            out[sym] = gates
        except Exception:  # noqa: BLE001
            log.exception("gate evaluation failed for %s", sym)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Data-quality gates over stored chains")
    ap.add_argument("--date", default=None)
    ap.add_argument("--base-dir", default=None)
    ap.add_argument("--write-manifests", action="store_true",
                    help="Write the gate record into each fetch-time manifest")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    res = run(args.date, args.base_dir, args.write_manifests)
    if not res:
        print("No stored chains found.")
        return 1

    print(f"\nthresholds: OI>={config.LIQUIDITY_MIN_TOTAL_OI:,} "
          f"volume>={config.LIQUIDITY_MIN_TOTAL_VOLUME:,} "
          f"roughness<={config.IV_ROUGHNESS_MAX}")
    print(f"\n{'sym':<6} {'verdict':<9} {'total OI':>12} {'total vol':>11} "
          f"{'spread':>7} {'rough':>7} {'HHI':>8} {'effN':>6} {'oiDTE':>7}")
    for sym, g in sorted(res.items()):
        liq, ivd = g["liquidity_floor"], g["iv_dispersion"]
        hhi, wd = g["oi_concentration"], g["oi_weighted_dte"]
        f = lambda v, w, p=0: (f"{v:>{w},.{p}f}" if isinstance(v, (int, float)) else f"{'-':>{w}}")
        print(f"{sym:<6} {g['data_quality']:<9} {f(liq['total_oi'],12)} "
              f"{f(liq['total_volume'],11)} {f(liq['median_rel_spread'],7,3)} "
              f"{f(ivd.get('roughness'),7,3)} {f(hhi.get('hhi'),8,4)} "
              f"{f(hhi.get('effective_strikes'),6,1)} "
              f"{f(wd.get('oi_weighted_dte'),7,1)}")

    from collections import Counter
    counts = Counter(g["data_quality"] for g in res.values())
    print(f"\n  verdicts: {dict(counts)}")
    excluded = [s for s, g in res.items() if g["data_quality"] == "excluded"]
    if excluded:
        print(f"  EXCLUDED (liquidity floor): {', '.join(excluded)}")
        for s in excluded:
            print(f"    {s}: {'; '.join(res[s]['liquidity_floor']['reasons'])}")
    if args.write_manifests:
        print(f"  manifests updated: {sum(1 for g in res.values() if g.get('manifest'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

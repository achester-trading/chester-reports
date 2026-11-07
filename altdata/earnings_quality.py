"""
Batch 22 item 122 (the order's 104; A134, 7 Nov 2026): earnings quality, NIPA
profits against reported EPS -- a report line and a flag in the Monthly's
earnings chain ("What's carrying the index", What's priced), Monthly only.

    from altdata import earnings_quality as eq
    r = eq.read(st, cutoff)          # as of the cutoff, from the store
    eq.lines(r)                      # the code-written lines

THE LINE. Year-on-year growth, each on its latest quarter knowable at the cutoff:
  NIPA after-tax profits         fred.cpatax (CPATAX, with IVA and CCAdj)
  BEA domestic nonfinancial      fred.profits_domestic_nonfin (A463RC1Q027SBEA;
                                 V-104a, the FRED id found 7 Nov 2026)
  S&P EPS                        shiller.sp_earnings, trailing twelve months AS
                                 REPORTED, read at the quarter's last month.
                                 V-104a: S&P operating EPS has no keyless source
                                 -- S&P DJI's EPS file was withdrawn on 17 Oct
                                 2026 (altdata/sources/spdji.py) and answers 403
                                 -- so the line prints Shiller's reported series
                                 and says so (config `eps_label`).
and the gap, EPS growth less each NIPA growth, in points.

THE FLAG. EPS growth above NIPA (CPATAX) growth by the margin for two quarters
running. The margin is O-3's: calibrated by tools/calibration/earnings_quality.py
under the rule pre-registered at the head of
docs/ledgers/earnings-quality-calibration-2026-11.md (its SHA-256 held in
config/earnings_quality.yaml); 10 points when the calibration is ambiguous.
Report line and flag only: nothing here is a state, a modifier or a rule, and
the flag enters no composite or the market-state object. Nothing here fetches or
writes.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Any, Optional

import yaml

from .batch3 import _pts

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "earnings_quality.yaml"


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG_PATH).read_text(encoding="utf-8")) or {}


def rule_sha256(text: str) -> str:
    """The pre-registered rule's hash, over its whitespace-normalised text (as
    altdata/tb_harness.py hashes its pass rule)."""
    return hashlib.sha256(" ".join(str(text).split()).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Quarters and growth
# ---------------------------------------------------------------------------
def quarter_of(day: str) -> str:
    """'2026-04-01' (or any day in it) -> '2026Q2'."""
    d = dt.date.fromisoformat(str(day)[:10])
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def prev_quarter(q: str, k: int = 1) -> str:
    y, n = int(q[:4]), int(q[5])
    i = y * 4 + (n - 1) - k
    return f"{i // 4}Q{i % 4 + 1}"


def last_month(q: str) -> str:
    """'2026Q2' -> '2026-06'."""
    return f"{q[:4]}-{int(q[5]) * 3:02d}"


def quarterly(points) -> dict[str, float]:
    """[(observed_at, value)] of a quarterly series -> {quarter: value}."""
    return {quarter_of(d): float(v) for d, v in points}


def monthly(points) -> dict[str, float]:
    """[(observed_at, value)] of a monthly series -> {'YYYY-MM': value}."""
    return {str(d)[:7]: float(v) for d, v in points}


def _yoy(now: Optional[float], then: Optional[float]) -> Optional[float]:
    if now is None or then is None or then <= 0:
        return None
    return 100.0 * (now / then - 1.0)


def growth_rows(nipa: dict[str, float], eps: dict[str, float],
                nonfin: Optional[dict[str, float]] = None) -> dict[str, dict]:
    """Per quarter: NIPA growth, EPS growth (the quarter's last month against a
    year earlier), the gap EPS less NIPA, and the nonfinancial leg beside it."""
    out: dict[str, dict] = {}
    for q in sorted(nipa):
        g_n = _yoy(nipa.get(q), nipa.get(prev_quarter(q, 4)))
        m = last_month(q)
        g_e = _yoy(eps.get(m), eps.get(f"{int(m[:4]) - 1}{m[4:]}"))
        row: dict[str, Any] = {"nipa_yoy": g_n, "eps_yoy": g_e,
                               "gap": (g_e - g_n) if None not in (g_e, g_n) else None}
        if nonfin is not None:
            g_f = _yoy(nonfin.get(q), nonfin.get(prev_quarter(q, 4)))
            row["nonfin_yoy"] = g_f
            row["gap_nonfin"] = (g_e - g_f) if None not in (g_e, g_f) else None
        out[q] = row
    return out


def fired(rows: dict[str, dict], margin: float, field: str = "gap") -> list[str]:
    """Quarters at which the flag fires: the gap at least `margin` in the
    quarter and in the quarter before it (two quarters running)."""
    out = []
    for q in sorted(rows):
        g, p = rows[q].get(field), (rows.get(prev_quarter(q)) or {}).get(field)
        if g is not None and p is not None and g >= margin and p >= margin:
            out.append(q)
    return out


def episodes(quarters: list[str]) -> list[list[str]]:
    """Maximal runs of consecutive quarters."""
    runs: list[list[str]] = []
    for q in sorted(quarters):
        if runs and prev_quarter(q) == runs[-1][-1]:
            runs[-1].append(q)
        else:
            runs.append([q])
    return runs


def _in(q: str, window: list) -> bool:
    return str(window[0]) <= q <= str(window[1])


def calibrate(rows: dict[str, dict], cfg: dict) -> dict:
    """O-3 under the pre-registered rule (config `calibration`): every candidate
    margin's fires in each target, its false-positive episodes since `fp_from`,
    the admissible set, the choice, and why when ambiguous."""
    c = cfg["calibration"]
    targets = {k: list(v) for k, v in c["targets"].items()}
    fp_from = str(c.get("fp_from", "1990Q1"))
    lo, hi = (int(x) for x in c["candidates"])
    scored = {q: r for q, r in rows.items() if q >= prev_quarter(fp_from)}
    table = []
    for m in range(lo, hi + 1):
        f = fired(scored, m)
        f = [q for q in f if q >= fp_from]
        eps_ = episodes(f)
        hits = {k: any(_in(q, w) for q in f) for k, w in targets.items()}
        fps = [e for e in eps_ if not any(_in(q, w) for q in e for w in targets.values())]
        table.append({"margin": m, "hits": hits, "admissible": all(hits.values()),
                      "episodes": len(eps_), "false_positives": len(fps),
                      "fp_episodes": [(e[0], e[-1]) for e in fps],
                      "fired_quarters": len(f)})
    adm = [t for t in table if t["admissible"]]
    out: dict[str, Any] = {"table": table, "admissible": [t["margin"] for t in adm],
                           "quarters": (min(scored), max(scored)) if scored else None}
    default = float(c.get("ambiguous_margin", 10))
    if not adm:
        out.update(margin=default, ambiguous=True,
                   why="no candidate margin fires in both target windows")
    else:
        best = min(t["false_positives"] for t in adm)
        tied = [t["margin"] for t in adm if t["false_positives"] == best]
        if len(tied) > 1:
            out.update(margin=default, ambiguous=True,
                       why=(f"the fewest false-positive episodes ({best}) is shared by "
                            f"{len(tied)} admissible margins ({tied[0]} to {tied[-1]} "
                            f"points{'' if tied == list(range(tied[0], tied[-1] + 1)) else ', not contiguous'})"))
        else:
            out.update(margin=float(tied[0]), ambiguous=False, why=None)
    chosen = next((t for t in table if t["margin"] == out["margin"]), None)
    out["chosen"] = chosen
    # The nonfinancial leg, scored beside it at the chosen margin; never selects.
    fn = [q for q in fired(scored, out["margin"], "gap_nonfin") if q >= fp_from]
    out["nonfin"] = {"episodes": [(e[0], e[-1]) for e in episodes(fn)],
                     "hits": {k: any(_in(q, w) for q in fn) for k, w in targets.items()},
                     "false_positives": sum(
                         1 for e in episodes(fn)
                         if not any(_in(q, w) for q in e for w in targets.values()))}
    return out


# ---------------------------------------------------------------------------
# The Monthly's read, as of the cutoff
# ---------------------------------------------------------------------------
def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The latest quarter knowable at the cutoff on each leg, its growth, the
    gaps and the flag. A missing leg is named "not tracked" or "not stored"."""
    cfg = cfg or config()
    k = cfg["keys"]
    nipa = quarterly(_pts(st, k["nipa"], cutoff))
    nonfin = quarterly(_pts(st, k["nonfin"], cutoff)) if k.get("nonfin") else None
    eps = monthly(_pts(st, k["eps"], cutoff))
    out: dict[str, Any] = {"margin": float(cfg.get("margin", 10)),
                           "eps_label": cfg.get("eps_label"),
                           "margin_basis": cfg.get("margin_basis")}
    missing = []
    if not nipa:
        missing.append("NIPA after-tax profits not stored")
    if k.get("nonfin") is None:
        out["nonfin_reason"] = "not tracked"
    elif not nonfin:
        out["nonfin_reason"] = "not stored"
    if not eps:
        missing.append("S&P EPS not stored")
    if missing:
        out["absent"] = "; ".join(missing)
        return out
    rows = growth_rows(nipa, eps, nonfin or None)
    have = [q for q in sorted(rows) if rows[q]["gap"] is not None]
    if not have:
        q = max(nipa)
        out["absent"] = (f"no quarter carries both growth rates at the cutoff (NIPA to "
                         f"{q}; S&P EPS to {max(eps)})")
        return out
    q = have[-1]
    out.update(quarter=q, **{f: rows[q].get(f) for f in
                             ("nipa_yoy", "eps_yoy", "gap", "nonfin_yoy", "gap_nonfin")})
    out["previous"] = {"quarter": prev_quarter(q), "gap": (rows.get(prev_quarter(q)) or {}).get("gap")}
    out["flag"] = q in fired(rows, out["margin"])
    if max(nipa) != q:
        out["note"] = f"NIPA carries {max(nipa)}, S&P EPS's quarter-end month not yet stored"
    return out


def _pct(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.1f}%"


def _pp(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.1f} pts"


def lines(r: dict) -> list[str]:
    """The earnings-quality line, and the flag line when it fires."""
    if r.get("absent"):
        return [f"Earnings quality (NIPA profits against S&P EPS): {r['absent']}."]
    lab = r.get("eps_label") or "S&P EPS"
    q = r["quarter"]
    nf = (f"BEA domestic nonfinancial {_pct(r.get('nonfin_yoy'))} (gap {_pp(r.get('gap_nonfin'))})"
          if r.get("nonfin_yoy") is not None else
          f"BEA domestic nonfinancial {r.get('nonfin_reason') or 'not stored'}")
    out = [f"Earnings quality, {q} on the year: {lab} {_pct(r['eps_yoy'])} against NIPA "
           f"after-tax profits {_pct(r['nipa_yoy'])}, a gap of {_pp(r['gap'])}; {nf}."]
    m = r["margin"]
    basis = r.get("margin_basis") or "O-3"
    if r.get("flag"):
        out.append(f"Earnings-quality flag: EPS growth has run at least {m:.0f} points above "
                   f"NIPA growth for two quarters ({r['previous']['quarter']} and {q}); a "
                   f"flag, not a state ({basis}).")
    else:
        out.append(f"Earnings-quality flag off: it fires when EPS growth runs {m:.0f} points "
                   f"or more above NIPA growth two quarters running ({basis}).")
    if r.get("note"):
        out.append(f"{r['note']}.")
    return out

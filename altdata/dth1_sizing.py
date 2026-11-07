"""
DTH-1's constant-dollar-risk sizing (signal-triage Batch 23 item 124g(ii), the
body's 106g(ii); A130, 6 Nov 2026), reconciled with the day-trading rules'
rule 8 as the operator ruled it in chat (D63's D8, until paste B140 files the
rules order): STRUCTURE SETS THE STOP; THE ATR MULTIPLE IS ITS FLOOR; SIZE =
FIXED DOLLAR RISK / STOP DISTANCE.

    python -m altdata.dth1_sizing [--date D] [--stop POINTS] [--instrument ES|MES]

THE INPUTS
- the instrument, ES or MES (point values in config/dth1.yaml `sizing`);
- the structural stop the operator names, in points from entry, or none;
- THE ACCOUNT BASE, read from the operator's file dth1-account-base.csv in the
  private Drive folder chester-cards, which the nightly sweep already copies
  whole to ~/chester-data/inbox/cards/ (scripts/rclone_sync.sh `pull_folder
  chester-cards cards`, A92b). Never from the repo: without the file every
  figure that needs it prints "no base";
- the risk fraction (1% of the base, config) and the daily limit (2%, config);
- the ATR: 14 sessions of ES's complete daily bars, built from the stored
  5-minute bars as the volatile-day flag builds them (daily_cascade/
  volatile_day.py `_es_inputs`, `true_ranges`).

THE RULE
  floor          = k x ATR        (k from config, 1.0, session-set; 124c(i)'s vol
                                   state will set k once it exists: `vol_state_k`
                                   reads "not built" today)
  stop distance  = max(structural distance, floor), or the floor with no stop named
  contracts      = floor(risk dollars / (stop distance x point value)); MES when
                   ES rounds to zero; "below one MES contract" when MES does too

EVERYTHING PRINTS; NOTHING PLACES AN ORDER. No broker, order or register import
(tools/validate_item_124_g2.py proves it in a fresh interpreter). The sizes
print in the 07:00 anchor's DTH-1 block only, as 124g(ii) orders: the risk
and the daily limit in dollars, never the base itself, never a trade.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import re
from pathlib import Path
from typing import Any, Optional

import yaml

CONFIG = Path(__file__).resolve().parent.parent / "config" / "dth1.yaml"
NO_BASE = "no base"
NOT_BUILT = "not built"
BASE_FILE = "dth1-account-base.csv"
BASE_NOT_FOUND = f"account base not found in chester-cards ({BASE_FILE})"


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def sizing_cfg(cfg: Optional[dict] = None) -> dict:
    return (cfg or config()).get("sizing") or {}


# ---------------------------------------------------------------------------
# The account base: the operator's file, through the inbox, never the repo
# ---------------------------------------------------------------------------
def _key(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(h).strip().lower()).strip("_")


def account_base(path: Optional[str] = None, on: Optional[str] = None,
                 cfg: Optional[dict] = None) -> dict:
    """{base, as_of, file} from the newest row on or before `on`; {reason} when
    the file or a usable row is absent. Columns are read by header name, as the
    ledger reader reads its own (date; account_base / base / equity)."""
    s = sizing_cfg(cfg)
    p = Path(path or s.get("base_path") or "").expanduser()
    if not p.is_file():
        return {"reason": BASE_NOT_FOUND, "file": BASE_FILE}
    names = s.get("base_columns") or {}
    dnames = [_key(x) for x in names.get("date", ["date"])]
    bnames = [_key(x) for x in names.get("base", ["account_base", "base"])]
    best: Optional[tuple[str, float]] = None
    try:
        with open(p, newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            hdr = {_key(h): h for h in (rd.fieldnames or [])}
            dcol = next((hdr[k] for k in dnames if k in hdr), None)
            bcol = next((hdr[k] for k in bnames if k in hdr), None)
            if not dcol or not bcol:
                return {"reason": f"{BASE_FILE}: no "
                                  + ("date" if not dcol else "account base")
                                  + " column", "file": BASE_FILE}
            for row in rd:
                d = str(row.get(dcol) or "").strip()[:10]
                try:
                    dt.date.fromisoformat(d)
                    v = float(str(row.get(bcol) or "").replace(",", "").replace("$", ""))
                except ValueError:
                    continue
                if v <= 0 or (on and d > on):
                    continue
                if best is None or d >= best[0]:
                    best = (d, v)
    except OSError:
        return {"reason": BASE_NOT_FOUND, "file": BASE_FILE}
    if best is None:
        return {"reason": f"{BASE_FILE}: no dated row on or before {on}"
                          if on else f"{BASE_FILE}: no usable row", "file": BASE_FILE}
    return {"base": best[1], "as_of": best[0], "file": BASE_FILE}


# ---------------------------------------------------------------------------
# The ATR and k
# ---------------------------------------------------------------------------
def atr(daily: list[dict], n: int = 14) -> tuple[Optional[float], int]:
    """The mean of the last `n` true ranges over consecutive daily bars, and how
    many it averaged."""
    from daily_cascade.volatile_day import true_ranges          # noqa: PLC0415
    trs = true_ranges(daily)[-n:]
    return (sum(trs) / len(trs), len(trs)) if trs else (None, 0)


def atr_from_store(day: str, cutoff: str, db_path: Optional[str],
                   n: int = 14) -> dict:
    """ES's ATR from the stored 5-minute bars: the complete sessions before `day`
    (the volatile-day flag's own reader)."""
    from daily_cascade import volatile_day                      # noqa: PLC0415
    try:
        _, _, daily = volatile_day._es_inputs(day, cutoff, db_path,  # noqa: SLF001
                                              {"atr_sessions": n})
    except Exception as exc:                                    # noqa: BLE001
        return {"atr": None, "n": 0, "reason": f"ES bars not read: {type(exc).__name__}"}
    a, k = atr(daily, n)
    if a is None:
        return {"atr": None, "n": 0, "reason": "no complete ES sessions stored"}
    return {"atr": a, "n": k}


def vol_state_k() -> Optional[float]:
    """124c(i)'s vol state will set k. It is not built, so this returns None and
    the config's k applies (the hook the paste names)."""
    return None


def k_value(cfg: Optional[dict] = None) -> tuple[float, str]:
    vs = vol_state_k()
    if vs is not None:
        return vs, "the vol state (124c(i))"
    return float(sizing_cfg(cfg).get("k", 1.0)), \
        f"config, session-set; the vol state (124c(i)): {NOT_BUILT}"


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------
def stop_distance(structural: Optional[float], atr_pts: Optional[float],
                  k: float) -> dict:
    """max(structural, k x ATR); the floor alone when no stop is named; the
    structural stop alone when no ATR is stored (said so)."""
    floor = k * atr_pts if atr_pts is not None else None
    if structural is not None and structural <= 0:
        structural = None
    if structural is None and floor is None:
        return {"distance": None, "floor": None, "floor_applied": None,
                "reason": "no stop named and no ATR stored"}
    if floor is None:
        return {"distance": structural, "floor": None, "floor_applied": False,
                "reason": "no ATR stored: the structural stop alone, unfloored"}
    if structural is None:
        return {"distance": floor, "floor": floor, "floor_applied": True}
    return {"distance": max(structural, floor), "floor": floor,
            "floor_applied": floor > structural}


def contracts(risk_usd: Optional[float], distance: Optional[float],
              cfg: Optional[dict] = None, instrument: str = "ES") -> dict:
    """floor(risk / (distance x point value)); MES when ES rounds to zero."""
    pv = sizing_cfg(cfg).get("point_value") or {"ES": 50.0, "MES": 5.0}
    if risk_usd is None:
        return {"instrument": None, "contracts": None, "reason": NO_BASE}
    if not distance or distance <= 0:
        return {"instrument": None, "contracts": None, "reason": "no stop distance"}
    inst = instrument.upper()
    if inst == "ES":
        n = math.floor(risk_usd / (distance * float(pv["ES"])) + 1e-9)
        if n >= 1:
            return {"instrument": "ES", "contracts": n,
                    "risk_at_size": n * distance * float(pv["ES"])}
        inst = "MES"
    n = math.floor(risk_usd / (distance * float(pv["MES"])) + 1e-9)
    if n >= 1:
        return {"instrument": "MES", "contracts": n,
                "risk_at_size": n * distance * float(pv["MES"]),
                **({"rounded_from": "ES"} if instrument.upper() == "ES" else {})}
    return {"instrument": "MES", "contracts": 0, "reason": "below one MES contract"}


def size(base: dict, atr_pts: Optional[float], structural: Optional[float] = None,
         instrument: str = "ES", cfg: Optional[dict] = None) -> dict:
    """The whole computation for one stop."""
    s = sizing_cfg(cfg)
    k, kwhy = k_value(cfg)
    b = base.get("base")
    risk = b * float(s.get("risk_fraction", 0.01)) if b is not None else None
    limit = b * float(s.get("daily_limit_fraction", 0.02)) if b is not None else None
    sd = stop_distance(structural, atr_pts, k)
    c = contracts(risk, sd["distance"], cfg, instrument)
    return {"risk_usd": risk, "daily_limit_usd": limit, "k": k, "k_source": kwhy,
            "atr": atr_pts, **sd, **c,
            "base_reason": base.get("reason")}


# ---------------------------------------------------------------------------
# The 07:00 anchor's DTH-1 block: the day's sizing table
# ---------------------------------------------------------------------------
def _usd(v: Optional[float]) -> str:
    return NO_BASE if v is None else f"${v:,.0f}"


def plan_block(day: str, cutoff: str, db_path: Optional[str],
               base_path: Optional[str] = None, cfg: Optional[dict] = None,
               atr_override: Optional[dict] = None) -> dict:
    """{title, lines, table} for the anchor: the risk and the daily limit in
    dollars (never the base itself), the ATR, the floor, and contracts in ES and
    MES at three candidate stop distances (multiples of the ATR, config). With
    no base file: one line naming it, and nothing sized."""
    cfg = cfg or config()
    s = sizing_cfg(cfg)
    if not s.get("enabled", True):
        return {"enabled": False, "title": "", "lines": [], "table": None}
    title = str(s.get("title") or "DTH-1 sizing (constant dollar risk)")
    base = account_base(base_path, day, cfg)
    n_atr = int(s.get("atr_sessions", 14))
    at = atr_override if atr_override is not None else atr_from_store(day, cutoff,
                                                                      db_path, n_atr)
    k, kwhy = k_value(cfg)
    if base.get("base") is None:
        return {"enabled": True, "title": title, "table": None,
                "lines": [base["reason"] if base["reason"].startswith("account base")
                          else f"{BASE_NOT_FOUND}: {base['reason']}"]}
    risk = base["base"] * float(s.get("risk_fraction", 0.01))
    limit = base["base"] * float(s.get("daily_limit_fraction", 0.02))
    lines = [f"Risk per trade {_usd(risk)} ({100 * float(s.get('risk_fraction', 0.01)):g}% "
             f"of the base as of {base['as_of']}); daily limit {_usd(limit)} "
             f"({100 * float(s.get('daily_limit_fraction', 0.02)):g}%)."]
    if at.get("atr") is None:
        lines.append(f"ATR({n_atr}): not read ({at.get('reason')}); no floor, so no "
                     f"stop is sized until the structure names one.")
        return {"enabled": True, "title": title, "lines": lines, "table": None}
    floor = k * at["atr"]
    lines.append(f"ES ATR({n_atr}) {at['atr']:.2f} points (n={at['n']}); the floor is "
                 f"k x ATR = {floor:.2f} points (k {k:g}: {kwhy}). The stop is the "
                 f"structure's, never tighter than the floor.")
    rows = []
    for m in s.get("candidates_atr") or [1.0, 1.5, 2.0]:
        dist = float(m) * at["atr"]
        sd = stop_distance(dist, at["atr"], k)
        es = contracts(risk, sd["distance"], cfg, "ES")
        mes = contracts(risk, sd["distance"], cfg, "MES")
        es_n = es["contracts"] if es.get("instrument") == "ES" else 0
        rows.append([f"{float(m):g} x ATR = {dist:.2f}"
                     + (f" (floored to {sd['distance']:.2f})" if sd["floor_applied"] else ""),
                     str(es_n) + ("" if es_n else " (MES below)"),
                     str(mes.get("contracts") or 0),
                     _usd(es.get("risk_at_size") if es_n else mes.get("risk_at_size"))])
    lines.append(str(s.get("footer") or "Sizes only: nothing here places an order."))
    return {"enabled": True, "title": title, "lines": lines,
            "table": {"columns": ["Stop distance (points)", "ES contracts",
                                  "MES contracts", "Risk at that size"], "rows": rows}}


def plan_text(block: Optional[dict]) -> list[str]:
    if not block or not block.get("enabled"):
        return []
    out = [block["title"]] + [f"  {ln}" for ln in block["lines"][:-1 if block.get("table") else None]]
    t = block.get("table")
    if t:
        out.append("  " + " | ".join(t["columns"]))
        out += ["  " + " | ".join(r) for r in t["rows"]]
        out.append(f"  {block['lines'][-1]}")
    return out


def plan_html(block: Optional[dict]) -> str:
    import html                                                 # noqa: PLC0415
    if not block or not block.get("enabled"):
        return ""
    t = block.get("table")
    lines = block["lines"][:-1] if t else block["lines"]
    parts = [f"<h3>{html.escape(block['title'])}</h3>"]
    parts += [f"<p>{html.escape(ln)}</p>" for ln in lines]
    if t:
        parts.append("<table><tr>" + "".join(f"<th>{html.escape(c)}</th>"
                                             for c in t["columns"]) + "</tr>"
                     + "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r)
                               + "</tr>" for r in t["rows"]) + "</table>")
        parts.append(f"<p><em>{html.escape(block['lines'][-1])}</em></p>")
    return "\n".join(parts)


def _main(argv: Optional[list[str]] = None) -> int:
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    from . import session                                       # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.dth1_sizing")
    ap.add_argument("--date", default=None)
    ap.add_argument("--stop", type=float, default=None,
                    help="the structural stop's distance from entry, in points")
    ap.add_argument("--instrument", default="ES", choices=["ES", "MES"])
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    day = a.date or session.session_date()
    now = session.utc_iso()
    if a.stop is None:
        for ln in plan_text(plan_block(day, now, a.db)):
            print(ln)
        return 0
    cfg = config()
    base = account_base(None, day, cfg)
    at = atr_from_store(day, now, a.db, int(sizing_cfg(cfg).get("atr_sessions", 14)))
    r = size(base, at.get("atr"), a.stop, a.instrument, cfg)
    print(f"stop {a.stop:g} points -> distance "
          f"{'n/a' if r['distance'] is None else format(r['distance'], '.2f')} "
          f"(floor {'n/a' if r['floor'] is None else format(r['floor'], '.2f')}, "
          f"applied: {r['floor_applied']}); {r.get('instrument')} "
          f"{r.get('contracts')}; risk {_usd(r['risk_usd'])}"
          + (f" ({r['reason']})" if r.get("reason") else ""))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))

"""
The HY bifurcation line (signal-triage Batch 25 item 131, the order's 110; B139).

    python -m altdata.credit_bifurcation show [--as-of 2026-11-06] [--db PATH]

One code-written line in Plumbing & rates -- the close, the Weekly and the
Monthly -- that sets the CYCLE series beside the IDIOSYNCRATIC ones:

    Credit bifurcation (as of 2026-11-04): cycle -- HY OAS 332 bp (+5 bp),
    Baa less the 10-year 152 bp (+6 bp); idiosyncratic -- CCC/HY OAS 4.05x,
    97th percentile of 5y asked, 3.4y stored (n=780), CCC less BB +40 bp.
    Changes over 20 observations. Report only.

- The CCC/HY ratio is computed at read from the two stored OAS series on their
  common days (fred.ccc_oas / fred.hy_oas); nothing new is stored.
- Its percentile is over its own history inside the asked window, with the
  window printed through A126's derived.window_label, so a short stored span
  says so ("5y asked, 3.4y stored").
- The composition clause prints only when a stored source carries it: a
  reading-shelf scan's reference-table row through the scans ingest
  (config/credit_bifurcation.yaml `composition`). With none stored the clause
  is omitted -- never invented, never "n/a".

Report line. No flag, no threshold, and nothing here enters the credit
dimension's computation, the market-state object, an overlay or a composite.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "credit_bifurcation.yaml"
TITLE = "Credit bifurcation: the cycle and the tail"


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load((path or CONFIG_PATH).read_text(encoding="utf-8"))


def _series(st, key: str, as_of: Optional[str]) -> list[tuple[str, float]]:
    """(day, value) per observation day, the newest vintage known at as_of."""
    by: dict[str, float] = {}
    for r in st.as_of(key, as_of):
        if r.get("value_num") is None:
            continue
        by[str(r["observed_at"])[:10]] = float(r["value_num"])
    return sorted(by.items())


def _bp(key: str, v: float) -> float:
    """A spread in bp: the OAS series are stored in percent, the calc.* in bp."""
    from . import derived                                       # noqa: PLC0415
    u = derived.level_units_of(key)
    return v if u in ("bps", "bp") else v * 100.0


def _chg(s: list[tuple[str, float]], n: int) -> Optional[float]:
    return None if len(s) <= n else s[-1][1] - s[-1 - n][1]


def _composition(cfg: dict, as_of: Optional[str], db_path: Optional[str],
                 rows: Optional[list]) -> list[dict]:
    comp = cfg.get("composition") or {}
    if rows is None and db_path is None:
        rows = []          # no store path named: read nothing, never the live default
    if rows is None:
        try:
            from . import scans                                 # noqa: PLC0415
            rows = scans.latest(as_of, db_path)
        except Exception:                                       # noqa: BLE001
            log.warning("the scans store could not be read", exc_info=True)
            rows = []
    out = []
    for m in comp.get("metrics") or []:
        hit = [r for r in rows if r.get("family") == comp.get("family")
               and r.get("metric") == m["metric"]]
        if hit:
            r = hit[-1]
            out.append({"label": m["label"], "value": str(r["value"]),
                        "as_of": r["as_of"], "source_url": r["source_url"]})
    return out


def read(st, as_of: Optional[str] = None, *, cfg: Optional[dict] = None,
         db_path: Optional[str] = None, scan_rows: Optional[list] = None) -> dict:
    """Everything the line prints, from the store as known at as_of."""
    from . import derived                                       # noqa: PLC0415
    c = cfg or config()
    n = int(c.get("change_observations", 20))
    out: dict[str, Any] = {"cycle": [], "ratio": None, "tail": None,
                           "composition": [], "n_change": n}
    for s in c["cycle"]:
        ser = _series(st, s["key"], as_of)
        if not ser:
            out["cycle"].append({**s, "level_bp": None})
            continue
        ch = _chg(ser, n)
        out["cycle"].append({**s, "observed_at": ser[-1][0],
                             "level_bp": _bp(s["key"], ser[-1][1]),
                             "change_bp": None if ch is None else _bp(s["key"], ch)})
    rc = c["ratio"]
    num = dict(_series(st, rc["numerator"], as_of))
    den = dict(_series(st, rc["denominator"], as_of))
    ratio = [(d, num[d] / den[d]) for d in sorted(set(num) & set(den)) if den[d]]
    if ratio:
        day, lvl = ratio[-1]
        asked = int(rc["window_days"])
        lo = (dt.date.fromisoformat(day) - dt.timedelta(days=asked)).isoformat()
        inside = [v for d, v in ratio if d >= lo]
        first = next(d for d, _ in ratio if d >= lo)
        held = (dt.date.fromisoformat(day) - dt.date.fromisoformat(first)).days
        ok = len(inside) >= int(rc.get("min_n", 2))
        out["ratio"] = {"observed_at": day, "level": lvl, "n": len(inside),
                        "window": derived.window_label(asked, held, start=first),
                        "window_compact": derived.window_label(asked, held,
                                                               compact=True, start=first),
                        "asked_days": asked, "held_days": held,
                        "percentile": derived.percentile_of(inside, lvl) if ok else None}
    tc = c["tail"]
    ts = _series(st, tc["key"], as_of)
    if ts:
        ch = _chg(ts, n)
        out["tail"] = {**tc, "observed_at": ts[-1][0], "level_bp": _bp(tc["key"], ts[-1][1]),
                       "change_bp": None if ch is None else _bp(tc["key"], ch)}
    out["composition"] = _composition(c, as_of, db_path, scan_rows)
    return out


def _s(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v:+.0f} bp"


def line(r: dict) -> Optional[str]:
    """The one line, or None when neither half has a stored print."""
    from .numeral_audit import percentile_ordinal               # noqa: PLC0415
    cyc = [f"{x['label']} {x['level_bp']:.0f} bp ({_s(x.get('change_bp'))})"
           for x in r["cycle"] if x.get("level_bp") is not None]
    idio = []
    q = r.get("ratio")
    if q:
        pct = (f", {percentile_ordinal(q['percentile'])} percentile of "
               f"{q['window']} (n={q['n']:,})" if q.get("percentile") is not None
               else f", percentile withheld ({q['n']} observation(s) in {q['window']})")
        idio.append(f"CCC/HY OAS {q['level']:.2f}x{pct}")
    t = r.get("tail")
    if t:
        idio.append(f"{t['label']} {_s(t.get('change_bp'))}")
    if not cyc and not idio:
        return None
    days = [x["observed_at"] for x in r["cycle"] if x.get("observed_at")]
    days += [q["observed_at"]] if q else []
    head = f"Credit bifurcation (as of {max(days)})" if days else "Credit bifurcation"
    parts = [f"cycle -- {', '.join(cyc) if cyc else 'not stored'}",
             f"idiosyncratic -- {', '.join(idio) if idio else 'not stored'}"]
    comp = "; ".join(f"{x['label']} {x['value']} (as of {x['as_of']}, {x['source_url']})"
                     for x in r.get("composition") or [])
    tail = f"; composition: {comp}" if comp else ""
    return (f"{head}: {'; '.join(parts)}{tail}. Changes over {r['n_change']} "
            f"observations. Report only.")


def subsection(st, as_of: Optional[str], db_path: Optional[str] = None) -> Optional[dict]:
    """The Plumbing & rates sub-section, or None. A fault costs the line only."""
    if db_path is None and getattr(st, "path", None) is not None:
        db_path = str(st.path)
    try:
        r = read(st, as_of, db_path=db_path)
        ln = line(r)
    except Exception:                                           # noqa: BLE001
        log.warning("the credit bifurcation line faulted", exc_info=True)
        return None
    if not ln:
        return None
    return {"title": TITLE, "lines": [ln], "paragraph_wanted": False,
            "table_note": ("Report only (Batch 25 item 131): nothing here enters "
                           "the credit dimension, the market-state object or a "
                           "composite."),
            "data": {"bifurcation": r, "line": ln}}


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    from . import observations                                  # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sh = sub.add_parser("show")
    sh.add_argument("--as-of", default=None)
    sh.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    st = observations.ObservationStore(a.db)
    try:
        print(line(read(st, a.as_of, db_path=a.db or str(st.path))) or "no stored print")
    finally:
        st.close()
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))

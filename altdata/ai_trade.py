"""
"One big AI trade": the AI-bottleneck PPI line, the Broad-AI proxy pair and the
AI-credit gap (signal-triage Batch 14 item 65, written as 58; ST-R6.65b-d; ruled
20 Oct 2026 with filing amendments F1-F8; a57-batch14-b1).

    python -m altdata.ai_trade show [--as-of ISO]

THE PPI LINE (ST-R6.65b), in item 46's pipeline: BLS's PPI by industry for
printed circuit assemblies, computer storage devices and semiconductors, through
FRED (F3), monthly. Not seasonally adjusted, so each is read on the year, with
dual percentiles of that change (five years and the full stored history).

THE PROXY PAIR (ST-R6.65c), in the concentration cluster: AIQ against SPXT
(config/ai_trade.yaml), labelled "proxy" wherever it prints (F2) -- each one's
return since the base date, the relative return over a year with its dual
percentiles. A leg with too little history is absent with its reason.

THE AI-CREDIT WATCH is a listed gap (F2): one line, no by-hand path.

Report only. Reads the store as of the cutoff; writes nothing; enters no
composite and not the market-state object.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "ai_trade.yaml"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


def _pts(st, key: str, cutoff: str) -> list[tuple[str, float]]:
    from . import st_r5_rates                                   # noqa: PLC0415
    return st_r5_rates._pts(st, key, cutoff)


def yoy_series(pts: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Each month's change on the same month a year earlier, in percent."""
    by = {d[:7]: v for d, v in pts}
    out = []
    for d, v in pts:
        y, m = int(d[:4]), d[5:7]
        prev = by.get(f"{y - 1:04d}-{m}")
        if prev:
            out.append((d, (v / prev - 1.0) * 100.0))
    return out


# ---------------------------------------------------------------------------
# ST-R6.65b -- the AI-bottleneck PPI line
# ---------------------------------------------------------------------------
def ppi_read(series: dict[str, list[tuple[str, float]]], cfg: dict) -> dict:
    """{rows, missing}: per configured PPI line, its latest month, the level, the
    year-on-year change and that change's dual percentiles."""
    from . import st_r5_rates                                   # noqa: PLC0415
    rows, missing = [], []
    for spec in cfg.get("ppi") or []:
        pts = series.get(spec["key"]) or []
        yy = yoy_series(pts)
        if not yy:
            missing.append({"name": spec["name"], "key": spec["key"],
                            "reason": ("not stored" if not pts else
                                       f"{len(pts)} month(s) stored, no year to compare")})
            continue
        lz = st_r5_rates.lens(yy)
        rows.append({"name": spec["name"], "key": spec["key"], "month": yy[-1][0][:7],
                     "level": pts[-1][1], "yoy_pct": round(yy[-1][1], 1), "lens": lz,
                     "lens_text": st_r5_rates.lens_text(lz)})
    return {"rows": rows, "missing": missing}


def ppi_lines(r: dict) -> list[str]:
    out = []
    if r["rows"]:
        out.append("The AI bottleneck in producer prices (BLS's PPI by industry, via FRED, "
                   "NSA, on the year): " + "; ".join(
                       f"{x['name']} {x['yoy_pct']:+.1f}% to {x['month']} "
                       f"({x['lens_text']})" for x in r["rows"]) + ".")
    if r["missing"]:
        out.append("Not read: " + "; ".join(f"{m['name']} ({m['reason']})"
                                            for m in r["missing"]) + ".")
    return out


# ---------------------------------------------------------------------------
# ST-R6.65c -- the proxy pair
# ---------------------------------------------------------------------------
def _on_or_after(pts: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    return next(((d, v) for d, v in pts if d >= day), None)


def relative(ai: list[tuple[str, float]], ex: list[tuple[str, float]],
             window: int) -> list[tuple[str, float]]:
    """The AI leg's return less the ex-AI leg's over `window` sessions, in pp, on
    the sessions both legs close."""
    b = dict(ex)
    both = [(d, v, b[d]) for d, v in ai if d in b]
    return [(both[i][0], ((both[i][1] / both[i - window][1])
                          - (both[i][2] / both[i - window][2])) * 100.0)
            for i in range(window, len(both))]


def proxy_read(ai: list[tuple[str, float]], ex: list[tuple[str, float]],
               cfg: dict) -> dict:
    from . import st_r5_rates                                   # noqa: PLC0415
    p = cfg["proxy"]
    out: dict[str, Any] = {"label": p["label"], "title": p["title"],
                           "ai": p["ai"]["symbol"], "ex_ai": p["ex_ai"]["symbol"],
                           "caveat": " ".join(str(p.get("caveat") or "").split())}
    gaps = [f"{leg['symbol']} ({leg['key']}): {len(pts)} session(s) stored"
            for leg, pts in ((p["ai"], ai), (p["ex_ai"], ex))
            if len(pts) < int(p["min_sessions"])]
    if gaps:
        out.update(state="absent", reason="too little history -- " + "; ".join(gaps)
                   + f" (fewer than {p['min_sessions']}; tools/backfill_prices.py)")
        return out
    base = p["base_date"]
    cum = {}
    for name, pts in (("ai", ai), ("ex_ai", ex)):
        b0 = _on_or_after(pts, base)
        cum[name] = (None if not b0 or b0[0] == pts[-1][0]
                     else round((pts[-1][1] / b0[1] - 1.0) * 100.0, 1))
    rel = relative(ai, ex, int(p["window_sessions"]))
    if not rel:
        out.update(state="absent", reason=f"the two legs share fewer than "
                                          f"{p['window_sessions']} sessions")
        return out
    lz = st_r5_rates.lens(rel)
    out.update(state="computed", as_of=rel[-1][0], since=base,
               cum_ai_pct=cum["ai"], cum_ex_pct=cum["ex_ai"],
               rel_1y_pp=round(rel[-1][1], 1), lens=lz,
               lens_text=st_r5_rates.lens_text(lz))
    return out


def proxy_line(r: dict) -> str:
    head = f"{r['title']}, {r['ai']} against {r['ex_ai']}"
    if r.get("state") != "computed":
        return f"{head}: {r.get('reason')}."
    cum = ""
    if r.get("cum_ai_pct") is not None and r.get("cum_ex_pct") is not None:
        cum = (f"; since {r['since']}, {r['ai']} {r['cum_ai_pct']:+.1f}% against "
               f"{r['ex_ai']} {r['cum_ex_pct']:+.1f}%")
    tag = "" if r["label"] in r["title"] else f" ({r['label']})"
    return (f"{head}{tag}, to {r['as_of']}: one-year relative return "
            f"{r['rel_1y_pp']:+.1f} pp ({r['lens_text']}){cum}. {r['caveat']}")


# ---------------------------------------------------------------------------
# The whole read
# ---------------------------------------------------------------------------
def build(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    ppi = ppi_read({s["key"]: _pts(st, s["key"], cutoff) for s in cfg.get("ppi") or []},
                   cfg)
    p = cfg["proxy"]
    prox = proxy_read(_pts(st, p["ai"]["key"], cutoff), _pts(st, p["ex_ai"]["key"], cutoff),
                      cfg)
    gap = " ".join(str(cfg.get("credit_watch_gap") or "").split())
    return {"block": "ai_trade", "as_of": cutoff, "ppi": ppi, "proxy": prox,
            "credit_watch_gap": gap}


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.ai_trade")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso()
    with observations.ObservationStore() as st:
        b = build(st, cutoff)
    for ln in ppi_lines(b["ppi"]) + [proxy_line(b["proxy"]), b["credit_watch_gap"] + "."]:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

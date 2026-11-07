"""
The vol-state read (signal-triage Batch 23 item 124c(i), the order's 106c(i);
paste B134, 6 Nov 2026).

A daily state from five inputs, each a percentile over its own stored history:
VIX, the S&P 500's 20-day realised vol, VIX/VIX3M, VVIX and the count of
|return| >= 2% days in the last 20. The state score is the mean of the available
percentiles and the decile is its bin (config/vol_state.yaml, session-set: no
weight is fitted). Calibrated from 1990 as P(|return| >= 3% within the next 10
sessions | decile), with the 5- and 20-session transition base rates, in a ledger
written once (docs/ledgers/vol-state-calibration-2026-11.md) whose figures are
copied into the config as a dated table the print reads.

RIGHTS: a daily line and the sizing input to item 124g, through vol_state_k. No
regime, no dial, no composite: calc.vol_state.* is barred from the market-state
object (metrics_registry.yaml market_state_barred). Nothing here sizes anything.

The stored series (source `calc`, point in time: a row is available when the
latest input it read is):
    calc.vol_state.decile          1..10
    calc.vol_state.<input>_pct     vix_pct, rv20_pct, term_pct, vvix_pct, bigmove_pct

    python -m altdata.vol_state compute [--from D]    recent days (the features pass)
    python -m altdata.vol_state backfill [--dry-run]  the whole history
    python -m altdata.vol_state show                  the close's block, read-only
    python -m altdata.vol_state ledger --source public|store [--through D]
                                                      the calibration ledger, once
"""

from __future__ import annotations

import bisect
import datetime as dt
import functools
import hashlib
import logging
import math
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("altdata.vol_state")

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "vol_state.yaml"
LEDGER_DIR = REPO / "docs" / "ledgers"
SOURCE = "calc"
DECILE_KEY = "calc.vol_state.decile"
INPUT_IDS = ("vix", "rv20", "term", "vvix", "bigmove")
PCT_KEYS = {i: f"calc.vol_state.{i}_pct" for i in INPUT_IDS}
KEYS = [DECILE_KEY] + [PCT_KEYS[i] for i in INPUT_IDS]
CAL_FROM = "1990-01-02"
MAX_FILL_DAYS = 5          # a level carried at most five calendar days over a gap
NOT_STORED = "not stored"
NOT_BUILT = "not built"
BEGIN, END = "<!-- computation:begin -->", "<!-- computation:end -->"
CFG_BEGIN, CFG_END = "<!-- config:begin -->", "<!-- config:end -->"

COMPUTATION = """\
THE INPUTS, per S&P 500 session, as of its close:
  vix      VIX: FRED VIXCLS, Yahoo's ^VIX close where FRED has not published
  rv20     the sample standard deviation of the S&P 500's 20 daily log returns
           ending the day, times sqrt(252), in percent
  term     VIX over VIX3M, from 3 January 2007
  vvix     VVIX, from 3 January 2012
  bigmove  the count of sessions with |simple return| >= 2% among the 20
           ending the day
A level is carried at most five calendar days over a gap; an input before its
first day, or holding fewer than 252 values, is n/a.

THE PERCENTILE: an input's share of its own values from its first day to the
day, the day included, that are at or below the day's value (expanding, point
in time).

THE RULE (session-set, config/vol_state.yaml): the score is the unweighted mean
of the available percentiles (at least two); the decile is the score's bin, 1
below 10 up to 10 at 90 and above. No weight is fitted.

THE CALIBRATION, from 2 January 1990: for every session with a decile and ten
sessions after it, whether any of the next ten sessions' |simple return| is 3%
or more; per decile, n, the share, and its Wilson 95% interval. The sessions
overlap, so the interval is narrower than independent draws would give.
THE TRANSITIONS: per decile today, the share of sessions whose decile five and
twenty sessions on is the same, higher and lower, and the full matrix.
"""


def computation_sha256(text: str = COMPUTATION) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@functools.lru_cache(maxsize=1)
def _config_cached() -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def config() -> dict:
    return _config_cached()


def inputs(cfg: Optional[dict] = None) -> dict[str, dict]:
    return {x["id"]: x for x in (cfg or config())["inputs"]}


# ---------------------------------------------------------------------------
# The sizing hook (item 124g(ii); A130's module reads it by this name)
# ---------------------------------------------------------------------------
def vol_state_k(decile: Optional[int], cfg: Optional[dict] = None) -> Optional[float]:
    """The ATR multiple for a vol-state decile: the stop's floor (D8, 6 Nov
    2026). None when there is no state; the table is config's, session-set."""
    if decile is None:
        return None
    tbl = (cfg or config()).get("k_table") or {}
    v = tbl.get(int(decile), tbl.get(str(int(decile))))
    return None if v is None else float(v)


# ---------------------------------------------------------------------------
# The computation, on plain series: {name: [(day, value, available_at)]}
# ---------------------------------------------------------------------------
def decile_of(score: Optional[float]) -> Optional[int]:
    if score is None or not math.isfinite(score):
        return None
    return max(1, min(10, int(score // 10) + 1))


def combine(pcts: dict[str, Optional[float]], cfg: Optional[dict] = None
            ) -> tuple[Optional[float], Optional[int]]:
    """The declared rule: the mean of the available percentiles, and its bin."""
    rule = (cfg or config()).get("rule") or {}
    have = [v for v in pcts.values() if v is not None]
    if len(have) < int(rule.get("min_inputs") or 2):
        return None, None
    s = sum(have) / len(have)
    return s, decile_of(s)


def _asof_value(days: list[str], vals: list, avs: list, day: str):
    i = bisect.bisect_right(days, day) - 1
    if i < 0:
        return None, None
    gap = (dt.date.fromisoformat(day) - dt.date.fromisoformat(days[i])).days
    if gap > MAX_FILL_DAYS:
        return None, None
    return vals[i], avs[i]


def _index(rows: list[tuple]) -> tuple[list, list, list]:
    rows = sorted(rows)
    return [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows]


def merge_first(*series: list[tuple]) -> list[tuple]:
    """Day by day, the first series' value where it has one, else the next's."""
    out: dict[str, tuple] = {}
    for s in reversed(series):
        for d, v, a in s:
            out[d] = (d, v, a)
    return [out[d] for d in sorted(out)]


def daily_table(series: dict[str, list[tuple]], cfg: Optional[dict] = None
                ) -> list[dict]:
    """Every S&P 500 session's raw inputs, percentiles, score and decile.

    `series` holds "spx", "vix", "vix3m" and "vvix", each [(day, value,
    available_at)]; a missing name is an input never stored."""
    cfg = cfg or config()
    inp = inputs(cfg)
    min_hist = int(cfg.get("min_history") or 252)
    spx = sorted(series.get("spx") or [])
    if not spx:
        return []
    vix = _index(series.get("vix") or [])
    v3m = _index(series.get("vix3m") or [])
    vvx = _index(series.get("vvix") or [])
    bm = inp["bigmove"]
    thr, win = float(bm.get("threshold", 0.02)), int(bm.get("window", 20))
    hist: dict[str, list[float]] = {i: [] for i in INPUT_IDS}
    rets: list[float] = []
    lrets: list[float] = []
    out = []
    for n, (day, close, av) in enumerate(spx):
        if n:
            prev = spx[n - 1][1]
            rets.append(close / prev - 1.0)
            lrets.append(math.log(close / prev))
        raw: dict[str, Optional[float]] = {i: None for i in INPUT_IDS}
        avail = [av]
        if len(lrets) >= 20:
            w = lrets[-20:]
            m = sum(w) / 20
            raw["rv20"] = math.sqrt(sum((x - m) ** 2 for x in w) / 19) * math.sqrt(252) * 100
        if len(rets) >= win:
            raw["bigmove"] = float(sum(1 for x in rets[-win:] if abs(x) >= thr))
        vv, va = _asof_value(*vix, day)
        if vv is not None:
            raw["vix"] = vv
            avail.append(va)
            tv, ta = _asof_value(*v3m, day)
            if tv:
                raw["term"] = vv / tv
                avail.append(ta)
        xv, xa = _asof_value(*vvx, day)
        if xv is not None:
            raw["vvix"] = xv
            avail.append(xa)
        pcts: dict[str, Optional[float]] = {}
        for i in INPUT_IDS:
            v = raw[i]
            if v is None or day < str(inp[i].get("from") or "0000"):
                raw[i], pcts[i] = None, None
                continue
            h = hist[i]
            bisect.insort(h, v)
            pcts[i] = (bisect.bisect_right(h, v) / len(h) * 100) if len(h) >= min_hist else None
        score, dec = combine(pcts, cfg)
        av_max = max((a for a in avail if a), default=None)
        out.append({"day": day, "raw": raw, "pct": pcts, "score": score, "decile": dec,
                    "ret": rets[-1] if n else None, "available_at": av_max})
    return out


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[Optional[float], Optional[float]]:
    if n <= 0:
        return None, None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def calibrate(table: list[dict], cfg: Optional[dict] = None,
              since: str = CAL_FROM) -> dict:
    """P(|r| >= big within the next `horizon` sessions | decile), n and Wilson;
    and the decile transitions at 5 and 20 sessions."""
    cfg = cfg or config()
    cal = cfg.get("calibration") or {}
    big, hz = float(cal.get("big_move", 0.03)), int(cal.get("horizon", 10))
    t = [r for r in table if r["day"] >= since]
    rets = [abs(r["ret"]) if r["ret"] is not None else 0.0 for r in t]
    out: dict[int, dict] = {d: {"n": 0, "k": 0, "t5": [0] * 10, "t20": [0] * 10}
                            for d in range(1, 11)}
    for i, r in enumerate(t):
        d = r["decile"]
        if d is None:
            continue
        if i + hz < len(t):
            out[d]["n"] += 1
            out[d]["k"] += any(x >= big for x in rets[i + 1: i + hz + 1])
        for h, key in ((5, "t5"), (20, "t20")):
            if i + h < len(t) and t[i + h]["decile"] is not None:
                out[d][key][t[i + h]["decile"] - 1] += 1
    total_n = sum(v["n"] for v in out.values())
    total_k = sum(v["k"] for v in out.values())
    for d, v in out.items():
        lo, hi = wilson(v["k"], v["n"])
        v["p"] = v["k"] / v["n"] if v["n"] else None
        v["lo"], v["hi"] = lo, hi
        for key in ("t5", "t20"):
            m = v[key]
            s = sum(m)
            v[key + "_odds"] = ({"same": m[d - 1] / s, "higher": sum(m[d:]) / s,
                                 "lower": sum(m[:d - 1]) / s} if s else None)
    days = [r["day"] for r in t if r["decile"] is not None]
    return {"deciles": out, "first": days[0] if days else None,
            "last": days[-1] if days else None, "n": total_n,
            "p_all": total_k / total_n if total_n else None, "big": big, "horizon": hz}


def config_table(cal: dict) -> dict:
    """The dated table copied into config/vol_state.yaml's calibration.deciles."""
    out = {}
    for d, v in cal["deciles"].items():
        row = {"n": v["n"], "p": None if v["p"] is None else round(v["p"], 4),
               "lo": None if v["lo"] is None else round(v["lo"], 4),
               "hi": None if v["hi"] is None else round(v["hi"], 4)}
        for key in ("t5", "t20"):
            o = v.get(key + "_odds")
            row[key] = None if o is None else {k: round(x, 4) for k, x in o.items()}
        out[d] = row
    return out


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
def _store_series(st, key: str, as_of: Optional[str]) -> list[tuple]:
    pts: dict[str, tuple] = {}
    for r in st.as_of(key, as_of=as_of):
        v = r.get("value_num")
        if v is None or not math.isfinite(float(v)):
            continue
        d = str(r["observed_at"])[:10]
        pts[d] = (d, float(v), str(r["available_at"]))
    return [pts[d] for d in sorted(pts)]


def store_series(st, as_of: Optional[str] = None, cfg: Optional[dict] = None
                 ) -> dict[str, list[tuple]]:
    inp = inputs(cfg)
    vix = merge_first(*[_store_series(st, k, as_of) for k in inp["vix"]["keys"]])
    return {"spx": _store_series(st, inp["rv20"]["keys"][0], as_of), "vix": vix,
            "vix3m": _store_series(st, inp["term"]["keys"][0], as_of),
            "vvix": _store_series(st, inp["vvix"]["keys"][0], as_of)}


def compute_rows(st, as_of: Optional[str] = None, first_day: Optional[str] = None,
                 cfg: Optional[dict] = None) -> list[dict]:
    rows = []
    for r in daily_table(store_series(st, as_of, cfg), cfg):
        if r["decile"] is None or (first_day and r["day"] < first_day):
            continue
        base = {"instrument": None, "observed_at": r["day"],
                "available_at": r["available_at"], "source": SOURCE,
                "availability_kind": None}
        rows.append({**base, "registry_key": DECILE_KEY, "value": float(r["decile"])})
        for i in INPUT_IDS:
            if r["pct"][i] is not None:
                rows.append({**base, "registry_key": PCT_KEYS[i],
                             "value": round(r["pct"][i], 4)})
    return rows


def default_first_day(db, as_of: Optional[str] = None) -> str:
    """30 days before the newest stored decile, else before the cutoff: the
    features pass never runs the history by itself (backfill is the operator's)."""
    last = db.last_observed(keys=[DECILE_KEY])
    from altdata import session                                 # noqa: PLC0415
    base = last or (as_of or session.utc_iso())[:10]
    return (dt.date.fromisoformat(str(base)[:10]) - dt.timedelta(days=30)).isoformat()


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store=None, dry_run: bool = False) -> dict:
    from altdata import observations                            # noqa: PLC0415
    own = store is None
    db = store or observations.open_writer(__name__)
    try:
        rows = compute_rows(db, as_of, first_day)
        written = 0 if dry_run else db.write_many(observations.drop_unchanged(db, rows))
        return {"computed": len(rows), "written": written, "dry_run": dry_run,
                "first_day": first_day}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# The read: what the close prints, from stored rows only
# ---------------------------------------------------------------------------
def _span(st, keys: list[str], as_of_day: str) -> Optional[str]:
    firsts = []
    for k in keys:
        row = st.conn.execute("SELECT MIN(observed_at) FROM observations WHERE "
                              "registry_key = ?", (k,)).fetchone()
        if row and row[0]:
            firsts.append(str(row[0])[:10])
    return min(firsts) if firsts else None


def window_text(start: Optional[str]) -> str:
    """The percentile's window: A126's derived.window_label where it exists (the
    one label builder; chain-13 merges it before this), else its full-history
    form, the same words."""
    from altdata import derived                                 # noqa: PLC0415
    lab = getattr(derived, "window_label", None)
    if lab is not None:
        return lab("full", start=start)
    return f"full history from {start}" if start else "full history"


def read(st, now: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    inp = inputs(cfg)
    dec = st.latest_as_of(DECILE_KEY, now)
    if not dec:
        return {"decile": None, "reason": f"{DECILE_KEY} {NOT_STORED}"}
    day = str(dec["observed_at"])[:10]
    rows = []
    for i in INPUT_IDS:
        spec = inp[i]
        p = [r for r in st.as_of(PCT_KEYS[i], as_of=now, observed_from=day)
             if str(r["observed_at"])[:10] == day]
        start = _span(st, spec["keys"], day)
        if p:
            pct, why = float(p[-1]["value_num"]), None
        elif start is None:
            pct, why = None, f"n/a ({', '.join(spec['keys'])} {NOT_STORED})"
        elif day < str(spec.get("from")):
            pct, why = None, f"n/a (from {spec.get('from')})"
        else:
            pct, why = None, "n/a (short history)"
        lo = max(start or "", str(spec.get("from") or ""))
        rows.append({"id": i, "label": spec["label"], "pct": pct, "why": why,
                     "window": window_text(lo or None) if start else NOT_STORED})
    d = int(dec["value_num"])
    cal = (cfg.get("calibration") or {})
    crow = (cal.get("deciles") or {}).get(d) or (cal.get("deciles") or {}).get(str(d))
    return {"decile": d, "day": day, "inputs": rows, "calibration": crow,
            "cal_as_of": cal.get("as_of"), "cal_ledger": cal.get("ledger"),
            "big": cal.get("big_move", 0.03), "horizon": cal.get("horizon", 10),
            "k": vol_state_k(d, cfg)}


def _pc(x: Optional[float], nd: int = 0) -> str:
    return "n/a" if x is None else f"{x * 100:.{nd}f}%"


def block(r: dict) -> dict:
    """The close's Mechanics sub-section: today's decile, the five inputs with
    their percentiles and windows, the calibrated probability with its n, the 5-
    and 20-session transition odds and the sizing hook's value."""
    title = "Vol state"
    if r.get("decile") is None:
        return {"title": title, "table": None, "paragraph_wanted": False,
                "lines": [f"Vol state: not computed ({r.get('reason')})."]}
    lines = [f"Vol state: decile {r['decile']} of 10, as of {r['day']} (the mean of "
             f"the available input percentiles, a session-set rule; no regime, no "
             f"dial)."]
    c = r.get("calibration")
    if c and c.get("n"):
        lines.append(
            f"Calibrated from 1990 (ledger of {r['cal_as_of']}): P(|return| ≥ "
            f"{r['big'] * 100:.0f}% within {r['horizon']} sessions | decile "
            f"{r['decile']}) = {_pc(c.get('p'), 1)}, n {c['n']:,}, 95% interval "
            f"{_pc(c.get('lo'), 1)}–{_pc(c.get('hi'), 1)}.")
        parts = []
        for key, h in (("t5", 5), ("t20", 20)):
            o = c.get(key)
            if o:
                parts.append(f"in {h} sessions, same decile {_pc(o['same'])}, "
                             f"higher {_pc(o['higher'])}, lower {_pc(o['lower'])}")
        if parts:
            lines.append("Transitions: " + "; ".join(parts) + ".")
    else:
        lines.append("Calibration: not in config (the ledger's table is not copied).")
    lines.append(f"Sizing input (item 124g, vol_state_k): ATR multiple "
                 f"{r['k']:g}, session-set." if r.get("k") is not None else
                 f"Sizing input (item 124g, vol_state_k): {NOT_BUILT}.")
    table = {"columns": ["Input", "Percentile", "Window"],
             "rows": [[x["label"], f"{x['pct']:.0f}" if x["pct"] is not None else x["why"],
                       x["window"]] for x in r["inputs"]]}
    return {"title": title, "table": table, "paragraph_wanted": False, "lines": lines}


def week_row(st, now: str, sessions: list[str]) -> str:
    """The Weekly's one row: the week's deciles, session by session."""
    if not sessions:
        return "Vol state, the week: no sessions."
    got = {str(r["observed_at"])[:10]: int(r["value_num"])
           for r in st.as_of(DECILE_KEY, as_of=now, observed_from=sessions[0])
           if r.get("value_num") is not None}
    cells = []
    for s in sessions:
        wd = dt.date.fromisoformat(s).strftime("%a")
        cells.append(f"{wd} {got[s]}" if s in got else f"{wd} n/a")
    return "Vol state, the week (decile of 10): " + " · ".join(cells) + "."


# ---------------------------------------------------------------------------
# The ledger, written once
# ---------------------------------------------------------------------------
def public_series(through: Optional[str] = None) -> dict[str, list[tuple]]:
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    from altdata.sources import yfinance_source as yfs          # noqa: PLC0415

    def yf(sym):
        return [(d, float(v), None) for d, v in yfs._fetch_symbol(sym, period="max")["closes"]  # noqa: SLF001
                if v is not None and float(v) > 0]
    out = {"spx": yf("^GSPC"), "vix": [(d, v, None) for d, v in S.fred("VIXCLS")],
           "vix3m": yf("^VIX3M"), "vvix": yf("^VVIX")}
    if through:
        out = {k: [r for r in v if r[0] <= through] for k, v in out.items()}
    return out


def ledger_text(series: dict, via: str, edition: str, cfg: Optional[dict] = None) -> tuple[str, dict]:
    import yaml                                                 # noqa: PLC0415
    cfg = cfg or config()
    table = daily_table(series, cfg)
    cal = calibrate(table, cfg)
    ct = config_table(cal)
    L = [f"# Vol-state calibration (item 124c(i)), {edition}", "",
         "*Written once by `python -m altdata.vol_state ledger`; refreshed yearly by "
         "the Annual Structural Review as a new dated file, never edited by hand. "
         "Signal-triage Batch 23 item 124c(i) (the order's 106c(i)); paste B134.*", "",
         "**Pre-registered:** the rule, the sample and the computation below, with "
         "its SHA-256. A re-run applies it and may not change it.", "",
         "| | |", "|---|---|",
         f"| As of | {cal['last']} |",
         f"| Sample | sessions with a decile, {cal['first']} to {cal['last']}; n = "
         f"{cal['n']:,} with {cal['horizon']} sessions after them |",
         f"| Sources | {via} |",
         "| Rule | the unweighted mean of the available input percentiles (at least "
         "two); the decile is its bin (config/vol_state.yaml, session-set) |",
         f"| Statistic | P(|return| ≥ {cal['big'] * 100:.0f}% within the next "
         f"{cal['horizon']} sessions \\| decile), Wilson 95%; decile transitions at 5 "
         f"and 20 sessions |",
         "| Pass rule | none: the order grants a daily line and the sizing input, "
         "and states no gate |",
         f"| Unconditional rate | {_pc(cal['p_all'], 1)} |",
         f"| Computation SHA-256 | `{computation_sha256()}` |", "",
         "## The computation", "", BEGIN, "```text", COMPUTATION.rstrip("\n"), "```",
         END, "", "## P(|return| ≥ 3% within 10 sessions | decile)", "",
         "| Decile | n | hits | P | 95% interval |", "|---|---|---|---|---|"]
    for d in range(1, 11):
        v = cal["deciles"][d]
        L.append(f"| {d} | {v['n']:,} | {v['k']:,} | {_pc(v['p'], 1)} | "
                 f"{_pc(v['lo'], 1)}–{_pc(v['hi'], 1)} |")
    for key, h in (("t5", 5), ("t20", 20)):
        L += ["", f"## Transitions, {h} sessions on", "",
              "| Decile today | same | higher | lower | " + " | ".join(
                  f"→{j}" for j in range(1, 11)) + " |",
              "|---|---|---|---|" + "---|" * 10]
        for d in range(1, 11):
            v = cal["deciles"][d]
            o = v.get(key + "_odds")
            m = v[key]
            L.append(f"| {d} | " + (" | ".join(_pc(o[x]) for x in ("same", "higher", "lower"))
                                     if o else "n/a | n/a | n/a")
                     + " | " + " | ".join(f"{x:,}" for x in m) + " |")
    L += ["", "## The config table", "",
          "Copied into `config/vol_state.yaml` `calibration.deciles`; "
          "`tools/validate_item_124_c1.py` holds the two equal.", "",
          CFG_BEGIN, "```yaml",
          yaml.safe_dump(ct, sort_keys=True, default_flow_style=None).rstrip(), "```",
          CFG_END, "",
          "## Caveats", "",
          "- The sessions overlap (a ten-session window per day), so the Wilson "
          "intervals are narrower than independent draws would give.",
          "- The inputs enter at different dates (VIX/VIX3M from 2007, VVIX from "
          "2012), so the score averages three inputs before 2007 and four before "
          "2012: the same decile is a slightly different state across the sample.",
          "- A base rate to read beside the day's state, not a forecast."]
    return "\n".join(L) + "\n", ct


def ledger_config_block(text: str) -> dict:
    import yaml                                                 # noqa: PLC0415
    body = text.split(CFG_BEGIN, 1)[1].split(CFG_END, 1)[0]
    body = body.strip().removeprefix("```yaml").removesuffix("```")
    return yaml.safe_load(body)


def ledger_sha(text: str) -> str:
    body = text.split(BEGIN, 1)[1].split(END, 1)[0]
    body = body.strip().removeprefix("```text").removesuffix("```").strip("\n") + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    from altdata import observations, session                   # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.vol_state")
    ap.add_argument("cmd", choices=["compute", "backfill", "show", "ledger"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--from", dest="first", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--source", choices=["store", "public"], default="store")
    ap.add_argument("--through", default=None)
    ap.add_argument("--edition", default=None, help="YYYY-MM (default: this month)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.stdout.reconfigure(encoding="utf-8")
    if a.cmd in ("compute", "backfill"):
        with observations.ObservationStore(a.db) as st:
            first = None if a.cmd == "backfill" else (a.first or default_first_day(st, a.as_of))
            r = compute(a.as_of, first, st, a.dry_run)
        print(f"{r['computed']} rows computed, {r['written']} written"
              + ("  (dry run)" if r["dry_run"] else ""))
        return 0
    if a.cmd == "show":
        from altdata import trend_breadth                       # noqa: PLC0415
        st = trend_breadth.open_ro(a.db)
        try:
            b = block(read(st, a.as_of or session.utc_iso()))
        finally:
            st.conn.close()
        for ln in b["lines"]:
            print(ln)
        for row in (b.get("table") or {}).get("rows") or []:
            print(" | ".join(str(c) for c in row))
        return 0
    edition = a.edition or (a.through or session.utc_iso())[:7]
    path = LEDGER_DIR / f"vol-state-calibration-{edition}.md"
    if path.exists():
        raise SystemExit(f"{path} exists: a ledger is written once; the yearly "
                         f"refresh is a new dated file")
    if a.source == "public":
        series = public_series(a.through)
        via = ("^GSPC, ^VIX3M and ^VVIX through the yfinance writer's reader (Yahoo "
               "Finance); VIXCLS from FRED's public graph CSV (the laptop's first "
               "edition; the box's run from the store supersedes it)")
    else:
        from altdata import trend_breadth                       # noqa: PLC0415
        st = trend_breadth.open_ro(a.db)
        try:
            series = store_series(st, a.through)
        finally:
            st.conn.close()
        via = "the store's yfinance.mkt_gspc, fred.vix, yfinance.mkt_vix, .mkt_vix3m, .mkt_vvix"
    text, _ = ledger_text(series, via, edition)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(path)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))

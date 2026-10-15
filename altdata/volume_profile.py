"""
The volume profile: where volume traded by price over a window. (VP-1, ruled
14 Oct 2026; docs/volume-profile.md)

    from altdata import volume_profile as vp
    prof = vp.profile(bars, bin_bps=5)                # pure: bars -> the profile
    win = vp.window(store, "spy", "prior_week", "2026-10-09", as_of=cutoff)
    book = vp.windows(store, "spy", "2026-10-09", as_of=cutoff)   # all six

    python -m altdata.volume_profile compute [--from DATE|first] [--dry-run]
    python -m altdata.volume_profile coverage --instrument spy --sessions 40
    python -m altdata.volume_profile compare  --instrument spy --sessions 40

ONE MODULE, EVERY READER. The level list (altdata/levels.py), the close's and
the Weekly's and the Monthly's tables, C1's shading, W7's side panel, the Book B
scanner's clause and the stored calc.vp_* series all call this module; none bins
volume itself. The settings are config/volume_profile.yaml, each session-set.

THE DEFINITION, in the order the brief gives it:

1. BINS. A fixed grid at integer multiples of the bin width. The width is
   bin_bps of the window's last close, rounded DOWN to the nearest step of the
   ladder (0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1, 2, 5, 10): 5 bps for 5-minute
   profiles, 25 for profiles from daily bars. This is "rounded to a round tick"
   in H-006 to H-008.
2. VOLUME AT PRICE. A bar's volume is spread evenly over its high-low range;
   each bin takes the share of the range it covers. A bar with high = low puts
   all its volume in its one bin.
3. POC. The bin with the most volume. A tie goes to the bin nearest the
   window's volume-weighted mean price (the profile's own: each bin's midpoint
   weighted by its volume), then to the lower. Its value is the bin's midpoint.
4. VALUE AREA. value_area_share of the window's volume, built outward from the
   POC: the next two bins above against the next two below (fewer where the
   profile ends), the larger pair added, both on a tie, until the share is
   reached. VAH is the upper edge of the highest bin in the area, VAL the lower
   edge of the lowest.
5. NODES. The profile over the bins between the window's low and high,
   smoothed by a centred 5-bin mean (truncated at the ends). An HVN is a local
   maximum of the smoothed profile at or above its 80th percentile; an LVN a
   local minimum at or below its 20th. Interior bins only: the tails are not
   nodes. A plateau counts once, at its first bin.
6. COMPLETENESS. A window of 5-minute bars is computed only when its bars reach
   bars.complete_share of the expected count in aggregate; otherwise it is
   absent with the reason, naming every session below the share -- as VWAP is.
7. ONE SOURCE PER WINDOW. Bars from more than one source in a window (6b's
   history beside Yahoo's) make the window absent with the reason. Never mixed.
8. AS OF. Every read goes through BarStore.read(as_of=...) -- the bars table's
   as-of read -- or, for daily bars, ObservationStore.as_of (derived.py rule 1).
   A profile from daily bars says "approximated from daily bars" wherever it
   prints.

WHAT IT IS NOT. The profile describes where volume traded. Nothing here, and
nothing that prints it, says a level will hold or a node will be crossed
quickly: those are H-006 to H-008, the Alpha Lab's to test. No backtest lives
in this repository.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

from . import bars as bars_mod, session

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "volume_profile.yaml"

DAILY_NOTE = "approximated from daily bars"
EPS = 1e-9

# The six windows, in the level list's order: (id, label prefix, prior?).
WINDOWS = (("session", "session's", False),
           ("prior_session", "prior session's", True),
           ("week", "week's", False),
           ("prior_week", "prior week's", True),
           ("month", "month's", False),
           ("prior_month", "prior month's", True))
WINDOW_IDS = tuple(w for w, _, _ in WINDOWS)
PRIOR_WINDOWS = tuple(w for w, _, p in WINDOWS if p)
FIELDS = (("poc", "point of control"), ("vah", "value-area high"),
          ("val", "value-area low"))


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def instrument_ids(cfg: Optional[dict] = None) -> list[str]:
    return [str(x) for x in (cfg or load_config()).get("instruments") or []]


def level_key(window: str, field: str) -> str:
    """The level list's field name: vp_prior_week_vah."""
    return f"vp_{window}_{field}"


def level_label(window: str, field: str) -> str:
    """"prior week's value-area high"."""
    pre = dict((w, p) for w, p, _ in WINDOWS)[window]
    return f"{pre} {dict(FIELDS)[field]}"


LEVEL_TYPES = tuple((level_key(w, f), level_label(w, f))
                    for w, _, _ in WINDOWS for f, _ in FIELDS)


# ---------------------------------------------------------------------------
# 1-5. The profile, from bars. Pure: no store, no clock.
# ---------------------------------------------------------------------------
def bin_width(last_close: float, bin_bps: float, ladder: Iterable[float]) -> float:
    """bin_bps of the last close, rounded DOWN to the ladder (never below its
    first step)."""
    raw = abs(float(last_close)) * float(bin_bps) / 1e4
    steps = sorted(float(x) for x in ladder)
    best = steps[0]
    for s in steps:
        if s <= raw + EPS:
            best = s
    return best


def _k(price: float, w: float) -> int:
    return int(math.floor(price / w + EPS))


def _span(lo: float, hi: float, w: float) -> tuple[int, int]:
    """The first and last bin a range [lo, hi] covers. A high exactly on a bin
    edge covers none of the bin above it."""
    k0, k1 = _k(lo, w), _k(hi, w)
    if k1 > k0 and abs(hi / w - round(hi / w)) < EPS:
        k1 -= 1
    return k0, k1


def volume_at_price(bars: list[dict], w: float) -> dict[int, float]:
    """bin index -> volume: each bar's volume spread evenly over its range."""
    out: dict[int, float] = {}
    for b in bars:
        v = float(b.get("volume") or 0.0)
        if v <= 0:
            continue
        lo, hi = float(b["low"]), float(b["high"])
        k0, k1 = _span(lo, hi, w)
        if hi - lo <= EPS * max(1.0, abs(hi)) or k0 == k1:
            out[k0] = out.get(k0, 0.0) + v
            continue
        span = hi - lo
        for k in range(k0, k1 + 1):
            cover = min(hi, (k + 1) * w) - max(lo, k * w)
            if cover > 0:
                out[k] = out.get(k, 0.0) + v * cover / span
    return out


def _percentile(vals: list[float], q: float) -> float:
    """Linear interpolation between closest ranks (numpy's default)."""
    xs = sorted(vals)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q / 100.0
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def profile(bars: list[dict], bin_bps: float, cfg: Optional[dict] = None,
            daily: bool = False) -> dict:
    """The profile of `bars` (dicts with high, low, close, volume, in time
    order). Returns the bins, the POC, the value area and the nodes, or
    {"absent": reason}."""
    cfg = cfg or load_config()
    if not bars:
        return {"absent": "no bars in the window"}
    last = float(bars[-1]["close"])
    w = bin_width(last, bin_bps, cfg.get("tick_ladder") or (0.01,))
    vap = volume_at_price(bars, w)
    total = sum(vap.values())
    if total <= 0:
        return {"absent": "no volume on the window's bars"}
    spans = [_span(float(b["low"]), float(b["high"]), w) for b in bars]
    kmin, kmax = min(a for a, _ in spans), max(b for _, b in spans)
    ks = list(range(kmin, kmax + 1))
    vol = [vap.get(k, 0.0) for k in ks]
    mean_px = sum((k + 0.5) * w * vap.get(k, 0.0) for k in ks) / total
    # 3. POC
    top = max(vol)
    tied = [k for k, v in zip(ks, vol) if _close(v, top)]
    poc_k = min(tied, key=lambda k: (round(abs((k + 0.5) * w - mean_px) / w, 9), k))
    # 4. Value area
    share = float(cfg.get("value_area_share", 0.70))
    target = share * total
    idx = {k: i for i, k in enumerate(ks)}
    lo_i = hi_i = idx[poc_k]
    acc = vol[lo_i]
    steps: list[float] = []              # the volume each step added, in order
    while acc < target - 1e-9 * total:
        up = vol[hi_i + 1:hi_i + 3]
        dn = vol[max(0, lo_i - 2):lo_i][::-1]
        if not up and not dn:
            break
        su, sd = sum(up), sum(dn)
        if up and (not dn or su > sd + 1e-12 * total):
            hi_i += len(up)
            acc += su
            steps.append(su)
        elif dn and (not up or sd > su + 1e-12 * total):
            lo_i -= len(dn)
            acc += sd
            steps.append(sd)
        else:                            # a tie: both pairs
            hi_i += len(up)
            lo_i -= len(dn)
            acc += su + sd
            steps.append(su + sd)
    val, vah = ks[lo_i] * w, (ks[hi_i] + 1) * w
    # 5. Nodes
    n = int(cfg.get("node_smoothing_bins", 5))
    half = n // 2
    sm = [sum(vol[max(0, i - half):i + half + 1]) / len(vol[max(0, i - half):i + half + 1])
          for i in range(len(vol))]
    hi_cut = _percentile(sm, float(cfg.get("hvn_percentile", 80)))
    lo_cut = _percentile(sm, float(cfg.get("lvn_percentile", 20)))
    hvn, lvn = [], []
    tol = 1e-12 * max(sm)
    for i in range(1, len(sm) - 1):
        # Interior bins only: the profile's tails are not nodes. A plateau
        # counts once, at its first bin -- strictly beyond the left neighbour,
        # at least level with the right.
        s, left, right = sm[i], sm[i - 1], sm[i + 1]
        if s > left + tol and s >= right - tol and s >= hi_cut - tol:
            hvn.append(round((ks[i] + 0.5) * w, 4))
        if s < left - tol and s <= right + tol and s <= lo_cut + tol:
            lvn.append(round((ks[i] + 0.5) * w, 4))
    return {"bin_width": w, "bin_bps": bin_bps, "n_bins": len(ks),
            "first_bin": ks[0], "volume": vol, "total_volume": total,
            "mean_price": mean_px,
            "poc": round((poc_k + 0.5) * w, 4), "vah": round(vah, 4),
            "val": round(val, 4), "value_area_volume": acc,
            "value_area_share": acc / total, "va_steps": steps,
            "hvn": hvn, "lvn": lvn, "last_close": last, "daily": daily,
            "note": DAILY_NOTE if daily else None}


# ---------------------------------------------------------------------------
# 6-8. The windows: sessions, completeness, one source, as of.
# ---------------------------------------------------------------------------
def _d(x: Any) -> dt.date:
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def _sessions_between(first: dt.date, last: dt.date) -> list[str]:
    out, d = [], first
    while d <= last:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def window_sessions(window_id: str, day: Any) -> list[str]:
    """The sessions in a window, as of the session `day`.

    session        the day itself
    prior_session  the session before it
    week           Monday of the day's week to the day
    prior_week     the whole calendar week before
    month          the 1st of the day's month to the day
    prior_month    the whole calendar month before
    """
    d = _d(day)
    if window_id == "session":
        return [d.isoformat()]
    if window_id == "prior_session":
        return [session.previous_trading_session(d).isoformat()]
    mon = d - dt.timedelta(days=d.weekday())
    if window_id == "week":
        return _sessions_between(mon, d)
    if window_id == "prior_week":
        return _sessions_between(mon - dt.timedelta(days=7), mon - dt.timedelta(days=1))
    first = d.replace(day=1)
    if window_id == "month":
        return _sessions_between(first, d)
    if window_id == "prior_month":
        end = first - dt.timedelta(days=1)
        return _sessions_between(end.replace(day=1), end)
    raise ValueError(f"unknown window {window_id!r}")


def trailing_sessions(day: Any, n: int) -> list[str]:
    """The n sessions ending at `day` (the rolling composite)."""
    d = _d(day)
    out = [d.isoformat()] if session.is_trading_session(d) else []
    while len(out) < n:
        d = session.previous_trading_session(d)
        out.insert(0, d.isoformat())
    return out


def complete_share(rcfg: Optional[dict] = None) -> float:
    """The bars table's own rule (config/reporting_stack.yaml bars.complete_share),
    so a profile and the session's VWAP are absent under the same rule."""
    rcfg = rcfg or bars_mod.load_config()
    return float((rcfg.get("bars") or {}).get("complete_share") or 0.9)


def session_bars(store, instrument: str, sessions: list[str],
                 as_of: Optional[str] = None) -> tuple[list[dict], dict]:
    """Every counted 5-minute bar of `sessions`, through the bars table's as-of
    read, and {session: (bars, expected)}."""
    rows, counts = [], {}
    for s in sessions:
        first, last, expected = bars_mod.session_window(instrument, s)
        got = store.read(instrument, "5m", first, last, as_of)
        rows.extend(got)
        counts[s] = (len(got), expected)
    return rows, counts


def check_window(bars: list[dict], counts: dict, share: float) -> Optional[str]:
    """None when a window may be computed; else why it is absent (rules 6, 7)."""
    n = sum(c[0] for c in counts.values())
    exp = sum(c[1] for c in counts.values())
    if not exp:
        return "no sessions in the window"
    if n / exp < share:
        short = [f"{s} ({c[0]} of {c[1]})" for s, c in sorted(counts.items())
                 if not c[1] or c[0] / c[1] < share]
        return (f"bars incomplete (n={n} of {exp})"
                + (f"; below the share: {', '.join(short)}" if short else ""))
    srcs = sorted({str(b.get("source") or "unknown") for b in bars})
    if len(srcs) > 1:
        return (f"bars from more than one source ({', '.join(srcs)}); a window "
                f"never mixes sources")
    return None


def from_bars(bars: list[dict], counts: dict, cfg: Optional[dict] = None,
              share: Optional[float] = None) -> dict:
    """A 5-minute window's profile under the completeness and source rules."""
    cfg = cfg or load_config()
    share = complete_share() if share is None else share
    why = check_window(bars, counts, share)
    if why:
        return {"absent": why}
    prof = profile(bars, float((cfg.get("bin_bps") or {}).get("five_minute", 5)), cfg)
    if "absent" in prof:
        return prof
    prof.update(sessions=sorted(counts), n_bars=len(bars),
                available_at=max(str(b["available_at"]) for b in bars),
                source=str(bars[0].get("source") or "unknown"))
    return prof


def window(store, instrument: str, window_id: str, day: Any,
           as_of: Optional[str] = None, cfg: Optional[dict] = None,
           share: Optional[float] = None) -> dict:
    """One window's profile for one instrument, read as of `as_of`."""
    sessions = window_sessions(window_id, day)
    if not sessions:
        return {"absent": "no sessions in the window", "window": window_id}
    bars, counts = session_bars(store, instrument, sessions, as_of)
    out = from_bars(bars, counts, cfg, share)
    out["window"] = window_id
    out.setdefault("sessions", sessions)
    return out


def windows(store, instrument: str, day: Any, as_of: Optional[str] = None,
            cfg: Optional[dict] = None, share: Optional[float] = None) -> dict:
    """All six windows: {window id: profile, or {"absent": reason}}."""
    cfg = cfg or load_config()
    return {w: window(store, instrument, w, day, as_of, cfg, share)
            for w in WINDOW_IDS}


def summary(prof: dict) -> dict:
    """What a level list or a payload carries of a profile: never the bins."""
    keep = ("window", "poc", "vah", "val", "hvn", "lvn", "bin_width", "sessions",
            "n_bars", "source", "available_at", "absent", "note")
    return {k: prof[k] for k in keep if k in prof}


# ---------------------------------------------------------------------------
# Daily bars: the approximation (the scanner's readings, `compare`)
# ---------------------------------------------------------------------------
def daily_profile(rows: list[dict], cfg: Optional[dict] = None) -> dict:
    """A profile from daily OHLCV rows, at the daily bin width, and said to be
    an approximation. A session without volume makes the window absent."""
    cfg = cfg or load_config()
    if not rows:
        return {"absent": "no daily bars in the window", "note": DAILY_NOTE}
    missing = [r for r in rows if r.get("volume") is None]
    if missing:
        return {"absent": f"daily volume not stored for {len(missing)} of "
                          f"{len(rows)} session(s)", "note": DAILY_NOTE}
    prof = profile(rows, float((cfg.get("bin_bps") or {}).get("daily", 25)), cfg,
                   daily=True)
    prof["note"] = DAILY_NOTE
    return prof


def daily_rows(db, key: str, first: str, last: str,
               as_of: Optional[str] = None) -> list[dict]:
    """Daily OHLCV for one price key (yfinance.mkt_spy with its _high, _low and
    _volume companions), through ObservationStore.as_of (derived.py rule 1)."""
    def load(k: str) -> dict:
        return {str(r["observed_at"])[:10]: r["value_num"] for r in db.as_of(k, as_of)
                if r.get("value_num") is not None}
    c, h, lo, v = (load(key), load(key + "_high"), load(key + "_low"),
                   load(key + "_volume"))
    return [{"observed_at": d, "close": c[d], "high": h.get(d, c[d]),
             "low": lo.get(d, c[d]), "volume": v.get(d)}
            for d in sorted(c) if first <= d <= last]


# ---------------------------------------------------------------------------
# The tables: migration and close against value, by declared rule
# ---------------------------------------------------------------------------
MIGRATIONS = ("higher", "lower", "unchanged", "inside", "outside",
              "overlapping higher", "overlapping lower")
WINDOW_NAMES = {"session": "session", "prior_session": "prior session",
                "week": "week", "prior_week": "prior week", "month": "month",
                "prior_month": "prior month"}
TABLE_COLUMNS = ("Market", "Value area (POC)", None, "Migration", "Close vs value")


def migration(cur: dict, prior: dict) -> Optional[str]:
    """The value area against the prior one.

    higher              VAL above the prior VAH
    lower               VAH below the prior VAL
    unchanged           both edges equal
    inside              within the prior area
    outside             containing it
    overlapping higher  both edges higher, still overlapping
    overlapping lower   both edges lower, still overlapping
    """
    try:
        vah, val = round(float(cur["vah"]), 4), round(float(cur["val"]), 4)
        pvah, pval = round(float(prior["vah"]), 4), round(float(prior["val"]), 4)
    except (KeyError, TypeError, ValueError):
        return None
    if vah == pvah and val == pval:
        return "unchanged"
    if val > pvah:
        return "higher"
    if vah < pval:
        return "lower"
    if val >= pval and vah <= pvah:
        return "inside"
    if val <= pval and vah >= pvah:
        return "outside"
    if val > pval and vah > pvah:
        return "overlapping higher"
    return "overlapping lower"


def close_vs_value(close: Optional[float], cur: dict) -> Optional[str]:
    """Above the VAH, inside, or below the VAL."""
    if close is None or cur.get("vah") is None or cur.get("val") is None:
        return None
    if close > cur["vah"]:
        return "above the VAH"
    if close < cur["val"]:
        return "below the VAL"
    return "inside"


def _px(v: float, unit: Optional[str]) -> str:
    if unit == "$":
        return f"${v:,.2f}"
    return f"{v:,.2f} {unit}" if unit else f"{v:,.2f}"


def area_text(prof: Optional[dict], unit: Optional[str] = None) -> str:
    """"$661.25–$664.75 (POC $663.10)", or "not computed"."""
    if not prof or prof.get("poc") is None:
        return "not computed"
    return (f"{_px(prof['val'], unit)}–{_px(prof['vah'], unit)} "
            f"(POC {_px(prof['poc'], unit)})")


def table_row(inst: dict, cur_w: str, prior_w: str,
              unit: Optional[str] = None) -> list[str]:
    """Market | Value area (POC) | Prior | Migration | Close vs value."""
    vpw = inst.get("volume_profile") or {}
    cur, prior = vpw.get(cur_w) or {}, vpw.get(prior_w) or {}
    mig = migration(cur, prior) if "poc" in cur and "poc" in prior else None
    cvv = close_vs_value((inst.get("frame") or {}).get("last"), cur) \
        if "poc" in cur else None
    return [inst.get("label") or inst.get("id"), area_text(cur, unit),
            area_text(prior, unit), mig or "—", cvv or "—"]


def table(insts: list[dict], cur_w: str, prior_w: str,
          units: Optional[dict] = None) -> dict:
    """The table every cadence prints: one row per configured instrument, the
    current window against the prior one. Absences go to not_tracked."""
    units = units or {}
    rows, gaps, data = [], [], []
    for i in insts:
        vpw = i.get("volume_profile")
        if not vpw:
            continue
        rows.append(table_row(i, cur_w, prior_w, units.get(i.get("id"))))
        for w in (cur_w, prior_w):
            why = (vpw.get(w) or {}).get("absent")
            if why:
                gaps.append(f"{i.get('label') or i.get('id')} "
                            f"{WINDOW_NAMES[w]}: {why}")
        data.append({"market": i.get("label"), "symbol": i.get("symbol"),
                     "window": cur_w, "prior_window": prior_w,
                     **{f"{w}_{f}": (vpw.get(w) or {}).get(f)
                        for w in (cur_w, prior_w) for f, _ in FIELDS},
                     "migration": rows[-1][3], "close_vs_value": rows[-1][4]})
    cols = list(TABLE_COLUMNS)
    cols[2] = WINDOW_NAMES[prior_w].capitalize()
    return {"columns": cols, "rows": rows, "not_tracked": gaps, "data": data}


# ---------------------------------------------------------------------------
# The stored series: calc.vp_<id>_session_* and calc.vp_<id>_20s_*
# ---------------------------------------------------------------------------
def series_key(instrument: str, span: str, field: str) -> str:
    return f"calc.vp_{instrument}_{span}_{field}"


SERIES_KEYS = tuple(series_key(i, s, f) for i in ("spy", "qqq", "iwm")
                    for s in ("session", "20s") for f, _ in FIELDS)


def calc_rows(store, days: list[str], instruments: Optional[list[str]] = None,
              cfg: Optional[dict] = None, as_of: Optional[str] = None) -> list[dict]:
    """For each instrument and session: the session's POC, VAH and VAL and the
    rolling composite's, each row's available_at the max of its input bars'.
    A window not computed writes nothing."""
    cfg = cfg or load_config()
    share = complete_share()
    n = int(cfg.get("composite_sessions", 20))
    rows: list[dict] = []
    for iid in instruments or instrument_ids(cfg):
        for day in days:
            for span, sess in (("session", [day]), ("20s", trailing_sessions(day, n))):
                bars, counts = session_bars(store, iid, sess, as_of)
                prof = from_bars(bars, counts, cfg, share)
                if prof.get("poc") is None:
                    continue
                for f, _ in FIELDS:
                    rows.append({"registry_key": series_key(iid, span, f),
                                 "instrument": None, "observed_at": day,
                                 "available_at": prof["available_at"],
                                 "value": prof[f], "source": "calc"})
    return rows


def _bar_days(store, instruments_: list[str]) -> list[str]:
    days: set[str] = set()
    for iid in instruments_:
        for r in store.read(iid, "5m"):
            days.add(session.session_date(r["observed_at"]))
    return sorted(days)


def compute(first: Optional[str] = None, store=None, dry_run: bool = False,
            cfg: Optional[dict] = None) -> dict:
    """Write the calc.vp_* rows for the sessions from `first` ("first": the
    earliest stored 5-minute bar) to the latest stored; with no `first`, the
    sessions of the last compute_lookback_days."""
    from . import observations                                  # noqa: PLC0415
    cfg = cfg or load_config()
    own = store is None
    st = store or bars_mod.BarStore()
    try:
        insts = instrument_ids(cfg)
        days = _bar_days(st, insts)
        if not days:
            return {"computed": 0, "written": 0, "sessions": 0, "dry_run": dry_run}
        if first == "first":
            first = days[0]
        elif first is None:
            first = (_d(days[-1]) - dt.timedelta(
                days=int(cfg.get("compute_lookback_days", 7)))).isoformat()
        days = [d for d in days if d >= first]
        rows = calc_rows(st, days, insts, cfg)
        written = 0
        if not dry_run and rows:
            with observations.ObservationStore(str(st.path)) as db:
                written = db.write_many(rows)
        by: dict[str, int] = {}
        for r in rows:
            by[r["registry_key"]] = by.get(r["registry_key"], 0) + 1
        return {"computed": len(rows), "written": written, "sessions": len(days),
                "first": days[0] if days else None, "by_key": by,
                "dry_run": dry_run}
    finally:
        if own:
            st.close()


# ---------------------------------------------------------------------------
# Two read-only measurements, for the operator to run on the box
# ---------------------------------------------------------------------------
def _spec(instrument: str) -> dict:
    return next(t for t in bars_mod.tape() if t["id"] == instrument)


def coverage(instrument: str, sessions: int, store=None, db=None) -> list[dict]:
    """The share of each session's daily volume (the yfinance _volume companion)
    that its 5-minute bars carry. Reads only."""
    from . import observations                                  # noqa: PLC0415
    own_s, own_d = store is None, db is None
    st = store or bars_mod.BarStore()
    ob = db or observations.ObservationStore(str(st.path))
    try:
        key = _spec(instrument)["daily"] + "_volume"
        daily = {str(r["observed_at"])[:10]: r["value_num"] for r in ob.as_of(key)
                 if r.get("value_num") is not None}
        days = _bar_days(st, [instrument])[-sessions:]
        out = []
        for d in days:
            bars, counts = session_bars(st, instrument, [d])
            v5 = sum(float(b.get("volume") or 0) for b in bars)
            dv = daily.get(d)
            out.append({"session": d, "bars": counts[d][0], "expected": counts[d][1],
                        "volume_5m": v5, "volume_daily": dv,
                        "share": (v5 / dv) if dv else None})
        return out
    finally:
        if own_d:
            ob.close()
        if own_s:
            st.close()


def compare(instrument: str, sessions: int, store=None, db=None,
            cfg: Optional[dict] = None) -> list[dict]:
    """The 5-minute profile against the daily-bar approximation of the same
    window -- the composite_sessions window ending at each of the last
    `sessions` sessions: the POC distance in daily bins, and the value areas'
    overlap (intersection over union). Reads only."""
    from . import observations                                  # noqa: PLC0415
    cfg = cfg or load_config()
    own_s, own_d = store is None, db is None
    st = store or bars_mod.BarStore()
    ob = db or observations.ObservationStore(str(st.path))
    try:
        n = int(cfg.get("composite_sessions", 20))
        key = _spec(instrument)["daily"]
        out = []
        for d in _bar_days(st, [instrument])[-sessions:]:
            sess = trailing_sessions(d, n)
            bars, counts = session_bars(st, instrument, sess)
            p5 = from_bars(bars, counts, cfg)
            pd_ = daily_profile(daily_rows(ob, key, sess[0], sess[-1]), cfg)
            row: dict[str, Any] = {"session": d, "window": f"{sess[0]} to {sess[-1]}"}
            if p5.get("poc") is None or pd_.get("poc") is None:
                row["absent"] = p5.get("absent") or pd_.get("absent")
            else:
                inter = max(0.0, min(p5["vah"], pd_["vah"]) - max(p5["val"], pd_["val"]))
                union = max(p5["vah"], pd_["vah"]) - min(p5["val"], pd_["val"])
                row.update(poc_5m=p5["poc"], poc_daily=pd_["poc"],
                           daily_bin=pd_["bin_width"],
                           poc_distance_bins=round(abs(p5["poc"] - pd_["poc"])
                                                   / pd_["bin_width"], 2),
                           va_overlap=round(inter / union, 3) if union else None)
            out.append(row)
        return out
    finally:
        if own_d:
            ob.close()
        if own_s:
            st.close()


def _main(argv: list[str]) -> int:
    import argparse
    import statistics
    p = argparse.ArgumentParser(description="The volume profile (VP-1).")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute", help="write calc.vp_* for the stored sessions")
    c.add_argument("--from", dest="first", default=None,
                   help="a date, or 'first' for the earliest stored 5-minute bar")
    c.add_argument("--dry-run", action="store_true")
    for name in ("coverage", "compare"):
        s = sub.add_parser(name, help="read-only; writes nothing")
        s.add_argument("--instrument", default="spy")
        s.add_argument("--sessions", type=int, default=40)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "compute":
        r = compute(a.first, dry_run=a.dry_run)
        print(f"{r['computed']} rows over {r['sessions']} session(s) from "
              f"{r.get('first')}, {r['written']} written"
              + ("  (dry run)" if r["dry_run"] else ""))
        for k in sorted(r.get("by_key") or {}):
            print(f"  {k:32} {r['by_key'][k]:>6}")
        return 0
    if a.cmd == "coverage":
        rows = coverage(a.instrument, a.sessions)
        for r in rows:
            sh = "—" if r["share"] is None else f"{100 * r['share']:.1f}%"
            print(f"{r['session']}  bars {r['bars']:>3}/{r['expected']:<3}  "
                  f"5m {r['volume_5m']:>16,.0f}  daily "
                  f"{(r['volume_daily'] or 0):>16,.0f}  share {sh}")
        shares = [r["share"] for r in rows if r["share"] is not None]
        if shares:
            print(f"median share {100 * statistics.median(shares):.1f}% over "
                  f"{len(shares)} session(s); min {100 * min(shares):.1f}%")
        return 0
    rows = compare(a.instrument, a.sessions)
    for r in rows:
        if "absent" in r:
            print(f"{r['session']}  {r['window']}  absent: {r['absent']}")
        else:
            print(f"{r['session']}  {r['window']}  POC 5m {r['poc_5m']:,.2f} daily "
                  f"{r['poc_daily']:,.2f} ({r['poc_distance_bins']} daily bins of "
                  f"{r['daily_bin']:g})  VA overlap {r['va_overlap']}")
    ok = [r for r in rows if "absent" not in r]
    if ok:
        print(f"median POC distance {statistics.median(r['poc_distance_bins'] for r in ok)}"
              f" daily bins; median VA overlap "
              f"{statistics.median(r['va_overlap'] for r in ok if r['va_overlap'] is not None)}"
              f" over {len(ok)} window(s)")
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))

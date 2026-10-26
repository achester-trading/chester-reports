"""
Trend-signal breadth (signal-triage Batch 16 item 89(b); written as the triage
chat's 82(b) in docs/change-order-signal-triage-round-7-2026-10-26.md; ruled
26 Oct 2026; B76).

From our own store, how many of the markets we hold are trending and how many
are reversing -- in place of a sell-side trend monitor read through an
aggregator. Report rights only; the stored keys are barred from the market-state
object (metrics_registry.yaml `market_state_barred`).

THE SIGNAL, DECLARED (config/trend_breadth.yaml; nothing fitted):
    sign(L, t)  +1 when the close on t is above the mean of the market's last L
                closes (t included), -1 below, 0 equal; L in 20, 60, 120, 250
    state(t)    "trending"  all four signs agree and none is 0
                "reversing" the 20-session sign is against the 250-session one,
                            and it changed on one of the last five sessions
                "mixed"     otherwise
                "insufficient history" while a lookback lacks L closes

The stored series (source `calc`, rows point-in-time: a sign is available when
the latest close in its window is):
    trend.<market>.<lookback>   the sign, per the market's own sessions
    trend.flips_week            sign changes across markets and lookbacks in the
                                seven calendar days to the day
    trend.reversing_share       the share of markets carrying a state that read
                                "reversing", percent

    python -m altdata.trend_breadth backfill --dry-run    the whole history, counted
    python -m altdata.trend_breadth backfill              ... and written
    python -m altdata.trend_breadth compute [--from D]    recent days (the features pass)
    python -m altdata.trend_breadth show                  the table as the Weekly prints it
    python -m altdata.trend_breadth ledger --db PATH      the calibration ledger's edition

The features pass (altdata/market_features.compute) runs `compute` after ST-5's
features, never fatally. The read and the ledger open the store read-only.
"""

from __future__ import annotations

import datetime as dt
import functools
import logging
import math
import statistics
from collections import deque
from pathlib import Path
from typing import Optional

from altdata import observations, session

log = logging.getLogger("altdata.trend_breadth")

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "trend_breadth.yaml"
SOURCE = "calc"
FLIPS_KEY = "trend.flips_week"
SHARE_KEY = "trend.reversing_share"
NOT_STORED = "not stored"
PREREG_BEGIN = "<!-- prereg:begin -->"
PREREG_END = "<!-- prereg:end -->"


@functools.lru_cache(maxsize=1)
def config() -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def lookbacks(cfg: Optional[dict] = None) -> list[int]:
    return [int(x) for x in (cfg or config())["lookbacks"]]


def sign_key(market: str, lookback: int) -> str:
    return f"trend.{market}.{lookback}"


def _sign_keys() -> list[str]:
    cfg = config()
    return [sign_key(m["id"], lb) for m in cfg["markets"] for lb in lookbacks(cfg)]


# The registry's bulk block reads this list (members_from), so the keys this
# module writes and the keys the registry knows are one list.
SIGN_KEYS = _sign_keys()


# ---------------------------------------------------------------------------
# The signal
# ---------------------------------------------------------------------------
def _sign(close: float, mean: float) -> int:
    return 1 if close > mean else (-1 if close < mean else 0)


def signs(closes: list[tuple], lbs: list[int]) -> list[dict]:
    """[(day, value, available_at, kind)] in day order -> one row per day:
    {day, s: {L: sign or None}, avail: {L: the window's latest available_at},
    kind}. A running sum per lookback and a monotone queue for the availability,
    so the backfill is linear in the history."""
    out = []
    sums = {lb: 0.0 for lb in lbs}
    queues = {lb: deque() for lb in lbs}       # (index, available_at), max first
    for i, (day, v, avail, kind) in enumerate(closes):
        row = {"day": day, "s": {}, "avail": {}, "kind": kind}
        for lb in lbs:
            sums[lb] += v
            if i >= lb:
                sums[lb] -= closes[i - lb][1]
            q = queues[lb]
            while q and q[-1][1] <= avail:
                q.pop()
            q.append((i, avail))
            while q[0][0] <= i - lb:
                q.popleft()
            if i + 1 >= lb:
                row["s"][lb] = _sign(v, sums[lb] / lb)
                row["avail"][lb] = q[0][1]
            else:
                row["s"][lb] = None
        out.append(row)
    return out


def state_at(rows: list[dict], t: int, cfg: Optional[dict] = None) -> str:
    """The market's state on rows[t] (rows as signs() returns them, or stored)."""
    cfg = cfg or config()
    lbs = lookbacks(cfg)
    s = rows[t]["s"]
    if any(s.get(lb) is None for lb in lbs):
        return "insufficient history"
    short, long_ = s[lbs[0]], s[lbs[-1]]
    if len({s[lb] for lb in lbs}) == 1 and short != 0:
        return "trending"
    if short != 0 and short == -long_:
        n = int(cfg.get("reversal_sessions") or 5)
        for j in range(max(1, t - n + 1), t + 1):
            a, b = rows[j - 1]["s"].get(lbs[0]), rows[j]["s"].get(lbs[0])
            if a is not None and b is not None and a != b:
                return "reversing"
    return "mixed"


def flips(rows: list[dict], lbs: list[int]) -> list[tuple[str, int, str]]:
    """(day, lookback, available_at) for every sign change in the rows."""
    out = []
    for j in range(1, len(rows)):
        for lb in lbs:
            a, b = rows[j - 1]["s"].get(lb), rows[j]["s"].get(lb)
            if a is not None and b is not None and a != b:
                out.append((rows[j]["day"], lb, rows[j]["avail"][lb]))
    return out


# ---------------------------------------------------------------------------
# Reading the closes
# ---------------------------------------------------------------------------
def closes(st, market: dict, as_of: Optional[str] = None
           ) -> tuple[Optional[str], list[tuple]]:
    """The market's series: the first declared key holding rows as of the cutoff,
    and its closes [(day, value, available_at, kind)] in day order. (None, [])
    when no declared key is stored: the market is "not stored"."""
    for k in market["keys"]:
        rows = st.as_of(k["key"], as_of=as_of, instrument=k.get("instrument"))
        pts = {}
        for r in rows:
            v = r.get("value_num")
            if v is None or not math.isfinite(float(v)):
                continue
            pts[str(r["observed_at"])[:10]] = (
                float(v), str(r["available_at"]), r.get("availability_kind"))
        if pts:
            return k["key"], [(d, *pts[d]) for d in sorted(pts)]
    return None, []


def _held(rows: list[dict], day: str, within: int) -> Optional[int]:
    """The index of the market's latest row on or before `day`, if fresh."""
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid]["day"] <= day:
            lo = mid + 1
        else:
            hi = mid
    i = lo - 1
    if i < 0:
        return None
    age = (dt.date.fromisoformat(day) - dt.date.fromisoformat(rows[i]["day"])).days
    return i if age <= within else None


def breadth_on(series: dict[str, list[dict]], day: str, cfg: Optional[dict] = None
               ) -> Optional[dict]:
    """{share, reversing, n, flips, avail} on `day` across the markets' sign rows,
    or None when no market carries a state."""
    cfg = cfg or config()
    lbs = lookbacks(cfg)
    within = int(cfg.get("held_within_days") or 7)
    window = int(cfg.get("flip_window_days") or 7)
    start = (dt.date.fromisoformat(day) - dt.timedelta(days=window)).isoformat()
    n = rev = nflip = 0
    avails = []
    for rows in series.values():
        i = _held(rows, day, within)
        if i is None:
            continue
        stt = state_at(rows, i, cfg)
        if stt == "insufficient history":
            continue
        n += 1
        rev += stt == "reversing"
        avails.append(max(rows[i]["avail"].values()))
        for j in range(max(1, i - 10), i + 1):
            if not start < rows[j]["day"] <= day:
                continue
            for lb in lbs:
                a, b = rows[j - 1]["s"].get(lb), rows[j]["s"].get(lb)
                if a is not None and b is not None and a != b:
                    nflip += 1
    if not n:
        return None
    return {"share": 100.0 * rev / n, "reversing": rev, "n": n, "flips": nflip,
            "avail": max(avails)}


def all_series(st, as_of: Optional[str] = None, cfg: Optional[dict] = None
               ) -> tuple[dict[str, list[dict]], dict[str, Optional[str]]]:
    cfg = cfg or config()
    lbs = lookbacks(cfg)
    series, used = {}, {}
    for m in cfg["markets"]:
        key, pts = closes(st, m, as_of)
        used[m["id"]] = key
        if pts:
            series[m["id"]] = signs(pts, lbs)
    return series, used


# ---------------------------------------------------------------------------
# The stored rows
# ---------------------------------------------------------------------------
def compute_rows(st, as_of: Optional[str] = None,
                 first_day: Optional[str] = None) -> list[dict]:
    cfg = config()
    lbs = lookbacks(cfg)
    series, _ = all_series(st, as_of, cfg)
    rows: list[dict] = []
    days = set()
    for mid, srows in series.items():
        for r in srows:
            days.add(r["day"])
            if first_day and r["day"] < first_day:
                continue
            for lb in lbs:
                if r["s"][lb] is None:
                    continue
                rows.append({"registry_key": sign_key(mid, lb), "instrument": None,
                             "observed_at": r["day"], "available_at": r["avail"][lb],
                             "value": float(r["s"][lb]), "source": SOURCE,
                             "availability_kind": r["kind"]})
    for day in sorted(days):
        if first_day and day < first_day:
            continue
        if dt.date.fromisoformat(day).weekday() >= 5:
            continue
        b = breadth_on(series, day, cfg)
        if b is None:
            continue
        for key, v in ((SHARE_KEY, round(b["share"], 4)), (FLIPS_KEY, float(b["flips"]))):
            rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                         "available_at": b["avail"], "value": v, "source": SOURCE,
                         "availability_kind": None})
    return rows


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False) -> dict:
    own = store is None
    db = store or observations.open_writer(__name__)
    try:
        rows = compute_rows(db, as_of, first_day)
        written = 0 if dry_run else db.write_many(observations.drop_unchanged(db, rows))
        by_key: dict[str, int] = {}
        for r in rows:
            by_key[r["registry_key"]] = by_key.get(r["registry_key"], 0) + 1
        return {"computed": len(rows), "written": written, "by_key": by_key,
                "dry_run": dry_run, "first_day": first_day}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# The read: what the Weekly and the Monthly print, from the stored rows
# ---------------------------------------------------------------------------
def read(st, now: str) -> dict:
    """Each market's four stored signs and its state, the week's flips and the
    reversing share, as of `now`. A market with no stored source key is "not
    stored" and leaves n; one held but not yet computed is "not computed"."""
    cfg = config()
    lbs = lookbacks(cfg)
    within = int(cfg.get("held_within_days") or 7)
    since = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=40)).isoformat()
    out = []
    for m in cfg["markets"]:
        key = next((k["key"] for k in m["keys"]
                    if st.latest_as_of(k["key"], now, k.get("instrument"))), None)
        if key is None:
            out.append({"id": m["id"], "label": m["label"], "state": NOT_STORED,
                        "signs": {}, "key": None, "day": None})
            continue
        byday: dict[str, dict] = {}
        for lb in lbs:
            for r in st.as_of(sign_key(m["id"], lb), as_of=now, observed_from=since):
                if r.get("value_num") is not None:
                    byday.setdefault(str(r["observed_at"])[:10], {})[lb] = int(r["value_num"])
        rows = [{"day": d, "s": {lb: byday[d].get(lb) for lb in lbs}}
                for d in sorted(byday)]
        if not rows or _held(rows, now[:10], within) is None:
            out.append({"id": m["id"], "label": m["label"], "state": "not computed",
                        "signs": {}, "key": key, "day": rows[-1]["day"] if rows else None})
            continue
        t = len(rows) - 1
        out.append({"id": m["id"], "label": m["label"], "state": state_at(rows, t, cfg),
                    "signs": rows[t]["s"], "key": key, "day": rows[t]["day"]})
    share = st.latest_as_of(SHARE_KEY, now)
    flp = st.latest_as_of(FLIPS_KEY, now)
    first = st.conn.execute("SELECT MIN(observed_at) FROM observations WHERE "
                            "registry_key = ?", (SHARE_KEY,)).fetchone()
    held = [x for x in out if x["state"] != NOT_STORED]
    states = [x for x in held if x["state"] not in ("not computed",
                                                     "insufficient history")]
    return {"markets": out, "lookbacks": lbs,
            "held": len(held), "named": len(out), "with_state": len(states),
            "reversing": sum(1 for x in states if x["state"] == "reversing"),
            "trending": sum(1 for x in states if x["state"] == "trending"),
            "share": None if not share else float(share["value_num"]),
            "share_day": None if not share else str(share["observed_at"])[:10],
            "flips": None if not flp else int(flp["value_num"]),
            "history_from": str(first[0])[:10] if first and first[0] else None}


def _sign_text(v: Optional[int]) -> str:
    return "—" if v is None else {1: "+", -1: "−", 0: "0"}[v]


def table(r: dict) -> dict:
    cols = ["Market", *[f"{lb}-session" for lb in r["lookbacks"]], "State", "As of"]
    rows = []
    for x in r["markets"]:
        rows.append([x["label"], *[_sign_text(x["signs"].get(lb)) for lb in r["lookbacks"]],
                     x["state"], x["day"] or "—"])
    return {"columns": cols, "rows": rows}


def lines(r: dict) -> list[str]:
    n, named = r["with_state"], r["named"]
    out = []
    if r["share"] is None:
        out.append(f"Reversing breadth: not computed yet, of {r['held']} held of "
                   f"{named} named (the backfill is the first box command).")
    else:
        out.append(f"Reversing breadth: {r['reversing']} of {n} held with a state "
                   f"reversing ({r['share']:.0f}% stored on {r['share_day']}); "
                   f"{r['trending']} trending. Signal flips in the week: {r['flips']} "
                   f"across markets and four lookbacks.")
    gaps = [x["label"] for x in r["markets"] if x["state"] == NOT_STORED]
    if gaps:
        out.append(f"Not stored: {', '.join(gaps)}; the count is of {r['held']} held, "
                   f"not {named}.")
    out.append(f"Window: the sign of each close against its 20-, 60-, 120- and "
               f"250-session mean; reversing is the 20-session sign flipped against "
               f"the 250-session inside five sessions. History from "
               f"{r['history_from'] or 'none stored'}; n = {n}.")
    return out


NOTE = ("Our own trend signal, from the store's closes (item 89(b)): + above the "
        "lookback mean, − below. Trending is all four signs agreeing; reversing is "
        "the 20-session sign turned against the 250-session within five sessions. "
        "Report only: no flag, and nothing enters the market-state object. The "
        "calibration ledger is pre-registered; it grants nothing until it is read.")


# ---------------------------------------------------------------------------
# The calibration ledger (docs/ledgers/trend-breadth-2026-10-26.md)
# ---------------------------------------------------------------------------
def prereg_bytes(text: str) -> bytes:
    """The pre-registration block, markers included, as LF bytes."""
    text = text.replace("\r\n", "\n")
    a, b = text.index(PREREG_BEGIN), text.index(PREREG_END) + len(PREREG_END)
    return text[a:b].encode("utf-8")


def prereg_sha(text: str) -> str:
    import hashlib                                              # noqa: PLC0415
    return hashlib.sha256(prereg_bytes(text)).hexdigest()


def welch_t(a: list[float], b: list[float]) -> Optional[float]:
    if len(a) < 2 or len(b) < 2:
        return None
    va, vb = statistics.variance(a), statistics.variance(b)
    se = math.sqrt(va / len(a) + vb / len(b))
    return None if se == 0 else (statistics.fmean(a) - statistics.fmean(b)) / se


def ledger_sample(st, as_of: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """The weekly sample: each ISO week's last S&P 500 session D with at least
    `min_markets` markets carrying a state; the reversing share on D and each
    outcome's percent change from D to the h-th of its sessions after D."""
    cfg = cfg or config()
    led = cfg["ledger"]
    series, used = all_series(st, as_of, cfg)
    outs = {}
    for o in led["outcomes"]:
        pts = closes(st, {"keys": [{"key": o["key"]}]}, as_of)[1]
        outs[o["id"]] = [(d, v) for d, v, _, _ in pts]
    spx = outs[led["outcomes"][0]["id"]]
    weeks: dict[tuple, str] = {}
    for d, _ in spx:
        weeks[dt.date.fromisoformat(d).isocalendar()[:2]] = d
    sample = []
    minm = int(led.get("min_markets") or 5)
    idx = {oid: {day: i for i, (day, _) in enumerate(pts)} for oid, pts in outs.items()}
    for d in sorted(weeks.values()):
        b = breadth_on(series, d, cfg)
        if b is None or b["n"] < minm:
            continue
        row = {"day": d, "share": b["share"], "n_markets": b["n"]}
        complete = True
        for oid, pts in outs.items():
            i = idx[oid].get(d)
            for h in led["horizons"]:
                if i is None or i + h >= len(pts):
                    row[f"{oid}_{h}"] = None
                    complete = False
                else:
                    row[f"{oid}_{h}"] = 100.0 * (pts[i + h][1] / pts[i][1] - 1.0)
        row["complete"] = complete
        sample.append(row)
    return {"sample": sample, "used": used,
            "held": sum(1 for k in used.values() if k), "named": len(used)}


def ledger_stats(sample: list[dict], cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    led = cfg["ledger"]
    hi_cut = float(led["high_share"])
    minw, tpass = int(led["min_weeks"]), float(led["t_pass"])
    res = {}
    for o in led["outcomes"]:
        for h in led["horizons"]:
            col = f"{o['id']}_{h}"
            rows = [r for r in sample if r.get(col) is not None]
            hi = [r[col] for r in rows if r["share"] >= hi_cut]
            lo = [r[col] for r in rows if r["share"] < hi_cut]
            mid = len(rows) // 2 + len(rows) % 2
            halves = []
            for part in (rows[:mid], rows[mid:]):
                a = [r[col] for r in part if r["share"] >= hi_cut]
                b = [r[col] for r in part if r["share"] < hi_cut]
                halves.append(None if not a or not b
                              else statistics.fmean(a) - statistics.fmean(b))
            t = welch_t(hi, lo)
            diff = None if not hi or not lo else statistics.fmean(hi) - statistics.fmean(lo)
            if len(hi) < minw or len(lo) < minw:
                verdict = "INSUFFICIENT"
            elif (t is not None and abs(t) >= tpass and diff
                  and all(x is not None and math.copysign(1, x) == math.copysign(1, diff)
                          for x in halves)):
                verdict = "PASS"
            else:
                verdict = "FAIL"
            res[col] = {"n_high": len(hi), "n_rest": len(lo),
                        "mean_high": statistics.fmean(hi) if hi else None,
                        "mean_rest": statistics.fmean(lo) if lo else None,
                        "diff": diff, "t": t, "halves": halves, "verdict": verdict}
    primary = f"{led['outcomes'][0]['id']}_{max(led['horizons'])}"
    return {"by": res, "primary": primary, "verdict": res[primary]["verdict"]}


def _f(x: Optional[float], fmt: str = "+.2f") -> str:
    return "—" if x is None else format(x, fmt)


def ledger_edition(st, as_of: Optional[str] = None, label: str = "") -> str:
    cfg = config()
    led = cfg["ledger"]
    s = ledger_sample(st, as_of, cfg)
    stats = ledger_stats(s["sample"], cfg)
    smp = s["sample"]
    win = f"{smp[0]['day']} to {smp[-1]['day']}" if smp else "no week qualifies"
    day = dt.date.fromisoformat((as_of or session.utc_iso())[:10])
    out = [f"## Edition: {label or day.isoformat()}", "",
           f"- **As of:** {day.day} {day.strftime('%b %Y')}" + (f" ({label})" if label else ""),
           f"- **Window:** {win}",
           f"- **n:** {len(smp)} weeks; markets held {s['held']} of {s['named']} named "
           f"(not stored: {', '.join(m for m, k in s['used'].items() if not k) or 'none'})",
           "", "| Field | Value |", "|---|---|",
           f"| Verdict | {stats['verdict']} (the S&P 500 at +20, the rule's cell) |",
           f"| n | {len(smp)} weeks |",
           "", "| Outcome | Horizon | n high | n rest | Mean high | Mean rest | "
           "Difference | Welch t | Halves | Verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
    for o in led["outcomes"]:
        for h in led["horizons"]:
            x = stats["by"][f"{o['id']}_{h}"]
            hv = " / ".join(_f(v) for v in x["halves"])
            primary = " (the rule)" if f"{o['id']}_{h}" == stats["primary"] else ""
            out.append(f"| {o['label']} | +{h} | {x['n_high']} | {x['n_rest']} | "
                       f"{_f(x['mean_high'])} | {_f(x['mean_rest'])} | {_f(x['diff'])} | "
                       f"{_f(x['t'])} | {hv} | {x['verdict']}{primary} |")
    out += ["", f"**Verdict (the pre-registered rule):** {stats['verdict']}.",
            "", "**Rights:** none."]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
def open_ro(path: Optional[str] = None):
    """The store opened read-only (mode=ro, query_only), as altdata/sm_draft.py
    does: `show` and `ledger` never write, nor migrate, the store they read."""
    import sqlite3                                              # noqa: PLC0415
    p = Path(path or observations.DEFAULT_DB)
    if not p.is_file():
        raise FileNotFoundError(f"no observation store at {p}")
    st = observations.ObservationStore.__new__(observations.ObservationStore)
    st.path = p
    st.conn = sqlite3.connect(f"file:{p.resolve().as_posix()}?mode=ro", uri=True)
    st.conn.row_factory = sqlite3.Row
    st.conn.execute("PRAGMA query_only = ON")
    return st


def default_first_day(db, as_of: Optional[str] = None) -> str:
    """30 days before the newest stored share, or before the cutoff when none is
    stored: the features pass never runs the history by itself, so the backfill
    stays the operator's command, dry run first."""
    last = db.last_observed(keys=[SHARE_KEY])
    base = last or (as_of or session.utc_iso())[:10]
    return (dt.date.fromisoformat(base) - dt.timedelta(days=30)).isoformat()


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.trend_breadth")
    ap.add_argument("cmd", choices=["compute", "backfill", "show", "ledger"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--from", dest="first", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if a.cmd in ("compute", "backfill"):
        with observations.ObservationStore(a.db) as st:
            first = None if a.cmd == "backfill" else (a.first or default_first_day(st, a.as_of))
            r = compute(a.as_of, first, st, a.dry_run)
        print(f"{r['computed']} rows computed, {r['written']} written"
              + ("  (dry run)" if r["dry_run"] else "")
              + (f", from {first}" if first else ", the whole history"))
        for k in sorted(r["by_key"]):
            print(f"  {k:32} {r['by_key'][k]:>7}")
        return 0
    st = open_ro(a.db)
    try:
        if a.cmd == "show":
            now = a.as_of or session.utc_iso(timespec="microseconds")
            r = read(st, now)
            t = table(r)
            print(" | ".join(t["columns"]))
            for row in t["rows"]:
                print(" | ".join(str(c) for c in row))
            for ln in lines(r):
                print(ln)
        else:
            print(ledger_edition(st, a.as_of, a.label))
    finally:
        st.conn.close()
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))

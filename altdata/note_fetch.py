"""
The secondary notes' fetch steps (docs/change-order-secondary-notes-2026-10-19.md,
ruled 19 Oct 2026). They WRITE THE STORE ONLY, in the overnight fetch's pattern:
the fetch writes, the payload reads the store, a report never fetches (30.4).

    python -m altdata.note_fetch open    [--date D] [--dry-run]   # after 09:45
    python -m altdata.note_fetch evening [--date D] [--dry-run]   # 21:30, Sun-Thu

THE OPEN FETCH (after the 09:45 capture):
  bars       today's 5-minute bars from 08:00 ET for SPY, ES=F, ZN=F, ZT=F (where
             Yahoo serves it), ^TNX, DX-Y.NYB and ^VIX
  fred       a targeted pull of ONLY the series behind today's 08:30 tier-1 and
             tier-2 releases, through the existing FRED writer (vintage-keyed,
             append-only); FRED's full daily pull stays at 16:10
  news       events_ingest pull --only news (the agencies' press feeds)
  voices     one voices-scan pass inside the scan's existing daily cap, with a
             short time budget so the note lands by 09:55

THE EVENING FETCH (21:30, the evening before a session):
  bars       5-minute bars since 16:00 ET (on Sunday, since Friday 16:00) for
             ES=F, NQ=F, RTY=F, ZN=F, JPY=X, CNH=X, ^N225, ^HSI, 000001.SS, ^KS11,
             BTC-USD and ETH-USD
  fix        the PBoC fix through the existing CFETS writer
  news       events_ingest pull --only news,earnings
  after      yfinance's pre- and post-market bars for each captured name whose
             stored release_at today is after 16:00: calc.after_hours_move, the
             regular close against the last after-hours trade by 21:30
  voices     one voices-scan pass inside its cap

EACH STEP IS NON-FATAL and names its absence; the summary is printed and the exit
code is 0 when any step wrote, 1 when none did. Only the existing writers write
the store's other keys; this module writes the bars table and the notes' own two
readings, calc.release_first_hour and calc.after_hours_move (source
secondary_notes), which the two pre-registered ledgers score.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from typing import Callable, Optional

log = logging.getLogger("altdata.note_fetch")

OPEN_IDS = ("spy", "es", "zn", "zt", "y10", "dxy", "vix")
EVENING_IDS = ("es", "nq", "rty", "zn", "usdjpy", "cnh", "btc", "eth")
# Asia's indices are read from four days back: their prior close is the last bar
# before tonight's open, which closed in the early ET morning (or on Friday).
ASIA_IDS = ("n225", "hsi", "sse", "kospi")
INDEX_FUNDS = {"SPY", "QQQ", "IWM"}
RFH_KEY = "calc.release_first_hour"
AH_KEY = "calc.after_hours_move"
SOURCE = "secondary_notes"
# THE FIRST-HOUR INSTRUMENTS (the release-first-hour pre-registration): ES in
# percent, the 10-year yield index in basis points (^TNX quotes the yield in %).
RFH_INSTRUMENTS = (("es", "ES=F", "percent_return"), ("y10", "^TNX", "bp"))


def symbols() -> dict[str, str]:
    """{bar id: Yahoo symbol} over the tape, intraday_extra and note_bars."""
    from . import bars as bars_mod                               # noqa: PLC0415
    out = {t["id"]: str(t.get("bars") or t.get("symbol"))
           for t in bars_mod.intraday_instruments()}
    out.update({t["id"]: str(t["bars"]) for t in bars_mod.note_instruments()})
    return out


def _et(day: str, hm: str) -> dt.datetime:
    from . import session                                       # noqa: PLC0415
    h, m = (int(x) for x in hm.split(":"))
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                               tzinfo=session._eastern_tz())     # noqa: SLF001


def yf_fetcher(sym: str, start: dt.datetime, end: dt.datetime,
               prepost: bool = False) -> list[dict]:
    """5-minute bars from Yahoo, [{observed_at, open, high, low, close}] (UTC)."""
    from . import import_yfinance                                # noqa: PLC0415
    yf = import_yfinance()
    h = yf.Ticker(sym).history(start=start, end=end, interval="5m", prepost=prepost,
                               auto_adjust=False)
    out = []
    for idx, r in h.iterrows():
        try:
            o, hi, lo, c = (float(r["Open"]), float(r["High"]), float(r["Low"]),
                            float(r["Close"]))
        except (TypeError, ValueError, KeyError):
            continue
        if any(x != x for x in (o, hi, lo, c)):
            continue
        t = idx.to_pydatetime().astimezone(dt.timezone.utc)
        out.append({"observed_at": t.isoformat(), "open": o, "high": hi, "low": lo,
                    "close": c})
    return out


def bar_rows(inst: str, sym: str, raw: list[dict], now: dt.datetime) -> list[dict]:
    """The bars table's rows: only completed bars (a bar in progress is dropped),
    no volume, available at the fetch instant."""
    out = []
    for b in raw:
        t = dt.datetime.fromisoformat(b["observed_at"])
        if t + dt.timedelta(minutes=5) > now:
            continue
        out.append({"instrument": inst, "symbol": sym, "interval": "5m",
                    "observed_at": b["observed_at"], "open": b["open"], "high": b["high"],
                    "low": b["low"], "close": b["close"], "volume": None,
                    "available_at": now.isoformat(), "source": "yfinance"})
    return out


def fetch_bars(ids, start: dt.datetime, now: dt.datetime, db_path=None, dry_run=False,
               fetcher: Optional[Callable] = None) -> dict:
    """{id: rows written | "error ..." | "none served"}."""
    from . import bars as bars_mod                               # noqa: PLC0415
    f = fetcher or yf_fetcher
    syms = symbols()
    out, rows = {}, []
    for i in ids:
        sym = syms.get(i)
        if not sym:
            out[i] = "not configured"
            continue
        try:
            got = bar_rows(i, sym, f(sym, start, now), now)
        except Exception as exc:                                # noqa: BLE001
            out[i] = f"error {type(exc).__name__}: {exc}"[:160]
            continue
        out[i] = len(got) if got else "none served"
        rows += got
    if rows and not dry_run:
        st = bars_mod.BarStore(db_path, create=True)
        try:
            st.write_many(rows)
        finally:
            st.close()
    return out


def todays_0830(day: str, db_path=None, now: Optional[str] = None) -> list[dict]:
    """Today's tier-1 and tier-2 releases scheduled for 08:30 ET:
    [{title, label, tier}], from the events table and the release calendar."""
    from . import events as ev_mod                               # noqa: PLC0415
    from daily_cascade import weekly_sections as ws             # noqa: PLC0415
    cal = ws.load_calendar()
    out, seen = [], set()
    with ev_mod.EventStore(db_path) as ev:
        rows = ev.calendar(day, day, as_of=now)
    for r in rows:
        if r.get("type") not in ("release", "scheduled"):
            continue
        m = ws.match_release(str(r.get("title") or ""), cal)
        if not m or m.get("time") != "08:30" or int(m.get("tier") or 3) > 2:
            continue
        lab = m.get("label") or r.get("title")
        if lab in seen:
            continue
        seen.add(lab)
        out.append({"title": r.get("title"), "label": lab, "tier": int(m["tier"]),
                    "match": m.get("match")})
    return out


def release_series(rel: dict, cfg_notes: Optional[dict] = None) -> list[dict]:
    """[{key, form, label}] behind a release: the calendar's declared form
    (tier1_headlines), else the notes' own declared form; [] where none."""
    import yaml                                                  # noqa: PLC0415
    from pathlib import Path                                     # noqa: PLC0415
    repo = Path(__file__).resolve().parent.parent
    cal = yaml.safe_load((repo / "config" / "release_calendar.yaml").read_text(encoding="utf-8"))
    for name, rows in (cal.get("tier1_headlines") or {}).items():
        if str(rel.get("title") or "").startswith(name) or rel.get("match") == name:
            return list(rows)
    extra = ((cfg_notes or {}).get("open") or {}).get("release_forms") or {}
    for name, rows in extra.items():
        if name.lower() in str(rel.get("title") or "").lower():
            return list(rows)
    return []


def fred_targeted(keys: list[str], dry_run=False, pull: Optional[Callable] = None) -> dict:
    """The existing FRED writer, for these series only."""
    from . import config as acfg                                 # noqa: PLC0415
    specs = [s for s in acfg.FRED_PULL_SERIES if f"fred.{s.key}" in set(keys)]
    if not specs:
        return {"state": "no series registered"}
    if dry_run:
        return {"state": "dry run", "series": [s.key for s in specs]}
    if pull is None:
        from .sources import fred                                # noqa: PLC0415
        from .store import Store                                 # noqa: PLC0415
        res = fred.pull(Store(), series=specs)
    else:
        res = pull(specs)
    return {"state": "ok", "series": [s.key for s in specs], "result": str(res)[:200]}


def news_pull(only: list[str], dry_run=False) -> dict:
    from . import events_ingest                                  # noqa: PLC0415
    try:
        return {"state": "ok", "result": str(events_ingest.pull(only=only, dry_run=dry_run))[:300]}
    except Exception as exc:                                    # noqa: BLE001
        return {"state": f"error {type(exc).__name__}: {exc}"[:160]}


def voices_pass(db_path=None, budget_seconds: int = 120, dry_run=False) -> dict:
    """One voices-scan pass inside the scan's existing daily cap (counted per UTC
    day by the scan itself), with a short time budget."""
    if dry_run:
        return {"state": "dry run"}
    from .sources import voices_scan                             # noqa: PLC0415
    from . import voices as vmod                                 # noqa: PLC0415
    try:
        cfg = {**vmod.load_config(), "time_budget_seconds": budget_seconds}
        r = voices_scan.run(db_path, cfg=cfg)
        return {"state": "ok", "sources": len((r or {}).get("sources") or {})}
    except Exception as exc:                                    # noqa: BLE001
        return {"state": f"error {type(exc).__name__}: {exc}"[:160]}


def after_hours_names(day: str, db_path=None, now: Optional[str] = None,
                      universe: Optional[list[str]] = None) -> list[str]:
    """Captured names whose stored release_at today is after 16:00 ET."""
    from . import config as acfg, events as ev_mod, session    # noqa: PLC0415
    uni = set(universe or acfg.chain_universe()) - INDEX_FUNDS
    uni = {s for s in uni if not _restricted(s)}
    out = []
    with ev_mod.EventStore(db_path) as ev:
        rows = ev.calendar(day, day, as_of=now)
    for r in rows:
        pl = r.get("payload") or {}
        if isinstance(pl, str):
            try:
                pl = json.loads(pl or "{}")
            except ValueError:
                pl = {}
        sym = str(pl.get("symbol") or "").upper()
        ra = pl.get("release_at")
        if sym in uni and ra:
            t = session.to_eastern(dt.datetime.fromisoformat(str(ra).replace("Z", "+00:00")))
            if t.date().isoformat() == day and (t.hour, t.minute) >= (16, 0) and sym not in out:
                out.append(sym)
    return out


def last_before(bars: list[dict], t: dt.datetime) -> Optional[dict]:
    """The last 5-minute bar that ENDS at or before t."""
    got = [b for b in bars
           if dt.datetime.fromisoformat(str(b["observed_at"])) + dt.timedelta(minutes=5) <= t]
    return max(got, key=lambda b: str(b["observed_at"])) if got else None


def move(a: float, b: float, unit: str) -> float:
    return round((b - a) * 100.0, 2) if unit == "bp" else round(100.0 * (b / a - 1.0), 3)


def release_first_hour(day: str, releases: list[str], now: dt.datetime, db_path=None,
                       dry_run=False) -> dict:
    """calc.release_first_hour: the last bar before 08:30 to the last before 09:45,
    from the bars this pass wrote. {instrument: "ok" | reason}."""
    from . import bars as bars_mod, observations                # noqa: PLC0415
    out, rows = {}, []
    t0, t1 = _et(day, "08:30"), _et(day, "09:45")
    with bars_mod.BarStore(db_path) as bst:
        for inst, sym, unit in RFH_INSTRUMENTS:
            bars = bst.read(inst, "5m", _et(day, "07:00").astimezone(dt.timezone.utc).isoformat(),
                            t1.astimezone(dt.timezone.utc).isoformat())
            a, b = last_before(bars, t0), last_before(bars, t1)
            if not a or not b:
                out[sym] = "no bar before 08:30" if not a else "no bar before 09:45"
                continue
            rec = {"from_at": a["observed_at"], "from": a["close"], "to_at": b["observed_at"],
                   "to": b["close"], "move": move(a["close"], b["close"], unit),
                   "units": unit, "releases": releases}
            rows.append({"registry_key": RFH_KEY, "instrument": sym, "observed_at": day,
                         "available_at": now.isoformat(), "source": SOURCE,
                         "value": json.dumps(rec, sort_keys=True)})
            out[sym] = "ok"
    if rows and not dry_run:
        with observations.open_writer(__name__, db_path) as st:
            st.write_many(rows)
    return out


def _restricted(sym: str) -> bool:
    """The Brookfield blocklist (register/instruments.py): no restricted name is
    fetched, stored or printed."""
    try:
        from register import instruments                        # noqa: PLC0415
        return instruments.restrictions().is_restricted(sym)
    except Exception:                                           # noqa: BLE001
        return False


def after_hours(names: list[str], day: str, now: dt.datetime, db_path=None,
                dry_run=False, fetcher: Optional[Callable] = None) -> dict:
    """calc.after_hours_move per name: the regular close (the bar ending at
    16:00) against the last after-hours trade the pass sees."""
    from . import observations                                   # noqa: PLC0415
    f = fetcher or yf_fetcher
    out, rows = {}, []
    close_t = _et(day, "16:00")
    for sym in names:
        try:
            got = f(sym, _et(day, "15:30"), now, True)
        except Exception as exc:                                # noqa: BLE001
            out[sym] = f"error {type(exc).__name__}: {exc}"[:160]
            continue
        c = last_before(got, close_t)
        ah = [b for b in got if dt.datetime.fromisoformat(str(b["observed_at"])) >= close_t]
        if not c or not ah:
            out[sym] = "no regular close served" if not c else "no after-hours trade served"
            continue
        last = max(ah, key=lambda b: str(b["observed_at"]))
        rec = {"close": c["close"], "after_hours": last["close"], "at": last["observed_at"],
               "move_pct": move(c["close"], last["close"], "pct")}
        rows.append({"registry_key": AH_KEY, "instrument": sym, "observed_at": day,
                     "available_at": now.isoformat(), "source": SOURCE,
                     "value": json.dumps(rec, sort_keys=True)})
        out[sym] = "ok"
    if rows and not dry_run:
        with observations.open_writer(__name__, db_path) as st:
            st.write_many(rows)
    return out


def open_fetch(day: str, now: Optional[dt.datetime] = None, db_path=None, dry_run=False,
               fetcher=None, steps: Optional[dict] = None) -> dict:
    """The open note's fetch. `steps` replaces any step (the gate's fakes)."""
    from . import bars as bars_mod                               # noqa: PLC0415
    s = steps or {}
    now = now or dt.datetime.now(dt.timezone.utc)
    cfg = bars_mod.load_config().get("secondary_notes") or {}
    out = {"bars": fetch_bars(OPEN_IDS, _et(day, "08:00"), now, db_path, dry_run, fetcher)}
    rels = (s.get("releases") or todays_0830)(day, db_path)
    keys = sorted({x["key"] for r in rels for x in release_series(r, cfg)})
    out["releases"] = [r["label"] for r in rels]
    out["fred"] = (s.get("fred") or fred_targeted)(keys, dry_run) if keys else \
        {"state": "no 08:30 release" if not rels else "no series behind today's releases"}
    out["news"] = (s.get("news") or news_pull)(["news"], dry_run)
    out["voices"] = (s.get("voices") or voices_pass)(db_path, 120, dry_run)
    out["first_hour"] = release_first_hour(day, out["releases"], now, db_path, dry_run)         if rels else "no 08:30 release"
    return out


def evening_fetch(day: str, now: Optional[dt.datetime] = None, db_path=None,
                  dry_run=False, fetcher=None, steps: Optional[dict] = None) -> dict:
    """The evening note's fetch. `day` is the ET date of the evening; on a
    Sunday the bars start at Friday 16:00."""
    s = steps or {}
    now = now or dt.datetime.now(dt.timezone.utc)
    d = dt.date.fromisoformat(day)
    since = (d - dt.timedelta(days=2)).isoformat() if d.weekday() == 6 else day
    out = {"bars": fetch_bars(EVENING_IDS, _et(since, "15:30"), now, db_path, dry_run,
                              fetcher)}
    out["bars"].update(fetch_bars(ASIA_IDS, _et(day, "00:00") - dt.timedelta(days=4), now,
                                  db_path, dry_run, fetcher))
    out["fix"] = (s.get("fix") or _cfets)(dry_run)
    out["news"] = (s.get("news") or news_pull)(["news", "earnings"], dry_run)
    names = (s.get("ah_names") or after_hours_names)(day, db_path)
    out["after_hours"] = after_hours(names, day, now, db_path, dry_run, fetcher) \
        if names else "no captured name reports after the close today"
    out["voices"] = (s.get("voices") or voices_pass)(db_path, 120, dry_run)
    return out


def _cfets(dry_run=False) -> dict:
    if dry_run:
        return {"state": "dry run"}
    try:
        from .sources import cfets                               # noqa: PLC0415
        return {"state": "ok", "result": str(cfets.pull())[:200]}
    except Exception as exc:                                    # noqa: BLE001
        return {"state": f"error {type(exc).__name__}: {exc}"[:160]}


def wrote(summary: dict) -> bool:
    b = summary.get("bars") or {}
    return any(isinstance(v, int) and v > 0 for v in b.values())


def main(argv=None) -> int:
    from . import session                                       # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.note_fetch")
    ap.add_argument("which", choices=["open", "evening"])
    ap.add_argument("--date")
    ap.add_argument("--db")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    day = a.date or session.session_date()
    fn = open_fetch if a.which == "open" else evening_fetch
    res = fn(day, db_path=a.db, dry_run=a.dry_run)
    print(json.dumps(res, indent=1, default=str))
    return 0 if wrote(res) else 1


if __name__ == "__main__":
    sys.exit(main())

"""
OS-12, relative options volume (signal-triage Batch 13, item 61, ruled 20 Oct 2026,
D1-D5; session A's a54-relative-volume). It sits beside OS-10.

    from daily_cascade import relative_volume as rv
    rv.readings(st, day, cutoff)          # OS-12a: every name's ratio
    rv.flagged(st, day, cutoff)           # OS-12b: the names at or over 1.5x
    rv.close_table(st, day, cutoff)       # the 16:45 close's detail table
    rv.next_close_line(st, flag_day, ...) # the next close's one line (D4)
    rv.flagged_yesterday(st, flag_day)    # the 07:00 anchor's OS-9 tag (D4)

OS-12a, THE METRIC. Each name's session total options volume (chain.options_volume,
our own capture: the 17 chain names, and SPX and SPCX from their Massive chains, as
OS-10 reads them -- 19 symbols) divided by its trailing 20-session average: the
mean of the stored sessions before the day, up to 20. The call and put split from
the stored put share of volume (chain.put_share_volume). Until a name has 20 stored
sessions before the day it prints "provisional (n sessions)". Rows read through
opening_setup._series: a flat-file row joins only where flatfile_history admits it,
and a captured reading wins on a shared session.

OS-12b, THE FLAG. At least 1.5 times the average (config/opening_setup.yaml
relative_volume, session-set, provisional, frozen 30 days from 2026-10-20). Beside
each flagged name: the put/call split, the day's change in front-month ATM IV
(OS-10's method: the last two stored readings of chain.atm_iv_front) and any
report within 10 sessions (OS-11's events). Labelled "volume, no side": no side is
ever inferred.

D4, WHAT BECAME OF IT. Whether the volume became positions is knowable only the next
morning, when the open interest settles. So both the 07:00 anchor's OS-9 tag and
the next close's line RECOMPUTE the flag day's flags as of that day's close cutoff
(16:45 ET) -- no flag is stored -- so they match the table that close printed. "Became
an OI build" uses OS-9's builds on the pair made of the flag day's settled capture
and the next session's (the first whose open interest includes the flag day's
trades): a name became a build when OS-9 finds at least one build for it at or over
its floor (session-set and stated).

Report-only: no score, no composite, no weights, no side. It reads the store and
the capture files and writes nothing.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

TITLE = "Relative options volume (OS-12)"
NO_SIDE = "volume, no side"
COLUMNS = ["Name", "Volume against its 20-session average", "Calls / puts",
           "Front-month ATM IV, 1-day change", "Report within 10 sessions", "Label"]


def config(cfg: Optional[dict] = None) -> dict:
    from . import opening_setup                                 # noqa: PLC0415
    return (cfg or opening_setup.config())["relative_volume"]


def names() -> list[str]:
    from altdata import config as acfg                          # noqa: PLC0415
    return acfg.chain_universe() + sorted(acfg.massive_universe())


def close_cutoff(day: str, cfg: Optional[dict] = None) -> str:
    """The flag day's close cutoff (ET) as a UTC instant."""
    from altdata import session                                 # noqa: PLC0415
    h, m = (int(x) for x in str(config(cfg).get("close_cutoff_et", "16:45")).split(":"))
    t = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                            tzinfo=session._eastern_tz())        # noqa: SLF001
    return t.astimezone(dt.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# OS-12a -- the metric (pure)
# ---------------------------------------------------------------------------
def ratio(series: list[tuple[str, float]], day: str, window: int = 20) -> Optional[dict]:
    """The day's volume over the mean of up to `window` stored sessions before
    it; `provisional` while fewer than `window` are stored. None when the day or
    every prior session is missing."""
    by = dict(series)
    if day not in by:
        return None
    prior = [v for d, v in sorted(series) if d < day][-window:]
    if not prior or not sum(prior):
        return None
    avg = sum(prior) / len(prior)
    return {"day": day, "volume": by[day], "average": avg, "n": len(prior),
            "ratio": by[day] / avg, "provisional": len(prior) < window}


def ratio_text(r: dict) -> str:
    base = f"{r['ratio']:.2f}x ({r['volume']:,.0f} against {r['average']:,.0f})"
    return base + (f", provisional ({r['n']} sessions)" if r["provisional"] else "")


def split_text(put_share: Optional[float]) -> str:
    if put_share is None:
        return "split not stored"
    return f"calls {100.0 - put_share:.0f}% / puts {put_share:.0f}%"


def is_flag(r: Optional[dict], threshold: float) -> bool:
    return bool(r) and r["ratio"] >= threshold


# ---------------------------------------------------------------------------
# The reads (store as of the cutoff)
# ---------------------------------------------------------------------------
def _on(series: list[tuple[str, float]], day: str) -> Optional[float]:
    return dict(series).get(day)


def readings(st, day: str, cutoff: str, cfg: Optional[dict] = None,
             syms: Optional[list[str]] = None) -> list[dict]:
    from altdata import chain_metrics as cm                     # noqa: PLC0415
    from .opening_setup import _series                          # noqa: PLC0415
    c = config(cfg)
    out = []
    for s in syms or names():
        r = ratio(_series(st, cm.VOL_KEY, cutoff, s), day, int(c["window"]))
        if r is None:
            continue
        iv = [x for x in _series(st, cm.FRONT_IV_KEY, cutoff, s) if x[0] <= day]
        out.append({**r, "symbol": s,
                    "put_share": _on(_series(st, cm.PUT_VOL_KEY, cutoff, s), day),
                    "iv": iv[-1][1] if iv else None,
                    "iv_change": (iv[-1][1] - iv[-2][1]) if len(iv) > 1 else None,
                    "flag": is_flag(r, float(c["threshold"]))})
    return out


def reports_within(st_path: Optional[str], day: str, cutoff: str, sessions: int
                   ) -> dict[str, str]:
    """{symbol: report date} for a report in the next `sessions` sessions, from
    the events table (OS-11's: an earnings print or a scheduled earnings date)."""
    import json                                                 # noqa: PLC0415
    from altdata import events as ev_mod, session               # noqa: PLC0415
    d, ahead = dt.date.fromisoformat(day), []
    while len(ahead) < sessions:
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            ahead.append(d.isoformat())
    out: dict[str, str] = {}
    try:
        with ev_mod.EventStore(st_path) as ev:
            for r in ev.calendar(day, ahead[-1], as_of=cutoff):
                pl = r.get("payload") or {}
                if isinstance(pl, str):
                    pl = json.loads(pl or "{}")
                if not (r.get("type") == "earnings" or pl.get("kind") == "earnings"):
                    continue
                e = str(r["observed_at"])[:10]
                sym = str(pl.get("symbol") or "").upper()
                if day < e <= ahead[-1] and sym:
                    out[sym] = min(out.get(sym, e), e)
    except Exception:                                           # noqa: BLE001
        log.warning("OS-12: the earnings calendar faulted", exc_info=True)
    return out


def flagged(st, day: str, cutoff: str, cfg: Optional[dict] = None,
            syms: Optional[list[str]] = None) -> list[dict]:
    """The flagged names, highest ratio first."""
    rs = [r for r in readings(st, day, cutoff, cfg, syms) if r["flag"]]
    return sorted(rs, key=lambda r: -r["ratio"])


def flagged_yesterday(st, flag_day: str, cfg: Optional[dict] = None,
                      syms: Optional[list[str]] = None) -> set[str]:
    """D4: the flag day's flags, recomputed as of its close cutoff."""
    return {r["symbol"] for r in flagged(st, flag_day, close_cutoff(flag_day, cfg), cfg, syms)}


# ---------------------------------------------------------------------------
# The close's table and the next close's line
# ---------------------------------------------------------------------------
def table_rows(rs: list[dict], reports: dict[str, str], gated: set) -> list[list[str]]:
    from .opening_setup import SOLVER_GATED                     # noqa: PLC0415
    out = []
    for r in rs:
        if r["symbol"] in gated:
            iv = SOLVER_GATED
        elif r["iv"] is None:
            iv = "not stored"
        else:
            iv = (f"{r['iv']:.1f}%, "
                  + (f"{r['iv_change']:+.1f} pts" if r["iv_change"] is not None
                     else "no prior reading"))
        rep = reports.get(r["symbol"])
        out.append([r["symbol"], ratio_text(r), split_text(r["put_share"]), iv,
                    f"report {rep}" if rep else "none", NO_SIDE])
    return out


def close_table(st, day: str, cutoff: str, cfg: Optional[dict] = None,
                syms: Optional[list[str]] = None) -> Optional[dict]:
    """The 16:45 close's detail table: flagged names only, five rows at most;
    None on a session with no flag. Data, outside the word budget."""
    from altdata import config as acfg                          # noqa: PLC0415
    c = config(cfg)
    rs = flagged(st, day, cutoff, cfg, syms)
    if not rs:
        return None
    shown = rs[:int(c["max_rows"])]
    reports = reports_within(str(st.path), day, cutoff, int(c["earnings_sessions"]))
    note = (f"OS-12 (Batch 13 item 61): each name's session options volume (our own "
            f"capture; SPX and SPCX from their Massive chains) against its trailing "
            f"{c['window']}-session average; flagged at {c['threshold']:g}x or more "
            f"({c['label']}). {len(rs)} flagged, {len(shown)} shown. The front-month ATM "
            f"IV change is OS-10's (the last two stored readings). Volume, no side: "
            f"whether it opened positions shows in tomorrow's open interest.")
    return {"title": TITLE,
            "table": {"columns": COLUMNS,
                      "rows": table_rows(shown, reports, set(acfg.massive_universe()))},
            "legend": note, "data": {"relative_volume": shown, "flagged": len(rs)}}


def became_builds(flag_day: str, next_day: str, symbols: set,
                  base: Optional[Path] = None, cfg: Optional[dict] = None) -> dict:
    """{symbol: True/False/None}: OS-9's builds on the pair (the flag day's settled
    capture, the next session's); None where either capture is missing."""
    from altdata import chain_metrics as cm, config as acfg     # noqa: PLC0415
    from . import opening_setup as OS                           # noqa: PLC0415
    ocfg = OS.config() if cfg is None else cfg
    root = Path(base) if base else cm.chain_dir()
    gated = set(acfg.massive_universe())
    out = {}
    for s in sorted(symbols):
        a, b = cm.latest_capture(flag_day, root, s), cm.latest_capture(next_day, root, s)
        if not a or not b:
            out[s] = None
            continue
        bs = OS.builds_for(s, cm.load_rows(a), cm.load_rows(b), acfg.RISK_FREE_RATE,
                           gated=s in gated, floor=OS.oi_floor(s, ocfg))
        out[s] = bool(bs)
    return out


def next_close_line(st, flag_day: str, next_day: str, base: Optional[Path] = None,
                    cfg: Optional[dict] = None, syms: Optional[list[str]] = None
                    ) -> Optional[str]:
    """D4's line at the next close, or None when the flag day flagged nothing."""
    flags = flagged_yesterday(st, flag_day, cfg, syms)
    if not flags:
        return None
    got = became_builds(flag_day, next_day, flags, base, cfg)
    k = sorted(s for s, v in got.items() if v)
    m = sorted(s for s, v in got.items() if v is False)
    u = sorted(s for s, v in got.items() if v is None)
    line = (f"Yesterday's flagged names: {len(k)} became OI builds, {len(m)} did not"
            + (f" ({', '.join(k)} did)" if k else "")
            + (f"; {len(u)} without both captures ({', '.join(u)})" if u else "")
            + f" -- OS-9's builds on the {flag_day} and {next_day} captures; {NO_SIDE}.")
    return line


def week_counts(st, sessions: list[str], cutoff: str, cfg: Optional[dict] = None,
                syms: Optional[list[str]] = None) -> dict[str, int]:
    """The Weekly's count of flags per name over the week's sessions, each read
    as of its own close cutoff."""
    out: dict[str, int] = {}
    for d in sessions:
        for s in flagged_yesterday(st, d, cfg, syms):
            out[s] = out.get(s, 0) + 1
    return dict(sorted(out.items(), key=lambda x: (-x[1], x[0])))


LEDGER_GLOB = "os-12c-ledger-????-??-??.md"


def ledger_to_date(ledger_dir: Optional[Path] = None) -> str:
    """The newest OS-12c edition's verdict, n and as-of, read from its file."""
    import re                                                   # noqa: PLC0415
    d = ledger_dir or Path(__file__).resolve().parent.parent / "docs" / "ledgers"
    eds = sorted(d.glob(LEDGER_GLOB))
    if not eds:
        return "OS-12c's ledger: no edition yet (pre-registered; it accrues from the captures)."
    txt = eds[-1].read_text(encoding="utf-8")
    pick = lambda k: (re.search(rf"^\| {k} \| (.+?) \|$", txt, re.M) or [None, "—"])[1]  # noqa: E731
    return (f"OS-12c's ledger to date ({eds[-1].name}): {pick('Verdict').strip('*')}; "
            f"n {pick('n')}; as of {pick('As of')}. Rights: none until it passes.")


def weekly_subsection(st, sessions: list[str], cutoff: str, cfg: Optional[dict] = None,
                      syms: Optional[list[str]] = None,
                      ledger_dir: Optional[Path] = None) -> dict:
    """The Weekly's table: the week's flags per name, and the ledger to date."""
    counts = week_counts(st, sessions, cutoff, cfg, syms)
    c = config(cfg)
    rows = [[s, str(n)] for s, n in counts.items()]
    lines = ([] if rows else
             [f"No name flagged this week (at or over {c['threshold']:g}x its "
              f"{c['window']}-session average)."])
    lines.append(ledger_to_date(ledger_dir))
    return {"title": TITLE, "table": {"columns": ["Name", "Sessions flagged"],
                                      "rows": rows},
            "lines": lines, "paragraph_wanted": False,
            "table_note": (f"OS-12: each session's flags as its close printed them "
                           f"({c['threshold']:g}x the trailing {c['window']}-session "
                           f"average; {c['label']}). Volume, no side."),
            "data": {"relative_volume_week": counts}}

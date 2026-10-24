#!/usr/bin/env python3
"""
THE DIGITAL ASSETS ADDENDUM to the Sunday Weekly (Batch 8 item 51, Phase 1,
ST-R6.51a; docs/change-order-signal-triage-batch-8-2026-10-17.md; 6e-digital,
17 Oct 2026). Config: config/digital_addendum.yaml.

    python -m daily_cascade.digital_addendum render --week-ending 2026-10-30 \\
        [--as-of ISO] [--no-narrative] [--out DIR]

NOT A SIXTH REPORT (the ruling): a fixed chapter rendered as its own page off the
Sunday Weekly's run, five minutes and phone-readable, archived beside the Weekly
and attached to its message; the Weekly prints one line pointing to it. It holds
the ten-section stack in miniature, crypto only, in the ruling's order:

  1 the read             one paragraph by the existing narrative step
                         (narrative.generate, its numeral audit, then the stack's
                         style, figure and stance audits), from the figures on
                         this page only; withheld with its reason otherwise
  2 tape                 BTC, ETH, SOL, ZEC: the weekly bar built from the
                         dailies, read against the daily and the 30-day bars;
                         realised vol; the derivatives cells
  3 flows                ETF totals, exchange flows, stablecoin supply,
                         treasury-company purchases
  4 mechanics            skew and term structure, mNAV, MSTR's implied move to
                         each event date from the chain store, crypto GEX
  5 on-chain             SR-29's long-term-holder share, the froth gauge,
                         exchange balances
  6 narratives and       the X pilot's ledgers and digests from the box's inbox,
    attention            and the Saturday scan's stored items
  7 incidents and        the digests' incident and regulation items; the
    regulation           calendar's regulatory dates
  8 ahead                config/digital_asset_calendar.yaml (item 49c), the FOMC
                         dates, Deribit's month-end expiries
  9 the book             Book D's paper decisions, the register opened read-only

PHASE 1 ASSEMBLES FROM WHAT ALREADY FLOWS. A cell whose source is Batch 4
Tranche A prints "awaiting Tranche A" until its key has a row at the cutoff:
never a guess, never a proxy. Every section is code-written; the model writes
only the read, and only from this page's figures.

POINT IN TIME. Every store read is as of the cutoff (the Weekly's: Sunday 05:00
ET). An inbox file's available_at is the sweep's copy instant, read from the
`<file>.copied_at` stamp the sweep writes beside it; a row from a file copied
after the cutoff does not print.

REPORT ONLY. Nothing on the page has decision rights; nothing here writes the
register, the ledgers or the store.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import logging
import math
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

log = logging.getLogger("daily_cascade.digital_addendum")

CONFIG_PATH = REPO / "config" / "digital_addendum.yaml"
NO_DIGEST = "no digest rows this week"
NOT_CAPTURED = "not captured"
PAGE_NAME = "weekly_digital_{ending}.html"
PDF_NAME = "weekly_digital_{ending}.pdf"
EDITION_NAME = "weekly_digital_{ending}_edition.json"
APPENDIX_NAME = "weekly_digital_{ending}_appendix.md"
SECTIONS = [("read", "The read"), ("tape", "Tape"), ("flows", "Flows"),
            ("mechanics", "Mechanics"), ("onchain", "On-chain"),
            ("attention", "Narratives and attention"),
            ("incidents", "Incidents and regulation"), ("ahead", "Ahead"),
            ("book", "The book")]


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def page_name(ending: str) -> str:
    return PAGE_NAME.format(ending=ending)


def inbox_dir() -> Path:
    """The box's inbox: $CHESTER_INBOX_DIR, else $CHESTER_DATA_DIR/inbox, else
    ~/chester-data/inbox (scripts/rclone_sync.sh's DATA_DIR)."""
    if os.environ.get("CHESTER_INBOX_DIR"):
        return Path(os.environ["CHESTER_INBOX_DIR"]).expanduser()
    return Path(os.environ.get("CHESTER_DATA_DIR") or "~/chester-data").expanduser() \
        / "inbox"


# ---------------------------------------------------------------------------
# The crypto week
# ---------------------------------------------------------------------------
def crypto_week(ending: str) -> tuple[str, str]:
    """(Sunday, Saturday) of the crypto week the Sunday Weekly reports: the week
    closes Saturday 24:00 UTC, the day after the Weekly's Friday."""
    sat = dt.date.fromisoformat(ending[:10]) + dt.timedelta(days=1)
    return (sat - dt.timedelta(days=6)).isoformat(), sat.isoformat()


def _minus(day: str, n: int) -> str:
    return (dt.date.fromisoformat(day[:10]) - dt.timedelta(days=n)).isoformat()


def _plus(day: str, n: int) -> str:
    return (dt.date.fromisoformat(day[:10]) + dt.timedelta(days=n)).isoformat()


def _pts(st, key: str, cutoff: str, instrument: Optional[str] = None
         ) -> list[tuple[str, float]]:
    out = []
    for r in st.as_of(key, cutoff, instrument):
        if r.get("value_num") is not None:
            out.append((str(r["observed_at"])[:10], float(r["value_num"])))
    return sorted(out)


def _at(pts: list, day: str) -> Optional[tuple[str, float]]:
    """The last point on or before `day`."""
    best = None
    for p in pts:
        if p[0] <= day:
            best = p
        else:
            break
    return best


def _pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    return 100.0 * (a / b - 1.0)


# ---------------------------------------------------------------------------
# Formatting: what the page prints is what the read may cite
# ---------------------------------------------------------------------------
def fmt_price(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"${v:,.0f}" if abs(v) >= 1000 else f"${v:,.2f}"


def fmt_pct(v: Optional[float], dp: int = 1) -> str:
    return "—" if v is None else f"{v:+.{dp}f}%"


def fmt_unit(v: Optional[float], unit: str) -> str:
    if v is None:
        return "—"
    if unit == "usd":
        a = abs(v)
        s = "-" if v < 0 else ""
        if a >= 1e9:
            return f"{s}${a / 1e9:,.1f}bn"
        if a >= 1e6:
            return f"{s}${a / 1e6:,.0f}m"
        return f"{s}${a:,.0f}"
    if unit == "usd_m":
        return f"{v:+,.1f} $m"
    if unit == "pct":
        return f"{v:.2f}%"
    if unit == "z":
        return f"z {v:+.1f}"
    if unit == "btc":
        return f"{v:,.0f} BTC"
    if unit == "count":
        return f"{v:,.0f}"
    return f"{v:,.1f}"


def short_date(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    return f"{d.day} {d:%b}"


# ---------------------------------------------------------------------------
# 2. The tape
# ---------------------------------------------------------------------------
def coin_bar(pts: list, week_end: str, vol_days: int = 30, month_days: int = 30
             ) -> Optional[dict]:
    """The weekly bar from the daily closes to `week_end`, read against the daily
    bar (the last day's change) and the monthly bar (`month_days` trailing)."""
    pts = [p for p in pts if p[0] <= week_end]
    if not pts:
        return None
    last_d, last = pts[-1]
    prev = pts[-2][1] if len(pts) > 1 else None
    w0 = _at(pts, _minus(last_d, 7))
    m0 = _at(pts, _minus(last_d, month_days))
    week = [v for d, v in pts if _minus(last_d, 7) < d <= last_d]
    rets = [math.log(b[1] / a[1]) for a, b in zip(pts[-vol_days - 1:-1], pts[-vol_days:])
            if a[1] > 0 and b[1] > 0]
    vol = (100.0 * math.sqrt(365.0) * (sum((r - sum(rets) / len(rets)) ** 2
                                           for r in rets) / (len(rets) - 1)) ** 0.5
           if len(rets) >= max(10, vol_days // 2) else None)
    return {"as_of": last_d, "close": last,
            "day_pct": _pct(last, prev),
            "week_pct": _pct(last, w0[1] if w0 else None),
            "month_pct": _pct(last, m0[1] if m0 else None),
            "week_low": min(week), "week_high": max(week),
            "vol_pct": vol, "n_week": len(week)}


def tape_section(st, cutoff: str, week_end: str, cfg: dict) -> dict:
    tc = cfg.get("tape") or {}
    rows, data, lines, absent = [], [], [], []
    for c in tc.get("coins") or []:
        bar = coin_bar(_pts(st, c["key"], cutoff), week_end,
                       int(tc.get("vol_days") or 30), int(tc.get("month_days") or 30))
        if bar is None:
            absent.append(f"{c['sym']}: no stored close at the cutoff")
            continue
        rows.append([c["sym"], fmt_price(bar["close"]), fmt_pct(bar["day_pct"]),
                     fmt_pct(bar["week_pct"]), fmt_pct(bar["month_pct"]),
                     "—" if bar["vol_pct"] is None else f"{bar['vol_pct']:.0f}%"])
        lines.append(f"{c['sym']} {fmt_price(bar['week_low'])} to "
                     f"{fmt_price(bar['week_high'])} (to {short_date(bar['as_of'])})")
        data.append({"coin": c["sym"], **{k: (None if v is None else round(v, 2))
                                          if isinstance(v, float) else v
                                          for k, v in bar.items()}})
    # PHASE 2: ONE LINE for the four weekly ranges (the line budget).
    lines = (["The week's range on daily closes: " + "; ".join(lines) + "."]
             if lines else [])
    deriv = cells_table(st, cutoff, tc.get("derivatives") or [], cfg, week_end)
    return {"tables": [{"columns": ["Coin", "Close", "Day", "Week", "30 days",
                                    "Realised vol (30d)"], "rows": rows},
                       deriv["table"]],
            "lines": lines + absent, "data": {"coins": data, "cells": deriv["data"]},
            "footnote": "Yahoo daily closes (UTC days); the week is the seven closes "
                        "to the last stored day; realised vol is 30 daily log "
                        "returns annualised over 365 days."}


# ---------------------------------------------------------------------------
# Cells: a figure where the key has a row, the phrase where it does not
# ---------------------------------------------------------------------------
def cell(st, c: dict, cutoff: str, week_end: str, awaiting: str) -> dict:
    absent = c.get("absent") or awaiting
    key = c.get("key")
    if not key:
        return {"label": c["label"], "text": absent, "value": None, "as_of": None}
    pts = [p for p in _pts(st, key, cutoff, c.get("instrument")) if p[0] <= week_end]
    if not pts:
        if key == "btcdata.lth_supply_share":
            # SR-29: not tracked without the key, awaiting the first pull with it
            from altdata import crypto_blocks                   # noqa: PLC0415
            absent = crypto_blocks.sr29_absent()
        return {"label": c["label"], "text": absent, "value": None, "as_of": None}
    agg = c.get("agg")
    if agg == "sum_week":
        wk = [v for d, v in pts if _minus(week_end, 7) < d <= week_end]
        v = sum(wk) if wk else None
    elif agg == "change_week":
        a = _at(pts, _minus(pts[-1][0], 7))
        v = pts[-1][1] - a[1] if a else None
    else:
        v = pts[-1][1]
    if v is None:
        return {"label": c["label"], "text": absent, "value": None, "as_of": None}
    text = fmt_unit(v, c.get("unit") or "")
    if agg == "change_week" and v > 0:
        text = "+" + text                       # a change carries its sign
    return {"label": c["label"], "text": text,
            "value": round(v, 4), "as_of": pts[-1][0], "key": key}


def mnav_cell(st, c: dict, cutoff: str, cfg: dict) -> dict:
    """ITEM 49's ONE FLAG (Batch 8, item 49): mNAV with the 1.2 watch line and
    the 1.0 flag line. The flag prints when the latest capture is at or below 1.0,
    with its date; nothing else is derived from it. Dual percentiles over the
    series' own history once `min_obs` sessions exist; before, the level and
    "percentile from <date>". Absent: "not tracked" with the missing input."""
    m = (cfg.get("mechanics") or {}).get("mnav") or {}
    watch, flag = float(m.get("watch", 1.2)), float(m.get("flag", 1.0))
    pts = _pts(st, c.get("key") or "calc.mnav", cutoff, c.get("instrument") or "MSTR")
    if not pts:
        missing = [lab for k, inst, lab in (
            ("treasury.mstr_shares", None, "the share count (EDGAR: CHESTER_SEC_CONTACT)"),
            ("treasury.btc_holdings", "MSTR", "Strategy's BTC holdings"),
            ("treasury.mstr_spot", "MSTR", "MSTR's captured spot"))
            if not st.as_of(k, cutoff, inst)]
        why = "; ".join(missing) or "no session with every input"
        return {"label": c["label"], "text": f"not tracked ({why})", "value": None,
                "as_of": None, "key": "calc.mnav"}
    d, v = pts[-1]
    parts = [f"{v:.2f}",
             f"{'at or below' if v <= watch else 'above'} the {watch:g} watch line"]
    if v <= flag:
        parts.append(f"FLAG: at or below {flag:g} on {short_date(d)}")
    n, need = len(pts), int(m.get("min_obs") or 60)
    if n >= need:
        from altdata import derived                              # noqa: PLC0415
        p5 = derived._pct_in_window(pts, v, dt.date.fromisoformat(cutoff[:10]), 5)  # noqa: SLF001
        pf = derived._pct_in_window(pts, v, dt.date.fromisoformat(cutoff[:10]), "full")  # noqa: SLF001
        parts.append(f"{derived._ord(p5['pct'])} percentile over 5 years, "  # noqa: SLF001
                     f"{derived._ord(pf['pct'])} over its history (n={n})")  # noqa: SLF001
    else:
        first = dt.date.fromisoformat(pts[0][0])
        parts.append(f"percentile from {short_date((first + dt.timedelta(days=int(need * 7 / 5))).isoformat())}")
    return {"label": c["label"], "text": "; ".join(parts), "value": round(v, 4),
            "as_of": d, "key": "calc.mnav", "flag": v <= flag}


def cells_table(st, cutoff: str, cells: list, cfg: dict, week_end: str) -> dict:
    aw = cfg.get("awaiting") or "awaiting Tranche A"
    out = [mnav_cell(st, c, cutoff, cfg) if c.get("panel") == "mnav"
           else cell(st, c, cutoff, week_end, aw) for c in cells]
    return {"table": {"columns": ["Measure", "Reading", "As of"],
                      "rows": [[x["label"], x["text"],
                                short_date(x["as_of"]) if x["as_of"] else "—"]
                               for x in out]},
            "data": out}


def who_is_buying(st, cutoff: str, cfg: dict) -> dict:
    """ITEM 49b: the latest complete month's BTC demand by leg -- ETF net flow
    (each session's Farside total over that day's BTC close), treasury-company
    net purchases (calc.treasury_net_purchases), new supply (blocks mined x the
    subsidy) -- and the residual (ETF + treasury - new supply). A leg with no
    reading prints "not tracked" and the residual is withheld."""
    wc = cfg.get("who_is_buying") or {}
    tnp = _pts(st, "calc.treasury_net_purchases", cutoff)
    # The month: the treasury leg's newest month, else the last complete month.
    if tnp:
        end = tnp[-1][0]
    else:
        first = dt.date.fromisoformat(cutoff[:10]).replace(day=1)
        end = (first - dt.timedelta(days=1)).isoformat()
    start = dt.date.fromisoformat(end).replace(day=1).isoformat()
    prev_end = (dt.date.fromisoformat(start) - dt.timedelta(days=1)).isoformat()
    month = dt.date.fromisoformat(end).strftime("%B %Y")
    legs: dict[str, Optional[float]] = {}
    why: dict[str, str] = {}
    flows = [p for p in _pts(st, "farside.btc_total", cutoff) if start <= p[0] <= end]
    btc = dict(_pts(st, "yfinance.mkt_btc_usd", cutoff))
    if len(flows) >= int(wc.get("min_sessions") or 15):
        conv = [v / btc[d] for d, v in flows if btc.get(d)]
        legs["etf"] = sum(conv) if len(conv) == len(flows) else None
        if legs["etf"] is None:
            why["etf"] = "a session without its BTC close"
    else:
        legs["etf"] = None
        why["etf"] = f"{len(flows)} Farside sessions stored for the month"
    t = next((v for d, v in tnp if d == end), None)
    legs["treasury"] = t
    if t is None:
        why["treasury"] = "no treasury snapshots at both month ends"
    tip = _pts(st, "mempool.tip_height", cutoff)
    w = int(wc.get("snapshot_window_days") or 3)

    def near(day):
        ks = [(d, v) for d, v in tip if d <= day and d >= (
            dt.date.fromisoformat(day) - dt.timedelta(days=w)).isoformat()]
        return ks[-1][1] if ks else None
    a, b = near(prev_end), near(end)
    legs["supply"] = ((b - a) * float(wc.get("subsidy_btc") or 3.125)
                      if a is not None and b is not None else None)
    if legs["supply"] is None:
        why["supply"] = "no chain-tip snapshots at both month ends"
    fmt = lambda v: f"{v:+,.0f} BTC"                             # noqa: E731
    rows = [[f"ETF net flow ({month})", fmt(legs["etf"]) if legs["etf"] is not None
             else f"not tracked ({why['etf']})"],
            [f"Treasury-company net purchases ({month})",
             fmt(legs["treasury"]) if legs["treasury"] is not None
             else f"not tracked ({why['treasury']})"],
            [f"New supply mined ({month})", f"{legs['supply']:,.0f} BTC"
             if legs["supply"] is not None else f"not tracked ({why['supply']})"]]
    if all(v is not None for v in legs.values()):
        res = legs["etf"] + legs["treasury"] - legs["supply"]
        rows.append(["Residual: the two buyers beyond new supply", fmt(res)])
    else:
        res = None
        rows.append(["Residual: the two buyers beyond new supply",
                     "withheld (a leg is not tracked)"])
    return {"table": {"title": "Who is buying (item 49b)",
                      "columns": ["Leg", "BTC"], "rows": rows},
            "data": {"month": end, **legs, "residual": res}}


def plain_section(st, cutoff: str, week_end: str, cells: list, cfg: dict,
                  footnote: str) -> dict:
    t = cells_table(st, cutoff, cells, cfg, week_end)
    return {"tables": [t["table"]], "lines": [], "data": {"cells": t["data"]},
            "footnote": footnote}


# ---------------------------------------------------------------------------
# 4. Mechanics
# ---------------------------------------------------------------------------
def mechanics_section(st, cutoff: str, week_end: str, cfg: dict,
                      chain_base: Optional[Path] = None) -> dict:
    mc = cfg.get("mechanics") or {}
    t = cells_table(st, cutoff, mc.get("cells") or [], cfg, week_end)
    im = mc.get("implied_moves") or {}
    sym = im.get("symbol") or "MSTR"
    rows, data = [], []
    from . import ahead                                         # noqa: PLC0415
    for d in im.get("dates") or []:
        d = str(d)
        if d < cutoff[:10]:
            continue
        mv = ahead.implied_move(sym, d, cutoff, chain_base)
        rows.append([f"{sym} to {short_date(d)}", mv or f"implied move {NOT_CAPTURED}"])
        data.append({"symbol": sym, "date": d, "implied_move": mv})
    tables = [t["table"]]
    if rows:
        tables.append({"columns": ["Through the event window", "Option-implied move"],
                       "rows": rows})
    return {"tables": tables, "lines": [],
            "data": {"cells": t["data"], "implied_moves": data},
            "footnote": "The implied move is the at-the-money straddle on the first "
                        "expiry on or after the date, over spot, from the newest "
                        "captured MSTR chain."}


# ---------------------------------------------------------------------------
# 6 and 7. The X pilot's files, from the inbox
# ---------------------------------------------------------------------------
def copied_at(path: Path) -> tuple[Optional[str], str]:
    """(available_at, how): the sweep's stamp beside the file, else its mtime."""
    stamp = path.with_name(path.name + ".copied_at")
    try:
        txt = stamp.read_text(encoding="utf-8").strip()
        if txt:
            return _utc(txt), "copied_at"
    except OSError:
        pass
    try:
        return (dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)
                .isoformat(timespec="seconds"), "mtime")
    except OSError:
        return None, "absent"


def _utc(iso: str) -> str:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def _visible(path: Path, cutoff: str) -> tuple[bool, str]:
    av, how = copied_at(path)
    return (av is not None and av <= _utc(cutoff)), how


def _clean(s: Any) -> str:
    """The Drive export escapes Markdown (\\_ for _); the file may not."""
    return re.sub(r"\\([_\\*#|~\[\]()-])", r"\1", str(s or "")).strip()


def read_ledger(path: Path, cutoff: str) -> tuple[list[dict], str]:
    if not path.is_file():
        return [], "absent"
    ok, how = _visible(path, cutoff)
    if not ok:
        return [], "copied after the cutoff"
    try:
        rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    except (OSError, csv.Error):
        return [], "unreadable"
    return [{k.strip(): _clean(v) for k, v in r.items() if k} for r in rows], how


def digest_files(d: Path, sun: str, sat: str, cutoff: str) -> list[tuple[str, Path]]:
    out = []
    if not d.is_dir():
        return out
    for p in sorted(d.glob("x-digest-*.md")):
        m = re.match(r"x-digest-(\d{4}-\d{2}-\d{2})", p.name)
        if m and sun <= m.group(1) <= sat and _visible(p, cutoff)[0]:
            out.append((m.group(1), p))
    return out


def digest_sections(text: str) -> dict[str, str]:
    """`## N. Name` -> body, names lower-cased."""
    out: dict[str, str] = {}
    cur = None
    for line in _clean_md(text).splitlines():
        m = re.match(r"^#{1,3}\s*\d+\.\s*(.+?)\s*$", line)
        if m:
            cur = m.group(1).strip().lower()
            out[cur] = ""
        elif cur is not None:
            out[cur] += line + "\n"
    return out


def _clean_md(text: str) -> str:
    return re.sub(r"\\([_\\*#|~\[\]()-])", r"\1", text)


X_URL = re.compile(r"https?://(?:x|twitter)\.com/[^\s|)]+/status/\d+")


def disagreements(body: str) -> list[dict]:
    """Question / Side A / Side B blocks; a pair prints only when both sides
    carry a post URL."""
    out, q, sides = [], None, {}
    for line in body.splitlines():
        s = line.strip()
        m = re.match(r"^[-*]?\s*Question:\s*(.+)$", s, re.I)
        if m:
            if q and len(sides) == 2:
                out.append({"question": q, **sides})
            q, sides = m.group(1).strip(), {}
            continue
        m = re.match(r"^[-*]?\s*Side\s+([AB])\b[^:]*:\s*(.+)$", s, re.I)
        if m and q:
            u = X_URL.search(m.group(2))
            if u:
                sides[f"side_{m.group(1).lower()}"] = u.group(0)
    if q and len(sides) == 2:
        out.append({"question": q, **sides})
    return out


def digest_items(body: str) -> list[dict]:
    """Section 2's rows: url | handle | time | claim | figures | engagement |
    theme | linked source. A row without a post URL is not an item."""
    out = []
    for line in body.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7 or not X_URL.match(parts[0]):
            continue
        out.append({"url": parts[0], "handle": parts[1], "time": parts[2],
                    "claim": parts[3], "theme": parts[6].lower()})
    return out


def _whole(s: str) -> str:
    """Whitespace collapsed; never shortened (D19/D20, 24 Oct 2026: a cell prints
    in full -- the 110- and 120-character truncations are retired)."""
    return re.sub(r"\s+", " ", s).strip()


def attention_section(st, cutoff: str, sun: str, sat: str, cfg: dict,
                      inbox: Optional[Path] = None) -> dict:
    ac = cfg.get("attention") or {}
    base = inbox or inbox_dir()
    tri = base / (ac.get("triage_dir") or "x-triage")
    led, how_a = read_ledger(tri / (ac.get("attention_ledger") or "x-attention-ledger.csv"),
                             cutoff)
    voices, how_v = read_ledger(tri / (ac.get("voices_ledger") or "x-voices-ledger.csv"),
                                cutoff)
    week = [r for r in led if sun <= str(r.get("date") or "")[:10] <= sat]
    themes: dict[str, dict] = {}
    rank = {"high": 3, "medium": 2, "low": 1}
    for r in sorted(week, key=lambda r: r.get("date") or ""):
        t = themes.setdefault(r.get("theme") or "unnamed",
                              {"days": set(), "peak": "", "shocks": [], "url": ""})
        t["days"].add(r["date"][:10])
        vc = (r.get("volume_class") or "").lower()
        if rank.get(vc, 0) > rank.get(t["peak"], 0):
            t["peak"] = vc
        if (r.get("shock_flag") or "").lower() in ("yes", "y", "true", "1"):
            t["shocks"].append(r["date"][:10])
        if X_URL.match(r.get("representative_url") or ""):
            t["url"] = r["representative_url"]
    order = sorted(themes, key=lambda k: (-rank.get(themes[k]["peak"], 0),
                                          -len(themes[k]["days"]), k))
    order = order[:int(ac.get("max_themes") or 9)]
    t_rows = [[k, str(len(themes[k]["days"])), themes[k]["peak"] or "—",
               str(len(themes[k]["shocks"])), themes[k]["url"] or "no post URL in the row"]
              for k in order]
    digs = digest_files(base / (ac.get("digest_dir") or "x-digest"), sun, sat, cutoff)
    pairs = []
    for day, p in digs:
        sec = digest_sections(p.read_text(encoding="utf-8"))
        for d in disagreements(next((v for k, v in sec.items()
                                     if k.startswith("disagree")), "")):
            pairs.append({"date": day, **d})
    new_v = [v for v in voices if sun <= str(v.get("first_seen") or "")[:10] <= sat]
    from altdata import crypto_basket                           # noqa: PLC0415
    try:
        scan = crypto_basket.scan_items(st, _minus(sun, 1), sat, as_of=cutoff)
    except Exception:                                           # noqa: BLE001
        scan = []
    tables, lines = [], []
    if t_rows:
        tables.append({"title": "The week's attention map", "columns":
                       ["Theme", "Days", "Peak volume", "Shock days", "Post"],
                       "rows": t_rows})
    if pairs:
        tables.append({"title": "Disagreement pairs", "columns":
                       ["Date", "Question", "Side A", "Side B"],
                       "rows": [[short_date(x["date"]), _whole(x["question"]),
                                 x["side_a"], x["side_b"]] for x in pairs[:4]]})
    if new_v:
        tables.append({"title": "New voices (the voices ledger)", "columns":
                       ["Handle", "Role", "Incentive"],
                       "rows": [[v.get("handle"), _whole(v.get("role") or ""),
                                 v.get("incentive_tag") or "—"] for v in new_v[:6]]})
    if scan:
        tables.append({"title": "The Saturday scan", "columns":
                       ["Date", "Name", "Kind", "Item"],
                       "rows": [[short_date(x["date"]), x["name"], x.get("kind"),
                                 f"{_whole(x.get('title') or '')} ({x.get('url')})"]
                                for x in scan[:6]]})
    if not week and not digs:
        lines.append(f"X attention: {NO_DIGEST}.")
    foot = ("The X pilot's ledgers and digests (item 50, Tranche 0), from the box's "
            "inbox after the nightly sweep; available as of the sweep's copy time"
            + ("" if "mtime" not in (how_a, how_v) else
               " (a file without its copy stamp: its modification time)")
            + ". A theme prints from its ledger rows; a disagreement pair only with "
              "both posts' URLs. Grok retrieves; nothing here is its judgement.")
    return {"tables": tables, "lines": lines,
            "data": {"themes": [{"theme": k, "days": len(themes[k]["days"]),
                                 "peak": themes[k]["peak"],
                                 "shock_days": len(themes[k]["shocks"])} for k in order],
                     "pairs": len(pairs), "new_voices": len(new_v),
                     "scan_items": len(scan), "ledger_rows": len(week),
                     "digests": [d for d, _ in digs]},
            "footnote": foot}


def incidents_section(cutoff: str, sun: str, sat: str, cfg: dict, cal: list[dict],
                      inbox: Optional[Path] = None) -> dict:
    ac = cfg.get("attention") or {}
    base = inbox or inbox_dir()
    themes = {t.lower() for t in ac.get("incident_themes") or []}
    items = []
    digs = digest_files(base / (ac.get("digest_dir") or "x-digest"), sun, sat, cutoff)
    for day, p in digs:
        sec = digest_sections(p.read_text(encoding="utf-8"))
        for it in digest_items(next((v for k, v in sec.items() if k == "items"), "")):
            if it["theme"] in themes and it["url"] not in {x["url"] for x in items}:
                items.append({**it, "date": day})
    items = items[:int(ac.get("max_items") or 6)]
    reg = [e for e in cal if e.get("kind") == "regulation"]
    tables, lines = [], []
    if items:
        tables.append({"title": "From the week's digests", "columns":
                       ["Date", "Account", "Theme", "As posted", "Post"],
                       "rows": [[short_date(x["date"]), x["handle"], x["theme"],
                                 _whole(x["claim"]), x["url"]] for x in items]})
    if reg:
        tables.append({"title": "Regulatory calendar", "columns":
                       ["Date", "Who", "Event"],
                       "rows": [[short_date(e["date"]), e["body"], e["event"]]
                                for e in reg]})
    if not digs:
        lines.append(f"Incidents from X: {NO_DIGEST}.")
    elif not items:
        lines.append("No incident or regulation item in the week's digests.")
    return {"tables": tables, "lines": lines,
            "data": {"items": len(items), "regulatory_dates": len(reg)},
            "footnote": "Items as the digests record them, each with its post's URL; "
                        "the claim is the account's, not checked here."}


# ---------------------------------------------------------------------------
# 8. Ahead
# ---------------------------------------------------------------------------
def load_calendar(path: Optional[Path] = None, cfg: Optional[dict] = None) -> dict:
    p = path or (REPO / ((cfg or config()).get("ahead") or {}).get(
        "calendar", "config/digital_asset_calendar.yaml"))
    try:
        return yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}


def deribit_expiries(first: str, last: str, weekday: int = 4) -> list[str]:
    """The last `weekday` (Friday) of each month between two dates."""
    out = []
    d = dt.date.fromisoformat(first[:10]).replace(day=1)
    end = dt.date.fromisoformat(last[:10])
    while d <= end:
        nxt = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        x = nxt - dt.timedelta(days=1)
        while x.weekday() != weekday:
            x -= dt.timedelta(days=1)
        if first[:10] <= x.isoformat() <= last:
            out.append(x.isoformat())
        d = nxt
    return out


def fomc_dates(first: str, last: str, cutoff: str,
               events_db: Optional[str] = None) -> list[dict]:
    try:
        from altdata import events as ev_mod                    # noqa: PLC0415
        with ev_mod.EventStore(events_db) as es:
            rows = es.calendar(first, last, cutoff)
    except Exception:                                           # noqa: BLE001
        return []
    out, seen = [], set()
    for r in rows:
        if "FOMC" in str(r.get("title") or "") and r.get("type") == "scheduled":
            d = str(r.get("observed_at"))[:10]
            if d not in seen:
                seen.add(d)
                out.append({"date": d, "body": "Federal Reserve",
                            "event": "FOMC meeting", "kind": "macro",
                            "time": "statement 14:00 ET"})
    return out


def calendar_window(cal: dict, first: str, last: str) -> list[dict]:
    out = []
    for e in cal.get("entries") or []:
        d = str(e.get("date"))[:10]
        if first <= d <= last:
            out.append({**e, "date": d})
    return out


def ahead_section(cutoff: str, cfg: dict, cal: dict,
                  events_db: Optional[str] = None) -> dict:
    ah = cfg.get("ahead") or {}
    first = cutoff[:10]
    last = _plus(first, int(ah.get("window_days") or 45))
    rows = calendar_window(cal, first, last)
    rows += fomc_dates(first, last, cutoff, events_db)
    de = ah.get("deribit_expiry") or {}
    for d in deribit_expiries(first, last, int(de.get("weekday", 4))):
        rows.append({"date": d, "body": "Deribit", "event": "month-end options expiry",
                     "kind": "expiry", "time": de.get("time") or "08:00 UTC",
                     "marker": de.get("marker")})
    rows.sort(key=lambda e: (e["date"], e.get("body") or ""))
    t_rows = []
    for e in rows:
        status = "; ".join(x for x in (e.get("time"), e.get("marker")) if x) or "—"
        t_rows.append([short_date(e["date"]), f"{e['body']}: {e['event']}", status])
    und = cal.get("watch_undated") or []
    lines = (["Date not published: " + "; ".join(
        f"{w['body']}, {w['event']} ({w['reason']})" for w in und) + "."] if und else [])
    return {"tables": [{"columns": ["Date", "Event", "Time / status"], "rows": t_rows}],
            "lines": lines,
            "data": {"events": [{"date": e["date"], "event": e["event"],
                                 "body": e["body"], "marker": e.get("marker")}
                                for e in rows]},
            "footnote": f"Dated events to {short_date(last)} from "
                        f"config/digital_asset_calendar.yaml (by hand, each with its "
                        f"source), the FOMC dates from the events store and "
                        f"Deribit's monthly expiries by rule. A date marked \"to "
                        f"verify\" is not yet confirmed at its source."}


# ---------------------------------------------------------------------------
# 9. The book: the register, opened read-only
# ---------------------------------------------------------------------------
def register_path() -> Path:
    return Path(os.environ.get("CHESTER_DB") or (REPO / "data" / "chester.db"))


def _is_crypto(inst: str, names: list[str]) -> bool:
    up = str(inst or "").upper()
    return any(re.match(rf"^{re.escape(n.upper())}(?![A-Z])", up) for n in names)


def book_section(cfg: dict, db_path: Optional[Path] = None) -> dict:
    bc = cfg.get("book") or {}
    book = bc.get("book") or "D"
    names = bc.get("instruments") or []
    p = Path(db_path) if db_path else register_path()
    note = bc.get("engine_note")
    if not p.is_file():
        return {"tables": [], "lines": [f"Book {book}: the register is not readable "
                                        f"here ({p.name} absent)."]
                + ([note[0].upper() + note[1:] + "."] if note else []),
                "data": {"state": "absent"}, "footnote": ""}
    try:
        # READ-ONLY, at the connection: the register is the operator's record,
        # and this page never writes it -- not even the schema migrations that
        # register.store.Register() runs when it opens a file.
        con = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        cols = {r[1] for r in con.execute("PRAGMA table_info(decisions)")}
        if "book" not in cols:
            con.close()
            return {"tables": [], "lines": [f"Book {book}: the register carries no "
                                            f"book column yet."],
                    "data": {"state": "no_book_column"}, "footnote": ""}
        want = [c for c in ("instrument", "direction", "status", "notional_usd",
                            "vega_usd", "created_at") if c in cols]
        rows = [dict(r) for r in con.execute(
            f"SELECT {', '.join(want)} FROM decisions WHERE book = ? AND "
            f"superseded_by IS NULL AND status IN ('active', 'draft') "
            f"ORDER BY created_at", (book,))]
        con.close()
    except sqlite3.Error as exc:
        return {"tables": [], "lines": [f"Book {book}: the register could not be "
                                        f"read ({type(exc).__name__})."],
                "data": {"state": "error"}, "footnote": ""}
    crypto = [r for r in rows if _is_crypto(r.get("instrument"), names)]
    active = [r for r in crypto if r.get("status") == "active"]
    drafts = [r for r in crypto if r.get("status") == "draft"]
    t_rows = [[r["instrument"], r.get("direction") or "—",
               fmt_unit(r.get("notional_usd"), "usd") if r.get("notional_usd") is not None
               else "not recorded",
               fmt_unit(r.get("vega_usd"), "usd") if r.get("vega_usd") is not None
               else "not recorded",
               short_date(str(r.get("created_at") or "")[:10]) if r.get("created_at")
               else "—"] for r in active]
    lines = []
    if not active:
        lines.append(f"Book {book} holds no active crypto paper decision.")
    if drafts:
        lines.append(f"{len(drafts)} crypto draft{'s' if len(drafts) != 1 else ''} "
                     f"in Book {book} {'await' if len(drafts) != 1 else 'awaits'} "
                     f"the operator.")
    if note:
        lines.append(note[0].upper() + note[1:] + ".")
    return {"tables": [{"columns": ["Instrument", "Direction", "Notional (paper)",
                                    "Vega (paper)", "Since"], "rows": t_rows}],
            "lines": lines,
            "data": {"active": len(active), "drafts": len(drafts)},
            "footnote": f"Book {book}'s paper decisions from the register, opened "
                        f"read-only. Paper only: no order path exists."}


# ---------------------------------------------------------------------------
# 1. The read
# ---------------------------------------------------------------------------
READ_FRAME = (
    "\n\nTHIS IS THE DIGITAL ASSETS ADDENDUM'S READ: ONE PARAGRAPH, at most "
    "{words} words, on the crypto week. Use ONLY the figures in `page`, each "
    "exactly as it is printed there, at most {figs} of them. Lead with the "
    "weekly bars of BTC, ETH, SOL and ZEC read against the daily and 30-day bars; "
    "then what the other sections add. A cell reading \"{awaiting}\" is not yet "
    "measured: say what is not measured, never estimate it. The attention and "
    "incident tables are posts' own claims, not facts. No recommendation, no "
    "cause: things that happened together are joined with \"alongside\". Plain "
    "prose, no markdown, no list.")


def read_payload(ed: dict) -> dict:
    """The page's figures, as printed: every table of every section but the read."""
    page = []
    for s in ed["sections"]:
        if s["id"] == "read":
            continue
        for t in s.get("tables") or []:
            if t.get("rows"):
                page.append({"section": s["title"], "table": t.get("title") or "",
                             "columns": t["columns"], "rows": t["rows"]})
        for ln in s.get("lines") or []:
            page.append({"section": s["title"], "line": ln})
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    return {"week": ed["crypto_week"], "page": page,
            "coins": (tape.get("data") or {}).get("coins") or []}


def write_read(ed: dict, cfg: dict, *, client=None, model: Optional[str] = None
               ) -> dict:
    """The read, through the existing narrative step and its audits; never
    raises. Withheld (with its reason) rather than published unaudited."""
    from . import narrative as base, readability, stack_prose   # noqa: PLC0415
    b = cfg.get("budget") or {}
    words, figs = int(b.get("read_words") or 120), int(b.get("read_figures") or 6)
    system = stack_prose.stack_system_prompt(base) + READ_FRAME.format(
        words=words, figs=figs, awaiting=cfg.get("awaiting") or "awaiting Tranche A")
    payload = read_payload(ed)
    try:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        style = bars_mod.load_config()
    except Exception:                                           # noqa: BLE001
        style = {}
    try:
        r = base.generate(payload, model=model, client=client, system_prompt=system,
                          max_chars=stack_prose.runaway(words * 9), one_paragraph=True,
                          citable_ids=[])
    except Exception as exc:                                    # noqa: BLE001
        return {"state": "fault", "published": False,
                "reason": f"FAULT {type(exc).__name__}: {exc}"}
    if not r.published:
        return {"state": r.state, "published": False,
                "reason": r.withheld_note() or r.reason,
                "rejected_text": getattr(r, "rejected_text", None)}
    text = r.text
    faults = (stack_prose.style_faults(text, style) + stack_prose.id_faults(text)
              + stack_prose.excess_faults(text) + readability.stance_faults(text)
              + stack_prose.figure_faults(text, figs))
    # D19/D20 (24 Oct 2026): a read over its 120 words prints in full (the
    # page's foot line covers the target); it is no longer withheld for length.
    # THE FLAG-WORD AUDIT (Phase 2): the page prints one flag, item 49's mNAV,
    # and only when it holds; a read may name a flag only when the page prints it.
    flag_on = any(c.get("flag") for s in ed["sections"]
                  for c in (s.get("data") or {}).get("cells") or [])
    if re.search(r"\bflag", text, re.I) and not flag_on:
        faults.append("the read names a flag the page does not print")
    if faults:
        return {"state": "audit", "published": False,
                "reason": "withheld: " + "; ".join(faults[:4]), "rejected_text": text}
    return {"state": "published", "published": True, "text": text, "model": r.model}


# ---------------------------------------------------------------------------
# The edition
# ---------------------------------------------------------------------------
def page_words(ed: dict) -> int:
    """Every word the page prints: tables, lines, the read and footnotes."""
    n = 0
    for s in ed["sections"]:
        for t in s.get("tables") or []:
            n += sum(len(str(c).split()) for c in t.get("columns") or [])
            n += sum(len(str(c).split()) for r in t.get("rows") or [] for c in r)
        for x in (s.get("lines") or []) + (s.get("paragraphs") or []):
            n += len(str(x).split())
        n += len(str(s.get("footnote") or "").split())
    n += len(str(ed.get("appendix_line") or "").split())
    return n


def reading_minutes(ed: dict) -> int:
    from . import readability as rd                             # noqa: PLC0415
    return max(1, math.ceil(page_words(ed) / rd.WORDS_PER_MINUTE
                            + int(ed.get("chart_count") or 0) * rd.SECONDS_PER_CHART
                            / 60.0))


def enforce_budget(ed: dict) -> None:
    """THE TARGETS (D19/D20, 24 Oct 2026; the 52-line cap and the row trim are
    retired): the page's words and minutes counted, and over the reading target
    one foot line; nothing is trimmed, dropped or withheld for length."""
    b = ed.get("budget") or {}
    ed["words"] = page_words(ed)
    ed["minutes"] = reading_minutes(ed)
    ed["over_budget"] = ed["words"] > int(b.get("words") or 1500)
    t = int(b.get("reading_minutes") or 7)
    ed["target_line"] = (f"This page runs about {ed['minutes']} minutes against a "
                         f"{t}-minute target." if ed["minutes"] > t else None)


def appendix_line(ed: dict) -> str:
    """One dated line for the paper's dated appendix, from the page's figures:
    a draft for Ari's accept-all, never the model's."""
    sat = ed["crypto_week"][1]
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    coins = (tape.get("data") or {}).get("coins") or []
    parts = [f"{c['coin']} {fmt_price(c['close'])} ({fmt_pct(c.get('week_pct'))} on the "
             f"week)" for c in coins]
    flows = next(s for s in ed["sections"] if s["id"] == "flows")
    stab = next((c for c in (flows.get("data") or {}).get("cells") or []
                 if c.get("key") == "llama.stable_total" and c.get("value") is not None),
                None)
    ahead = next(s for s in ed["sections"] if s["id"] == "ahead")
    evs = (ahead.get("data") or {}).get("events") or []
    nxt = evs[0] if evs else None
    line = f"**Week to {short_date(sat)} {sat[:4]}.** " + (
        "; ".join(parts) if parts else "no stored closes") + "."
    if stab:
        line += f" Stablecoin supply {stab['text']} on the week."
    if nxt:
        line += (f" Next dated event: {nxt['body']}, {nxt['event']}, "
                 f"{short_date(nxt['date'])}"
                 + (f" ({nxt['marker']})" if nxt.get("marker") else "") + ".")
    return line


def build(ending: str, *, as_of: Optional[str] = None, db_path: Optional[str] = None,
          register: Optional[Path] = None, inbox: Optional[Path] = None,
          chain_base: Optional[Path] = None, events_db: Optional[str] = None,
          cfg: Optional[dict] = None, calendar: Optional[dict] = None,
          narrative: bool = True, client=None, model: Optional[str] = None,
          run_id: Optional[str] = None) -> dict:
    """The edition for the Weekly of `ending` (its Friday), as of the cutoff."""
    from altdata import observations, session                    # noqa: PLC0415
    cfg = cfg or config()
    cal = calendar if calendar is not None else load_calendar(cfg=cfg)
    sun, sat = crypto_week(ending)
    if as_of is None:
        from daily_cascade import weekly_payload                 # noqa: PLC0415
        as_of = weekly_payload.scheduled_run_utc(ending)
    cutoff = as_of
    secs: dict[str, dict] = {}
    with observations.ObservationStore(db_path) as st:
        secs["tape"] = tape_section(st, cutoff, sat, cfg)
        secs["flows"] = plain_section(
            st, cutoff, sat, cfg.get("flows") or [], cfg,
            "ETF totals are Farside's (CD-4); the stablecoin supply is DefiLlama's "
            "(llama.stable_total); treasury holdings are BitcoinTreasuries.com's "
            "(treasuries.bitbo.io).")
        wib = who_is_buying(st, cutoff, cfg)
        secs["flows"]["tables"].append(wib["table"])
        secs["flows"]["data"]["who_is_buying"] = wib["data"]
        secs["mechanics"] = mechanics_section(st, cutoff, sat, cfg, chain_base)
        secs["onchain"] = plain_section(
            st, cutoff, sat, cfg.get("onchain") or [], cfg,
            "SR-29's share is BGeometrics' (bitcoin-data.com), read with the "
            "operator's free key; until the key is in .env it prints not tracked "
            "(CD-12). The froth gauge is unscored until its gate (not before "
            "January 2027).")
        secs["attention"] = attention_section(st, cutoff, sun, sat, cfg, inbox)
        # Batch 15 items 77 and 78 (b56), in the incidents section's BODY since
        # D19/D20 (24 Oct 2026; the 52-line cap that held them in its footnote
        # is retired): each with its full read and its table.
        from daily_cascade import batch15_b2_block               # noqa: PLC0415
        b15 = batch15_b2_block.incidents_body(st, cutoff)
    first = cutoff[:10]
    last = _plus(first, int((cfg.get("ahead") or {}).get("window_days") or 45))
    secs["incidents"] = incidents_section(cutoff, sun, sat, cfg,
                                          calendar_window(cal, first, last),
                                          inbox)
    secs["incidents"]["tables"] += b15["tables"]
    secs["incidents"]["lines"] += b15["lines"]
    secs["incidents"]["data"]["items_77_78"] = b15["data"]
    secs["ahead"] = ahead_section(cutoff, cfg, cal, events_db)
    secs["book"] = book_section(cfg, register)
    secs["read"] = {"tables": [], "lines": [], "paragraphs": [], "data": {},
                    "footnote": "One paragraph by the narrative step, from this page's "
                                "figures only, under its numeral, style and figure "
                                "audits."}
    ed = {"title": cfg.get("title") or "Digital Assets — the week",
          "week_ending": ending, "crypto_week": [sun, sat], "as_of": cutoff,
          "run_id": run_id or session.new_run_id("weekly_digital"),
          "config_version": cfg.get("version"), "budget": cfg.get("budget") or {},
          "chart_count": 0,
          "sections": [{"id": k, "title": t, **secs[k]} for k, t in SECTIONS]}
    ed["appendix_line"] = appendix_line(ed)
    read = next(s for s in ed["sections"] if s["id"] == "read")
    if narrative:
        res = write_read(ed, cfg, client=client, model=model)
    else:
        res = {"state": "skipped", "published": False, "reason": "--no-narrative"}
    ed["prose"] = {k: res.get(k) for k in ("state", "published", "reason", "model",
                                           "rejected_text")}
    if res.get("published"):
        read["paragraphs"] = [res["text"]]
    else:
        read["lines"] = [f"The read is withheld: {res.get('reason')}."
                         if narrative else "The read was not written (no narrative "
                                           "on this run)."]
    enforce_budget(ed)
    return ed


# ---------------------------------------------------------------------------
# Render: one page, phone-readable, every style inline (Gmail strips sheets)
# ---------------------------------------------------------------------------
def render(ed: dict, archive_path: Optional[str] = None) -> str:
    from . import readability as rd, stack_render as sr          # noqa: PLC0415
    esc = sr.esc
    sun, sat = ed["crypto_week"]
    head = sr.page_header(f"{ed['title']} to {rd.prose_date(sat)}",
                          rd.stamp_et(ed.get("as_of")), int(ed.get("minutes") or 1),
                          wrap=True,
                          extra_html=(" &middot; the addendum to the Weekly of "
                                      f"{esc(rd.prose_date(ed['week_ending']))}"))
    out = [head]
    for n, s in enumerate(ed["sections"], start=1):
        out.append(f'<h2 style="{sr.H2}">{n}. {esc(s["title"])}</h2>')
        for p in s.get("paragraphs") or []:
            out.append(f'<p style="{sr.PARA}">{esc(p)}</p>')
        for t in s.get("tables") or []:
            if t.get("title") and t.get("rows"):
                out.append(f'<p style="{sr.H3}">{esc(t["title"])}</p>')
            out.append(sr._table(t, wrap=True))
        if s.get("lines"):
            out.append(sr.lines_table(s["lines"], "Notes", wrap=True))
        if s.get("footnote"):
            out.append(f'<p style="{sr.FOOT}">{esc(s["footnote"])}</p>')
    if ed.get("appendix_line"):
        out.append(f'<h2 style="{sr.H2}">For the Digital Assets paper</h2>'
                   f'<p style="{sr.PARA}">{esc(ed["appendix_line"].replace("**", ""))}'
                   f'</p><p style="{sr.FOOT}">One dated line for the paper\'s dated '
                   f'appendix, written by code from this page: a draft for Ari\'s '
                   f'accept-all.</p>')
    meta = (f"Addendum v{esc(ed.get('config_version'))} &middot; "
            f"{esc(rd.plural(int(ed.get('words') or 0), 'word'))} against a "
            f"{esc(str((ed.get('budget') or {}).get('words')))}-word target &middot; "
            f"{esc(rd.plural(int(ed.get('chart_count') or 0), 'chart'))} &middot; "
            f"as-of cutoff {esc(rd.stamp_et(ed.get('as_of')))} &middot; run "
            f"{esc(ed.get('run_id') or 'n/a')}")
    foot = ([esc(ed["target_line"])] if ed.get("target_line") else []) + [
        meta, "Report only: nothing on this page has decision rights. Paper only."]
    if archive_path:
        foot.append(f"Archived to {esc(archive_path)}.")
    out.append('<div style="margin:24px 0 0 0;padding-top:8px;border-top:1px solid '
               '#d5dde5">' + "".join(f'<p style="{sr.FOOT}">{x}</p>' for x in foot)
               + "</div>")
    return (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>'
            f'{esc(ed["title"])} to {esc(sat)}</title></head><body style="margin:0">'
            f'<div style="{sr.WRAP}">' + "".join(out) + "</div></body></html>")


def appendix_md(ed: dict) -> str:
    return (f"<!-- Draft for Ari's accept-all: one dated line for the Digital Assets "
            f"paper's dated appendix ({(config().get('appendix') or {}).get('heading')})."
            f" Written by code from the addendum of {ed['week_ending']}; never the "
            f"model's. -->\n- {ed['appendix_line']}\n")


# ---------------------------------------------------------------------------
# The Weekly's side
# ---------------------------------------------------------------------------
def link_line(addendum: Optional[dict], mode: str = "email") -> str:
    """THE WEEKLY'S ONE LINE (Batch 8 item 51): where the addendum is. Empty when
    the run carries no addendum."""
    if not addendum:
        return ""
    if addendum.get("state") != "built":
        return (f"Digital Assets addendum: not built this week "
                f"({addendum.get('reason') or 'see the run log'}).")
    where = ("attached to this message" if mode == "email" else
             "beside this edition")
    return (f"Digital Assets addendum, about {addendum.get('minutes')} minutes: "
            f"{addendum.get('attached') or addendum['name']}, {where}.")


def _pdf(html: str) -> tuple[Optional[bytes], str]:
    from . import readability                                    # noqa: PLC0415
    return readability.pdf_bytes(html, [])


def produce(p: dict, *, archive_dir: Optional[str], db_path: Optional[str] = None,
            narrative: bool = True, client=None, model: Optional[str] = None,
            pdf_renderer=None, **kw) -> dict:
    """Build, render and archive the addendum for the Weekly payload `p`; record
    it on `p["addendum"]` for the Weekly's link line. Never raises: a failed
    addendum costs the addendum, never the Weekly.

    THE PAGE TRAVELS AS A SECOND PDF on the Weekly's own email (ruling (e) of 17
    Oct 2026), rendered by the Weekly's own PDF step (readability.pdf_bytes) and
    archived beside the HTML. A PDF that cannot be built leaves the HTML attached
    in its place, and the run says why. `pdf_renderer` is injectable so a gate
    never renders one."""
    from . import deliver                                        # noqa: PLC0415
    ending = p.get("week_ending")
    try:
        cfg = kw.get("cfg") or config()
        first = str(cfg.get("first_edition_week_ending") or "")
        # BEFORE THE FIRST EDITION, A DRY RUN: archived under dryrun/, never
        # attached, no line in the Weekly.
        dry = bool(first) and str(ending) < first
        if dry:
            archive_dir = str(Path(archive_dir or deliver.ARCHIVE_DIR) / "dryrun")
        ed = build(ending, as_of=p.get("as_of"), db_path=db_path, narrative=narrative,
                   client=client, model=model, run_id=p.get("run_id"), **kw)
        name = page_name(ending)
        html = render(ed, deliver.archive_path(name, archive_dir))
        path = deliver.archive(html, name, archive_dir)
        pdf, pdf_detail = (pdf_renderer or _pdf)(html)
        if pdf:
            deliver.archive_bytes(pdf, PDF_NAME.format(ending=ending), archive_dir)
        deliver.archive(json.dumps(ed, indent=2, default=str, sort_keys=True),
                        EDITION_NAME.format(ending=ending), archive_dir)
        deliver.archive(appendix_md(ed), APPENDIX_NAME.format(ending=ending),
                        archive_dir)
    except Exception as exc:                                    # noqa: BLE001
        log.warning("digital addendum failed", exc_info=True)
        p["addendum"] = {"state": "failed", "reason": f"{type(exc).__name__}: {exc}"}
        return {"state": "failed", "reason": p["addendum"]["reason"]}
    if dry:
        return {"state": "dry_run", "edition": ed, "html": html, "name": name,
                "archive_path": path, "pdf": pdf, "pdf_detail": pdf_detail,
                "reason": f"a dry run before the first edition (the Weekly of "
                          f"{first}): archived to {path}, not attached"}
    attached = PDF_NAME.format(ending=ending) if pdf else name
    p["addendum"] = {"state": "built", "name": name, "attached": attached,
                     "minutes": ed["minutes"], "words": ed["words"],
                     "archive_path": path, "read": ed["prose"].get("state"),
                     "pdf": "built" if pdf else f"NOT built -- {pdf_detail}"}
    return {"state": "built", "edition": ed, "html": html, "name": name,
            "archive_path": path, "pdf": pdf, "pdf_detail": pdf_detail,
            "pdf_name": PDF_NAME.format(ending=ending)}


def attachment(out: Optional[dict]) -> list[tuple[str, Any, str]]:
    """The addendum as an attachment of the Weekly's message: the second PDF
    (ruling (e) of 17 Oct 2026), or the HTML where no PDF could be built; none
    when the addendum was not built."""
    if not out or out.get("state") != "built":
        return []
    if out.get("pdf"):
        return [(out["pdf_name"], out["pdf"], "pdf")]
    return [(out["name"], out["html"], "html")]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="The Digital Assets addendum.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="build and render one week's addendum to a "
                                      "directory (default <reports>/dryrun); "
                                      "sends nothing")
    r.add_argument("--week-ending", required=True, help="the Weekly's Friday")
    r.add_argument("--as-of", default=None)
    r.add_argument("--no-narrative", action="store_true")
    r.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from . import deliver                                        # noqa: PLC0415
    out_dir = args.out or str(Path(deliver.ARCHIVE_DIR) / "dryrun")
    p = {"week_ending": args.week_ending, "as_of": args.as_of}
    res = produce(p, archive_dir=out_dir, narrative=not args.no_narrative)
    if res["state"] != "built":
        print(f"addendum FAILED: {res['reason']}")
        return 1
    ed = res["edition"]
    print(f"digital addendum -- week to {ed['crypto_week'][1]}")
    print(f"  words      : {ed['words']} (target {ed['budget'].get('words')}), "
          f"about {ed['minutes']} minutes, {ed['chart_count']} charts"
          + (f" -- {ed['target_line']}" if ed.get("target_line") else ""))
    print(f"  the read   : {ed['prose'].get('state')} "
          f"{ed['prose'].get('reason') or ''}")
    for s in ed["sections"]:
        print(f"    {s['id']:<10} {sum(len(t.get('rows') or []) for t in s.get('tables') or [])}"
              f" rows")
    print(f"  archive    : {res['archive_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())

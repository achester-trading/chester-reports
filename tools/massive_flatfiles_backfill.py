#!/usr/bin/env python3
"""
Two years of per-name option readings from Massive's options day bars (signal-
triage Batch 11, decision D4, ruled 19 Oct 2026). RUN BY ARI ON THE BOX.

    .venv/bin/python tools/massive_flatfiles_backfill.py --dry-run          # the plan
    .venv/bin/python tools/massive_flatfiles_backfill.py --max-days 25      # one capped run
    .venv/bin/python tools/massive_flatfiles_backfill.py --status

WHAT D4'S PROBE FOUND (Massive's public documentation, read 19 Oct 2026):
  - the options day-aggregates flat file is "Included in select Options plans";
    Options Starter: recency "End-of-day", history "2 years"; records "date back
    to June 2, 2014"; "Updated at 11a ET to include the previous day";
  - its columns: ticker, volume, open, close, high, low, window_start,
    transactions -- no open interest; Massive "returns options open interest only
    on its snapshots, as the latest daily figure", so no OI history exists in any
    form we pay for;
  - access: S3-compatible, endpoint https://files.massive.com, bucket flatfiles,
    prefix us_options_opra, with an S3 Access Key and Secret Key from the
    dashboard; rclone is among the supported clients.

WHAT IT DOES. For each session in the last two years, oldest first, one file at a
time: streams us_options_opra/day_aggs_v1/YYYY/MM/YYYY-MM-DD.csv.gz through rclone's
S3 backend (configured from the environment, never in rclone.conf), keeps only the
17 captured names' contracts, and writes per name and session:
  chain.put_share_volume   puts' share of the day's volume, percent
  chain.iv30_atm           the 30-day ATM IV (SPY's method)
  chain.skew_25d_put       the front month's 25-delta put skew
  chain.rr_25d             the front month's 25-delta risk reversal
under the source `chain_capture:flatfiles`, every IV figure "from last-trade
closes, not mids" (the day bar's close is the solver's price; bid and ask are
absent). availability_kind "reconstructed": a file is published at 11:00 ET the
next day, which is each row's available_at. A rank reads these rows only where
altdata/flatfile_history.py admits them.

RESUMABLE AND CAPPED. Progress is ~/chester-data/flatfiles/backfill_state.json (the
sessions done, each with its row count); a run takes at most --max-days sessions
(default 25) and stops cleanly. A session whose file is absent is recorded as such
and not retried. --dry-run checks the credentials and the bucket with one listing
and prints the plan; it downloads no day file and writes nothing.

CREDENTIALS, by name (Ari's, in .env): MASSIVE_FLATFILES_ACCESS_KEY_ID and
MASSIVE_FLATFILES_SECRET_ACCESS_KEY. No new dependency: rclone is already on the
box for the backup (scripts/rclone_sync.sh).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

REMOTE = "massiveff"
BUCKET_PATH = "flatfiles/us_options_opra/day_aggs_v1"
STATE = Path(os.environ.get("CHESTER_DATA_DIR") or Path.home() / "chester-data") \
    / "flatfiles" / "backfill_state.json"
TICKER = re.compile(r"^O:([A-Z.]+?)(\d{6})([CP])(\d{8})$")
HISTORY_DAYS = 730


def rclone_env() -> dict:
    """rclone's S3 backend from the environment (never written to rclone.conf)."""
    # The repo's one secrets reader: .env by name (an ssh shell reads no .env).
    from altdata import secrets                                 # noqa: PLC0415
    key = secrets.get("MASSIVE_FLATFILES_ACCESS_KEY_ID")
    sec = secrets.get("MASSIVE_FLATFILES_SECRET_ACCESS_KEY")
    if not key or not sec:
        raise SystemExit("MASSIVE_FLATFILES_ACCESS_KEY_ID and MASSIVE_FLATFILES_SECRET_"
                         "ACCESS_KEY must be set (in .env, by name)")
    p = f"RCLONE_CONFIG_{REMOTE.upper()}_"
    return {**os.environ, p + "TYPE": "s3", p + "PROVIDER": "Other",
            p + "ENDPOINT": "https://files.massive.com", p + "ACCESS_KEY_ID": key,
            p + "SECRET_ACCESS_KEY": sec}


def parse_ticker(t: str) -> Optional[dict]:
    m = TICKER.match(t or "")
    if not m:
        return None
    root, ymd, right, k = m.groups()
    exp = f"20{ymd[:2]}-{ymd[2:4]}-{ymd[4:6]}"
    return {"root": root, "expiry": exp, "right": right, "strike": int(k) / 1000.0}


def rows_for(lines: Iterable[dict], names: set[str], day: str,
             spots: dict[str, float]) -> dict[str, list[dict]]:
    """The day file's rows, kept for the names only, in the chain shape the
    solver reads (the close as the last price; no bid, no ask)."""
    out: dict[str, list[dict]] = {}
    d0 = dt.date.fromisoformat(day)
    for r in lines:
        t = parse_ticker(r.get("ticker", ""))
        if not t or t["root"] not in names or t["expiry"] < day:
            continue
        try:
            close, vol = float(r["close"]), float(r["volume"])
        except (TypeError, ValueError, KeyError):
            continue
        out.setdefault(t["root"], []).append({
            "expiry": t["expiry"], "strike": t["strike"], "right": t["right"],
            "dte": (dt.date.fromisoformat(t["expiry"]) - d0).days,
            "bid": None, "ask": None, "last_price": close, "volume": vol,
            "open_interest": None, "spot": spots.get(t["root"]),
            "last_trade_date": day, "fetched_at": f"{day}T21:00:00+00:00"})
    return out


def readings(rows: list[dict]) -> dict:
    """Puts' share of volume, and the three IV figures from the day bars' closes."""
    from altdata import chain_metrics as cm                     # noqa: PLC0415
    pv = sum(r["volume"] for r in rows if r["right"] == "P")
    tv = sum(r["volume"] for r in rows)
    out = {"chain.put_share_volume": 100.0 * pv / tv if tv else None}
    if rows and rows[0].get("spot"):
        try:
            iv = cm.atm_iv_30d(rows)
            out["chain.iv30_atm"] = iv["iv_pct"] if iv else None
            f = cm.front_month_iv(rows)
            out["chain.skew_25d_put"] = (f or {}).get("skew_25d_put")
            out["chain.rr_25d"] = (f or {}).get("rr_25d")
        except Exception:                                       # noqa: BLE001
            pass
    return out


def store_rows(day: str, by_name: dict[str, list[dict]]) -> list[dict]:
    from altdata import flatfile_history as ffh, session        # noqa: PLC0415
    nxt = dt.date.fromisoformat(day) + dt.timedelta(days=1)
    while not session.is_trading_session(nxt):
        nxt += dt.timedelta(days=1)
    avail = f"{nxt.isoformat()}T15:00:00+00:00"                 # 11:00 ET the next day
    out = []
    for sym, rows in by_name.items():
        for key, v in readings(rows).items():
            if v is not None:
                out.append({"registry_key": key, "instrument": sym, "observed_at": day,
                            "available_at": avail, "value": round(float(v), 3),
                            "source": ffh.SOURCE, "availability_kind": "reconstructed"})
    return out


def sessions(today: dt.date) -> list[str]:
    from altdata import session                                 # noqa: PLC0415
    d, out = today - dt.timedelta(days=HISTORY_DAYS), []
    while d < today:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def load_state(path: Path = STATE) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"done": {}}


def save_state(state: dict, path: Path = STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def exists(day: str, env: dict) -> bool:
    path = f"{REMOTE}:{BUCKET_PATH}/{day[:4]}/{day[5:7]}/"
    p = subprocess.run(["rclone", "lsf", path, "--include", f"{day}.csv.gz"], env=env,
                       capture_output=True, text=True, timeout=120)
    return p.returncode == 0 and f"{day}.csv.gz" in p.stdout


def stream_day(day: str, env: dict):
    """(the process, its rows): the day's file streamed through `rclone cat` and
    the gzip reader a line at a time, never held whole (the box has 4 GB)."""
    path = f"{REMOTE}:{BUCKET_PATH}/{day[:4]}/{day[5:7]}/{day}.csv.gz"
    proc = subprocess.Popen(["rclone", "cat", path], env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    rows = csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=proc.stdout),
                                           encoding="utf-8"))
    return proc, rows


def spots_for(st, day: str, names: list[str]) -> dict[str, float]:
    out = {}
    for s in names:
        r = [x for x in st.as_of(f"yfinance.mkt_{s.lower()}", f"{day}T23:59:59+00:00")
             if str(x["observed_at"])[:10] == day and x.get("value_num") is not None]
        if r:
            out[s] = float(r[-1]["value_num"])
    return out


def main(argv=None) -> int:
    from altdata import config as acfg, observations            # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-days", type=int, default=25)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--db")
    a = ap.parse_args(argv)
    state = load_state()
    todo = [d for d in sessions(dt.date.today()) if d not in state["done"]]
    if a.status:
        print(f"{len(state['done'])} sessions done, {len(todo)} to do; state {STATE}")
        return 0
    env = rclone_env()
    names = acfg.chain_universe()
    if a.dry_run:
        ls = subprocess.run(["rclone", "lsf", f"{REMOTE}:{BUCKET_PATH}/{todo[0][:4]}/"],
                            env=env, capture_output=True, text=True, timeout=120) if todo else None
        print(f"credentials and bucket: {'ok' if ls and ls.returncode == 0 else 'FAILED'}"
              f"{'' if not ls or ls.returncode == 0 else ' -- ' + ls.stderr.strip()[:200]}")
        print(f"{len(todo)} sessions to do ({todo[0] if todo else '-'} to "
              f"{todo[-1] if todo else '-'}); a run takes {a.max_days}; names: "
              f"{', '.join(names)}. Nothing downloaded or written.")
        return 0
    with observations.open_writer("tools.massive_flatfiles_backfill", a.db) as st:
        for day in todo[:a.max_days]:
            if not exists(day, env):
                state["done"][day] = {"rows": 0, "note": "no file"}
                save_state(state)
                print(f"{day}: no file")
                continue
            proc, lines = stream_day(day, env)
            try:
                kept = rows_for(lines, set(names), day, spots_for(st, day, names))
            finally:
                proc.stdout.close()
                proc.wait(timeout=300)
            if proc.returncode not in (0, None):
                print(f"{day}: the download failed (rclone {proc.returncode}); not marked done")
                continue
            rows = store_rows(day, kept)
            if rows:
                st.write_many(rows)
            state["done"][day] = {"rows": len(rows)}
            save_state(state)
            print(f"{day}: {len(rows)} rows")
    print(f"{len([d for d in todo[:a.max_days]])} sessions this run; "
          f"{max(len(todo) - a.max_days, 0)} left")
    return 0


if __name__ == "__main__":
    sys.exit(main())

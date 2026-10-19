"""
THE DATA-QUALITY CHECK, READ-ONLY, AFTER EACH PULL. (AUD-3c, 15 Oct 2026; the
data and architecture audit of 14 Oct, recommendation 14.)

    python -m altdata.quality check   [--date D] [--db PATH]   # the day's table
    python -m altdata.quality measure [--to D]   [--db PATH]   # the pairs' tolerances
    python -m altdata.quality record  [--date D] [--db PATH]   # after a pull: mark
    python -m altdata.quality outliers [--date D] [--db PATH]  # "n outliers"

THE MARK (audit-leftovers-2, 17 Oct 2026; the audit's item 14). `record` runs the
check and writes each flag as one row in data_quality_flags -- after the EOD
pass's price pull and the 06:45 FRED pull -- and lists them in the run log; the
freshness check and the heartbeat print the count, "n outliers". A flag is
MARKED, never corrected: no value is altered, dropped or withheld. `check` and
`outliers` stay read-only. The multiple and the window are listed per family
(config outliers.families).

Config: config/data_quality.yaml (every number session-set, each with its reason).

A bad print -- a decimal slip, a stale close, a vendor's unit change -- entered the
store and the reports as if it were real: nothing between the pull and the page
compared a print with the key's own history or with a second source. This module
does both, and only reads.

  1. OUTLIERS. Every price (the closes block) and every FRED series with a new
     observation on the date: its change against the standard deviation of its
     own last 60 changes, flagged past 6 of them. A change is measured by the
     key's own delta rule through the move screen's unit_rule -- log for a price,
     a difference for a yield, a rate or a spread, and the move screen's pinned
     log basis for the volatility indexes and SKEW (config/move_screen.yaml). A
     key with fewer than 60 changes, or none of any size, is skipped and named.
  2. REVISIONS. A FRED value that differs from the value stored earlier for the
     same observation date, written on the date, is a revision: listed with its
     old and new values, never flagged as an outlier.
  3. CROSS-SOURCE PAIRS. ^TNX against DGS10, ^TYX against DGS30, ^VIX against
     VIXCLS, on the latest date both hold: a gap beyond the pair's measured
     tolerance flags. A pair with no measured tolerance prints "not measured".

RULED 15 OCT 2026:
  BACKFILL. A row whose source is a declared backfill string (fred:backfill,
     the FRED-history writer's) is labelled "backfill": never a revision, and
     never a new print the outlier rule judges.
  STEP SERIES. A policy rate (config `steps`) moves in steps, so it does not take
     the standard-deviation rule: a change on the date prints as an
     informational "step" line and never flags.

"NEW ON THE DATE" is an observation whose first vintage became available on that
date in Eastern time (a row with no available_at: its observed_at). A later
vintage of an observation already stored is a revision, never a new print.

READ-ONLY. The store is opened with SQLite's mode=ro; nothing here writes, and
no value is ever changed. A flag is a prompt to look: the close prints the day's
flags in its Warnings table (close_warnings) and never blocks, withholds or
alters a number. Exit codes: 0 clean, 1 flags, 2 the store cannot be opened.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import sqlite3
import statistics
import sys
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "data_quality.yaml"
ET = ZoneInfo("America/New_York")


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# The store, read-only
# ---------------------------------------------------------------------------
def default_db() -> str:
    from . import observations                                  # noqa: PLC0415
    return observations.DEFAULT_DB


def open_ro(db: str) -> sqlite3.Connection:
    """The store, read-only. Raises when it does not exist or is no database; a
    missing file is never created."""
    p = Path(db)
    if not p.is_file():
        raise FileNotFoundError(f"no store at {db}")
    conn = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True)
    conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    return conn


def et_date(ts: Any) -> Optional[str]:
    """The Eastern date of an ISO instant, or None."""
    if not ts:
        return None
    try:
        t = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return str(ts)[:10]
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(ET).date().isoformat()


def vintages(conn: sqlite3.Connection, key: str, day: str, limit: int = 2000
             ) -> dict[str, list[tuple[str, float, str]]]:
    """{observed date: [(available Eastern date, value, source), ...] oldest
    vintage first}, every vintage available on or before `day`."""
    out: dict[str, list[tuple[str, float, str]]] = {}
    for obs, avail, v, src in conn.execute(
            "SELECT observed_at, available_at, value_num, source FROM observations "
            "WHERE registry_key = ? AND instrument IS NULL AND value_num IS NOT NULL "
            "AND observed_at <= ? ORDER BY observed_at DESC, available_at DESC "
            "LIMIT ?", (key, day + "T99", limit)):
        if v is None or (isinstance(v, float) and not math.isfinite(v)):
            continue
        ad = et_date(avail) or str(obs)[:10]
        if ad > day:
            continue
        out.setdefault(str(obs)[:10], []).append((ad, float(v), str(src or "")))
    for d in out:
        out[d].sort()
    return out


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------
def change(a: float, b: float, basis: str) -> Optional[float]:
    """b against a, by the move screen's own arithmetic."""
    from . import move_screen                                   # noqa: PLC0415
    return move_screen.change(a, b, basis)


def basis_of(key: str) -> str:
    """"log" or "diff": the key's delta rule, with the move screen's pins."""
    from . import move_screen                                   # noqa: PLC0415
    return move_screen.unit_rule(key)


def checked_keys(cfg: dict) -> list[str]:
    """Every key in the configured blocks: the closes and every FRED block."""
    from . import derived                                       # noqa: PLC0415
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    by: dict = {}
    derived.resolve_registry(reg, by)
    keys: list[str] = []
    for b in (cfg.get("outliers") or {}).get("blocks") or []:
        keys += [k for k in by.get(b) or [] if k not in keys]
    return keys


def backfill_sources(cfg: dict) -> set:
    return set(cfg.get("backfill_sources") or [])


def step_keys(cfg: dict) -> set:
    return {str(s["key"]) for s in ((cfg.get("steps") or {}).get("series") or [])}


def family_of(key: str) -> Optional[str]:
    """The key's metric-lens family (price, rate, release, ...), or None."""
    from . import derived                                       # noqa: PLC0415
    return (derived._load_registry().get(key) or {}).get("family")  # noqa: SLF001


def params_for(key: str, cfg: dict) -> tuple[float, int]:
    """(sigma, window) for the key: its family's line under outliers.families,
    else the defaults (audit-leftovers-2: the multiple and the window listed per
    family)."""
    o = cfg.get("outliers") or {}
    sigma, window = float(o.get("sigma") or 6), int(o.get("window") or 60)
    fam = (o.get("families") or {}).get(family_of(key) or "") or {}
    return float(fam.get("sigma", sigma)), int(fam.get("window", window))


def outlier_of(key: str, v: dict, day: str, cfg: dict) -> dict:
    """{"state": "flag" | "clean" | "skipped" | "not new" | "backfill", ...} for
    one key."""
    sigma, window = params_for(key, cfg)
    if not v:
        return {"state": "not new"}
    newest = max(v)
    first_avail = v[newest][0][0]
    if first_avail != day:
        return {"state": "not new"}
    if v[newest][0][2] in backfill_sources(cfg):
        # The history writer's row, not a new print from the day's pull.
        return {"state": "backfill"}
    dates = sorted(v)
    # Each observation at its first vintage: what the series printed, in order.
    vals = [v[d][0][1] for d in dates]
    basis = basis_of(key)
    ch = [change(a, b, basis) for a, b in zip(vals[:-1], vals[1:])]
    if len(ch) < window + 1 or any(c is None for c in ch[-(window + 1):]):
        return {"state": "skipped", "why": f"{len(vals)} observations; "
                f"{window + 1} needed for {window} changes and the day's"}
    hist, last = ch[-(window + 1):-1], ch[-1]
    sd = statistics.stdev(hist)
    if sd == 0 or not math.isfinite(sd):
        return {"state": "skipped", "why": f"no variation in its last {window} changes"}
    k = abs(last) / sd
    return {"state": "flag" if k > sigma else "clean", "key": key, "basis": basis,
            "observed_at": newest, "level": vals[-1], "prior": vals[-2],
            "prior_at": dates[-2], "change": last, "sd": sd, "sigmas": round(k, 2),
            "sigma": sigma, "window": window}


def revisions_of(key: str, v: dict, day: str,
                 backfill: frozenset = frozenset()) -> tuple[list[dict], list[dict]]:
    """(revisions, backfill): every vintage written on `day` whose value differs
    from the vintage before it for the same observation date. One whose source is
    a backfill string is labelled backfill (ruled 15 Oct 2026), never a
    revision."""
    revs, bf = [], []
    for d, vs in sorted(v.items()):
        for (a0, x0, _s0), (a1, x1, s1) in zip(vs[:-1], vs[1:]):
            if a1 == day and abs(x1 - x0) > 1e-12:
                row = {"key": key, "observed_at": d, "old": x0, "new": x1,
                       "old_available": a0, "new_available": a1, "source": s1}
                (bf if s1 in backfill else revs).append(row)
    return revs, bf


def backfill_firsts(key: str, v: dict, day: str, backfill: frozenset) -> int:
    """How many observations the backfill wrote for the first time on `day`."""
    return sum(1 for vs in v.values() if vs[0][0] == day and vs[0][2] in backfill)


def step_of(key: str, v: dict, day: str) -> Optional[dict]:
    """A step series' change on the date: informational, never a flag."""
    if not v:
        return None
    newest = max(v)
    if v[newest][0][0] != day:
        return None
    dates = sorted(v)
    if len(dates) < 2:
        return None
    a, b = v[dates[-2]][0][1], v[newest][0][1]
    if abs(b - a) < 1e-12:
        return None
    from . import derived                                       # noqa: PLC0415
    du = derived.delta_unit_for(key)[0]
    return {"key": key, "observed_at": newest, "prior_at": dates[-2], "prior": a,
            "level": b, "change": round((b - a) * (100.0 if du == "bps" else 1.0), 4),
            "unit": "bp" if du == "bps" else du}


def step_line(s: dict) -> str:
    sign = "+" if s["change"] > 0 else "−"
    return (f"Data check (step): {_label(s['key'])} ({s['key']}) {_num(s['level'])} "
            f"from {_num(s['prior'])} on {_short(s['observed_at'])}, a step of "
            f"{sign}{_num(abs(s['change']))} {s['unit']} -- informational, never a "
            f"flag")


def measure_gaps(gaps: list[float], percentile: float, floor: float) -> dict:
    """The tolerance: the `percentile`th percentile of the absolute gaps (linear
    interpolation between order statistics), floored at the quote's precision."""
    g = sorted(abs(x) for x in gaps)
    if not g:
        return {"n": 0, "p99": None, "tolerance": None, "floored": False}
    i = (len(g) - 1) * float(percentile) / 100.0
    lo = int(math.floor(i))
    hi = min(lo + 1, len(g) - 1)
    p = g[lo] + (g[hi] - g[lo]) * (i - lo)
    return {"n": len(g), "p99": p, "tolerance": max(p, float(floor)),
            "floored": p < float(floor), "max": g[-1]}


def _short(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    return f"{d.day} {d:%b}"


def _num(x: float) -> str:
    return f"{x:,.2f}".rstrip("0").rstrip(".") if abs(x) < 1000 else f"{x:,.0f}"


def pair_verdict(pc: dict, a: Optional[float], b: Optional[float], on: Optional[str]
                 ) -> dict:
    """One pair on one date: the gap against the tolerance."""
    base = {"id": pc["id"], "a_label": pc.get("a_label"), "b_label": pc.get("b_label"),
            "unit": pc.get("unit"), "scale": pc.get("scale") or 1, "on": on,
            "a": a, "b": b, "tolerance": pc.get("tolerance"), "flagged": False}
    if a is None or b is None or on is None:
        return dict(base, state="absent", why="no date both hold")
    gap = abs(a - b)
    base["gap"] = gap
    if pc.get("tolerance") is None:
        return dict(base, state="not measured",
                    why=" ".join(str(pc.get("unmeasured_reason") or "").split()))
    flagged = gap > float(pc["tolerance"]) + 1e-12
    return dict(base, state="flag" if flagged else "clean", flagged=flagged)


def pair_line(p: dict) -> str:
    tol = float(p["tolerance"]) * float(p.get("scale") or 1)
    unit = (f"{_num(tol)} bp" if p.get("unit") == "bp"
            else f"{_num(tol)}-{p.get('unit') or 'point'}")
    return (f"Data check: {p['a_label']} {_num(p['a'])} vs {p['b_label']} "
            f"{_num(p['b'])} on {_short(p['on'])}, beyond its {unit} tolerance")


def _label(key: str) -> str:
    from . import move_screen                                   # noqa: PLC0415
    return move_screen.label_of(key)


def flag_line(f: dict) -> str:
    if f.get("kind") == "pair":
        return pair_line(f)
    how = "log change" if f["basis"] == "log" else "change"
    # The key beside the label: two sources of one fact share a label (the VIX
    # is both yfinance.mkt_vix and fred.vix), and the key is what to look up.
    return (f"Data check: {_label(f['key'])} ({f['key']}) {_num(f['level'])} from "
            f"{_num(f['prior'])} on {_short(f['observed_at'])}, a {how} "
            f"{f['sigmas']:.1f} times the standard deviation of its last "
            f"{f['window']} changes")


def check(db: str, day: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """The day's three checks, as data. Raises when the store cannot be opened."""
    from . import session                                       # noqa: PLC0415
    cfg = cfg if cfg is not None else load_config()
    day = (day or session.session_date())[:10]
    conn = open_ro(db)
    try:
        outliers, skipped, revisions, n = [], [], [], 0
        backfill, steps = [], []
        bfs, sks = frozenset(backfill_sources(cfg)), step_keys(cfg)
        for key in checked_keys(cfg):
            v = vintages(conn, key, day)
            if not v:
                continue
            if key.startswith("fred."):
                revs, bf = revisions_of(key, v, day, bfs)
                revisions += revs
                backfill += bf
                firsts = backfill_firsts(key, v, day, bfs)
                if firsts:
                    backfill.append({"key": key, "first_written": firsts})
            if key in sks:
                st = step_of(key, v, day)
                if st and v[st["observed_at"]][0][2] not in bfs:
                    steps.append(st)
                continue
            res = outlier_of(key, v, day, cfg)
            if res["state"] in ("not new", "backfill"):
                continue
            if res["state"] == "skipped":
                skipped.append({"key": key, "why": res["why"]})
                continue
            n += 1
            if res["state"] == "flag":
                outliers.append(res)
        pairs = []
        for pc in (cfg.get("pairs") or {}).get("list") or []:
            va, vb = vintages(conn, pc["a"], day), vintages(conn, pc["b"], day)
            both = sorted(set(va) & set(vb))
            on = both[-1] if both else None
            pairs.append(pair_verdict(pc, va[on][-1][1] if on else None,
                                      vb[on][-1][1] if on else None, on))
    finally:
        conn.close()
    flags = ([dict(f, kind="outlier") for f in
              sorted(outliers, key=lambda f: -f["sigmas"])]
             + [dict(p, kind="pair") for p in pairs if p["flagged"]])
    return {"db": db, "day": day, "config_version": cfg.get("version"),
            "checked": n, "outliers": outliers, "skipped": skipped,
            "revisions": revisions, "backfill": backfill, "steps": steps,
            "pairs": pairs, "flags": flags}


# ---------------------------------------------------------------------------
# The close
# ---------------------------------------------------------------------------
def close_lines(r: dict, cap: int) -> list[str]:
    """At most `cap` flag lines, then a count; nothing on a clean day."""
    fl = r.get("flags") or []
    out = [flag_line(f) for f in fl[:cap]]
    if len(fl) > cap:
        more = len(fl) - cap
        out.append(f"and {more} more data-check flag{'s' if more != 1 else ''} -- "
                   f"python -m altdata.quality check --date {r['day']}")
    return out


def close_warnings(day: str, db: Optional[str] = None,
                   cfg: Optional[dict] = None) -> list[str]:
    """The close's Warnings lines for the day. Read-only, and never raises: a store
    it cannot open, or a check that fails, prints nothing -- the check is a prompt
    to look and must never cost the close its edition."""
    try:
        cfg = cfg if cfg is not None else load_config()
        r = check(db or default_db(), day, cfg)
        return close_lines(r, int(cfg.get("close_lines") or 5))
    except Exception:                                           # noqa: BLE001
        return []


# ---------------------------------------------------------------------------
# The record (audit-leftovers-2, the 14 Oct audit's item 14): after each pull
# ---------------------------------------------------------------------------
# THE MARK IS A ROW, NEVER AN EDIT. `record` runs the same read-only check and
# writes each flag as one row in data_quality_flags, in the store's database but
# not in `observations`: the value stays exactly as stored, and the flag says to
# look at it. The table's own triggers refuse UPDATE and DELETE; a second record
# of the same day writes nothing new (the primary key). The freshness check and
# the heartbeat print the day's count as "n outliers".
FLAGS_TABLE = "data_quality_flags"
# One row per record run, so a clean day (no flag rows) reads "0 outliers"
# rather than "no record yet".
RUNS_TABLE = "data_quality_runs"
FLAGS_SQL = f"""
CREATE TABLE IF NOT EXISTS {FLAGS_TABLE} (
    day          TEXT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('outlier', 'pair')),
    registry_key TEXT NOT NULL,
    reason       TEXT NOT NULL,
    observed_at  TEXT,
    detail       TEXT,
    recorded_at  TEXT NOT NULL,
    PRIMARY KEY (day, kind, registry_key)
);
CREATE TRIGGER IF NOT EXISTS {FLAGS_TABLE}_no_update BEFORE UPDATE ON {FLAGS_TABLE}
BEGIN SELECT RAISE(ABORT, '{FLAGS_TABLE} is append-only'); END;
CREATE TRIGGER IF NOT EXISTS {FLAGS_TABLE}_no_delete BEFORE DELETE ON {FLAGS_TABLE}
BEGIN SELECT RAISE(ABORT, '{FLAGS_TABLE} is append-only'); END;
CREATE TABLE IF NOT EXISTS {RUNS_TABLE} (
    day          TEXT NOT NULL,
    recorded_at  TEXT NOT NULL,
    checked      INTEGER NOT NULL,
    flagged      INTEGER NOT NULL,
    PRIMARY KEY (day, recorded_at)
);
"""


def flag_rows(r: dict, recorded_at: str) -> list[tuple]:
    import json                                                 # noqa: PLC0415
    out = []
    for f in r.get("flags") or []:
        key = f.get("key") if f.get("kind") == "outlier" else f.get("id")
        detail = {k: v for k, v in f.items() if isinstance(v, (int, float, str))}
        out.append((r["day"], f["kind"], str(key), flag_line(f),
                    f.get("observed_at") or f.get("on"),
                    json.dumps(detail, sort_keys=True, default=str), recorded_at))
    return out


def record(db: str, day: Optional[str] = None, cfg: Optional[dict] = None,
           now: Optional[str] = None) -> dict:
    """Check the day (read-only), then write each flag as a row. Returns the
    check's result with `recorded`, the rows new this run."""
    from . import observations, session                         # noqa: PLC0415
    r = check(db, day, cfg)
    rows = flag_rows(r, now or session.utc_iso())
    st = observations.open_writer("quality", db)
    try:
        st.conn.executescript(FLAGS_SQL)
        before = st.conn.total_changes
        st.conn.executemany(
            f"INSERT OR IGNORE INTO {FLAGS_TABLE} (day, kind, registry_key, reason, "
            f"observed_at, detail, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        st.conn.commit()
        r["recorded"] = st.conn.total_changes - before
        st.conn.execute(f"INSERT OR IGNORE INTO {RUNS_TABLE} (day, recorded_at, checked, "
                        f"flagged) VALUES (?, ?, ?, ?)",
                        (r["day"], now or session.utc_iso(), r["checked"], len(rows)))
        st.conn.commit()
    finally:
        st.close()
    return r


def outliers_count(db: str, day: Optional[str] = None) -> Optional[dict]:
    """{"day", "n", "keys"} for `day`, or for the newest recorded day; None when
    nothing has been recorded (or the store cannot be opened)."""
    try:
        conn = open_ro(db)
    except (sqlite3.Error, OSError):
        return None
    try:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                            "name=?", (RUNS_TABLE,)).fetchone():
            return None
        if day is None:
            row = conn.execute(f"SELECT MAX(day) FROM {RUNS_TABLE}").fetchone()
            day = row[0] if row else None
            if not day:
                return None
        keys = [k for (k,) in conn.execute(
            f"SELECT registry_key FROM {FLAGS_TABLE} WHERE day = ? "
            f"ORDER BY kind, registry_key", (day,))]
        return {"day": day, "n": len(keys), "keys": keys}
    finally:
        conn.close()


def outliers_line(c: Optional[dict]) -> str:
    """The freshness check's and the heartbeat's line: "n outliers"."""
    if not c:
        return "data check: no record yet (python -m altdata.quality record)"
    return (f"data check: {c['n']} outlier{'s' if c['n'] != 1 else ''} on {c['day']}"
            + (f" ({', '.join(c['keys'][:5])}{', ...' if c['n'] > 5 else ''})"
               if c["n"] else ""))


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------
def report(r: dict) -> str:
    line = "=" * 74
    out = [line, f"The data-quality check -- {r['db']} (read-only), {r['day']}", line,
           f"  keys with a new print checked : {r['checked']}",
           f"  1. outliers (past {int(load_config()['outliers']['sigma'])} sigma of "
           f"the last {int(load_config()['outliers']['window'])} changes): "
           f"{len(r['outliers'])}"]
    for f in r["outliers"]:
        out.append(f"       {f['key']}: {_num(f['prior'])} ({f['prior_at']}) -> "
                   f"{_num(f['level'])} ({f['observed_at']}), {f['basis']} change "
                   f"{f['change']:+.6g} = {f['sigmas']:.1f} sd")
    out.append(f"  2. revisions (listed, never flagged): {len(r['revisions'])}")
    for x in r["revisions"]:
        out.append(f"       {x['key']} {x['observed_at']}: {x['old']:g} "
                   f"(stored {x['old_available']}) -> {x['new']:g}")
    bf_rows = [x for x in r.get("backfill") or [] if "old" in x]
    bf_new = [x for x in r.get("backfill") or [] if "first_written" in x]
    out.append(f"  backfill (the history writer's rows; never revisions): "
               f"{len(bf_rows)} restated, {sum(x['first_written'] for x in bf_new)} "
               f"written first, across "
               f"{len({x['key'] for x in r.get('backfill') or []})} key(s)")
    for x in bf_rows[:8]:
        out.append(f"       {x['key']} {x['observed_at']}: {x['old']:g} -> "
                   f"{x['new']:g} ({x['source']})")
    if len(bf_rows) > 8:
        out.append(f"       ... and {len(bf_rows) - 8} more")
    out.append(f"  steps (policy rates; informational, never flags): "
               f"{len(r.get('steps') or [])}")
    out += [f"       {step_line(s)}" for s in r.get("steps") or []]
    out.append(f"  3. cross-source pairs: {sum(1 for p in r['pairs'] if p['flagged'])}"
               f" flagged of {len(r['pairs'])}")
    for p in r["pairs"]:
        if p["state"] in ("flag", "clean"):
            out.append(f"       {p['a_label']} vs {p['b_label']} on {p['on']}: "
                       f"{_num(p['a'])} vs {_num(p['b'])}, gap {p['gap']:.4g} "
                       f"against {p['tolerance']:g} -- {p['state'].upper()}")
        else:
            out.append(f"       {p['a_label']} vs {p['b_label']}: {p['state']}"
                       + (f" ({p['why'][:90]})" if p.get("why") else ""))
    out.append(f"  skipped (too short or flat): {len(r['skipped'])}")
    for s in r["skipped"][:12]:
        out.append(f"       {s['key']}: {s['why']}")
    if len(r["skipped"]) > 12:
        out.append(f"       ... and {len(r['skipped']) - 12} more")
    out += ["", "  CLEAN" if not r["flags"] else
            f"  FLAGS: {len(r['flags'])} -- a prompt to look, never a block", line]
    return "\n".join(out)


def measure(db: str, to: Optional[str] = None, cfg: Optional[dict] = None) -> list[dict]:
    """Each pair's tolerance over its own shared history to `to`: read-only,
    printed for the operator to record in config. Writes nothing."""
    cfg = cfg if cfg is not None else load_config()
    pcfg = cfg.get("pairs") or {}
    to = (to or "9999-12-31")[:10]
    conn = open_ro(db)
    try:
        out = []
        for pc in pcfg.get("list") or []:
            va, vb = vintages(conn, pc["a"], to, 10 ** 7), vintages(conn, pc["b"], to,
                                                                   10 ** 7)
            both = sorted(set(va) & set(vb))
            m = measure_gaps([va[d][-1][1] - vb[d][-1][1] for d in both],
                             float(pcfg.get("percentile") or 99),
                             float(pc.get("floor") or 0))
            out.append(dict(m, id=pc["id"], first=both[0] if both else None,
                            last=both[-1] if both else None))
    finally:
        conn.close()
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="The data-quality check (read-only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--date", default=None)
    c.add_argument("--db", default=None)
    m = sub.add_parser("measure")
    m.add_argument("--to", default=None)
    m.add_argument("--db", default=None)
    rc_ = sub.add_parser("record", help="check, then mark each flag as a row "
                                        "(after a pull; never alters a value)")
    rc_.add_argument("--date", default=None)
    rc_.add_argument("--db", default=None)
    oc = sub.add_parser("outliers", help="the day's count: 'n outliers'")
    oc.add_argument("--date", default=None)
    oc.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    db = a.db or default_db()
    if a.cmd == "outliers":
        c = outliers_count(db, a.date)
        print(outliers_line(c))
        return 0 if c is not None else 2
    try:
        if a.cmd == "record":
            r = record(db, a.date)
            print(f"data check {r['day']}: {r['checked']} checked, "
                  f"{len(r['flags'])} flagged, {r['recorded']} new mark(s)")
            for f in r["flags"]:
                print(f"  {flag_line(f)}")
            return 0

        if a.cmd == "measure":
            for x in measure(db, a.to):
                print(f"{x['id']}: n={x['n']} {x['first']}..{x['last']} "
                      f"p99={x['p99']} max={x.get('max')} tolerance={x['tolerance']}"
                      f"{' (floored)' if x['floored'] else ''}")
            return 0
        r = check(db, a.date)
    except (sqlite3.Error, OSError) as exc:
        print(f"cannot open the store: {type(exc).__name__}: {exc}")
        return 2
    print(report(r))
    return 1 if r["flags"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

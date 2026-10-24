"""
GDELT's raw event files: daily conflict counts and tone for the geopolitical
families, and a daily mention count per narrative (rulings of 24 Oct 2026, D26;
b59-trigger-sources). Report only.

    python -m altdata.sources.gdelt daily [--dry-run]          # the basket's run
    python -m altdata.sources.gdelt backfill [--days N] [--dry-run]   # the operator's
    python -m altdata.sources.gdelt show [--as-of D]

THE SOURCE (config/gdelt.yaml carries the check of 24 Oct 2026): GDELT 2.0's
15-minute event exports, keyless, unlimited and unrestricted use; robots.txt
answers 404. The daily step reads the 96 exports of each complete UTC day not yet
stored (the last `catch_up_days`), one request at a time, `pause_seconds` apart.
A FAILED OR REFUSED FETCH MARKS THE DAY STALE WITH ITS REASON: nothing is written
for a day with a missing file, and no day is ever filled. The DOC API is not read.

THE BACKFILL reads GDELT 1.0's daily files (one a day, the same events in the 1.0
layout), source `gdelt:v1_daily`, reconstructed at the next day's noon UTC. The
2.0 days are `gdelt:v2_15min`, available at the pull. GDELT 1.0 and 2.0 do not
hold the same number of events a day, which is why the family's level is a SHARE
of the day's events (per 10,000) and the lines name the history's mix.

THE KEYS (observed_at = the UTC day the events were added):
  gdelt.events_total              every event added that day
  gdelt.source_urls_total         the distinct source articles among them
  gdelt.conflict_events           instrument = family: CAMEO roots 18-20
  gdelt.reduce_relations_events   instrument = family: CAMEO root 16
  gdelt.conflict_share            instrument = family: conflict per 10,000 events
  gdelt.avg_tone                  instrument = family: the mean AvgTone, all roots
  gdelt.narrative_mentions        instrument = narrative: distinct articles whose
                                  address carries one of the story's phrases

A family is countries and dyads (config `families`); a narrative is phrases
(config `narratives`), both session-set and listed. Nothing here enters a
composite or the market-state object.
"""

from __future__ import annotations

import datetime as dt
import io
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config" / "gdelt.yaml"
ROSTER = "gdelt"
EVENTS_KEY = "gdelt.events_total"
URLS_KEY = "gdelt.source_urls_total"
CONFLICT_KEY = "gdelt.conflict_events"
REDUCE_KEY = "gdelt.reduce_relations_events"
SHARE_KEY = "gdelt.conflict_share"
TONE_KEY = "gdelt.avg_tone"
NARR_KEY = "gdelt.narrative_mentions"
ROSTER_KEYS = [EVENTS_KEY, URLS_KEY, CONFLICT_KEY, REDUCE_KEY, SHARE_KEY, TONE_KEY,
               NARR_KEY]
SOURCE_V2, SOURCE_V1 = "gdelt:v2_15min", "gdelt:v1_daily"
MEASURE_KEYS = {"conflict": CONFLICT_KEY, "reduce_relations": REDUCE_KEY}

# The two layouts' columns (0-based): actor 1 and 2 CAMEO countries, the root
# code, AvgTone, the action's FIPS country, DATEADDED and SOURCEURL.
LAYOUTS = {
    61: {"name": "v2", "a1": 7, "a2": 17, "root": 28, "tone": 34, "geo": 53,
         "added": 59, "url": 60},
    58: {"name": "v1", "a1": 7, "a2": 17, "root": 28, "tone": 34, "geo": 51,
         "added": 56, "url": 57},
}


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _phrase_re(phrases: list[str]) -> re.Pattern:
    alts = ["-".join(p.lower().split()) for p in phrases]
    return re.compile(r"(?:^|-)(?:" + "|".join(re.escape(a) for a in alts) + r")(?:-|$)")


def _slug(url: str) -> str:
    """The address's host and path as lower-case words joined by hyphens."""
    u = url.lower().split("?", 1)[0].split("#", 1)[0]
    u = re.sub(r"^[a-z]+://", "", u)
    return "-".join(w for w in re.split(r"[^a-z0-9]+", u) if w)


def new_acc() -> dict:
    return {"events": 0, "urls": set(), "fam": {}, "narr": {}, "bad_lines": 0}


def accumulate(acc: dict, text: str, cfg: dict, day: Optional[str] = None) -> dict:
    """Add one export's rows to the day's tallies. A row whose DATEADDED is not
    `day` (YYYYMMDD) is left out when `day` is given; a malformed row is counted
    in `bad_lines` and skipped."""
    fams = cfg["families"]
    roots = {m: set(v) for m, v in cfg["measures"].items()}
    nre = {n: _phrase_re(p) for n, p in (cfg.get("narratives") or {}).items()}
    dy = [(f, {frozenset(d) for d in f.get("dyads") or []}) for f in fams]
    for line in text.splitlines():
        if not line.strip():
            continue
        c = line.split("\t")
        lay = LAYOUTS.get(len(c))
        if lay is None:
            acc["bad_lines"] += 1
            continue
        if day and c[lay["added"]][:8] != day:
            continue
        acc["events"] += 1
        url = c[lay["url"]].strip()
        if url:
            acc["urls"].add(url)
        a1, a2, geo = c[lay["a1"]], c[lay["a2"]], c[lay["geo"]]
        root = c[lay["root"]].strip().zfill(2)
        try:
            tone = float(c[lay["tone"]])
        except ValueError:
            tone = None
        for f, dyads in dy:
            hit = (a1 in f["actors"] or a2 in f["actors"] or geo in f["locations"]
                   or (a1 and a2 and frozenset((a1, a2)) in dyads))
            if not hit:
                continue
            t = acc["fam"].setdefault(f["id"], {"n": 0, "tone_sum": 0.0, "tone_n": 0,
                                                **{m: 0 for m in roots}})
            t["n"] += 1
            for m, rs in roots.items():
                if root in rs:
                    t[m] += 1
            if tone is not None:
                t["tone_sum"] += tone
                t["tone_n"] += 1
        if url and nre:
            s = _slug(url)
            for n, rx in nre.items():
                if rx.search(s):
                    acc["narr"].setdefault(n, set()).add(url)
    return acc


def rows_for_day(day: str, acc: dict, cfg: dict, at: str, source: str,
                 kind: str = "ingest_instant") -> list[dict]:
    """The day's rows (day as YYYY-MM-DD). Every family and narrative gets a row,
    zero included, so a quiet day is a zero and never a gap."""
    per = float(cfg.get("share_per") or 10000)
    n = acc["events"]

    def row(key, value, inst=None):
        return {"registry_key": key, "instrument": inst, "observed_at": day,
                "available_at": at, "value": value, "source": source,
                "availability_kind": kind}
    out = [row(EVENTS_KEY, n), row(URLS_KEY, len(acc["urls"]))]
    for f in cfg["families"]:
        t = acc["fam"].get(f["id"]) or {"n": 0, "tone_sum": 0.0, "tone_n": 0}
        for m, key in MEASURE_KEYS.items():
            out.append(row(key, int(t.get(m) or 0), f["id"]))
        out.append(row(SHARE_KEY, round(per * (t.get("conflict") or 0) / n, 3) if n else None,
                       f["id"]))
        if t["tone_n"]:
            out.append(row(TONE_KEY, round(t["tone_sum"] / t["tone_n"], 4), f["id"]))
    for name in cfg.get("narratives") or {}:
        out.append(row(NARR_KEY, len(acc["narr"].get(name) or ()), name))
    return [r for r in out if r["value"] is not None]


def unzip_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        name = z.namelist()[0]
        return z.read(name).decode("utf-8", "replace")


def stamps_for(day: dt.date) -> list[str]:
    """The 96 15-minute export stamps of a UTC day."""
    base = dt.datetime.combine(day, dt.time(0, 0))
    return [(base + dt.timedelta(minutes=15 * i)).strftime("%Y%m%d%H%M%S")
            for i in range(96)]


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------
def _get(url: str) -> bytes:
    from ._base import http_get_bytes                           # noqa: PLC0415
    return http_get_bytes(url, timeout=90)


def fetch_day_v2(day: dt.date, cfg: dict, fetch: Callable = None,
                 sleep: Callable = time.sleep) -> tuple[Optional[dict], Optional[str]]:
    """The day's 96 exports, tallied; (None, reason) on the first failed fetch."""
    fetch = fetch or _get
    acc = new_acc()
    ymd = day.strftime("%Y%m%d")
    for i, stamp in enumerate(stamps_for(day)):
        if i:
            sleep(float(cfg.get("pause_seconds") or 1.5))
        url = cfg["urls"]["v2_export"].format(stamp=stamp)
        try:
            accumulate(acc, unzip_text(fetch(url)), cfg, ymd)
        except Exception as exc:                                # noqa: BLE001
            return None, (f"STALE: the export {stamp} failed "
                          f"({type(exc).__name__}: {str(exc)[:100]}); nothing written "
                          f"for {day}")
    return acc, None


def last_complete_day(now: Optional[dt.datetime] = None) -> dt.date:
    """The last UTC day whose 96 exports are all published (the 23:45 window's
    file lands by about 00:15 UTC; 30 minutes' margin)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    return (now - dt.timedelta(minutes=30)).date() - dt.timedelta(days=1)


def _stored_days(st, cutoff: str) -> set[str]:
    return {str(r["observed_at"])[:10] for r in st.as_of(EVENTS_KEY, cutoff)}


def daily(dry_run: bool = False, now: Optional[dt.datetime] = None,
          cfg: Optional[dict] = None, fetch: Callable = None,
          sleep: Callable = time.sleep, db=None, record: bool = True,
          stored: Optional[set] = None) -> dict:
    """A step of the crypto basket's 17:25 run (no new timer): each complete UTC
    day of the last `catch_up_days` not yet stored."""
    from .. import observations, session                        # noqa: PLC0415
    cfg = cfg or config()
    last = last_complete_day(now)
    days = [last - dt.timedelta(days=i) for i in range(int(cfg.get("catch_up_days") or 3))]
    own = db is None and not dry_run
    st = db or (observations.open_writer(__name__) if not dry_run else None)
    out: dict[str, Any] = {"step": "daily", "dry_run": dry_run, "stale": {}, "days": []}
    try:
        if stored is None:
            stored = (_stored_days(st, session.utc_iso(timespec="microseconds"))
                      if st is not None else set())
        rows: list[dict] = []
        for d in sorted(days):
            if d.isoformat() in stored:
                continue
            acc, why = fetch_day_v2(d, cfg, fetch, sleep)
            if acc is None:
                out["stale"][d.isoformat()] = why
                continue
            at = session.utc_iso(timespec="microseconds")
            rows += rows_for_day(d.isoformat(), acc, cfg, at, SOURCE_V2)
            out["days"].append({"day": d.isoformat(), "events": acc["events"],
                                "bad_lines": acc["bad_lines"]})
        out["rows"] = len(rows)
        if dry_run:
            out["preview"] = rows[:12]
            return out
        out["written"] = st.write_many(rows) if rows else 0
    finally:
        if own and st is not None:
            st.close()
    if record:
        from .. import feeds                                    # noqa: PLC0415
        reason = "; ".join(out["stale"].values()) if out["stale"] else None
        feeds.record_attempted(ROSTER, ROSTER_KEYS, merge=True,
                               failed=({k: reason for k in ROSTER_KEYS}
                                       if reason and not out.get("written") else None))
    return out


def backfill(days: Optional[int] = None, dry_run: bool = False,
             now: Optional[dt.datetime] = None, cfg: Optional[dict] = None,
             fetch: Callable = None, sleep: Callable = time.sleep, db=None,
             stored: Optional[set] = None) -> dict:
    """The operator's: GDELT 1.0's daily files for the `days` before the 2.0
    history, one request a day; a failed day is listed and skipped, never filled."""
    from .. import observations, session                        # noqa: PLC0415
    cfg = cfg or config()
    fetch = fetch or _get
    n = int(days or cfg.get("backfill_days") or 365)
    last = last_complete_day(now)
    own = db is None and not dry_run
    st = db or (observations.open_writer(__name__) if not dry_run else None)
    out: dict[str, Any] = {"step": "backfill", "dry_run": dry_run, "failed": {}, "rows": 0}
    try:
        if stored is None:
            stored = (_stored_days(st, session.utc_iso(timespec="microseconds"))
                      if st is not None else set())
        todo = [last - dt.timedelta(days=i) for i in range(n, 0, -1)]
        todo = [d for d in todo if d.isoformat() not in stored]
        out["requests"] = len(todo)
        if dry_run:
            out["first"] = todo[0].isoformat() if todo else None
            out["last"] = todo[-1].isoformat() if todo else None
            return out
        for i, d in enumerate(todo):
            if i:
                sleep(float(cfg.get("pause_seconds") or 1.5))
            try:
                acc = accumulate(new_acc(), unzip_text(fetch(cfg["urls"]["v1_daily"].format(
                    day=d.strftime("%Y%m%d")))), cfg, d.strftime("%Y%m%d"))
            except Exception as exc:                            # noqa: BLE001
                out["failed"][d.isoformat()] = f"{type(exc).__name__}: {str(exc)[:100]}"
                continue
            at = observations.canonical_instant(dt.datetime.combine(
                d + dt.timedelta(days=1), dt.time(12, 0),
                tzinfo=dt.timezone.utc).isoformat())
            rows = rows_for_day(d.isoformat(), acc, cfg, at, SOURCE_V1, "reconstructed")
            out["rows"] += st.write_many(rows)
    finally:
        if own and st is not None:
            st.close()
    return out


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------
def _pts(st, key: str, cutoff: str, inst: Optional[str] = None):
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    return rt._pts(st, key, cutoff, inst)                       # noqa: SLF001


def _sources(st, cutoff: str) -> dict:
    """The history's mix: the first and last day each source holds."""
    out: dict[str, list[str]] = {}
    for r in st.as_of(EVENTS_KEY, cutoff):
        s = str(r.get("source") or "")
        d = str(r["observed_at"])[:10]
        a = out.setdefault(s, [d, d])
        a[0], a[1] = min(a[0], d), max(a[1], d)
    return out


def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    cfg = cfg or config()
    years = int(cfg.get("lens_years") or 5)
    ev = _pts(st, EVENTS_KEY, cutoff)
    out: dict[str, Any] = {"as_of": ev[-1][0] if ev else None, "families": [],
                           "narratives": [], "sources": _sources(st, cutoff) if ev else {}}
    if not ev:
        out["state"] = "absent"
        return out
    out["state"] = "computed"
    out["events"] = int(ev[-1][1])
    for f in cfg["families"]:
        sh = _pts(st, SHARE_KEY, cutoff, f["id"])
        cn = _pts(st, CONFLICT_KEY, cutoff, f["id"])
        rr = _pts(st, REDUCE_KEY, cutoff, f["id"])
        tn = _pts(st, TONE_KEY, cutoff, f["id"])
        row: dict[str, Any] = {"id": f["id"], "label": f["label"], "factor": f.get("factor")}
        if sh:
            five = [v for _, v in sh[-5:]]
            row.update(day=sh[-1][0], share=sh[-1][1], share_5d=round(sum(five) / len(five), 2),
                       lens=rt.lens(sh, years), conflict=int(cn[-1][1]) if cn else None,
                       reduce=int(rr[-1][1]) if rr else None,
                       tone=tn[-1][1] if tn and tn[-1][0] == sh[-1][0] else None,
                       tone_lens=rt.lens(tn, years) if tn else None)
        out["families"].append(row)
    for name in cfg.get("narratives") or {}:
        p = _pts(st, NARR_KEY, cutoff, name)
        week = sum(v for _, v in p[-7:]) if p else None
        prior = sum(v for _, v in p[-14:-7]) if len(p) >= 14 else None
        out["narratives"].append({"id": name, "day": p[-1][0] if p else None,
                                  "week": None if week is None else int(week),
                                  "prior": None if prior is None else int(prior)})
    return out


def mix_text(r: dict) -> str:
    src = r.get("sources") or {}
    parts = []
    for s, lab in ((SOURCE_V1, "1.0 daily files"), (SOURCE_V2, "2.0 15-minute exports")):
        if s in src:
            parts.append(f"{lab} {src[s][0]} to {src[s][1]}")
    return "; ".join(parts) or "no history stored"


def factor_lines(r: dict) -> list[str]:
    """Factor III's lines: each family's conflict share with its dual percentiles,
    its counts and tone; one line when nothing is stored."""
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    if r.get("state") != "computed":
        return ["Factor III, GDELT's event files: not read (the first daily pull has "
                "not run; gdelt.conflict_share)."]
    out = [f"Factor III, GDELT's event files (as of {r['as_of']}, {r['events']:,} events; "
           f"history: {mix_text(r)}):"]
    for f in r["families"]:
        if f.get("share") is None:
            out.append(f"  {f['label']}: not read (gdelt.conflict_share).")
            continue
        out.append(f"  {f['label']}: conflict {f['share']:.1f} per 10,000 events "
                   f"({rt.lens_text(f['lens'])}; five-day mean {f['share_5d']:.1f}); "
                   f"{f['conflict']} conflict and {f['reduce']} reduce-relations events"
                   + (f"; tone {f['tone']:+.2f}" if f.get("tone") is not None else "")
                   + ".")
    out.append("Report only: event counts as the news reports them, no composite, no "
               "market-state input (D26).")
    return out


def tail_line(r: dict) -> str:
    """The Weekly's tail register: the family highest on its five-year percentile."""
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    fams = [f for f in r.get("families") or [] if f.get("share") is not None]
    if r.get("state") != "computed" or not fams:
        return "Geopolitical attention (GDELT): not read (gdelt.conflict_share)."
    top = max(fams, key=lambda f: f["lens"].get("percentile_window") or -1)
    return (f"Geopolitical attention (GDELT, as of {r['as_of']}): {top['label']} "
            f"highest, conflict {top['share']:.1f} per 10,000 events at the "
            f"{rt.ordinal(top['lens'].get('percentile_window'))} percentile of its "
            f"history (n={top['lens'].get('n_window')}). Report only.")


def story_title(sid: str) -> str:
    """The story's plain title (altdata/labels.py), else its register name."""
    import yaml                                                 # noqa: PLC0415

    from .. import labels                                       # noqa: PLC0415
    t = labels.story(sid).get("title")
    if t:
        return str(t)
    d = yaml.safe_load((REPO / "config" / "narratives.yaml").read_text(encoding="utf-8"))
    for grp in ("narratives", "proposals"):
        e = (d.get(grp) or {}).get(sid)
        if isinstance(e, dict) and e.get("name"):
            return str(e["name"])
    return sid


def narrative_table(r: dict) -> dict:
    rows = []
    for n in r.get("narratives") or []:
        rows.append([story_title(n["id"]), "—" if n["week"] is None else f"{n['week']:,}",
                     "—" if n["prior"] is None else f"{n['prior']:,}", n["day"] or "—"])
    return {"columns": ["Story", "Articles, last 7 days", "The 7 days before", "As of"],
            "rows": rows}


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415

    from .. import observations, session                        # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.gdelt")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("daily")
    d.add_argument("--dry-run", action="store_true")
    b = sub.add_parser("backfill")
    b.add_argument("--days", type=int, default=None)
    b.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "daily":
        print(json.dumps(daily(dry_run=a.dry_run), indent=1, default=str))
        return 0
    if a.cmd == "backfill":
        print(json.dumps(backfill(days=a.days, dry_run=a.dry_run), indent=1, default=str))
        return 0
    with observations.ObservationStore() as st:
        r = read(st, a.as_of or session.utc_iso())
    for ln in factor_lines(r) + [tail_line(r)]:
        print(ln)
    for row in narrative_table(r)["rows"]:
        print("  " + " | ".join(str(x) for x in row))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

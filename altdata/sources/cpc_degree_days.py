"""
NOAA CPC's population-weighted heating and cooling degree days, daily, from 1981,
and their departure from normal (rulings of 24 Oct 2026, D26; b59-trigger-sources).
Report only.

    python -m altdata.sources.cpc_degree_days daily [--dry-run]      # the basket's run
    python -m altdata.sources.cpc_degree_days backfill [--dry-run]   # the operator's
    python -m altdata.sources.cpc_degree_days show [--as-of D]

THE SOURCE (config/cpc_degree_days.yaml carries the check of 24 Oct 2026): the
Climate Prediction Center's daily files, public domain, keyless; robots.txt
answers 404. One file per year and kind, one row per census division and CONUS,
one column per day. The daily step reads this year's two files (and last year's
in the first days of January) and writes each day not stored, and a new vintage
of a re-read day whose value changed. A failed fetch writes nothing and the roster
names the failure; nothing is filled.

THE KEYS (observed_at = the day; instrument = the region, `conus` among them):
  noaa.hdd_pop    heating degree days, population-weighted
  noaa.cdd_pop    cooling degree days, population-weighted

THE NORMAL is computed on read, never stored: the mean of the same calendar day
over 1991-2020 (NOAA's normals period; 29 February takes 28 February's), from the
stored history. The lines print the last seven days' sums, their normals, the
departure and its dual percentiles, beside Henry Hub spot (FRED DHHNGSP). Nothing
here enters a composite or the market-state object.
"""

from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config" / "cpc_degree_days.yaml"
ROSTER = "degree_days"
HDD_KEY, CDD_KEY = "noaa.hdd_pop", "noaa.cdd_pop"
KEYS = {"hdd": HDD_KEY, "cdd": CDD_KEY}
ROSTER_KEYS = [HDD_KEY, CDD_KEY]
SOURCE = "noaa_cpc"
TITLE = "Energy: degree days beside natural gas"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse(text: str, cfg: dict) -> dict[str, list[tuple[str, float]]]:
    """{instrument: [(YYYY-MM-DD, value)]} from one year's file. A cell that is
    not a non-negative number is left out (never filled)."""
    regions = {str(k): v for k, v in cfg["regions"].items()}
    days: list[str] = []
    out: dict[str, list[tuple[str, float]]] = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if not cells or len(cells) < 2:
            continue
        if cells[0] == "Region":
            days = [f"{c[:4]}-{c[4:6]}-{c[6:8]}" for c in cells[1:] if len(c) == 8]
            continue
        inst = regions.get(cells[0])
        if inst is None or not days:
            continue
        pts = []
        for d, c in zip(days, cells[1:]):
            try:
                v = float(c)
            except ValueError:
                continue
            if v >= 0:
                pts.append((d, v))
        out[inst] = pts
    return out


def rows(kind: str, parsed: dict, at: str, avail: str = "ingest_instant",
         since: Optional[str] = None, known: Optional[dict] = None) -> list[dict]:
    """Rows for days on or after `since`, skipping a day whose stored value is
    unchanged (`known`: {(instrument, day): value})."""
    key = KEYS[kind]
    out = []
    for inst, pts in sorted(parsed.items()):
        for d, v in pts:
            if since and d < since:
                continue
            if known is not None and known.get((inst, d)) == v:
                continue
            out.append({"registry_key": key, "instrument": inst, "observed_at": d,
                        "available_at": at, "value": v, "source": SOURCE,
                        "availability_kind": avail})
    return out


def _backfill_at(day: str) -> str:
    from .. import observations                                 # noqa: PLC0415
    d = dt.date.fromisoformat(day) + dt.timedelta(days=2)
    return observations.canonical_instant(
        dt.datetime.combine(d, dt.time(12, 0), tzinfo=dt.timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------
def _get(url: str) -> str:
    from ._base import http_get_bytes                           # noqa: PLC0415
    return http_get_bytes(url, timeout=90).decode("utf-8", "replace")


def _known(st, key: str, since: str, cutoff: str, cfg: dict) -> dict:
    out = {}
    for inst in cfg["regions"].values():
        for r in st.as_of(key, cutoff, inst, observed_from=since):
            if r.get("value_num") is not None:
                out[(inst, str(r["observed_at"])[:10])] = float(r["value_num"])
    return out


def daily(dry_run: bool = False, today: Optional[str] = None, cfg: Optional[dict] = None,
          fetch: Callable = None, sleep: Callable = time.sleep, db=None,
          record: bool = True) -> dict:
    from .. import observations, session                        # noqa: PLC0415
    cfg = cfg or config()
    fetch = fetch or _get
    day = dt.date.fromisoformat((today or session.session_date())[:10])
    since = (day - dt.timedelta(days=int(cfg.get("reread_days") or 14))).isoformat()
    years = sorted({day.year, dt.date.fromisoformat(since).year})
    out: dict[str, Any] = {"step": "daily", "dry_run": dry_run, "failed": {}, "newest": {}}
    own = db is None and not dry_run
    st = db or (observations.open_writer(__name__) if not dry_run else None)
    try:
        at = session.utc_iso(timespec="microseconds")
        allrows: list[dict] = []
        n = 0
        for kind, label in cfg["kinds"].items():
            known = (_known(st, KEYS[kind], since, session.utc_iso(timespec="microseconds"),
                            cfg) if st is not None else None)
            for y in years:
                if n:
                    sleep(float(cfg.get("pause_seconds") or 1.0))
                n += 1
                url = cfg["url"].format(year=y, kind=label)
                try:
                    parsed = parse(fetch(url), cfg)
                except Exception as exc:                        # noqa: BLE001
                    out["failed"][KEYS[kind]] = (f"noaa_cpc {y} {label}: "
                                                 f"{type(exc).__name__}: {str(exc)[:100]}")
                    continue
                c = parsed.get("conus") or []
                if c:
                    out["newest"][kind] = c[-1]
                allrows += rows(kind, parsed, at, since=since, known=known)
        out["rows"] = len(allrows)
        if dry_run:
            out["preview"] = [r for r in allrows if r["instrument"] == "conus"][-6:]
            return out
        out["written"] = st.write_many(allrows) if allrows else 0
    finally:
        if own and st is not None:
            st.close()
    if record:
        from .. import feeds                                    # noqa: PLC0415
        feeds.record_attempted(ROSTER, ROSTER_KEYS, merge=True,
                               failed=out["failed"] or None)
    return out


def backfill(dry_run: bool = False, today: Optional[str] = None,
             cfg: Optional[dict] = None, fetch: Callable = None,
             sleep: Callable = time.sleep, db=None) -> dict:
    """The operator's, once: every year's two files from 1981 to last year,
    reconstructed (available two days after the day, the files' own lag)."""
    from .. import observations, session                        # noqa: PLC0415
    cfg = cfg or config()
    fetch = fetch or _get
    day = dt.date.fromisoformat((today or session.session_date())[:10])
    years = list(range(int(cfg["history_from"]), day.year))
    out: dict[str, Any] = {"step": "backfill", "requests": 2 * len(years), "failed": {},
                           "rows": 0}
    if dry_run:
        out["years"] = [years[0], years[-1]] if years else []
        return out
    own = db is None
    st = db or observations.open_writer(__name__)
    try:
        n = 0
        for kind, label in cfg["kinds"].items():
            for y in years:
                if n:
                    sleep(float(cfg.get("pause_seconds") or 1.0))
                n += 1
                try:
                    parsed = parse(fetch(cfg["url"].format(year=y, kind=label)), cfg)
                except Exception as exc:                        # noqa: BLE001
                    out["failed"][f"{y} {label}"] = f"{type(exc).__name__}: {str(exc)[:100]}"
                    continue
                rs = []
                for inst, pts in parsed.items():
                    rs += [{"registry_key": KEYS[kind], "instrument": inst, "observed_at": d,
                            "available_at": _backfill_at(d), "value": v, "source": SOURCE,
                            "availability_kind": "reconstructed"} for d, v in pts]
                out["rows"] += st.write_many(rs)
    finally:
        if own:
            st.close()
    return out


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------
def normals(pts: list[tuple[str, float]], cfg: dict) -> dict[str, float]:
    """{MM-DD: the mean over the normal years}, where at least `normal_min_years`
    of them are stored; 02-29 takes 02-28's."""
    a, b = (int(x) for x in cfg["normal_years"])
    acc: dict[str, list[float]] = {}
    for d, v in pts:
        if a <= int(d[:4]) <= b:
            acc.setdefault(d[5:], []).append(v)
    need = int(cfg.get("normal_min_years") or 20)
    out = {md: sum(vs) / len(vs) for md, vs in acc.items() if len(vs) >= need and md != "02-29"}
    if "02-28" in out:
        out["02-29"] = out["02-28"]
    return out


def window_read(pts: list[tuple[str, float]], cfg: dict,
                norm: Optional[dict] = None) -> dict:
    """The last `window_days` days' sum, its normal and departure, and the
    departure's dual percentiles against every stored window's departure."""
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    w = int(cfg.get("window_days") or 7)
    if len(pts) < w:
        return {"state": "absent"}
    norm = normals(pts, cfg) if norm is None else norm
    last = pts[-w:]
    s = sum(v for _, v in last)
    out: dict[str, Any] = {"state": "computed", "end": last[-1][0], "start": last[0][0],
                           "sum": round(s, 1)}
    if not norm or any(d[5:] not in norm for d, _ in last):
        out["normal_state"] = "not read"
        return out
    nsum = sum(norm[d[5:]] for d, _ in last)
    out.update(normal=round(nsum, 1), departure=round(s - nsum, 1), normal_state="computed")
    # Every stored window of `w` consecutive days with a normal on each, as its
    # departure: the percentiles' history.
    deps = [(d, v - norm[d[5:]]) for d, v in pts if d[5:] in norm]
    roll = []
    for i in range(w - 1, len(deps)):
        a, b = dt.date.fromisoformat(deps[i - w + 1][0]), dt.date.fromisoformat(deps[i][0])
        if (b - a).days == w - 1:
            roll.append((deps[i][0], sum(x for _, x in deps[i - w + 1:i + 1])))
    out["lens"] = rt.lens(roll, int(cfg.get("lens_years") or 5)) if roll else None
    return out


def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    cfg = cfg or config()
    out: dict[str, Any] = {"as_of": cutoff}
    for kind, key in KEYS.items():
        pts = rt._pts(st, key, cutoff, "conus")                 # noqa: SLF001
        out[kind] = window_read(pts, cfg) if pts else {"state": "absent"}
        out[kind]["from"] = pts[0][0] if pts else None
    ng = rt._pts(st, cfg["natgas_key"], cutoff)                 # noqa: SLF001
    if ng:
        ch = rt.change(ng, 7)
        out["natgas"] = {"day": ng[-1][0], "level": ng[-1][1],
                         "week_pct": (round(100.0 * (ch["now"] / ch["then"] - 1), 1)
                                      if ch and ch["then"] else None)}
    return out


def lines(r: dict) -> list[str]:
    from .. import st_r5_rates as rt                            # noqa: PLC0415
    out = []
    for kind, lab in (("hdd", "Heating degree days"), ("cdd", "Cooling degree days")):
        x = r.get(kind) or {}
        if x.get("state") != "computed":
            out.append(f"{lab} (CONUS, population-weighted): not read (noaa."
                       f"{kind}_pop; the first pull has not run).")
            continue
        head = f"{lab} (CONUS, population-weighted), {x['start']} to {x['end']}: {x['sum']:.0f}"
        if x.get("normal_state") == "computed":
            head += (f" against a normal of {x['normal']:.0f}, {x['departure']:+.0f} "
                     f"from normal")
            if x.get("lens"):
                head += f" ({rt.lens_text(x['lens'])} of seven-day departures)"
        else:
            head += (f"; no normal (needs {r.get('normal_min_years', 20)} of the "
                     f"1991-2020 years stored; history from {x.get('from')})")
        out.append(head + ".")
    ng = r.get("natgas")
    out.append("Natural gas, Henry Hub spot (FRED DHHNGSP): " +
               (f"${ng['level']:.2f} on {ng['day']}"
                + (f", {ng['week_pct']:+.1f}% on the week" if ng.get("week_pct") is not None
                   else "") + "."
                if ng else "not stored (fred.natgas)."))
    out.append("Report only: weather-driven demand beside the price, no composite, no "
               "market-state input (D26).")
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415

    from .. import observations, session                        # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.cpc_degree_days")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("daily", "backfill"):
        p = sub.add_parser(name)
        p.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "daily":
        print(json.dumps(daily(dry_run=a.dry_run), indent=1, default=str))
        return 0
    if a.cmd == "backfill":
        print(json.dumps(backfill(dry_run=a.dry_run), indent=1, default=str))
        return 0
    with observations.ObservationStore() as st:
        r = read(st, a.as_of or session.utc_iso())
    for ln in lines(r):
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

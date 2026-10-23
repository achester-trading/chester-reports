"""
The dealer captures, stored (decision 9 of 19 Oct 2026, 15:59 ET; session A's
a50-dealer-store). Each computed exposure profile our own engine wrote --
data/computed/<session>/<SYM>_<HHMMSSZ>_exposure.json, the 09:45 and 12:30
captures and the 16:10 profiles -- becomes a handful of store rows, so the
readers that read the dealer series by name have a history.

    python -m altdata.dealer_store backfill [--from D] [--to D] [--dir PATH]
                                            [--db PATH] [--dry-run]

WHAT EACH CAPTURE WRITES, one row per field, keyed by symbol and slot:

    exposure.net_gex          overall.net_gex ($ per point, as the engine stores it)
    exposure.net_to_gross     overall.net_to_gross
    exposure.regime_word      the regime word as the gate reads it
                              (daily_cascade/dealer_block.regime): "positive
                              gamma" or "negative gamma" with net-to-gross at
                              least net_to_gross_min (0.10, RULED), otherwise
                              "indeterminate"; no row without both inputs
    exposure.gamma_flip       overall.gamma_flip (the zero-gamma level)
    exposure.call_wall_otm    overall.call_wall_otm
    exposure.put_wall_otm     overall.put_wall_otm
    exposure.spot             the profile's spot

THE KEYS AND THE CLOCKS.
  instrument    the symbol
  observed_at   the slot's instant on the session: <session> 09:45, 12:30 or
                16:10 ET as an ISO instant, the slot by dealer_block.slot_of (a
                settled capture is 16:10; an intraday one the nearest declared
                slot within the tolerance, else it is not stored). Every reader
                that groups by day (alpha/pit.py, alpha/search.py) reads the
                first ten characters, so a day's slots are that day's vintages in
                computed order, and an as-of read takes the newest capture
                knowable at its cutoff
  available_at  the file's own computed_at, never the write instant
  source        dealer_capture:<the capture's own id>: its run_id, else the
                file's stem

A re-store of the same file is a no-op (the store's vintage key); a recomputed
profile has a new computed_at and is a new vintage, as its registry entry says
(revision_policy recomputed).

OUR OWN ENGINE'S FILES ONLY. The glob is *_exposure.json; a profile whose gamma
the vendor supplied (gamma_source "vendor") is refused, and no data/vendor file,
FlashAlpha slot or *_gex.json is opened. A restricted (Brookfield) symbol is
never stored.

WHERE IT RUNS. Inside the existing runs, after compute, never fatal: the capture
(altdata/dealer_capture.py, after compute_written) and the EOD pass (run_eod.py,
after Stage 2). No unit and no timer of its own. The backfill reads the files
already on the box; it is the operator's command, dry run first.

WHAT IT IS NOT. It computes no regime of its own: the word is the capture's own
gate reading, as the close prints it. It writes nothing to the market-state
object, a composite, the register or a ledger.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

log = logging.getLogger("altdata.dealer_store")

SOURCE = "dealer_capture"
FIELDS = (("net_gex", "exposure.net_gex"),
          ("net_to_gross", "exposure.net_to_gross"),
          ("gamma_flip", "exposure.gamma_flip"),
          ("call_wall_otm", "exposure.call_wall_otm"),
          ("put_wall_otm", "exposure.put_wall_otm"))
SPOT_KEY = "exposure.spot"
WORD_KEY = "exposure.regime_word"
KEYS = tuple(k for _, k in FIELDS) + (WORD_KEY, SPOT_KEY)
WORDS = ("positive gamma", "negative gamma", "indeterminate")
NAME_RE = re.compile(r"^(?P<sym>[A-Z0-9^.\-]+)_\d{6}Z_exposure\.json$")


def regime_word(net: Optional[float], ntg: Optional[float],
                cfg: Optional[dict] = None) -> Optional[str]:
    """The gate's own word (dealer_block.regime), its printed percentage dropped:
    "positive gamma", "negative gamma", "indeterminate", or None without both."""
    from daily_cascade import dealer_block                      # noqa: PLC0415
    w = dealer_block.regime(net, ntg, cfg if cfg is not None else dealer_block.config())
    if w.startswith("indeterminate"):
        return "indeterminate"
    return w if w in WORDS else None


def slot_instant(day: str, slot: str) -> str:
    """<day> <slot> ET as an ISO instant with its offset."""
    from . import session                                       # noqa: PLC0415
    h, m = (int(x) for x in slot.split(":"))
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                               tzinfo=session._eastern_tz()).isoformat()  # noqa: SLF001


def _restricted(sym: str) -> bool:
    try:
        from register import instruments                        # noqa: PLC0415
        return instruments.restrictions().is_restricted(sym)
    except Exception:                                           # noqa: BLE001
        return False


def rows_for(profile: dict, path: Optional[Path] = None,
             cfg: Optional[dict] = None) -> tuple[list[dict], Optional[str]]:
    """(rows, None) for one profile, or ([], the reason it is not stored)."""
    from daily_cascade import dealer_block                      # noqa: PLC0415
    cfg = cfg if cfg is not None else dealer_block.config()
    if path is not None and not NAME_RE.match(path.name):
        return [], "not one of our engine's exposure files"
    if profile.get("error"):
        return [], "the profile carries an error"
    if profile.get("gamma_source") == "vendor":
        return [], "vendor-supplied gamma: never read"
    sym = str(profile.get("symbol") or "")
    if not sym:
        return [], "no symbol"
    if _restricted(sym):
        return [], "restricted instrument"
    at = profile.get("computed_at")
    day = profile.get("session_date")
    if not at or not day:
        return [], "no computed_at" if not at else "no session_date"
    slot = dealer_block.slot_of(profile, cfg)
    if not slot:
        return [], "no declared slot within the tolerance"
    cap = str(profile.get("run_id") or (path.stem if path is not None else "") or "")
    if not cap:
        return [], "no capture id"
    base = {"instrument": sym, "observed_at": slot_instant(str(day)[:10], slot),
            "available_at": str(at), "source": f"{SOURCE}:{cap}",
            "run_id": profile.get("run_id"), "availability_kind": "observed"}
    o = profile.get("overall") or {}
    out = []
    for f, key in FIELDS:
        v = o.get(f)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v == v:
            out.append({**base, "registry_key": key, "value": float(v)})
    spot = profile.get("spot")
    if isinstance(spot, (int, float)) and not isinstance(spot, bool) and spot == spot:
        out.append({**base, "registry_key": SPOT_KEY, "value": float(spot)})
    w = regime_word(o.get("net_gex"), o.get("net_to_gross"), cfg)
    if w:
        out.append({**base, "registry_key": WORD_KEY, "value": w})
    return out, (None if out else "no field stored")


def store_paths(paths: Iterable, db_path: Optional[str] = None,
                dry_run: bool = False) -> dict:
    """Store each profile file's rows. {"written": n, "rows": n, "files":
    {"<session>/<name>": "ok" | reason}}. Opens the store only when there is a
    row to write."""
    from daily_cascade import dealer_block                      # noqa: PLC0415
    cfg = dealer_block.config()
    files, rows = {}, []
    for p in paths:
        path = Path(str(p))
        if not str(p).endswith(".json") or not path.is_file():
            continue
        name = f"{path.parent.name}/{path.name}"
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            files[name] = f"unreadable: {type(exc).__name__}"
            continue
        got, why = rows_for(rec, path, cfg)
        files[name] = why or "ok"
        rows += got
    written = 0
    if rows and not dry_run:
        from . import observations                              # noqa: PLC0415
        with observations.open_writer(__name__, db_path) as st:
            written = st.write_many(rows)
    return {"written": written, "rows": len(rows), "files": files}


def store_after_compute(paths: Iterable, db_path: Optional[str] = None,
                        out_dir: Optional[str] = None) -> dict:
    """The capture's and the EOD pass's step: never fatal. A run that wrote its
    profiles to a directory of its own (out_dir) without naming a store stores
    nothing, so no caller writes the default store by accident."""
    if out_dir is not None and db_path is None:
        return {"skipped": "out_dir given without a store path"}
    try:
        return store_paths(paths, db_path)
    except Exception as exc:                                    # noqa: BLE001
        log.exception("dealer store step failed; the profiles are on disk")
        return {"error": f"{type(exc).__name__}: {exc}"[:200]}


def profile_files(base_dir: Optional[str] = None, since: Optional[str] = None,
                  until: Optional[str] = None) -> list[Path]:
    """Our engine's exposure files under the computed directory, by session."""
    from . import config as acfg                                # noqa: PLC0415
    root = Path(base_dir or acfg.COMPUTED_DIR)
    out = []
    if not root.is_dir():
        return out
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d.name):
            continue
        if (since and d.name < since) or (until and d.name > until):
            continue
        out += sorted(f for f in d.glob("*_exposure.json") if NAME_RE.match(f.name))
    return out


def backfill(base_dir: Optional[str] = None, db_path: Optional[str] = None,
             since: Optional[str] = None, until: Optional[str] = None,
             dry_run: bool = True) -> dict:
    files = profile_files(base_dir, since, until)
    res = store_paths(files, db_path, dry_run)
    stored = [n for n, v in res["files"].items() if v == "ok"]
    skipped: dict[str, int] = {}
    for v in res["files"].values():
        if v != "ok":
            skipped[v] = skipped.get(v, 0) + 1
    days = sorted({n.split("/")[0] for n in stored})
    return {"dry_run": dry_run, "files": len(files), "stored_files": len(stored),
            "rows": res["rows"], "written": res["written"], "skipped": skipped,
            "first_session": days[0] if days else None,
            "last_session": days[-1] if days else None}


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.dealer_store")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backfill", help="store the profiles already on disk")
    b.add_argument("--from", dest="since")
    b.add_argument("--to", dest="until")
    b.add_argument("--dir", dest="base_dir")
    b.add_argument("--db", dest="db_path")
    b.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    res = backfill(a.base_dir, a.db_path, a.since, a.until, dry_run=a.dry_run)
    print(json.dumps(res, indent=2, sort_keys=True))
    return 0 if res["files"] else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

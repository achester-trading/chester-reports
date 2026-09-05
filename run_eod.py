"""
End-of-day options pass: fetch chains -> compute GEX -> score the pin log.

One command, three stages, run in order because each consumes the previous
stage's output. Intended for cron on the VPS after the close; run manually
until then.

    python run_eod.py                    # full universe
    python run_eod.py --symbols SPY QQQ  # subset
    python run_eod.py --skip-fetch       # recompute from the last snapshot

STAGE ISOLATION. The fetch is the only irreplaceable stage -- yfinance serves
no historical chains, so a night not captured is a night lost forever. Compute
and pin-scoring read from disk and can be re-run at any time against a stored
snapshot. So a failure in stage 2 or 3 never discards stage 1's work, and the
exit code distinguishes "no data captured" from "captured but not scored".

CLOSE PRICE. --close-source labels what the snapshot's spot actually is. The
default assumes a post-close run. Run this before the bell and the label is
wrong, so pass something honest instead; the pin log stores the label with
every row precisely so a mid-session run can never be mistaken later for a
settled result.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from altdata import config
from altdata import session
from altdata.sources import options_chain
sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import exposure_compute     # noqa: E402
import pin_log              # noqa: E402


def backup_chains(date_str: str, backup_dir: Optional[str] = None) -> dict:
    """Zip the day's raw chains and copy them off this machine.

    The chains are the one asset here that cannot be re-fetched -- yfinance
    serves no history -- so a laptop failure loses the sample permanently. This
    is insurance, not a stage the pipeline depends on, so it never raises.

    The zip is built in a temp directory and verified before it is copied, so a
    truncated archive never lands in the backup folder looking valid. A same-day
    re-run overwrites its own zip rather than accumulating duplicates.
    """
    import shutil
    import tempfile
    import zipfile

    src = Path(config.CHAIN_DIR) / date_str
    out: dict = {"ok": False, "date": date_str, "source": str(src)}
    if not src.exists():
        out["error"] = f"no chain directory for {date_str}"
        return out

    files = sorted(p for p in src.iterdir() if p.is_file())
    if not files:
        out["error"] = "chain directory is empty"
        return out

    dest_dir = Path(backup_dir or config.BACKUP_DIR)
    tmp_zip = Path(tempfile.gettempdir()) / f"chains_{date_str}.zip"
    try:
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, arcname=f.name)
        # Verify before it is allowed anywhere near the backup folder.
        with zipfile.ZipFile(tmp_zip) as z:
            if z.testzip() is not None:
                raise RuntimeError("zip failed CRC verification")
            if len(z.namelist()) != len(files):
                raise RuntimeError(f"zip holds {len(z.namelist())} of {len(files)} files")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / tmp_zip.name
        shutil.copy2(tmp_zip, dest)
        out.update(ok=True, files=len(files), bytes=dest.stat().st_size,
                   dest=str(dest))
    except Exception as e:  # noqa: BLE001 -- backup must never end the run
        out["error"] = f"{type(e).__name__}: {e}"
    finally:
        tmp_zip.unlink(missing_ok=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="EOD options pass")
    ap.add_argument("--symbols", nargs="*", help="Override the configured universe")
    ap.add_argument("--skip-fetch", action="store_true",
                    help="Recompute from the newest stored snapshot")
    ap.add_argument("--max-expiries", type=int, default=None)
    ap.add_argument("--close-source", default="eod_chain_snapshot_spot",
                    help="Label recorded on every pin-log row")
    ap.add_argument("--skip-backup", action="store_true",
                    help="Skip the off-box chain backup")
    ap.add_argument("--backup-dir", default=None,
                    help="Override config.BACKUP_DIR")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    log = logging.getLogger("run_eod")

    universe = args.symbols or config.options_universe()
    started = session.utc_now()
    print(f"EOD options pass -- {started.isoformat(timespec='seconds')}")
    print(f"  universe:   {len(universe)} symbols")
    print(f"  convention: {config.CONVENTION_VERSION}")
    print(f"  tolerance:  {config.PIN_TOLERANCE_BPS}bps\n")

    # ---- Stage 1: chains (the irreplaceable one) ------------------------
    if args.skip_fetch:
        log.info("Stage 1 skipped -- using the newest stored snapshot")
    else:
        log.info("Stage 1: fetching chains")
        try:
            s = options_chain.pull(symbols=universe, max_expiries=args.max_expiries)
            log.info("  chains: %d/%d symbols, %d rows",
                     s["success"], s["total"],
                     sum(e["rows"] for e in s["symbols"].values()))
            if not s["success"]:
                print("\nERROR: no chains captured. Nothing downstream can run.",
                      file=sys.stderr)
                return 1
        except Exception:
            log.exception("Stage 1 failed outright")
            return 1

    # ---- Stage 2: compute ------------------------------------------------
    log.info("Stage 2: computing exposure (GEX/DEX/VEX/CHEX)")
    try:
        computed = exposure_compute.run(symbols=universe)
    except Exception:
        log.exception("Stage 2 failed; chains are stored and can be recomputed "
                      "with --skip-fetch")
        return 2
    if not computed:
        print("\nERROR: nothing computed. Chains are stored; retry with "
              "--skip-fetch.", file=sys.stderr)
        return 2
    log.info("  computed: %d symbols", len(computed))

    # ---- Stage 3: pin log ------------------------------------------------
    log.info("Stage 3: scoring pin levels")
    try:
        rows = pin_log.run(symbols=universe, close_source=args.close_source)
    except Exception:
        log.exception("Stage 3 failed; chains and computed profiles are stored")
        return 3
    log.info("  scored: %d rows", len(rows))

    # ---- Stage 4: off-box backup of the irreplaceable raw chains ---------
    backup = None
    if args.skip_backup:
        log.info("Stage 4 skipped -- backup disabled")
    else:
        log.info("Stage 4: backing up chains")
        # Key the backup on the trading session the chains belong to, not the
        # UTC run date. An EOD run after 20:00 ET is already the next day in
        # UTC, which made this look for a chain directory that never existed.
        session_key = next((c.get("session_date") for c in computed.values()
                            if c.get("session_date")), None) or session.session_date()
        backup = backup_chains(session_key, args.backup_dir)
        if backup.get("ok"):
            log.info("  backed up %d files (%s bytes) -> %s",
                     backup["files"], f"{backup['bytes']:,}", backup["dest"])
        else:
            log.warning("  BACKUP FAILED: %s", backup.get("error"))

    # ---- Summary ---------------------------------------------------------
    print(f"\n{'sym':<6} {'spot':>9} {'$gamma/1%':>16} {'flip':>9} "
          f"{'maxpain':>9} {'peakGEX':>9} {'hit':>4}")
    for sym, r in computed.items():
        if r.get("error"):
            print(f"{sym:<6} ERROR: {r['error']}")
            continue
        o, row = r["overall"], next((x for x in rows if x["symbol"] == sym), {})
        f = lambda v, w=9, p=2: (f"{v:>{w},.{p}f}" if isinstance(v, (int, float))
                                 else f"{'-':>{w}}")
        h = "Y" if row.get("peak_gex_hit") else "n" if row.get("peak_gex_hit") is False else "-"
        print(f"{sym:<6} {f(r['spot'])} {f(o['dollar_gamma_per_1pct'], 16, 0)} "
              f"{f(o['gamma_flip'])} {f(r['max_pain'])} "
              f"{f(o.get('peak_abs_gex_strike'))} {h:>4}")

    hits = sum(1 for r in rows if r.get("peak_gex_hit"))
    elapsed = (session.utc_now() - started).total_seconds()
    print(f"\n  peak-GEX pins within {config.PIN_TOLERANCE_BPS}bps: {hits}/{len(rows)}")
    print(f"  pin log: {config.PIN_LOG_PATH}")
    if backup is None:
        print("  backup:  skipped")
    elif backup.get("ok"):
        print(f"  backup:  {backup['files']} files, {backup['bytes']:,} bytes "
              f"-> {backup['dest']}")
    else:
        print(f"  backup:  FAILED -- {backup.get('error')}")
    print(f"  elapsed: {elapsed:.0f}s")
    # Everything else succeeded, but a failed backup leaves the one
    # irreplaceable asset with a single copy. Distinct exit code so cron alerts
    # on it instead of reporting a clean run.
    if backup is not None and not backup.get("ok"):
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())

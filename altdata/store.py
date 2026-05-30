"""
Normalized data store.

Each series is written as a CSV file under the store directory, with one row
per observation. Columns:

    date         ISO YYYY-MM-DD (or YYYY-MM-DD HH:MM:SS for intraday)
    value        numeric value (may be NaN if FRED reports a gap)
    source       provenance: 'fred', 'eia', etc.
    as_of        when this observation was pulled (ISO timestamp)

CSV chosen over parquet because:
- Zero external dependency on pyarrow (keeps GitHub Actions install fast)
- Human-readable; you can open files in a text editor or Excel
- Diff-friendly so monthly changes appear cleanly in git history

For the data scale here (~50 series, monthly run), CSV is fine.
"""

from __future__ import annotations
import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


# Default location: $ALTDATA_STORE, else ./data_store
DEFAULT_STORE_DIR = os.environ.get("ALTDATA_STORE", "data_store")


class Store:
    """A simple per-series CSV store with provenance."""

    def __init__(self, store_dir: Optional[str] = None):
        self.dir = Path(store_dir or DEFAULT_STORE_DIR)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.csv"

    def write_observations(
        self,
        key: str,
        observations: Iterable[tuple[str, Optional[float]]],
        source: str,
    ) -> int:
        """
        Write a batch of (date, value) tuples for one series.
        Overwrites any existing file for this key.

        Returns count of rows written.
        """
        as_of = datetime.now(timezone.utc).isoformat(timespec="seconds")
        path = self._path(key)
        n = 0
        with path.open("w", newline="") as fp:
            w = csv.writer(fp)
            w.writerow(["date", "value", "source", "as_of"])
            for date, value in observations:
                if value is None:
                    val_str = ""
                else:
                    val_str = f"{value}"
                w.writerow([date, val_str, source, as_of])
                n += 1
        return n

    def read(self, key: str) -> list[dict]:
        """Read all observations for a key. Returns list of {date, value, source, as_of}.
        Returns empty list if the file doesn't exist."""
        path = self._path(key)
        if not path.exists():
            return []
        rows = []
        with path.open() as fp:
            r = csv.DictReader(fp)
            for row in r:
                try:
                    row["value"] = float(row["value"]) if row["value"] != "" else None
                except ValueError:
                    row["value"] = None
                rows.append(row)
        return rows

    def latest(self, key: str) -> Optional[dict]:
        """Latest observation for a key (highest date). None if missing."""
        rows = self.read(key)
        if not rows:
            return None
        valid = [r for r in rows if r["value"] is not None]
        if not valid:
            return None
        return max(valid, key=lambda r: r["date"])

    def prior_n(self, key: str, n: int) -> Optional[dict]:
        """Nth observation back from latest (1 = the most recent prior obs)."""
        rows = [r for r in self.read(key) if r["value"] is not None]
        if not rows or n >= len(rows):
            return None
        rows.sort(key=lambda r: r["date"], reverse=True)
        return rows[n]

    def list_keys(self) -> list[str]:
        return sorted(p.stem for p in self.dir.glob("*.csv"))

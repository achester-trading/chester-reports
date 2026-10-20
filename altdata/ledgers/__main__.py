"""python -m altdata.ledgers run <item|all> [--source public|store] [--out DIR] [--db PATH]

Runs each study against its provider and writes docs/ledgers/<item>-ledger-<date>.md
with its episodes CSV. `public` (the default) is the integrated order's offline rule;
`store` reads the box's newest vintages and refuses a study whose keys it lacks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from importlib import import_module
from pathlib import Path

from . import write_ledger
from . import sources as src

ITEMS = {"30b": "st_r5_30b", "32b": "st_r5_32b", "35b": "st_r5_35b",
         "36b": "st_r5_36b", "43b": "st_r5_43b",
         "17b": "st_r4_17b", "19b": "st_r4_19b"}
MODE = {"public": "laptop run, public sources",
        "store": "box run, the observation store's newest vintages"}


def load_public(spec: dict) -> dict:
    shiller_cache = None
    out = {}
    for name, (kind, arg) in spec.items():
        if kind == "fred":
            out[name] = src.fred(arg)
        elif kind == "shiller":
            shiller_cache = shiller_cache or src.shiller()
            out[name] = shiller_cache[arg]
        elif kind == "yahoo":
            out[name] = src.yahoo(arg)
        elif kind == "bis":
            out[name] = src.bis_policy_rates()
        elif kind == "oecd_cli":
            out[name] = src.oecd_cli(arg)
        elif kind == "redfin":
            out[name] = src.redfin_country(arg)
        else:
            raise ValueError(f"unknown source kind {kind!r}")
    return out


def load_store(spec: dict, db=None) -> dict:
    missing = [n for n, k in spec.items() if not k]
    if missing:
        raise LookupError(f"the store holds no key for {missing}: run --source public "
                          f"(the integrated order's offline rule)")
    return {n: src.store(k, db=db) for n, k in spec.items()}


def run(item: str, source: str = "public", out=None, db=None,
        run_date=None) -> tuple:
    mod = import_module(f".{ITEMS[item]}", __package__)
    series = (load_public(mod.SERIES_PUBLIC) if source == "public"
              else load_store(mod.SERIES_STORE, db))
    r = mod.study(series)
    r["source_mode"] = MODE[source]
    r["sources"] = [f"{n}: {k} {a or ''}".strip() for n, (k, a) in mod.SERIES_PUBLIC.items()] \
        if source == "public" else [f"{n}: store key {k}" for n, k in mod.SERIES_STORE.items()]
    r["sources"].append(f"read {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")
    return write_ledger(r, out, run_date), r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.ledgers")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("item", choices=list(ITEMS) + ["all"])
    r.add_argument("--source", choices=list(MODE), default="public")
    r.add_argument("--out", default=None)
    r.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rc = 0
    for item in (list(ITEMS) if a.item == "all" else [a.item]):
        try:
            (md, csv_path), res = run(item, a.source, Path(a.out) if a.out else None, a.db)
            print(f"{item}: {md}" + (f" (+ {csv_path.name})" if csv_path else "")
                  + f" -- n {res['n']}, as of {res['as_of']}")
        except Exception as exc:                                # noqa: BLE001
            print(f"{item}: FAILED {type(exc).__name__}: {exc}")
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

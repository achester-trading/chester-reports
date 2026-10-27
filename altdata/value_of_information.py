"""
Value of information -- which missing input costs the most forecast accuracy?
(Learning Loop v2, LL-2; A80.)

    python -m altdata.value_of_information list [--as-of ISO] [--db PATH] [--no-objects]
    python -m altdata.value_of_information pack [--as-of ISO] [--db PATH] [--no-objects]
    python -m altdata.value_of_information json [--as-of ISO] [--db PATH] [--no-objects]

The brief's section 2.6 (docs/briefs/learning-loop-v2-brief-2026-10-25.md, ruled
25 Oct 2026). The system records what it could not see; this asks which absence
costs the most, so the scans and the source checks search in that order. Report
only: it changes a search order, which is the operator's. Computed at read from
the stored rows, never stored, never written by a model.

THE METHOD, declared, not fitted:
  * The rows: the probability ledger's resolved rows by the as-of, live sources
    only (decision_quality.resolved_rows), each with its Brier.
  * What was missing at a row's emission: the row's own `missing_inputs` (written
    once by its source; NULL is "not recorded"), united with the market-state
    object held at the emission instant (regime.latest(as_of=emitted_at)): its
    absent dimensions by name and its absent contradiction rows as
    "leg:<row>". A row with neither recorded is UNRECORDED and enters no
    comparison: NULL is never read as "nothing missing".
  * The cell: source family (the source to its first colon) x horizon bucket,
    decision_quality's own (1-7d, 8-31d, 32-92d, >92d).
  * For each input X missing anywhere in a cell: the recorded rows missing X
    against the recorded rows that had it. The statistic is the difference in
    mean Brier (missing less had; positive means the absence cost accuracy),
    with n on both sides and a percentile bootstrap interval: RESAMPLES
    resamples of each side independently, with replacement, from a generator
    seeded by SEED and the entry's name, so the interval is the same on every
    run and does not depend on the order entries are computed in.
  * The share: the rows missing X over the cell's recorded rows.
  * From the error corpus (altdata/error_corpus.py): how many stored misses
    recorded X missing at emission, ledger rows and grades together.
  * The ranked list: every entry with at least FLOOR rows missing the input
    (the brief's section 5: 30 affected rows an input) and at least one row
    that had it, by the Brier difference, largest first. An entry below the
    floor prints as accruing and is not ranked.

Nothing here enters a composite, a dial, a band, a packet or the market-state
object (metrics_registry.yaml market_state_barred). Dry-run sources are never
counted.
"""

from __future__ import annotations

import json
import random
import sys
from typing import Any, Callable, Optional

from . import decision_quality as dq

FLOOR = 30             # rows missing an input before its entry is ranked
RESAMPLES = 2000       # bootstrap resamples, declared
SEED = 20261025        # the brief's ruling date; fixed
LEVEL = 0.95           # a 95% percentile interval
METHOD = "value-of-information-v1"


# ---------------------------------------------------------------------------
# What was missing at emission
# ---------------------------------------------------------------------------
def _loads(v: Any) -> Optional[list]:
    if v is None:
        return None
    try:
        out = json.loads(v) if isinstance(v, str) else v
    except (TypeError, ValueError):
        return None
    return [str(x) for x in out] if isinstance(out, list) else None


def from_object(obj: Optional[dict]) -> Optional[set[str]]:
    """The object's absent dimensions and legs, as input names; None: no object."""
    if not obj:
        return None
    return ({str(d) for d in obj.get("absent_dimensions") or []}
            | {f"leg:{c}" for c in obj.get("absent_contradictions") or []})


def object_reader(db: Optional[str]) -> tuple[Callable[[str], Optional[dict]], Any]:
    """objects(emitted_at) -> the object held then, cached by instant; and the
    store to close. The store is opened `mode=ro` (alpha/store.py's reader,
    which runs no schema, pragma or journal switch), so reading it writes
    nothing beside it."""
    from alpha.store import ReadOnlyStore                       # noqa: PLC0415
    from . import error_corpus                                  # noqa: PLC0415
    st = ReadOnlyStore(db)
    cache: dict[str, Optional[dict]] = {}

    def objects(at: str) -> Optional[dict]:
        if at not in cache:
            cache[at] = error_corpus.object_at(at, st)
        return cache[at]
    return objects, st


def missing_at_emission(r: dict, objects=None) -> Optional[set[str]]:
    """The inputs missing when the row was emitted, or None: nothing recorded."""
    mi = _loads(r.get("missing_inputs"))
    ob = from_object(objects(str(r["emitted_at"]))) if objects else None
    if mi is None and ob is None:
        return None
    return set(mi or []) | (ob or set())


def brier(r: dict) -> float:
    b = r.get("brier")
    return float(b) if b is not None else (float(r["probability"]) - int(r["outcome"])) ** 2


# ---------------------------------------------------------------------------
# The statistic
# ---------------------------------------------------------------------------
def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def _pct(xs: list[float], q: float) -> float:
    """The q-th quantile by linear interpolation between order statistics."""
    s = sorted(xs)
    i = q * (len(s) - 1)
    lo = int(i)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def bootstrap(miss: list[float], had: list[float], name: str,
              resamples: int = RESAMPLES, seed: int = SEED) -> tuple[float, float]:
    """The percentile interval of mean(miss) - mean(had), each side resampled
    with replacement, from a generator seeded by `seed` and the entry's name.
    Each side is sorted first, so the rows' storage order cannot move it."""
    rng = random.Random(f"{seed}|{name}")
    miss, had = sorted(miss), sorted(had)
    nm, nh = len(miss), len(had)
    diffs = []
    for _ in range(resamples):
        a = sum(miss[rng.randrange(nm)] for _ in range(nm)) / nm
        b = sum(had[rng.randrange(nh)] for _ in range(nh)) / nh
        diffs.append(a - b)
    tail = (1.0 - LEVEL) / 2.0
    return _pct(diffs, tail), _pct(diffs, 1.0 - tail)


def entries(rows: list[dict], objects=None, floor: int = FLOOR,
            resamples: int = RESAMPLES, seed: int = SEED) -> dict:
    """{entries, recorded, unrecorded, by_cell}: one entry per (family, bucket,
    input) missing anywhere in its cell."""
    cells: dict[tuple[str, str], list[tuple[float, set[str]]]] = {}
    unrecorded = 0
    for r in rows:
        miss = missing_at_emission(r, objects)
        if miss is None:
            unrecorded += 1
            continue
        k = (dq.family(r["source"]), dq.bucket(r["emitted_at"], r["horizon_date"]))
        cells.setdefault(k, []).append((brier(r), miss))
    out = []
    for (fam, hb), xs in sorted(cells.items()):
        inputs = sorted(set().union(*(m for _, m in xs)))
        for x in inputs:
            a = [b for b, m in xs if x in m]
            h = [b for b, m in xs if x not in m]
            e: dict[str, Any] = {
                "input": x, "family": fam, "horizon": hb, "n_missing": len(a),
                "n_had": len(h), "n_cell": len(xs), "share": len(a) / len(xs),
                "brier_missing": _mean(a), "brier_had": _mean(h) if h else None,
                "diff": None, "lo": None, "hi": None,
                "accruing": len(a) < floor, "comparable": bool(h)}
            if h:
                e["diff"] = e["brier_missing"] - e["brier_had"]
                if not e["accruing"]:
                    e["lo"], e["hi"] = bootstrap(a, h, f"{fam}|{hb}|{x}",
                                                 resamples, seed)
            out.append(e)
    return {"entries": out, "unrecorded": unrecorded,
            "recorded": sum(len(v) for v in cells.values()),
            "cells": {f"{k[0]}|{k[1]}": len(v) for k, v in sorted(cells.items())}}


def ranked(es: list[dict]) -> list[dict]:
    """Ranked: past the floor and comparable, by the Brier difference, largest
    first; ties by the interval's lower end, then by rows affected."""
    ok = [e for e in es if not e["accruing"] and e["comparable"]]
    return sorted(ok, key=lambda e: (-e["diff"], -e["lo"], -e["n_missing"], e["input"]))


def corpus_counts(db: Optional[str] = None, corpus: Optional[list[dict]] = None
                  ) -> dict[str, int]:
    """input -> stored misses that recorded it missing at emission."""
    if corpus is None:
        from . import error_corpus                              # noqa: PLC0415
        corpus = error_corpus.rows(db)
    out: dict[str, int] = {}
    for c in corpus:
        names = set(_loads(c.get("missing_inputs")) or [])
        names |= set(_loads(c.get("absent_dimensions")) or [])
        names |= {f"leg:{x}" for x in _loads(c.get("awaiting_legs")) or []}
        for x in names:
            out[x] = out.get(x, 0) + 1
    return out


def build(as_of: Optional[str] = None, db: Optional[str] = None,
          objects: Any = True, floor: int = FLOOR, corpus: Optional[list[dict]] = None
          ) -> dict:
    """Everything, as of an instant. `objects`: True reads the market-state
    object held at each emission from the store; False reads none; a callable
    is used as given (the gate's fixture)."""
    as_of = as_of or dq._now()
    rows = dq.resolved_rows(as_of, db)
    st = None
    if objects is True:
        try:
            objects, st = object_reader(db) if rows else (None, None)
        except FileNotFoundError:
            objects = None
    try:
        b = entries(rows, objects or None, floor)
    finally:
        if st is not None:
            st.close()
    if corpus is None:
        from . import error_corpus                              # noqa: PLC0415
        corpus = error_corpus.rows(db)
    cc = corpus_counts(db, corpus)
    for e in b["entries"]:
        e["corpus_misses"] = cc.get(e["input"], 0)
    b.update(as_of=as_of, method=METHOD, floor=floor, resamples=RESAMPLES,
             seed=SEED, level=LEVEL, rows=len(rows), ranked=ranked(b["entries"]),
             corpus_rows=len(corpus))
    return b


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------
def _e(e: dict) -> str:
    return (f"{e['diff']:+.4f} [{e['lo']:+.4f}, {e['hi']:+.4f}]"
            if e["lo"] is not None else
            (f"{e['diff']:+.4f}" if e["diff"] is not None else "no row had it"))


def tables_md(b: dict) -> list[str]:
    out = [f"Resolved ledger rows: {b['rows']} ({b['recorded']} with what was "
           f"missing recorded, {b['unrecorded']} unrecorded and not compared). "
           f"The difference is the mean Brier of the rows missing the input less "
           f"that of the rows that had it, in the same family and horizon: "
           f"positive means the absence cost accuracy. The interval is a "
           f"{int(100 * b['level'])}% percentile bootstrap ({b['resamples']} "
           f"resamples, seed {b['seed']}). An input is ranked from "
           f"{b['floor']} affected rows.", "",
           "| Rank | Input | Family | Horizon | Rows missing | Rows had | Share "
           "| Brier difference [interval] | Misses in the corpus |",
           "|---:|---|---|---|---:|---:|---:|---|---:|"]
    if not b["ranked"]:
        out.append("| – | (none ranked) | | | | | | no input has "
                   f"{b['floor']} affected rows with a comparison | |")
    for i, e in enumerate(b["ranked"], 1):
        out.append(f"| {i} | {e['input']} | {e['family']} | {e['horizon']} | "
                   f"{e['n_missing']} | {e['n_had']} | {100 * e['share']:.0f}% | "
                   f"{_e(e)} | {e['corpus_misses']} |")
    acc = [e for e in b["entries"] if e["accruing"] or not e["comparable"]]
    if acc:
        out += ["", "Accruing or without a comparison (not ranked): " + "; ".join(
            f"{e['input']} in {e['family']} {e['horizon']} "
            + (f"(accruing, n={e['n_missing']} of {b['floor']})" if e["accruing"]
               else f"(n={e['n_missing']}; every row missed it)")
            for e in acc) + "."]
    return out + [""]


def head_line(b: dict) -> str:
    top = b["ranked"][:3]
    if not top:
        return (f"Value of information (as of {b['as_of'][:10]}): no missing input "
                f"has {b['floor']} affected rows yet, so there is no search order.")
    return (f"Value of information (as of {b['as_of'][:10]}; computed from the "
            f"stored rows, never written by a model): the search order begins "
            + "; ".join(f"{i}. {e['input']} ({e['family']} {e['horizon']}, "
                        f"{_e(e)}, n={e['n_missing']})" for i, e in enumerate(top, 1))
            + ".")


def lab_section(as_of: Optional[str] = None, db: Optional[str] = None) -> str:
    """The Monthly's Lab report section."""
    b = build(as_of, db)
    return "\n".join(["## Value of information (Learning Loop v2, LL-2)", "",
                      f"**{head_line(b)}**", ""] + tables_md(b))


def with_lab_report(lab: Optional[tuple[str, str, str]], stamp: str,
                    db: Optional[str] = None) -> Optional[tuple[str, str, str]]:
    """The Monthly's hook, after decision quality's: the Lab report attachment
    with this section appended, or the section alone. Never raises."""
    try:
        sec = lab_section(None, db)
    except Exception:                                         # noqa: BLE001
        return lab
    if lab:
        name, md, kind = lab
        return (name, md.rstrip() + "\n\n" + sec, kind)
    return (f"value_of_information_{str(stamp)[:7]}.md", sec, "markdown")


def pack_md(as_of: Optional[str] = None, db: Optional[str] = None,
            objects: Any = True) -> str:
    """The Doctrine sitting pack's section."""
    b = build(as_of, db, objects)
    return "\n".join([
        "## Value of information: the search order (LL-2)", "",
        f"**As built.** `altdata/value_of_information.py` ({METHOD}), as of "
        f"{b['as_of'][:10]}: computed at read from the stored ledger, the objects "
        f"held at each emission and the error corpus. Report only: the order is "
        f"the operator's to adopt.", "",
        f"**The line.** {head_line(b)}", ""] + tables_md(b))


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.value_of_information")
    ap.add_argument("what", choices=("list", "pack", "json"))
    ap.add_argument("--as-of")
    ap.add_argument("--db")
    ap.add_argument("--no-objects", action="store_true",
                    help="read only the rows' own missing_inputs, not the objects")
    a = ap.parse_args(argv)
    objects = not a.no_objects
    if a.what == "pack":
        print(pack_md(a.as_of, a.db, objects))
        return 0
    b = build(a.as_of, a.db, objects)
    if a.what == "list":
        print(head_line(b))
        print("\n".join(tables_md(b)))
    else:
        print(json.dumps(b, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

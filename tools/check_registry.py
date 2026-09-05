"""
Registry gate: no metric feeds a decision without a registry entry.

One check, run in CI. It exists because a registry nobody validates is a
document, not a control -- it drifts the first time someone adds a column, and
the drift is invisible until a decision is made on an unregistered number.

WHAT IT ENFORCES

  1. Every field the code emits is accounted for. A field in the exposure
     profile or the pin log must be a registered metric, a member of a bulk
     import, a declared non-metric, or reserved. Anything else fails. This is
     the drift check and it is the one that will actually fire: adding a column
     without a registry line breaks the build.

  2. Every metric names a source that exists in source_registry.yaml, and
     every source declares a tier and a timestamp reliability from the
     vocabulary.

  3. Every metric's mechanism_group, native_horizon and units come from the
     declared vocabularies. A typo is a new category otherwise, and a new
     category silently becomes a second confluence cluster -- which is exactly
     the double-counting architecture 26.9 forbids.

  4. THE DECISION RULE. Nothing may be trigger_eligible without a complete
     entry: a source, a mechanism group, a native horizon, units, and a written
     rationale. Trigger eligibility is the thing that lets a metric move money,
     so it is the one field that may not be acquired by default.

  5. Bulk imports resolve. `members_from` must import, and the member count
     must match what the block declares -- so a series added to config without
     a registry note is caught here rather than in a report.

WHAT IT DOES NOT DO. It does not check that a metric is correct, useful, or
well-calibrated. It checks that it is DECLARED. Everything else in this repo is
where correctness is argued.

Usage:
    python tools/check_registry.py            # exit 0 clean, 1 on any failure
    python tools/check_registry.py --verbose
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO = Path(__file__).resolve().parent.parent
METRICS_PATH = REPO / "metrics_registry.yaml"
SOURCES_PATH = REPO / "source_registry.yaml"

REQUIRED_FOR_TRIGGER = ("source", "mechanism_group", "native_horizon", "units")


class Failures:
    """Collects every failure rather than stopping at the first.

    A gate that reports one problem per run makes fixing five problems take
    five runs, and CI runs are the slowest feedback loop anyone has.
    """

    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, check: str, detail: str) -> None:
        self.items.append((check, detail))

    def __bool__(self) -> bool:
        return bool(self.items)


def load_yaml(path: Path):
    import yaml
    with path.open(encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def resolve_members(spec: str, key_attr: str | None = None) -> list:
    """Resolve `members_from: package.module.ATTRIBUTE` to its members."""
    module_path, _, attr = spec.rpartition(".")
    mod = importlib.import_module(module_path)
    obj = getattr(mod, attr)
    if key_attr:
        return [getattr(m, key_attr) for m in obj]
    return list(obj)


def emitted_fields() -> dict[str, set[str]]:
    """Every field name the code actually emits, by surface.

    Read from the code, not from a fixture: the point is to catch the code
    growing a field the registry has not heard of.
    """
    import exposure_compute as ec
    import pin_log

    out: dict[str, set[str]] = {}
    out["pin_log"] = set(pin_log.PIN_COLUMNS)

    # Exposure surface, unioned across BOTH shapes a profile can take: a
    # computed one and a deferred one (the vendor symbols, whose Greeks are
    # gated). Sampling only whichever happens to be newest would let the other
    # shape's fields drift unregistered -- and on any day the vendor capture
    # ran last, that is the shape a naive sample would find.
    fields: set[str] = set()
    seen_computed = seen_deferred = False

    def absorb(prof: dict) -> None:
        nonlocal seen_computed, seen_deferred
        fields.update(k for k in prof if k != "per_strike")
        for key in ("overall", "quality", "gates"):
            fields.update(prof.get(key) or {})
        for bucket in (prof.get("buckets") or {}).values():
            fields.update(bucket)
        for rel in (prof.get("expiration_release") or [])[:1]:
            fields.update(rel)
        for strike in (prof.get("per_strike") or [])[:1]:
            fields.update(strike)
        if prof.get("error"):
            seen_deferred = True
        else:
            seen_computed = True

    root = Path(ec.config.CHAIN_DIR)
    days = sorted((p for p in root.iterdir() if p.is_dir()), reverse=True) \
        if root.exists() else []
    for day in days:
        for sym, path in ec.newest_chains(day.name).items():
            if seen_computed and seen_deferred:
                break
            prof = ec.compute_symbol(ec.load_chain(path), sym)
            if (prof.get("error") and not seen_deferred) or \
               (not prof.get("error") and not seen_computed):
                absorb(prof)
        if seen_computed and seen_deferred:
            break

    # data/ is gitignored, so CI has no chains and the drift check above would
    # find nothing and pass vacuously -- which is the one outcome a gate must
    # never have. Fall back to a synthetic chain: same engine, same code path,
    # enough shape to emit every field. smoke_test.py uses the same trick for
    # the same reason.
    for prof in _synthetic_profiles(ec, need_computed=not seen_computed,
                                    need_deferred=not seen_deferred):
        absorb(prof)

    out["exposure"] = fields
    return out


def _synthetic_profiles(ec, need_computed: bool, need_deferred: bool) -> list[dict]:
    """Minimal chains that still exercise every branch of the profile.

    Two expiries so a bucket other than 0DTE exists, 0DTE present so the
    settlement branch runs, calls and puts at several strikes so the walls and
    the flip have something to find.
    """
    if not (need_computed or need_deferred):
        return []
    fetched = "2026-09-04T20:10:00+00:00"      # after the close: a settled capture
    spot = 100.0
    rows = []
    for expiry, dte in (("2026-09-04", 0), ("2026-09-11", 7), ("2026-10-16", 42)):
        for strike in (90.0, 95.0, 100.0, 105.0, 110.0):
            for right in ("C", "P"):
                rows.append({
                    "symbol": "SYN", "fetched_at": fetched, "spot": spot,
                    "expiry": expiry, "dte": dte, "right": right,
                    "strike": strike, "open_interest": 1000.0,
                    "implied_vol": 0.25, "volume": 100.0,
                    "bid": 1.0, "ask": 1.1, "gamma": None,
                    "greeks_status": None, "vendor": None, "spot_source": None,
                })
    out = []
    if need_computed:
        out.append(ec.compute_symbol([dict(r) for r in rows], "SYN"))
    if need_deferred:
        out.append(ec.compute_symbol(
            [{**r, "greeks_status": "pending_solver_gate"} for r in rows], "SYN"))
    return out


def registry_coverage(metrics: dict) -> set[str]:
    """Every field name the metrics registry accounts for, however declared."""
    covered: set[str] = set()

    # Registered metrics: the leaf of a dotted id is the emitted field name.
    for mid in (metrics.get("metrics") or {}):
        covered.add(mid.rsplit(".", 1)[-1])

    for block in (metrics.get("bulk_imports") or {}).values():
        spec = block.get("members_from")
        if spec:
            try:
                covered |= set(resolve_members(spec, block.get("member_key")))
            except Exception:  # noqa: BLE001 -- reported separately in check 5
                pass

    for group in (metrics.get("non_metrics") or {}).values():
        covered |= set(group or [])

    covered |= set((metrics.get("reserved") or {}).get("members") or [])
    return covered


def main() -> int:
    ap = argparse.ArgumentParser(description="Registry gate")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    f = Failures()
    metrics = load_yaml(METRICS_PATH)
    sources = load_yaml(SOURCES_PATH)

    src = sources.get("sources") or {}
    svocab = sources.get("vocabularies") or {}
    mvocab = metrics.get("vocabularies") or {}
    defaults = metrics.get("defaults") or {}
    entries = metrics.get("metrics") or {}
    bulk = metrics.get("bulk_imports") or {}

    # --- 2/3/4: per-metric declarations ----------------------------------
    for mid, m in entries.items():
        m = m or {}
        if m.get("source") not in src:
            f.add("source resolves", f"{mid}: source {m.get('source')!r} not in source_registry")
        mg = m.get("mechanism_group")
        if mg not in (mvocab.get("mechanism_group") or []):
            f.add("mechanism_group vocabulary", f"{mid}: {mg!r}")
        nh = m.get("native_horizon")
        if nh not in (mvocab.get("native_horizon") or []):
            f.add("native_horizon vocabulary", f"{mid}: {nh!r}")
        u = m.get("units")
        if u not in (mvocab.get("units") or []):
            f.add("units vocabulary", f"{mid}: {u!r}")

        # THE DECISION RULE.
        eligible = m.get("trigger_eligible", defaults.get("trigger_eligible", False))
        if eligible:
            missing = [k for k in REQUIRED_FOR_TRIGGER if not m.get(k)]
            if missing:
                f.add("trigger_eligible completeness",
                      f"{mid}: trigger_eligible with no {', '.join(missing)}")
            if not (m.get("rationale") or m.get("description")):
                f.add("trigger_eligible completeness",
                      f"{mid}: trigger_eligible with no written rationale")

    # --- sources -----------------------------------------------------------
    for sid, s in src.items():
        s = s or {}
        if s.get("tier") not in (svocab.get("tier") or []):
            f.add("source tier vocabulary", f"{sid}: {s.get('tier')!r}")
        tr = s.get("timestamp_reliability")
        if tr not in (svocab.get("timestamp_reliability") or []) and tr != "inherits":
            f.add("timestamp_reliability vocabulary", f"{sid}: {tr!r}")

    # --- 5: bulk imports resolve ------------------------------------------
    for bid, block in bulk.items():
        block = block or {}
        spec = block.get("members_from")
        if not spec:
            f.add("bulk import", f"{bid}: no members_from")
            continue
        try:
            members = resolve_members(spec, block.get("member_key"))
        except Exception as e:  # noqa: BLE001
            f.add("bulk import resolves", f"{bid}: {spec} -> {type(e).__name__}: {e}")
            continue
        expected = block.get("expected_members")
        if expected is not None and len(members) != expected:
            f.add("bulk import count",
                  f"{bid}: {spec} has {len(members)}, registry says {expected}. "
                  f"Update the registry deliberately -- this is the drift check.")
        if block.get("source") not in src:
            f.add("source resolves", f"{bid}: source {block.get('source')!r} unknown")

    # --- 1: drift ----------------------------------------------------------
    covered = registry_coverage(metrics)
    emitted = emitted_fields()
    for surface, fields in emitted.items():
        unknown = sorted(fields - covered)
        if unknown:
            f.add("no unregistered field",
                  f"{surface}: {len(unknown)} unregistered -> {', '.join(unknown[:12])}"
                  + (" ..." if len(unknown) > 12 else ""))

    # --- report ------------------------------------------------------------
    line = "=" * 74
    print(f"{line}\nRegistry gate\n{line}")
    n_bulk = sum(len(resolve_members(b["members_from"], b.get("member_key")))
                 for b in bulk.values() if b.get("members_from"))
    print(f"  metrics registered   : {len(entries)}")
    print(f"  bulk-import members  : {n_bulk} across {len(bulk)} block(s)")
    print(f"  sources registered   : {len(src)}")
    print(f"  trigger_eligible     : "
          f"{sum(1 for m in entries.values() if (m or {}).get('trigger_eligible'))}"
          f"  (default {defaults.get('trigger_eligible')})")
    for surface, fields in sorted(emitted.items()):
        print(f"  {surface + ' fields':<21}: {len(fields)} emitted, "
              f"{len(fields - covered)} unregistered")
    if args.verbose:
        for surface, fields in sorted(emitted.items()):
            print(f"\n  {surface}: {', '.join(sorted(fields))}")

    if not f:
        print(f"\n  OK -- every emitted field is declared, every metric names a "
              f"known source,\n       and nothing is trigger-eligible without a "
              f"complete entry.\n{line}")
        return 0

    print(f"\n  {len(f.items)} FAILURE(S)")
    for check, detail in f.items:
        print(f"    [{check}] {detail}")
    print(f"\n  A new field is not a bug. An UNDECLARED one is: add it to "
          f"metrics_registry.yaml\n  as a metric, a bulk member, or a "
          f"non-metric, and say which it is.\n{line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

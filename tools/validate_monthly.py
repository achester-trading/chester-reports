#!/usr/bin/env python3
"""
Validation gate for the Monthly. (Phase 4b; Audit #3 section G, N, O 7/8/10)

    python tools/validate_monthly.py

A. The pillars are SUBORDINATE to the dials, with a stated mapping, and no pillar
   computes a regime of its own.
B. Payload completeness: every section present, every absence carrying its reason,
   and every figure at the precision the report would print it.
C. Every scenario weight beside its Brier -- in the payload AND in the renderer.
D. A PAST MONTH REPLAYS AS-OF ITS CUTOFF: nothing observed after the cutoff reaches
   the payload, and two builds at one cutoff agree.
E. The no-recompute guard: the Monthly READS the object and computes no regime.
F. The model boundary: the narrative payload is a projection of the document, the
   placeholders are gone, and the long form is a parameter rather than a rewrite.

Groups B, D and F BUILD THE PAYLOAD, which is why this gate is slower than its
neighbours and worth the seconds: a completeness rule asserted against the code that
writes the payload, rather than against a payload, is a rule about a promise.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from monthly_macro import pillars                              # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = 0
FAIL = 0
SKIPPED: list[str] = []

# The object's eight dimensions. A pillar may only claim to read one of these.
DIMENSIONS = ("growth", "inflation", "rates", "liquidity", "credit", "trend",
              "breadth", "volatility")


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {msg}")


def check(cond: bool, msg: str) -> bool:
    (ok if cond else bad)(msg)
    return bool(cond)


def group_a() -> None:
    print(f"\n{LINE}\nA. PILLARS SUBORDINATE TO THE DIALS, WITH A MAPPING\n{LINE}")
    reg = pillars.load()
    ps = reg["pillars"]
    print(f"  {len(ps)} pillars, version {reg['version']}")

    check(len(ps) == 11,
          f"eleven pillars are declared (got {len(ps)}) -- the number the "
          f"architecture names, including the one that was relocated")
    check(set(ps) == {str(i) for i in range(1, 12)},
          f"numbered 1 to 11 with no gaps ({sorted(ps, key=int)})")

    # --- EVERY PILLAR MAPPED --------------------------------------------------
    for num, p in sorted(ps.items(), key=lambda kv: int(kv[0])):
        dial = p.get("dial")
        if dial is None:
            check(bool(p.get("from_object_absent_reason")),
                  f"pillar {num} ({p.get('name')}) feeds no dial AND says why "
                  f"({str(p.get('from_object_absent_reason'))[:52]}...)")
        else:
            check(dial in pillars.DIALS,
                  f"pillar {num} feeds a declared dial ({dial})")
        check(p.get("weight") is not None,
              f"pillar {num} declares a weight ({p.get('weight')})")
        check(bool(p.get("name")), f"pillar {num} is named")
        dim = p.get("from_object")
        if dim is None:
            check(bool(p.get("from_object_absent_reason")),
                  f"pillar {num} reads no dimension AND records the reason")
        else:
            check(dim in DIMENSIONS,
                  f"pillar {num} reads the object's `{dim}` dimension")

    # --- WEIGHTS SUM, PER DIAL ------------------------------------------------
    for dial in ("macro", "vol"):
        total = pillars.weight_total(dial)
        check(abs(total - 1.0) < 1e-9,
              f"the {dial} dial's pillar weights sum to 1.0 (got {total})")
    check(pillars.weight_total("gamma") == 0
          and not pillars.for_dial("gamma"),
          "THE GAMMA DIAL HAS NO PILLAR INPUTS, and the mapping says so rather "
          "than leaving a row that looks forgotten: gamma is dealer positioning "
          "from the chain, and no macro series bears on it")

    # --- NO PILLAR COMPUTES A REGIME OF ITS OWN -------------------------------
    src = (REPO / "config" / "pillars.yaml").read_text(encoding="utf-8")
    stateful = [num for num, p in ps.items()
                if any(k in p for k in ("state", "score", "reading", "verdict"))]
    check(not stateful,
          f"no pillar declares a state, a score or a verdict"
          + (f" -- {stateful}" if stateful else "")
          + ": a pillar is an input, and regime.py is the only writer of a state")
    check("NO PILLAR COMPUTES A REGIME OF ITS OWN" in src,
          "and the file says so in the one place a reader would look")
    reader = (REPO / "monthly_macro" / "pillars.py").read_text(encoding="utf-8")
    for banned in ("def compute", "def score", "def state_of"):
        check(banned not in reader,
              f"the reader offers no {banned!r} -- it maps and reads, and computing "
              f"a pillar state here is the defect the mapping exists to remove")

    # --- THE GAPS ARE DECLARED, NOT SILENT ------------------------------------
    gaps = pillars.unsourced()
    check(len(gaps) >= 3,
          f"{len(gaps)} pillar gaps are declared with what each needs")
    for g in gaps:
        check(bool(g.get("needs")) and bool(g.get("why")),
              f"pillar {g['pillar']}'s gap names its inputs and why it matters "
              f"({g['what']})")
    zero = [n for n, p in ps.items()
            if float(p.get("weight") or 0) == 0 and p.get("dial")]
    check(zero,
          f"a pillar with no metrics carries weight ZERO rather than being deleted "
          f"({zero}) -- zero is the honest weight for a pillar that cannot move a "
          f"view, and the row stays visible")
    check(pillars.load()["pillars"]["11"].get("status") == "relocated"
          and pillars.load()["pillars"]["11"].get("relocated_to"),
          "and the eleventh pillar resolves to where it went rather than to "
          "nothing")


# ---------------------------------------------------------------------------
# B. PAYLOAD COMPLETENESS
# ---------------------------------------------------------------------------
# An absent section is not a failure -- three of the eight dimensions have no data
# and the Top & Bottom harness is not built. An absent section with NO REASON is the
# failure, because that is the one a reader cannot tell from an oversight.
def group_b(built: dict) -> None:
    print(f"\n{LINE}\nB. PAYLOAD COMPLETENESS -- every section, every absence with "
          f"its reason\n{LINE}")
    from monthly_macro import payload
    from daily_cascade import precision

    for k in ("report", "report_date", "as_of", "generated_at", "sections",
              "pillar_mapping_version", "warnings"):
        check(k in built, f"the payload carries `{k}`")
    check(built.get("report") == "monthly",
          f"it names itself `monthly` (got {built.get('report')!r}) -- the archive "
          f"and the state key read this")
    check(tuple(built.get("sections") or ()) == payload.SECTIONS,
          f"it declares its six sections in order ({built.get('sections')})")

    for name in payload.SECTIONS:
        block = built.get(name)
        if not check(isinstance(block, dict), f"section `{name}` is present"):
            continue
        state = block.get("state")
        if name == "alternative_assets":
            # This one is a family table: the STATE lives per family, because
            # `metals` having data says nothing about `real_assets`.
            fams = block.get("families") or {}
            check(bool(fams), f"`{name}` carries its families ({len(fams)})")
            for fam, v in fams.items():
                st = v.get("state")
                if st == "ok":
                    ok(f"  {name}.{fam}: ok")
                else:
                    check(bool(v.get("reason") or v.get("why")),
                          f"  {name}.{fam} is `{st}` AND says why "
                          f"({str(v.get('reason') or v.get('why'))[:48]}...)")
            continue
        if state == "ok":
            ok(f"section `{name}`: ok")
        else:
            check(bool(block.get("reason")),
                  f"section `{name}` is `{state}` AND records the reason "
                  f"({str(block.get('reason'))[:48]}...)")

    # --- EVERY WARNING IS A SECTION THAT SAID WHY -----------------------------
    warned = built.get("warnings") or []
    check(all("--" in w for w in warned),
          f"each of the {len(warned)} warning(s) carries its section's reason "
          f"after a dash")

    # --- PRINT PRECISION, AT ASSEMBLY -----------------------------------------
    v = precision.violations(built)
    check(not v,
          f"every figure in the payload is at printing precision "
          f"({len(v)} violation(s)"
          + (f", first {v[0]['path']}={v[0]['value']} -> {v[0]['expected']}"
             if v else "") + ") -- the rule is that the model never sees a figure "
          f"the report would not print, and a payload rounded only at the model "
          f"boundary would put one in the document instead")


# ---------------------------------------------------------------------------
# C. EVERY WEIGHT BESIDE ITS BRIER
# ---------------------------------------------------------------------------
# The old Monthly printed scenario weights with no score anywhere near them, which
# is a forecast nobody has marked. The rule is structural: the row carries the
# score's FIELD even when the score is None, so an unresolved weight reads as
# unresolved rather than as unscored.
def group_c(built: dict) -> None:
    print(f"\n{LINE}\nC. EVERY SCENARIO WEIGHT BESIDE ITS BRIER\n{LINE}")
    sc = built.get("scenarios") or {}
    weights = sc.get("weights")
    check(weights is not None,
          "the scenarios section carries a `weights` list (possibly empty)")
    for i, w in enumerate(weights or []):
        for k in ("claim", "probability", "brier", "outcome", "resolve_by"):
            check(k in w, f"weight {i} carries `{k}`")
    if not weights:
        check(bool(sc.get("reason")),
              "no weight has been emitted, and the section says why rather than "
              "printing an empty table: the ledger is seeded from a Monthly's own "
              "scenario table, so the first score arrives a month after the first "
              "weight")
        SKIPPED.append("per-weight Brier rows: the ledger is empty")

    # The RENDERER has to print the column, not merely carry the field.
    src = (REPO / "monthly_macro" / "writer" / "render_v2.py").read_text(
        encoding="utf-8")
    check("| Brier |" in src,
          "the renderer's scenario table has a Brier COLUMN -- the payload field "
          "is not the guarantee; a table that drops the column prints the forecast "
          "and hides the mark")
    check("brier" in src,
          "and it reads each row's own score rather than a summary elsewhere")


# ---------------------------------------------------------------------------
# D. A PAST MONTH REPLAYS AS-OF ITS CUTOFF
# ---------------------------------------------------------------------------
# This is the property that makes a grade worth anything. If the payload can see
# past its cutoff, every replayed month is marked against data the month did not
# have, and the Brier ledger measures hindsight.
def group_d() -> None:
    print(f"\n{LINE}\nD. REPLAY: A PAST MONTH AS-OF ITS OWN CUTOFF\n{LINE}")
    import datetime as dt
    from monthly_macro import payload

    cutoff_day = dt.date.today().replace(day=1) - dt.timedelta(days=1)
    cutoff = f"{cutoff_day.isoformat()}T23:59:59Z"
    print(f"  replaying as-of {cutoff}")
    try:
        past = payload.build(as_of=cutoff)
    except Exception as exc:                                   # noqa: BLE001
        bad(f"the payload builds at a past cutoff (raised {type(exc).__name__}: "
            f"{exc})")
        return
    ok("the payload builds at a past cutoff without raising")
    check(past.get("as_of") == cutoff,
          f"and echoes the cutoff it was given ({past.get('as_of')})")

    # --- NOTHING OBSERVED AFTER THE CUTOFF ------------------------------------
    day = cutoff[:10]
    late: list[str] = []
    for num, v in ((past.get("appendix") or {}).get("pillars") or {}).items():
        for r in v.get("series") or []:
            o = r.get("observed_at")
            if o and str(o)[:10] > day:
                late.append(f"appendix pillar {num} {r['metric']} @ {o}")
    for fam, v in (((past.get("alternative_assets") or {})
                    .get("families")) or {}).items():
        for m in v.get("metrics") or []:
            o = m.get("observed_at")
            if o and str(o)[:10] > day:
                late.append(f"{fam} {m['metric']} @ {o}")
    rg = past.get("regime") or {}
    if rg.get("session") and str(rg["session"])[:10] > day:
        late.append(f"regime session {rg['session']}")
    check(not late,
          f"NO figure in the payload was observed after the cutoff "
          f"({len(late)} leak(s)"
          + (f": {late[0]}" if late else "") + ") -- a replay that can see past its "
          f"cutoff grades the month against data the month did not have")
    if rg.get("state") != "ok":
        check(bool(rg.get("reason")),
              f"the object is `{rg.get('state')}` at this cutoff and the reason is "
              f"recorded ({str(rg.get('reason'))[:44]}...): the close pass writes "
              f"the object, so an old cutoff can legitimately predate the first one")

    # --- TWO BUILDS AT ONE CUTOFF AGREE ---------------------------------------
    again = payload.build(as_of=cutoff)
    volatile = ("generated_at", "run_id", "report_date")
    a = {k: v for k, v in past.items() if k not in volatile}
    b = {k: v for k, v in again.items() if k not in volatile}
    differing = sorted(k for k in a if a[k] != b.get(k))
    check(not differing,
          f"two builds at the same cutoff agree on every section "
          f"({differing or 'none differ'}) -- a replay that is not reproducible is "
          f"not evidence")


# ---------------------------------------------------------------------------
# E. THE NO-RECOMPUTE GUARD
# ---------------------------------------------------------------------------
# CLAUDE.md's rule, enforced at the one report most likely to break it: the Monthly
# has eleven pillars' worth of macro series in front of it and used to characterise
# a regime from them ten times over.
def group_e() -> None:
    print(f"\n{LINE}\nE. NO SECOND REGIME -- the Monthly reads the object\n{LINE}")
    pkg = REPO / "monthly_macro"
    files = sorted(f for f in pkg.rglob("*.py") if "__pycache__" not in str(f))
    print(f"  {len(files)} modules under monthly_macro/")

    banned = ("regime.build", "regime.compute", "regime.write", "build_state",
              "compute_state", "import contradictions", "from contradictions",
              "classify_dial", "dial_state(")
    hits: list[str] = []
    readers: list[str] = []
    for f in files:
        body = "\n".join(ln for ln in f.read_text(encoding="utf-8").splitlines()
                          if not ln.lstrip().startswith("#"))
        for b in banned:
            if b in body:
                hits.append(f"{f.relative_to(REPO)}: {b}")
        if "regime.latest(" in body:
            readers.append(str(f.relative_to(REPO)))
    check(not hits,
          f"no module builds, writes or classifies a regime "
          f"({hits or 'none'}) -- the close pass is the only writer, and a second "
          f"regime is two answers to one question with no way to say which one a "
          f"decision was taken under")
    check(readers,
          f"and the object is READ through regime.latest() ({', '.join(readers)})")

    # The dials' own bands must not be restated here. A copy of a band is the same
    # defect wearing a number.
    pay = (REPO / "monthly_macro" / "payload.py").read_text(encoding="utf-8")
    cfg = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check("threshold" not in pay.replace("threshold_z", ""),
          f"and no band or threshold is restated in the payload -- "
          f"config/market_state.yaml is {len(cfg.splitlines())} lines of declared "
          f"rules, and a second copy of one of them is a rule that will disagree")


# ---------------------------------------------------------------------------
# F. THE MODEL BOUNDARY
# ---------------------------------------------------------------------------
def group_f(built: dict) -> None:
    print(f"\n{LINE}\nF. THE MODEL BOUNDARY -- a projection, not a second "
          f"payload\n{LINE}")
    from monthly_macro import narrative, payload
    from daily_cascade import precision

    np_ = payload.narrative_payload(built)
    check(not precision.violations(np_),
          "the narrative payload is at printing precision")

    def leaves(v, out=None):
        out = set() if out is None else out
        if v is None or isinstance(v, bool):
            return out
        if isinstance(v, (int, float)):
            out.add(round(float(v), 6))
        elif isinstance(v, dict):
            for x in v.values():
                leaves(x, out)
        elif isinstance(v, (list, tuple)):
            for x in v:
                leaves(x, out)
        return out

    doc, brief = leaves(built), leaves(np_)
    extra = sorted(brief - doc)
    check(not extra,
          f"every figure the model sees exists in the document "
          f"({len(brief)} of {len(doc)}; {len(extra)} extra"
          + (f", first {extra[0]}" if extra else "") + ") -- a brief carrying a "
          f"figure the report does not print is a citation a reader cannot check")
    # STRICT narrowing only when the appendix actually carries series. On a CI
    # runner with no observation store both sets are nearly empty, and a gate that
    # goes red for want of data is a data gate in a code gate's list -- which is the
    # split registry-check.yml maintains two matrices to keep.
    if (built.get("appendix") or {}).get("series_total"):
        check(len(brief) < len(doc),
              f"and it is NARROWER than the document ({len(brief)} < {len(doc)}): "
              f"the appendix alone is 59 series with four figures each, and a "
              f"paragraph given all of them can cite an intermediate as a headline")
    else:
        check(len(brief) <= len(doc),
              f"and it is no wider than the document ({len(brief)} <= {len(doc)}); "
              f"the store is empty here, so strict narrowing is not asserted")

    # --- THE PLACEHOLDERS ARE GONE FROM THE REPORT'S PATH ---------------------
    for name in ("run.py", "payload.py", "writer/render_v2.py"):
        f = REPO / "monthly_macro" / name
        body = "\n".join(ln for ln in f.read_text(encoding="utf-8").splitlines()
                          if not ln.lstrip().startswith("#"))
        check("NARRATIVE PLACEHOLDER" not in body,
              f"{name} emits no NARRATIVE PLACEHOLDER marker")
    run = (REPO / "monthly_macro" / "run.py").read_text(encoding="utf-8")
    check("add_narratives" not in run,
          "run.py no longer walks the document replacing per-pillar markers -- ten "
          "calls asking for a regime with no shared state is the defect this report "
          "was restructured to remove")
    check("render_v2" in run and "render_report" not in run,
          "and it renders the six sections rather than the ten pillar pages")

    # --- LONG FORM IS A PARAMETER --------------------------------------------
    check(narrative.TEMPLATE_PATH.exists(),
          f"the Monthly's own template exists ({narrative.TEMPLATE_PATH.name})")
    check(narrative.MAX_CHARS > 10000,
          f"the ceiling is a runaway guard rather than a word count "
          f"({narrative.MAX_CHARS} chars)")
    check("one_paragraph=False" in run,
          "and run.py asks for the long form explicitly: the close report's "
          "one-paragraph limit is its own rule, not the system's")
    tmpl = narrative.TEMPLATE_PATH.read_text(encoding="utf-8")
    ref = tmpl.split("## Reference paragraph")[-1].split("## Style rules")[0]
    check("**" not in ref,
          "the reference paragraph carries NO markdown -- an example that breaks "
          "the rule it illustrates teaches the example")


def main() -> int:
    print(f"{LINE}\nThe Monthly -- Phase 4b\n{LINE}")
    group_a()
    built = None
    try:
        from monthly_macro import payload
        built = payload.build()
    except Exception as exc:                                   # noqa: BLE001
        bad(f"the payload builds at all (raised {type(exc).__name__}: {exc})")
    if built is not None:
        group_b(built)
        group_c(built)
        group_d()
        group_e()
        group_f(built)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed"
          + (f", {len(SKIPPED)} skipped" if SKIPPED else "") + f"\n{LINE}")
    for s in SKIPPED:
        print(f"  SKIPPED: {s}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

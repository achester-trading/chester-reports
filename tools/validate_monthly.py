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

A CODE GATE NEVER READS THE LIVE STORE (1 Oct 2026). B-F built the payload from
whatever data/chester.db they found, so on the box the verdict was about the box's
history and in CI about an empty store. main() now points CHESTER_DB and the pin
log at a temporary database BEFORE anything opens a store, and seeds it: two
pillar series running past the replay cutoff (so D's no-leak check has something
to catch), one market-state object computed by regime.compute on them, and one
Monthly forecast in the probability ledger (so C's per-weight Brier rows exist).
The same B, C and D over the box's real history are the data gate
tools/validate_monthly_store.py.
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

    # --- THE DERIVED MACRO SERIES ARE IN THE APPENDIX -------------------------
    from altdata import market_features as mf
    macro = (built.get("appendix") or {}).get("derived_macro")
    check(macro is not None, "the appendix carries `derived_macro`")
    keys = {m.get("metric") for m in macro or []}
    missing = sorted(set(mf.MACRO_FEATURES) - keys)
    check(not missing,
          f"and all {len(mf.MACRO_FEATURES)} of them ({len(keys)} present"
          + (f", missing {missing}" if missing else "") + ") -- Sahm, the "
          f"year-over-year family, 2s10s, r-vs-g and net liquidity, which were "
          f"monthly_macro/compute.py and reached no report after it was deleted")
    for m in macro or []:
        for k in ("metric", "level", "units", "percentile", "read_by",
                  "delta_20d", "delta_unit"):
            check(k in m, f"  {m.get('metric')} carries `{k}`")
        if m.get("level") is None:
            check(bool(m.get("absent_reason")),
                  f"  {m.get('metric')} has no level AND says why")
    src = (REPO / "monthly_macro" / "writer" / "render_v2.py").read_text(
        encoding="utf-8")
    check("Derived macro series" in src and "Read by" in src,
          "the renderer prints them with the DIMENSION each one feeds -- a derived "
          "series whose reader is not named is a number in a report")

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
def group_d(live: bool = False) -> None:
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
    # NOT VACUOUS: the store DOES hold observations after the cutoff -- the
    # current build sees one -- so a clean replay means the cutoff was applied.
    now_obs = [str(r.get("observed_at"))[:10]
               for v in ((payload.build().get("appendix") or {}).get("pillars")
                         or {}).values()
               for r in v.get("series") or [] if r.get("observed_at")]
    newest = max(now_obs) if now_obs else None
    if live and not any(o > day for o in now_obs):
        # On the real store, the first days of a month hold nothing observed
        # after the previous month-end yet: a fact about the calendar, not a
        # fault. Named, so a vacuous no-leak pass is never read as a real one.
        SKIPPED.append(f"no-leak check is vacuous today: the store's newest "
                       f"pillar observation ({newest}) is not after the cutoff "
                       f"{day}; it bites once this month's first print lands")
    else:
        check(any(o > day for o in now_obs),
              f"the store holds pillar observations AFTER the cutoff (newest "
              f"{newest}), so the check below can fail")
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


# ---------------------------------------------------------------------------
# G. DELIVERY (M-1, 1 Oct 2026)
# ---------------------------------------------------------------------------
# The 1 Oct Monthly logged "built and archived (rc=0)" and reached nobody: the
# wrapper had no delivery step, and nothing could tell a delivered edition from an
# archived one. Checked without a network: SMTP is a fake that records what it was
# handed, and the credentials are patched in, so no run of this gate sends mail.
def group_g() -> None:
    print(f"\n{LINE}\nG. DELIVERY -- the Monthly reaches the inbox, or says it did not\n{LINE}")
    import contextlib
    import io
    import os
    import shutil
    import subprocess
    import tempfile
    from email import message_from_bytes
    from email.policy import default as email_default
    from daily_cascade import deliver
    from monthly_macro import run as mrun

    stamp = "2026-10-01"
    sent: list = []

    class FakeSMTP:
        fail = None

        def __init__(self, host, port, timeout=None):
            self.host = host

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            if FakeSMTP.fail:
                raise FakeSMTP.fail

        def send_message(self, msg):
            sent.append(message_from_bytes(msg.as_bytes(), policy=email_default))

    cfg = {"user": "from@example.invalid", "password": "s3cret-not-real",
           "rcpt": "to@example.invalid", "host": "smtp.example.invalid", "port": 587}
    saved = (deliver.smtp_config, deliver.smtplib.SMTP)
    deliver.smtplib.SMTP = FakeSMTP

    def run_deliver(td: str) -> tuple[dict, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = mrun.deliver_edition(stamp, td)
        return out, buf.getvalue()

    try:
        with tempfile.TemporaryDirectory() as td:
            md = "# Monthly\n\n- one figure ✓\n"
            html = "<html><body><h1>Monthly</h1></body></html>"
            Path(td, f"monthly_macro_{stamp}.md").write_text(md, encoding="utf-8")
            Path(td, f"monthly_macro_{stamp}.html").write_text(html, encoding="utf-8")

            # --- SENT ---------------------------------------------------------
            deliver.smtp_config = lambda: (cfg, [])
            out, printed = run_deliver(td)
            check(out["delivery"] == "sent" and len(sent) == 1,
                  f"configured, the archived edition is SENT once "
                  f"({out['delivery']}, {len(sent)} message)")
            m = sent[0] if sent else None
            if m is not None:
                check(m["Subject"] == f"Monthly Regime & Allocation — {stamp}",
                      f"subject is \"Monthly Regime & Allocation — <date>\" "
                      f"({m['Subject']!r})")
                body = m.get_body(preferencelist=("html",))
                check(body is not None and "<h1>Monthly</h1>" in body.get_content(),
                      "the HTML edition is the message BODY, not an attachment -- "
                      "32.3's 'a report that must be opened is read late'")
                atts = list(m.iter_attachments())
                a = atts[0] if atts else None
                check(len(atts) == 1 and a.get_filename() == f"monthly_macro_{stamp}.md"
                      and a.get_content_type() == "text/markdown"
                      and a.get_content() == md,
                      f"the Markdown is attached, byte-identical to the archive "
                      f"({[x.get_filename() for x in atts]})")
            check(printed.startswith("delivery=smtp ok "),
                  f"and one greppable line says so ({printed.strip()[:40]}...)")

            # --- NOT CONFIGURED ------------------------------------------------
            deliver.smtp_config = lambda: (None, ["SMTP_USER"])
            out, printed = run_deliver(td)
            check(out["delivery"] == "not_configured" and len(sent) == 1
                  and printed.startswith("delivery=smtp failed state=not_configured"),
                  f"no credentials -> not_configured, nothing sent, and the line "
                  f"says FAILED rather than nothing ({printed.strip()[:60]})")

            # --- SEND FAILED -----------------------------------------------------
            deliver.smtp_config = lambda: (cfg, [])
            FakeSMTP.fail = RuntimeError("535 auth rejected for s3cret-not-real")
            try:
                out, printed = run_deliver(td)
            except Exception as exc:                           # noqa: BLE001
                out, printed = {"delivery": f"RAISED {type(exc).__name__}"}, ""
            FakeSMTP.fail = None
            check(out["delivery"] == "send_failed"
                  and printed.startswith("delivery=smtp failed state=send_failed"),
                  f"an SMTP error is send_failed and never raises ({out['delivery']})")
            check("s3cret-not-real" not in printed
                  and "s3cret-not-real" not in str(out.get("delivery_detail")),
                  "and the password the server quoted back is redacted")

            # --- THE EXIT CODE ---------------------------------------------------
            argv = sys.argv
            try:
                sys.argv = ["run", "--deliver-only", stamp, "--out-dir", td]
                with contextlib.redirect_stdout(io.StringIO()):
                    rc_ok = mrun.main()
                    deliver.smtp_config = lambda: (None, ["SMTP_USER"])
                    rc_bad = mrun.main()
            finally:
                sys.argv = argv
            check(rc_ok == 0 and rc_bad == 2,
                  f"--deliver-only exits 0 when sent and 2 when not (got {rc_ok}, "
                  f"{rc_bad}) -- the Weekly's codes: built-and-archived-but-not-"
                  f"delivered is 2, never a build failure")

        with tempfile.TemporaryDirectory() as empty:
            deliver.smtp_config = lambda: (cfg, [])
            before = len(sent)
            out, printed = run_deliver(empty)
            check(out["delivery"] == "archive_missing" and len(sent) == before,
                  "an edition that was never archived is not sent, and says why")
    finally:
        deliver.smtp_config, deliver.smtplib.SMTP = saved

    # --- THE PATHS THAT MUST NOT SEND --------------------------------------------
    wf = (REPO / ".github" / "workflows" / "monthly-report.yml").read_text(
        encoding="utf-8")
    check("monthly_macro.run --verbose --no-deliver" in wf,
          "the GitHub fallback passes --no-deliver: that runner has no SMTP, "
          "and a not_configured rc=2 would fail the workflow that uploads the "
          "artifact")

    # --- THE WRAPPER: rc=2 is not_delivered, and the heartbeat is stamped -----
    if not (shutil.which("bash") and shutil.which("flock")):
        SKIPPED.append("run_monthly.sh rc mapping: no bash+flock on this machine")
        return
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "repo").mkdir()
        subprocess.run(["git", "init", "-q", str(t / "repo")], check=True)
        stub = t / "py"
        stub.write_text("#!/usr/bin/env bash\necho 'delivery=smtp failed "
                        "state=not_configured -- stub'\nexit \"${STUB_RC:-0}\"\n")
        stub.chmod(0o755)
        for rc, want_state, want_delivery, stamped in (
                (2, "not_delivered", "smtp_failed", True),
                (0, "ok", "smtp_ok", True),
                (1, "failed", "none", False)):
            st = t / f"state{rc}"
            env = {**os.environ, "CHESTER_REPO": str(t / "repo"),
                   "CHESTER_LOG_DIR": str(t / "logs"), "CHESTER_STATE_DIR": str(st),
                   "CHESTER_PYTHON": str(stub), "STUB_RC": str(rc)}
            r = subprocess.run(["bash", str(REPO / "scripts" / "run_monthly.sh")],
                               env=env, capture_output=True, text=True)
            status = (st / "monthly_status").read_text() if (st / "monthly_status").exists() else ""
            hb = st / "monthly_heartbeat"
            check(r.returncode == rc and f"state={want_state} " in status
                  and f"delivery={want_delivery} " in status
                  and hb.exists() == stamped
                  and (not stamped or hb.read_text().startswith(want_state + " ")),
                  f"run_monthly.sh rc={rc}: state={want_state}, "
                  f"delivery={want_delivery}, heartbeat "
                  f"{'stamped ' + want_state if stamped else 'NOT stamped'} "
                  f"(got rc {r.returncode}; {status.strip()[:70]})")
        log_text = "".join(p.read_text() for p in (t / "logs").glob("*.log"))
        check("delivery=smtp failed" in log_text and "delivery=smtp ok" in log_text,
              "and the log carries a delivery=smtp ok|failed line per run")
        check("built, archived and delivered" in log_text
              and "re-delivered (no build)" not in log_text,
              "a full run says built, archived and delivered")
        for p in (t / "logs").glob("*.log"):
            p.unlink()
        env = {**os.environ, "CHESTER_REPO": str(t / "repo"),
               "CHESTER_LOG_DIR": str(t / "logs"), "CHESTER_STATE_DIR": str(t / "rs"),
               "CHESTER_PYTHON": str(stub), "STUB_RC": "0",
               "CHESTER_MONTHLY_DELIVER_ONLY": "2026-10-01"}
        subprocess.run(["bash", str(REPO / "scripts" / "run_monthly.sh")],
                       env=env, capture_output=True, text=True)
        log_text = "".join(p.read_text() for p in (t / "logs").glob("*.log"))
        check("re-delivered (no build)" in log_text
              and "built, archived and delivered" not in log_text,
              "and a CHESTER_MONTHLY_DELIVER_ONLY re-send says re-delivered (no "
              "build) -- never that it built a second edition")


# ---------------------------------------------------------------------------
# H. MONTHLY v2, PHASE A (brief 2026-10-01)
# ---------------------------------------------------------------------------
# The brief's three gates: a fixture month renders ALL sections; a theme item
# without a source is REFUSED; "What changed" is COMPUTED. The fixture month is a
# database of its own -- two market-state objects a month apart with credit at
# opposite poles, a story opened in the window with two tier-1 headlines and an
# evaluation that moved it, a CPI release, a scheduled FOMC and a live forecast --
# so every item kind and every tag path has something to print.
def group_h() -> None:
    print(f"\n{LINE}\nH. MONTHLY v2 PHASE A -- a fixture month, the tag rules, a "
          f"computed What changed\n{LINE}")
    import datetime as dt
    import json
    import sqlite3
    import tempfile
    from altdata import events, narratives, observations, probability_ledger
    from monthly_macro import payload, v2
    from monthly_macro.writer import render_v2
    from register import store as register_store
    import regime

    # --- THE TAG RULES, item by item -------------------------------------------
    win = ("2026-09-01", "2026-10-01T21:00:00+00:00")
    t1 = [v2.src("event", 1, "2026-09-20", title="a - Reuters", tier=1),
          v2.src("event", 2, "2026-09-21", title="b - Bloomberg.com", tier=1)]
    cases = (
        ("a theme item WITHOUT A SOURCE", {"tag": "NEW", "sources": []}, False),
        ("a source with no id or date", {"tag": "NEW",
                                         "sources": [{"kind": "event"}]}, False),
        ("CONSENSUS on one tier-1 source", {"tag": "CONSENSUS",
                                            "sources": t1[:1]}, False),
        ("CONSENSUS on two tier-1 sources", {"tag": "CONSENSUS",
                                             "sources": t1}, True),
        ("CONSENSUS on two tier-3 sources", {"tag": "CONSENSUS", "sources": [
            {**t1[0], "tier": 3}, {**t1[1], "tier": 3}]}, False),
        ("DISSENT that names nobody", {"tag": "DISSENT", "sources": [
            v2.src("object", "market_state@x", "2026-09-20")]}, False),
        ("DISSENT naming its source", {"tag": "DISSENT", "sources": t1[:1]}, True),
        ("CORRECTION with nothing it corrects", {"tag": "CORRECTION",
                                                  "sources": t1[:1]}, False),
        ("CORRECTION citing the prior statement", {
            "tag": "CORRECTION", "sources": t1[:1],
            "corrects": {"id": "market_state@2026-09-01", "date": "2026-09-01",
                         "statement": "credit read easy"}}, True),
        ("NEW dated outside the window", {"tag": "NEW", "sources": [
            v2.src("event", 9, "2026-08-15")]}, False),
        ("an unknown tag", {"tag": "BULLISH", "sources": t1}, False),
    )
    for label, item, admit in cases:
        why = v2.check_item(item, win)
        check((why is None) == admit,
              f"{label}: {'admitted' if admit else 'REFUSED'}"
              + (f" ({why[:60]})" if why else ""))
    ok_, refused = v2._admit([{"tag": "NEW", "sources": [], "text": "x"}], win)
    check(not ok_ and refused and refused[0].get("refused_because"),
          "and _admit keeps a refused item WITH its reason, never printing it")

    # --- THE FIXTURE MONTH --------------------------------------------------------
    td = tempfile.mkdtemp(prefix="monthly_v2_fixture_")
    db = str(Path(td) / "fixture.db")
    saved = (observations.DEFAULT_DB, register_store.DEFAULT_DB,
             payload.previous_monthly)
    try:
        observations.DEFAULT_DB = register_store.DEFAULT_DB = db
        today = dt.date.fromisoformat(
            __import__("altdata").session.session_date())
        prev = (today - dt.timedelta(days=30)).isoformat()
        mid = (today - dt.timedelta(days=12)).isoformat()
        nxt = (today + dt.timedelta(days=20)).isoformat()
        payload.previous_monthly = lambda as_of=None: prev
        now_iso = __import__("altdata").session.utc_iso()

        # Today's object knowable FIVE MINUTES AGO: stamped at 21:00 UTC it would
        # be in the future before the close, and the build would read last
        # month's object as "now" and find nothing changed.
        seen = (dt.datetime.now(dt.timezone.utc)
                - dt.timedelta(minutes=5)).isoformat()
        with observations.ObservationStore(db) as st:
            for day, credit, at in ((prev, "easy", f"{prev}T21:00:00+00:00"),
                                    (today.isoformat(), "stressed", seen)):
                regime.store_object({
                    "session": day, "computed_at": at,
                    "config_version": "fixture", "method_version": "fixture",
                    "dials": {"macro": {"state": "calm" if credit == "easy"
                                        else "mixed"}},
                    "dimensions": {"credit": {"state": credit, "percentile": 12.0,
                                              "members": []}},
                    "contradictions": []}, st)
        nr = narratives.NarrativeRegister(db)
        nr.conn.execute(
            "INSERT INTO narratives (narrative_id, name, status, state, direction,"
            " opened, linked_dimensions, implied_outcome, story_query, origin,"
            " created_at, updated_at) VALUES ('yen_carry', 'The yen carry',"
            " 'active', 'emerging', 'Yen-funded carry is being unwound.', ?,"
            " '{}', '{}', 'yen_carry', 'seed', ?, ?)", (mid, now_iso, now_iso))
        nr.conn.commit()
        nr.close()
        es = events.EventStore(db)
        rows = [
            ("headline", f"{mid}T12:00:00+00:00", "google_news",
             "Yen jumps as BoJ signals hike - Reuters",
             json.dumps({"query": "yen_carry"})),
            ("headline", f"{mid}T13:00:00+00:00", "google_news",
             "Carry trade unwinds - Bloomberg.com",
             json.dumps({"query": "yen_carry"})),
            ("release", f"{mid}T12:30:00+00:00", "bls_cpi",
             "Consumer Price Index -- August", "{}"),
            ("scheduled", f"{nxt}T18:00:00+00:00", "claims_registry",
             f"FOMC statement -- {nxt}", "{}"),
        ]
        for i, (typ, at, source, title, pay) in enumerate(rows):
            es.conn.execute(
                "INSERT INTO events (content_hash, type, observed_at, available_at,"
                " ingested_at, source, title, payload) VALUES (?,?,?,?,?,?,?,?)",
                (f"fixture-{i}", typ, at, f"{mid}T14:00:00+00:00", now_iso, source,
                 title, pay))
        es.conn.commit()
        es.close()
        with probability_ledger.ProbabilityLedger(db) as led:
            led.record(source="narrative_register",
                       scenario_set="hypothesis:yen_carry:primary",
                       claim="USD/JPY is lower at the horizon (fixture).",
                       probability=0.55, emitted_at=f"{mid}T20:00:00+00:00",
                       horizon_date=(today + dt.timedelta(days=60)).isoformat(),
                       resolution_criterion="fred.usd_jpy below its emission level")

        # THE SCORECARD'S MONTH-ENDS: the S&P 500 at 5,000 then 5,250 (+5.00%)
        # and the 10-year at 4.00% then 4.25% (+25.0 bp) -- each in its own unit.
        m_start, m_end = v2.month_bounds({"report_date": today.isoformat()})
        with observations.ObservationStore(db) as st:
            st.write_many([
                {"registry_key": k, "instrument": None, "observed_at": d.isoformat(),
                 "available_at": f"{d.isoformat()}T21:00:00+00:00", "value": v,
                 "source": "synthetic"}
                for k, d, v in (("yfinance.mkt_gspc", m_start, 5000.0),
                                ("yfinance.mkt_gspc", m_end, 5250.0),
                                ("fred.yield_10y", m_start, 4.00),
                                ("fred.yield_10y", m_end, 4.25),
                                ("fred.hy_oas", m_start - dt.timedelta(days=40), 3.0),
                                ("fred.hy_oas", m_end - dt.timedelta(days=40), 3.0))])

        built = payload.build()
        md = render_v2.render(built)

        # --- ALL SECTIONS RENDER -------------------------------------------------
        for s in v2.V2_SECTIONS:
            check(isinstance(built.get(s), dict) and built[s].get("state") in
                  ("ok", "empty", "not_yet_sourced"),
                  f"the fixture month builds `{s}` ({(built.get(s) or {}).get('state')})")
        heads = ("## 1. The month in markets", "## 2. The month in one page",
                 "## 3. Looking back, by theme", "## 4. Voices",
                 "## 5. Looking ahead, 2–3 months", "## 6. Where our read lands",
                 "## 7. The record", "## I. Regime", "## II. Scenarios",
                 "## III. Top & Bottom", "## IV. Alternative Assets",
                 "## V. The register's month", "## Appendix")
        for h in heads:
            check(h in md, f"and renders {h!r}")
        pos = [md.find(h) for h in heads[:8]]
        check(all(a < b for a, b in zip(pos, pos[1:])),
              "in order: the month in markets first, then 2-6, then the record")
        check("Voices register not yet built" in md,
              "the voices section prints \"Voices register not yet built\"")

        # --- THE SCORECARD, in each metric's own unit ------------------------------
        sc = {r["metric"]: r for r in built["month_in_markets"]["rows"]}
        spx, y10 = sc.get("yfinance.mkt_gspc") or {}, sc.get("fred.yield_10y") or {}
        check(spx.get("change") == 5.0 and spx.get("change_unit") == "percent"
              and y10.get("change") == 25.0 and y10.get("change_unit") == "bps",
              f"the scorecard moves are month-end to month-end in their own unit "
              f"(S&P {spx.get('change')} {spx.get('change_unit')}, 10y "
              f"{y10.get('change')} {y10.get('change_unit')})")
        check("fred.hy_oas" not in sc and any("High-yield OAS" in m and
                                             "more than a week" in m
                                             for m in built["month_in_markets"]
                                             ["missing"]),
              "a series whose last print is weeks before the month-end is left OFF "
              "the scorecard with its reason, not printed as a flat month")
        check("| S&P 500 |" in md and "**+5.00%**" in md and "**+25.0 bp**" in md,
              "and the table prints them")

        # --- ONE AUDITED CALL PER SECTION -------------------------------------------
        import types
        from monthly_macro import prose as prose_mod
        calls: list[str] = []

        class Resp:
            def __init__(self, t):
                self.content = [types.SimpleNamespace(type="text", text=t)]
                self.model = "fixture-model"
                self.stop_reason = "end_turn"

        def reply(prompt: str) -> str:
            if "THE SECTION: Credit Cycle" in prompt:
                return ("Credit widened by 999 basis points.\n\nThat figure is not "
                        "in this section's data.")
            if "THE SECTION: Fed Policy Path" in prompt:
                return "- a bullet\n- another bullet"
            if "THE SECTION: Sentiment" in prompt:
                return ("The payload shows the sentiment dimension improving.\n\n"
                        "That argues for patience.")
            if "THE SECTION: The month in markets" in prompt:
                return ("The S&P 500 rose 5.00% over the month, and the 10-year "
                        "yield rose 25.0 basis points.\n\nThe move favours "
                        "duration-light exposures over long duration.")
            # Every other section: prose with no figure, so only the two seeded
            # failures can withhold anything.
            return ("The stored record for this section moved little over the "
                    "month.\n\nThat argues for reading the next prints before "
                    "drawing a conclusion from it.")

        class Client:
            def __init__(self):
                def create(**k):
                    calls.append(k["system"] + k["messages"][0]["content"])
                    return Resp(reply(k["system"]))
                self.messages = types.SimpleNamespace(create=create)

        written = prose_mod.write_all(built, client=Client())
        n_themes = len(built["looking_back"]["themes"])
        planned = [s["key"] for s in prose_mod.plan(built)]
        n_pillars = sum(1 for k in planned if k.startswith("pillar:"))
        check(len(calls) == len(planned) and list(written) == planned
              and {"month_in_markets", "month_in_one_page", "looking_ahead",
                   "our_read"} <= set(planned) and n_themes == 7,
              f"one model call per section: the opening, the takeaways, {n_themes} "
              f"themes (Sentiment among them), the look-ahead, our read and "
              f"{n_pillars} appendix pillar(s) ({len(calls)} calls)")
        check(not written["theme:sentiment"]["published"]
              and written["theme:sentiment"]["state"] == "internal_vocabulary"
              and "payload" in str(written["theme:sentiment"]["reason"]),
              f"a section that writes about the system -- \"the payload\", \"the "
              f"dimension\" -- is WITHHELD ({written['theme:sentiment']['state']})")
        check(prose_mod.internal_terms("an objective read of the field trial")
              == ["field"] and not prose_mod.internal_terms(
                  "gold is a store of value"[:0] + "credit spreads widened"),
              "the vocabulary check matches whole words only")
        fed = next((c for c in calls if "THE SECTION: Fed Policy Path" in c), "")
        check('"fed_calendar"' in fed and '"next_meetings"' in fed
              and '"we_do_not_yet_track"' in fed and '"dimensions"' not in fed,
              "the Fed section is fed its calendar, its series and its gaps, under "
              "plain keys -- never `dimensions`")
        pr = [c for c in calls if "THE SECTION: Pillar:" in c]
        check(len(pr) == n_pillars and all("exactly 1" in c for c in pr),
              f"each appendix pillar gets one paragraph of its own ({len(pr)})")
        cc = next((c for c in calls if "THE SECTION: Credit Cycle" in c), "")
        check("Credit Cycle" in cc and "Fiscal Dominance & Dollar\"" not in cc
              and "Equity Positioning & Sentiment\"" not in cc,
              "each call carries its OWN slice -- the credit theme's prompt holds "
              "no other theme's data")
        check(not written["theme:credit_cycle"]["published"]
              and "999" in str(written["theme:credit_cycle"]["reason"]),
              f"a section citing a figure its slice lacks is WITHHELD alone, with "
              f"its reason ({str(written['theme:credit_cycle']['reason'])[:60]})")
        check(not written["theme:fed_path"]["published"]
              and written["theme:fed_path"]["state"] in ("list_fragments",
                                                         "markdown_found"),
              "a section that comes back as bullet fragments is withheld: narrative "
              "sections are prose")
        others = [k for k in written if k not in ("theme:credit_cycle",
                                                  "theme:fed_path",
                                                  "theme:sentiment")]
        check(all(written[k]["published"] for k in others),
              f"while the {len(others)} sections beside them publish")
        check(all(written[k]["words"] > 0 for k in others),
              "and each published section carries its word count")
        pmd = render_v2.render(built, prose=written)
        check("Section withheld." in pmd and "999" in pmd
              and "The S&P 500 rose 5.00% over the month" in pmd,
              "the render prints the withheld section's reason in its place and "
              "the published prose in theirs")
        s3 = pmd[pmd.index("## 3."):pmd.index("## 4.")]
        check("### In one line each" in s3
              and s3.index("### In one line each") < s3.index("### Liquidity")
              and "**Liquidity & Plumbing.** The stored record" in s3,
              "section 3 opens with an executive summary: one line per theme, its "
              "opening claim, before the theme sections")
        check(s3.count("**Not yet tracked:**") == n_themes
              and "rate-cut odds" in s3,
              f"every theme ends with a \"Not yet tracked\" footnote outside its "
              f"prose ({s3.count('**Not yet tracked:**')} of {n_themes}), in plain "
              f"words")
        la = built["looking_ahead"]
        wn = [w["name"] for w in la["windows"]]
        check(len(wn) == 2 and "–" in wn[1] and "### " + wn[0] in pmd
              and "### " + wn[1] in pmd,
              f"the look-ahead splits into the rest of this month and the two after "
              f"({wn})")
        cov = {c["item"]: c for c in la["coverage"]}
        check(len(cov) == 17 and "FOMC meetings" in cov
              and any(w["present"] for w in cov["FOMC meetings"]["windows"].values())
              and not any(w["present"] for w in cov["ISM manufacturing"]
                          ["windows"].values())
              and "ISM manufacturing dates" in la["not_yet_tracked"],
              "the coverage check reports every listed release by window: the "
              "fixture's FOMC is present, ISM is missing and footnoted")
        sysp = prose_mod.system_prompt("X", "y")
        check("open with the claim" in sysp and "implication for positioning" in sysp
              and "No headings, no bullet points" in sysp,
              "the section brief asks for prose, insight first: claim, evidence, "
              "implication for positioning")
        ties = built.get("tie_backs") or {}
        check(set(ties) == set(v2.TIE_BACK_SECTIONS)
              and all(f"*{s}*" in md for s in ties.values()),
              f"every section after the first opens with its tie-back sentence "
              f"({len(ties)} of {len(v2.TIE_BACK_SECTIONS)})")
        takes = built["month_in_one_page"]["takeaways"]
        check(1 <= len(takes) <= 5 and all(t["sources"] for t in takes),
              f"{len(takes)} numbered takeaway(s), each with a stored source")
        check(any(t["origin"] == "regime" and "credit" in t["text"] for t in takes)
              and "Takeaway" in ties.get("regime", ""),
              "a takeaway drawn from the regime is named in the regime section's "
              "tie-back")

        # --- THE ITEMS, TAGGED BY THE RULES ----------------------------------------
        items = {i.get("story") or i.get("dimension") or i.get("text"): i
                 for t in built["looking_back"]["themes"] for i in t["items"]}
        cr = items.get("credit") or {}
        check(cr.get("tag") == "CORRECTION"
              and (cr.get("corrects") or {}).get("date") == prev,
              f"credit easy -> stressed (pole to pole) is a CORRECTION citing the "
              f"previous Monthly's read ({cr.get('tag')})")
        yc = items.get("yen_carry") or {}
        check(yc.get("tag") == "NEW" and yc.get("tier12_in_window") == 2,
              f"the story opened in the window is NEW with its two tier-1 "
              f"headlines ({yc.get('tag')}, {yc.get('tier12_in_window')})")
        check(any(i.get("kind") == "release" and "Consumer Price Index" in i["text"]
                  for t in built["looking_back"]["themes"] for i in t["items"]),
              "the CPI release prints under its theme, sourced to its event")
        for t in built["looking_back"]["themes"]:
            for i in t["items"]:
                if v2.check_item(i, tuple(built["looking_back"]["window"])):
                    bad(f"a printed item fails its own tag rule: {i['text'][:50]}")

        # --- WHAT CHANGED IS COMPUTED ------------------------------------------------
        wc = built["looking_back"]["what_changed"]
        whats = [r["what"] for r in wc["rows"]]
        check(wc.get("computed") is True
              and all((r.get("source") or {}).get("id") for r in wc["rows"]),
              f"What changed carries {len(wc['rows'])} row(s), every one sourced")
        check("dimension credit" in whats and "dial macro" in whats
              and "story yen_carry" in whats and "forecast emitted" in whats,
              f"and they are the fixture's differences: the object's credit and "
              f"macro moves, the story opened, the forecast emitted ({whats})")
        conn = sqlite3.connect(db)
        conn.execute("UPDATE narratives SET opened = ? WHERE narrative_id = "
                     "'yen_carry'", ((today - dt.timedelta(days=90)).isoformat(),))
        conn.commit()
        conn.close()
        again = payload.build()["looking_back"]["what_changed"]
        check("story yen_carry" not in [r["what"] for r in again["rows"]],
              "change the stored record and the list changes with it: the story "
              "opened before the window is no longer listed -- nothing in it is "
              "written by hand")
        src_text = (REPO / "monthly_macro" / "writer" / "render_v2.py").read_text(
            encoding="utf-8")
        check("each read from a stored record" in src_text,
              "and the renderer prints the list from the payload, saying so")

        # --- LOOKING AHEAD, AND OUR READ ------------------------------------------
        la = built["looking_ahead"]
        check(any(c["title"].startswith("FOMC") for c in la["calendar"]),
              "the scheduled FOMC is on the forward calendar")
        sc = la["scenarios"][0] if la["scenarios"] else {}
        check(sc.get("signposts") and all(s.get("date") for s in sc["signposts"]),
              f"the live weight prints with its Brier field and a dated 'what "
              f"would change our mind' ({len(sc.get('signposts') or [])} "
              f"signpost(s))")
        check("brier" in sc, "and the Brier sits beside the weight")
        para = built["our_read"]["paragraph"]
        check("0.55" in para and "no active position" in para,
              "Where our read lands restates the live weight and the books and "
              "nothing else")

        # --- THE DRY RUN: a pre-v2 archived payload, re-rendered, never sent -----
        import contextlib
        import io
        from daily_cascade import deliver
        from monthly_macro import run as mrun
        old = {k: v for k, v in built.items() if k not in v2.V2_SECTIONS
               and k != "tie_backs"}
        pay = Path(td) / "monthly_macro_fixture_payload.json"
        pay.write_text(json.dumps(old, default=str), encoding="utf-8")
        sends: list = []
        saved_send = deliver.send_html
        deliver.send_html = lambda *a, **k: (sends.append(a), ("sent", "x"))[1]
        argv = sys.argv
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                sys.argv = ["run", "--from-payload", str(pay), "--out-dir", td,
                            "--skip-narrative"]
                rc_refused = mrun.main()
                sys.argv += ["--dry-run"]
                rc_dry = mrun.main()
        finally:
            sys.argv = argv
            deliver.send_html = saved_send
        stamp = old.get("report_date")
        dmd = Path(td) / f"monthly_macro_{stamp}_dryrun.md"
        check(rc_refused == 1, "--from-payload without --dry-run is refused -- a "
                               "re-render never replaces an archived edition")
        check(rc_dry == 0 and dmd.exists()
              and (Path(td) / f"monthly_macro_{stamp}_dryrun.html").exists()
              and not sends,
              f"--dry-run writes _dryrun.md and .html and sends NOTHING "
              f"({len(sends)} send(s))")
        text = dmd.read_text(encoding="utf-8") if dmd.exists() else ""
        check("## 1. The month in markets" in text
              and "Voices register not yet built" in text,
              "and a payload archived before v2 gets its v2 sections built at its "
              "own cutoff")
    finally:
        (observations.DEFAULT_DB, register_store.DEFAULT_DB,
         payload.previous_monthly) = saved


def isolate_and_seed() -> str:
    """Point every store the payload reads at a temporary database, and seed it.

    Before ANY import that opens a store: altdata.observations and register.store
    read CHESTER_DB once, at import, and the ledger and grade store default to
    observations.DEFAULT_DB. The module attributes are set as well, in case an
    earlier import already resolved them.
    """
    import atexit
    import datetime as dt
    import os
    import shutil
    import tempfile
    td = tempfile.mkdtemp(prefix="validate_monthly_")
    atexit.register(shutil.rmtree, td, ignore_errors=True)
    db = str(Path(td) / "monthly.db")
    os.environ["CHESTER_DB"] = db
    os.environ["CHESTER_PIN_LOG_PATH"] = str(Path(td) / "pin_log.csv")
    from altdata import config, observations, probability_ledger, session
    from register import store as register_store
    import regime
    observations.DEFAULT_DB = register_store.DEFAULT_DB = db
    config.PIN_LOG_PATH = os.environ["CHESTER_PIN_LOG_PATH"]

    # Synthetic, NOT market data: two registered pillar members (pillar 5's VIX,
    # pillar 6's HY OAS), every weekday for 1,200 days up to yesterday -- so past
    # the replay cutoff, which is the last day of the previous month.
    today = session.session_date_obj()
    days, d = [], today - dt.timedelta(days=1200)
    while d < today:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    rows = [{"registry_key": key, "instrument": None,
             "observed_at": d.isoformat(),
             "available_at": f"{d.isoformat()}T21:00:00+00:00",
             "value": float(v), "source": "synthetic"}
            for i, d in enumerate(days)
            for key, v in (("fred.vix", 15 + (i % 11)),
                           ("fred.hy_oas", 3 + (i % 7) * 0.1))]
    # AND ONE ROW OBSERVED TODAY, knowable five minutes ago: on the 1st, "up to
    # yesterday" ends ON the cutoff, and D's no-leak check would be vacuous.
    seen = (session.utc_now() - dt.timedelta(minutes=5)).isoformat()
    rows += [{"registry_key": key, "instrument": None,
              "observed_at": today.isoformat(), "available_at": seen,
              "value": v, "source": "synthetic"}
             for key, v in (("fred.vix", 21.0), ("fred.hy_oas", 3.4))]
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        last = days[-1].isoformat()
        regime.store_object(regime.compute(as_of=regime.session_cutoff(last),
                                           session_day=last, store=st), st)
    month = today.replace(day=1) - dt.timedelta(days=1)
    with probability_ledger.ProbabilityLedger(db) as led:
        led.record(source="monthly_macro",
                   scenario_set=f"monthly_macro:{month.replace(day=1).isoformat()}",
                   claim="Seeded scenario (synthetic)", probability=0.6,
                   emitted_at=f"{month.replace(day=1).isoformat()}T12:00:00+00:00",
                   horizon_date=(today + dt.timedelta(days=60)).isoformat(),
                   resolution_criterion="seeded by validate_monthly")
    print(f"  seeded {len(rows):,} observations, one market-state object for "
          f"{last} and one ledger forecast into {db}")
    return td


def main() -> int:
    print(f"{LINE}\nThe Monthly -- Phase 4b (seeded store; the real one is "
          f"tools/validate_monthly_store.py)\n{LINE}")
    isolate_and_seed()
    group_a()
    group_g()
    group_h()
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

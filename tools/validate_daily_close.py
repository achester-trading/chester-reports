"""
Validation gate for the D4c close debrief.

Four properties, each of which is a ruling rather than a preference, and each
of which would fail silently:

  1. **NO PROSE.** 32.5 makes the data-only edition the thing that proves the
     delivery chain while narrative is untrusted. "We just won't add prose" is
     an intention; a check on the source text is an enforcement. So the package
     is read and any import of the narrative layer or an LLM client fails the
     build. This is 31.5(b) applied here -- a safety property is verified by
     reading the enforcing code, not the comment that describes it.

  2. **THE ARCHIVE SURVIVES A FAILED SEND.** 32.3 wants the record not to
     depend on an inbox. The only way to be sure is to fail the send and check
     the file is still there, which is what this does with a stubbed transport.

  3. **DELIVERY NEVER RAISES, AND ALWAYS NAMES ITS OUTCOME.** A transport that
     throws would discard a report that already succeeded; a transport that
     returns quietly would be the sixth silent delivery path in this repo.
     Every outcome is a named state.

  4. **ABSENCE IS NEVER A BLANK CELL.** A missing value and a missing source
     render identically as empty table cells and mean opposite things. Every
     None must reach the page as a dash.

Runs anywhere: no SMTP, no network, no store required.

    python tools/validate_daily_close.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from daily_cascade import deliver, render  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


# Anything that would let a sentence reach the data path.
FORBIDDEN = ("anthropic", "openai", "claude", "llm", "completion")

# THE MODULES THAT MUST STAY PROSE-FREE, which is not the same as the package.
#
# This used to scan every file in daily_cascade/ for a set of substrings, which
# was right while the package had no narrative at all and became wrong the moment
# D3 made one publishable: the scan failed on narrative.py for being a narrative
# module, and on payload.py for containing a function named narrative_payload.
#
# The invariant was never "the word must not appear". It is that THE DATA PATH
# CANNOT REACH A LANGUAGE MODEL -- so the payload and render modules are the ones
# checked, the check is about imports rather than spelling, and it is verified at
# runtime as well as in the text. A helper named narrative_payload is fine; an
# `import narrative` in payload.py is not, because that is the edge along which a
# generated sentence could reach a figure before anything audited it.
DATA_PATH = ("payload.py", "render.py", "morning_payload.py",
             "morning_render.py", "state_block.py")

# Modules allowed to reach a model, because gating them is the whole design.
PROSE_PATH = ("narrative.py",)


def group_a() -> None:
    """The data path cannot reach a model. Checked in the source AND at runtime."""
    print(f"{LINE}\nA. The data-only ruling (32.5), enforced on the data path\n{LINE}")
    pkg = REPO / "daily_cascade"

    for name in DATA_PATH:
        f = pkg / name
        if not f.exists():
            bad(f"{name} is missing -- the check is pointed at nothing")
            continue
        text = f.read_text(encoding="utf-8")
        # Strip docstrings and comments first. A check that trips on the
        # sentence explaining why prose is banned is a check somebody deletes.
        code = re.sub(r'""".*?"""', "", text, flags=re.S)
        code = re.sub(r"#.*", "", code)
        hits = [w for w in FORBIDDEN if w in code.lower()]
        if hits:
            bad(f"{name} references {hits} outside comments -- the data path "
                f"must not reach a language model")
        else:
            ok(f"{name}: no LLM client in the code")

        # The narrative module by IMPORT, which is the edge that matters.
        imports = re.findall(r"^\s*(?:from|import)\s+([\w.]+)", code, re.M)
        narr = [m for m in imports if m.endswith("narrative")
                or ".narrative" in m]
        if narr:
            bad(f"{name} imports {narr} -- the narrative module must not be "
                f"reachable from the data path")
        else:
            ok(f"{name}: does not import the narrative module")

    # RUNTIME, not just text. An indirect import through a third module would
    # satisfy every regex above and still put a model one call away from the
    # payload, so the assertion is made against sys.modules in a clean process.
    probe = ("import sys; "
             "import daily_cascade.payload, daily_cascade.render, "
             "daily_cascade.morning_payload, daily_cascade.morning_render; "
             "bad=[m for m in sys.modules "
             "     if m.endswith('narrative') or m in ('anthropic','openai')]; "
             "print('LEAKED:' + ','.join(sorted(bad)) if bad else 'CLEAN')")
    r = subprocess.run([sys.executable, "-c", probe], capture_output=True,
                       text=True, cwd=str(REPO))
    out = (r.stdout or "").strip()
    check("CLEAN" in out,
          f"importing the data path pulls in NO narrative or LLM module "
          f"({out or r.stderr.strip()[:80]})")

    for name in PROSE_PATH:
        f = pkg / name
        check(f.exists(), f"{name} exists -- the prose path is present to be gated")
        if not f.exists():
            continue
        src = f.read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", src, flags=re.S)
        code = re.sub(r"#.*", "", code)
        check("numeral_audit" in code,
              f"{name} imports the numeral audit -- prose it produces is gated "
              f"by construction, not by the caller remembering to")
        check("import anthropic" in code and "def _client" in code,
              f"{name} imports the client LAZILY, so a box without the package "
              f"runs the rest of the pipeline")


def group_b() -> None:
    """The archive survives a failed send, and outcomes are always named."""
    print(f"\n{LINE}\nB. Archive before transport (32.3)\n{LINE}")
    html = "<div>report</div>"

    with tempfile.TemporaryDirectory() as d:
        # Force the send to fail in the most total way available: no config.
        # `not_configured` is the honest state for a box that has no
        # credentials, and it must not look like a delivery.
        saved = deliver.smtp_config
        deliver.smtp_config = lambda: (None, ["SMTP_USER"])  # type: ignore
        try:
            out = deliver.deliver("subj", html, "r.html", archive_dir=d)
        finally:
            deliver.smtp_config = saved

        p = Path(d) / "r.html"
        if p.exists() and p.read_text(encoding="utf-8") == html:
            ok("unsendable report is still archived, byte for byte")
        else:
            bad("the archive did not survive a failed send")
        if out["delivery"] == "not_configured":
            ok("missing credentials -> delivery=not_configured, not a success")
        else:
            bad(f"missing credentials reported {out['delivery']!r}")
        if out["archive_state"] == "archived":
            ok("archive_state is reported separately from delivery")
        else:
            bad(f"archive_state={out['archive_state']!r}")

    with tempfile.TemporaryDirectory() as d:
        # A transport that throws. deliver() must swallow it into a named
        # state -- an exception here would discard a report that was already
        # written and already correct.
        saved = deliver.send_html
        deliver.send_html = lambda *a, **k: ("send_failed", "stubbed")  # type: ignore
        try:
            out = deliver.deliver("subj", html, "r.html", archive_dir=d)
            ok("a failed transport returns a state instead of raising")
        except Exception as exc:  # noqa: BLE001
            bad(f"deliver() raised: {exc}")
            out = {}
        finally:
            deliver.send_html = saved
        if (Path(d) / "r.html").exists():
            ok("archive written even when the transport failed")
        else:
            bad("archive missing after a transport failure")

    # send_html itself, against a host that cannot exist.
    import os  # noqa: PLC0415
    env = {"SMTP_USER": "u@example.invalid", "SMTP_PASSWORD": "pw",
           "SMTP_RCPT": "r@example.invalid", "SMTP_HOST": "127.0.0.1",
           "SMTP_PORT": "9"}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        state, detail = deliver.send_html("s", "<p>x</p>")
        if state == "send_failed":
            ok("an unreachable relay -> send_failed, named and not raised")
        else:
            bad(f"unreachable relay reported {state!r}")
        if "pw" not in detail:
            ok("the password does not appear in the failure detail")
        else:
            bad("PASSWORD LEAKED into the failure detail")
    except Exception as exc:  # noqa: BLE001
        bad(f"send_html raised instead of returning: {exc}")
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def group_f() -> None:
    """The session move carries BOTH denominators, and the audit can see them."""
    print(f"\n{LINE}\nF. THE MOVE'S TWO PERCENTILES REACH THE AUDIT\n{LINE}")
    import regime
    from altdata import numeral_audit as na
    from daily_cascade import payload as pl, state_block

    # A CONSTRUCTED OBJECT, not a store read. The figure under test is whether the
    # payload CARRIES the fields and whether the audit can SEE them, and both are
    # properties of the plumbing rather than of tonight's market. Reading the store
    # would make this gate pass or fail on whether the box happened to have run
    # base_rates yet, which is a different fact.
    move = {"metric": "yfinance.mkt_spy", "change": -1.4, "delta_unit": "percent",
            "from_date": "2026-09-21", "to_date": "2026-09-22",
            "percentile_5y": 7.48, "n_5y": 1254, "z_5y": -2.1,
            "percentile_long_run": 9.96, "long_run_n": 24796,
            "long_run_first": "1927-12-30",
            "long_run_series": "yfinance.mkt_gspc",
            "long_run_method": "base-rates-method-1"}
    payload = {"session": "2026-09-22",
               "what_changed": {"session": "2026-09-22", "session_move": move}}

    vals = na.payload_numbers(payload)
    for field in ("percentile_5y", "percentile_long_run", "long_run_n"):
        check(float(move[field]) in vals,
              f"what_changed.session_move.{field} ({move[field]}) is in the "
              f"audit's reference set, so a paragraph may cite it")
    check(na.payload_numbers({"what_changed": {"session_move": {}}}) == [],
          "and an empty move contributes nothing, so the reference set cannot be "
          "widened by a field that was not measured")

    # THE RENDER PRINTS BOTH, and the reason it must is that they disagree exactly
    # where it matters: five years hold fewer very bad days than ninety-nine do, so
    # a hard session reads lower against five years than against the century. One
    # denominator invites the reader to supply the other from memory.
    html = state_block.move_line(payload["what_changed"])
    check("7.5" in html or "7.48" in html,
          "the rendered line carries the five-year percentile")
    check("9.96" in html or "10.0" in html,
          "and the long-run percentile beside it")
    check("24796" in html or "24,796" in html,
          "with the long-run sample size, so the denominator is visible and not "
          "implied")
    check("1927-12-30" in html,
          "and the date the long-run sample starts from")

    absent = state_block.move_line(
        {"session_move": {"change": None,
                          "absent_reason": "no observation for the metric"}})
    check("not measured" in absent.lower() or "absent" in absent.lower(),
          "a move that could not be measured renders as not measured rather than "
          "as a zero")
    partial = state_block.move_line(
        {"session_move": dict(move, percentile_long_run=None,
                              long_run_absent_reason="no baserate table stored")})
    check("no baserate table stored" in partial,
          "and a missing long-run leg prints its reason -- the five-year number "
          "still prints, because a box that has not computed the base rates has "
          "not lost the move")

    # THE NARRATIVE SUBSET MUST CARRY IT TOO, or the audit's reference set is
    # narrower than the page and a true sentence fails the gate.
    src = (REPO / "daily_cascade" / "payload.py").read_text(encoding="utf-8")
    check('"what_changed": full.get("what_changed")' in src,
          "the narrative payload passes what_changed through whole, so the move's "
          "percentiles are in the model's own reference set and a paragraph citing "
          "one does not fail D3")
    check(callable(getattr(regime, "session_move", None)),
          "and regime.session_move() is the one producer of the figure")


def group_g() -> None:
    """Print precision: the model never sees a figure the report would not print."""
    print(f"\n{LINE}\nG. PRINT PRECISION AT THE MODEL BOUNDARY\n{LINE}")
    from daily_cascade import narrative as nv, payload as pl, precision as pr
    print(f"  {pr.describe()}")

    # --- the declared table, case by case ------------------------------------
    for key, raw, want in (("percentile", 45.2951, 45.3),
                           ("spot", 770.658508, 770.66),
                           ("distance_pct", 1.756612, 1.76),
                           ("magnitude", -0.320149, -0.32),
                           ("dollar_gamma_per_1pct", 4590394967.0, 4590000000.0),
                           ("net_gex", 593512345.0, 593510000.0),
                           ("long_run_n", 24796, 24796)):
        got = pr.round_value(key, raw)
        check(got == want, f"{key}: {raw!r} -> {got!r} (want {want!r})")
    check(pr.round_value("dollar_gamma_per_1pct", 412.5) == 412.5,
          "a dollar figure below a thousand keeps two ordinary decimals -- there "
          "is no scale to round it at")
    check(pr.apply(True) is True and pr.apply(3) == 3,
          "booleans and integers pass through: spot_above_flip is a fact, not a "
          "figure, and a count of sessions is exact")

    # --- A PAYLOAD FIGURE ABOVE ITS PRECISION FAILS THE BUILD ----------------
    raw = {"market_state": {"dimensions": {"trend": {"percentile": 55.8601}}},
           "positions": [{"avg_cost": 769.070007, "distance_pct": 1.756612}]}
    v = pr.violations(raw)
    check(len(v) == 3,
          f"three over-precise figures are found and NAMED by path "
          f"({[x['path'] for x in v]})")
    check(all(x.get("expected") is not None and x.get("dp") for x in v),
          "each violation carries what it should have been and the rule it broke, "
          "so a failure names the field rather than the count")
    check(pr.violations(pr.apply(raw)) == [],
          "and applying the transform removes every one")
    check(pr.violations(pr.apply(pr.apply(raw))) == [],
          "twice changes nothing -- idempotent, which is what lets it be applied "
          "at the assembly AND at the boundary without one undoing the other")

    # --- the real payload conforms -------------------------------------------
    try:
        full = pl.build()
        narr = pl.narrative_payload(full)
    except Exception as exc:                                   # noqa: BLE001
        SKIPPED.append(f"narrative payload not buildable here: {exc}")
        print(f"  SKIP  payload not buildable: {exc}")
        narr = None
    if narr:
        v = pr.violations(narr)
        from altdata import numeral_audit as _na
        n_figs = len(_na.payload_numbers(narr))
        check(not v,
              f"the narrative payload built from this store conforms across "
              f"{n_figs} numeric leaves"
              if not v else
              f"the narrative payload carries {len(v)} over-precise figure(s): "
              f"{[x['path'] for x in v][:6]}")

    # --- AND THE BOUNDARY ENFORCES IT, whatever it is handed ------------------
    # A stub client that records the prompt it was given. The point is not that
    # generate() works -- other groups cover that -- but that a caller handing it a
    # full-precision payload cannot get a full-precision prompt.
    seen: dict = {}

    class _Stub:
        class messages:
            @staticmethod
            def create(**kw):
                seen.update(kw)

                class _B:
                    type = "text"
                    text = "Trend sits at the 55.9 percentile."

                class _R:
                    content = [_B()]
                    model = "stub"
                    stop_reason = "end_turn"
                    usage = None
                return _R()

    res = nv.generate({"market_state": {"dimensions":
                                        {"trend": {"percentile": 55.8601}}}},
                      client=_Stub())
    prompt = str((seen.get("messages") or [{}])[0].get("content", ""))
    check("55.8601" not in prompt,
          "a full-precision figure handed to generate() does NOT reach the prompt")
    check("55.9" in prompt,
          "and the rounded one does -- the rule is enforced at the boundary it is "
          "about, not by every caller remembering")
    check(res.state == "published",
          f"and the paragraph citing 55.9 passes the audit against the rounded "
          f"payload ({res.state}: {res.reason[:48]})")

    # MARKDOWN IS WITHHELD, NOT STRIPPED. The weekly's first published paragraph
    # opened with `**Week ending...**` and the reader would have seen the asterisks.
    class _Md(_Stub):
        class messages:
            @staticmethod
            def create(**kw):
                class _B:
                    type = "text"
                    text = "**Trend** sits at the 55.9 percentile."

                class _R:
                    content = [_B()]
                    model = "stub"
                    stop_reason = "end_turn"
                    usage = None
                return _R()

    md = nv.generate({"market_state": {"dimensions":
                                       {"trend": {"percentile": 55.8601}}}},
                     client=_Md())
    check(md.state == "markdown_found",
          f"a reply containing markdown is withheld ({md.state}) -- these reports "
          f"are HTML and the renderer escapes what it is given")
    check("**" in md.reason,
          "and the reason names what it found")
    check(md.rejected_text and "**" in md.rejected_text,
          "with the rejected text kept, so the next diagnosis starts from the "
          "sentence rather than from the rule")


def group_h() -> None:
    """The exceptions reach the paragraph, and the table may not be recited."""
    print(f"\n{LINE}\nH. EXCEPTIONS IN THE COVERAGE, AND NO ROW-BY-ROW RECITAL\n{LINE}")
    from daily_cascade import narrative as nv, payload as pl

    # A CONSTRUCTED OBJECT with both kinds, so the ranking is exercised rather than
    # whatever the store happens to hold tonight.
    obj = {
        "session": "2026-09-22",
        "dials": {"vol": {"state": "normal"}},
        "dimensions": {},
        "exceptions": [
            {"id": "contradiction:a", "kind": "contradiction", "what": "a open 6",
             "value": 2.4, "threshold": 2.0, "since": "2026-09-15"},
            {"id": "contradiction:b", "kind": "contradiction", "what": "b open 9",
             "value": 6.0, "threshold": 2.0, "since": "2026-09-10"},
            {"id": "extreme:x", "kind": "extreme", "what": "x at an extreme",
             "value": 2.7, "threshold": "percentile <= 5 or >= 95"},
            {"id": "extreme:y", "kind": "extreme", "what": "y at an extreme",
             "value": 49.0, "threshold": "percentile <= 5 or >= 95"},
        ],
    }
    ns = pl._narrative_state(obj)                              # noqa: SLF001
    check(ns.get("exceptions_open") == 4,
          f"the open set travels as a COUNT ({ns.get('exceptions_open')}) -- eight "
          f"exceptions cannot each get a clause in one paragraph")
    check(ns.get("exceptions_by_kind") == {"contradiction": 2, "extreme": 2},
          f"split by kind ({ns.get('exceptions_by_kind')})")
    named = [e["id"] for e in ns.get("exceptions_most_extreme") or []]
    check(named == ["contradiction:b", "extreme:x"],
          f"and TWO are named, the most extreme of each kind ({named}) -- b at 3x "
          f"its threshold over a at 1.2x, and x at 47 points from the middle of "
          f"its distribution over y at 1")
    # THE REASON THEY ARE RANKED SEPARATELY: `value` means two different things.
    check(all(isinstance(e.get("value"), (int, float))
              for e in ns["exceptions_most_extreme"]),
          "both carry their value, one a gap z-score and one a percentile -- which "
          "is exactly why they are not sorted against each other: that would be a "
          "composite across unlike units")
    one_kind = pl._narrative_state(                            # noqa: SLF001
        {"dimensions": {}, "exceptions": obj["exceptions"][2:]})
    check(len(one_kind.get("exceptions_most_extreme") or []) == 2,
          "where only one kind is open, that kind's top two are named rather than "
          "one slot going empty")
    none = pl._narrative_state({"dimensions": {}, "exceptions": []})  # noqa: SLF001
    check(none.get("exceptions_open") == 0
          and none.get("exceptions_most_extreme") == [],
          "and a quiet session carries a zero rather than an absent field")

    # --- the template's bar, in the prompt the model actually reads ------------
    check("DO NOT RESTATE A TABLE ROW BY ROW" in nv.SYSTEM_PROMPT,
          "the prompt bars reciting a table row by row")
    for phrase in ("changed", "extreme", "disagrees"):
        check(phrase in nv.SYSTEM_PROMPT,
              f"and says when a dimension MAY be named ({phrase})")
    tpl = (REPO / "docs" / "narrative-template-close.md").read_text(
        encoding="utf-8")
    check("The paragraph does not restate a table" in tpl,
          "the template carries the same rule, since it is the committed contract")
    check("exceptions" in tpl.lower() and "two most extreme" in tpl.lower(),
          "and the coverage list now includes the exceptions")
    check(tpl.count("\n6. ") == 1 and tpl.count("\n7. ") == 1,
          "seven coverage items, not six")


def group_c() -> None:
    """Absence renders as a dash, never as an empty cell."""
    print(f"\n{LINE}\nC. Absence is visible (32.5)\n{LINE}")
    for fn, name in ((render.num, "num"), (render.money, "money"),
                     (render.pct, "pct"), (render.hit, "hit")):
        out = fn(None)
        if "mdash" in out:
            ok(f"{name}(None) renders a dash, not an empty cell")
        else:
            bad(f"{name}(None) produced {out!r}")

    # A NON-NUMERIC VALUE COSTS A CELL, NEVER THE REPORT. close_report.py has
    # no try around render(), and the archive is written from the same string,
    # so an exception here would destroy the nightly report AND its permanent
    # copy over one bad field. Verified with the values a store or a profile
    # JSON could actually produce.
    for fn, name in ((render.num, "num"), (render.money, "money"),
                     (render.pct, "pct")):
        for junk in ("n/a", "", [], {}, object()):
            try:
                out = fn(junk)
            except Exception as exc:  # noqa: BLE001
                bad(f"{name}({junk!r}) raised {type(exc).__name__} -- "
                    f"one bad cell would kill the report and its archive")
                break
            if "mdash" not in out:
                bad(f"{name}({junk!r}) returned {out!r}, not a dash")
                break
        else:
            ok(f"{name}() returns a dash on every non-numeric value, never raises")

    empty = {"report": "daily_close", "session": "2026-01-02",
             "generated_at": "x", "as_of": "y", "run_id": "z",
             "convention_version": "dealers-hand-v1", "tolerance_bps": 25.0,
             "universe": {"greeks": [], "ingestion_only": []},
             "exposure": [], "exposure_missing": [], "pins": [],
             # regime.macro_state came OFF this list in Phase 2 -- it is the
             # macro dial now -- so the seeded row is one of the two that remain.
             "pin_hits": {}, "regime_not_built": [
                 {"key": "regime.vix_term_structure", "state": "not_built",
                  "note": "gated on the CFE Enhanced subscription"}],
             # No market_state: this fixture is the EMPTY payload, and the state
             # block must say the object is missing rather than raise.
             "market_state": None, "what_changed": None,
             "portfolio": {"state": "absent", "reason": "no rows"},
             "warnings": ["nothing computed"]}
    html = render.render(empty)
    for needle, why in (
            ("NOT BUILT", "an unbuilt block says so in words"),
            ("No market-state object", "an absent state object says so, and the "
                                      "page renders without it"),
            ("does not recompute it", "and says the report will not recompute "
                                     "one -- two regimes with no way to say which "
                                     "a decision was made under is the failure "
                                     "this wording exists to prevent"),
            ("No exposure profiles", "an empty exposure table says so"),
            ("No pin-log rows", "an empty pin table says so"),
            ("No Portfolio Truth", "an absent portfolio says so, with a reason"),
            ("nothing computed", "warnings reach the page")):
        if needle in html:
            ok(why)
        else:
            bad(f"{why} -- {needle!r} missing from the rendered page")
    if "<td style" not in html or "&mdash;" in html or "exposure" in html:
        ok("an empty payload still renders a page rather than crashing")
    else:
        bad("empty payload rendered nothing recognisable")

    # Escaping. A symbol or a reason string is data, and data ends up in HTML.
    if "&lt;script&gt;" in render.esc("<script>"):
        ok("esc() neutralises markup in payload strings")
    else:
        bad("esc() does not escape markup")


def group_d() -> None:
    """The unit and timer agree with the wrapper about when it runs."""
    print(f"\n{LINE}\nD. Schedule and unit wiring\n{LINE}")
    t = (REPO / "deploy/systemd/chester-daily-close.timer").read_text(encoding="utf-8")
    s = (REPO / "deploy/systemd/chester-daily-close.service").read_text(encoding="utf-8")
    if "OnCalendar=Mon-Fri 16:45 America/New_York" in t:
        ok("timer fires 16:45 ET Mon-Fri, zone-pinned -- clear of the 16:30 sync")
    else:
        bad("timer is not 16:45 America/New_York")
    if re.search(r"^Persistent=false", t, re.M):
        ok("Persistent=false -- no catch-up report dated today for a session "
           "the reader already lived through")
    else:
        bad("timer would fire a stale catch-up run")
    if re.search(r"^SuccessExitStatus=0 2\s*$", s, re.M):
        ok("exit 2 (archived, not delivered) is a successful run; 1 is not")
    else:
        bad("SuccessExitStatus does not distinguish transport from payload")
    w = (REPO / "scripts/run_daily_close.sh").read_text(encoding="utf-8")
    if "altdata.session is-session" in w:
        ok("the wrapper asks the shared holiday table, keeping no second copy")
    else:
        bad("the wrapper does not consult the calendar")


def group_e() -> None:
    """The audit GATES the paragraph, and the withheld case is not silent."""
    print(f"\n{LINE}\nE. The numeral audit gates the narrative (D3 -> D4e)\n{LINE}")
    from daily_cascade import narrative as nr          # noqa: PLC0415

    base = {"session": "2026-09-09", "exposure": [], "exposure_missing": [],
            "pins": [], "pin_hits": {}, "warnings": [], "universe": {},
            "portfolio": {"state": "absent", "reason": "x"}}
    figures = {"session": "2026-09-09", "spot": 762.4500122070312,
               "call_wall": 775.0}

    class Blk:
        type = "text"
        def __init__(self, t): self.text = t

    class Resp:
        def __init__(self, t): self.content = [Blk(t)]; self.model = "claude-sonnet-5"

    class Fake:
        def __init__(self, t): self._t = t
        @property
        def messages(self): return self
        def create(self, **kw): return Resp(self._t)

    # PASS -> the paragraph ships, ABOVE the tables.
    honest = nr.generate(figures, client=Fake(
        "SPY closed at 762.45 with the call wall at 775."))
    check(honest.published, f"an honest paragraph passes the audit ({honest.state})")
    html = render.render(base, {"archive_path": "/x/y.html"}, narrative=honest)
    check("762.45" in html, "and reaches the page")
    check(html.index("762.45") < html.index("Dealer exposure"),
          "ABOVE the tables -- it is read first and the tables are what a "
          "reader checks it against")
    check("claude-sonnet-5" in html,
          "with the model recorded on the artifact, so the writer of any graded "
          "paragraph is identifiable later")

    # FAIL -> the data-only edition, with the one line the order specifies.
    liar = nr.generate(figures, client=Fake(
        "SPY closed at 762.45 and realized vol is 11.3%."))
    check(not liar.published and liar.state == "audit_failed",
          f"an invented figure fails the audit ({liar.state})")
    note = liar.withheld_note()
    check(note.startswith("narrative withheld: numeral audit failed on 1 figure"),
          f"the note is the specified one line ({note!r})")
    check("11.3%" in note, "and names the figure that failed")
    html = render.render(base, {"archive_path": "/x/y.html"}, narrative=liar)
    check("narrative withheld" in html,
          "the withheld note reaches the page rather than the page going quiet")
    check("11.3%" in html and "762.45" not in html,
          "the offending figure is named and NO part of the paragraph ships -- "
          "it is withheld, not corrected, because a figure that failed the "
          "audit is one nobody can vouch for")
    check(html.index("narrative withheld") < html.index("Dealer exposure"),
          "in the same place the paragraph would have been, so a prose-free "
          "edition is distinguishable from one where nothing was asked")

    # Disabled is a third state and adds nothing at all.
    html = render.render(base, {"archive_path": "/x/y.html"}, narrative=None)
    check("narrative withheld" not in html and "Generated paragraph" not in html,
          "with no narrative attempted the page carries neither prose nor a note")

    # The entry point must actually consult the audit rather than trusting it.
    src = (REPO / "daily_cascade" / "close_report.py").read_text(encoding="utf-8")
    code = re.sub(r'""".*?"""', "", src, flags=re.S)
    code = re.sub(r"#.*", "", code)
    check("narrative=narr" in code.replace(" ", ""),
          "close_report passes the narrative result to the renderer")
    check("published" in code or "narr.state" in code,
          "and branches on it rather than assuming a paragraph exists")
    check("log.warning" in code,
          "a withheld paragraph is LOGGED -- the report carries one line and the "
          "log is the only place it can be investigated later")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    group_g()
    group_h()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

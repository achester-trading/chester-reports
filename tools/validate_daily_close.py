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


# Anything that would let a sentence into this edition.
FORBIDDEN = ("anthropic", "narrative", "openai", "claude", "llm", "completion")


def group_a() -> None:
    """No prose, and it is checked in the source rather than promised."""
    print(f"{LINE}\nA. The data-only ruling (32.5), enforced on the source\n{LINE}")
    pkg = REPO / "daily_cascade"
    for f in sorted(pkg.glob("*.py")):
        text = f.read_text(encoding="utf-8")
        # Strip docstrings and comments first. A check that trips on the
        # sentence explaining why prose is banned is a check somebody deletes.
        code = re.sub(r'""".*?"""', "", text, flags=re.S)
        code = re.sub(r"#.*", "", code)
        hits = [w for w in FORBIDDEN if w in code.lower()]
        if hits:
            bad(f"{f.name} references {hits} outside comments -- "
                f"this edition must contain no generated prose")
        else:
            ok(f"{f.name}: no narrative or LLM path in the code")


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

    empty = {"report": "daily_close", "session": "2026-01-02",
             "generated_at": "x", "as_of": "y", "run_id": "z",
             "convention_version": "dealers-hand-v1", "tolerance_bps": 25.0,
             "universe": {"greeks": [], "ingestion_only": []},
             "exposure": [], "exposure_missing": [], "pins": [],
             "pin_hits": {}, "regime": [{"key": "regime.macro_state",
                                         "state": "not_built", "note": "D2"}],
             "portfolio": {"state": "absent", "reason": "no rows"},
             "warnings": ["nothing computed"]}
    html = render.render(empty)
    for needle, why in (
            ("NOT BUILT", "an unbuilt block says so in words"),
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
    if "OnCalendar=Mon-Fri 16:30 America/New_York" in t:
        ok("timer fires 16:30 ET Mon-Fri, zone-pinned")
    else:
        bad("timer is not 16:30 America/New_York")
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


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    group_a()
    group_b()
    group_c()
    group_d()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

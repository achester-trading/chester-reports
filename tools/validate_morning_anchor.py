"""
Validation gate for the 07:00 morning anchor (Phase 1, data-only edition).

Runs entirely against a temporary store. Nothing here touches the network, and
that is also the first thing it proves.

  A  THE RENDER FETCHES NOTHING (30.4). The payload and render modules are read
     for any HTTP client, any yfinance import, any socket. The 06:45 fetch is a
     separate unit precisely so this process cannot fail for a transport reason,
     and a later edit that added a convenience fetch would quietly undo that.
  B  AN ABSENT BLOCK PUBLISHES A REASON, NOT SILENCE. A dead 06:45 must produce a
     report that says the fetch did not run, because that is what tells the
     reader before the open. Exit 1 is reserved for EVERY block empty.
  C  STALE IS MARKED, NOT DROPPED. Yesterday's overnight rows must not be printed
     as this morning's, and must not be silently omitted either -- omitting them
     makes a dead timer look like a market with nothing to say.
  D  THE RENDERER DOES NO ARITHMETIC. Every number in the HTML is a number in the
     payload. This is the boundary D3's numeral audit will enforce on prose, and
     it has to already hold for the figures.
  E  THE FOOTER NAMES THE ARCHIVE PATH, and the archive precedes the send.
  F  THE UNITS AND THE WRAPPER AGREE with the schedule and the heartbeat rule.

    python tools/validate_morning_anchor.py
"""

from __future__ import annotations

import datetime as dt
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import observations                      # noqa: E402
from altdata.sources import overnight as on           # noqa: E402
from daily_cascade import morning_payload as mp       # noqa: E402
from daily_cascade import morning_render as mr        # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

PKG = REPO / "daily_cascade"
UNITS = REPO / "deploy" / "systemd"


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


def code_of(path: Path) -> str:
    """Source with docstrings and comments stripped.

    A check that trips on the paragraph explaining why fetching is banned is a
    check somebody deletes.
    """
    t = path.read_text(encoding="utf-8")
    t = re.sub(r'"""(?:.|\n)*?"""', "", t)
    return re.sub(r"#.*", "", t)


def seed(db: str, *, age_minutes: float = 1.0, symbols=None) -> None:
    """Write one overnight vintage into a fresh store."""
    fetched = (dt.datetime.now(dt.timezone.utc)
               - dt.timedelta(minutes=age_minutes)).isoformat()
    store = observations.ObservationStore(db)
    rows = []
    vals = {"ES=F": (6512.25, 6498.50), "^VIX": (14.8, 15.6)}
    for sym in (symbols or vals):
        last, prior = vals[sym]
        slug = on.SYMBOLS[sym]
        for f, v in (("last", last), ("prior_settle", prior),
                     ("chg", last - prior),
                     ("chg_pct", 100 * (last - prior) / prior)):
            rows.append({"registry_key": on.registry_key(slug, f),
                         "instrument": sym, "observed_at": fetched,
                         "available_at": fetched, "value": v,
                         "source": "yfinance", "run_id": "seed"})
        if sym in on.CONTINUOUS:
            total = last - prior
            for name, v in (("tokyo", total * 0.6), ("europe", total * 0.3),
                            ("other", total * 0.1)):
                rows.append({"registry_key": on.registry_key(slug, f"attrib_{name}"),
                             "instrument": sym, "observed_at": fetched,
                             "available_at": fetched, "value": v,
                             "source": "yfinance", "run_id": "seed"})
    store.write_many(rows)
    store.close()


def group_a() -> None:
    print(f"{LINE}\nA. THE 07:00 RENDER FETCHES NOTHING (30.4)\n{LINE}")
    forbidden = ("requests", "urllib", "httpx", "yfinance.download",
                 "socket", "http.client", "urlopen")
    for f in (PKG / "morning_payload.py", PKG / "morning_render.py",
              PKG / "morning_anchor.py"):
        code = code_of(f).lower()
        hits = [w for w in forbidden if w in code]
        check(not hits,
              f"{f.name}: no HTTP or socket path ({hits or 'none'})")

    # It imports the fetch MODULE, which is correct and is not a fetch: it needs
    # SYMBOLS and registry_key() to know what to read. What it must not do is
    # call anything that opens a connection.
    code = code_of(PKG / "morning_payload.py")
    check("overnight as on" in code or "import overnight" in code,
          "the payload imports the fetch module for its key names")
    for call in ("on.pull(", "on.fetch(", "on._bars(", "on._yf("):
        check(call not in code,
              f"and never calls {call.rstrip('(')}() -- names, not network")


def group_b() -> None:
    print(f"\n{LINE}\nB. AN ABSENT BLOCK PUBLISHES A REASON, NOT SILENCE\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "empty.db")
        observations.ObservationStore(db).close()      # schema, no rows
        block = mp.overnight_block(db_path=db)
        check(block["state"] == "absent", "an empty store -> state=absent")
        check(bool(block["reason"]), "and a reason is recorded")
        check("06:45" in (block["reason"] or ""),
              "the reason names the 06:45 fetch, which is where to look")
        check("overnight --dry-run" in (block["reason"] or ""),
              "and the command that says which symbol failed")

        p = mp.build(db_path=db, sess="2026-09-18")
        html = mr.render(p)
        check("absent" in html.lower(),
              "the rendered report SHOWS the absence rather than omitting it")
        check(block["reason"].split(" -- ")[0][:20] in html
              or "06:45" in html,
              "and carries the reason into the HTML")
        check(any("overnight block absent" in w for w in p["warnings"]),
              "the payload warns, so the state row lands degraded")


def group_c() -> None:
    print(f"\n{LINE}\nC. STALE IS MARKED, NOT DROPPED\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "fresh.db")
        seed(db, age_minutes=2)
        b = mp.overnight_block(db_path=db)
        check(b["state"] == "ok" and not b["stale"],
              "a two-minute-old fetch is ok")

        db2 = str(Path(d) / "stale.db")
        seed(db2, age_minutes=mp.MAX_FETCH_AGE_MINUTES + 30)
        b2 = mp.overnight_block(db_path=db2)
        check(b2["state"] == "stale", "an old fetch -> state=stale")
        check(len(b2["rows"]) == 2,
              "the rows are STILL PRESENT -- dropping them would make a dead "
              "06:45 look like a quiet market")
        check(all(r.get("stale") for r in b2["rows"]),
              "and every one of them is flagged")
        html = mr.render(mp.build(db_path=db2, sess="2026-09-18"))
        check("stale" in html.lower(),
              "the reader is told, in the report, that these are not this "
              "morning's levels")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE RENDERER DOES NO ARITHMETIC\n{LINE}")
    code = code_of(PKG / "morning_render.py")
    # The renderer may format and may compare (colour by sign). It may not
    # derive a reported quantity, because then the number in the report has no
    # counterpart in the payload for an audit to check it against.
    for banned in ("/ 100", "* 100", "- prior", "prior_settle -", "sum("):
        check(banned not in code,
              f"morning_render.py contains no {banned!r}")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "x.db")
        seed(db)
        p = mp.build(db_path=db, sess="2026-09-18")
        html = mr.render(p)

        # Every figure printed for ES=F must be findable in the payload.
        row = next(r for r in p["overnight"]["rows"] if r["symbol"] == "ES=F")
        for field, dp in (("last", 2), ("prior_settle", 2)):
            shown = f"{row[field]:,.{dp}f}"
            check(shown in html,
                  f"ES=F {field} {shown} appears in the HTML as stored")
        check(f"{row['chg']:+,.2f}" in html,
              f"ES=F change {row['chg']:+,.2f} is the payload's, not recomputed")

        # The attribution legs sum to the change, so a reader can check them
        # against the level -- the property the fetcher computes and the report
        # must not disturb.
        legs = next(a for a in p["overnight"]["attribution"]
                    if a["symbol"] == "ES=F")
        total = legs["tokyo"] + legs["europe"] + legs["other"]
        check(abs(total - row["chg"]) < 1e-6,
              f"the three windows sum to the overnight change "
              f"({total:.4f} vs {row['chg']:.4f})")


def group_e() -> None:
    print(f"\n{LINE}\nE. THE FOOTER NAMES THE ARCHIVE PATH\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "x.db")
        seed(db)
        p = mp.build(db_path=db, sess="2026-09-18")

        html = mr.render(p, {"archive_path": "/home/ari/chester-reports/reports/m.html",
                             "delivery": "sent"})
        check("/home/ari/chester-reports/reports/m.html" in html,
              "the archive path is printed in the footer")
        check("before this message was sent" in html,
              "and the footer states the archive preceded the send")
        # L2(1) drops the delivery field from the close report's footer for the
        # same reason it is absent here: the emailed copy is built BEFORE the
        # send, so any delivery status it printed would be a guess.
        check("sent</code>" not in html and ">sent<" not in html,
              "the delivery status is NOT printed -- the mailed copy is built "
              "before the send and could only guess")

        bare = mr.render(p)
        check("n/a" in bare,
              "with no outcome yet the path renders as n/a rather than blank")

    entry = code_of(PKG / "morning_anchor.py")
    check("delivery.deliver(" in entry, "the entry point calls deliver()")
    check("delivery.archive(" in entry,
          "and archives directly on the dry-run path")


def group_f() -> None:
    print(f"\n{LINE}\nF. THE UNITS AND THE WRAPPER\n{LINE}")
    fetch_t = (UNITS / "chester-overnight.timer").read_text(encoding="utf-8")
    anchor_t = (UNITS / "chester-morning-anchor.timer").read_text(encoding="utf-8")
    anchor_s = (UNITS / "chester-morning-anchor.service").read_text(encoding="utf-8")
    fetch_s = (UNITS / "chester-overnight.service").read_text(encoding="utf-8")

    check("OnCalendar=Mon-Fri 06:45 America/New_York" in fetch_t,
          "the fetch fires 06:45 ET, zone-pinned (Mon-Fri; holidays are the "
          "wrapper's calendar guard)")
    check("OnCalendar=Mon-Fri 07:00 America/New_York" in anchor_t,
          "the anchor fires 07:00 ET, fifteen minutes later")
    check("Persistent=false" in fetch_t and "Persistent=false" in anchor_t,
          "neither is Persistent -- a catch-up run at noon would email a "
          "pre-open report to a reader already two hours into the session")

    # The jitter must not be able to push the fetch past the render.
    def delay(text):
        m = re.search(r"RandomizedDelaySec=(\d+)", text)
        return int(m.group(1)) if m else 0
    check(delay(fetch_t) + delay(anchor_t) < 15 * 60,
          f"the two jitters ({delay(fetch_t)}s + {delay(anchor_t)}s) cannot "
          f"close the fifteen-minute gap and cross the units over")

    check("After=chester-overnight.service" in anchor_s,
          "the anchor is ordered After= the fetch")
    for kw in ("Requires=", "BindsTo=", "Wants="):
        check(kw not in anchor_s,
              f"and NOT {kw.rstrip('=')} -- it must still publish an absent "
              f"block when the fetch failed, since silence hides the failure")

    check("SuccessExitStatus=0 2" in anchor_s,
          "0 and 2 are both successful runs of the anchor (delivery is transport)")
    check("SuccessExitStatus=0 2" not in fetch_s,
          "but not for the fetch -- 'nothing fetched' is a real failure of its "
          "one job and should show red")

    wrapper = (REPO / "scripts" / "run_morning_anchor.sh").read_text(encoding="utf-8")
    check("morning_heartbeat" in wrapper,
          "the wrapper writes a morning heartbeat")
    check(re.search(r"\$RC -eq 0.*\|\|.*\$RC -eq 2", wrapper) is not None,
          "on rc 0 or 2 only -- rc 1 means every block was empty and a warm "
          "heartbeat would assert a morning read that did not happen")
    check("is-session" in wrapper,
          "and asks the shared holiday table before running")

    checker = (REPO / "scripts" / "check_heartbeat.sh").read_text(encoding="utf-8")
    check("morning_heartbeat" in checker,
          "check_heartbeat.sh reads it, so a missed 07:00 is non-healthy")
    check("exit 5" in checker, "with its own exit code, distinct from the EOD's")


def main() -> int:
    print(f"{LINE}\nMorning anchor validation (no network, temporary store)\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

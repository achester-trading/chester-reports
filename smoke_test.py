"""
Smoke test: builds a synthetic observation store, runs the report the box runs,
and verifies it renders. No network, no real store, no API key.

Run: python smoke_test.py

-----------------------------------------------------------------------------
WHAT THIS EXERCISES, AND WHAT IT USED TO
-----------------------------------------------------------------------------

Until Phase 4b this test called `monthly_macro.writer.render_md.render_report`
over a synthetic CSV `Store` -- ten pillar pages and ten narrative placeholders.
That module is not on the report's path any more: `monthly_macro/run.py` builds a
payload from the observation store, renders six sections through
`writer/render_v2.py`, and archives through `daily_cascade.deliver`. A full-
pipeline test that exercised the old renderer was passing on a path nothing runs,
which is worse than no test: it reported green for a pipeline it had not touched.

So it now runs THE REAL PATH -- payload -> narrative (skipped, no key) ->
render_v2 -> build_html -> deliver.archive -- against a store this file builds.

THE ABSENCES ARE THE POINT. A synthetic store carries the 59 FRED series and
nothing else: no option chain, no register, no probability ledger, no prices. So
most of this report comes back absent, and what is asserted is the contract that
matters -- every absent section names a reason, the document renders anyway, and
nothing raises. A pipeline that only works with complete data is a pipeline that
fails on the first quiet feed.
"""

import datetime as dt
import os
import sys
import tempfile
import traceback

# Windows consoles default to cp1252, which cannot encode the check marks
# and box-drawing characters the report uses. Force UTF-8 on stdout.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# BOTH STORES REDIRECTED BEFORE THE FIRST IMPORT. observations.DEFAULT_DB reads
# CHESTER_DB at import time, so setting it afterwards would silently point this
# test at the real chester.db -- the register, the grades and the probability
# ledger -- and a test that writes into the evidence is not a test.
TMP = tempfile.mkdtemp(prefix="smoketest_")
os.environ["ALTDATA_STORE"] = os.path.join(TMP, "data_store")
os.environ["CHESTER_DB"] = os.path.join(TMP, "chester.db")
os.environ["SNAPSHOT_DIR"] = os.path.join(TMP, "snapshots")
# AND THE PIN LOG. The gamma dial reads `altdata.grader.PriceSeries`, which reads
# data/pin_log.csv rather than the observation store -- so without this line the
# test quietly read this box's real captures and returned a gamma state on a store
# that holds no option data at all. Read-only, so nothing was at risk; but a test
# whose result depends on a file it never mentions gives a different answer on a
# runner than on the box, and the whole point of a synthetic store is that it does
# not.
os.environ["CHESTER_PIN_LOG_PATH"] = os.path.join(TMP, "pin_log.csv")

import shutil                                                  # noqa: E402

import regime                                                  # noqa: E402
from altdata import config, observations, session               # noqa: E402
from daily_cascade import deliver as delivery                   # noqa: E402
from monthly_macro import payload as payload_mod                # noqa: E402
from monthly_macro.writer import render_v2                      # noqa: E402
from monthly_macro.writer.build_html import build_html          # noqa: E402


def synth_monthly_series(start_value, n=60, growth_per_yr=0.02):
    """Generate 5 years of monthly observations with mild growth."""
    rows = []
    today = dt.date.today().replace(day=1)
    monthly_growth = (1 + growth_per_yr) ** (1 / 12)
    v = start_value / (monthly_growth ** n)
    for i in range(n):
        d = today - dt.timedelta(days=30 * (n - i))
        rows.append((d.isoformat(), round(v, 4)))
        v *= monthly_growth
    return rows


def synth_daily_series(value, n=400):
    """Generate ~400 days of constant-ish daily observations."""
    rows = []
    today = dt.date.today()
    for i in range(n):
        d = today - dt.timedelta(days=(n - i))
        rows.append((d.isoformat(), round(value * (1 + ((i % 5) - 2) * 0.001), 4)))
    return rows


def populate(db):
    """Every configured FRED series, as observations with all three clocks."""
    rows = []
    for spec in config.FRED_SERIES:
        obs = (synth_monthly_series(start_value=100.0)
               if spec.freq in ("monthly", "quarterly", "weekly")
               else synth_daily_series(value=4.5))
        for day, value in obs:
            # available_at = the session's own evening. A synthetic vintage that
            # claimed to be knowable earlier than its observation would make the
            # replay assertions below meaningless.
            rows.append({"registry_key": f"fred.{spec.key}", "instrument": None,
                         "observed_at": day, "available_at": f"{day}T23:00:00Z",
                         "value": value, "source": "synthetic",
                         "availability_kind": "observed"})
    return db.write_many(rows)


def main():
    failures = []

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond:
            failures.append(msg)

    try:
        db = observations.ObservationStore()
        print(f"Smoke test store: {TMP}")
        n = populate(db)
        print(f"Wrote {n:,} synthetic observations "
              f"across {len(config.FRED_SERIES)} series")

        # --- THE OBJECT, COMPUTED AND STORED BY THE ONE WRITER ---------------
        # Not a hand-built dict: a fake object is a second place the object's
        # shape lives, and it goes stale the first time regime.py changes.
        obj = regime.compute(store=db)
        regime.store_object(obj, store=db)
        dials = {k: (v or {}).get("state") for k, v in (obj.get("dials") or {}).items()}
        print(f"Object stored for session {obj.get('session')}: dials {dials}")
        db.close()

        # --- THE REPORT'S OWN PATH ------------------------------------------
        p = payload_mod.build(run_id="smoke-test")
        check(p.get("report") == "monthly", "the payload names itself monthly")
        check(tuple(p.get("sections") or ()) == payload_mod.SECTIONS,
              "it carries its six sections in order")
        for name in payload_mod.SECTIONS:
            block = p.get(name) or {}
            if name == "alternative_assets":
                states = {f: (v or {}).get("state")
                          for f, v in (block.get("families") or {}).items()}
                check(all(s == "ok" or (block["families"][f].get("reason")
                                        or block["families"][f].get("why"))
                          for f, s in states.items()),
                      f"{name}: every family is ok or says why ({states})")
                continue
            state = block.get("state")
            check(state == "ok" or bool(block.get("reason")),
                  f"{name}: {state}" + ("" if state == "ok" else " WITH a reason"))

        # THE NARRATIVE IS NOT CALLED. No key, and a smoke test that made a
        # network call would fail on a runner for a reason that is not a defect.
        md = render_v2.render(p, narrative=None)
        check("# Monthly Regime & Allocation" in md, "the masthead renders")
        for heading in ("## I. Regime", "## II. Scenarios", "## III. Top & Bottom",
                        "## IV. Alternative Assets", "## V. The register's month",
                        "## Appendix"):
            check(heading in md, f"section renders: {heading}")
        check("NARRATIVE PLACEHOLDER" not in md,
              "and NO placeholder marker survives -- the markers that asked prose "
              "for a regime are deleted, not repointed")
        check("Pillar 1" in md and "dial: macro" in md,
              "the pillars appear as inputs beneath the dial they feed")
        print(f"Markdown rendered: {len(md):,} chars")

        html = build_html(md)
        check("<details" in html, "the accordion is built")
        check("navy" in html.lower(), "the navy styling is present")
        check(html.count("<details ") == html.count("</details>"),
              "details tags balance")
        print(f"HTML built: {len(html):,} chars, "
              f"{html.count('<details ')} accordions, "
              f"{html.count('<table>')} tables")

        # --- ARCHIVE THROUGH THE ONE ARCHIVE PATH ---------------------------
        outdir = os.path.join(TMP, "reports")
        md_path = delivery.archive(md, "smoke_monthly.md", outdir)
        html_path = delivery.archive(html, "smoke_monthly.html", outdir)
        check(os.path.getsize(md_path) > 0 and os.path.getsize(html_path) > 0,
              f"archived through deliver(): {os.path.basename(md_path)}, "
              f"{os.path.basename(html_path)}")

        # --- A PAST CUTOFF SEES NOTHING AFTER ITSELF ------------------------
        cutoff_day = (dt.date.today() - dt.timedelta(days=120)).isoformat()
        past = payload_mod.build(as_of=f"{cutoff_day}T23:59:59Z")
        late = [r["metric"]
                for v in (past.get("appendix") or {}).get("pillars", {}).values()
                for r in v.get("series") or []
                if r.get("observed_at") and str(r["observed_at"])[:10] > cutoff_day]
        check(not late,
              f"a build as-of {cutoff_day} reads nothing observed after it "
              f"({len(late)} leaks)")

        if failures:
            print(f"\n❌ SMOKE TEST FAILED -- {len(failures)} check(s)")
            for f in failures:
                print(f"   {f}")
            sys.exit(1)
        print("\n✅ SMOKE TEST PASSED")

    except Exception:
        print("\n❌ SMOKE TEST FAILED")
        traceback.print_exc()
        sys.exit(1)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

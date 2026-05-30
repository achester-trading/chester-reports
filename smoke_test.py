"""
Smoke test: builds a synthetic store, runs the full report pipeline, and
verifies the outputs render without errors. No network required.

Run: python smoke_test.py
"""

import os
import sys
import datetime as dt
import shutil
import tempfile
import traceback

# Make sure we use a temp store
TMP_STORE = tempfile.mkdtemp(prefix="smoketest_store_")
os.environ["ALTDATA_STORE"] = TMP_STORE

from altdata import config
from altdata.store import Store
from monthly_macro.writer.render_md import render_report
from monthly_macro.writer.build_html import build_html


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
        # tiny jitter
        rows.append((d.isoformat(), round(value * (1 + ((i % 5) - 2) * 0.001), 4)))
    return rows


def main():
    try:
        store = Store(TMP_STORE)
        print(f"Smoke test store: {TMP_STORE}")

        # Populate a synthetic dataset that covers every series in config
        for spec in config.FRED_SERIES:
            if spec.freq == "monthly" or spec.freq == "quarterly" or spec.freq == "weekly":
                obs = synth_monthly_series(start_value=100.0)
            else:
                obs = synth_daily_series(value=4.5)
            store.write_observations(spec.key, obs, source="synthetic")

        print(f"Wrote {len(config.FRED_SERIES)} synthetic series")

        # Construct a fake fetch summary
        fetch_summary = {
            "total": len(config.FRED_SERIES),
            "success": len(config.FRED_SERIES),
            "failed": [],
            "series": {},
        }

        # Render
        md = render_report(store, fetch_summary)
        assert "Monthly Macro Report" in md, "Title missing"
        assert "Pillar 1" in md, "Pillar 1 missing"
        assert "Appendix A" in md, "Appendix A missing"
        assert "Pillar Snapshot" in md, "Pillar Snapshot missing"
        print(f"Markdown rendered: {len(md):,} chars")

        # Build HTML
        html = build_html(md)
        assert "<details" in html, "Accordion missing in HTML"
        assert "navy" in html.lower(), "Navy styling missing"
        assert html.count("<details ") == html.count("</details>"), "Details tag balance broken"
        print(f"HTML built: {len(html):,} chars")
        print(f"  Accordions: {html.count('<details ')}")
        print(f"  Tables: {html.count('<table>')}")

        # Write to a temp output for inspection
        outdir = "/tmp/smoke_out"
        os.makedirs(outdir, exist_ok=True)
        md_path = os.path.join(outdir, "smoke.md")
        html_path = os.path.join(outdir, "smoke.html")
        open(md_path, "w").write(md)
        open(html_path, "w").write(html)
        print(f"Outputs: {md_path}, {html_path}")
        print("\n✅ SMOKE TEST PASSED")

    except Exception:
        print("\n❌ SMOKE TEST FAILED")
        traceback.print_exc()
        sys.exit(1)
    finally:
        shutil.rmtree(TMP_STORE, ignore_errors=True)


if __name__ == "__main__":
    main()

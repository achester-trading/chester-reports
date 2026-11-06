#!/usr/bin/env python3
"""
Validation gate: b51-registry-html -- what the box evening of 20 Oct 2026 turned
up in the store-registry check and the HTML editions. On synthetic fixtures; no
network, no model, no live store (each store here is the gate's own).

  A  THE CLOCK. The store check counts sessions on the ET calendar up to the last
     completed session, never to the UTC date: an as-of of 00:47 UTC on a
     Wednesday counts Tuesday as the last session, so a session-half-life key
     last written on Monday is 1 session old, not 2.
  B  THE ALLOWANCES. config/publication_lags.yaml: every family states its id,
     source, reason, lag and bound; no lag exceeds its bound; every family
     matches a registered key; the one staleness rule (derived) adds the lag, and
     a key with no family keeps its cadence's allowance. A key past three times
     its allowance prints "dead?", whatever its lag.
  C  THE THREE UNREGISTERED KEYS. market_state and fred.series_release_map are
     declared stored objects, yfinance.mkt_usdcnh a superseded name, so none is
     unregistered and the superseded key is never stale.
  D  THE SYNTHETIC ROWS. Nothing in the repository reads a synthetic.* key.
     altdata/purge_synthetic: the dry run deletes nothing; --apply refuses without
     a NEW backup; with one it backs up, checks, and deletes only rows that are
     both under synthetic.* and of source 'synthetic'.
  E  THE HTML EDITIONS. Lists nested two or three spaces in render nested; fenced
     code is left alone; "- [ ]" prints a checkbox mark; figure ids are namespaced
     by each figure's own number and unique across the edition (the Master Guide
     built: its five figures f01 to f05, no id twice, its Part 4 and Part 6 lists
     nested, no "[ ]" left).

    python tools/validate_b51_registry_html.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("b51_registry_html_"))
LINE = "=" * 78
PASS = FAIL = 0
TUESDAY_EVENING = "2026-10-21T00:47:00+00:00"   # 20:47 ET, Tuesday 20 Oct 2026
WEDNESDAY_EVENING = "2026-10-21T22:00:00+00:00"  # 18:00 ET, Wednesday 21 Oct


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def store(name: str, rows: list[tuple]) -> str:
    """A synthetic observation store: rows of (key, observed_at, value, source)."""
    from altdata import observations                            # noqa: PLC0415
    p = TD / f"{name}.db"
    with observations.ObservationStore(str(p)) as st:
        for key, day, v, src in rows:
            st.write(key, None, day, f"{day}T21:00:00+00:00", v, src)
    return str(p)


def group_a() -> None:
    from altdata import session                                 # noqa: PLC0415
    import check_store_registry as csr                          # noqa: PLC0415
    head("A. THE CLOCK: THE ET SESSION CALENDAR, TO THE LAST COMPLETED SESSION")
    check(session.last_completed_session(TUESDAY_EVENING).isoformat() == "2026-10-20",
          "an as-of of 00:47 UTC on Wednesday 21 Oct counts Tuesday 20 Oct as the last "
          "session")
    key = "corr.stock_bond.spx_tlt.60d"             # half-life 'session': 1 allowed
    db = store("clock", [(key, "2026-10-19", 0.1, "derived_state")])
    r = csr.check(db, TUESDAY_EVENING)
    check(r["last_session"] == "2026-10-20" and not [s for s in r["stale"] if s["key"] == key],
          f"a session key last written on Monday is 1 session old on Tuesday evening, "
          f"not stale ({[s for s in r['stale'] if s['key'] == key]})")
    r2 = csr.check(db, WEDNESDAY_EVENING)
    s2 = [s for s in r2["stale"] if s["key"] == key]
    check(s2 and s2[0]["sessions"] == 2 and s2[0]["allowance"] == 1,
          f"and on Wednesday evening it is 2 sessions against 1: stale ({s2})")
    src = (REPO / "tools" / "check_store_registry.py").read_text(encoding="utf-8")
    check("as_of[:10])" not in src and "last_completed_session(" in src,
          "the check no longer counts to the UTC date")


def group_b() -> None:
    import yaml                                                 # noqa: PLC0415
    from altdata import derived                                 # noqa: PLC0415
    import check_store_registry as csr                          # noqa: PLC0415
    head("B. THE ALLOWANCES: EACH SOURCE'S PUBLICATION LAG, SESSION-SET AND BOUNDED")
    fams = derived.publication_lags(REPO / "config" / "publication_lags.yaml")
    res = derived.resolve_registry(yaml.safe_load(
        (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")))
    bad_fields = [f.get("id") for f in fams
                  if not all(f.get(x) for x in ("id", "source", "reason"))
                  or not isinstance(f.get("lag_sessions"), int)
                  or not isinstance(f.get("max_lag"), int)]
    over = [f["id"] for f in fams if f["lag_sessions"] > f["max_lag"]]
    unmatched = [f["id"] for f in fams
                 if not any(derived.publication_lag(res[k], k, [f])[0] for k in res)]
    check(fams and not bad_fields and not over and not unmatched
          and len({f["id"] for f in fams}) == len(fams),
          f"{len(fams)} families, each with its source, reason, lag and bound; none over "
          f"its bound ({over or 'none'}); each matches a registered key "
          f"(unmatched: {unmatched or 'none'})")
    want = {"fred.usd_eur": ("fred_h10", 2 + 6), "fred.brent": ("eia_spot", 2 + 6),
            "calc.naive_expectation.dxy": ("fred_h10", 8),
            "fred.cpi": ("fred_monthly_release", 32 + 22),
            "tic.holdings_by_country": ("tic", 32 + 45),
            "calc.attr_kw_tp_share_20d": ("term_premium_models", 2 + 5)}
    got = {k: (derived.publication_lag(res[k], k)[1],
               derived.staleness_allowance_of(res[k], k)[0]) for k in want}
    check(got == want, f"the one staleness rule adds each family's lag ({got})")
    check(derived.staleness_allowance_of(res["fred.yield_10y"], "fred.yield_10y")[0] == 2
          and derived.staleness_allowance_of(
              res["corr.stock_bond.spx_tlt.60d"], "corr.stock_bond.spx_tlt.60d")[0] == 1,
          "a key with no family keeps its cadence's allowance (the 10-year 2; a "
          "correlation 1)")
    db = store("dead", [("fred.usd_eur", "2026-07-01", 1.1, "fred"),
                        ("fred.usd_jpy", "2026-10-13", 150.0, "fred")])
    r = csr.check(db, TUESDAY_EVENING)
    by = {s["key"]: s for s in r["stale"]}
    check("fred.usd_jpy" not in by and by.get("fred.usd_eur", {}).get("dead") is True,
          f"H.10's week-old print is inside its lag; a print from July is past three "
          f"times the allowance and marked dead? ({by.get('fred.usd_eur')})")
    check("dead? fred.usd_eur" in csr.report(r),
          "the report prints the dead? mark")


def group_c() -> None:
    import check_store_registry as csr                          # noqa: PLC0415
    head("C. MARKET_STATE, THE RELEASE MAP AND THE OLD CNH CLOSE")
    db = store("three", [("market_state", "2026-10-20", '{"session": "2026-10-20"}',
                          "regime"),
                         ("fred.series_release_map", "2026-09-20", '{"CPIAUCSL": 10}',
                          "fred"),
                         ("yfinance.mkt_usdcnh", "2026-10-03", 7.1, "yfinance")])
    r = csr.check(db, TUESDAY_EVENING)
    three = {"market_state", "fred.series_release_map", "yfinance.mkt_usdcnh"}
    check(not (three & set(r["unregistered"])),
          f"none of the three is unregistered ({sorted(three & set(r['unregistered']))})")
    check(not [s for s in r["stale"] if s["key"] == "yfinance.mkt_usdcnh"],
          "the superseded CNH close is never stale")


def group_d() -> None:
    from altdata import observations, purge_synthetic as ps     # noqa: PLC0415
    head("D. THE SYNTHETIC ROWS: NOTHING READS THEM; THE PURGE IS AUDITED")
    allowed = {"altdata/purge_synthetic.py", "tools/validate_b51_registry_html.py"}
    readers = []
    for p in list(REPO.glob("*.py")) + [q for d in ("altdata", "daily_cascade",
                                                   "monthly_macro", "register", "alpha",
                                                   "alpha_proposer", "tools", "state")
                                       for q in (REPO / d).rglob("*.py")]:
        rel = p.relative_to(REPO).as_posix()
        if rel in allowed:
            continue
        if re.search(r"""["']synthetic\.[a-z_]""", p.read_text(encoding="utf-8",
                                                                errors="replace")):
            readers.append(rel)
    check(not readers, f"no module names a synthetic.* key ({readers or 'none'})")
    db = store("synth", [("synthetic.cpi", "2026-09-01", 1.0, "synthetic"),
                         ("synthetic.cpi", "2026-08-01", 0.9, "synthetic"),
                         ("synthetic.gdp", "2026-07-01", 2.0, "synthetic"),
                         ("synthetic.other", "2026-07-01", 2.0, "fred"),
                         ("fred.cpi", "2026-09-01", 3.0, "synthetic"),
                         ("fred.cpi", "2026-08-01", 3.1, "fred")])
    lines: list[str] = []
    rc = ps.run(db, apply=False, out=lines.append)
    n = sqlite3.connect(db).execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    check(rc == 0 and n == 6 and any("3 synthetic rows" in x for x in lines)
          and any("nothing deleted" in x for x in lines),
          f"the dry run counts 3 rows in 2 keys and deletes nothing ({lines[:1]})")
    check(ps.run(db, apply=True, out=lines.append) == 2,
          "--apply without --backup is refused")
    taken = TD / "taken.db"
    taken.write_text("x", encoding="utf-8")
    check(ps.run(db, apply=True, backup=str(taken), out=lines.append) == 2,
          "--apply onto an existing backup path is refused")
    bk = TD / "backups" / "pre-purge.db"
    out: list[str] = []
    rc = ps.run(db, apply=True, backup=str(bk), out=out.append)
    conn = sqlite3.connect(db)
    left = conn.execute("SELECT registry_key, source FROM observations "
                        "ORDER BY registry_key, source").fetchall()
    conn.close()
    check(rc == 0 and bk.is_file() and not observations.integrity_check(bk)
          and any(x.startswith("backup ok") for x in out),
          "the apply makes a NEW backup and integrity-checks it first")
    check(left == [("fred.cpi", "fred"), ("fred.cpi", "synthetic"),
                   ("synthetic.other", "fred")],
          f"only rows both under synthetic.* and of source 'synthetic' go ({left})")


def group_e() -> None:
    import build_paper_html as b                                # noqa: PLC0415
    head("E. THE HTML EDITIONS: NESTED LISTS, CHECKBOXES, FIGURE IDS")
    md = "- parent\n  - child two in\n    - grandchild\n\n1. step\n   - under a numbered item\n"
    out = b.commonmark_lists(md)
    check(out.split("\n")[:3] == ["- parent", "    - child two in", "        - grandchild"]
          and "    - under a numbered item" in out,
          f"two- and three-space nests become four a level ({out.splitlines()})")
    import markdown                                             # noqa: PLC0415
    html = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"]).convert(out)
    check(html.count("<ul>") == 4 and "- child" not in html,
          "and render as nested lists, no literal '- ' left")
    fenced = "- item\n\n  ```\n  - not a list\n  ```\n"
    check("- not a list" in b.commonmark_lists("```\n  - not a list\n```"),
          "fenced code outside a list is left as written")
    check(b.commonmark_lists(fenced).count("- not a list") == 1, "and inside one")
    t = b.task_marks("<ul>\n<li>[ ] open</li>\n<li>[x] done</li>\n</ul>")
    check("[ ]" not in t and "&#9744;" in t and "&#9745;" in t and 'class="task"' in t,
          "'- [ ]' and '- [x]' print checkbox marks")
    seen: set = set()
    tags = [b.figure_tag(c, seen) for c in ("Figure 3 — a", "Figure 3 — again",
                                           "Figure 12b — panel", "no number")]
    check(tags[0] == "f03" and tags[2] == "f12b" and len(set(tags)) == 4,
          f"a figure is tagged by its own number, unique across the edition ({tags})")
    html, report = b.build(REPO / "docs" / "master-guide.md")
    ids = re.findall(r'\bid="(f\d[^"]*)"', html)
    dup = [k for k, v in Counter(ids).items() if v > 1]
    figs = sorted({i.split("-")[0] for i in ids})
    check(figs == ["f01", "f02", "f03", "f04", "f05"] and not dup and not report,
          f"the Master Guide: its five figures f01 to f05, no id twice ({figs}; dup "
          f"{dup[:3] or 'none'})")
    i = html.find("Option chains and the dealer engine")
    check(i > 0 and "<ul>" in html[i:i + 4000][html[i:i + 4000].find("<li>"):]
          and "[ ]" not in html and "&#9744;" in html,
          "its Part 4 section 3 nests its lists, and Part 7's checklist prints boxes")


def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
        group_d()
        group_e()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

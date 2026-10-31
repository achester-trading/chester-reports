#!/usr/bin/env python3
"""
Validation gate: the price sources' per-family switch (A96; tranche 2b of the
price-source migration, decisions 4 and 5 ruled D38). Fixtures only; a switched
family is a config held in memory, never the shipped file.

  A  THE DEFAULT     every family ships on yfinance, and every moved reader -- the
                     tape, the correlation universe, batch 3, the horizon charts, the
                     Quarterly's chapters, the move screen, the rates shape, the
                     consistency aliases -- gets the key it read before
  B  A SWITCH        a switched family resolves to the FRED key, its break label
                     carries the date and prints once per family, beneath the tape
                     table; unswitched, no label and no new field
  C  NO HARD CODE    no reader under daily_cascade/, monthly_macro/, altdata/ or
                     config/ names ^TNX's, ^TYX's or the dollar index's key, but for
                     the declared exemptions (the writer, the instrument identity, the
                     existing cross-source pairs, the switch file itself)
  D  NO SPLICE       across a switch a chart draws two series and the break, never
                     one series running through it
  E  PINS AND PAIRS  a pinned reference keeps its source; the inactive pairs resolve
                     and are not in the quality check's active list
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from altdata import price_sources as ps                        # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
OLD = {"yfinance.mkt_tnx", "yfinance.mkt_tyx", "yfinance.mkt_dxy"}
# Where an old key may still be named, and why.
EXEMPT = {
    "altdata/sources/yfinance_source.py": "the writer of the keys",
    "config/security_master.yaml": "the instrument's identity (store_key)",
    "config/data_quality.yaml": "the existing ^TNX/DGS10 and ^TYX/DGS30 cross-source pairs",
    "config/price_sources.yaml": "the switch itself",
}


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


def switched(*families: str) -> dict:
    c = copy.deepcopy(ps.config())
    for f in families:
        c["families"][f]["source"] = "fred"
        c["families"][f]["switched_on"] = "2026-11-23"
    return c


class Using:
    """The resolver's cached config replaced for the block, then restored."""

    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg

    def __enter__(self):
        self.saved = ps._CFG                                    # noqa: SLF001
        ps._CFG = self.cfg                                      # noqa: SLF001
        return self

    def __exit__(self, *a):
        ps._CFG = self.saved                                    # noqa: SLF001


def group_a() -> None:
    head("A. THE DEFAULT")
    ps.reset()
    fams = ps.config()["families"]
    check(all(f["source"] == "yfinance" for f in fams.values()),
          f"every family ships on yfinance ({sorted(fams)})")
    check(ps.key("us_yields", "y10") == "yfinance.mkt_tnx"
          and ps.key("us_yields", "y30") == "yfinance.mkt_tyx"
          and ps.key("dollar_index", "dxy") == "yfinance.mkt_dxy",
          "the three keys resolve to Yahoo's, as read before")
    from altdata import bars, batch3, correlation           # noqa: PLC0415
    tape = {t["id"]: t.get("daily") for t in bars.tape()}
    check(tape.get("y10") == "yfinance.mkt_tnx" and tape.get("y30") == "yfinance.mkt_tyx"
          and tape.get("dxy") == "yfinance.mkt_dxy", "the tape's loader resolves them")
    correlation._CFG = None                                     # noqa: SLF001
    uni = {u["id"]: u.get("key") for u in correlation.config().get("universe") or []}
    check(uni.get("dxy") == "yfinance.mkt_dxy", "the correlation universe resolves the dollar")
    check((batch3.config().get("buybacks") or {}).get("thirty_year_tape")
          == "yfinance.mkt_tyx", "batch 3's thirty-year tape resolves")
    import horizon_charts as hc                                 # noqa: PLC0415
    hcfg = hc.load_config()
    uni2, _origin = hc.universe(hcfg)
    keys = [u.get("key") for u in uni2] + [
        s.get("key") for blk in (hcfg.get("panels") or {}).values() if isinstance(blk, dict)
        for s in (blk.get("series") or []) if isinstance(s, dict)]
    check("yfinance.mkt_dxy" in keys and not any(str(k).startswith("price:") for k in keys),
          "the horizon charts' config and universe resolve")
    from monthly_macro import quarterly_items as qi             # noqa: PLC0415
    qtxt = str(qi.load_config())
    check("price:" not in qtxt and "yfinance.mkt_dxy" in qtxt and "fred.dxy" in qtxt,
          "the Quarterly's chapters resolve, the twin chart keeping both indices")
    from altdata import rates_shape                             # noqa: PLC0415
    from daily_cascade import consistency                       # noqa: PLC0415
    check(rates_shape.ten_year_legs() == (("fred.yield_10y", "FRED"),
                                         ("yfinance.mkt_tnx", "Yahoo Finance"))
          and consistency.ALIASES["y10"] == ("y10", "yfinance.mkt_tnx", "fred.yield_10y")
          and consistency.ALIASES["y30"] == ("y30", "yfinance.mkt_tyx", "fred.yield_30y"),
          "the rates shape's legs and the consistency aliases are as they were")
    from daily_cascade import weekly_sections as ws              # noqa: PLC0415
    tt = ws.tape_table({"instruments": []})
    check("break_labels" not in tt["table"], "unswitched, the tape table carries no new field")


def group_b() -> None:
    head("B. A SWITCH")
    with Using(switched("us_yields")):
        check(ps.key("us_yields", "y10") == "fred.yield_10y"
              and ps.resolve("price:us_yields.y30") == "fred.yield_30y"
              and ps.key("dollar_index", "dxy") == "yfinance.mkt_dxy",
              "a switched family resolves to FRED; the other is untouched")
        lab = ps.break_label("us_yields")
        check(lab and lab.startswith("series change 2026-11-23: FRED's constant-maturity")
              and lab.endswith("not spliced"), f"the label carries the date ({lab})")
        labs = ps.labels_for(["yfinance.mkt_tnx", "fred.yield_30y", "fred.yield_10y"])
        check(labs == [lab], "a block printing both yields owes the label once")
        from daily_cascade import weekly_sections as ws          # noqa: PLC0415
        from daily_cascade import stack_render as sr             # noqa: PLC0415
        tt = ws.tape_table({"instruments": []})
        check(tt["table"].get("break_labels") == [lab],
              "the tape table carries the label")
        html = sr._table({"columns": ["Market", "Last"], "rows": [["10-year", "4.20%"]],  # noqa: SLF001
                          "break_labels": [lab]})
        check(html.index("4.20%") < html.index("series change") and html.count("series change") == 1,
              "it prints once, beneath the table holding the first figure")
        segs = ps.segments("us_yields", "y10")
        check([s["key"] for s in segs] == ["yfinance.mkt_tnx", "fred.yield_10y"]
              and segs[0]["to"] == segs[1]["from"] == "2026-11-23",
              "history: the old key up to the switch, the new key from it")
    check(ps.break_label("us_yields") is None, "back on yfinance, no label")


def group_c() -> None:
    head("C. NO HARD CODE")
    rx = re.compile("|".join(re.escape(k) for k in OLD))
    hits = []
    for d in ("daily_cascade", "monthly_macro", "altdata", "config"):
        for f in (REPO / d).rglob("*"):
            if f.suffix not in (".py", ".yaml", ".sh") or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(REPO).as_posix()
            if rel in EXEMPT:
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{n}")
    check(not hits, f"no reader names the three keys outside the exemptions ({hits[:6]})")
    check(all((REPO / p).exists() for p in EXEMPT),
          f"each exemption is a real file: {sorted(EXEMPT)}")


def group_d() -> None:
    head("D. NO SPLICE")
    old = [("2026-11-18", 99.1), ("2026-11-19", 99.3), ("2026-11-20", 99.0),
           ("2026-11-23", 98.9)]
    new = [("2026-11-19", 121.0), ("2026-11-20", 121.2), ("2026-11-23", 121.1),
           ("2026-11-24", 121.4)]
    sp = ps.split_points(old, new, "2026-11-23")
    check(len(sp["series"]) == 2 and sp["break"] == "2026-11-23"
          and all(d < "2026-11-23" for d, _ in sp["series"][0])
          and all(d >= "2026-11-23" for d, _ in sp["series"][1]),
          "across a switch: two series, the old before the break, the new from it")
    check(ps.split_points(old, new, None) == {"series": [old], "break": None},
          "unswitched: the one series as it was")
    import matplotlib                                           # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                             # noqa: PLC0415
    fig, ax = plt.subplots()
    drawn = ps.plot_split(ax, sp, ("DXY", "Broad dollar"))
    xs = [[str(x) for x in ln.get_xdata()] for ln in drawn]
    check(len(drawn) == 2 and not any(any(x < "2026-11-23" for x in a) and
                                      any(x >= "2026-11-23" for x in a) for a in xs)
          and any(ln.get_linestyle() == "--" for ln in ax.lines),
          "the chart draws two lines and a dashed break; no line crosses the break")
    plt.close(fig)
    with Using(switched("dollar_index")):
        check(ps.switch_date_of("yfinance.mkt_dxy") == "2026-11-23"
              and ps.switch_date_of("yfinance.mkt_tnx") is None,
              "a chart leg knows its family's switch date, and only its own")


def group_e() -> None:
    head("E. PINS AND PAIRS")
    with Using(switched("dollar_index")):
        check(ps.resolve("price:dollar_index.dxy@yfinance") == "yfinance.mkt_dxy"
              and ps.resolve("price:dollar_index.dxy") == "fred.dxy",
              "switched, a pinned reference keeps Yahoo's key; the plain one moves")
    import yaml                                                 # noqa: PLC0415
    dq = yaml.safe_load((REPO / "config" / "data_quality.yaml").read_text(encoding="utf-8"))
    ip = dq.get("inactive_pairs_fred") or []
    resolved = [(ps.resolve(p["a"]), ps.resolve(p["b"])) for p in ip]
    active = {(p.get("a"), p.get("b")) for p in (dq.get("pairs") or {}).get("list") or []}
    check(len(ip) == 3 and all(p["active"] is False and "measured on the overlap" in p["tolerance"]
                               for p in ip)
          and resolved == [("yfinance.mkt_dxy", "fred.dxy"),
                           ("yfinance.mkt_tnx", "fred.yield_10y"),
                           ("yfinance.mkt_tyx", "fred.yield_30y")]
          and not any(str(a).startswith("price:") for a, _ in active),
          "the three inactive pairs resolve, tolerance to be measured, none in the active list")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

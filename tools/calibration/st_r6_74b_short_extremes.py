"""
ST-R6.74b -- leveraged funds' extreme net shorts in ES against the S&P 500's 5- and
20-session outcome (signal-triage Batch 15, item 74, written as 67; b56-batch15-2).
A dated ledger, report only.

    python tools/calibration/st_r6_74b_short_extremes.py --db PATH [--out DIR] [--date D]

THE PRE-REGISTRATION is docs/ledgers/short-extremes-preregistration-2026-10.md,
committed alone before this script and never edited (tools/validate_batch15_2.py
holds its SHA-256). The rule is applied by altdata/hf_positioning.ledger; this
script reads the stored series and writes the edition, nothing else.

STORED HISTORY ONLY, as the paste rules: the store at --db is opened read-only
(`mode=ro`), the newest vintage of each observation read; nothing is fetched.
A store without the ES rows (before the TFF pull carries ES) gives n 0 and
INSUFFICIENT, which is the honest first edition.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from altdata import hf_positioning as hf                         # noqa: E402

ITEM = "ST-R6.74b"
NET_OI, INSTRUMENT, SPX = "cftc.tff_lev_money_net_oi", "ES", "yfinance.mkt_gspc"


def stored(db: str, key: str, instrument=None) -> list[tuple[str, float]]:
    """The newest vintage per observed day, read-only."""
    p = Path(db)
    if not p.exists():
        return []
    conn = sqlite3.connect(f"{p.resolve().as_uri()}?mode=ro", uri=True)
    try:
        q = ("SELECT substr(observed_at, 1, 10), value_num FROM observations "
             "WHERE registry_key = ? AND value_num IS NOT NULL AND "
             + ("instrument = ?" if instrument else "instrument IS NULL")
             + " ORDER BY observed_at, available_at")
        rows = conn.execute(q, (key, instrument) if instrument else (key,)).fetchall()
    finally:
        conn.close()
    out: dict[str, float] = {}
    for d, v in rows:
        out[d] = float(v)
    return sorted(out.items())


def render(res: dict, as_of: str, db: str, sha: str) -> str:
    r = res["result"]
    w = r.get("window")

    def pct(x):
        return "—" if x is None else f"{x:+.2f}%"
    share = ("—" if r["share_positive"] is None else
             f"{r['share_positive'] * 100:.0f}%")
    why = ("no ES rows in the store yet (the TFF pull adds ES from this build)"
           if not w else f"{r['n']} episodes against the rule's {hf.RULE['min_episodes']}"
           if r["verdict"] == "INSUFFICIENT" else
           f"lift {r['lift_pp']:+.2f} pp (rule: at least {hf.RULE['median_lift_pp']:.1f}); "
           f"{share} positive (rule: at least {hf.RULE['share_positive'] * 100:.0f}%)")
    lines = [
        f"# {ITEM} ledger -- leveraged funds' extreme net shorts in ES and the S&P 500 "
        f"after (item 74)",
        "",
        f"**Edition:** {as_of}, read-only from the store `{Path(db).name}` (stored history "
        f"only; nothing fetched). A run against the box's store supersedes it (a new "
        f"dated file).",
        "",
        f"**The pass rule is pre-registered**: "
        f"`docs/ledgers/short-extremes-preregistration-2026-10.md`, SHA-256 `{sha}`, "
        f"committed alone before any scoring code and never edited.",
        "",
        "| | |",
        "|---|---|",
        f"| As of | {as_of} |",
        f"| Window | {'none ranked' if not w else f'report weeks {w[0]} to {w[1]}'}; each "
        f"week ranked against the 260 reports ending at it |",
        f"| n | {r['n']} (pending {r['pending']}; baseline {r['baseline_n']} weeks) |",
        "| Statistic | the S&P 500's median 20-session outcome after an episode's first "
        "week (ES's leveraged-fund net short at or above its 90th percentile of five "
        "years), against every ranked week's, and the share of episodes positive |",
        f"| Pass rule (as pre-registered) | INSUFFICIENT below {hf.RULE['min_episodes']} "
        f"episodes; PASS when the episodes' median 20-session outcome beats the "
        f"baseline's by at least {hf.RULE['median_lift_pp']:.1f} pp and at least "
        f"{hf.RULE['share_positive'] * 100:.0f}% are positive; FAIL otherwise |",
        f"| Verdict | **{r['verdict']} -- {why}** |",
        "| Rights consequence | Grants nothing: the squeeze-risk flag keeps a flag's "
        "rights, and any T&B or Book modifier is the operator's ruling. The verdict "
        "reaches the register only as a rule-31 draft. |",
        "",
        "## Results",
        "",
        f"- Episodes: median 20-session outcome {pct(r['median_long'])}, 5-session "
        f"{pct(r['median_short'])}; {share} with a positive 20-session outcome.",
        f"- Baseline: median 20-session {pct(r['baseline_long'])}, 5-session "
        f"{pct(r['baseline_short'])}.",
        "- The episodes are in the CSV beside this file.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="st_r6_74b_short_extremes")
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", default=str(REPO / "docs" / "ledgers"))
    ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args(argv)
    sha = hf.prereg_sha256()
    if sha != hf.PREREG_SHA256:
        print(f"refused: the pre-registration's SHA-256 is {sha}, not the registered one")
        return 2
    res = hf.ledger(stored(a.db, NET_OI, INSTRUMENT), stored(a.db, SPX))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    md = out / f"st-r6.74b-ledger-{a.date}.md"
    if md.exists():
        print(f"refused: {md} exists (an edition is never rewritten)")
        return 2
    md.write_text(render(res, a.date, a.db, sha), encoding="utf-8", newline="\n")
    with open(out / f"st-r6.74b-episodes-{a.date}.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh, lineterminator="\n")
        wr.writerow(["week", "release", "entry", "short_oi_pct", "percentile", "r5", "r20"])
        for e in res["episodes"]:
            wr.writerow([e["week"], e["release"], e["entry"], e["short_oi_pct"],
                         e["percentile"], e.get("r5"), e.get("r20")])
    print(f"{ITEM}: {res['result']['verdict']}, n {res['result']['n']} -> {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

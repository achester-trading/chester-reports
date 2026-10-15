#!/usr/bin/env python3
"""
Assign a lens family to every registry series, once (6e; the metric-lenses
brief of 1 Oct, ratified at the Doctrine monthly of 3-4 Oct, item 6).

    python tools/assign_families.py --report docs/briefs/6e-family-assignments.md
    python tools/assign_families.py --write      # edits metrics_registry.yaml in place

The registry then carries the family of every level series, three ways:
  - `families:`         key -> family, for individually registered metrics (the
                        map batch 3 began; check_registry holds it);
  - a block's `family`  for a bulk block whose members are one family;
  - `member_families`   on a mixed block (the FRED blocks, the closes), store
                        key -> family.
A series that is not a level -- a flag, a label, a date, a corporate action, a
log's column -- takes no family and is named in `lens_excluded` with its reason.

The rules, in order: the ratified assignments (minutes item 6e); what the
registry already declares; the FRED members by hand (FRED_FAMILIES below); then
the registry `units`, with a key-pattern refinement. Every assignment a rule
could not make with confidence is AMBIGUOUS, and the report lists each with the
alternative. --write only writes; it never changes an assignment already in the
registry.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

REG = REPO / "metrics_registry.yaml"
VOCAB = ("price", "rate", "spread", "release", "quantity", "conditions", "ratio")
NOT_LEVEL_UNITS = {"boolean", "label", "date", "0/1", "by_source", "None", ""}

# The FRED members, by hand: (family, ambiguous-why or None). The minutes' 6e:
# unemployment rate -> release; breakevens and the ACM-style term premium ->
# rate; DXY, gold, oil, BTC -> price; VIX -> conditions.
A = "ambiguous"
FRED_FAMILIES: dict[str, tuple[str, str | None]] = {
    **{k: ("release", None) for k in (
        "nfp", "u3_rate", "claims_4wk", "lfp_rate", "emp_pop_ratio", "lt_unemp",
        "job_openings", "hires_total", "quits_rate", "layoffs", "real_gdp",
        "housing_starts", "housing_starts_sf", "housing_permits", "existing_homes",
        "new_homes", "cpi", "core_cpi", "pce", "core_pce", "gdp_nominal",
        "current_account", "ahe_yoy", "avg_wkly_hours")},
    **{k: ("release", "a series FRED already publishes as a year-over-year rate: its "
                      "own YoY is a change of a change; alternative: rate")
       for k in ("sticky_cpi", "sticky_core", "flex_cpi")},
    **{k: ("release", "a quarterly delinquency or charge-off rate: released, but read "
                      "as a level; alternative: conditions")
       for k in ("mortgage_delinq", "cc_delinq_30", "cc_chargeoff", "auto_delinq",
                 "cre_delinq")},
    **{k: ("conditions", "a lending-standards survey (net %), read as a level like "
                         "sentiment; alternative: release")
       for k in ("sloos_ci_large", "sloos_ci_small", "sloos_cre_construction",
                 "sloos_cre_nonres", "sloos_cre_multifamily")},
    "case_shiller_national": ("release", "a house-price index, released monthly; "
                                         "alternative: price"),
    "uoM_sent": ("conditions", None),
    **{k: ("quantity", "a stock released on a schedule; alternative: release")
       for k in ("total_hh_debt", "consumer_credit_total", "consumer_credit_revolving",
                 "consumer_credit_nonrevolving", "hh_equities", "hh_debt_securities",
                 "hh_deposits", "fed_outlays")},
    "fed_debt_pct_gdp": ("ratio", "debt over GDP, released quarterly; alternative: release"),
    **{k: ("rate", None) for k in (
        "yield_2y", "yield_10y", "yield_30y", "yield_5y", "tbill_3m", "mortgage_30y",
        "breakeven_10y", "breakeven_5y5y", "breakeven_5y", "fed_funds", "effr_daily",
        "sofr", "iorb", "ecb_dfr", "jp_call_rate", "jp_10y", "jp_3m", "gilt_10y",
        "tips_5y", "tips_10y", "tips_30y")},
    **{k: ("rate", None) for k in (
        "oecd_10y_us", "oecd_10y_ca", "oecd_10y_de", "oecd_10y_fr", "oecd_10y_it",
        "oecd_10y_es", "oecd_10y_nl", "oecd_10y_be", "oecd_10y_au", "oecd_10y_nz",
        "oecd_10y_ch", "oecd_10y_se")},
    "term_premium_kw": ("rate", "the Kim-Wright term premium: the minutes rule the ACM "
                                "term premium a rate, and this follows by analogy"),
    **{k: ("spread", None) for k in (
        "ig_oas", "hy_oas", "ccc_oas", "bb_oas", "aa_oas", "bbb_oas", "em_corp_oas",
        "em_hy_oas")},
    **{k: ("quantity", None) for k in (
        "fed_balance", "rrp", "tga", "m2", "bank_reserves", "soma_treasuries")},
    "nfci": ("conditions", None), "nfci_lev": ("conditions", None),
    "vix": ("conditions", None),
    **{k: ("price", None) for k in ("wti", "brent", "natgas", "dxy_em")},
    "dxy": ("price", "FRED's broad dollar index (DTWEXBGS), not ICE's DXY; the minutes "
                     "rule DXY a price and this follows"),
    "real_dollar_broad": ("price", "a monthly real dollar index; alternative: release"),
}
FX_PREFIX = "usd_"                        # every FRED FX pair: a price

# The closes' members that are not prices (yfinance_source.SYMBOLS' store keys).
CLOSE_MEMBERS = {"yfinance.mkt_tnx": ("rate", None), "yfinance.mkt_tyx": ("rate", None)}

BLOCK_FAMILY: dict[str, tuple[str, str | None]] = {
    "market_closes": ("price", None), "market_ohlc": ("price", None),
    "market_volume_shares": ("quantity", None), "market_volume_contracts": ("quantity", None),
    "market_volume_usd": ("quantity", None), "bars_prices": ("price", None),
    "bars_volume_shares": ("quantity", None), "bars_volume_contracts": ("quantity", None),
    "bars_volume_usd": ("quantity", None),
    "naive_expectations": ("release", "the naive expectation of a release, in its "
                                      "units; alternative: the member's own family"),
    "naive_surprises": ("conditions", "a surprise against the naive expectation, read "
                                      "as a standardised level; alternative: ratio"),
    "driver_attribution_explained": ("ratio", None),
    "driver_attribution_residual": ("ratio", "a residual return; alternative: price"),
    "driver_attribution_loadings": ("ratio", None),
    "paper_bid_call_put_oi": ("quantity", None),
    "paper_bid_risk_reversal": ("conditions", "a 25-delta risk reversal in vol points; "
                                              "alternative: spread"),
    "overnight_levels": ("price", "the overnight levels block also holds changes and "
                                  "settles; alternative: split per member"),
    "overnight_percent_changes": ("price", "percent changes, not levels; alternative: "
                                           "exclude"),
    "correlation_matrix": ("ratio", None), "correlation_breaks": ("ratio", None),
    "crypto_basket_closes": ("price", None), "crypto_basket_volume": ("quantity", None),
    "llama_protocol_daily": ("quantity", None),
    "llama_coin_mcap": ("quantity", "a market capitalisation, price times supply; "
                                    "alternative: price"),
    "llama_coin_supply": ("quantity", None), "crypto_dilution": ("ratio", None),
}
BLOCK_EXCLUDED = {
    "market_actions": "dividends and splits: corporate-action events, not level series",
    "structure_comparison": "labels", "base_rate_tables": "tables, not series",
    "event_columns": "the events table's columns", "event_types": "the events table's types",
    "pin_log_columns": "the pin log's columns",
    "driver_attribution_sign_stability": "boolean flags",
    "correlation_shift_flags": "boolean flags",
}

# Names the minutes rule (6e) for individually registered metrics.
NAMED = [
    (re.compile(r"(^|[._])(cape|erp|equity_risk_premium|forward_pe|fwd_pe)$"), "ratio",
     "the minutes 6e: CAPE, ERP and forward P/E are ratios (full-history window)"),
    (re.compile(r"(breadth|rsp_spy|2s10s)"), "ratio",
     "the minutes 6e: 2s10s and breadth are ratios (20y)"),
    (re.compile(r"(^|\.)vix$|mkt_vix$"), "conditions", "the minutes 6e: VIX"),
]
BY_UNITS = {
    "price": ("price", None), "percent_rate": ("rate", None), "bps": ("spread", None),
    "vol_pct": ("conditions", None), "vol_index": ("conditions", None),
    "ratio": ("ratio", None), "fraction": ("ratio", None), "percent_share": ("ratio", None),
    "percentile": ("ratio", None),
    **{u: ("quantity", None) for u in (
        "usd", "count", "shares", "K", "M", "B", "$", "usd_per_point", "usd_per_1pct",
        "shares_per_volpt", "shares_per_day", "shares_per_1pct", "usd_per_volpt",
        "usd_per_day", "contract_ccy", "JPY", "CNY", "MXN", "CAD", "CHF", "SEK", "NOK",
        "DKK", "BRL")},
    "percent_return": ("ratio", "a return series, not a level; alternative: price"),
    "idx": ("conditions", "an index level of unknown kind; alternative: release or price"),
    "days": ("quantity", "a duration in days; alternative: ratio"),
    "hrs": ("quantity", "hours; alternative: release"),
    "N": ("quantity", "a plain number; alternative: release"),
}


def classify(key: str, e: dict) -> tuple[str | None, str, str | None]:
    """(family or None, basis, ambiguous-why or None) for one resolved entry."""
    units = str(e.get("units"))
    for rx, fam, why in NAMED:
        if rx.search(key):
            return fam, why, None
    if key.startswith("fred."):
        k = key[5:]
        if k == "usrec":
            return None, "the NBER recession flag (0/1)", None
        if k in FRED_FAMILIES:
            fam, amb = FRED_FAMILIES[k]
            return fam, "FRED member, by hand", amb
        if k.startswith(FX_PREFIX):
            return "price", "a FRED FX pair", None
    if key in CLOSE_MEMBERS:
        fam, amb = CLOSE_MEMBERS[key]
        return fam, "a yield index inside the closes", amb
    if units in NOT_LEVEL_UNITS:
        return None, f"units {units!r}: not a level series", None
    if units == "%":
        f = str(e.get("freq") or e.get("native_horizon") or "")
        fam = "release" if f in ("monthly", "quarterly", "annual") else "rate"
        return fam, f"units % at {f or 'unknown'} frequency", (
            "a percent of unknown kind; alternative: " + ("rate" if fam == "release"
                                                         else "release"))
    if units in BY_UNITS:
        fam, amb = BY_UNITS[units]
        return fam, f"units {units!r}", amb
    return None, f"units {units!r}: no rule", "no rule matched; assign by hand"


def written_ambiguity() -> dict[str, str]:
    """The `# ambiguous:` comments already written into the registry, by key."""
    out = {}
    for ln in REG.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s+([\w.^\-]+):\s*\w+\s+# ambiguous: (.*)$", ln)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def plan() -> dict:
    from altdata import derived  # noqa: PLC0415
    raw = yaml.safe_load(REG.read_text(encoding="utf-8"))
    amb_written = written_ambiguity()
    by_block: dict[str, list[str]] = {}
    reg = derived.resolve_registry(raw, by_block)
    declared = dict(raw.get("families") or {})
    inline = {k for k, m in (raw.get("metrics") or {}).items()
              if isinstance(m, dict) and m.get("family")}
    in_block = {k: b for b, ks in by_block.items() for k in ks}
    blocks: dict[str, dict] = {}
    metrics_map: dict[str, tuple[str, str, str | None]] = {}
    excluded: dict[str, str] = {}
    rows = []
    for bid, ks in by_block.items():
        if bid in BLOCK_EXCLUDED:
            excluded[bid] = BLOCK_EXCLUDED[bid]
            for k in ks:
                rows.append((k, None, f"block {bid}: {BLOCK_EXCLUDED[bid]}", None))
            continue
        if bid in BLOCK_FAMILY:
            fam, amb = BLOCK_FAMILY[bid]
            members = {}
            for k in ks:
                if k in CLOSE_MEMBERS:
                    members[k] = CLOSE_MEMBERS[k][0]
            blocks[bid] = {"family": fam, "members": members, "ambiguous": amb}
            for k in ks:
                f = declared.get(k) or members.get(k) or fam
                rows.append((k, f, "declared" if k in declared else f"block {bid}",
                             amb_written.get(k) if k in declared else amb))
            continue
        # a mixed block: member by member
        members = {}
        for k in ks:
            if k in declared:
                rows.append((k, declared[k], "declared", amb_written.get(k)))
                continue
            fam, basis, amb = classify(k, {**reg[k], "family": None})
            if fam is None:
                excluded[k] = basis
            else:
                members[k] = fam
            rows.append((k, fam, basis, amb))
        blocks[bid] = {"member_families": members}
    for k, e in reg.items():
        if k in in_block:
            continue
        if k in declared or k in inline:
            rows.append((k, declared.get(k) or e.get("family"), "declared",
                         amb_written.get(k)))
            continue
        fam, basis, amb = classify(k, e)
        if fam is None:
            excluded[k] = basis
        else:
            metrics_map[k] = (fam, basis, amb)
        rows.append((k, fam, basis, amb))
    return {"blocks": blocks, "metrics": metrics_map, "excluded": excluded, "rows": rows,
            "resolved": len(reg)}


def write(p: dict) -> None:
    text = REG.read_text(encoding="utf-8")
    lines = text.split("\n")
    # 1. blocks: insert after each block's members_from line
    for bid, spec in p["blocks"].items():
        i = next(n for n, ln in enumerate(lines) if ln == f"  {bid}:")
        j = next(n for n in range(i + 1, len(lines)) if lines[n].startswith("    members_from:"))
        add = []
        if spec.get("family"):
            add.append(f"    family: {spec['family']}"
                       + (f"   # ambiguous: {spec['ambiguous']}" if spec.get("ambiguous") else ""))
        mf = spec.get("member_families") or spec.get("members") or {}
        if mf:
            add.append("    member_families:")
            add += [f"      {k}: {v}" for k, v in sorted(mf.items())]
        lines[j + 1:j + 1] = add
    # 2. the families map: append to its section
    i = lines.index("families:")
    j = i + 1
    while j < len(lines) and (lines[j].startswith("  ") or lines[j].strip() == ""):
        if lines[j].strip() == "" and j + 1 < len(lines) and not lines[j + 1].startswith("  "):
            break
        j += 1
    add = ["  # 6e (15 Oct 2026): every other individually registered level series,",
           "  # by tools/assign_families.py; `# ambiguous:` marks one listed for Ari."]
    for k, (fam, _basis, amb) in sorted(p["metrics"].items()):
        add.append(f"  {k}: {fam}" + (f"   # ambiguous: {amb}" if amb else ""))
    lines[j:j] = add
    # 3. lens_excluded, a new section at the end
    out = "\n".join(lines).rstrip("\n") + "\n\n" + "\n".join(
        ["# NOT A LEVEL SERIES (6e): no lens family, each with its reason. A block id",
         "# names every member of the block; a key names one series.",
         "lens_excluded:"]
        + [f"  {k}: {yaml.safe_dump(v, default_style=chr(34)).strip()}"
           for k, v in sorted(p["excluded"].items())]) + "\n"
    REG.write_text(out, encoding="utf-8")


def report(p: dict, path: Path) -> None:
    from collections import Counter  # noqa: PLC0415
    rows = p["rows"]
    fams = Counter(f for _, f, _, _ in rows if f)
    amb = [r for r in rows if r[3]]
    out = ["# 6e: the family assignments (generated by tools/assign_families.py)", "",
           f"{p['resolved']} resolved registry keys: "
           + ", ".join(f"{f} {fams[f]}" for f in VOCAB)
           + f"; {sum(1 for r in rows if not r[1])} not level series (no family).", "",
           f"## The ambiguous assignments, {len(amb)}, for Ari", "",
           "| Series | Family | Basis | Why ambiguous, and the alternative |", "|---|---|---|---|"]
    out += [f"| `{k}` | {f} | {b} | {a} |" for k, f, b, a in sorted(amb)]
    out += ["", "## Not level series (no family)", "",
            "| Block or series | Reason |", "|---|---|"]
    out += [f"| `{k}` | {v} |" for k, v in sorted(p["excluded"].items())]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    p = plan()
    if a.report:
        report(p, Path(a.report))
    if a.write:
        write(p)
    from collections import Counter  # noqa: PLC0415
    print(Counter(f for _, f, _, _ in p["rows"]), sum(1 for r in p["rows"] if r[3]),
          "ambiguous;", len(p["metrics"]), "metrics lines;", len(p["blocks"]), "blocks")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

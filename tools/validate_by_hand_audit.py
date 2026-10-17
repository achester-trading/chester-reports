"""
validate_by_hand_audit -- the by-hand audit (st-r5-audit, ruled 16 Oct 2026),
held where no other gate holds it.

    python tools/validate_by_hand_audit.py

Ruling (b) of 16 Oct 2026: no recurring by-hand data line survives without the
operator's explicit yes; the yeses are the global PMI headline (Batch 6 item 43)
and item 47's quarterly AI unit-economics line (Batch 7). Ruling (a): prefer
public, easy-to-access sources; friction is a gap, not a key. The readers the
audit built are held by their readers' gates (validate_st_r5_t1_rest: the ONS
and Statistics Canada CPI; validate_batch3_a: the Banque de France's TEC 10 and
SR-30's daily tiers); CLAUDE.md's rule by validate_deploy group F. This gate
holds the rest:

  A  THE ONE KEY. tools/manual_input.py's registry holds exactly one key,
     manual.global_pmi; each of the 23 keys the audit dropped is gone from the
     registry (metrics, families, long windows), the catalogue and
     manual_input, and no code or config outside the gates that name them as
     gone reads it.
  B  THE LINES. Each line a dropped key fed now prints its reason: the
     Quarterly's rows are absent with "not tracked (by-hand audit, 16 Oct
     2026)", the sovereign gold-share analysis waits with its reason, the
     allocation block's AAII line is a listed gap; the Korea 2-year's gap
     no longer waits on a key.
  C  THE AUDIT TABLE. docs/briefs/st-r5-audit-notes.md carries a verdict for
     every key: KEEP for manual.global_pmi and nothing else, DROP or AUTOMATE
     for each dropped key, on one table row each.
  D  THE WARSH FILE. docs/warsh-matrix-lines.md holds one dated entry for items
     34 and 42, each with its scenario and the measure that adjudicates it, and
     a place for item 46; item 42's line no longer sits in the t1-rest notes.

No gate reads the live store, fetches or calls a model.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78

KEEP = {"manual.global_pmi"}
DROPPED = (
    "manual.sep_median_next2", "manual.sep_median_12m",
    "manual.fedwatch_next_meeting_prob", "manual.cbo_deficit_path",
    "manual.ig_nic_median_bp", "manual.ig_cover_median",
    "manual.aaii_stocks_pct", "manual.aaii_bonds_pct", "manual.aaii_cash_pct",
    "manual.msci_em_usd", "manual.msci_em_local", "manual.msci_world_usd",
    "manual.msci_acwi_exus_usd", "manual.oecd_days_cover",
    "manual.global_visible_stocks_bbl", "manual.cofer_usd_share",
    "manual.cofer_usd_share_constant_fx", "manual.gold_share_total_reserves",
    "manual.mu_hbm_share", "manual.dram_contract_dir", "manual.g4_issuance_gap_gdp",
    "manual.panda_bond_issuance", "manual.state_bank_dollar_selling")
# Gates that name the dropped keys to hold them gone, and fixtures recording a
# past registry; neither reads a key.
NAMES_AS_GONE = {"validate_by_hand_audit.py", "validate_official_sources.py",
                 "validate_audit_3a.py"}
NOTES = REPO / "docs" / "briefs" / "st-r5-audit-notes.md"
WARSH = REPO / "docs" / "warsh-matrix-lines.md"


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def registry() -> dict:
    return yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))


def group_a() -> None:
    print(f"{LINE}\nA. THE ONE KEY\n{LINE}")
    import manual_input                                         # noqa: PLC0415
    from altdata import catalogue                               # noqa: PLC0415
    reg = registry()
    keys = set(manual_input.manual_keys())
    check(keys == KEEP, f"manual_input holds exactly the operator's one yes, "
                        f"manual.global_pmi ({sorted(keys)})")
    check(len(DROPPED) == 23 and not KEEP & set(DROPPED),
          "the audit dropped 23 keys, and the kept key is not among them")
    in_reg = [k for k in DROPPED if k in (reg.get("metrics") or {})
              or k in (reg.get("families") or {}) or k in (reg.get("long_windows") or {})]
    in_cat = [k for k in DROPPED if k in catalogue.resolved()]
    check(not in_reg and not in_cat,
          f"none is in the registry (metrics, families, long windows) or the "
          f"catalogue ({(in_reg + in_cat) or 'none'})")
    readers = []
    for p in list(REPO.glob("**/*.py")) + list(REPO.glob("**/*.yaml")):
        parts = set(p.parts)
        if parts & {".venv", ".git", "docs", "fixtures", "__pycache__"} \
                or p.name in NAMES_AS_GONE:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        readers += [f"{p.relative_to(REPO)}:{k}" for k in DROPPED if k in text]
    check(not readers, f"no code or config reads a dropped key ({readers[:6] or 'none'})")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE LINES\n{LINE}")
    q = yaml.safe_load((REPO / "config" / "quarterly_chapters.yaml").read_text(encoding="utf-8"))
    absent: list[dict] = []
    waits: list[dict] = []

    def walk(v):
        if isinstance(v, dict):
            if v.get("absent") and v.get("label"):
                absent.append(v)
            if v.get("id") == "sovereign_gap":
                waits.append(v)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(q)
    labels = {a["label"]: a["absent"] for a in absent}
    want = ("MSCI EM, USD (SR-14)", "MSCI EM, local currency (SR-14)",
            "MSCI World, USD (SR-14's DM leg)", "MSCI World, USD",
            "MSCI ACWI ex-US, USD", "The dollar's COFER share, constant currency",
            "Panda bond issuance", "State-bank dollar selling")
    check(all(labels.get(w, "").startswith("not tracked (by-hand audit, 16 Oct 2026): ")
              for w in want),
          f"the Quarterly's eight rows print \"not tracked\" with the audit's reason "
          f"({[w for w in want if w not in labels] or 'all present'})")
    check(waits and "series" not in waits[0] and "dropped" in waits[0].get("waits", ""),
          "the sovereign gold-share analysis waits, saying its by-hand key is dropped")
    ix = yaml.safe_load((REPO / "config" / "st_r5_index.yaml").read_text(encoding="utf-8"))
    alloc = ix.get("allocation") or {}
    check("aaii_keys" not in alloc and "not tracked" in alloc.get("aaii_gap", "")
          and "403" in alloc.get("aaii_gap", ""),
          "the allocation block's AAII line is a listed gap (aaii.com answers 403)")
    rt = yaml.safe_load((REPO / "config" / "st_r5_rates.yaml").read_text(encoding="utf-8"))
    kr = next((x for v in rt.values() if isinstance(v, list) for x in v
               if isinstance(x, dict) and x.get("id") == "kr"), {})
    check("ruled out" in kr.get("gap", "") and ".env" not in kr.get("gap", ""),
          f"the Korea 2-year's gap no longer waits on a key ({kr.get('gap', '')[:70]})")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE AUDIT TABLE\n{LINE}")
    check(NOTES.exists(), "docs/briefs/st-r5-audit-notes.md exists")
    if not NOTES.exists():
        return
    rows = [ln for ln in NOTES.read_text(encoding="utf-8").splitlines()
            if ln.startswith("|")]

    def verdicts(key: str) -> set[str]:
        out = set()
        for ln in rows:
            if f"`{key}`" in ln:
                out |= set(re.findall(r"\*\*(KEEP|DROP|AUTOMATE)\b", ln))
        return out
    check(verdicts("manual.global_pmi") == {"KEEP"},
          "manual.global_pmi: KEEP (Batch 6 item 43, the operator's yes)")
    bad = {k: v for k in DROPPED if len(v := verdicts(k)) != 1 or "KEEP" in v}
    check(not bad, f"each dropped key has one verdict, DROP or AUTOMATE, on its row "
                   f"({sorted(bad)[:5] or 'all 23'})")
    keeps = [ln for ln in rows if "**KEEP" in ln]
    check(len(keeps) == 2 and any("47" in ln for ln in keeps),
          f"KEEP only for the two explicit yeses, the PMI and item 47 ({len(keeps)} rows)")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE WARSH FILE\n{LINE}")
    text = WARSH.read_text(encoding="utf-8") if WARSH.exists() else ""
    secs = {m.group(1): s for m, s in
            ((re.match(r"## Item (\d+)", s), s) for s in re.split(r"\n(?=## )", text))
            if m}
    check(set(secs) == {"34", "42", "46"},
          f"one entry each for items 34 and 42, and item 46's place ({sorted(secs)})")
    for item, measure in (("34", "ST-R5.34a"), ("42", "ST-R5.42a")):
        s = secs.get(item, "")
        check("added 16 October 2026" in s and "**Scenario:**" in s
              and "**Adjudicated by:**" in s and measure in s,
              f"item {item}: dated, its scenario, and the measure that adjudicates "
              f"it ({measure})")
    check("accept-all" in text and "weights stay Ari's" in text,
          "listed for Ari's accept-all; the matrix's weights stay his")
    notes = (REPO / "docs" / "briefs" / "st-r5-t1-rest-notes.md").read_text(encoding="utf-8")
    check("hikes-resume cell up" not in notes and "docs/warsh-matrix-lines.md" in notes,
          "item 42's line moved: the t1-rest notes point to the file")


def main() -> int:
    print(f"{LINE}\nThe by-hand audit (st-r5-audit, 16 Oct 2026)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback                                    # noqa: PLC0415
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

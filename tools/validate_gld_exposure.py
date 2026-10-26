"""
Signal-triage Batch 16 item 88(c) (B75): GLD in the dealer engine's nightly
exposure files, a one-ticker exception to the 13-ticker hold.

  A  THE HOLD STANDS. options_universe() is still the 13, GLD not among them; the
     exception list is exactly GLD, declared in config/exposure_universe.yaml
     with its ruling and its Security Master id (SM00022, SPDR Gold Shares); GLD
     is already captured nightly (chain_universe).
  B  CONFIG, NOT CODE. run_eod.py names no exception symbol: it reads
     config.exposure_exceptions(); an entry without a ruling, or for a symbol not
     captured, or one already in the hold, is not an exception.
  C  THE ENGINE'S FIELDS. A fixture GLD chain through the engine's own
     compute_symbol gives GEX, DEX, the OTM walls and the flip in the exposure
     file's shape, written where the readers glob; the dealer store reads its
     rows like any of the 13's.
  D  THE WEEKLY READS THE LEVELS. The gold block's GLD line prints the flip, the
     walls and net GEX from the newest settled profile, "inferred, not observed",
     and the vendor line says FlashAlpha's plan does not serve GLD.
  E  WHAT IT DOES NOT GET. The pin log and the completeness gate still take the 13
     alone.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_gld_exposure.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "dealer_block"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chains as C  # noqa: E402
import exposure_compute as ec  # noqa: E402
import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import config  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78


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


def group_a() -> None:
    head("A. THE HOLD STANDS")
    u = config.options_universe()
    check(len(u) == 13 and "GLD" not in u, f"the hold is the 13 ({len(u)}), GLD not in it")
    check(config.exposure_exceptions() == ["GLD"], "the exceptions: GLD alone")
    doc = yaml.safe_load((REPO / "config" / "exposure_universe.yaml").read_text(
        encoding="utf-8"))
    e = doc["exceptions"][0]
    check(doc["hold"]["count"] == 13 and "88(c)" in e["ruled"] and "26 Oct 2026" in e["ruled"]
          and e["security_master_id"] == "SM00022",
          "declared with its ruling and its Security Master id")
    sm = yaml.safe_load((REPO / "config" / "security_master.yaml").read_text(
        encoding="utf-8"))
    ent = next(x for x in (sm if isinstance(sm, list) else sm.get("securities") or sm.get(
        "instruments") or []) if x.get("id") == "SM00022")
    check((ent.get("identifiers") or {}).get("yahoo") == "GLD", "SM00022 is GLD")
    check("GLD" in config.chain_universe(), "GLD is already captured nightly")


def group_b() -> None:
    head("B. CONFIG, NOT CODE")
    src = (REPO / "run_eod.py").read_text(encoding="utf-8")
    lits = {n.value for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    check("GLD" not in lits and "config.exposure_exceptions()" in src,
          "run_eod.py names no exception symbol and reads the config")
    check("exposure_compute.run(symbols=universe + exceptions" in src
          and "pin_log.run(symbols=universe," in src,
          "computed beside the 13; the pin log keeps the 13")
    td = Path(gate_tmp.mkdtemp("gldexp_"))
    bad = td / "x.yaml"
    bad.write_text(yaml.safe_dump({"exceptions": [
        {"symbol": "GLD"}, {"symbol": "XYZ", "ruled": "r"}, {"symbol": "SPY", "ruled": "r"},
        {"symbol": "SLV", "ruled": "r"}]}), encoding="utf-8")
    check(config.exposure_exceptions(str(bad)) == ["SLV"],
          "no ruling, not captured, or already held: not an exception")
    check(config.exposure_exceptions(str(td / "missing.yaml")) == [],
          "no file: no exception")


def _gld_profile(out_dir: Path) -> tuple[dict, Path]:
    # The dealer fixture's chain under GLD's name: the engine is symbol-blind,
    # so the shape is what is held, not GLD's own strikes.
    rows = C.bs_chain()
    for r in rows:
        r["symbol"] = "GLD"
    res = ec.compute_symbol(rows, "GLD")
    return res, ec.write_computed(res, str(out_dir))


def group_c() -> None:
    head("C. THE ENGINE'S FIELDS")
    td = Path(gate_tmp.mkdtemp("gldexp_c_"))
    res, path = _gld_profile(td)
    o = res.get("overall") or {}
    need = ("net_gex", "dex_notional", "gamma_flip", "call_wall_otm", "put_wall_otm",
            "net_to_gross")
    check(not res.get("error") and all(k in o for k in need),
          f"GEX, DEX, the walls and the flip under the engine's names "
          f"({[k for k in need if k not in o] or 'all present'})")
    check(path.name.startswith("GLD_") and path.name.endswith("_exposure.json")
          and path.parent.name == res["session_date"],
          f"written where the readers glob ({path.parent.name}/{path.name})")
    from altdata import dealer_store                           # noqa: PLC0415
    rows, why = dealer_store.rows_for(res, path)
    keys = {r["registry_key"] for r in rows}
    check(rows and all(r["instrument"] == "GLD" for r in rows)
          and {"exposure.net_gex", "exposure.call_wall_otm", "exposure.put_wall_otm"} <= keys,
          f"the dealer store reads its rows like the 13's ({len(rows)} rows; {why})")


def group_d() -> None:
    head("D. THE WEEKLY READS THE LEVELS")
    from daily_cascade import gold_block                        # noqa: PLC0415
    td = Path(gate_tmp.mkdtemp("gldexp_d_"))
    res, _ = _gld_profile(td)
    ln = gold_block.gld_levels_line(str(td), res["session_date"])
    o = res["overall"]
    flip = "—" if o.get("gamma_flip") is None else f"{o['gamma_flip']:,.2f}"
    check(ln.startswith("GLD's dealer levels (") and "inferred, not observed" in ln
          and f"gamma flip {flip}" in ln and f"{o['call_wall_otm']:,.2f}" in ln
          and f"{o['put_wall_otm']:,.2f}" in ln,
          f"the flip and the walls from the newest settled profile ({ln[:120]}...)")
    check("does not serve GLD" in ln, "the vendor-comparison line: not served")
    fa = (REPO / "config" / "flashalpha.yaml").read_text(encoding="utf-8")
    check("GLD" not in fa, "and FlashAlpha's plan indeed names no GLD")
    none = gold_block.gld_levels_line(str(td / "empty"), "2026-11-06")
    check("no settled profile stored" in none, "no profile: said so")


def group_e() -> None:
    head("E. WHAT IT DOES NOT GET")
    src = (REPO / "run_eod.py").read_text(encoding="utf-8")
    check("comp = completeness(s, universe, vs, vendor_universe)" in src
          and "write_completeness(completeness(s, universe)" in src,
          "the completeness gate takes the 13 alone")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())

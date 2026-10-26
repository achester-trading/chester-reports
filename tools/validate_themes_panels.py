"""
6i-5 -- Disruptive Themes' Stage 1 panels, a slow layer of the Alternative Assets
Quarterly (A77, 26 Oct 2026; daily_cascade/themes_block.py,
config/themes_panels.yaml, config/stack_hooks/quarterly-slow-themes-panels.yaml).

    python tools/validate_themes_panels.py

Fixtures only:

  A  the config: every row a registered key or a gap with its reason, each naming
     the order that queued it
  B  a fixture store renders every panel: a stored input prints its value; a
     missing one prints GAP with its reason, never a blank cell
  C  the chapter is the Quarterly's alone: its hook is quarterly, after the family
     chapters; the Monthly and the Weekly never run it
  D  Stage 1 only: no model call, no chapter (a chapter is summarised by a model),
     no score
"""

from __future__ import annotations

import ast
import datetime as dt
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

from altdata import derived                                    # noqa: E402
from daily_cascade import stack_hooks as sh                     # noqa: E402
from daily_cascade import themes_block as tb                    # noqa: E402

HOOK_ID = "quarterly-slow-themes-panels"
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  ok    {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


class FakeStore:
    def __init__(self, data: dict) -> None:
        self.data = data

    def as_of(self, key, now=None, inst=None, observed_from=None):
        return [{"observed_at": d, "value_num": v, "available_at": f"{d}T21:00:00+00:00"}
                for d, v in self.data.get((key, inst), [])]


def full_store(cfg: dict) -> FakeStore:
    d0 = dt.date(2026, 5, 1)
    pts = [((d0 + dt.timedelta(days=i)).isoformat(), 100.0 + i) for i in range(160)]
    return FakeStore({(r["key"], r.get("instrument")): pts
                      for p in cfg["panels"] for r in p["rows"] if r.get("key")})


def group_a(cfg: dict) -> None:
    print("A. the config")
    rows = [r for p in cfg["panels"] for r in p["rows"]]
    bad = [r["label"] for r in rows if not ((r.get("key") and derived.registry_entry(r["key"]))
                                            or (r.get("gap") and not r.get("key")))]
    check(rows and not bad, f"every row is a registered key or a gap with its reason "
                            f"({len(rows)} rows) {bad[:2]}")
    check(all(r.get("queued") for r in rows),
          "every row names the order that queued it")
    queued = {r["queued"] for r in rows}
    want = {"Batch 5 item 22", "Batch 5 item 23", "Batch 5 item 26", "Batch 7 item 47",
            "Batch 14 item 63", "Batch 14 item 65", "Batch 15 item 75", "Batch 15 item 76"}
    check(queued == want, f"the queued inputs are the brief's (Batch 14's 56 and 58 "
                          f"filed as 63 and 65) {sorted(queued ^ want)}")


def group_b(cfg: dict) -> None:
    print("B. a fixture store renders every panel")
    now, end = "2026-10-10T12:00:00+00:00", "2026-09-30"
    full = tb.panels(full_store(cfg), now, end, cfg)
    empty = tb.panels(FakeStore({}), now, end, cfg)
    check(len(full) == len(cfg["panels"]) and all(s["table"]["rows"] for s in full),
          f"every panel renders ({len(full)} panels)")
    declared = sum(1 for p in cfg["panels"] for r in p["rows"] if r.get("gap"))
    got = sum(s["data"]["gaps"] for s in full)
    check(got == declared, f"with every key stored, the GAP cells are the declared gaps "
                           f"alone ({got} of {declared})")
    cells = [c for s in full + empty for r in s["table"]["rows"] for c in r]
    check(all(str(c).strip() for c in cells), "no cell is blank")
    miss = [r for s in empty for r in s["table"]["rows"]]
    check(all(r[1].startswith(f"{tb.GAP} — ") for r in miss),
          "with nothing stored, every input prints GAP with its reason")
    edgar = next(r for s in empty for r in s["table"]["rows"] if r[0] == "Filed capex: Oracle")
    check("edgar.xbrl_capex [ORCL]: nothing stored by 2026-09-30" in edgar[1],
          f"a stored key's GAP names the key, its instrument and the cutoff ({edgar[1]!r})")
    val = next(r for s in full for r in s["table"]["rows"] if r[0] == "Filed capex: Oracle")
    check(not val[1].startswith(tb.GAP), f"and reads the instrument's own rows when stored ({val[1]!r})")
    sec = tb.quarterly_section(full_store(cfg), now, end)
    check(sec and sec["data"]["rows"] == sum(len(p["rows"]) for p in cfg["panels"]),
          "the Quarterly's section carries every row")


def group_c() -> None:
    print("C. the Quarterly's alone")
    check(sh.ids("quarterly", "slow", "family_chapters") == [HOOK_ID],
          "the hook runs in the Quarterly's slow layers, after the family chapters")
    others = [h["id"] for hs in sh.ORDER.values() for h in hs
              if h["module"] == "daily_cascade.themes_block" and h["cadence"] != "quarterly"]
    check(not others, "no Monthly, Weekly or Daily hook runs it")
    check(not sh.wired("monthly", "slow", "daily_cascade.themes_block", "quarterly_section"),
          "the Monthly's slow layers do not carry it")
    q = (REPO / "monthly_macro" / "quarterly.py").read_text(encoding="utf-8")
    check('stack_hooks.run("quarterly", "slow", "family_chapters"' in q,
          "the Quarterly runs the hooks at the family_chapters anchor")
    for f in ("monthly_macro/stack.py", "daily_cascade/weekly_stack.py",
              "daily_cascade/stack_close.py"):
        p = REPO / f
        check(not p.exists() or "themes_block" not in p.read_text(encoding="utf-8"),
              f"{f} does not name the Themes block")


def group_d(cfg: dict) -> None:
    print("D. Stage 1 only")
    src = (REPO / "daily_cascade" / "themes_block.py").read_text(encoding="utf-8")
    mods = set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
    check(not {m for m in mods if any(x in m for x in ("anthropic", "model_meter", "prose",
                                                       "narrative", "register"))},
          f"no model, prose or register import ({sorted(mods)})")
    sec = tb.quarterly_section(FakeStore({}), "2026-10-10T12:00:00+00:00", "2026-09-30")
    check(sec and not sec.get("chapter") and sec.get("prose_wanted") is False
          and sec["tier"] == "reference" and sec["data"]["scored"] is False,
          "a reference-tier section, never a chapter, no prose wanted, unscored")


def main() -> int:
    line = "=" * 72
    print(f"{line}\n6i-5 -- Disruptive Themes' Stage 1 panels\n{line}")
    cfg = tb.config()
    group_a(cfg)
    group_b(cfg)
    group_c()
    group_d(cfg)
    print(f"\n{line}\n{PASS} passed, {FAIL} failed\n{line}")
    print("VALIDATION FAILED" if FAIL else "VALIDATION PASSED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

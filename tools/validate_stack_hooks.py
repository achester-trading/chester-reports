#!/usr/bin/env python3
"""
Validation gate: the stack hooks (S1 part 5; the cloud-sessions brief, decision
5). Fixtures only; no network, no model, no live store.

  A  TODAY'S ORDER. The hook files render the Monthly's slow-layer tail in the
     frozen order it had inline (each builder stubbed to return its own id), and
     every module:function resolves.
  B  THE GRAPH IS REFUSED WHEN IT IS WRONG. On fixture directories: a cycle, an
     anchor the stack does not declare, a hook that follows no hook, a field
     missing and an id that is not its file's stem each raise HookError; two
     hooks after one run in id order, depth first.
  C  A HOOK IS CALLED AS IT WAS INLINE. A required value unset skips it; "one"
     drops a None; "many" extends.
  D  THE STACK HOLDS NO INLINE COPY. monthly_macro/stack.py imports the hooks at
     module level (so a bad graph fails the import) and no longer calls the five
     builders itself.

    python tools/validate_stack_hooks.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import importlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("stack_hooks_"))
LINE = "=" * 78
PASS = FAIL = 0
# The Monthly's slow-layer tail as it ran inline at chain-7-main dfa14a54.
FROZEN = {("monthly", "slow", "sourced_figures"): [
    "monthly-slow-batch14-b2-cma", "monthly-slow-batch5-construction",
    "monthly-slow-batch5b-expansion", "monthly-slow-batch14-a1-cape",
    "monthly-slow-capex-chain"]}


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
    from daily_cascade import stack_hooks as sh                 # noqa: PLC0415
    head("A. TODAY'S ORDER, RENDERED FROM THE HOOK FILES")
    for (cad, sec, anc), want in FROZEN.items():
        got = sh.ids(cad, sec, anc)
        # A hook added after S1 (6i-4's T&B lines, A79) follows the frozen order.
        check(got[:len(want)] == want, f"{cad}/{sec} after {anc}: the frozen order, "
              f"then any later hook ({got})")
    resolved = []
    for h in sh.HOOKS:
        try:
            resolved.append(callable(getattr(importlib.import_module(h["module"]),
                                             h["function"])))
        except Exception:                                       # noqa: BLE001
            resolved.append(False)
    check(resolved and all(resolved),
          f"every hook's module:function resolves ({len(resolved)} hooks)")
    # Render with each builder stubbed to return its own id: the section's
    # sub-section order, as the stack would print it.
    saved = []
    try:
        for h in sh.HOOKS:
            mod = importlib.import_module(h["module"])
            saved.append((mod, h["function"], getattr(mod, h["function"])))
            tag = h["id"]
            stub = ((lambda *a, _t=tag: [{"title": _t}]) if h["returns"] == "many"
                    else (lambda *a, _t=tag: {"title": _t}))
            setattr(mod, h["function"], stub)
        out = sh.run("monthly", "slow", "sourced_figures",
                     {"st": object(), "now": "2026-11-01T10:00:00+00:00",
                      "db_path": "fixture.db"})
    finally:
        for mod, name, fn in saved:
            setattr(mod, name, fn)
    want = FROZEN[("monthly", "slow", "sourced_figures")]
    check([s["title"] for s in out][:len(want)] == want,
          "rendered, the sub-sections come out in the frozen order, later hooks after")


def write(d: Path, files: dict) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / "_anchors.yaml").write_text("monthly:\n  slow:\n    - tail\n", encoding="utf-8")
    for hid, body in files.items():
        (d / f"{hid}.yaml").write_text(body, encoding="utf-8")
    return d


def hook(hid: str, after: str, extra: str = "") -> str:
    return (f"id: {hid}\ncadence: monthly\nsection: slow\nafter: {after}\n"
            f"module: json\nfunction: dumps\nargs: [now]\nrequires: [now]\n"
            f"returns: one\n{extra}")


def refused(d: Path, word: str) -> bool:
    from daily_cascade import stack_hooks as sh                 # noqa: PLC0415
    try:
        sh.order(*sh.load(d))
    except sh.HookError as e:
        return word in str(e)
    return False


def group_b() -> None:
    from daily_cascade import stack_hooks as sh                 # noqa: PLC0415
    head("B. A WRONG GRAPH IS REFUSED")
    check(refused(write(TD / "cycle", {"a": hook("a", "inline:tail"),
                                       "b": hook("b", "c"), "c": hook("c", "b")}),
                  "cycle"), "a cycle (b after c, c after b) is refused")
    check(refused(write(TD / "anchor", {"a": hook("a", "inline:nowhere")}),
                  "missing anchor"), "an anchor the stack does not declare is refused")
    check(refused(write(TD / "nohook", {"a": hook("a", "ghost")}), "missing anchor"),
          "a hook that follows no hook is refused")
    bad = TD / "field"
    write(bad, {"a": "id: a\ncadence: monthly\nsection: slow\nafter: inline:tail\n"})
    check(refused(bad, "missing"), "a hook file with a field missing is refused")
    check(refused(write(TD / "stem", {"a": hook("z", "inline:tail")}), "stem"),
          "a hook whose id is not its file's stem is refused")
    d = write(TD / "tree", {"a": hook("a", "inline:tail"), "c": hook("c", "inline:tail"),
                            "b": hook("b", "a"), "d": hook("d", "c")})
    got = [h["id"] for h in sh.order(*sh.load(d))[("monthly", "slow", "tail")]]
    check(got == ["a", "b", "c", "d"],
          f"two hooks after one run in id order, depth first ({got})")


def group_c() -> None:
    from daily_cascade import stack_hooks as sh                 # noqa: PLC0415
    head("C. A HOOK IS CALLED AS IT WAS INLINE")
    one = {"module": "json", "function": "loads", "args": ["x"], "requires": ["x"],
           "returns": "one"}
    check(sh.call(one, {"x": None}) == [] and sh.call(one, {"x": ""}) == [],
          "a required value unset (None or empty) skips the hook")
    check(sh.call(one, {"x": '{"t": 1}'}) == [{"t": 1}] and sh.call(one, {"x": "null"})
          == [], "'one' wraps a sub-section and drops a None")
    many = {**one, "returns": "many"}
    check(sh.call(many, {"x": '[{"a": 1}, {"b": 2}]'}) == [{"a": 1}, {"b": 2}],
          "'many' extends with every sub-section")


def group_d() -> None:
    head("D. THE STACK HOLDS NO INLINE COPY")
    src = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    top = src.split("\ndef ", 1)[0]
    check("from daily_cascade import stack_hooks" in top,
          "monthly_macro/stack.py imports the hooks at module level, so a bad graph "
          "fails its import")
    gone = ("batch14_b2_block.slow_subsection(", "batch5_block.slow_subsection(",
            "batch5b_block.slow_subsections(", "batch14_a1_block.slow_subsection(",
            "capex_chain_block.slow_subsection(")
    check(not [g for g in gone if g in src],
          "and no longer calls the five hooked builders inline")
    check('stack_hooks.run("monthly", "slow", "sourced_figures"' in src,
          "it runs the declared hooks at the anchor the files name")


def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
        group_d()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

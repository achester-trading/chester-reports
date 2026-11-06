"""
THE STACK HOOKS (S1 part 5; the cloud-sessions brief, section 2.2, decision 5).

A sub-section joins a stack through a declared hook file rather than an inline
edit of the stack's section list, so two branches adding sub-sections never
touch the same lines:

    config/stack_hooks/<id>.yaml
      id:       the hook's id (the file's stem)
      cadence:  daily | weekly | monthly | quarterly
      section:  the section it joins (e.g. "slow")
      after:    the hook it follows, or "inline:<anchor>" for the stack's own
                place, declared in config/stack_hooks/_anchors.yaml
      module:   the module that builds it        (e.g. daily_cascade.batch5_block)
      function: the function                     (e.g. slow_subsection)
      args:     the context names it is called with, in order (st, now, db_path)
      requires: the context names that must be set, or the hook is skipped
      returns:  one (a sub-section or None) | many (a list)

    from daily_cascade import stack_hooks
    subs += stack_hooks.run("monthly", "slow", "sourced_figures", ctx)

ORDER is `after:`: the hooks after an anchor, then the hooks after each of
those, depth first; two hooks after the same one run in id order. The graph is
checked when this module is imported, so a stack that imports it refuses a
cycle or a missing anchor before it renders anything.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
HOOK_DIR = REPO / "config" / "stack_hooks"
ANCHORS_FILE = "_anchors.yaml"
FIELDS = ("id", "cadence", "section", "after", "module", "function", "args",
          "requires", "returns")


class HookError(ValueError):
    """A hook file the stacks refuse: a field missing, a cycle, a missing anchor."""


def load(hook_dir: Optional[Path] = None) -> tuple[list[dict], dict]:
    d = Path(hook_dir or HOOK_DIR)
    anchors_raw = yaml.safe_load((d / ANCHORS_FILE).read_text(encoding="utf-8")) \
        if (d / ANCHORS_FILE).exists() else {}
    anchors = {(c, s): set(v or []) for c, secs in (anchors_raw or {}).items()
               for s, v in (secs or {}).items()}
    hooks = []
    for p in sorted(d.glob("*.yaml")):
        if p.name == ANCHORS_FILE:
            continue
        h = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        missing = [f for f in FIELDS if f not in h]
        if missing:
            raise HookError(f"{p.name}: missing {missing}")
        if h["id"] != p.stem:
            raise HookError(f"{p.name}: id {h['id']!r} is not the file's stem")
        if h["returns"] not in ("one", "many"):
            raise HookError(f"{p.name}: returns must be one or many")
        hooks.append(h)
    return hooks, anchors


def order(hooks: list[dict], anchors: dict) -> dict:
    """{(cadence, section, anchor): [hook, ...]} in `after:` order. Raises
    HookError on a missing anchor or a cycle."""
    ids = {h["id"]: h for h in hooks}
    for h in hooks:
        a = str(h["after"])
        key = (h["cadence"], h["section"])
        if a.startswith("inline:"):
            if a[7:] not in anchors.get(key, set()):
                raise HookError(f"{h['id']}: missing anchor {a!r} for {key}")
        elif a not in ids:
            raise HookError(f"{h['id']}: missing anchor {a!r} (no such hook)")
        elif (ids[a]["cadence"], ids[a]["section"]) != key:
            raise HookError(f"{h['id']}: follows {a!r}, a hook of another section")
    children: dict = {}
    for h in hooks:
        children.setdefault(str(h["after"]), []).append(h)
    for v in children.values():
        v.sort(key=lambda h: h["id"])
    out, seen = {}, set()

    def walk(parent: str, acc: list) -> None:
        for h in children.get(parent, []):
            seen.add(h["id"])
            acc.append(h)
            walk(h["id"], acc)
    for (cad, sec), names in anchors.items():
        for name in sorted(names):
            acc: list = []
            walk(f"inline:{name}", acc)
            out[(cad, sec, name)] = acc
    stray = sorted(set(ids) - seen)
    if stray:
        raise HookError(f"a cycle: {stray} follow one another and reach no anchor")
    return out


def call(h: dict, ctx: dict) -> list:
    """The hook's sub-sections: [] when a required context value is unset or
    the builder returns nothing."""
    if any(ctx.get(r) is None or ctx.get(r) == "" for r in h.get("requires") or []):
        return []
    fn = getattr(importlib.import_module(h["module"]), h["function"])
    r = fn(*[ctx.get(a) for a in h.get("args") or []])
    if h["returns"] == "many":
        return list(r or [])
    return [r] if r else []


def run(cadence: str, section: str, anchor: str, ctx: dict) -> list:
    out = []
    for h in ORDER.get((cadence, section, anchor), []):
        out += call(h, ctx)
    return out


def ids(cadence: str, section: str, anchor: str) -> list[str]:
    return [h["id"] for h in ORDER.get((cadence, section, anchor), [])]


def wired(cadence: str, section: str, module: str, function: str,
          args: Optional[list] = None) -> bool:
    """Does a hook of this section call module.function (with these context
    args, when given)? The wiring check a gate makes in place of reading the
    stack's source for an inline call."""
    return any(h["cadence"] == cadence and h["section"] == section
               and h["module"] == module and h["function"] == function
               and (args is None or list(h.get("args") or []) == list(args))
               for hs in ORDER.values() for h in hs)


# Checked at import: a stack that imports this refuses a bad graph at once.
HOOKS, ANCHORS = load()
ORDER = order(HOOKS, ANCHORS)

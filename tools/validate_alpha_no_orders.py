"""
Validation gate: the Alpha Lab can send nothing anywhere (X-1.5; constitution
`orders: none`). Runs in CI on every push, with every other gate.

alpha/ is a machine's book in LEDGER-PAPER: a signal becomes a row in alpha.db
filled against a price the store already holds. There is no order path of any
kind before the Gate 3 ruling, and the lab never fetches. This gate makes that a
property of the source rather than of anyone's memory, three ways:

  A  NO FORBIDDEN IMPORT. Every .py under alpha/ is parsed (ast) and every
     `import`, `from ... import`, `__import__("...")` and
     `importlib.import_module("...")` is checked against FORBIDDEN: the order
     gate and the register (register/ -- the gate at entry, the reconciliation,
     the decision writer); the broker modules (the IBKR sources and loggers,
     altdata.executions, ib_insync / ib_async / ibapi); the ledgers and the
     report writers the lab may not write (the probability ledger, the narrative
     ledger, state/emit, delivery); and every network library (requests,
     urllib, http, socket, ssl, httpx, aiohttp, websockets, smtplib, ftplib,
     yfinance, the repo's own fetchers in altdata.sources and altdata.feeds),
     plus subprocess, the way round all of them.
  B  NO NETWORK OR ORDER USE. No identifier in alpha/'s code (names, attributes,
     definitions -- not docstrings or comments) is `requests`, `urllib` or
     `socket`, or one of the order-routing names CLAUDE.md's deny list blocks
     (placeOrder, place_order, bracketOrder, submit_order, order_router,
     ibkr_orders, execution_framework, reqGlobalCancel), and no string in it is
     `--allow-live`; no os.system / os.popen.
  C  NOTHING FORBIDDEN AT IMPORT TIME. Every alpha module is imported in a fresh
     interpreter and sys.modules is searched for FORBIDDEN, so a transitive
     import through an allowed module is caught too. The system's blocklist is
     reached by loading register/instruments.py from its file under a private
     name (alpha/blocklist.py), so the `register` package -- whose __init__
     imports the decision writer -- is never imported.

AND THE CHECKS ARE CHECKED: SELF_TESTS drives one synthetic source per defect
through the same scanner, so a check that stopped firing fails here.

    python tools/validate_alpha_no_orders.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ALPHA = REPO / "alpha"
LINE = "=" * 78

# A module is forbidden if its dotted name equals one of these or starts with
# one followed by a dot.
FORBIDDEN = (
    # the order gate, the register and its writer
    "register",
    # the broker modules
    "altdata.executions", "altdata.sources.ibkr_portfolio",
    "altdata.sources.ibkr_costs", "altdata.sources.ibkr_whatif",
    "altdata.loggers.borrow", "altdata.loggers.auction",
    "ib_insync", "ib_async", "ibapi", "ibkr",
    # the ledgers and the report writers the lab never writes
    "altdata.probability_ledger", "altdata.narratives", "altdata.grader",
    "state", "daily_cascade.deliver", "monthly_macro",
    # network libraries, and the repo's fetchers
    "requests", "urllib", "urllib3", "http", "socket", "ssl", "httpx",
    "aiohttp", "websocket", "websockets", "smtplib", "ftplib", "telnetlib",
    "xmlrpc", "yfinance", "altdata.sources", "altdata.feeds", "altdata.loggers",
    # the way round all of them
    "subprocess",
)
# The standard library loads these itself; they are not imports alpha/ made, and
# neither opens a connection. pathlib (3.12) imports urllib.parse for as_uri() --
# a string quoter -- and with it the `urllib` package. CI's first run of this gate
# (#347) caught exactly that on the runner's Python. The network halves are
# still refused at import time: urllib.request, http.client, socket and the rest
# are not here. The static scan (A/B) still forbids alpha/ importing any of them.
RUNTIME_ALLOWED = ("urllib", "urllib.parse")

NETWORK_IDENTIFIERS = {"requests", "urllib", "socket"}
ORDER_IDENTIFIERS = {"placeOrder", "place_order", "bracketOrder", "submit_order",
                     "order_router", "ibkr_orders", "execution_framework",
                     "reqGlobalCancel"}
ORDER_STRINGS = {"--allow-live"}

PASS = FAIL = 0


def check(cond: bool, msg: str) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {msg}")
    else:
        FAIL += 1
        print(f"  FAIL  {msg}")


def forbidden(name: str) -> bool:
    return any(name == f or name.startswith(f + ".") for f in FORBIDDEN)


def _docstrings(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(
                    getattr(body[0], "value", None), ast.Constant) and isinstance(
                    body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def scan(source: str, name: str = "<src>", package: str = "alpha") -> list[str]:
    """Every violation in one source text, as a message."""
    tree = ast.parse(source, filename=name)
    docs = _docstrings(tree)
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if forbidden(a.name):
                    out.append(f"{name}:{node.lineno} imports {a.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.level:                       # a relative import: inside alpha/
                mod = package + ("." + node.module if node.module else "")
            else:
                mod = node.module or ""
            if forbidden(mod):
                out.append(f"{name}:{node.lineno} imports from {mod}")
            for a in node.names:
                full = f"{mod}.{a.name}" if mod else a.name
                if not node.level and forbidden(full):
                    out.append(f"{name}:{node.lineno} imports {full}")
        elif isinstance(node, ast.Call):
            fn = node.func
            fname = (fn.id if isinstance(fn, ast.Name) else
                     fn.attr if isinstance(fn, ast.Attribute) else "")
            if fname in ("__import__", "import_module") and node.args \
                    and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str) \
                    and forbidden(node.args[0].value):
                out.append(f"{name}:{node.lineno} dynamically imports "
                           f"{node.args[0].value}")
            if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) \
                    and fn.value.id == "os" and fn.attr in ("system", "popen"):
                out.append(f"{name}:{node.lineno} calls os.{fn.attr}")
        if isinstance(node, ast.Name) and node.id in NETWORK_IDENTIFIERS | ORDER_IDENTIFIERS:
            out.append(f"{name}:{node.lineno} uses {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in (
                NETWORK_IDENTIFIERS | ORDER_IDENTIFIERS):
            out.append(f"{name}:{node.lineno} uses .{node.attr}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and node.name in ORDER_IDENTIFIERS:
            out.append(f"{name}:{node.lineno} defines {node.name}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docs \
                and any(s in node.value for s in ORDER_STRINGS):
            out.append(f"{name}:{getattr(node, 'lineno', '?')} carries --allow-live")
    return out


SELF_TESTS = [
    ("import requests", "a network library"),
    ("import urllib.request", "urllib"),
    ("from socket import create_connection", "socket"),
    ("import http.client", "http"),
    ("import yfinance as yf", "a fetcher's library"),
    ("from altdata.sources import fred", "the repo's fetchers"),
    ("from altdata.feeds import pull", "the feed runner"),
    ("from register import Register", "the register"),
    ("from register.heat import gate", "the order gate"),
    ("import register.reconcile", "the order gate's reconciliation"),
    ("from altdata.sources.ibkr_portfolio import sync", "a broker module"),
    ("import ib_insync", "the broker library"),
    ("from altdata import probability_ledger", "the probability ledger"),
    ("from altdata.narratives import confirm", "the narrative ledger"),
    ("from state.emit import emit", "the state emitter (a POST)"),
    ("import subprocess", "subprocess"),
    ("importlib.import_module('requests')", "a dynamic import"),
    ("__import__('socket')", "__import__"),
    ("os.system('curl x')", "os.system"),
    ("x = requests.get", "a network identifier"),
    ("def place_order(): pass", "an order entry point"),
    ("ib.placeOrder(c, o)", "an order call"),
    ("args = ['--allow-live']", "the live flag"),
]
CLEAN = '''"""A docstring may say requests, urllib, socket and place_order."""
from altdata import observations, session
from . import ledger
import sqlite3, json, math
# a comment about socket
x = observations.canonical_instant("2026-10-13")
'''


def self_test() -> None:
    print(f"{LINE}\nSELF-TEST: each defect is caught; a clean source is not\n{LINE}")
    for src, what in SELF_TESTS:
        check(bool(scan("import importlib, os\n" + src, "<self-test>")),
              f"catches {what}: {src}")
    check(scan(CLEAN, "<clean>") == [],
          "passes a clean source whose docstring and comment name the forbidden words")


def group_a_b() -> list[str]:
    print(f"\n{LINE}\nA/B. alpha/'s source: no forbidden import, no network or order use\n{LINE}")
    files = sorted(p for p in ALPHA.rglob("*.py") if "__pycache__" not in p.parts)
    check(len(files) >= 10, f"alpha/ holds the lab's modules ({len(files)} files)")
    mods = []
    for p in files:
        rel = p.relative_to(REPO).with_suffix("")
        pkg = ".".join(rel.parts[:-1]) if p.name != "__init__.py" else ".".join(rel.parts[:-1])
        v = scan(p.read_text(encoding="utf-8"), str(p.relative_to(REPO)), pkg)
        check(not v, f"{p.relative_to(REPO)}: clean" + (f" -- {v}" if v else ""))
        mods.append(".".join(rel.parts) if p.name != "__init__.py"
                    else ".".join(rel.parts[:-1]))
    return mods


def group_c(mods: list[str]) -> None:
    print(f"\n{LINE}\nC. at import time, in a fresh interpreter: nothing forbidden loads\n{LINE}")
    code = ("import importlib, json, sys\n"
            f"sys.path.insert(0, {str(REPO)!r})\n"
            f"for m in {mods!r}:\n"
            "    importlib.import_module(m)\n"
            "import alpha.blocklist as _b\n"
            "_b.roots()\n"
            "print(json.dumps(sorted(sys.modules)))\n")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=str(REPO), timeout=300)
    check(r.returncode == 0, f"every alpha module imports ({len(mods)})"
          + ("" if r.returncode == 0 else f": {r.stderr.strip()[-400:]}"))
    if r.returncode:
        return
    loaded = json.loads(r.stdout.strip().splitlines()[-1])
    bad = sorted(m for m in loaded if forbidden(m) and m not in RUNTIME_ALLOWED)
    check(not bad, f"no forbidden module is loaded by importing alpha/ "
          f"({len(loaded)} modules loaded){'' if not bad else ': ' + ', '.join(bad[:12])}")
    net = [m for m in ("urllib.request", "http.client", "socket", "ssl", "requests")
           if m in loaded]
    check(not net, "and none of the network modules is loaded "
          "(urllib.request, http.client, socket, ssl, requests)"
          + (f": {net}" if net else ""))
    check("alpha._system_blocklist" in loaded and "register" not in loaded,
          "the system's blocklist, applied, is loaded from register/instruments.py's "
          "file, and the register package is not")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{LINE}\nTHE ALPHA LAB SENDS NOTHING ANYWHERE (X-1.5)\n{LINE}")
    self_test()
    mods = group_a_b()
    group_c(mods)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Validation gate for the Alpha Lab's daily proposer (X-2.10b; change order 10.2).
On the Tranche 2 fixture store, a fixture ledger and a FAKE model: no network,
no key, no live store, no box.

  A  NO ORDER, GATE OR BROKER IMPORT. Every .py under alpha_proposer/ is parsed
     and checked against PROPOSER_FORBIDDEN: the order gate and the register,
     the broker modules, the ledgers and report writers it may not write, the
     state emitter, subprocess -- and the harness, the workbench, the paper
     book and the loops, so it never sees a test result. It calls no
     rules.backtest. Then the package is imported in a fresh interpreter and
     sys.modules searched for the same list. (Unlike alpha/, it MAY import a
     network client: it makes one model call. alpha/'s own gate is unchanged.)
  B  IT WRITES ONLY THE INBOX AND ITS OWN LOG. No module but alpha_proposer/
     out.py opens a file for writing, renames or removes one; out.py refuses
     any path outside the two roots; a fixture run leaves every other file as
     it was.
  C  THE FAKE MODEL. Three proposals -- one valid, one a duplicate of a
     registered fixture hypothesis, one on a blocked instrument -- and exactly
     one is written, as a v1 batch (channel daily-proposer, source model,
     model_idea_rule true, the prompt version, the model id, the packet's
     sha256) with a manifest line whose sha256 is the file's; the ingestion
     accepts it, pre-registered at the manifest's instant; a second run on the
     same session writes nothing; four valid proposals write at most three, and
     a family over its weekly budget is cut.
  D  THE PACKET. Built by code, with every field the change order names, the
     register's titles and rule hashes (failures included) and no result.
  E  THE UNIT AND TIMER. 18:10 ET weekdays, after the nightly loop; not in
     DEPLOY_TIMERS (printed, never enabled); writes inbox/lab only.

    python tools/validate_alpha_proposer.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_alpha_proposer_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "store.sqlite")
os.environ.pop("ALPHA_DB", None)
for _k, _d in (("ALPHA_INBOX", "inbox"), ("ALPHA_OUTBOX", "outbox"),
               ("ALPHA_RESEARCH_DIR", "research"), ("ALPHA_REPORTS_DIR", "reports"),
               ("CHESTER_LOG_DIR", "logs")):
    os.environ[_k] = os.path.join(_TMP, _d)

import yaml  # noqa: E402

from altdata import observations  # noqa: E402

observations.DEFAULT_DB = os.environ["CHESTER_DB"]

PKG = REPO / "alpha_proposer"
LINE = "=" * 78
PASS = FAIL = 0
SEED = REPO / "tests" / "fixtures" / "alpha" / "inbox" / "hypotheses-2026-10-14.yaml"
SEED_SHA = "6fdc4dc7a32d659375e22e0dbe1293b480b4c0877c48174a8cc8272d14446626"
AS_OF = "2026-10-09T22:10:00+00:00"

PROPOSER_FORBIDDEN = (
    "register", "altdata.executions", "altdata.sources.ibkr_portfolio",
    "altdata.sources.ibkr_costs", "altdata.sources.ibkr_whatif",
    "altdata.loggers", "ib_insync", "ib_async", "ibapi", "ibkr",
    "altdata.probability_ledger", "altdata.narratives", "altdata.grader",
    "state", "daily_cascade.deliver", "monthly_macro", "subprocess",
    # the harness and everything that runs a test: it never sees a result
    "alpha.validate", "alpha.research", "alpha.paper", "alpha.loops",
    "alpha.allocate", "alpha.governor",
)
ORDER_NAMES = {"placeOrder", "place_order", "bracketOrder", "submit_order",
               "order_router", "ibkr_orders", "execution_framework", "reqGlobalCancel"}


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def forbidden(name: str) -> bool:
    return any(name == f or name.startswith(f + ".") for f in PROPOSER_FORBIDDEN)


def scan(src: str, name: str) -> list[str]:
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            out += [f"{name}:{node.lineno} imports {a.name}" for a in node.names
                    if forbidden(a.name)]
        elif isinstance(node, ast.ImportFrom):
            mod = ("alpha_proposer" if node.level else "") + (
                ("." if node.level and node.module else "") + (node.module or ""))
            if forbidden(mod):
                out.append(f"{name}:{node.lineno} imports from {mod}")
            for a in node.names:
                if not node.level and forbidden(f"{mod}.{a.name}"):
                    out.append(f"{name}:{node.lineno} imports {mod}.{a.name}")
        elif isinstance(node, ast.Call):
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if nm == "backtest":
                out.append(f"{name}:{node.lineno} runs a backtest")
            if nm in ("__import__", "import_module") and node.args and isinstance(
                    node.args[0], ast.Constant) and forbidden(str(node.args[0].value)):
                out.append(f"{name}:{node.lineno} dynamically imports {node.args[0].value}")
            if isinstance(fn, ast.Attribute) and getattr(fn.value, "id", "") == "os" \
                    and fn.attr in ("system", "popen"):
                out.append(f"{name}:{node.lineno} calls os.{fn.attr}")
        if isinstance(node, (ast.Name, ast.Attribute)):
            n = node.id if isinstance(node, ast.Name) else node.attr
            if n in ORDER_NAMES:
                out.append(f"{name}:{node.lineno} uses {n}")
    return out


def writes(src: str, name: str) -> list[str]:
    out = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        owner = getattr(getattr(fn, "value", None), "id", None)
        if nm == "open" and len(node.args) > 1 and isinstance(node.args[1], ast.Constant) \
                and any(c in str(node.args[1].value) for c in "wax+"):
            out.append(f"{name}:{node.lineno} open({node.args[1].value!r})")
        elif nm in ("write_text", "write_bytes", "unlink", "rmdir"):
            out.append(f"{name}:{node.lineno} {nm}()")
        elif owner in ("os", "shutil") and nm in ("replace", "rename", "remove",
                                                   "unlink", "rmtree", "copy",
                                                   "copyfile", "move"):
            out.append(f"{name}:{node.lineno} {owner}.{nm}()")
        elif owner in ("yaml", "json") and nm in ("dump", "safe_dump") and \
                len(node.args) > 1:
            out.append(f"{name}:{node.lineno} {owner}.{nm}(..., stream)")
    return out


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. NO ORDER, GATE OR BROKER IMPORT; NO HARNESS")
    files = sorted(p for p in PKG.rglob("*.py") if "__pycache__" not in p.parts)
    check(len(files) >= 4, f"alpha_proposer/ holds the proposer ({len(files)} files)")
    for p in files:
        v = scan(p.read_text(encoding="utf-8"), str(p.relative_to(REPO)))
        check(not v, f"{p.relative_to(REPO)}: clean" + (f" -- {v}" if v else ""))
    for src, what in (("from register import Register", "the register"),
                      ("from altdata.sources.ibkr_portfolio import x", "a broker module"),
                      ("import subprocess", "subprocess"),
                      ("from alpha.validate import run", "the harness"),
                      ("from alpha.research import workbench", "the workbench"),
                      ("rules.backtest(c, s, a, b)", "a backtest"),
                      ("ib.placeOrder(c, o)", "an order call")):
        check(bool(scan(src, "<self-test>")), f"the scan catches {what}")
    code = ("import importlib, json, sys\n"
            f"sys.path.insert(0, {str(REPO)!r})\n"
            "for m in ('alpha_proposer', 'alpha_proposer.packet', 'alpha_proposer.out',"
            " 'alpha_proposer.propose', 'alpha_proposer.__main__'):\n"
            "    importlib.import_module(m)\n"
            "from alpha_proposer import propose\n"
            "propose.model_id()\n"
            "print(json.dumps(sorted(sys.modules)))\n")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       cwd=str(REPO), timeout=300)
    check(r.returncode == 0, "the package imports, and resolves its model id through "
          "the reports' config" + ("" if r.returncode == 0 else f": {r.stderr[-400:]}"))
    if r.returncode == 0:
        loaded = json.loads(r.stdout.strip().splitlines()[-1])
        bad = sorted(m for m in loaded if forbidden(m))
        check(not bad, f"at import time no order, gate, broker or harness module loads "
              f"({len(loaded)} modules)" + (f": {bad[:8]}" if bad else ""))


def group_b() -> None:
    head("B. IT WRITES ONLY THE INBOX AND ITS OWN LOG")
    for p in sorted(PKG.rglob("*.py")):
        if "__pycache__" in p.parts or p.name == "out.py":
            continue
        w = writes(p.read_text(encoding="utf-8"), str(p.relative_to(REPO)))
        check(not w, f"{p.relative_to(REPO)} writes no file" + (f": {w}" if w else ""))
    from alpha_proposer import out                              # noqa: PLC0415
    for fn, args, what in ((out.write_batch, ("../escape.yaml", b"x"), "a path out of the inbox"),
                           (out.write_batch, ("note.md", b"x"), "a non-batch name")):
        try:
            fn(*args)
            check(False, f"out.py refuses {what}")
        except (out.OutsideTheProposer, FileExistsError):
            check(True, f"out.py refuses {what}")


class FakeBlock:
    def __init__(self, t: str) -> None:
        self.type, self.text = "text", t


class FakeResp:
    def __init__(self, t: str) -> None:
        self.content, self.model = [FakeBlock(t)], "fake-model-1"


class FakeClient:
    def __init__(self, reply: str) -> None:
        self.reply, self.calls = reply, 0
        self.messages = self

    def create(self, **kw):
        self.calls += 1
        self.kw = kw
        return FakeResp(self.reply)


TITLES = ["Fixture: SPY after a two-sigma down day",
          "Gold miners lag when real yields jump",
          "Small caps rally on a breadth thrust",
          "Energy reverses after an inventory shock",
          "Utilities bid when the curve bull-flattens",
          "Semiconductors fade a gap through resistance",
          "Transports lead industrials out of a pause",
          "Banks follow the two-year after payrolls",
          "Staples lag in a melt-up week",
          "The dollar's breakout fails in the first hour"]


def _valid(i: int, family: str = "mean-reversion") -> dict:
    return {"title": TITLES[i % len(TITLES)] if i < 10 else f"{TITLES[i % len(TITLES)]} ({i})",
            "horizon_class": "short", "horizon_sessions": 3, "family": family,
            "mechanism": "Fixture mechanism: forced selling overshoots and dealers "
                         "long gamma buy the dip.",
            "universe": ["SPY"], "rule_text": f"fixture rule {i}",
            "expected": {"sign": "positive_expectancy_after_costs"},
            "sample": {"min_independent_signals": 100},
            "data": {"in_store": ["yfinance.mkt_spy"], "gaps": []},
            "state_at_registration": "fixture",
            "rule_dsl": {"grammar": "alpha-lab-rules/v1", "universe": ["SPY"],
                         "cadence": "daily_close",
                         "trigger": [{"series": "SPY", "transform": "zscore",
                                      "w": 60 + i, "op": "<=", "value": -2.0}],
                         "direction": "long", "instrument": "SPY",
                         "entry": "next_open", "exits": {"time": 3}}}


def reply(props: list[dict]) -> str:
    return "Here are today's.\n```yaml\n" + yaml.safe_dump({"hypotheses": props},
                                                            sort_keys=False) + "```\n"


def tree_snapshot() -> dict:
    out = {}
    for p in REPO.rglob("*"):
        if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts \
                and ".venv" not in p.parts:
            out[str(p)] = p.stat().st_mtime_ns
    return out


def group_c_d() -> None:
    head("C. THE FAKE MODEL: ONE VALID, ONE DUPLICATE, ONE BLOCKED -> EXACTLY ONE")
    from tests.fixtures.alpha import fixture_store              # noqa: PLC0415
    fixture_store.build(os.environ["CHESTER_DB"])
    from alpha import hypotheses as hyp                         # noqa: PLC0415
    from alpha import inbox, intake                             # noqa: PLC0415
    from alpha.ledger import Ledger                             # noqa: PLC0415
    from alpha.store import ReadOnlyStore                       # noqa: PLC0415
    from alpha_proposer import packet, propose                  # noqa: PLC0415
    st = ReadOnlyStore(os.environ["CHESTER_DB"])
    lp = Path(_TMP) / "alpha.db"
    raw = SEED.read_bytes()
    seed = hyp.load_batch(raw.decode("utf-8"))
    with Ledger(lp) as lg:
        intake.admit(lg, st, seed, hyp.instant("2026-10-14T09:26:23.000Z"),
                     "2026-10-14T21:40:00+00:00", SEED.name, SEED_SHA)
        lg.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    h5 = dict(seed["hypotheses"][4])
    h5["rule_dsl"] = yaml.safe_load((REPO / "alpha" / "research" / "translations" /
                                     "2026-10-14-claude-weekly-01" / "H-005.yaml")
                                    .read_text(encoding="utf-8"))["rule_dsl"]
    bn = dict(_valid(9), title="Fixture: a Brookfield name", universe=["BN"],
              rule_text="buy BN on a dip")
    bn.pop("rule_dsl")
    fake = FakeClient(reply([_valid(1), h5, bn]))
    before = tree_snapshot()
    ro = Ledger(lp, read_only=True)
    try:
        rec = propose.run(st, ro, AS_OF, cl=fake, model="fake-model-1")
    finally:
        ro.close()
    after = tree_snapshot()
    box = Path(os.environ["ALPHA_INBOX"])
    written = sorted(p.name for p in box.glob("*.yaml"))
    check(fake.calls == 1 and rec.get("state") == "written"
          and written == ["proposals-2026-10-09.yaml"],
          f"one model call; one batch file written ({written})")
    batch = yaml.safe_load((box / written[0]).read_text(encoding="utf-8")) if written else {}
    hs = batch.get("hypotheses") or []
    check(len(hs) == 1 and hs[0]["title"] == _valid(1)["title"],
          "exactly one proposal written: the valid one")
    why = {r["title"]: r["why"] for r in rec.get("rejected") or []}
    check(any("duplicate" in w and "HYP-" in w for w in why.values())
          and any("blocked" in w for w in why.values()),
          f"the duplicate of a registered hypothesis and the blocked one are refused "
          f"by code, with reasons ({sorted(why.values())[:2]})")
    check(batch.get("channel") == "daily-proposer" and batch.get("source") == "model"
          and batch.get("model_idea_rule") is True
          and batch.get("prompt_version") == propose.prompt_version()
          and batch.get("model_id") == "fake-model-1"
          and batch.get("packet_sha256") == rec.get("packet_sha256")
          and hyp.validate_batch(batch) == [],
          f"a v1 batch: channel daily-proposer, source model, model_idea_rule, prompt "
          f"{batch.get('prompt_version')}, model id, packet sha256")
    man = [json.loads(x) for x in (box / "manifest-proposer.jsonl").read_text(
        encoding="utf-8").splitlines()]
    check(len(man) == 1 and man[0]["sha256"] == hashlib.sha256(
        (box / written[0]).read_bytes()).hexdigest() and man[0]["written_at"],
          "its manifest line carries the file's sha256 and its write time")
    logs = list(Path(os.environ["CHESTER_LOG_DIR"]).glob("alpha_proposer-*.jsonl"))
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    check(logs and not changed,
          "it wrote the inbox and its own log, and no file in the repository")
    sysp = fake.kw.get("system", "")
    check("alpha-lab-rules/v1" in sysp and "AT MOST THREE" in sysp
          and fake.kw.get("thinking") == {"type": "disabled"},
          "the prompt carries the grammar and the rules; thinking is off")
    with Ledger(lp) as lg:
        res = inbox.ingest(lg, st, "2026-10-12T21:40:00+00:00")
        ing = [r for r in res["ingested"] if r["file"] == written[0]] if written else []
        hid = (ing[0]["registered"] or {}).get("P-1") if ing else None
        h = hyp.Register(lg).get(hid) if hid else None
    check(h is not None and h["pre_registered_at"] == hyp.instant(man[0]["written_at"])
          and h["channel"] == "daily-proposer" and h["status"] == "registered",
          "the next nightly loop ingests it, pre-registered at the manifest's instant")
    ro = Ledger(lp, read_only=True)
    try:
        rec2 = propose.run(st, ro, AS_OF, cl=FakeClient(reply([_valid(2)])))
        four = propose.check([_valid(i) for i in (2, 3, 4, 5)], st, ro, "2026-11-02")
        fam = propose.check([_valid(6, "rotation-tell"), _valid(7, "rotation-tell"),
                             _valid(8, "rotation-tell")], st, ro, "2026-10-14")
    finally:
        ro.close()
    check(rec2.get("state") == "skipped", "a second run on the same session writes nothing")
    check(len(four[0]) == 2 and any("of family" in r["why"] for r in four[1]),
          f"four valid proposals of one family: the weekly family budget (2) cuts them "
          f"({len(four[0])} kept)")
    check(len(fam[0]) == 2,
          "and the budget counts the register's own week for the family")
    many = [_valid(2 + i, f"fam-{i}") for i in range(4)]
    ro = Ledger(lp, read_only=True)
    try:
        cut = propose.check(many, st, ro, "2026-10-15")
    finally:
        ro.close()
    check(len(cut[0]) == 3 and any("a session day" in r["why"] for r in cut[1]),
          "four of four families: at most three a session day")

    head("D. THE PACKET, BUILT BY CODE")
    ro = Ledger(lp, read_only=True)
    try:
        pkt = packet.build(st, ro, AS_OF)
    finally:
        ro.close()
    want = {"session", "as_of", "moves", "screen", "dealer", "state", "prediction",
            "calendar", "agenda", "register", "budgets", "dictionary"}
    check(want <= set(pkt), f"every field: {sorted(want)}")
    check(len(pkt["moves"]) >= 10 and all("z" in m for m in pkt["moves"])
          and pkt["screen"]["sigma"] == 2.5,
          f"the basket's moves with z-scores ({len(pkt['moves'])}), the 2.5-sigma screen")
    check(pkt["register"] and all(set(r) == {"id", "title", "family", "status",
                                             "rule_hash"} for r in pkt["register"])
          and any(r["status"] == "needs_code" for r in pkt["register"]),
          "the register's titles, statuses and rule hashes -- and no result")
    check(any(d["key"] == "fred.ccc_oas" and d["first"] <= "2018-01-03"
              for d in pkt["dictionary"]) and pkt["calendar"] is not None
          and "dials" in pkt["state"] and pkt["dealer"],
          "the data dictionary with history starts, the calendar, the state, the dealer")
    st.close()


def group_e() -> None:
    head("E. THE UNIT AND TIMER (printed, never enabled)")
    sd = REPO / "deploy" / "systemd"
    tm = (sd / "chester-alpha-proposer.timer").read_text(encoding="utf-8")
    sv = (sd / "chester-alpha-proposer.service").read_text(encoding="utf-8")
    check(re.search(r"^OnCalendar=Mon-Fri 18:10 America/New_York$", tm, re.M) is not None,
          "the timer fires weekdays at 18:10 ET")
    nt = (sd / "chester-alpha-nightly.timer").read_text(encoding="utf-8")
    ns = (sd / "chester-alpha-nightly.service").read_text(encoding="utf-8")
    tmo = int(re.search(r"^TimeoutStartSec=(\d+)min", ns, re.M).group(1))
    check("Mon-Fri 17:40" in nt and 17 * 60 + 40 + 1 + tmo < 18 * 60 + 10
          and "After=chester-alpha-nightly.service" in sv,
          "after the nightly loop's whole budget (17:40 + 60 s + its 20-minute cap)")
    remote = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    timers = re.search(r'DEPLOY_TIMERS="([^"]*)"', remote, re.S).group(1).split()
    check("chester-alpha-proposer.timer" not in timers,
          "not in DEPLOY_TIMERS: the deploy copies it, enabling is the operator's")
    rw = re.search(r"^ReadWritePaths=(.*)$", sv, re.M).group(1).split()
    check(rw == ["%h/logs", "%h/.chester", "%h/chester-reports",
                 "-%h/chester-data/inbox/lab"],
          "it may write its logs, its status, the checkout's pull, and the inbox only")
    w = (REPO / "scripts" / "run_alpha_proposer.sh").read_text(encoding="utf-8")
    check("-m alpha_proposer" in w and "git pull --ff-only" in w
          and "altdata.session is-session" in w,
          "the wrapper pulls, asks the session calendar, runs alpha_proposer")


def main() -> int:
    print(f"{LINE}\nTHE ALPHA LAB'S DAILY PROPOSER (X-2.10b) -- FIXTURE STORE, FAKE MODEL\n{LINE}")
    for g in (group_a, group_b, group_c_d, group_e):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

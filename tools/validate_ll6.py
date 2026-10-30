#!/usr/bin/env python3
"""
Validation gate: Learning Loop v2, LL-6 -- the forecasters and the second
provider behind the meter (A94; the brief's section 2.3; decision 4 ruled D38:
Gemini, the key the operator's). Fixtures only: fake clients, a fake HTTP opener
and a SYNTHETIC key. Nothing here calls a provider.

  A  NO KEY        a provider with no key prints "<provider>: skipped, key not
                   configured", and the aggregate comes from the forecasters present
  B  THE KEY       a synthetic key reaches the request's header and nowhere else: not
                   the URL, a printed line, a log record, a manifest, the client's repr
                   or an error's text
  C  THE BUDGET    zero calls a day blocks the call before it is made; the shipped
                   config's budgets are zero; a spent budget skips and says so
  D  THE AGGREGATE the extremized log-odds mean, by hand; n printed; clipping
  E  MANIFESTS     one line per forecaster per run, appended: a second run leaves the
                   first run's lines as they were; the module opens the file only to
                   append; each line carries provider, model, prompt sha256, as-of,
                   output and tokens
  F  THE METER     each call is a model_calls row; the lines split the providers, each
                   beside its budget
  G  RIGHTS        no report writer, the register or the object imports the forecasters
"""

from __future__ import annotations

import ast
import copy
import io
import json
import logging
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

from altdata import forecasters as fc                          # noqa: E402
from altdata import model_meter as meter                       # noqa: E402

TD = Path(gate_mkdtemp("ll6_"))
LINE = "=" * 78
PASS = FAIL = 0
KEY_NAME = "GEMINI" + "_API_KEY"
SYNTHETIC_KEY = "synthetic-fixture-key-7f3a9c21d04e"     # SYNTHETIC: no real key
QS = [{"id": "q1", "question": "Does the synthetic claim resolve YES?"},
      {"id": "q2", "question": "Does the second synthetic claim resolve YES?"}]


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


class FakeAnthropic:
    def __init__(self, reply: str) -> None:
        self.reply, self.calls = reply, 0
        self.messages = self

    def create(self, model, max_tokens, messages):
        self.calls += 1
        return SimpleNamespace(model=model, content=[SimpleNamespace(text=self.reply)],
                               usage=SimpleNamespace(input_tokens=120, output_tokens=12))


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeOpener:
    """Records each request; answers with Gemini's shape, or an HTTP error."""

    def __init__(self, reply: str, status: int = 200) -> None:
        self.reply, self.status, self.requests = reply, status, []

    def __call__(self, req, timeout=None):
        import urllib.error                                     # noqa: PLC0415
        self.requests.append(req)
        if self.status != 200:
            raise urllib.error.HTTPError(req.full_url, self.status, "error", {}, None)
        body = {"candidates": [{"content": {"parts": [{"text": self.reply}]}}],
                "usageMetadata": {"promptTokenCount": 110, "candidatesTokenCount": 9},
                "modelVersion": "gemini-2.5-pro"}
        return FakeResponse(json.dumps(body).encode("utf-8"))


def cfg_with(anthropic: int, gemini: int) -> dict:
    c = copy.deepcopy(fc.config())
    c["budgets"] = {"anthropic": {"calls_per_day": anthropic},
                    "gemini": {"calls_per_day": gemini}}
    return c


def group_a() -> None:
    head("A. NO KEY")
    os.environ.pop(KEY_NAME, None)
    cli, why = meter.gemini_client(fc.config())
    check(cli is None and why == "key not configured", f"no key: no client ({why})")
    fa = FakeAnthropic('{"q1": 0.6, "q2": 0.3}')
    r = fc.run(QS, "2026-10-30T20:45:00+00:00", cfg=cfg_with(2, 1),
               clients={"anthropic": (fa, ""), "gemini": (None, why)},
               db_path=str(TD / "a.db"), manifests=TD / "a.jsonl")
    check("gemini: skipped, key not configured" in r["lines"],
          "the run prints 'gemini: skipped, key not configured'")
    check(any(l.startswith("aggregate q1: 0.60 (n=2 of 3 forecasters") for l in r["lines"]),
          f"the aggregate comes from the two present and says so "
          f"({[l for l in r['lines'] if l.startswith('aggregate q1')]})")


def group_b() -> None:
    head("B. THE KEY")
    os.environ[KEY_NAME] = SYNTHETIC_KEY
    cap = io.StringIO()
    h = logging.StreamHandler(cap)
    logging.getLogger().addHandler(h)
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        op = FakeOpener('{"q1": 0.8, "q2": 0.2}')
        cli, why = meter.gemini_client(fc.config(), opener=op)
        fa = FakeAnthropic('{"q1": 0.6, "q2": 0.3}')
        r = fc.run(QS, "2026-10-30T20:45:00+00:00", cfg=cfg_with(2, 1),
                   clients={"anthropic": (fa, ""), "gemini": (cli, why)},
                   db_path=str(TD / "b.db"), manifests=TD / "b.jsonl")
        req = op.requests[0] if op.requests else None
        hdr = {k.lower(): v for k, v in (req.header_items() if req else [])}
        check(req is not None and hdr.get("x-goog-api-key") == SYNTHETIC_KEY
              and SYNTHETIC_KEY not in req.full_url,
              "the key travels in the request's header, never in its URL")
        bad = FakeOpener("", status=500)
        cli2, _ = meter.gemini_client(fc.config(), opener=bad)
        cli2._sleep = lambda s: None
        err = ""
        try:
            cli2.generate("gemini-2.5-pro", "x")
        except meter.ProviderError as exc:
            err = str(exc)
        texts = {"the printed lines": "\n".join(r["lines"]),
                 "the manifests": (TD / "b.jsonl").read_text(encoding="utf-8"),
                 "the log": cap.getvalue(), "the client's repr": repr(cli),
                 "an error's text": err}
        leaks = [k for k, v in texts.items() if SYNTHETIC_KEY in v]
        check(not leaks and err == "gemini HTTP 500" and len(bad.requests) == 2,
              f"the key appears in none of {sorted(texts)} (leaks: {leaks or 'none'}); "
              f"a 500 is retried once and reported as '{err}'")
    finally:
        logging.getLogger().removeHandler(h)
        os.environ.pop(KEY_NAME, None)


def group_c() -> None:
    head("C. THE BUDGET")
    shipped = fc.config()["budgets"]
    check(shipped == {"anthropic": {"calls_per_day": 0}, "gemini": {"calls_per_day": 0}},
          f"the shipped budgets are zero calls a day ({shipped})")
    fa = FakeAnthropic('{"q1": 0.6}')
    blocked = False
    with meter.scope(report="forecasters", db_path=str(TD / "c.db")):
        try:
            meter.create_metered("anthropic", fa, model="claude-opus-5-5", prompt="x",
                                 cfg=fc.config())
        except meter.BudgetExhausted:
            blocked = True
    check(blocked and fa.calls == 0, "a zero budget blocks the call before it is made")
    fa2 = FakeAnthropic('{"q1": 0.6, "q2": 0.3}')
    r = fc.run(QS, "2026-10-30T20:45:00+00:00", cfg=cfg_with(1, 0),
               clients={"anthropic": (fa2, ""), "gemini": (None, "key not configured")},
               db_path=str(TD / "c2.db"), manifests=TD / "c2.jsonl")
    check(fa2.calls == 1 and any(l.startswith("opus-b (anthropic): skipped, budget 1 call(s) a day, 1 used")
                                for l in r["lines"]),
          "a spent budget: the first forecaster calls, the second is skipped and says so")


def group_d() -> None:
    head("D. THE AGGREGATE")
    lg = lambda p: math.log(p / (1 - p))                        # noqa: E731
    sig = lambda z: 1 / (1 + math.exp(-z))                      # noqa: E731
    v = fc.aggregate([0.6, 0.8])
    check(abs(v - sig((lg(0.6) + lg(0.8)) / 2)) < 1e-12 and abs(v - 0.71010) < 1e-4,
          f"the log-odds mean of 0.6 and 0.8 is {v:.4f}")
    v2 = fc.aggregate([0.6, 0.8], extremize=2.0)
    check(abs(v2 - sig(2 * (lg(0.6) + lg(0.8)) / 2)) < 1e-12 and v2 > v,
          f"extremized by 2 it moves outward ({v2:.4f})")
    v3 = fc.aggregate([1.0, 0.5])
    check(abs(v3 - sig((lg(0.99) + 0.0) / 2)) < 1e-12, "a 1.0 is clipped to 0.99 first")
    check(fc.aggregate([]) is None, "no answers, no aggregate")
    check(fc.config()["aggregate"]["extremize"] == 1.0,
          "the shipped factor is 1.0 (the brief names none; a ruling sets it)")


def group_e() -> None:
    head("E. MANIFESTS")
    p = TD / "e.jsonl"
    for reply in ('{"q1": 0.6, "q2": 0.3}', '{"q1": 0.7, "q2": 0.4}'):
        fc.run(QS, "2026-10-30T20:45:00+00:00", cfg=cfg_with(5, 0),
               clients={"anthropic": (FakeAnthropic(reply), ""),
                        "gemini": (None, "key not configured")},
               db_path=str(TD / "e.db"), manifests=p)
        if reply.startswith('{"q1": 0.6'):
            first = p.read_text(encoding="utf-8")
    after = p.read_text(encoding="utf-8")
    check(after.startswith(first) and len(after.splitlines()) == 4,
          "two runs of two forecasters: four lines, the first run's untouched")
    e = json.loads(after.splitlines()[0])
    need = {"provider", "model", "prompt_id", "prompt_sha256", "inputs_as_of", "output",
            "cost", "source", "run_id", "forecaster"}
    check(need <= set(e) and e["source"] == "forecaster:anthropic:base-rate-v1"
          and e["output"] == {"q1": 0.6, "q2": 0.3} and e["cost"]["input_tokens"] == 120,
          f"a line carries {sorted(need)}")
    tree = ast.parse((REPO / "altdata" / "forecasters.py").read_text(encoding="utf-8"))
    modes = [a.value for n in ast.walk(tree) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", getattr(n.func, "id", "")) == "open"
             for a in n.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
    check(modes == ["a"] and "write_text" not in ast.dump(tree),
          f"the module opens the manifest only to append ({modes})")


def group_f() -> None:
    head("F. THE METER")
    os.environ[KEY_NAME] = SYNTHETIC_KEY
    try:
        op = FakeOpener('{"q1": 0.8, "q2": 0.2}')
        cli, why = meter.gemini_client(fc.config(), opener=op)
        db = str(TD / "f.db")
        fc.run(QS, "2026-10-30T20:45:00+00:00", cfg=cfg_with(2, 1),
               clients={"anthropic": (FakeAnthropic('{"q1": 0.6, "q2": 0.3}'), ""),
                        "gemini": (cli, why)}, db_path=db, manifests=TD / "f.jsonl")
    finally:
        os.environ.pop(KEY_NAME, None)
    from altdata import session                                 # noqa: PLC0415
    day = session.session_date()
    check(meter.calls_today(db, "anthropic") == 2 and meter.calls_today(db, "gemini") == 1,
          "three calls recorded: two Anthropic, one Gemini")
    lines = meter.provider_lines(db, day, cfg_with(2, 1))
    check(lines[0].startswith("Model (anthropic): 2 call(s), 240 input / 24 output")
          and lines[1].startswith("Model (gemini): 1 call(s), 110 input / 9 output")
          and lines[1].endswith("forecaster budget 1 a day"),
          f"the lines split the providers beside their budgets ({lines})")


def group_g() -> None:
    head("G. RIGHTS")
    hits = []
    for d in ("daily_cascade", "monthly_macro", "register", "alpha"):
        for f in (REPO / d).rglob("*.py"):
            t = f.read_text(encoding="utf-8", errors="replace")
            if "forecasters" in t and ("import forecasters" in t or "altdata.forecasters" in t):
                hits.append(str(f.relative_to(REPO)))
    for f in ("regime.py",):
        if "forecasters" in (REPO / f).read_text(encoding="utf-8"):
            hits.append(f)
    check(not hits, f"no report writer, the register, the lab or the object imports it ({hits})")


def main() -> int:
    try:
        for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
            g()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

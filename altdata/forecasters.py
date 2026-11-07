"""
The forecasters: Learning Loop v2, LL-6 (A94; the brief's section 2.3, on
b65-learning-loop-v2; decision 4 ruled D38: two Anthropic forecasters with
distinct prompts and one on a second provider, Gemini, the key the operator's).

    python -m altdata.forecasters status                   # what each would do; no call
    python -m altdata.forecasters run --questions FILE     # answer a packet's questions

Each forecaster answers the same code-built packet's questions as probabilities,
independently (decision 5): it never sees another's answer. Each answer is its
own source, forecaster:<provider>:<prompt-id>, and the aggregate is
forecaster:aggregate.

THE RULES:
- NO KEY, A STATED SKIP. A provider whose key is not configured prints
  "<provider>: skipped, key not configured"; the aggregate is computed from the
  forecasters present and says how many.
- NOTHING SPENDS BY SURPRISE. Every call goes through model_meter.create_metered,
  refused past the provider's daily budget in config/forecasters.yaml, which
  starts at zero.
- THE KEY NEVER LEAVES THE CLIENT. It is read through altdata.secrets, sent as a
  header, and never reaches a printed line, a log line or a manifest.
- MANIFESTS ARE APPEND-ONLY. One JSON line per forecaster per run: provider, model
  id, prompt id and its sha256, the packet's as-of, the output and the tokens.
  The file is only ever opened for appending.
- THE AGGREGATE is section 2.3's: the extremized mean of the log-odds, weighted
  by track record, equal until each forecaster has 100 resolved rows (none has
  yet). The extremizing factor is config's (1.0 until ruled) and prints beside it.
- RIGHTS: none. No forecaster output reaches a packet, a dial, the register or a
  report sentence.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Optional

from . import model_meter as meter
from . import session

CONFIG = meter.FORECASTERS_CONFIG


def config(path: Optional[Path] = None) -> dict:
    return meter.forecasters_config(path)


def source_id(f: dict) -> str:
    return f"forecaster:{f['provider']}:{f['prompt_id']}"


def prompt_sha(f: dict) -> str:
    return hashlib.sha256(str(f.get("prompt") or "").encode("utf-8")).hexdigest()


def packet_text(questions: list[dict], as_of: str) -> str:
    """The code-built packet every forecaster reads: the questions and their
    resolution criteria, nothing of another forecaster's answer."""
    lines = [f"As of {as_of}. Questions:"]
    for q in questions:
        lines.append(f"- {q['id']}: {q['question']}"
                     + (f" (resolves by {q['resolves_by']})" if q.get("resolves_by") else ""))
    return "\n".join(lines)


def parse_probabilities(text: str, ids: list[str]) -> dict[str, float]:
    """{question id: probability} from a reply's JSON; anything else is dropped."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        raw = json.loads(m.group(0))
    except ValueError:
        return {}
    out = {}
    for k in ids:
        try:
            v = float(raw.get(k))
        except (TypeError, ValueError):
            continue
        if 0.0 <= v <= 1.0:
            out[k] = v
    return out


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def aggregate(probs: list[float], extremize: float = 1.0,
              clip: tuple[float, float] = (0.01, 0.99),
              weights: Optional[list[float]] = None) -> Optional[float]:
    """The (weighted) mean of the log-odds, times the extremizing factor, back to
    a probability. None with no input."""
    if not probs:
        return None
    lo, hi = clip
    ps = [min(max(float(p), lo), hi) for p in probs]
    w = weights or [1.0] * len(ps)
    z = sum(wi * _logit(p) for wi, p in zip(w, ps)) / sum(w)
    return 1.0 / (1.0 + math.exp(-extremize * z))


def append_manifest(path: Path, entry: dict) -> None:
    """One line, appended; the file is never opened for writing over."""
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def _clients(cfg: dict, clients: Optional[dict]) -> dict[str, tuple[Any, str]]:
    if clients is not None:
        return clients
    return {"anthropic": meter.client(), "gemini": meter.gemini_client(cfg)}


def run(questions: list[dict], as_of: str, cfg: Optional[dict] = None,
        clients: Optional[dict] = None, db_path: Optional[str] = None,
        manifests: Optional[Path] = None, run_id: Optional[str] = None) -> dict:
    """Every forecaster over the packet, then the aggregate per question.
    Returns {lines, answers, aggregate}; the lines carry no key."""
    c = cfg if cfg is not None else config()
    run_id = run_id or session.new_run_id("forecasters")
    ids = [q["id"] for q in questions]
    packet = packet_text(questions, as_of)
    cl = _clients(c, clients)
    mpath = Path(manifests or c.get("manifests_path") or "forecasters.jsonl").expanduser()
    lines, answers = [], {}
    skipped_providers: set[str] = set()
    fs = c.get("forecasters") or []
    with meter.scope(report="forecasters", run_id=run_id, db_path=db_path):
        for f in fs:
            prov = f["provider"]
            client_, why = cl.get(prov, (None, "no client"))
            if client_ is None:
                if prov not in skipped_providers:
                    lines.append(f"{prov}: skipped, {why}")
                    skipped_providers.add(prov)
                continue
            if not f.get("model"):
                lines.append(f"{f['id']} ({prov}): skipped, no model set")
                continue
            try:
                with meter.scope(section=f["id"]):
                    resp = meter.create_metered(prov, client_, model=f["model"],
                                                prompt=f"{f['prompt']}\n\n{packet}", cfg=c)
            except meter.BudgetExhausted as exc:
                lines.append(f"{f['id']} ({prov}): skipped, {exc}")
                continue
            except Exception as exc:                            # noqa: BLE001
                from . import secrets                           # noqa: PLC0415
                lines.append(f"{f['id']} ({prov}): failed, "
                             f"{secrets.redact(type(exc).__name__ + ': ' + str(exc))}")
                continue
            text = getattr(resp, "text", None)
            if text is None:
                text = "".join(getattr(b, "text", "") for b in getattr(resp, "content", []) or [])
            got = parse_probabilities(text, ids)
            answers[f["id"]] = got
            usage = getattr(resp, "usage", None)
            append_manifest(mpath, {
                "run_id": run_id, "at": session.utc_iso(), "forecaster": f["id"],
                "source": source_id(f), "provider": prov,
                "model": getattr(resp, "model", None) or f["model"],
                "prompt_id": f["prompt_id"], "prompt_sha256": prompt_sha(f),
                "inputs_as_of": as_of, "questions": ids, "output": got,
                "cost": {"input_tokens": getattr(usage, "input_tokens", None),
                         "output_tokens": getattr(usage, "output_tokens", None)}})
            lines.append(f"{f['id']} ({prov}): answered {len(got)} of {len(ids)}")
    ag = c.get("aggregate") or {}
    a = float(ag.get("extremize", 1.0))
    clip = tuple(ag.get("clip") or (0.01, 0.99))
    agg = {}
    for q in ids:
        ps = [ans[q] for ans in answers.values() if q in ans]
        v = aggregate(ps, a, clip)
        agg[q] = {"p": v, "n": len(ps)}
        lines.append(f"aggregate {q}: "
                     + (f"{v:.2f}" if v is not None else "none")
                     + f" (n={len(ps)} of {len(fs)} forecasters; extremized log-odds "
                       f"mean, factor {a:g}, equal weights)")
    return {"lines": lines, "answers": answers, "aggregate": agg, "run_id": run_id}


def status(cfg: Optional[dict] = None, clients: Optional[dict] = None,
           db_path: Optional[str] = None) -> list[str]:
    """What each forecaster would do now: no call is made."""
    c = cfg if cfg is not None else config()
    cl = _clients(c, clients)
    out = []
    for f in c.get("forecasters") or []:
        prov = f["provider"]
        client_, why = cl.get(prov, (None, "no client"))
        if client_ is None:
            out.append(f"{f['id']} ({prov}): skipped, {why}")
            continue
        b, used = meter.budget(prov, c), meter.calls_today(db_path, prov)
        out.append(f"{f['id']} ({prov}): ready, model {f.get('model')}, budget {b} a day, "
                   f"{used} used" + ("" if used < b else " -- would be skipped"))
    return out


def _main(argv: Optional[list[str]] = None) -> int:
    import argparse                                             # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    r = sub.add_parser("run")
    r.add_argument("--questions", required=True)
    r.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "status":
        print("\n".join(status()))
        return 0
    qs = json.loads(Path(a.questions).read_text(encoding="utf-8"))
    print("\n".join(run(qs, a.as_of or session.utc_iso())["lines"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

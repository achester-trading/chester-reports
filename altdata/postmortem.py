"""
Code-built post-mortems -- one file per graded miss of the week, the evidence
laid out for the operator's stamp (Learning Loop v2, LL-4; A80).

    python -m altdata.postmortem week [--saturday YYYY-MM-DD] [--db PATH]
                                      [--out-root DIR] [--dry-run] [--shorten]

The brief's section 2.7 (docs/briefs/learning-loop-v2-brief-2026-10-25.md),
decisions 9 and 11 as ruled 25 Oct 2026: weekly, the Saturday before the Sunday
session; code builds the whole post-mortem; a model may only shorten it and
never names a cause (R-4: "an LLM never writes counterfactual attribution").

WHAT A FILE IS. For every error-corpus row (altdata/error_corpus.py: a ledger row
past the coin's Brier, a grade below zero R) whose outcome landed in the week
ending that Saturday, `<out-root>/docs/postmortems/<saturday>/<corpus_id>.md`,
in four parts, every one read from a stored row:

  1. What was said: the emission as stored (the claim and its probability, or
     the decision; for a decision, the register's thesis, falsifiers and
     counter-thesis as recorded at entry).
  2. What happened: the resolution or the grade, and the margin in its unit.
  3. What was missing at emission: the source's missing_inputs, the object's
     absent dimensions and awaiting legs ("not recorded" where NULL).
  4. The decision it fed: the decision for a grade; "none recorded" for a ledger
     row (the ledger records no link to a decision).

Then the Doctrine's six categorical questions (Part IX, 9.2), and its seventh
field (a rule broken) and the one-line note, as BLANK fields: the operator's
answers are the only cause field there is. A hit is not in the corpus and gets
no file. A file already written is never rewritten: the operator may have
stamped it.

THE SHORTENING, off by default (`--shorten`). One call per file through
altdata/model_meter.py, with the narrative step's model, asking for one
paragraph of what the file already says. Its output is refused, and the file
keeps the code-built parts alone with the reason, when it names a cause (a
cause field or causal wording, CAUSE_WORDS) or carries a figure the file's own
rows do not hold (altdata/numeral_audit.py).

Report-only. It writes files under its out-root and nothing else: not the
register, not the ledger, not the corpus, not review_changed.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parent.parent
log = logging.getLogger("altdata.postmortem")

METHOD = "postmortem-v1"
SUBDIR = Path("docs") / "postmortems"

# The Doctrine's 9.2, in its own order and words; the categories are the remedies.
QUESTIONS = (
    ("thesis", "Was the thesis wrong?"),
    ("timing", "Was the timing wrong?"),
    ("expression", "Was the expression wrong?"),
    ("size", "Was the size wrong?"),
    ("regime", "Did the regime change during the trade?"),
    ("signal", "Was the signal itself degraded (its family's trailing expectancy "
               "below its long-run figure)?"),
)
SEVENTH = ("rule_broken", "Was any rule broken, and which? (the seventh field)")
NOTE = ("note", "One-line note")

# A shortening that names a cause is refused. A cause field, or the wording that
# attributes one; the list is declared, and a refusal costs only the paragraph.
CAUSE_WORDS = re.compile(
    r"(?im)^\s*[*_#>-]*\s*(?:root\s+)?causes?\s*[:=]"
    r"|\b(?:because|caused|causes|cause of|due to|driven by|owing to|led to|"
    r"leading to|resulted from|as a result of|attributable|attributed|blame[sd]?|"
    r"the reason|why it|explains?|explained)\b")

SHORTEN_PROMPT = (
    "Below is a post-mortem built by code from stored records: what a forecast or "
    "decision said, what happened, and what inputs were missing when it was made. "
    "Rewrite its first three parts as ONE short paragraph of plain prose, for an "
    "operator who will answer six yes-or-no questions about it.\n\n"
    "Rules, every one binding:\n"
    "- Say only what the record says. Do not explain the outcome, name a cause, "
    "or say why anything happened. Do not use the words because, due to, driven "
    "by, led to, caused, or explains.\n"
    "- Use no number that is not printed in the record, and copy each number as "
    "printed.\n"
    "- Do not answer or hint at the six questions.\n"
    "- No headings, no list, no preamble.\n\n"
    "THE RECORD:\n")


# ---------------------------------------------------------------------------
# The week
# ---------------------------------------------------------------------------
def saturday_before(day: dt.date) -> dt.date:
    """The Saturday on or before `day` -- the eve of the Sunday session."""
    return day - dt.timedelta(days=(day.weekday() - 5) % 7)


def week_window(saturday: dt.date) -> tuple[str, str]:
    """(start, end] as dates: the seven days ending that Saturday."""
    return (saturday - dt.timedelta(days=7)).isoformat(), saturday.isoformat()


def landed(row: dict) -> str:
    """When the miss's outcome landed: the resolution, or the grade."""
    h = _j(row.get("happened_json")) or {}
    return str(h.get("resolved_at") or h.get("graded_at") or row.get("recorded_at") or "")


def _j(v: Any) -> Any:
    if v is None:
        return None
    if not isinstance(v, str):
        return v
    try:
        return json.loads(v)
    except ValueError:
        return None


def of_week(rows: list[dict], saturday: dt.date) -> list[dict]:
    lo, hi = week_window(saturday)
    return [r for r in rows if lo < landed(r)[:10] <= hi]


# ---------------------------------------------------------------------------
# The decision it fed (read-only)
# ---------------------------------------------------------------------------
DECISION_FIELDS = ("id", "book", "instrument", "direction", "horizon", "status",
                   "operator_action", "decision_time", "thesis", "invalidation",
                   "falsifiers", "counter_thesis", "setup_id")


def decision_of(row: dict, db: Optional[str]) -> Optional[dict]:
    if row.get("kind") != "decision" or not db or not Path(db).exists():
        return None
    did = str(row["ref_id"]).split("|", 1)[0]
    conn = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(decisions)")}
        if not cols:
            return None
        got = conn.execute(
            f"SELECT {', '.join(c for c in DECISION_FIELDS if c in cols)} "
            f"FROM decisions WHERE id = ?", (did,)).fetchone()
        return dict(got) if got else {"id": did}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# The file
# ---------------------------------------------------------------------------
def _v(x: Any) -> str:
    if x is None or x == "":
        return "not recorded"
    if isinstance(x, (list, dict)):
        return json.dumps(x, sort_keys=True, default=str)
    return str(x)


def _inputs(v: Any) -> str:
    xs = _j(v)
    if xs is None:
        return "not recorded"
    return ", ".join(str(x) for x in xs) if xs else "none recorded missing"


def build(row: dict, decision: Optional[dict] = None,
          saturday: Optional[dt.date] = None) -> str:
    """The post-mortem's Markdown, from the corpus row (and the decision it fed)
    alone. Pure: the same rows give the same file."""
    said = _j(row.get("said_json")) or {}
    happened = _j(row.get("happened_json")) or {}
    out = [f"# Post-mortem {row['corpus_id']}", "",
           f"Code-built ({METHOD}) from the error corpus row `{row['corpus_id']}` "
           f"({row['kind']}, source `{row['source']}`)"
           + (f", for the session of the Sunday after {saturday.isoformat()}"
              if saturday else "") + ". Nothing below is a model's; nothing below "
           "names a cause. The operator's answers are the cause field.", "",
           "## 1. What was said", ""]
    out += [f"- **{k}:** {_v(said.get(k))}" for k in sorted(said)]
    out += ["", "## 2. What happened", ""]
    out += [f"- **{k}:** {_v(happened.get(k))}" for k in sorted(happened)]
    out += [f"- **margin:** {row['margin']} ({row['margin_unit']})", "",
            "## 3. What was missing at emission", "",
            f"- **the source's missing inputs:** {_inputs(row.get('missing_inputs'))}",
            f"- **the object's absent dimensions:** {_inputs(row.get('absent_dimensions'))}",
            f"- **the object's awaiting legs:** {_inputs(row.get('awaiting_legs'))}",
            f"- **the object read:** {_v(row.get('object_session'))}", "",
            "## 4. The decision it fed", ""]
    if decision:
        out += [f"- **{k}:** {_v(decision.get(k))}" for k in DECISION_FIELDS
                if k in decision]
    else:
        out.append("- none recorded (the probability ledger records no link to a "
                   "decision)" if row.get("kind") == "probability"
                   else "- the decision is not in the register read")
    out += ["", "## The operator's stamp (Doctrine 9.2; blank until the Sunday session)",
            "", "Answer each yes or no. The categories are the remedies.", "",
            "| Field | Question | Answer |", "|---|---|---|"]
    out += [f"| {k} | {q} | |" for k, q in QUESTIONS + (SEVENTH, NOTE)]
    return "\n".join(out) + "\n"


def blank_fields(md: str) -> list[str]:
    """The stamp's fields still blank, by key (the gate's reading)."""
    keys = [k for k, _ in QUESTIONS + (SEVENTH, NOTE)]
    out = []
    for line in md.splitlines():
        m = re.match(r"^\| (\w+) \| .* \| *\|$", line)
        if m and m.group(1) in keys:
            out.append(m.group(1))
    return out


# ---------------------------------------------------------------------------
# The shortening (off by default)
# ---------------------------------------------------------------------------
def check_short(text: str, row: dict, decision: Optional[dict] = None) -> list[str]:
    """Why a shortening is refused; empty: it may print. A cause, or a figure
    the file's own rows do not hold."""
    out = []
    m = CAUSE_WORDS.search(text or "")
    if m:
        out.append(f"names a cause ({m.group(0).strip()!r})")
    from . import numeral_audit                                 # noqa: PLC0415
    payload = {"row": {k: v for k, v in row.items() if not k.endswith("_json")},
               "said": _j(row.get("said_json")), "happened": _j(row.get("happened_json")),
               "decision": decision}
    res = numeral_audit.audit(text or "", payload)
    if not res.passed:
        out.append("a figure the record does not hold: "
                   + ", ".join(str(getattr(f, "text", f)) for f in res.unmatched))
    return out


def shorten(md: str, row: dict, decision: Optional[dict] = None,
            call: Optional[Callable[[str], str]] = None,
            db: Optional[str] = None) -> tuple[Optional[str], str]:
    """(the paragraph, "") or (None, why). `call(prompt) -> text` is the gate's
    fake; by default one metered call with the narrative step's model."""
    prompt = SHORTEN_PROMPT + md.split("## The operator's stamp")[0]
    try:
        if call is None:
            from . import model_meter                           # noqa: PLC0415
            from daily_cascade.narrative import DEFAULT_MODEL   # noqa: PLC0415
            cl, why = model_meter.client()
            if cl is None:
                return None, why
            with model_meter.scope(report="postmortem", section="shorten", db_path=db):
                resp = model_meter.create(cl, model=DEFAULT_MODEL, max_tokens=400,
                                          messages=[{"role": "user", "content": prompt}])
            text = "".join(getattr(b, "text", "") for b in resp.content).strip()
        else:
            text = call(prompt).strip()
    except Exception as exc:                                    # noqa: BLE001
        return None, f"the call failed ({type(exc).__name__})"
    faults = check_short(text, row, decision)
    if faults:
        return None, "; ".join(faults)
    return text, ""


def with_short(md: str, short: Optional[str], why: str) -> str:
    head, sep, stamp = md.partition("## The operator's stamp")
    if short:
        block = ("## Shortened (a model's paragraph of parts 1-3: no cause, every "
                 "figure audited against the rows above)\n\n" + short + "\n\n")
    else:
        block = f"## Shortened\n\nWithheld: {why}. The parts above stand alone.\n\n"
    return head + block + sep + stamp


# ---------------------------------------------------------------------------
# The week's run
# ---------------------------------------------------------------------------
def out_dir(saturday: dt.date, root: Optional[Path] = None) -> Path:
    return Path(root or REPO) / SUBDIR / saturday.isoformat()


def run_week(saturday: Optional[dt.date] = None, db: Optional[str] = None,
             root: Optional[Path] = None, dry_run: bool = False,
             shorten_on: bool = False, call=None, corpus: Optional[list[dict]] = None
             ) -> dict:
    """One file per graded miss of the week. Never rewrites a file."""
    from . import error_corpus, session                         # noqa: PLC0415
    if saturday is None:
        saturday = saturday_before(dt.date.fromisoformat(session.utc_iso()[:10]))
    rows = of_week(error_corpus.rows(db) if corpus is None else corpus, saturday)
    d = out_dir(saturday, root)
    out = {"saturday": saturday.isoformat(), "dir": str(d), "misses": len(rows),
           "written": [], "kept": [], "withheld": {}, "dry_run": dry_run}
    for r in rows:
        p = d / f"{r['corpus_id']}.md"
        if p.exists():
            out["kept"].append(p.name)
            continue
        dec = decision_of(r, db)
        md = build(r, dec, saturday)
        if shorten_on:
            short, why = shorten(md, r, dec, call, db)
            md = with_short(md, short, why)
            if why:
                out["withheld"][p.name] = why
        if not dry_run:
            d.mkdir(parents=True, exist_ok=True)
            p.write_text(md, encoding="utf-8", newline="\n")
        out["written"].append(p.name)
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.postmortem")
    ap.add_argument("what", choices=("week",))
    ap.add_argument("--saturday", help="the Saturday the week ends on (default: the "
                                       "Saturday on or before today, UTC)")
    ap.add_argument("--db")
    ap.add_argument("--out-root", help="the directory docs/postmortems/ sits under "
                                       "(default: the checkout)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--shorten", action="store_true",
                    help="one metered model call per file; off by default")
    a = ap.parse_args(argv)
    sat = dt.date.fromisoformat(a.saturday) if a.saturday else None
    if sat is not None and sat.weekday() != 5:
        ap.error(f"{a.saturday} is not a Saturday")
    res = run_week(sat, a.db, Path(a.out_root) if a.out_root else None,
                   dry_run=a.dry_run, shorten_on=a.shorten)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

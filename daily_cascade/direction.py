"""
THE DIRECTION AUDIT (W-1.1a item 3, the Weekly dry run of 12 Oct 2026).

    from daily_cascade import direction
    moves = direction.edition_moves(ed, "plumbing")   # {name: (value, display)}
    direction.faults(text, moves)                     # [] or one fault line

The numeral audit asks whether every figure exists; it cannot ask whether the
word beside it points the right way. The 12 Oct dry run's Plumbing wrote "even
as the dollar softened, with EUR/USD down -0.43%" in a week the DXY rose +0.27%
-- and EUR/USD down is the dollar FIRMER. Every figure was true; the sentence was
false. This check sits beside the numeral audit and withholds the same way:

    direction audit failed on 1 clause: 'the dollar softened' against DXY +0.27%

THE RULE, PER CLAUSE (a sentence split at commas, semicolons, colons, dashes and
"while"):

  A CURRENCY'S DIRECTION. A directional word within a few words of a currency
    ("the dollar softened", "a firmer dollar") is read against that currency's
    own index where the section prints one (the dollar's is the DXY), else
    against a pair it is quoted in, through metrics_registry.yaml's
    `quote_conventions`: EUR/USD up is the euro firmer and the dollar softer,
    USD/JPY up the dollar firmer and the yen weaker.
  A FIGURE'S DIRECTION. Otherwise, for every cited figure that is a signed
    change the section's tables carry, the nearest directional word in the same
    clause must agree with its sign -- "fell" with a fall, "widened" with a
    spread's rise, "steepened" with a curve's. A figure after "to" or "at" is a
    level, not a change, and is not read.

A clause with no directional word is not checked. The lexicon is config
(config/direction_lexicon.yaml); the sign conventions are the registry's.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
LEXICON_PATH = REPO / "config" / "direction_lexicon.yaml"
_LEX: Optional[dict] = None
_CONV: Optional[dict] = None


def lexicon() -> dict:
    global _LEX
    if _LEX is None:
        _LEX = yaml.safe_load(LEXICON_PATH.read_text(encoding="utf-8")) or {}
    return _LEX


def conventions() -> dict:
    """{alias, lower case: {pair, base, quote, rises}} from the registry."""
    global _CONV
    if _CONV is None:
        reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(
            encoding="utf-8")) or {}
        _CONV = {}
        for key, qc in (reg.get("quote_conventions") or {}).items():
            for a in [qc.get("pair")] + list(qc.get("aliases") or []):
                if a:
                    _CONV[str(a).lower()] = {**qc, "key": key}
    return _CONV


_CLAUSE = re.compile(r"[;:,—–]|\s-\s|\s+(?:while|whereas)\s+", re.I)
_SENT = re.compile(r"(?<=[.!?])\s+")
_NUM = re.compile(r"(?<![\w.])(?P<sign>[+\-−]?)(?P<num>\d[\d,]*(?:\.\d+)?)\s?"
                  r"(?P<unit>%|bps?\b|pts\b|points\b)?")


def _words(lex: dict) -> dict[str, int]:
    out = {str(w).lower(): 1 for w in lex.get("up") or []}
    out.update({str(w).lower(): -1 for w in lex.get("down") or []})
    return out


def _mask(text: str) -> str:
    """Names that carry digits ("the 10-year", "2s10s", "S&P 500", "60-40") as
    spaces of the same length, so a position still points into the text."""
    from .readability import _NOT_FIGURES                       # noqa: PLC0415
    for rx in _NOT_FIGURES:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


def _forms(name: str) -> list[str]:
    forms = {name, name.split(" (")[0]}
    if name.startswith("CFTC "):
        forms.add(name[5:])
    return [f.strip() for f in forms if len(f.strip()) > 1]


def _named(clause: str, moves: dict) -> list[str]:
    low = clause.lower()
    hits = []
    for name in moves:
        for f in _forms(name):
            if re.search(rf"(?<![\w/-]){re.escape(f.lower())}(?![\w/-])", low):
                hits.append(name)
                break
    return hits


def _parse(display) -> Optional[tuple[float, str]]:
    from .figure_budget import parse_figure                     # noqa: PLC0415
    got = parse_figure(display)
    if not got:
        return None
    return got[0], {"pts": "pts", "points": "pts", "bps": "bp"}.get(got[1], got[1])


def _sign(v: float) -> int:
    return (v > 0) - (v < 0)


def edition_moves(ed: dict, sid: Optional[str] = None,
                  column: Optional[str] = "Week") -> dict:
    """{series name: (signed value, display, unit)} -- every change the section
    `sid` prints (every section's for The read, or `sid` None), from its tables
    the way the figure budget reads them."""
    from . import figure_budget as fb                           # noqa: PLC0415
    out: dict = {}
    for s in ed.get("sections") or []:
        if sid not in (None, "read") and s.get("id") != sid:
            continue
        for m in fb.section_moves(s, column):
            if m.get("kind") != "move" or m.get("change") is None:
                continue
            got = _parse(m["change"])
            if got:
                out.setdefault(m["name"], (got[0], str(m["change"]), got[1]))
    return out


def _currency_at(tokens: list, i: int, window: int, cur: dict) -> Optional[str]:
    lo, hi = max(0, i - window), min(len(tokens), i + window + 1)
    near = " ".join(t for t, _ in tokens[lo:hi]).lower()
    for c, spec in cur.items():
        for w in spec.get("words") or []:
            if re.search(rf"(?<![\w/]){re.escape(str(w).lower())}(?![\w/])", near):
                return c
    return None


def _currency_actual(c: str, clause: str, moves: dict, cur: dict
                     ) -> Optional[tuple[int, str]]:
    """The currency's direction on the period and what says so: its own index
    if the section prints one, else a pair it is quoted in (the one the clause
    names first)."""
    idx = [str(x).lower() for x in (cur.get(c) or {}).get("index") or []]
    for name, (v, disp, _) in moves.items():
        if any(f.lower() in idx for f in _forms(name)):
            return _sign(v), f"{name.split(' (')[0]} {disp}"
    conv = conventions()
    pairs = []
    for name, (v, disp, _) in moves.items():
        qc = next((conv[f.lower()] for f in _forms(name) if f.lower() in conv), None)
        if qc and c in (qc.get("base"), qc.get("quote")) and qc.get("quote") != "basket":
            first = clause.lower().find(qc["pair"].lower())
            pairs.append((first if first >= 0 else 10 ** 6, name, v, disp, qc))
    if not pairs:
        return None
    _, name, v, disp, qc = min(pairs, key=lambda x: x[0])
    rises = qc.get(qc.get("rises") or "base")
    d = _sign(v) if c == rises else -_sign(v)
    return d, f"{name.split(' (')[0]} {disp}"


def clause_faults(clause: str, moves: dict) -> list[str]:
    lex = lexicon()
    words = _words(lex)
    cur = lex.get("currencies") or {}
    window = int(lex.get("subject_window_words") or 3)
    tokens = [(m.group(0), m.start()) for m in re.finditer(r"[A-Za-z/][\w/'-]*", clause)]
    dirs = []
    for i, (t, at) in enumerate(tokens):
        d = words.get(t.lower())
        if d is None:
            continue
        nxt = tokens[i + 1][0].lower() if i + 1 < len(tokens) else ""
        if t.lower() == "up" and nxt == "front":
            continue
        dirs.append((i, at, t, d))
    if not dirs:
        return []
    out = []
    masked = _mask(clause)
    figs = [m for m in _NUM.finditer(masked)
            if not re.search(r"\b(?:to|at)\s*$", masked[:m.start()], re.I)]
    named = _named(clause, moves)
    for i, at, word, d in dirs:
        c = _currency_at(tokens, i, window, cur)
        if c:
            actual = _currency_actual(c, clause, moves, cur)
            if actual and actual[0] and actual[0] != d:
                out.append(f"'{_phrase(clause, tokens, i, c, cur)}' against "
                           f"{actual[1]}")
            continue
        if not figs:
            continue
        f = min(figs, key=lambda m: abs(m.start() - at))
        sign = _figure_sign(f, named, moves)
        if sign and sign != d:
            out.append(f"'{clause.strip()[:80]}': '{word}' with a "
                       f"{'rise' if sign > 0 else 'fall'}")
    return out


def _phrase(clause: str, tokens: list, i: int, c: str, cur: dict) -> str:
    """The currency and its word as the clause writes them: "the dollar
    softened", "a firmer dollar"."""
    ws = [str(w).lower() for w in cur[c].get("words") or [] if " " not in str(w)]
    j = next((k for k in range(len(tokens)) if tokens[k][0].lower() in ws), i)
    a, b = min(i, j), max(i, j)
    start = tokens[a][1]
    if a > 0 and tokens[a - 1][0].lower() in ("the", "a", "an"):
        start = tokens[a - 1][1]
    end = tokens[b][1] + len(tokens[b][0])
    return clause[start:end]


def _figure_sign(m: "re.Match", named: list, moves: dict) -> int:
    """The sign of a cited change: the prose's own, where it wrote one, for a
    figure the section prints as a change; else the change's in the tables.
    0 when the figure is not a change the section carries."""
    num = float(m.group("num").replace(",", ""))
    dec = len(m.group("num").split(".", 1)[1]) if "." in m.group("num") else 0
    tol = 0.5 * 10 ** -dec + 1e-9
    unit = {"bps": "bp", "points": "pts"}.get((m.group("unit") or "").lower(),
                                              (m.group("unit") or "").lower())
    cands = [(n, v) for n, (v, _, u) in moves.items()
             if abs(abs(v) - num) <= tol and (not unit or not u or u == unit)]
    if not cands:
        return 0
    written = m.group("sign")
    if written in ("+", "-", "−"):
        return 1 if written == "+" else -1
    pref = [v for n, v in cands if n in named] or [v for _, v in cands]
    signs = {_sign(v) for v in pref}
    return signs.pop() if len(signs) == 1 else 0


def faults(text: str, moves: dict) -> list[str]:
    """The direction audit over a paragraph: [] or one fault line naming every
    clause that fails."""
    bad = []
    for sent in _SENT.split(text or ""):
        for clause in _CLAUSE.split(sent):
            if clause and clause.strip():
                bad += clause_faults(clause, moves)
    if not bad:
        return []
    return [f"direction audit failed on {len(bad)} clause"
            f"{'' if len(bad) == 1 else 's'}: " + "; ".join(bad)]

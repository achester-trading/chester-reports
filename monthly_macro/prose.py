"""
Monthly v2: the prose, one audited model call per section. (Ari's revision, 1 Oct)

    The month in markets          3-4 paragraphs on what drove the month
    Looking back, one per theme   2-4 paragraphs each, six themes
    Looking ahead                 2-4 paragraphs
    Where our read lands          2-3 paragraphs, bounded to weights and books

WHY ONE CALL PER SECTION. The single paragraph over the whole payload read as a
summary of a summary: too abridged, insight hard to find, no account of where the
market went. A section's call sees ONLY that section's slice -- the opening sees
the scorecard and what changed; a theme sees its own items, its dimensions and its
scorecard rows -- so the model writes about the thing in front of it, at the length
it needs, and a failure costs that section alone.

THE AUDITS ARE THE CLOSE REPORT'S, per section. Every call goes through
daily_cascade.narrative.generate(): print precision, the precomputed percentile
ordinals, the numeral and label audit against THAT SECTION'S slice, the state audit
against the object, markdown refused. A section that fails is WITHHELD WITH ITS
REASON; the sections beside it publish.

THE SHAPE IS INSTITUTIONAL DESK COMMENTARY, insight first: each paragraph opens
with the claim, gives the evidence with numbers, and ends with what it implies for
positioning -- stated as what the evidence favours or argues against, never as an
instruction. The style reference is docs/briefs/monthly-style-reference.md when it
exists; until then the Monthly template carries the rules.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable, Optional

from altdata import observations, session

from .narrative import TEMPLATE_PATH

log = logging.getLogger("monthly_macro.prose")

REPO = Path(__file__).resolve().parent.parent
STYLE_REFERENCE = REPO / "docs" / "briefs" / "monthly-style-reference.md"

# 2-4 paragraphs of desk commentary run 250-600 words; this is the runaway guard,
# not a target. The opening asks for 3-4.
SECTION_MAX_CHARS = 5200

SECTION_RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH, CLOSE-REPORT FRAMING ABOVE. You are writing ONE \
SECTION of the Monthly Regime & Allocation report, in the register of institutional \
desk commentary: a senior strategist's monthly note to a portfolio manager. Every \
other rule above -- every figure from the payload, signs as numerals, percentiles \
copied from their _ordinal field, no recommendation -- still holds.

THE SECTION: {title}. {scope}

SHAPE. Write {paragraphs} paragraphs of continuous prose, separated by one blank \
line. No headings, no bullet points, no numbered lists, no bold, no tables -- the \
tables are printed beside your text. Each paragraph is INSIGHT FIRST:
  1. open with the claim -- the one thing this paragraph says about the month;
  2. give the evidence, with the numbers from the payload that carry it;
  3. end with the implication for positioning: what the evidence favours, what it \
argues against, which risk it raises or lowers. State it as an observation about \
exposures, NEVER as an instruction -- buy, sell, add, trim, hold, overweight, \
underweight and their synonyms remain forbidden.

THE HORIZON IS THE MONTH named in the payload. The regime is the object's: name \
what the dials and dimensions read, never infer a regime of your own. Say plainly \
where the payload says something is not sourced; do not fill a gap with knowledge \
from outside the payload. Do not cite event, claim or row ids.

WRITE ABOUT MARKETS, NEVER ABOUT THE SYSTEM. The reader has no idea how this \
report is built and must never need to. Do not use these words at all: payload, \
object, dimension, dial, field, row, scorecard, slice, store, registry, tracked \
series, not_sourced, "the system", "the data". Say "our read on credit", "our \
macro regime read", "the table below", "the month's moves". A missing input is \
either left out or said ONCE, in plain words ("we don't yet track rate-cut \
odds") -- the footnote under your text lists every gap, so you never need to.

DO NO ARITHMETIC OF YOUR OWN. Quote each move exactly as the payload gives it. \
Never compute a difference, a spread between two moves, a ratio, a sum or a \
relative performance ("the Russell lagged by 4.36%") -- that number is in no \
field, and one such figure withholds the whole section. Say "lagged" and give \
both moves instead.
"""


def _style_guide() -> Path:
    return STYLE_REFERENCE if STYLE_REFERENCE.exists() else TEMPLATE_PATH


def system_prompt(title: str, scope: str, paragraphs: str = "2 to 4") -> str:
    from daily_cascade import narrative as base
    return base.SYSTEM_PROMPT + SECTION_RULES.format(
        title=title, scope=scope, paragraphs=paragraphs)


# ---------------------------------------------------------------------------
# The slices -- each section sees everything the store holds for it, under
# PLAIN-LANGUAGE KEYS: a key name is a word the model will borrow, so the keys
# say "our_reads" and "series", never "dimensions" or "rows".
# ---------------------------------------------------------------------------
def _reads(p: dict, names: Optional[list] = None) -> list[dict]:
    """Our regime reads for these areas: the state, last month's, its percentile."""
    return [{"area": d.get("dimension"), "our_read": d.get("state"),
             "last_month": d.get("previous_state"),
             "read_changed": d.get("changed"), "percentile": d.get("percentile"),
             "not_available_because": d.get("absent_reason")}
            for d in ((p.get("regime") or {}).get("dimensions") or [])
            if names is None or d.get("dimension") in names]


def _regime(p: dict) -> list[dict]:
    return [{"regime": d.get("dial"), "our_read": d.get("state"),
             "last_month": d.get("previous_state"), "read_changed": d.get("changed")}
            for d in ((p.get("regime") or {}).get("dials") or [])]


def _move_row(r: dict) -> dict:
    """One scorecard move, its fields named for what they ARE.

    A yield or a spread is QUOTED in percent and MOVES in basis points, so its
    levels travel as `*_level_pct` and its move as `change_bps`; a price's levels
    are `*_level` and its move `change_pct`. The audit types a field by its name,
    and "the 10-year rose to 5.24%" was withheld when 5.24 travelled as
    `end_level` -- a price -- in the first per-section dry run.
    """
    # THE PERCENTILE IS THE LEVEL'S, over five years -- not the move's. Named so,
    # because the first per-section opening called the S&P 500's 99th "the 99th
    # percentile of moves", a mislabel no numeral audit can see.
    out = {"market": r.get("label"), "level_percentile_5y": r.get("percentile")}
    if r.get("change_unit") == "bps":
        out.update(start_level_pct=r.get("start_level"),
                   end_level_pct=r.get("end_level"), change_bps=r.get("change"))
    elif r.get("change_unit") == "percent":
        out.update(start_level=r.get("start_level"), end_level=r.get("end_level"),
                   change_pct=r.get("change"))
    else:
        out.update(start_level=r.get("start_level"), end_level=r.get("end_level"),
                   change=r.get("change"))
    return out


def _moves(p: dict, ids: Optional[list] = None) -> dict:
    m = p.get("month_in_markets") or {}
    return {"month": m.get("month"), "from": m.get("start"), "to": m.get("end"),
            "moves": [_move_row(r) for r in m.get("rows") or []
                      if ids is None or r.get("id") in ids]}


def _series(rows: list[dict]) -> list[dict]:
    """Every series a section sees, plainly keyed (the metric id stays out)."""
    keep = ("latest_level", "latest_pct", "latest_date", "since", "change_pct",
            "change_bps", "change", "level_percentile_5y")
    return [{"series": r.get("label"), **{k: r[k] for k in keep if k in r}}
            for r in rows]


def _changed(p: dict, words: Optional[list] = None) -> list[dict]:
    rows = ((p.get("looking_back") or {}).get("what_changed") or {}).get("rows") or []
    return [{"what_changed": r.get("what"), "from": r.get("from"), "to": r.get("to")}
            for r in rows
            if words is None or any(w in r.get("what", "") for w in words)]


def _stories(p: dict) -> list[dict]:
    lb = p.get("looking_back") or {}
    return [{"story": i.get("text"), "status": i.get("state"),
             "major_outlet_headlines_this_month": i.get("tier12_in_window")}
            for t in lb.get("themes") or [] for i in t.get("items") or []
            if i.get("kind") == "story"]


def opening_slice(p: dict) -> dict:
    lb = p.get("looking_back") or {}
    releases = [{"release": i["text"],
                 "date": (i.get("sources") or [{}])[0].get("date")}
                for t in lb.get("themes") or [] for i in t.get("items") or []
                if i.get("kind") == "release"]
    return {"the_month": _moves(p), "our_regime_reads": _regime(p),
            "our_reads_by_area": _reads(p),
            "what_changed_since_last_month": _changed(p),
            "releases_this_month": releases, "stories": _stories(p)}


def takeaways_slice(p: dict) -> dict:
    takes = (p.get("month_in_one_page") or {}).get("takeaways") or []
    return {"facts_to_build_from": [t.get("text") for t in takes],
            "the_month": _moves(p), "our_regime_reads": _regime(p),
            "what_changed_since_last_month": _changed(p)}


def theme_slice(p: dict, theme: dict) -> dict:
    from . import v2
    cfg = (v2.load_themes().get("themes") or {}).get(theme["theme"]) or {}
    return {"theme": theme["name"],
            "month": (p.get("month_in_markets") or {}).get("month"),
            "our_reads": _reads(p, theme.get("dimensions") or []),
            "series": _series(theme.get("rows") or []),
            "moves": _moves(p, cfg.get("scorecard"))["moves"],
            "fed_calendar": theme.get("fed_calendar"),
            "developments": [{"kind": i.get("kind"), "development": i.get("text"),
                              "date": (i.get("sources") or [{}])[0].get("date"),
                              "major_outlet_headlines":
                                  i.get("tier12_in_window")}
                             for i in theme.get("items") or []],
            "what_changed_since_last_month": _changed(
                p, (theme.get("dimensions") or []) + (theme.get("stories") or [])),
            "we_do_not_yet_track": theme.get("not_yet_tracked") or []}


def ahead_slice(p: dict) -> dict:
    la = p.get("looking_ahead") or {}
    return {"calendar_by_period": [{"period": w["name"],
                                    "events": [{"date": c["date"],
                                                "event": c["title"]}
                                               for c in w["calendar"]]}
                                   for w in la.get("windows") or []],
            "scenarios": [{"claim": s.get("claim"),
                           "probability": s.get("probability"),
                           "brier": s.get("brier"), "resolves": s.get("resolve_by"),
                           "would_change_our_mind": [sp.get("observable")
                                                     for sp in s.get("signposts")
                                                     or []]}
                          for s in la.get("scenarios") or []],
            "our_regime_reads": _regime(p),
            "not_yet_on_our_calendar": la.get("not_yet_tracked") or []}


def our_read_slice(p: dict) -> dict:
    r = p.get("our_read") or {}
    la = p.get("looking_ahead") or {}
    return {"what_we_hold": r.get("paragraph"),
            "live_weights": [{"claim": s.get("claim"),
                              "probability": s.get("probability"),
                              "resolves": s.get("resolve_by")}
                             for s in la.get("scenarios") or []],
            "active_positions": r.get("active_decisions"),
            "books_against_benchmark": ((p.get("register_month") or {})
                                        .get("books_vs_benchmark") or {})
            .get("line"),
            "our_regime_reads": _regime(p)}


def pillar_slice(p: dict, num: str, pillar: dict) -> dict:
    """One appendix pillar: its series over the month, plainly labelled."""
    from . import v2
    cutoff = str(p.get("as_of") or session.utc_iso())
    _, month_end = v2.month_bounds(p)
    rows, gaps = [], []
    with observations.ObservationStore() as st:
        for r in pillar.get("series") or []:
            m = v2.metric_month(st, {"metric": r["metric"],
                                     "label": r.get("description") or r["metric"]},
                                cutoff, month_end)
            if m["state"] == "ok":
                rows.append(m)
            else:
                gaps.append(m["label"] + (f" (latest print {m['last_print']})"
                                          if m.get("last_print") else ""))
    return {"pillar": pillar.get("name"), "feeds_regime": pillar.get("dial"),
            "series": _series(rows), "we_do_not_yet_track": gaps,
            "month": (p.get("month_in_markets") or {}).get("month")}


def plan(p: dict) -> list[dict]:
    """Every section's call: its key, title, scope, paragraph count and slice."""
    out = [{"key": "month_in_markets", "title": "The month in markets",
            "scope": "What drove the month across asset classes: lead with the "
                     "biggest moves and what explains them, then what our regime "
                     "reads and the month's releases add.",
            "paragraphs": "3 to 4", "slice": opening_slice(p)},
           {"key": "month_in_one_page", "title": "The month in one page",
            "scope": "Five takeaways for a reader with no context. Each takeaway "
                     "is ONE short paragraph whose first sentence is a plain-English "
                     "headline, followed by what is happening, why it matters, and "
                     "what it means for positioning. Build them from the facts "
                     "given; one takeaway per paragraph, in order of importance.",
            "paragraphs": "exactly 5", "slice": takeaways_slice(p)}]
    for t in ((p.get("looking_back") or {}).get("themes") or []):
        out.append({"key": f"theme:{t['theme']}", "title": t["name"],
                    "scope": "This theme over the month, so that a reader with no "
                             "context understands it: what happened in its markets "
                             "and series, why, and what it means. Use the series "
                             "given, with their dates.",
                    "paragraphs": "2 to 4", "slice": theme_slice(p, t)})
    out.append({"key": "looking_ahead", "title": "Looking ahead, 2-3 months",
                "scope": "What the calendar tests next, period by period (the "
                         "first period, then the two months after it), and what "
                         "the scenario weights say, with what would change our "
                         "mind for each.",
                "paragraphs": "2 to 4", "slice": ahead_slice(p)})
    out.append({"key": "our_read", "title": "Where our read lands",
                "scope": "Our position against consensus, stated ONLY through the "
                         "weights and the positions given. Restate nothing they do "
                         "not already hold; if they hold little, say so.",
                "paragraphs": "2 to 3", "slice": our_read_slice(p)})
    ap = (p.get("appendix") or {}).get("pillars") or {}
    for num, pillar in sorted(ap.items(), key=lambda kv: int(kv[0])):
        out.append({"key": f"pillar:{num}", "title": f"Pillar: {pillar.get('name')}",
                    "scope": "ONE long paragraph: what this pillar measures, in "
                             "plain terms a newcomer understands; how its series "
                             "moved over the month, with the numbers; and what to "
                             "watch next month.",
                    "paragraphs": "exactly 1", "slice": pillar_slice(p, num, pillar)})
    return out


def _market_states(p: dict) -> Optional[dict]:
    """The object's states, for the state audit. None if unreadable."""
    try:
        import regime
        from daily_cascade import story_block
        obj = regime.latest(session_day=(p.get("regime") or {}).get("session"))
        return story_block.market_states(obj) if obj else None
    except Exception:                                          # noqa: BLE001
        return None


# NEVER WRITE ABOUT THE SYSTEM (Ari's second round). Internal vocabulary in a
# reader's prose -- "the payload", "the object", "the dimension", "not_sourced" --
# is the report describing its own plumbing. A section using any of these is
# withheld like a failed audit. Whole words, case-insensitive; "fielded" or
# "objective" do not match, "field" and "object" do.
BANNED_TERMS = (r"payloads?", r"objects?", r"dimensions?", r"dials?", r"fields?",
                r"scorecard rows?", r"rows?", r"slices?", r"registry",
                r"not_sourced", r"not[ _-]sourced", r"absent_reason",
                r"the system", r"tracked series", r"the data the system tracks",
                r"in the store", r"the store", r"market[- ]state", r"tier-?[123]",
                r"_ordinal", r"_signed")
_BANNED = re.compile(r"(?<![\w-])(" + "|".join(BANNED_TERMS) + r")(?![\w-])", re.I)


def internal_terms(text: Optional[str]) -> list[str]:
    return sorted({m.group(0).lower() for m in _BANNED.finditer(text or "")})


# NO BULLET FRAGMENTS IN A NARRATIVE SECTION. The brief asks for prose; a reply
# that lists is withheld like any other failed audit rather than re-flowed.
_LIST_LINE = re.compile(r"^\s*(?:[-*•–]\s|\d+[.)]\s|#+\s)", re.M)


def list_lines(text: Optional[str]) -> list[str]:
    return [m.group(0).strip() for m in _LIST_LINE.finditer(text or "")]


def words(text: Optional[str]) -> int:
    return len(re.findall(r"\b[\w'.%$-]+\b", text or ""))


def write_all(p: dict, *, model: Optional[str] = None, client=None,
              only: Optional[Callable[[dict], bool]] = None) -> dict:
    """{section key: result}, one audited call each. Never raises."""
    from daily_cascade import narrative as base
    states = _market_states(p)
    out: dict[str, dict] = {}
    for sec in plan(p):
        if only and not only(sec):
            continue
        try:
            r = base.generate(sec["slice"], model=model, client=client,
                              system_prompt=system_prompt(sec["title"], sec["scope"],
                                                          sec["paragraphs"]),
                              guide_path=_style_guide(),
                              max_chars=SECTION_MAX_CHARS, one_paragraph=False,
                              citable_ids=[], market_states=states)
            published, state = bool(r.published), r.state
            reason = None if published else (r.withheld_note() or r.reason)
            lists = list_lines(r.text) if published else []
            jargon = internal_terms(r.text) if published else []
            if jargon:
                published, state = False, "internal_vocabulary"
                reason = (f"narrative withheld: it writes about the system "
                          f"({', '.join(jargon)}) -- a reader's prose names markets, "
                          f"not the report's plumbing")
            elif lists:
                published, state = False, "list_fragments"
                reason = (f"narrative withheld: the section came back as list "
                          f"fragments ({len(lists)} list line(s)), and a narrative "
                          f"section is prose")
            out[sec["key"]] = {
                "title": sec["title"], "state": state, "published": published,
                "text": r.text if published else None, "reason": reason,
                "words": words(r.text) if published else 0,
                # Kept for inspection, never printed: the operator can see what a
                # withheld section said and why the audit stopped it.
                "rejected_text": None if published else (
                    getattr(r, "rejected_text", None) or r.text),
                "model": r.model,
                "figures_checked": getattr(r, "figures_checked", None)}
        except Exception as exc:                               # noqa: BLE001
            out[sec["key"]] = {"title": sec["title"], "state": "fault",
                               "published": False, "text": None, "words": 0,
                               "reason": f"FAULT (code, not data) -- "
                                         f"{type(exc).__name__}: {exc}"}
        log.info("section %s: %s (%s words)", sec["key"], out[sec["key"]]["state"],
                 out[sec["key"]]["words"])
    return out

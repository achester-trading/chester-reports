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
against the object, markdown refused. A section the audit withholds gets ONE
RETRY with the audit's reason fed back (T3, the stacked reports' rule); if that
fails too it is WITHHELD WITH ITS REASON, and the sections beside it publish. A
fault -- the API, a payload past its guard -- is not retried.

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
from daily_cascade import readability

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

WRITE ABOUT MARKETS, NEVER ABOUT THE SYSTEM. This OVERRIDES rule 5 above: do NOT \
end on the system -- end on the market and what the next prints will test. The \
rules above speak in internal terms ("dial", "dimension", "the object", "the \
payload"); those are for you, never for the reader. Translate every time: a \
dimension is "our read on credit" (or rates, liquidity...), a dial is "our macro \
regime read" or "our volatility regime read", the payload is simply "the data". \
The reader has no idea how this report is built and must never need to. Do not use these words at all: payload, \
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

FIGURES. Cite at most {figure_cap} figures in any one paragraph -- the tables carry \
the rest.{ordinals}{display}
"""


def _style_guide() -> Path:
    return STYLE_REFERENCE if STYLE_REFERENCE.exists() else TEMPLATE_PATH


# THE MONTHLY'S FIGURE CAP AND ITS ORDINALS (T3.2 items 1-2, 10 Oct 2026). Every
# Monthly frame states the cap -- the cadence's `paragraph_figures`, 8 -- and that
# the tables carry the rest; the executive summary's frame asks for at most three.
# An ordinal is copied as printed: the tables and the `_ordinal` fields share the
# one half-up rule (numeral_audit.percentile_ordinal), so the two agree.
# The summary's cap is the cadence's `summary_figures` (T3.4: config, not a literal).
def summary_figures() -> int:
    from daily_cascade import cadence as cadence_mod            # noqa: PLC0415
    return cadence_mod.summary_cap(cadence_mod.get("monthly"))


SUMMARY_FIGURES = summary_figures()


def _month_column() -> str:
    from daily_cascade import cadence as cadence_mod            # noqa: PLC0415
    return str(cadence_mod.get("monthly").get("column") or "The month")


# The Monthly's period column head ("The month"): a move is read from it first.
MONTH_COLUMN = _month_column()
# A LARGE FIGURE IS COPIED IN ITS DISPLAY FORM (T3.3 item 2): every level and
# change a pillar or theme hands over in millions or thousands comes with its
# `_display` string, built by the one scaler, and only that string.
DISPLAY_RULE = (" A level or change that carries a latest_level_display or "
                "change_display is written as that string, copied verbatim, sign "
                "and scale included (\"+$23.15bn\", \"200.5 thousand\"; a count "
                "or a small payroll change as its integer with its noun, "
                "\"+42,984 contracts\", \"+29,000 jobs\") -- never as a raw number "
                "and never without its noun: a change of 10,000 or more printed "
                "without its unit, scale or noun withholds the paragraph.")
# THE FRAME RULES OF T3.6 (the Monthly dry run of 13 Oct 2026), on every frame
# that carries the display rule:
#   M1  a figure's ROLE: "closed at" and "the close" bind to a close, never to an
#       average -- the long frame's columns are averages beside the close;
#   M7  a small count in words ("two of the next four meetings"): the numeral
#       audit reads numerals only, so a count in words is exempt by construction
#       and a bare "2" the data does not hold is withheld;
#   M10 two dollar series print in the Monthly (the DXY and the Fed's broad
#       index): name the one cited, never "the dollar" beside a level.
ROLE_RULE = (" Every figure has a role -- a close, an average, a percentile, a "
             "change, a level -- and the words beside it must fit that role: "
             "\"closed at\", \"the close\" and \"ended the month at\" bind ONLY to "
             "a close, never to an average; a 40-week, 10-month or 20-month figure "
             "is an average and is written as one (\"its 40-week average of "
             "...\").")
COUNT_RULE = (" A small count -- of meetings, sessions, markets, gaps -- is written "
              "in words (\"two of the next four meetings\"), never as a bare "
              "numeral.")
DOLLAR_RULE = (" Two dollar series print in this report -- the dollar index (DXY) "
               "and the Fed's broad trade-weighted dollar index: a dollar level or "
               "move names the series it is (\"the dollar index (DXY) at ...\", "
               "\"the Fed's broad dollar index at ...\"), never a bare \"the "
               "dollar\" beside a figure.")
T36_RULES = ROLE_RULE + COUNT_RULE + DOLLAR_RULE
ORDINAL_RULE = (" A percentile ordinal is copied exactly as it is printed -- from "
                "the table, or from its _ordinal field -- never re-rounded from a "
                "decimal: \"the 100th percentile\" stays 100th.")


def figure_cap() -> int:
    """The Monthly's per-paragraph figure cap (cadences.monthly)."""
    from daily_cascade import cadence as cadence_mod            # noqa: PLC0415
    return cadence_mod.figure_cap(cadence_mod.get("monthly"))


def _cap_word(n: Optional[int] = None) -> str:
    from daily_cascade import cadence as cadence_mod            # noqa: PLC0415
    return cadence_mod.figure_word(figure_cap() if n is None else n)


def system_prompt(title: str, scope: str, paragraphs: str = "2 to 4") -> str:
    from daily_cascade import narrative as base
    return base.SYSTEM_PROMPT + SECTION_RULES.format(
        title=title, scope=scope, paragraphs=paragraphs, figure_cap=_cap_word(),
        ordinals=ORDINAL_RULE, display=DISPLAY_RULE + T36_RULES + vocab_frame())


# ---------------------------------------------------------------------------
# The slices -- each section sees everything the store holds for it, under
# PLAIN-LANGUAGE KEYS: a key name is a word the model will borrow, so the keys
# say "our_reads" and "series", never "dimensions" or "rows".
# ---------------------------------------------------------------------------
# THE NAMES THE READER SEES for each read, and the line that tells the two
# volatility reads apart (1 Oct 2026). Every slice carries VOLATILITY_TERMS so the
# model can say both without conflating them; the state audit holds each name
# to its own stored value (daily_cascade.narrative.STATE_ALIASES).
AREA_NAMES = {"volatility": "volatility against its five-year history"}
REGIME_NAMES = {"vol": "volatility regime", "macro": "macro regime",
                "gamma": "dealer gamma"}
VOLATILITY_TERMS = (
    "Two different volatility reads, each with its own name. The volatility "
    "regime bands the VIX's absolute level (normal is 14 to 20). Volatility "
    "against its five-year history places the VIX and realized volatility within "
    "their own last five years (subdued is the bottom third). Both can hold at "
    "once: a VIX ordinary in level but low for recent years. Always use the full "
    "name of the one you mean; never write bare 'volatility is ...'.")


def _reads(p: dict, names: Optional[list] = None) -> list[dict]:
    """Our regime reads for these areas: the state, last month's, its percentile."""
    return [{"area": AREA_NAMES.get(d.get("dimension"), d.get("dimension")),
             "our_read": d.get("state"),
             "last_month": d.get("previous_state"),
             "read_changed": d.get("changed"), "percentile": d.get("percentile"),
             "not_available_because": d.get("absent_reason")}
            for d in ((p.get("regime") or {}).get("dimensions") or [])
            if names is None or d.get("dimension") in names]


def _regime(p: dict) -> list[dict]:
    return [{"regime": REGIME_NAMES.get(d.get("dial"), d.get("dial")),
             "our_read": d.get("state"),
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
    """Every series a section sees, plainly keyed (the metric id stays out).

    WHERE A DISPLAY FORM EXISTS, THE RAW NUMBER IS NOT HANDED OVER (T3.3 item 2):
    the Systemic Liquidity pillar wrote "rose +23,154 to $2.95tn" -- bank
    reserves' change in raw millions, copied from `change` beside the
    `change_display` it should have used. A series with `change_display` (or
    `latest_level_display`) carries only that string for the figure, so the one
    form the writer can copy is the scaled one."""
    keep = ("latest_level", "latest_level_display", "latest_pct", "latest_date",
            "since", "change_pct", "change_bps", "change", "change_display",
            "level_percentile_5y")
    out = []
    for r in rows:
        d = {"series": r.get("label"), **{k: r[k] for k in keep if k in r}}
        if "change_display" in d:
            d.pop("change", None)
        if "latest_level_display" in d:
            d.pop("latest_level", None)
        out.append(d)
    return out


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
                     "given; one takeaway per paragraph, in order of importance. "
                     "Say each thing once: no takeaway restates another.",
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
    for sec in out:
        sec["slice"]["volatility_terms"] = VOLATILITY_TERMS
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
# "The system" alone is NOT banned: "liquidity in the system" is desk language
# for the banking system (the second-round dry run withheld a section over it);
# only the phrases that can mean this report's machinery are.
# PHRASES ABOUT THE REPORT, NOT BARE WORDS (Ari, 1 Oct). The first list banned
# "slice", "row", "field" and "the system's" outright, and the third dry run
# withheld "the system's shock absorber" and "the cyclically-sensitive slice of
# CPI" -- ordinary English. A bare word that markets also use ("three sessions in
# a row", "a playing field", "dial back") is not banned; the phrase that can only
# mean this report's machinery is.
_DIMS = r"(?:growth|inflation|rates|liquidity|credit|trend|breadth|volatility|sentiment)"
BANNED_TERMS = (r"payloads?", r"this payload", r"the object", r"state object",
                r"(?:the|our|its) " + _DIMS + r" dimensions?",
                r"dimension framework", r"(?:vol|macro|gamma|regime) dials?",
                r"the dials?", r"scorecard rows?", r"data rows?",
                r"not_sourced", r"not[ _-]sourced", r"absent_reason",
                r"the system tracks", r"our system", r"this system",
                r"the system's (?:data|reads?|store|payload|object|records?)",
                r"tracked series", r"the data the system tracks",
                r"in the store", r"the store(?! of value)", r"the registry",
                r"market[- ]state", r"tier-?[123](?:/2)?",
                r"_ordinal", r"_signed", r"_display")
_BANNED = re.compile(r"(?<![\w-])(" + "|".join(BANNED_TERMS) + r")(?![\w-])", re.I)


def internal_terms(text: Optional[str]) -> list[str]:
    return sorted({m.group(0).lower() for m in _BANNED.finditer(text or "")})


# THE BANNED LIST, IN THE FRAME (T3.4a, the third box dry run). summary:read and
# summary:slow were withheld three times each over "the object", "tracked series"
# and "extreme:", and stack:priced three times over "venues": the audit named the
# word, but the frame never listed what is banned, so each retry traded one
# banned word for another. Every Monthly frame now carries the list -- these
# words in the reader's form, the stack's banned phrases from
# config/reporting_stack.yaml -- and a retry names the offending word(s) and
# quotes the rule (VOCAB_RETRY).
BANNED_WORDS_READABLE = (
    "payload", "the object", "state object", "our/the/its growth (inflation, "
    "rates, liquidity, credit, trend, breadth, volatility, sentiment) dimension",
    "dimension framework", "vol/macro/gamma/regime dial", "the dials",
    "scorecard rows", "data rows", "not sourced", "absent_reason",
    "the system tracks", "our system", "this system", "the system's data / reads "
    "/ store / records", "tracked series", "in the store", "the store", "the "
    "registry", "market state", "tier 1 / tier 2 / tier 3", "_ordinal",
    "_signed", "_display")
VOCAB_RULE = ("a reader's prose names markets, not the report's plumbing: never "
              "write a word or phrase that names this report's machinery, its "
              "labels or its section titles")
VOCAB_RETRY = 'your draft used {words}; the rule: "{rule}"'


def banned_phrases() -> list[str]:
    """The stack's banned phrases (config/reporting_stack.yaml, style)."""
    try:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        st = bars_mod.load_config().get("style") or {}
    except Exception:                                           # noqa: BLE001
        return []
    return [str(x) for x in st.get("banned_phrases") or []]


def vocab_frame() -> str:
    return (f" WORDS THAT WITHHOLD THE PARAGRAPH -- {VOCAB_RULE}. Never write: "
            + "; ".join(BANNED_WORDS_READABLE) + ". Never write these phrases: "
            + "; ".join(f"'{x}'" for x in banned_phrases())
            + ". Say \"prediction market\", never \"venue\".")


_LABEL = re.compile(r"(?<![\w-])(?:extreme|contradiction|story|scen):[\w.:/-]*")


def reader_slice(sl: dict) -> dict:
    """A summary's prompt slice without the stack's own labels and titles
    (T3.4a): the section and sub-section titles go, and the label prefixes the
    stack prints for its own ids ("extreme:...", "contradiction:...") are struck
    from every string. The figures stay, so the audit's given set is unchanged."""
    def walk(o, depth=0):
        if depth > 12:
            return o
        if isinstance(o, dict):
            return {k: walk(v, depth + 1) for k, v in o.items()
                    if k not in ("section", "title")}
        if isinstance(o, list):
            return [walk(v, depth + 1) for v in o]
        if isinstance(o, str):
            return " ".join(_LABEL.sub("", o).split())
        return o
    return walk(sl)


def vocab_words(jargon: list[str], faults: list[str]) -> list[str]:
    """The offending words: the internal terms, and the tape's banned phrases."""
    out = list(jargon)
    for f in faults:
        m = re.match(r"(?:internal vocabulary: (.+)|banned phrase: '(.+)')$", f)
        if m:
            out.append(m.group(1) or m.group(2))
    return sorted(set(out))


# NO BULLET FRAGMENTS IN A NARRATIVE SECTION. The brief asks for prose; a reply
# that lists is withheld like any other failed audit rather than re-flowed.
_LIST_LINE = re.compile(r"^\s*(?:[-*•–]\s|\d+[.)]\s|#+\s)", re.M)


def list_lines(text: Optional[str]) -> list[str]:
    return [m.group(0).strip() for m in _LIST_LINE.finditer(text or "")]


def words(text: Optional[str]) -> int:
    return len(re.findall(r"\b[\w'.%$-]+\b", text or ""))


# ---------------------------------------------------------------------------
# THE STACK'S OWN SECTIONS (T3): the six with no Monthly v2 prose -- the tape,
# Mechanics, What doesn't fit, Plumbing, Positioning, What's priced -- plus the
# claim lines of Narratives and Slow layers. Each is one call over that section's
# data, written as the stack writes the close's and the Weekly's
# (daily_cascade.stack_prose: the claim line, the tape's rules, the same audits),
# in the Monthly's frames.
# ---------------------------------------------------------------------------
STACK_SECTIONS = ("tape", "mechanics", "misfit", "plumbing", "positioning",
                  "priced", "narratives", "slow")
# Sections whose call writes the claim line alone: Narratives' paragraphs are the
# themes' own.
CLAIM_ONLY = ("narratives",)
MONTHLY_FRAMES = ("the weeks of the month first, then the month as a whole, then "
                  "where the month sits in the long frame.")
MONTHLY_NOTES = {
    "tape": (
        "\n\nTHE LONG FRAME'S COLUMNS AND THEIR ROLES: 'Month-end close' is the "
        "close; the 40-week, 10-month and 20-month columns are AVERAGES of past "
        "closes, never a close and never where a market ended the month; 'From "
        "the 52-week high' is a percentage distance. A market 'closed' or "
        "'ended' only at its month-end close."),
    "mechanics": (
        "\n\nTHE DEALER RETROSPECTIVE: how the market behaved against dealer "
        "positioning over the month, never what to do about it. Every figure "
        "comes from the counts table and the per-session flags. Write 'pinned', "
        "'held' or 'amplified' about a session ONLY where that session's flag "
        "is set, naming the session; or state the month's count for that flag "
        "exactly as the table gives it. Never infer a flag from the figures."),
    "misfit": (
        "\n\nEach open gap in the plain words its row gives, never by an id; the "
        "month's dissent and corrections as their sources state them."),
    "slow": (
        "\n\nSLOW LAYERS: the valuation, the base rates and the alternative "
        "assets as the tables state them -- levels and frequencies, never a "
        "signal. A level beside its long-run average or percentile names that "
        "window as the table gives it ('full history since ...', 'five years'). "
        "A sourced figure is the publisher's, stated with the publisher and its "
        "as-of date; never the publisher's view, forecast or recommendation."),
}


# THE PARENT SECTIONS NAME THE MOVES, NOT THE LEVELS (T3.3 item 4). The second box
# dry run withheld five parent paragraphs (the tape 10 figures, Plumbing 16,
# Positioning 11, What's priced 12, Slow layers 21) against the cap of 8: each
# re-listed the numbers its blocks beneath already print with their own reads. A
# parent with blocks under it is told so, and told the cap, before it writes.
PARENT_NOTE = ("\n\nTHE BLOCKS BENEATH THIS SECTION CARRY ITS NUMBERS: each has its "
               "own table and its own paragraph. Your paragraph names the moves, "
               "not the levels -- what moved, which way, and what moved with what "
               "-- and leaves the levels to the blocks. Cite at most {cap} figures "
               "in it; a paragraph over {n} figures is withheld.")


def parent_note(s: dict) -> str:
    """The parent frame's note, for a section with sub-sections beneath it."""
    if not s.get("subsections"):
        return ""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    # T3.4: the frame itself now offers only the cap's worth of figures.
    return (PARENT_NOTE.format(cap=_cap_word(), n=figure_cap())
            + (sp.parent_frame_note("monthly") if sp.is_parent(s, "monthly") else ""))


# THE POLICY WORDS, MARKET BY MARKET, BEFORE THE WRITER WRITES (T3.3 item 8).
# stack:priced was withheld for "a policy word ('hiking') attached to a recession
# market" -- a rule the writer met only in the rejection. The frame now lists,
# for each watched market, the policy words it may carry: the FOMC decision
# markets and the fed-funds path all of them, every other market none.
# The sections whose frames carry the list: What's priced writes about these
# markets, and The read's summary may name them.
POLICY_SECTIONS = ("priced", "read")
POLICY_WORDS = ("hike", "hikes", "hiked", "hiking", "cut", "cuts", "cutting",
                "hold", "holds", "holding", "held")


def policy_word_frame(pm_cfg: Optional[dict] = None) -> str:
    """The permitted policy words per scenario market, from the prediction-market
    config's watch list and its non-policy terms (the audit's own list)."""
    if pm_cfg is None:
        try:
            from altdata.sources import prediction_markets as _pm  # noqa: PLC0415
            pm_cfg = _pm.load_config()
        except Exception:                                       # noqa: BLE001
            pm_cfg = {}
    terms = ((pm_cfg.get("rules") or {}).get("non_policy_terms")
             or ["CPI", "inflation print", "recession", "House", "Senate",
                 "shutdown"])
    words = ", ".join(POLICY_WORDS)
    rows = ["the fed-funds futures path: " + words]
    for w in pm_cfg.get("watch_list") or []:
        lab = str(w.get("label") or w.get("id"))
        rows.append(f"{lab}: " + (words if w.get("id") == "fomc_decision"
                                  else "none"))
    return ("\n\nPOLICY WORDS, MARKET BY MARKET. The words a sentence may use about "
            "each market:\n" + "\n".join(f"  - {r}" for r in rows)
            + "\nA sentence that names " + ", ".join(f"'{t}'" for t in terms)
            + " carries no policy word at all -- a recession or CPI market is odds "
              "on that event, never on the Fed. Put the Fed's path and such a "
              "market in separate sentences.")


def stack_plan(ed: dict) -> list[dict]:
    """One entry per stack section that wants prose (not empty, not collapsed,
    not Mechanics below its session threshold)."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import narrative as base                 # noqa: PLC0415
    from altdata import bars as bars_mod                        # noqa: PLC0415
    cfg = bars_mod.load_config()
    caps = cfg.get("depth_words_monthly") or {}
    out = []
    for s in ed.get("sections") or []:
        if s["id"] not in STACK_SECTIONS or s.get("empty") \
                or not s.get("prose_wanted", True):
            continue
        paras = "0" if (s["id"] in CLAIM_ONLY or s.get("claim_only")) else \
            sp.DEPTH_PARAGRAPHS.get(s["depth"], "0")
        cap = int(caps.get(s["depth"]) or 120)
        body = (f"Then write ONE paragraph of at most {cap} words."
                if paras != "0" else "Write ONLY that one sentence.")
        why = f" ({s['depth_reason']})" if s.get("depth_reason") else ""
        system = sp.stack_system_prompt(base) + sp.RULES.format(
            title=s["title"], depth=s["depth"], why=why, body=body,
            report=voice(ed)[0], period=voice(ed)[1], frames=voice(ed)[2],
            figure_cap=_cap_word(), figure_tail=" -- the tables carry the rest")
        system += (sp.SECTION_NOTES.get(s["id"], "") + MONTHLY_NOTES.get(s["id"], "")
                   + parent_note(s)
                   + (policy_word_frame() if s["id"] in POLICY_SECTIONS else "")
                   + "\n" + ORDINAL_RULE.strip() + DISPLAY_RULE + T36_RULES + vocab_frame())
        out.append({"key": f"stack:{s['id']}", "title": s["title"], "kind": "stack",
                    "sid": s["id"], "system": system,
                    "max_chars": int(sp.MAX_CHARS.get(s["depth"], 900) * 2.5),
                    # T3.4: a parent's frame is its budget, not its tables.
                    "slice": sp.section_slice(s, ed, "monthly")})
    return out


# ---------------------------------------------------------------------------
# THE WRITTEN READS UNDER A SUB-SECTION'S TABLE (T3.1, ruled 9 Oct 2026): "the
# operator reads the Monthly for takeaways, not for numbers". A sub-section that
# declares `prose` -- Plumbing's buckets, Positioning's reads, What's priced's
# blocks, Slow layers' families -- gets ONE paragraph through this writer, over
# that sub-section's own table and data and nothing else, behind every audit the
# section's own paragraph passes (the numeral audit against the slice, the tape's
# rules, "no stored source, not printed"), with the one retry.
# ---------------------------------------------------------------------------
BLOCK_RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH FRAMING ABOVE. You are writing ONE BLOCK of a
section of {report}: the written read printed under the block's table, in a
desk's register. Every other rule above still holds -- every figure from the data
given, signs and percentile ordinals copied from their _signed and _ordinal
fields, no recommendation.

THE BLOCK: {title}, in the section {section}. {scope}

SHAPE. ONE paragraph of {words} words. Its FIRST SENTENCE is the takeaway: the
one thing the block's figures say together about the {period}, with its figure.
No headings, no bullets, no lists, no bold, no tables -- the block's table is
printed ABOVE your paragraph. Interpret it -- what the figures mean together,
what moved with what -- and never re-list its rows: cite at most
{figure_cap} figures -- the tables carry the rest.{ordinals}
Write about the market, never about this report, its checks or its data.
"""


def block_plan(ed: dict) -> list[dict]:
    """One entry per sub-section that declares `prose`, in a section that is
    not empty. Keyed by the sub-section's `phase`, so apply_prose sets its
    paragraphs, or its withheld note."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import narrative as base                 # noqa: PLC0415
    tape = "THE TAPE'S RULES:" + sp.RULES.split("THE TAPE'S RULES:", 1)[1] \
        .replace("{frames}", voice(ed)[2])
    out = []
    for s in ed.get("sections") or []:
        if s.get("empty"):
            continue
        for ss in s.get("subsections") or []:
            spec = ss.get("prose")
            if not spec or not ss.get("phase"):
                continue
            words_ = str(spec.get("words") or "60 to 100")
            hi = max(int(x) for x in re.findall(r"\d+", words_) or ["100"])
            system = sp.stack_system_prompt(base) + BLOCK_RULES.format(
                report=voice(ed)[0], title=ss["title"], section=s["title"],
                scope=(spec.get("scope") or "").rstrip(".") + ".", words=words_,
                period=voice(ed)[1],
                # A block may carry its own figure budget (AQ-2: the Quarterly's
                # items), never above the cadence's cap.
                figure_cap=_cap_word(min(int(spec.get("figures") or figure_cap()),
                                         figure_cap())),
                ordinals=ORDINAL_RULE) + tape
            sl = block_slice(s, ss, ed)
            system += ((spec.get("note") or "") + MONTHLY_NOTES.get(s["id"], "")
                       + (policy_word_frame() if s["id"] in POLICY_SECTIONS else "")
                       + DISPLAY_RULE + T36_RULES + vocab_frame()
                       + (BLOCK_FRAME_NOTE.format(cap=_cap_word().lower(),
                                                  filler=sp.FILLER_RULE)
                          if "figures_you_may_cite" in sl else
                          "\n\n" + sp.FILLER_RULE))
            out.append({"key": ss["phase"], "title": f"{s['title']}: {ss['title']}",
                        "kind": "stack", "sid": s["id"], "system": system,
                        "max_chars": hi * 9 + 500, "slice": sl})
    return out


# THE BLOCK'S FRAME, IN THE WEEKLY PARENTS' TERMS (T3.5 (b)). Monthly dry run #4
# withheld Yields & spreads, Macro, FOMC pricing and Prediction markets: the rest
# on the numeral audit -- figures the blocks' tables print but the frame did not
# offer. A block past the cap is now handed what a Weekly parent is (W-1.1 item
# 1.0): the figures it may cite, the table with the rest masked, and the other
# rows' names under "In the tables (do not enumerate)"; the filler rule is in
# the frame and enforced; a retry after the numeral audit names the figures it
# refused and lists the ones allowed.
BLOCK_FRAME_NOTE = (
    "\n\nYOUR FIGURES ARE IN YOUR DATA: `figures_you_may_cite` holds every row "
    "this paragraph may quantify -- at most {cap} figures -- each exactly as the "
    "table prints it; copy them verbatim, and never convert one (a percent into "
    "basis points, a level into a change, two figures into a difference). The "
    "table is given with every other row's figures masked; the series under 'In "
    "the tables (do not enumerate)' are printed for the reader: never list them "
    "or quantify them. {filler}")


def block_slice(s: dict, ss: dict, ed: dict) -> dict:
    """A block's frame (T3.4): its table, lines, points and data while they offer
    no more figures than the cap -- percentiles as ordinals only -- and past the
    cap, the Weekly parents' frame (T3.5): the rows that fit under
    `figures_you_may_cite`, the table with the rest masked, their names under
    "In the tables (do not enumerate)" (figure_budget.block_frame)."""
    from daily_cascade import figure_budget as fb               # noqa: PLC0415
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    full = fb.scrub_percentiles({"section": s["title"], "block": ss["title"],
                                 "month": ed.get("month"), "table": ss.get("table"),
                                 "lines": ss.get("lines"), "points": ss.get("points"),
                                 "data": sp._scrub(ss.get("data") or {})})
    if fb.quantified_figures(full) <= figure_cap():
        return full
    return fb.block_frame(s, ss, ed.get("month"), figure_cap(), MONTH_COLUMN)


# ---------------------------------------------------------------------------
# THE EXECUTIVE SUMMARY (T3.1 item 20, ruled 9 Oct 2026): one paragraph per
# section, in stack order, opening the edition. BUILT LAST, FROM THE FINISHED
# SECTIONS -- each call sees only what its section prints (its claim, its
# paragraphs, its tables, lines, points and reading entries, and the data they
# were written from), never the raw payload -- and through the same writer and
# audits, with the one retry. A paragraph the audit withholds prints "(summary
# withheld — audit)" rather than an unaudited sentence.
# ---------------------------------------------------------------------------
SUMMARY_RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH FRAMING ABOVE. You are writing ONE PARAGRAPH of
the EXECUTIVE SUMMARY that opens {report}: the paragraph for its section
"{title}". A reader may read only the summary, so it must stand alone. Every
other rule above still holds -- every figure from the data given, signs and
percentile ordinals as the data gives them, no recommendation.

SHAPE. THREE TO FIVE sentences of continuous prose. Carry the section's
takeaways -- what it says about the {period} -- and its load-bearing figures:
at most {figures} figures per paragraph -- the section's tables carry the rest --
each copied exactly as the section prints it.{ordinals} Introduce no figure, name
or claim the section does not print. No headings, bullets, lists or bold. Write
about the market, never about this report or its sections.
"""
SUMMARY_WITHHELD = "(summary withheld — audit)"
# THE NARRATIVES' SUMMARY CITES ITS SOURCES' DELTAS (T3.6 M8): withheld three
# times on bare_delta, each a positioning or survey change without its noun.
SOURCED_SUMMARIES = ("narratives",)
SOURCE_RULE = (" EVERY CHANGE IN THIS PARAGRAPH CARRIES ITS SOURCE AND ITS NOUN "
               "beside it, copied as the section prints it: \"+42,984 contracts "
               "(CFTC)\", \"+3.1 points (AAII)\" -- never a bare number, never a "
               "change without the publisher that reported it.")


def voice(ed: Optional[dict]) -> tuple[str, str, str]:
    """(report, period noun, frames) for the edition's cadence: the Monthly's own
    words, or -- for the Quarterly (AQ-1) -- the cadence's from
    config/reporting_stack.yaml."""
    name = (ed or {}).get("cadence") or "monthly"
    if name == "monthly":
        return "the Monthly", "month", MONTHLY_FRAMES
    from daily_cascade import cadence as cadence_mod             # noqa: PLC0415
    c = cadence_mod.get(name)
    return c["report"], c["period"], c["frames"]


def summary_slice(s: dict) -> dict:
    """What a finished section prints, for its summary paragraph."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    subs = [{"title": ss.get("title"), "table": ss.get("table"),
             "lines": ss.get("lines"), "points": ss.get("points"),
             "paragraphs": ss.get("paragraphs"),
             "entries": [{"publication": e.get("publication"),
                          "summary": e.get("summary") or e.get("line")}
                         for e in ss.get("entries") or []]}
            for ss in s.get("subsections") or []]
    return {"section": s["title"], "claim": s.get("claim"),
            "paragraphs": s.get("paragraphs"), "table": s.get("table"),
            "points": s.get("points"),
            "entries": [{"publication": e.get("publication"),
                         "summary": e.get("summary") or e.get("line")}
                        for e in s.get("entries") or []],
            "subsections": subs, "data": sp._scrub(s.get("data") or {})}


def summary_plan(ed: dict, sections: Optional[list] = None) -> list[dict]:
    """One entry per section that is not empty, in stack order -- the read,
    the tape, ..., Reading, Ahead, the book, Slow layers. An empty section gets
    no call; its summary line is its empty note. `sections` (AQ-1): the
    Quarterly's summary is one paragraph per CHAPTER, so it passes its chapters."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import narrative as base                 # noqa: PLC0415
    tape = "THE TAPE'S RULES:" + sp.RULES.split("THE TAPE'S RULES:", 1)[1] \
        .replace("{frames}", voice(ed)[2])
    out = []
    for s in (sections if sections is not None else ed.get("sections") or []):
        if s.get("empty"):
            continue
        system = sp.stack_system_prompt(base) + SUMMARY_RULES.format(
            report=voice(ed)[0], title=s["title"], period=voice(ed)[1],
            figures=_cap_word(summary_figures()).lower(),
            ordinals=ORDINAL_RULE) + tape
        frame = summary_frame(s, ed)
        cite = "; ".join(f"{f['series']} {f.get('change') or f.get('level')}"
                         for f in frame["figures_you_may_cite"]) or "none"
        system += ((policy_word_frame() if s["id"] in POLICY_SECTIONS else "")
                   + DISPLAY_RULE + T36_RULES + vocab_frame()
                   + SUMMARY_CITE.format(n=_cap_word(len(frame["figures_you_may_cite"]))
                                         .lower(), figures=cite))
        if s["id"] in SOURCED_SUMMARIES:
            system += SOURCE_RULE
        out.append({"key": f"summary:{s['id']}", "title": f"Summary: {s['title']}",
                    "kind": "stack", "sid": s["id"], "system": system,
                    "max_chars": 1400, "slice": reader_slice(frame),
                    "audit_extra": summary_audit_extra(s, ed)})
    return out


# THE SUMMARY IS AUDITED AGAINST WHAT IT SUMMARISES (T3.3 item 3). summary:read was
# withheld twice for "100th": the S&P 500, QQQ and the 10-year sit at the 100th
# percentile, printed by the tape, whose own paragraph passed -- but the read's
# summary was audited against the read's slice alone, which does not carry them.
# Each summary paragraph is now audited against the union of the figures and
# `_ordinal` fields of the sections it summarises: its own section, and for The
# read -- the edition's lines, drawn from every section -- every finished
# section. The audit set widens; the prompt does not, and the cap stays.
SUMMARISES_ALL = ("read",)


def summary_audit_extra(s: dict, ed: dict) -> dict:
    """What a summary paragraph is audited against beyond its frame: the
    section it summarises as it prints (since T3.4 the frame masks the prose's
    figures, so the section's own slice moves here and the scope is unchanged),
    and for The read every other finished section too."""
    own = summary_slice(s)
    if s["id"] not in SUMMARISES_ALL:
        return {"section_summarised": own}
    return {"section_summarised": own,
            "sections_summarised": [summary_slice(x) for x in ed.get("sections") or []
                                    if x is not s and not x.get("empty")]}


# THE SUMMARY'S FRAME HANDS IT ITS FIGURES (T3.4). The prose it summarises is given
# with its figures masked, and the cadence's `summary_figures` -- the section's
# top moves, ranked as a parent's are -- are named in the frame and the data.
SUMMARY_CITE = ("\n\nFIGURES YOU MAY CITE: these {n} -- {figures}. Each exactly as "
                "printed here; the prose you are given has its figures masked as "
                "[figure], and no other figure may be written.")


def summary_frame(s: dict, ed: dict) -> dict:
    """The summary's frame: the section's prose with its figures masked and its
    top moves up to the cadence's summary cap. The read, which summarises the
    edition and has no table of its own, takes the top moves across every
    finished section."""
    from daily_cascade import figure_budget as fb               # noqa: PLC0415
    frame = fb.summary_frame(s, summary_figures(), MONTH_COLUMN)
    if s["id"] in SUMMARISES_ALL:
        pool = [m for x in ed.get("sections") or [] if x is not s
                and not x.get("empty") for m in fb.section_moves(x, MONTH_COLUMN)]
        got, _ = fb.take(pool, summary_figures())
        frame["figures_you_may_cite"] = [fb.cite(m) for m in got]
    return frame


def _stack_faults(text: str, sec: dict, ed: dict, pm_cfg) -> list[str]:
    """The stack's tape rules (daily_cascade.stack_prose), and in Mechanics the
    flag words held to the per-session flags (monthly_macro.dealer)."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from altdata import bars as bars_mod                        # noqa: PLC0415
    cfg = bars_mod.load_config()
    out = (sp.style_faults(text, cfg) + sp.id_faults(text)
           + sp.policy_word_faults(text, pm_cfg) + sp.excess_faults(text)
           + sp.outlook_misprints(text, [], sp.venue_percents(ed))
           + sp.figure_faults(text, figure_cap())
           # T3.5 (b): the Weekly's filler ban (W-1.1 item 1.0d), on every
           # Monthly frame -- section, block and summary.
           + sp.filler_faults(text, sp.filler_names(sec.get("slice"))))
    # THE DIRECTION AUDIT AND THE STANCE CHECK (W-1.1b), as stack_prose.write
    # runs them for the Weekly and the close: a direction word is held to the
    # sign of the change the section prints in its month column, and "bullish on
    # inflation" is refused. Withheld on the same messages.
    out += direction_faults(text, sec, ed) + readability.stance_faults(text)
    # T3.6: the role audit (M1), the display form (M9), the dollar's label (M10).
    out += t36_faults(text, sec, ed)
    if sec["sid"] == "mechanics" and ed.get("_retro"):
        from . import dealer                                    # noqa: PLC0415
        out += dealer.flag_word_faults(text, ed["_retro"])
    return out


def _payloads(sec: dict, ed: Optional[dict]) -> list:
    """What a frame's figures are held to: its slice, its audit widening, and the
    edition's sections as they print (their tables and data)."""
    out = [sec.get("slice"), sec.get("audit_extra")]
    for x in (ed or {}).get("sections") or []:
        out.append({"table": x.get("table"), "data": x.get("data"),
                    "subsections": [{"table": ss.get("table"), "data": ss.get("data")}
                                    for ss in x.get("subsections") or []]})
    return out


def t36_faults(text: str, sec: dict, ed: Optional[dict]) -> list[str]:
    """T3.6's checks on one frame: a figure's role (M1), the display form of a
    large figure (M9), the dollar's name (M10)."""
    from altdata import numeral_audit as na                     # noqa: PLC0415
    pay = _payloads(sec, ed)
    return (na.role_faults(text, pay) + na.separator_faults(text)
            + dollar_label_faults(text, pay))


_DOLLAR_LABEL = re.compile(r"dollar|\bdxy\b", re.I)
_DOLLAR_NOT = re.compile(r"-(?:yen|yuan)|real|yen|yuan|cftc|speculator|net", re.I)
_DOLLAR_KEYS = ("close", "level", "value", "end_level", "latest", "last")


def dollar_series(payload, _out: Optional[dict] = None, _depth: int = 0) -> dict:
    """{label: {values}} -- every dollar series the payload prints a level of
    (the DXY, the Fed's broad index), by its own label."""
    out = {} if _out is None else _out
    if _depth > 12:
        return out
    if isinstance(payload, dict):
        lab = next((str(payload[k]) for k in ("market", "name", "series", "label")
                    if isinstance(payload.get(k), str)), "")
        if lab and _DOLLAR_LABEL.search(lab) and not _DOLLAR_NOT.search(lab):
            for k in _DOLLAR_KEYS:
                v = payload.get(k)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.setdefault(lab, set()).add(round(float(v), 2))
        cols, rows = payload.get("columns"), payload.get("rows")
        if isinstance(cols, list) and isinstance(rows, list):
            for r in rows:
                if not isinstance(r, (list, tuple)) or not r:
                    continue
                lab = str(r[0])
                if not _DOLLAR_LABEL.search(lab) or _DOLLAR_NOT.search(lab):
                    continue
                for j, c in enumerate(r[1:], start=1):
                    h = str(cols[j]).lower() if j < len(cols) else ""
                    m = re.match(r"^\$?(\d[\d,]*\.\d+)$", str(c).strip())
                    if m and ("close" in h or "level" in h or "last" in h):
                        out.setdefault(lab, set()).add(
                            round(float(m.group(1).replace(",", "")), 2))
        for v in payload.values():
            if isinstance(v, (dict, list, tuple)):
                dollar_series(v, out, _depth + 1)
    elif isinstance(payload, (list, tuple)):
        for v in payload:
            dollar_series(v, out, _depth + 1)
    return out


_BARE_DOLLAR = re.compile(r"\b(?:the\s+)?(?:US\s+)?dollar\b(?!\s+index|\s*\(|['’]s"
                          r"\s+broad|-)", re.I)
_NAMED_BEFORE = re.compile(r"(?:broad|trade-weighted|index|DXY)[\s\w'’]*$", re.I)


def dollar_label_faults(text: str, payload) -> list[str]:
    """[] or one fault line: "the dollar" bound to a level of one of TWO dollar
    series the edition prints (W-1.1a item 6's label rule, the Monthly's). With
    one dollar series, "the dollar" is its alias and passes."""
    series = dollar_series(payload)
    if len(series) < 2 or not text:
        return []
    from altdata import numeral_audit as na                     # noqa: PLC0415
    bad = []
    for sent in re.split(r"(?<=[.!?])\s+", text):
        for m in _BARE_DOLLAR.finditer(sent):
            if _NAMED_BEFORE.search(sent[max(0, m.start() - 25):m.start()]):
                continue
            tail = re.split(r"[;:,()—–]", sent[m.end():m.end() + 70])[0]
            for f in na.extract(tail):
                hit = [lab for lab, vals in series.items()
                       if any(abs(abs(f.value) - v) <= 0.006 for v in vals)]
                if hit and not f.is_percent:
                    others = "; ".join(f"{lab} {', '.join(f'{v:,.2f}' for v in sorted(vs))}"
                                       for lab, vs in sorted(series.items()))
                    bad.append(f"'{m.group(0).strip()} ... {f.text}' is {hit[0]}; "
                               f"the edition prints {others}")
    if not bad:
        return []
    return ["a dollar level printed as 'the dollar' where two dollar series print -- "
            "name the series: " + "; ".join(bad)]


def gap_faults(text: str, ed: Optional[dict]) -> list[str]:
    """T3.6 M5: a direction word about a GAP is held to that gap's direction over
    the month (rising: its |z| grew; falling: it shrank), as the misfit section's
    data carries it. A clause naming a gap is read against that gap; a clause
    about "the gaps" in general against all of them when they agree."""
    gaps = []
    for x in (ed or {}).get("sections") or []:
        if x.get("id") == "misfit":
            gaps = [g for g in (x.get("data") or {}).get("gaps") or []
                    if g.get("direction") in ("rising", "falling")]
    if not gaps or not text:
        return []
    from daily_cascade import direction as dmod                 # noqa: PLC0415
    lex = dmod._words(dmod.lexicon())
    lex.update({"widened": 1, "widening": 1, "widens": 1, "grew": 1, "growing": 1,
                "narrowed": -1, "narrowing": -1, "narrows": -1, "shrank": -1,
                "shrinking": -1, "closing": -1})
    sign = {"rising": 1, "falling": -1}
    bad = []
    for sent in re.split(r"(?<=[.!?])\s+", text):
        low = sent.lower()
        named = [g for g in gaps if str(g.get("gap") or "").lower() in low]
        generic = not named and re.search(r"\bgaps?\b", low)
        if not named and not generic:
            continue
        words_ = [(w, lex[w]) for w in re.findall(r"[a-z]+", low) if w in lex]
        if not words_:
            continue
        word, d = words_[0]
        targets = named or gaps
        actual = {sign[g["direction"]] for g in targets}
        if len(actual) == 1 and actual.pop() != d:
            bad.append(f"'{sent.strip()[:90]}': '{word}' against "
                       + ", ".join(f"{g['gap']} {g['direction']} (z {g.get('z')})"
                                   for g in targets))
    if not bad:
        return []
    return ["direction audit failed on the gaps: " + "; ".join(bad)]


def direction_faults(text: str, sec: dict, ed: dict) -> list[str]:
    """daily_cascade.direction's audit over one Monthly frame: the moves its
    section prints (a block's and a summary's are its parent section's), read
    from the month column -- every section's for a frame over the whole edition."""
    from daily_cascade import direction                         # noqa: PLC0415
    if not ed:
        return []
    out = direction.faults(text, direction.edition_moves(
        ed, sec.get("sid"), MONTH_COLUMN))
    if sec.get("sid") in ("misfit", "read"):
        out += gap_faults(text, ed)
    return out


# Withheld for a reason the prose cannot fix (Reader's Guide 5.3): no client, the
# API call failed, a payload past its guard, an empty reply, a reply that overran
# its length. Only an AUDIT's refusal is retried.
#
# THREE ATTEMPTS FOR EVERY SECTION (T3.3 item 4, the second box dry run): the
# first, and two retries, each with the audit's reason fed back. Where the draft
# ran over the figure cap the retry says exactly how far, in one fixed sentence
# (CAP_RETRY) -- the 10 Oct retries were told only "at most 8" and came back over
# it again. The caps themselves are not raised.
ATTEMPTS = 3
CAP_RETRY = "your draft cited {n} figures; the cap is {m}; remove figures, keep the reading"


def retry_prompt(system: str, prev: dict, sl: Optional[dict] = None) -> str:
    """The prompt for the next attempt: the frame, the audit's reason, and --
    when the draft ran over the cap -- the count and the cap; after the
    numeral audit, the figures it refused and those `sl` allows (T3.5)."""
    out = (system + "\n\nYOUR PREVIOUS DRAFT OF THIS SECTION WAS WITHHELD BY THE "
           "AUDIT: " + str(prev.get("reason"))[:600])
    if prev.get("vocab_words"):
        out += "\n" + VOCAB_RETRY.format(
            words=", ".join(f'"{w}"' for w in prev["vocab_words"]), rule=VOCAB_RULE)
    if prev.get("figures_over"):
        n, m = prev["figures_over"]
        out += "\n" + CAP_RETRY.format(n=n, m=m)
    if prev.get("unmatched"):
        out += "\n" + FIGURE_RETRY.format(
            figures=", ".join(f'"{f}"' for f in prev["unmatched"][:12]),
            allowed=allowed_figures(sl) or "none -- write the reading without figures")
    return out + ("\nWrite it again from the same data, fixing exactly that and "
                  "changing nothing else.")


# THE RETRY NAMES THE FIGURES (T3.5 (b), as W-1.1's did for the Weekly): after the
# numeral audit, the figures it refused and the ones the frame allows, so the
# second draft is not a guess at which number was wrong.
FIGURE_RETRY = ("the audit could not find {figures} in your data; cite only these, "
                "exactly as written: {allowed}")


def allowed_figures(sl: Optional[dict]) -> str:
    """The frame's citable figures as one line: each series and its cells, in the
    frame's order."""
    rows = []
    for r in (sl or {}).get("figures_you_may_cite") or []:
        if not isinstance(r, dict):
            continue
        name = r.get("series") or r.get("name") or ""
        cells = [f"{k} {v}" if k not in ("change", "level") else str(v)
                 for k, v in r.items() if k not in ("series", "name", "where")
                 and v not in (None, "", "—")]
        rows.append(f"{name}: " + ", ".join(cells) if cells else str(name))
    return "; ".join(rows)


TIGHTER = 0.7
TOO_LONG_RETRY = ("YOUR PREVIOUS DRAFT RAN PAST THE {n} CHARACTERS ALLOWED. Write it "
                  "again in at most {cap} characters: fewer sentences, the same "
                  "reading, every figure as the data gives it.")
NOT_RETRIED = ("fault", "unavailable", "call_failed", "prompt_too_large",
               "payload_too_large", "empty", "too_long")


def _not_retried(r: dict) -> bool:
    reason = str(r.get("reason") or "")
    return (r.get("state") in NOT_RETRIED
            or ("past the" in reason and "guard" in reason))


def write_all(p: dict, *, model: Optional[str] = None, client=None,
              only: Optional[Callable[[dict], bool]] = None,
              ed: Optional[dict] = None,
              secs: Optional[list[dict]] = None) -> dict:
    """{section key: result}, one audited call each -- and, for a section the
    audit withholds, up to two retries (ATTEMPTS, T3.3) with the audit's reason
    fed back (T3: the stack's retry, extended to the Monthly's section writer).
    Never raises.

    With `ed` (the stacked edition, monthly_macro.stack), the stack's own
    sections are written too, after the Monthly v2 sections. With `secs`, only
    those calls are made (the executive summary's, summary_plan)."""
    from daily_cascade import narrative as base
    from daily_cascade import stack_prose as sp_mod             # noqa: PLC0415
    from altdata import numeral_audit as na                     # noqa: PLC0415
    states = _market_states(p)
    try:
        from altdata.sources import prediction_markets as _pm   # noqa: PLC0415
        pm_cfg = _pm.load_config()
    except Exception:                                           # noqa: BLE001
        pm_cfg = None
    out: dict[str, dict] = {}
    if secs is None:
        secs = plan(p) + (stack_plan(ed) + block_plan(ed) if ed else [])

    def attempt(sec: dict, system: str) -> dict:
        stack = sec.get("kind") == "stack"
        try:
            if stack:
                from daily_cascade import stack_prose as sp     # noqa: PLC0415
                r = base.generate(sec["slice"], model=model, client=client,
                                  system_prompt=system, max_chars=sec["max_chars"],
                                  one_paragraph=False, citable_ids=[],
                                  unit_constants=sp.UNIT_CONSTANTS,
                                  guide_path=sp.STACK_GUIDE, market_states=states,
                                  audit_payload=sec.get("audit_extra"))
            else:
                r = base.generate(sec["slice"], model=model, client=client,
                                  system_prompt=system, guide_path=_style_guide(),
                                  max_chars=SECTION_MAX_CHARS, one_paragraph=False,
                                  citable_ids=[], market_states=states)
            published, state = bool(r.published), r.state
            reason = None if published else (r.withheld_note() or r.reason)
            lists = list_lines(r.text) if published else []
            jargon = internal_terms(r.text) if published else []
            tape = (_stack_faults(r.text, sec, ed or {}, pm_cfg)
                    if (published and stack) else
                    # A v2 section has no edition to hold directions to; the
                    # stance check needs none, and T3.6's role, display and
                    # dollar checks read its own slice.
                    readability.stance_faults(r.text) + t36_faults(r.text, sec, ed)
                    if published else [])
            # A count's or a small thousands change's own display form is
            # accepted (T3.4a): "+42,984" contracts, "+29,000" payrolls.
            accepted = na.accepted_deltas([sec.get("slice"),
                                           sec.get("audit_extra")])
            bare = na.bare_deltas(r.text, accepted) if published else []
            # The draft's figure count against the cap, published or not, so the
            # retry can say how far over it ran.
            drafted = r.text or getattr(r, "rejected_text", None) or ""
            cited = sp_mod.figures_cited(drafted) if stack and drafted else None
            over = ((cited, figure_cap()) if cited is not None
                    and cited > figure_cap() else None)
            vwords = vocab_words(jargon, tape)
            if jargon:
                published, state = False, "internal_vocabulary"
                reason = (f"narrative withheld: it writes about the system "
                          f"({', '.join(jargon)}) -- {VOCAB_RULE}")
            elif lists:
                published, state = False, "list_fragments"
                reason = (f"narrative withheld: the section came back as list "
                          f"fragments ({len(lists)} list line(s)), and a narrative "
                          f"section is prose")
            elif tape:
                published, state = False, "tape_rules"
                reason = "withheld: " + "; ".join(tape[:4])
            elif bare:
                published, state = False, "bare_delta"
                reason = (f"withheld: a change of 10,000 or more printed without its "
                          f"unit or scale ({', '.join(bare[:3])}) -- copy its "
                          f"change_display or latest_level_display verbatim")
            # A DIRECTIONAL VERB CARRIES THE SIGN (W-1.1b, the Weekly's W-1.1a
            # item 4): "fell -3 bp" prints "fell 3 bp", after every audit, and
            # the rewrite is counted.
            text, n_unsigned = (readability.unsign_after_verbs(r.text)
                                if published else (None, 0))
            return {
                "title": sec["title"], "state": state, "published": published,
                "text": text, "reason": reason,
                "unsigned_rewrites": n_unsigned,
                "words": words(text) if published else 0,
                # Kept for inspection, never printed: the operator can see what a
                # withheld section said and why the audit stopped it.
                "rejected_text": None if published else (
                    getattr(r, "rejected_text", None) or r.text),
                "model": r.model,
                "figures_checked": getattr(r, "figures_checked", None),
                "figures_cited": cited,
                "figures_over": None if published else over,
                "vocab_words": None if published else (vwords or None),
                "unmatched": (list(getattr(r, "unmatched", None) or []) or None)
                if state == "audit_failed" else None}
        except Exception as exc:                               # noqa: BLE001
            return {"title": sec["title"], "state": "fault",
                    "published": False, "text": None, "words": 0,
                    "reason": f"FAULT (code, not data) -- "
                              f"{type(exc).__name__}: {exc}"}

    for sec in secs:
        if only and not only(sec):
            continue
        system = sec.get("system") or system_prompt(sec["title"], sec["scope"],
                                                    sec["paragraphs"])
        # THE RETRIES (Reader's Guide 5.3; three attempts from T3.3): the audit's
        # reason goes back with the instruction to fix exactly that; a third
        # failure is withheld as before, with every reason kept.
        res = {**attempt(sec, system), "attempts": 1}
        reasons = [res.get("reason")]
        while (not res["published"] and not _not_retried(res)
               and res["attempts"] < ATTEMPTS):
            res = {**attempt(sec, retry_prompt(system, res, sec.get("slice"))),
                   "attempts": res["attempts"] + 1}
            reasons.append(res.get("reason"))
        # TOO LONG IS RETRIED ONCE, TIGHTER (T3.6 M8): the Ahead summary failed
        # "too_long" on its only attempt -- the length was never fed back. One
        # more call, told the cap it overran and a tighter one to write to.
        if res.get("state") == "too_long" and res["attempts"] < ATTEMPTS + 1:
            cap = int(round(int(sec.get("max_chars") or SECTION_MAX_CHARS) * TIGHTER))
            res = {**attempt(sec, system + "\n\n" + TOO_LONG_RETRY.format(
                n=int(sec.get("max_chars") or SECTION_MAX_CHARS), cap=cap)),
                   "attempts": res["attempts"] + 1}
            reasons.append(res.get("reason"))
        if not res["published"] and len(reasons) > 1:
            res["first_reason"] = reasons[0]
            res["reasons"] = reasons
        out[sec["key"]] = res
        log.info("section %s: %s (%s words, %d attempt(s))", sec["key"],
                 res["state"], res["words"], res["attempts"])
    return out


# ---------------------------------------------------------------------------
# T3.6 M2: ONE DIRECTION PER INSTRUMENT ACROSS THE EXECUTIVE SUMMARY
# ---------------------------------------------------------------------------
# The direction audit holds each paragraph to the signs its section prints; it
# could not see two paragraphs disagree with each other. The dry run's summary had
# gold "pulling back" in one paragraph and "holding its level" in another, the
# dollar "firmed" and "held". Each published summary paragraph's direction for
# each instrument it names is read -- up, down, or flat -- and an instrument with
# two directions has its paragraph(s) that disagree with the month's sign
# rewritten once with the reason; a paragraph still in conflict is withheld.
FLAT_WORDS = (r"held(?:\s+(?:its|their)\s+(?:level|ground|gains))?", r"holding",
              r"steady", r"steadied", r"unchanged", r"flat", r"little\s+changed",
              r"stable", r"sideways")
_FLAT = re.compile(r"\b(?:" + "|".join(FLAT_WORDS) + r")\b", re.I)
# Phrases the one-word lexicon cannot carry; a phrase is read before its words.
_DOWN_PHRASE = re.compile(r"\b(?:pull(?:s|ed|ing)?\s+back|g(?:ave|ive|iving)\s+back|"
                          r"gave\s+back|pared|backed\s+off|lost\s+ground)\b", re.I)
_UP_PHRASE = re.compile(r"\b(?:push(?:es|ed|ing)?\s+higher|gained\s+ground|"
                        r"extended\s+(?:its|their)\s+gains)\b", re.I)
_CLASS_NAME = {1: "up", -1: "down", 0: "flat"}


def summary_directions(text: str, moves: dict) -> dict[str, tuple[int, str]]:
    """{instrument: (1 | -1 | 0, the word)} for each clause of `text` that names
    exactly one instrument (a series the edition prints, or a currency) and
    carries a direction word: up or down from the direction lexicon, or flat."""
    from daily_cascade import direction as dmod                 # noqa: PLC0415
    lex = dmod.lexicon()
    words_ = dmod._words(lex)
    cur = lex.get("currencies") or {}
    out: dict[str, tuple[int, str]] = {}
    for sent in re.split(r"(?<=[.!?])\s+", text or ""):
        for clause in dmod._CLAUSE.split(sent):
            if not clause or not clause.strip():
                continue
            low = clause.lower()
            subjects = list(dmod._named(clause, moves))
            for c, spec in cur.items():
                if any(re.search(rf"(?<![\w/]){re.escape(str(w).lower())}(?![\w/])", low)
                       for w in spec.get("words") or []):
                    subjects.append(f"currency:{c}")
            if len(set(subjects)) != 1:
                continue
            hits = []
            taken: list[tuple[int, int]] = []
            for rx, d in ((_DOWN_PHRASE, -1), (_UP_PHRASE, 1), (_FLAT, 0)):
                for m in rx.finditer(clause):
                    hits.append((m.start(), d, m.group(0)))
                    taken.append((m.start(), m.end()))
            for t in re.finditer(r"[A-Za-z][\w'-]*", clause):
                d = words_.get(t.group(0).lower())
                if d is not None and not any(a <= t.start() < b for a, b in taken):
                    hits.append((t.start(), d, t.group(0)))
            if hits:
                _, d, w = min(hits)
                out.setdefault(subjects[0], (d, w))
    return out


def _actual(subject: str, moves: dict) -> Optional[tuple[int, str]]:
    from daily_cascade import direction as dmod                 # noqa: PLC0415
    if subject.startswith("currency:"):
        cur = dmod.lexicon().get("currencies") or {}
        got = dmod._currency_actual(subject.split(":", 1)[1], "", moves, cur)
        return got
    v = moves.get(subject)
    if not v:
        return None
    return dmod._sign(v[0]), f"{subject} {v[1]}"


def summary_conflicts(written: dict, ed: dict) -> dict[str, str]:
    """{summary key: why} -- the paragraphs to rewrite: for each instrument given
    two directions across the published summary paragraphs, those whose
    direction is not the month's sign (or, where the edition prints no sign for
    it, every paragraph after the first that named it)."""
    from daily_cascade import direction as dmod                 # noqa: PLC0415
    moves = dmod.edition_moves(ed, None, MONTH_COLUMN)
    order = [f"summary:{s['id']}" for s in ed.get("sections") or []]
    titles = {f"summary:{s['id']}": s["title"] for s in ed.get("sections") or []}
    seen: dict[str, list[tuple[str, int, str]]] = {}
    for key in order:
        r = written.get(key) or {}
        if not (r.get("published") and r.get("text")):
            continue
        for subj, (d, w) in summary_directions(r["text"], moves).items():
            seen.setdefault(subj, []).append((key, d, w))
    out: dict[str, str] = {}
    for subj, uses in seen.items():
        if len({d for _, d, _ in uses}) < 2:
            continue
        act = _actual(subj, moves)
        if act and act[0]:
            bad = [u for u in uses if u[1] != act[0]]
            fact = f"; the month's change is {act[1]}"
        else:
            bad = [u for u in uses[1:] if u[1] != uses[0][1]]
            fact = ""
        name = subj.split(":", 1)[-1]
        for key, d, w in bad:
            other = next(u for u in uses if u[0] != key or u[1] != d)
            out[key] = (out.get(key, "") + ("; " if key in out else "") +
                        f"one direction per instrument across the executive summary: "
                        f"{name} is '{w}' ({_CLASS_NAME[d]}) here and '{other[2]}' "
                        f"({_CLASS_NAME[other[1]]}) in the summary of "
                        f"{titles.get(other[0], other[0])}{fact}")
    return out


def reconcile_summary(p: dict, written: dict, ed: dict, *, model=None,
                      client=None) -> dict:
    """The summary's consistency pass: each conflicting paragraph rewritten once
    with the reason; one still in conflict is withheld."""
    bad = summary_conflicts(written, ed)
    if not bad:
        return written
    plan_ = {sec["key"]: sec for sec in summary_plan(ed)}
    redo = []
    for key, why in bad.items():
        sec = plan_.get(key)
        if sec is None:
            continue
        redo.append({**sec, "system": sec["system"] + "\n\nYOUR PREVIOUS DRAFT OF THIS "
                     "PARAGRAPH WAS WITHHELD: " + why + ". Write it again with the "
                     "month's direction, changing nothing else."})
    again = write_all(p, model=model, client=client, ed=ed, secs=redo) if redo else {}
    out = dict(written)
    for key, r in again.items():
        out[key] = {**r, "consistency_retry": bad[key]}
    still = summary_conflicts(out, ed)
    for key, why in still.items():
        if key in bad:
            out[key] = {**out[key], "published": False, "text": None,
                        "state": "inconsistent",
                        "reason": "withheld: " + why}
    return out

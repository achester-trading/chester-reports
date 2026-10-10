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
    """Every series a section sees, plainly keyed (the metric id stays out)."""
    keep = ("latest_level", "latest_level_display", "latest_pct", "latest_date",
            "since", "change_pct", "change_bps", "change", "change_display",
            "level_percentile_5y")
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
            report="the Monthly", period="month", frames=MONTHLY_FRAMES)
        system += sp.SECTION_NOTES.get(s["id"], "") + MONTHLY_NOTES.get(s["id"], "")
        out.append({"key": f"stack:{s['id']}", "title": s["title"], "kind": "stack",
                    "sid": s["id"], "system": system,
                    "max_chars": int(sp.MAX_CHARS.get(s["depth"], 900) * 2.5),
                    "slice": sp._slice(s, ed)})
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
what moved with what -- and never re-list its rows: cite at most SIX figures.
Write about the market, never about this report, its checks or its data.
"""


def block_plan(ed: dict) -> list[dict]:
    """One entry per sub-section that declares `prose`, in a section that is
    not empty. Keyed by the sub-section's `phase`, so apply_prose sets its
    paragraphs, or its withheld note."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import narrative as base                 # noqa: PLC0415
    tape = "THE TAPE'S RULES:" + sp.RULES.split("THE TAPE'S RULES:", 1)[1] \
        .replace("{frames}", MONTHLY_FRAMES)
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
                report="the Monthly", title=ss["title"], section=s["title"],
                scope=(spec.get("scope") or "").rstrip(".") + ".", words=words_,
                period="month") + tape
            system += (spec.get("note") or "") + MONTHLY_NOTES.get(s["id"], "")
            out.append({"key": ss["phase"], "title": f"{s['title']}: {ss['title']}",
                        "kind": "stack", "sid": s["id"], "system": system,
                        "max_chars": hi * 9 + 500,
                        "slice": {"section": s["title"], "block": ss["title"],
                                  "month": ed.get("month"),
                                  "table": ss.get("table"),
                                  "lines": ss.get("lines"),
                                  "points": ss.get("points"),
                                  "data": sp._scrub(ss.get("data") or {})}})
    return out


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
takeaways -- what it says about the {period} -- and its two or three
load-bearing figures, each copied exactly as the section prints it. Introduce no
figure, name or claim the section does not print. No headings, bullets, lists or
bold. Write about the market, never about this report or its sections.
"""
SUMMARY_WITHHELD = "(summary withheld — audit)"


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


def summary_plan(ed: dict) -> list[dict]:
    """One entry per section that is not empty, in stack order -- the read,
    the tape, ..., Reading, Ahead, the book, Slow layers. An empty section gets
    no call; its summary line is its empty note."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import narrative as base                 # noqa: PLC0415
    tape = "THE TAPE'S RULES:" + sp.RULES.split("THE TAPE'S RULES:", 1)[1] \
        .replace("{frames}", MONTHLY_FRAMES)
    out = []
    for s in ed.get("sections") or []:
        if s.get("empty"):
            continue
        system = sp.stack_system_prompt(base) + SUMMARY_RULES.format(
            report="the Monthly", title=s["title"], period="month") + tape
        out.append({"key": f"summary:{s['id']}", "title": f"Summary: {s['title']}",
                    "kind": "stack", "sid": s["id"], "system": system,
                    "max_chars": 1400, "slice": summary_slice(s)})
    return out


def _stack_faults(text: str, sec: dict, ed: dict, pm_cfg) -> list[str]:
    """The stack's tape rules (daily_cascade.stack_prose), and in Mechanics the
    flag words held to the per-session flags (monthly_macro.dealer)."""
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from altdata import bars as bars_mod                        # noqa: PLC0415
    cfg = bars_mod.load_config()
    out = (sp.style_faults(text, cfg) + sp.id_faults(text)
           + sp.policy_word_faults(text, pm_cfg) + sp.excess_faults(text)
           + sp.outlook_misprints(text, [], sp.venue_percents(ed))
           + sp.figure_faults(text))
    if sec["sid"] == "mechanics" and ed.get("_retro"):
        from . import dealer                                    # noqa: PLC0415
        out += dealer.flag_word_faults(text, ed["_retro"])
    return out


# Withheld for a reason the prose cannot fix (Reader's Guide 5.3): no client, the
# API call failed, a payload past its guard, an empty reply, a reply that overran
# its length. Only an AUDIT's refusal is retried.
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
    audit withholds, ONE RETRY with the audit's reason fed back (T3: the stack's
    retry, extended to the Monthly's section writer). Never raises.

    With `ed` (the stacked edition, monthly_macro.stack), the stack's own
    sections are written too, after the Monthly v2 sections. With `secs`, only
    those calls are made (the executive summary's, summary_plan)."""
    from daily_cascade import narrative as base
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
                                  guide_path=sp.STACK_GUIDE, market_states=states)
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
                    if (published and stack) else [])
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
            elif tape:
                published, state = False, "tape_rules"
                reason = "withheld: " + "; ".join(tape[:4])
            return {
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
            return {"title": sec["title"], "state": "fault",
                    "published": False, "text": None, "words": 0,
                    "reason": f"FAULT (code, not data) -- "
                              f"{type(exc).__name__}: {exc}"}

    for sec in secs:
        if only and not only(sec):
            continue
        system = sec.get("system") or system_prompt(sec["title"], sec["scope"],
                                                    sec["paragraphs"])
        first = attempt(sec, system)
        if first["published"] or _not_retried(first):
            res = {**first, "attempts": 1}
        else:
            # THE ONE RETRY (Reader's Guide 5.3): the audit's reason goes back
            # with the instruction to fix exactly that; a second failure is
            # withheld as before, with both reasons kept.
            retry = (system + "\n\nYOUR PREVIOUS DRAFT OF THIS SECTION WAS "
                     "WITHHELD BY THE AUDIT: " + str(first.get("reason"))[:600]
                     + "\nWrite it again from the same data, fixing exactly that "
                       "and changing nothing else.")
            res = {**attempt(sec, retry), "attempts": 2}
            if not res["published"]:
                res["first_reason"] = first.get("reason")
        out[sec["key"]] = res
        log.info("section %s: %s (%s words, %d attempt(s))", sec["key"],
                 res["state"], res["words"], res["attempts"])
    return out

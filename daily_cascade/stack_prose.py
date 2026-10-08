"""
The stack's prose on the daily close: claim lines, tape commentary, The read.
(reporting-stack brief 1.3 rule 1, 2.1 -- Tranche T1)

ONE AUDITED CALL PER SECTION, over that section's own data. The first sentence a
call returns is the section's CLAIM LINE, printed bold; a deep section's call also
writes its paragraphs. "The read" is written last, over the other sections'
claims and items -- the model's only free paragraph, five sentences. A collapsed
section reuses its prior claim and makes no call.

EVERY CALL GOES THROUGH narrative.generate(): print precision, the precomputed
ordinals and signed forms, the numeral and LABEL audit against the section's data
(the level list's rows carry the tape's level names), the state audit against the
object, markdown refused. Then four tape rules (2.1) the generic audit cannot see:

  internal vocabulary   phrases about the report (monthly_macro.prose.BANNED_TERMS)
  motive                "because", "driven by", "on fears" ... -- co-movement is
                        stated, a cause is not (rule 4)
  intensity             "plunged", "massive" ... in a sentence with no figure
                        (rule 7: no adjective doing a number's work)
  held / broke          a level said to have held or broken must carry that status
                        in the level list (rule 5)
  odds                  a probability prints only if it is an outlook's, with its
                        ledger entry, and only as a BASE RATE with its n -- never
                        as the system's view (rule 6; 1.3 rule 3; D-1 2 Oct 2026)

A section that fails any of them is withheld alone, with its reason; the items
and table beneath it still print.

THE ONE RETRY (Reader's Guide 5.3) is for the audit's refusals only. A fault --
no client, the API call failing (`call_failed`), a payload past its guard, an
empty reply, a reply that overran its length -- is not retried: the reason is not
the prose's to fix (NOT_RETRIED, not_retried).

PER CADENCE (T2.6). The report's name, its period and its frames, the paragraph
allowance and the runaway guards come from config `cadences:` through
daily_cascade/cadence.py. section_prompt / read_prompt / section_max_chars are
the hook a report outside this package (the Monthly) builds its prompts from, so
every cadence's sections are written to the same rule text.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from pathlib import Path

from altdata import levels as levels_mod

from . import readability

DEPTH_PARAGRAPHS = {"deep": "2 to 3", "medium": "1", "light": "0", "short": "0",
                    "line": "0"}
# Runaway guards, not style rules: a one-sentence section is cut to its first
# sentence after the audit, so its guard only has to catch a reply that lost
# the thread.
MAX_CHARS = {"deep": 2600, "medium": 1400, "light": 1600, "short": 1600,
             "line": 1200}
# The per-1% hedge-flow metric's own 1 (payload.NARRATIVE_UNIT_CONSTANTS).
UNIT_CONSTANTS = [1.0]

RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH FRAMING ABOVE. You are writing ONE SECTION of
{report}, in a desk's register. Every other rule above still holds -- every
figure from the data given, signs and percentile ordinals copied from their
_signed and _ordinal fields, no recommendation.

THE SECTION: {title}. Its depth today is {depth}{why}.

SHAPE. Your FIRST SENTENCE is the section's claim line: the one thing this section
says about the {period}, with its figure. {body}
No headings, no bullets, no lists, no bold, no tables -- the section's tables are
printed ABOVE your paragraph, and every figure lives in them. Your paragraph
INTERPRETS the tables -- what the figures mean together, what moved with what --
and never re-lists their rows: cite at most SIX figures in it.
Never write about how this report, its checks or its data work: no sentence about
the method, what the report tracks, what it can or cannot see, or why something is
printed. Write about the market.

THE TAPE'S RULES:
1. Frames in order: {frames}
2. A level is named by its label and value exactly as the data lists it ("the
   20-day average at 652.10"); never name a level the data does not list.
3. A move carries its sign and size, copied from its _signed form.
4. Co-movement, never motive. "The long end led: 30-year +9 bp against 2-year
   +2 bp" is allowed; "because", "driven by", "on fears of" are not. A cause is
   named only when a stored event coincides, as "on the day of the CPI release".
5. Say a level "held" or "broke" only when its status in the data says so.
6. A probability appears only as an outlook's BASE RATE, in this form: "the base
   rate for <the outlook's claim> is 79% (n=82)". It is a frequency in the stored
   history, never our view: no "we expect", "likely", "odds", "chance", "lean".
   A VENUE'S figure is the market's price, written as such: "Kalshi prices a
   hike at 62%", "fed funds futures imply 21% of a 25 bp hike" -- never "a 62%
   chance", never as a fact or as our view, and never as a reason to act.
7. No adjective does a number's work: no "plunged", "soared", "massive" without
   the figure in the same sentence.
8. Short declarative sentences; one idea per paragraph; the figure in the
   sentence, not in a parenthesis after it.
Never write about the report itself: no "the data", "the payload", "this section".
The word "because" is refused anywhere, whatever it joins.
The market-wide reads are "dealer gamma", "the volatility regime" and "the macro
regime" -- never the word "dial", which is the system's word, not the market's.
For one symbol write its net GEX ("QQQ's net GEX is positive"), never "QQQ is in
positive gamma".
Never write the session's date or weekday: the header carries it. Any other
date only as given (2026-10-02).
Name each level with its own market, one at a time; never "respectively".
Never compute a count, a difference or a ratio: copy the one the data carries.
"""

READ_RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH FRAMING ABOVE. Write THE READ: the lines that
matter about the {period}, as ONE paragraph of at most five sentences and at most
120 words, most important first, citing at most six figures in all. The FIRST
sentence is the claim line and the email's subject: keep it under 90 characters.
Draw only on the section claims and items given, and NEVER copy a section's claim
or any of its sentences: every sentence of The read is worded afresh, because the
sections print theirs below and a sentence printed twice is withheld. Never write
about how this report works. Every other rule above still holds; no recommendation; a probability only
as an outlook's base rate ("the base rate for ... is 79% (n=82)"), never as our
view; no motive words; never write about the report itself.
The word "because" is refused anywhere. Write "dealer gamma", "the volatility
regime", "the macro regime" -- never "dial"; for one symbol write its net GEX. Never write the session's date
or weekday. A level is named with the market it belongs to, one at a time.
"""


def figure_faults(text: str) -> list[str]:
    """ONE FACT, ONCE (T2.5 item 1): the paragraph after the claim line cites at
    most six figures -- the tables carry the rest."""
    sents = _sentences((text or "").split("\n\n")[0])
    rest = (text or "")[len(sents[0]):] if sents else ""
    n = readability.figure_count(rest)
    return ([f"the paragraph cites {n} figures; at most "
             f"{readability.PARAGRAPH_FIGURES} -- the tables carry the rest"]
            if n > readability.PARAGRAPH_FIGURES else [])


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def style_faults(text: str, cfg: dict) -> list[str]:
    from monthly_macro.prose import internal_terms              # noqa: PLC0415
    st = cfg.get("style") or {}
    out = [f"internal vocabulary: {t}" for t in internal_terms(text)]
    low = (text or "").lower()
    for ph in st.get("motive_phrases") or []:
        if re.search(rf"(?<![\w-]){re.escape(ph.lower())}(?![\w-])", low):
            out.append(f"motive: '{ph}'")
    for ph in st.get("banned_phrases") or []:
        if re.search(rf"(?<![\w-]){re.escape(ph.lower())}(?![\w-])", low):
            out.append(f"banned phrase: '{ph}'")
    for s in _sentences(text):
        for w in st.get("intensity_words") or []:
            if re.search(rf"\b{re.escape(w)}\b", s, re.I) and not re.search(r"\d", s):
                out.append(f"'{w}' with no figure in its sentence")
    return out


# NO UNLABELLED ID (T2.2 item 2): a registry key ("fred.hy_oas"), a contradiction
# or story id ("equities_vs_credit"), or an exception id ("extreme:...") in prose
# is the system's vocabulary, not the reader's. The labels in
# config/display_labels.yaml are the only words for them.
_KEY = re.compile(r"\b(?:fred|calc|yfinance|cftc|acm|pm|dial|ndl|finra|tic|umich|"
                  r"nyfed|aaii|apewisdom|dealer|auction)\.[a-z0-9_]+\b")
_SNAKE = re.compile(r"\b[a-z]+(?:_[a-z0-9]+)+\b")


def id_faults(text: str) -> list[str]:
    out = [f"internal id: '{m.group(0)}'" for m in _KEY.finditer(text or "")]
    out += [f"internal id: '{m.group(0)}'" for m in _SNAKE.finditer(text or "")]
    return out


_VERB = re.compile(r"\b(held|holds|holding|broke|breaks|broken)\b", re.I)
_CLAUSE = re.compile(r"[;:]|,\s+(?:and|but|while)\s+|\s+(?:and|but|while)\s+")


def level_status_faults(text: str, level_status: dict,
                        rows: Optional[list] = None) -> list[str]:
    """'held'/'broke' beside a level label must match THAT instrument's status.

    Per clause: the label, the verb, and the instrument named nearest before the
    label (by ticker, or by an alias the level list declares). A clause naming
    no instrument is held to the instrument the sentence last named, and failing
    that to any instrument -- the weakest reading, used only when the prose gives
    nothing better.
    """
    out = []
    labels = sorted({lv["label"] for lvs in level_status.values() for lv in lvs},
                    key=len, reverse=True)
    names: list[tuple[re.Pattern, str]] = []
    for r in rows or []:
        iid = next((k for k in level_status
                    if k.upper() == str(r.get("symbol")).upper()
                    or k == str(r.get("symbol")).lower()), None)
        if not iid:
            continue
        for n in [r.get("symbol"), r.get("name")] + list(r.get("aliases") or []):
            if n:
                names.append((re.compile(rf"(?<![\w-]){re.escape(str(n))}(?![\w-])",
                                         re.I if n != r.get("symbol") else 0), iid))

    def named(s: str) -> Optional[str]:
        best, at = None, -1
        for rx, iid in names:
            for m in rx.finditer(s):
                if m.start() > at:
                    best, at = iid, m.start()
        return best
    for sent in _sentences(text):
        context = None
        pos = 0
        for clause in _CLAUSE.split(sent):
            here = named(clause)
            context = here or context
            pos += len(clause)
            v = _VERB.search(clause)
            if not v:
                continue
            said = "broke" if v.group(1).lower().startswith("br") else "held"
            lab = next((lb for lb in labels
                        if re.search(rf"\b{re.escape(lb)}\b", clause, re.I)), None)
            if not lab:
                continue
            pool = ([level_status.get(context) or []] if context
                    else list(level_status.values()))
            if not any(lv["label"] == lab and lv.get("status") == said
                       for lvs in pool for lv in lvs):
                who = f"{context.upper()}'s " if context else "any listed "
                out.append(f"'{lab}' said to have "
                           f"{'held' if said == 'held' else 'broken'}, which "
                           f"{who}{lab} did not")
    return out


_ODDS = re.compile(r"\b(\d{1,2}(?:\.\d+)?)\s?(?:%|percent)\s+(?:that|chance|"
                   r"probability|odds|likely)\b", re.I)


_VIEW = re.compile(r"\b(?:we|our)\s+(?:expect|think|see|believe|view|lean|call|"
                   r"forecast|odds)\b|\b(?:likely|likelihood|odds|chance|lean|"
                   r"probably|expected to)\b", re.I)
_PCT = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d+)?)\s?(?:%|percent)")


_POLICY = re.compile(r"\b(hike[sd]?|hiking|cut|cuts|cutting|hold|holds|holding)\b",
                     re.I)


def policy_word_faults(text: str, cfg_pm: Optional[dict] = None) -> list[str]:
    """T2 ruling 2: a sentence with a policy word (hike, cut, hold) may cite only
    the fomc_decision item or the fed-funds path. A policy word in a sentence that
    names another watched market -- a CPI print, a recession, an election, a
    shutdown -- is withheld: a CPI market is odds on an inflation print, nothing
    more."""
    terms = ((cfg_pm or {}).get("rules") or {}).get("non_policy_terms") or \
        ["CPI", "inflation print", "recession", "House", "Senate", "shutdown"]
    out = []
    for s in _sentences(text):
        word = None
        m = _RATE_MOVE.search(s)
        if m:
            word = m.group(0)
        else:
            # "HOLD" IS A POLICY WORD ONLY BESIDE THE FED (T2.1 item 6): with Fed,
            # FOMC or meeting in the same clause. "The low holds", "the wall held"
            # are level verbs and pass.
            for clause in re.split(r"[;:,—]|\s-\s|\band\b|\bwhile\b", s):
                h = _HOLD.search(clause)
                if h and _FED.search(clause):
                    word = h.group(0)
                    break
        if not word:
            continue
        hit = next((t for t in terms
                    if re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", s, re.I)), None)
        if hit:
            out.append(f"a policy word ('{word}') attached to a {hit} market")
    return out


_RATE_MOVE = re.compile(r"\b(?:hike[sd]?|hiking|rate cuts?|cut rates|cuts?|cutting)\b",
                        re.I)
_HOLD = re.compile(r"\b(?:hold|holds|holding|held)\b", re.I)
_FED = re.compile(r"\b(?:Fed|FOMC|meeting)\b", re.I)


_BOOKZ = re.compile(r"\b(?:Book Z|the book|book's|cash|60-40|60/40)\b", re.I)
_VS = re.compile(r"\b(?:vs\.?|versus|against|beat|beats|outperform\w*|"
                 r"underperform\w*|trail\w*|lag\w*)\b", re.I)
_FIG = re.compile(r"\d(?:[\d.,]*)\s?(?:%|pts|points|pp)")


def excess_faults(text: str) -> list[str]:
    """T2 ruling 1: a book-against-benchmark comparison with a figure must say
    'excess' or 'relative to' -- the book's return and a benchmark's are two
    absolutes, and a 'vs' figure without the word reads as the book's own."""
    return [f"a vs-figure against Book Z without 'excess' or 'relative to'"
            for s in _sentences(text)
            if _BOOKZ.search(s) and _VS.search(s) and _FIG.search(s)
            and not re.search(r"\bexcess\b|\brelative to\b", s, re.I)]


def venue_percents(ed: dict) -> set:
    """Every probability a VENUE or the futures put in front of the prose, in
    whole percent -- figures the prose may quote as the market's price."""
    pr = next((s for s in ed.get("sections") or [] if s["id"] == "priced"), {})
    d = pr.get("data") or {}
    out = set()
    for rows in (d.get("watch") or {}).values():
        for r in rows:
            if r.get("probability") is not None:
                out.add(round(r["probability"] * 100))
    for by_venue in ((d.get("venues") or {}).get("fomc_odds") or {}).values():
        for o in by_venue.values():
            out.update(round(v * 100) for v in o.values())
    for m in (d.get("rate_path") or {}).get("meetings") or []:
        p = m.get("move_probability_25bp")
        if p is not None:
            out.update({round(p * 100), round((1 - p) * 100), 0})
    return out


def outlook_misprints(text: str, outlooks: list[dict],
                      venue_ok: Optional[set] = None) -> list[str]:
    """A probability prints only as a ledgered outlook's base rate, with its n.

    Two refusals. A figure framed as odds ("62% chance that ...") that is not an
    outlook's is not in the ledger. And a sentence carrying an outlook's figure
    must name it as a base rate with its n and use no view word -- the outlook is
    a frequency in the stored history, never the system's view (D-1, 2 Oct 2026).
    """
    live = [o for o in outlooks
            if o.get("state") == "computed" and o.get("ledger_id")]
    ok = {round(o["probability"] * 100) for o in live}
    # A VENUE'S OR THE FUTURES' figure is the market's price, quotable as such;
    # it is not an outlook and needs no base-rate framing. Anything else framed
    # as odds came from nowhere and is refused.
    vok = set(venue_ok or ())
    out = [f"{m.group(1)}% is not an outlook in the ledger or a venue's price"
           for m in _ODDS.finditer(text or "")
           if round(float(m.group(1))) not in ok | vok]
    for s in _sentences(text):
        hits = [m for m in _PCT.finditer(s) if round(float(m.group(1))) in ok]
        if not hits:
            continue
        if not re.search(r"\bbase rate\b", s, re.I) or not re.search(r"\bn\s?=\s?\d", s):
            out.append(f"{hits[0].group(1)}% printed without 'base rate' and its n")
        v = _VIEW.search(s)
        if v:
            out.append(f"{hits[0].group(1)}% framed as a view ('{v.group(0)}')")
    return out


def _scrub(v):
    """A prose slice carries no internal id: `_`-prefixed keys (where the
    charts keep a contradiction's id) are dropped at every depth."""
    if isinstance(v, dict):
        return {k: _scrub(x) for k, x in v.items() if not str(k).startswith("_")}
    if isinstance(v, list):
        return [_scrub(x) for x in v]
    return v


def _compact(v, depth: int = 0):
    """The Read's view of a section's data: its figures, not its tables. Scalars
    and short lists to three levels; long lists (level lists, venue tables,
    histories) are dropped -- the section's own prose already used them, and The
    read's payload must stay inside the runaway guard."""
    if isinstance(v, dict):
        if depth >= 3:
            return None
        out = {k: _compact(x, depth + 1) for k, x in v.items()}
        return {k: x for k, x in out.items() if x not in (None, {}, [])}
    if isinstance(v, list):
        if len(v) > 6 or depth >= 3:
            return None
        return [x for x in (_compact(x, depth + 1) for x in v) if x not in (None, {})]
    return v


def _slice(s: dict, ed: dict) -> dict:
    # NOT-YET-TRACKED ITEMS ARE FOOTNOTES ONLY (T2.1 item 10): the report prints
    # them under the section, and the prose is never given them to narrate. The
    # bar-completeness counts stay out for the same reason.
    return {"section": s["title"], "depth": s["depth"],
            "depth_reason": s.get("depth_reason"), "session": ed["session"],
            "items": [i["text"] for i in s["items"]], "table": s.get("table"),
            "table_note": s.get("table_note"),
            # EVERY SUB-SECTION'S TABLE, untagged (T2.5 item 2): the section
            # writes one paragraph across them.
            "subsections": [{"title": ss.get("title"), "table": ss.get("table"),
                             "lines": ss.get("lines")}
                            for ss in s.get("subsections") or []],
            "data": _scrub({k: v for k, v in (s.get("data") or {}).items()
                            if k != "intraday"})}


STACK_GUIDE = Path(__file__).resolve().parent.parent / "docs" / \
    "narrative-template-stack.md"

# THE BASE PROMPT'S RULE 5 ends a paragraph "on the system ... what it will test
# next". The stack drops it (T2.1 item 8): a section says what happened in its
# own window and stops; only Ahead looks forward.
STACK_RULE5 = ("5. STOP AT WHAT HAPPENED. Do not end on what the next session or "
               "week will test, and never write about the system. Only the Ahead "
               "section looks forward.")


def stack_system_prompt(base) -> str:
    sp = base.SYSTEM_PROMPT
    i = sp.find("5. END ON THE SYSTEM")
    if i < 0:
        return sp + "\n\n" + STACK_RULE5
    j = sp.find("\n\n", i)
    return sp[:i] + STACK_RULE5 + (sp[j:] if j > 0 else "")


# What one section's prose must do beyond the shared rules.
SECTION_NOTES = {
    "positioning": (
        "\n\nPOSITIONING & FLOWS: the claim line states the leadership; the "
        "paragraph reads the sources together -- futures positioning (CFTC), "
        "retail, short interest, foreign flows -- for what they say jointly. A "
        "source with no figure in the data gets no mention."),
    "book": (
        "\n\nBOOK Z: the book's return and each benchmark's are absolutes; any "
        "comparison between them is written as an EXCESS ('an excess of +0.8 "
        "points over cash'), never 'the book against cash' with a figure."),
    "narratives": (
        "\n\nNARRATIVES AS SYNTHESIS (Phase B): for each story, what moved it for "
        "and against this period and who dissented, from the sourced items in the "
        "data. Name a voice only as the data names it, with its outlet; a voice "
        "not in the data does not exist for this section. Never declare a status "
        "-- NEW, REITERATED, INFLECTED and SILENT are computed and printed in the "
        "table; describe an inflection only where the data marks one. Attribute "
        "every view ('Goldman Sachs Research expects ...'); never adopt one."),
    "ahead": (
        "\n\nTHIS SECTION ALONE LOOKS FORWARD: the calendar, the base rates and "
        "the graded calls it is given, stated as what is scheduled and what the "
        "record shows -- never as what the market will do."),
}


# THE WEEKLY'S OWN NOTES (T2.2, ruled 4 Oct 2026), appended after SECTION_NOTES
# on the Weekly only -- the daily close keeps its shape.
WEEKLY_NOTES = {
    "read": (
        "\n\nTHE WEEK BY DAY: the data carries a table, one row per session -- "
        "SPY's and the 10-year's moves, the tier-1 release with actual and prior, "
        "the Fed speech or auction, the day's most-cited story. The table prints "
        "under your claim: interpret the week's shape from it (which day carried "
        "the move, what coincided with it), never walk it day by day. A press "
        "outlet's explanation of a move is ITS attribution, never ours: write "
        "'CNBC attributed the fall to ...', never the cause as fact."),
    "tape": (
        "\n\nTHE TAPE IN ONE PARAGRAPH: what the week's moves across equities, "
        "rates, the dollar and commodities, and crypto say together -- which led, "
        "which diverged. Name only figures in the table or the level list; a "
        "market with no figure in the table gets no sentence."),
    "mechanics": (
        "\n\nTHE WEEK'S DEALER STORY FROM THE TABLE AND ITS FLAGS ONLY. Write "
        "'pinned', 'held' or 'amplified' about a session only where that "
        "session's flag column says so; never infer a flag from the figures. "
        "The flags sit in the Ranges and flags table."
        "\n\nTHE VOLATILITY READ, inside the one paragraph, is stated from the "
        "daily move: 'the market is pricing X% daily moves; it realized Y%', both "
        "from the Volatility table's 'Daily move priced, and realized' row and "
        "nowhere else, then the VIX against its percentile; MOVE and SKEW only "
        "where their rows carry a level."),
    "misfit": (
        "\n\nEach open gap is described in the plain words its row gives "
        "(what each side is saying), never by an id."),
    "plumbing": (
        "\n\nRead the table: the curve, credit and the week's tier-1 releases "
        "with their actual and prior."),
    "positioning": (
        "\n\nOne paragraph across the sub-sections' tables: what they say "
        "together."),
    "priced": (
        "\n\nOne paragraph across the sub-sections' tables: what they say "
        "together. "
        "Prediction markets are 'prediction markets', never 'venues'."),
    "narratives": (
        "\n\nName each story by its plain title as the data gives it, and give "
        "counts in words ('nine sourced items supported it, none contradicted "
        "it')."),
}


# PER CADENCE (T2; config `cadences:` since T2.6): the report, its period, the
# frames it writes (brief 2.1 rule 1: each report writes the frame it owns and
# the one above it), its paragraph allowance and its runaway guards. A cadence's
# own notes follow the shared SECTION_NOTES; on the Weekly, Positioning's and
# What's priced's shared notes give way to the Weekly's.
CADENCE_NOTES = {"weekly": WEEKLY_NOTES}
CADENCE_REPLACES_NOTES = {"weekly": ("positioning", "priced")}

# Withheld for a reason the prose cannot fix (Reader's Guide 5.3): no client, the
# API call failed, a payload past its guard, an empty reply, a reply that overran
# its length. Only an AUDIT's refusal is retried.
NOT_RETRIED = ("fault", "unavailable", "call_failed", "prompt_too_large",
               "payload_too_large", "empty", "too_long")


def not_retried(r: dict) -> bool:
    reason = str(r.get("reason") or "")
    return (r.get("state") in NOT_RETRIED
            or ("past the" in reason and "guard" in reason))


def retry_prompt(system: str, reason: Optional[str]) -> str:
    """The one retry's system prompt: the audit's reason, and the instruction to
    fix exactly that."""
    return (system + "\n\nYOUR PREVIOUS DRAFT OF THIS SECTION WAS "
            "WITHHELD BY THE AUDIT: " + str(reason)[:600]
            + "\nWrite it again from the same data, fixing exactly that "
              "and changing nothing else.")


def cadence_of(cadence: str) -> dict:
    from . import cadence as cadence_mod                        # noqa: PLC0415
    return cadence_mod.get(cadence)


def section_prompt(s: dict, cadence: str = "daily", base=None,
                   extra_notes: Optional[dict] = None,
                   claim_only: bool = False) -> str:
    """One section's system prompt at `cadence`: the stack's base prompt, the
    shared RULES in the cadence's report, period and frames, the paragraph
    allowance, the section's shared note and the cadence's own. `extra_notes`
    ({section id: text}) is appended last -- the Monthly's notes live with the
    Monthly. `claim_only` asks for the claim line alone."""
    from . import cadence as cadence_mod                        # noqa: PLC0415
    if base is None:
        from daily_cascade import narrative as base             # noqa: PLC0415
    cad = cadence_mod.get(cadence)
    paras = "0" if claim_only else DEPTH_PARAGRAPHS.get(s["depth"], "0")
    # ONE PARAGRAPH (T2.5 item 2): a section that carries prose writes its
    # claim line and one paragraph over ALL its tables -- the sub-sections
    # no longer take paragraphs of their own.
    body = (f"Then write ONE paragraph of at most "
            f"{cadence_mod.paragraph_cap(cad, s['depth'])} words."
            if paras != "0" else "Write ONLY that one sentence.")
    why = f" ({s['depth_reason']})" if s.get("depth_reason") else ""
    sys_prompt = stack_system_prompt(base) + RULES.format(
        title=s["title"], depth=s["depth"], why=why, body=body,
        report=cad["report"], period=cad["period"], frames=cad["frames"])
    if s["id"] not in CADENCE_REPLACES_NOTES.get(cadence, ()):
        sys_prompt += SECTION_NOTES.get(s["id"], "")
    sys_prompt += CADENCE_NOTES.get(cadence, {}).get(s["id"], "")
    sys_prompt += (extra_notes or {}).get(s["id"], "")
    return sys_prompt


def section_max_chars(s: dict, cadence: str = "daily") -> int:
    """The section's runaway guard at `cadence` (not a style rule)."""
    return int(MAX_CHARS.get(s["depth"], 900) * float(cadence_of(cadence)["chars_scale"]))


def read_prompt(cadence: str = "daily", base=None) -> str:
    """The read's system prompt at `cadence`."""
    if base is None:
        from daily_cascade import narrative as base             # noqa: PLC0415
    sp = stack_system_prompt(base) + READ_RULES.format(period=cadence_of(cadence)["period"])
    return sp + (CADENCE_NOTES.get(cadence, {}).get("read", "")
                 if cadence == "weekly" else "")


def write(ed: dict, *, market_states: Optional[dict] = None, client=None,
          model: Optional[str] = None, outlooks: Optional[list] = None,
          cadence: str = "daily") -> dict:
    """Fill each section's claim and paragraphs; then The read. Never raises."""
    cad = cadence_of(cadence)
    try:
        from altdata.sources import prediction_markets as _pm   # noqa: PLC0415
        pm_cfg = _pm.load_config()
    except Exception:                                           # noqa: BLE001
        pm_cfg = None
    from daily_cascade import narrative as base                  # noqa: PLC0415
    from altdata import bars as bars_mod                         # noqa: PLC0415
    cfg = bars_mod.load_config()
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    lstatus = (tape.get("data") or {}).get("level_status") or {}
    lrows = (tape.get("data") or {}).get("levels") or []
    results: dict[str, dict] = {}

    def run(sid: str, payload: dict, system: str, max_chars: int) -> dict:
        """One audited attempt; if the audit withholds it, ONE retry with the
        audit's reason fed back (T2.1 ruling), then withhold as before. A fault
        (the API, the payload guard) is not retried: the reason is not the
        prose's to fix."""
        first = attempt(sid, payload, system, max_chars)
        # A FAULT IS NOT RETRIED (Reader's Guide 5.3): until T2.6 only "fault"
        # and the payload guard were excluded here, so a failed API call
        # (`call_failed`) was sent a second time with an "audit" reason.
        if first.get("published") or not_retried(first):
            return {**first, "attempts": 1}
        retry_sys = retry_prompt(system, first.get("reason"))
        # THE RETRY MAY KEEP A REPEATED SENTENCE (T2.5 item 4): the code check
        # after the prose withholds it in the later section, so a Read that
        # repeats one sentence is not lost whole.
        second = attempt(sid, payload, retry_sys, max_chars, dup_ok=True)
        second["attempts"] = 2
        if not second.get("published"):
            second["first_reason"] = first.get("reason")
        return second

    def attempt(sid: str, payload: dict, system: str, max_chars: int,
                dup_ok: bool = False) -> dict:
        try:
            r = base.generate(payload, model=model, client=client,
                              system_prompt=system, max_chars=max_chars,
                              one_paragraph=False, citable_ids=[],
                              unit_constants=UNIT_CONSTANTS, guide_path=STACK_GUIDE,
                              market_states=market_states)
        except Exception as exc:                                # noqa: BLE001
            return {"state": "fault", "published": False,
                    "reason": f"FAULT {type(exc).__name__}: {exc}"}
        text = r.text if r.published else None
        faults = []
        if text:
            faults = (style_faults(text, cfg) + id_faults(text)
                      + policy_word_faults(text, pm_cfg) + excess_faults(text)
                      + outlook_misprints(text, outlooks or [], venue_percents(ed))
                      + (level_status_faults(text, lstatus, lrows)
                         if sid in ("tape", "read") else [])
                      + figure_faults(text)
                      # NO SENTENCE TWICE (T2.5 item 4): The read is written
                      # last, over the sections' claims, so it is the one held
                      # to them; what survives the retry is withheld where it
                      # repeats (readability.withhold_duplicates).
                      + ([f"repeats a section's sentence: '{x[:80]}'" for x in
                          readability.duplicates_of(text,
                                                    readability.section_sentences(ed))]
                         if sid == "read" and not dup_ok else []))
        if faults:
            return {"state": "tape_rules", "published": False,
                    "reason": "withheld: " + "; ".join(faults[:4]),
                    "rejected_text": text}
        if not r.published:
            return {"state": r.state, "published": False,
                    "reason": r.withheld_note() or r.reason,
                    "rejected_text": getattr(r, "rejected_text", None)}
        return {"state": "published", "published": True, "text": text,
                "model": r.model}

    for s in ed["sections"]:
        if s["id"] == "read":
            continue
        # EMPTY MEANS ONE LINE (T2.5 item 5): no new facts, no model call.
        if s.get("empty"):
            results[s["id"]] = {"state": "empty", "published": False}
            continue
        paras = DEPTH_PARAGRAPHS.get(s["depth"], "0")
        res = run(s["id"], _slice(s, ed), section_prompt(s, cadence, base),
                  section_max_chars(s, cadence))
        results[s["id"]] = res
        if res.get("published"):
            sents = _sentences(res["text"].split("\n\n")[0])
            s["claim"] = sents[0] if sents else res["text"]
            rest = res["text"][len(s["claim"]):].strip()
            s["paragraphs"] = ([re.sub(r"\s+", " ", rest)] if rest and paras != "0"
                               else [])
        else:
            s["claim"] = None
            s["withheld"] = res.get("reason")
    # THE READ, over the other sections' claims and items.
    read = next(s for s in ed["sections"] if s["id"] == "read")
    rp = {"session": ed["session"],
          # THE SECTIONS' DATA TOO (T2.1): The read draws on every section, and
          # a figure it repeats -- a percentile ordinal, a z -- must be one the
          # audit can find; ids and not-yet-tracked lists are scrubbed as for
          # any section.
          "sections": [{"section": s["title"], "claim": s.get("claim"),
                        "items": [i["text"] for i in s["items"]],
                        "data": _compact(_scrub({k: v for k, v in
                                                 (s.get("data") or {}).items()
                                                 if k != "intraday"}))}
                       for s in ed["sections"]
                       if s["id"] != "read" and not s.get("empty")],
          "levels": (tape.get("data") or {}).get("levels")}
    read_sys = read_prompt(cadence, base)
    if cadence == "weekly":
        # THE WEEK BY DAY (T2.2 item 3): the opening reads from The read's own
        # table, and a press attribution is the outlet's, never ours.
        rp["week_by_day"] = read.get("table")
        rp["press_attributions"] = [i["text"] for i in read["items"]
                                    if i["key"].startswith("read:attr")]
    res = run("read", rp, read_sys, int(cad["read_chars"]))
    results["read"] = res
    if res.get("published"):
        sents = _sentences(res["text"])
        read["claim"] = sents[0] if sents else res["text"]
        read["paragraphs"] = [" ".join(sents[1:])] if len(sents) > 1 else []
    else:
        read["withheld"] = res.get("reason")
    ed["prose"] = {k: {kk: v.get(kk) for kk in ("state", "published", "reason",
                                                 "rejected_text", "attempts",
                                                 "first_reason")}
                   for k, v in results.items()}
    return ed


def split_tagged(text: str) -> dict:
    """'[A] one. [B] two.' -> {'A': 'one.', 'B': 'two.'}; text before the first
    tag is dropped (the claim was taken from it)."""
    parts = re.split(r"\[([A-E])\]\s*", text or "")
    out = {}
    for i in range(1, len(parts) - 1, 2):
        body = parts[i + 1].strip()
        if body:
            out[parts[i]] = re.sub(r"\s+", " ", body)
    return out


def prose_levels(text: str, book: dict) -> list[str]:
    """Level labels the prose names that are not in the level list (gate)."""
    known = {lab.lower() for _, lab, _ in levels_mod.labelled(book)}
    out = []
    for _, lab in levels_mod.LEVEL_TYPES:
        if re.search(rf"\b{re.escape(lab)}\b", text or "", re.I) and lab.lower() not in known:
            out.append(lab)
    return out

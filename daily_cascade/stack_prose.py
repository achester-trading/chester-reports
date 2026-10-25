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
from altdata import model_meter

from . import audit_retry, direction, readability
from . import opener as opener_mod

# The read's depth on every cadence (config `sections`): its opener band.
READ_DEPTH = "deep"
DEPTH_PARAGRAPHS = {"deep": "2 to 3", "medium": "1", "light": "0", "short": "0",
                    "line": "0"}
# Runaway guards, not style rules: each only has to catch a reply that lost the
# thread. Since D19/D20 (24 Oct 2026) a reply under its guard prints in full: a
# section asked for one sentence is no longer cut to its first.
MAX_CHARS = {"deep": 2600, "medium": 1400, "light": 1600, "short": 1600,
             "line": 1200}
# D19/D20: each ceiling doubled (runaway()), and capped under the call's output
# limit: 2,000 tokens (narrative.MAX_TOKENS) is about 8,000 characters.
RUNAWAY_SCALE = 2.0
RUNAWAY_CEILING = 7000
# The per-1% hedge-flow metric's own 1 (payload.NARRATIVE_UNIT_CONSTANTS).
UNIT_CONSTANTS = [1.0]

# A CEILING, NOT A QUOTA (W-1.1a item 5). The 12 Oct dry run's Plumbing strung
# "Reverse repo balances slipped -1bn, a marginal draw against a jobless-claims
# four-week average whose prior stood at 200,500": two unrelated figures in one
# sentence to use the budget. Every frame carries this rule; the filler audit
# withholds the bare one-figure sentence ("Real Estate added +1.96%.").
CEILING_RULE = ("\nTHE FIGURE BUDGET IS A CEILING, NOT A QUOTA: cite only the "
                "figures the story needs, and never join two unrelated figures in "
                "one sentence to use the budget.\n")

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
and never re-lists their rows: cite at most {figure_cap} figures in it{figure_tail}.
Never write about how this report, its checks or its data work: no sentence about
the method, what the report tracks, what it can or cannot see, or why something is
printed. Write about the market.

THE TAPE'S RULES:
1. Frames in order: {frames}
2. A level is named by its label and value exactly as the data lists it ("the
   20-day average at 652.10"); never name a level the data does not list.
3. A move carries its sign and size, copied from its _signed form -- except
   after a directional verb, which carries the sign itself: "fell 3 bp",
   "rose 3.36%", "widened 37 bp", never "fell -3 bp" or "rose +3.36%". The verb
   must agree with the sign, and a sentence about the dollar, the euro or the
   yen must agree with that currency's own move ("EUR/USD fell 0.43%, the
   dollar firmer").
4. Co-movement, never motive. "The long end led: 30-year +9 bp against 2-year
   +2 bp" is allowed; "because", "driven by", "on fears of" are not. A cause is
   named only when a stored event coincides, as "on the day of the CPI release".
5. Say a level "held" or "broke" only when its status in the data says so --
   "the gamma flip at 775.54 broke", never "marked broke".
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
Never "bullish" or "bearish" on a macro variable -- inflation, growth, rates:
write what is expected ("expects inflation to stay above target").
"The front" and "the front end" mean the 2-year. Join two figures in one
sentence only where they share an as-of; where they do not, give each its date.
""" + CEILING_RULE

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
""" + CEILING_RULE


def figures_cited(text: str, groups: Optional[list] = None) -> int:
    """The figures the paragraph after the claim line cites -- the count the cap
    is held to, and the N a retry is told (T3.3 item 4). Each of `groups` (sets
    of figures that are one comparison -- the Book Z line, W-1.1a item 2) counts
    once, however many of its figures the paragraph copies."""
    sents = _sentences((text or "").split("\n\n")[0])
    rest = (text or "")[len(sents[0]):] if sents else ""
    figs = readability.figures(rest)
    if not groups:
        return len(figs)
    from .figure_budget import norm_figure                      # noqa: PLC0415
    hit, n = set(), 0
    for f in figs:
        g = next((i for i, grp in enumerate(groups) if norm_figure(f) in grp), None)
        if g is None:
            n += 1
        elif g not in hit:
            hit.add(g)
            n += 1
    return n


def figure_faults(text: str, cap: Optional[int] = None,
                  groups: Optional[list] = None) -> list[str]:
    """ONE FACT, ONCE (T2.5 item 1): the paragraph after the claim line cites at
    most `cap` figures -- the tables carry the rest. The cap is the cadence's
    `paragraph_figures` (six for the close and the Weekly, 8 for the Monthly,
    T3.2 item 1); unset, six. A group counts as one (W-1.1a item 2)."""
    cap = readability.PARAGRAPH_FIGURES if cap is None else int(cap)
    n = figures_cited(text, groups)
    return ([f"the paragraph cites {n} figures"
             + (" (the Book Z line counted as one)" if groups else "")
             + f"; at most {cap} -- the tables carry the rest"]
            if n > cap else [])


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


# FILLER (W-1.1 item 1.0d): a sentence that only says other series moved.
FILLER_MOVED = re.compile(r"\b(?:also|all)\s+mov(?:ed|ing)\b|\bmoved\s+alongside\b|"
                          r"\bmoved\s+through\s+the\s+(?:week|month|session)\b", re.I)


def filler_names(payload) -> list[str]:
    """The series names a frame hands the writer -- quantified or not -- which
    are the names a filler list strings together."""
    from . import figure_budget                                 # noqa: PLC0415
    out: list[str] = []

    def walk(o, key=None):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "series" and isinstance(v, str):
                    out.append(v)
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                if key in (figure_budget.IN_TABLES, "also_moved") and isinstance(v, str):
                    out.append(v)
                walk(v, key)
    walk(payload)
    return [n for n in dict.fromkeys(out) if n and len(n) > 2]


def _name_forms(name: str) -> list[str]:
    """A table name and its short form: "USD/JPY (yen per dollar)" -> also
    "USD/JPY"; "CFTC S&P 500 futures" -> also "S&P 500 futures"."""
    forms = [name, name.split(" (")[0]]
    if name.startswith("CFTC "):
        forms.append(name[5:])
    for f in list(forms):
        if f.lower().endswith(" futures"):
            forms.append(f[:-8])
    return [f.strip() for f in dict.fromkeys(forms) if len(f.strip()) > 2]


# THE BARE FIGURE (W-1.1a item 5): a sentence of six words or fewer carrying
# exactly one figure and no comparison word says a number and nothing about it.
COMPARISON_WORDS = ("against", "than", "while", "as", "from")
BARE_MAX_WORDS = 6


def bare_figure_sentence(s: str) -> bool:
    words = s.split()
    if not words or len(words) > BARE_MAX_WORDS:
        return False
    if readability.figure_count(s) != 1:
        return False
    return not any(re.search(rf"\b{w}\b", s, re.I) for w in COMPARISON_WORDS)


# CODE-WRITTEN TAGGED LINES ARE EXEMPT (post-Friday fix 1, ruled 16 Oct 2026).
# A line a block's code writes and closes on the descriptive tag -- SR-43/49's
# anchors line: "... ACM term premium 1.03% (as of 2026-10-09). (descriptive;
# unvalidated, n=0)" -- is a table row in sentence form, not prose: its figures
# are computed and printed by code, and the tag alone read as a bare figure.
# The exemption needs both: the caller says the line is code-written, and the
# line ends on the tag. A model's paragraph is never exempt, tag or no tag.
CODE_TAG = re.compile(r"\(descriptive; unvalidated, n=\d+\)\.?\s*$")


def code_tagged(text: str) -> bool:
    return bool(CODE_TAG.search(text or ""))


def filler_faults(text: str, names: Optional[list] = None,
                  code_written: bool = False) -> list[str]:
    """Withhold a paragraph with a filler sentence: "also/all moved(ing)",
    "moved alongside", "moved through the week" -- or three or more of the
    frame's series names joined by commas with no figure among them. The fault
    quotes the sentence, so the retry names it. A code-written line ending on
    the descriptive tag is exempt (`code_written=True`, CODE_TAG)."""
    if code_written and code_tagged(text):
        return []
    out = []
    ss = _sentences(text)
    for i, s in enumerate(ss):
        if FILLER_MOVED.search(s):
            out.append(f"filler sentence: '{s[:160]}'")
            continue
        if bare_figure_sentence(s):
            out.append(f"filler: a bare figure with nothing to read it against: "
                       f"'{s[:160]}'")
            continue
        if readability.figures(s):
            continue
        # THE TAKEAWAY NAMES SERIES AS A READING (dry run 7, 17 Oct 2026). The
        # opener rule bars any figure from the Takeaway, so a Takeaway that names
        # the series it reads ("a rotation this wide, from Technology into
        # Utilities, Energy and Financials, ...") cannot carry one itself. It
        # passes the list check when the paragraph's other sentences carry
        # figures; a body sentence is read alone, as before.
        if opener_mod.is_takeaway(s) and any(
                readability.figures(x) for j, x in enumerate(ss) if j != i):
            continue
        hits = [n for n in names or []
                if any(re.search(rf"(?<![\w-]){re.escape(f)}(?![\w-])", s, re.I)
                       for f in _name_forms(n))]
        if len(hits) >= 3 and s.count(",") >= 1:
            out.append(f"filler list of {len(hits)} series with no figure: '{s[:160]}'")
    return out


# "TAIL" ONLY WHERE A TAIL IS STORED (W-1.1 item 1.4). An auction "tailed" is a
# claim about the when-issued yield, which no source we hold publishes; the word
# is allowed in a sentence about an auction only when a stored tail is positive.
_TAIL = re.compile(r"\btail(?:ed|ing|s)?\b(?!-risk)", re.I)


def stored_tails(ed: dict) -> list[float]:
    pl = next((s for s in ed.get("sections") or [] if s.get("id") == "plumbing"), {})
    recs = (((pl.get("data") or {}).get("plumbing") or {}).get("auction_records") or [])
    return [r["tail_bp"] for r in recs if isinstance(r.get("tail_bp"), (int, float))]


def tail_faults(text: str, tails: Optional[list] = None) -> list[str]:
    if any(t > 0 for t in tails or []):
        return []
    return [f"'tail' about an auction with no positive stored tail: '{s[:120]}'"
            for s in _sentences(text)
            if re.search(r"\bauction", s, re.I) and _TAIL.search(s)]


# QUOTED TEXT IS ATTRIBUTION (W-1.1 item 1.6): a quoted official's "driven by" is
# the official's word, not our inference, so the motive check reads the prose
# with its quotations struck.
# T3.5 (e): single quotation marks too -- curly, guillemets, and straight ones
# that open after a space and close before one (an apostrophe in "Lane's" is
# not a quotation).
_QUOTED = re.compile(r"\"[^\"]*\"|“[^”]*”|‘[^’]*’|«[^»]*»"
                     r"|(?<![\w'])'[^'\n]+'(?![\w'])")


def unquoted(text: str) -> str:
    return _QUOTED.sub(" ", text or "")


def style_faults(text: str, cfg: dict, attributed: bool = False) -> list[str]:
    """The style list. `attributed` (T3.5 (e)): the text is a sourced voice's
    own view, printed under its name, outlet and URL -- the voices block -- so a
    motive phrase in it is the voice's claim, not ours, quoted or paraphrased;
    every other rule holds."""
    from monthly_macro.prose import internal_terms              # noqa: PLC0415
    st = cfg.get("style") or {}
    out = [f"internal vocabulary: {t}" for t in internal_terms(text)]
    low = (text or "").lower()
    own = unquoted(text).lower()
    for ph in ([] if attributed else st.get("motive_phrases") or []):
        if re.search(rf"(?<![\w-]){re.escape(ph.lower())}(?![\w-])", own):
            out.append(f"motive: '{ph}'")
    for ph in st.get("banned_phrases") or []:
        if re.search(rf"(?<![\w-]){re.escape(ph.lower())}(?![\w-])", low):
            out.append(f"banned phrase: '{ph}'")
    for s in _sentences(text):
        for w in st.get("intensity_words") or []:
            if re.search(rf"\b{re.escape(w)}\b", s, re.I) and not re.search(r"\d", s):
                out.append(f"'{w}' with no figure in its sentence")
    return out + basis_faults(text)


# THE BASIS PROXY'S FENCE (SR-36): the leveraged short in Treasury futures is the
# basis trade's futures leg, never a directional short. The rejected readings --
# "hedge funds are short bonds", a bet on yields, a squeeze -- withhold the
# paragraph wherever they appear (config/basis_proxy.yaml `banned_patterns`).
def basis_faults(text: str) -> list[str]:
    try:
        from altdata import basis_proxy                         # noqa: PLC0415
        pats = basis_proxy.load_config().get("banned_patterns") or []
    except Exception:                                           # noqa: BLE001
        return []
    out = []
    for s in _sentences(text):
        for p in pats:
            if re.search(p, s, re.I):
                out.append(f"directional reading of the basis trade: '{s[:120]}' -- "
                           f"the leveraged short is the basis trade's futures leg; "
                           f"read it only as fragility")
                break
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
    # The retry names the sentence and quotes the rule (W-1.1 item 1.0e), as
    # T3.4a's vocabulary retry does.
    return [f"a vs-figure against Book Z without 'excess' or 'relative to' in "
            f"'{s[:100]}'; the rule: {EXCESS_RULE}"
            for s in _sentences(text)
            if _BOOKZ.search(s) and _VS.search(s) and _FIG.search(s)
            and not re.search(r"\bexcess\b|\brelative to\b", s, re.I)]


# weekly-fixes-7 item 6: THE BOOK'S TIME WORD. Dry run 7's opener said "this week"
# four times over figures that all ran since 5 Sep. A time word in the book's
# paragraph must match a figure's window in its tables: "week" needs the week's
# window (benchmark.week_line, "on the week (... to ...)") in the book's data.
_WEEK_WORD = re.compile(r"\b(?:this|the|last) week\b|\bon the week\b|\bweek's\b|"
                        r"\bweekly return\b", re.I)


def na_signed_zero(text: str) -> list[str]:
    """weekly-fixes-7 item 12: no signed zero in prose (numeral_audit's rule)."""
    from altdata import numeral_audit                           # noqa: PLC0415
    return numeral_audit.signed_zero_faults(text)


_PERFORMANCE = re.compile(r"\b(?:return\w*|excess|relative to|outperform\w*|"
                          r"underperform\w*|beat\w*|lagg?\w*|trail\w*|cash|SPY|"
                          r"60-40|NAV|Book Z|gain\w*|lost|rose|fell|held its ground)"
                          r"\b|%")


def book_window_faults(text: str, ed: dict) -> list[str]:
    """A sentence about the book's PERFORMANCE with a week word needs the week's
    window in the book's data (benchmark.week_line); the tables' own week
    figures (trades, sitting time) need nothing."""
    bk = next((s for s in ed.get("sections") or [] if s.get("id") == "book"), {})
    bz = str((bk.get("data") or {}).get("book_z") or "")
    if "on the week (" in bz:
        return []
    return [f"a time word with no figure on that window in '{s[:100]}': every book "
            f"figure runs since inception, so say 'since' and its date, not the week"
            for s in _sentences(text)
            if _WEEK_WORD.search(s) and _PERFORMANCE.search(s)]


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
from altdata.basis_proxy import BASIS_NOTE                      # noqa: E402

SECTION_NOTES = {
    "positioning": (
        "\n\nPOSITIONING & FLOWS: the claim line states the leadership; the "
        "paragraph reads the sources together -- futures positioning (CFTC), "
        "retail, short interest, foreign flows -- for what they say jointly. A "
        "source with no figure in the data gets no mention." + BASIS_NOTE),
    # SR-36: the basis-unwind watch prints in Plumbing too.
    "plumbing": BASIS_NOTE,
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


# THE THREE FIXED SENTENCES (6b part 2; brief v2 section 4): when Mechanics
# carries the dealer block, its paragraph opens with them, from
# `dealer_sentences` only, behind the numeral and flag-word audits.
DEALER_SENTENCES_NOTE = (
    "\n\nTHE THREE DEALER SENTENCES: your paragraph's body opens with exactly "
    "three sentences, in this order, citing only the figures under "
    "`dealer_sentences`, verbatim: (1) the regime with its net-to-gross, the "
    "zero-gamma level and its distance from spot, and the asymmetry of net GEX "
    "one percent either side of spot; (2) where the gamma concentrates -- the "
    "OTM call wall, the OTM put gamma wall, the peak-gamma strike and which "
    "expiry carries it, and the hedge rolling off at the next expiry, as a SIZE "
    "with no direction; (3) the setups whose conditions hold for the session "
    "named, each with its invalidating level, or that no setup holds. Every "
    "level is inferred, not observed. Never write 'support' or 'resistance', "
    "and never write pinned, held, amplified or dampened about a session.")


# THE VOLATILITY EVENT'S PARAGRAPH (Batch 9 item 52): in the desk voice, from
# `vol_event` only, behind the same audits.
VOL_EVENT_NOTE = (
    "\n\nTHE VOLATILITY EVENT: one passage, in the desk voice, on what is behind "
    "the move, from `vol_event` only: the trigger, then which lenses carried it "
    "and which did not, then the regime consequence and the base rate as "
    "printed. The catalyst is the outlet's attribution when the data names one, "
    "never ours; where it says 'not established', say so. The Book C line is "
    "printed, not applied. No forecast beyond the base rate's own figures.")


def dealer_flag_faults(text: str, ed: dict) -> list[str]:
    """The flag-word audit over Mechanics: the Weekly's scored sessions
    (`dealer_week`) are the flags; the close has none at prose time."""
    from . import dealer_block                                  # noqa: PLC0415
    mech = next((s for s in ed.get("sections") or [] if s.get("id") == "mechanics"), {})
    return dealer_block.flag_word_faults(text, (mech.get("data") or {}).get("dealer_week"))


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
        "(what each side is saying), never by an id. \"Open n sessions\" is said "
        "only of a gap's age (gap_open_sessions); an exception's status has its "
        "own date and is never counted in sessions open. A gap's z measures how "
        "far apart the two markets have drifted in all, not the week's move."),
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


def retry_prompt(system: str, reason: Optional[str], attempt: int = 2,
                 attempts: int = 2, draft: Optional[str] = None) -> str:
    """A retry's system prompt: the audit's WHOLE withhold message, the rule
    behind each kind of fault it names, and the instruction to fix exactly that
    (W-1.3c item 6 -- until then the message was cut at 600 characters, after
    the first four faults, so a late fault never reached the writer). With the
    `draft` (W8-1), the retry is a revision: the failing span and the draft
    itself, to fix and change nothing else (daily_cascade/audit_retry.py)."""
    note = (audit_retry.revision_note(reason, draft) if draft
            else opener_mod.retry_note(reason, attempt, attempts))
    return system + note.replace(
        "YOUR PREVIOUS DRAFT WAS", "YOUR PREVIOUS DRAFT OF THIS SECTION WAS", 1)


def attempts_of(cad: dict) -> int:
    """Audited attempts per section: one draft and ONE revision at every cadence
    (W8-1, 18 Oct 2026; the Weekly's three of W-1.3c item 6 are withdrawn --
    the retry is now told the draft and the failing span, so a second retry
    would only re-draw). `cad` is kept for the callers."""
    return audit_retry.ATTEMPTS


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
    # THE OPENER (W-1.3a item 3.0): on a cadence that carries one, the claim
    # and the body are one paragraph in a word band, read before the tables.
    opens = (not claim_only and paras != "0"
             and opener_mod.band(cad, s["depth"]) is not None)
    body = ("Then continue the SAME paragraph in the opener shape below."
            if opens else
            f"Then write ONE paragraph of at most "
            f"{cadence_mod.paragraph_cap(cad, s['depth'])} words."
            if paras != "0" else "Write ONLY that one sentence.")
    why = f" ({s['depth_reason']})" if s.get("depth_reason") else ""
    sys_prompt = stack_system_prompt(base) + RULES.format(
        title=s["title"], depth=s["depth"], why=why, body=body,
        report=cad["report"], period=cad["period"], frames=cad["frames"],
        figure_cap=cadence_mod.figure_word(section_figure_cap(s.get("id"), cadence)),
        figure_tail="")
    if s["id"] not in CADENCE_REPLACES_NOTES.get(cadence, ()):
        sys_prompt += SECTION_NOTES.get(s["id"], "")
    if (s.get("data") or {}).get("dealer_sentences"):
        sys_prompt += DEALER_SENTENCES_NOTE
    if (s.get("data") or {}).get("vol_event"):
        sys_prompt += VOL_EVENT_NOTE
    if (s.get("data") or {}).get("dealer_week_vs_monday"):
        from .dealer_weekly import FOURTH_NOTE                  # noqa: PLC0415
        sys_prompt += FOURTH_NOTE
    sys_prompt += CADENCE_NOTES.get(cadence, {}).get(s["id"], "")
    sys_prompt += (extra_notes or {}).get(s["id"], "")
    if not claim_only and is_parent(s, cadence):
        sys_prompt += parent_frame_note(cadence, s.get("id"))
        if s.get("id") == "tape" and cadence in TAPE_LEVEL_CADENCES:
            sys_prompt += TAPE_LEVEL_NOTE
    elif not claim_only and s.get("id") in BUDGETED_FRAMES.get(cadence, ()):
        sys_prompt += BUDGETED_FRAME_NOTE.format(
            cap=cadence_mod.figure_word(section_figure_cap(s.get("id"), cadence)).lower(),
            filler=FILLER_RULE)
        if s.get("id") == "book":
            from .figure_budget import BOOK_CAP_NOTE             # noqa: PLC0415
            sys_prompt += "\n\nTHE BOOK'S CAP: " + BOOK_CAP_NOTE.format(
                cap=section_figure_cap("book", cadence))
    # THE COMPARISON VOCABULARY IN THE FRAME (W-1.1 item 1.0e), as T3.4a carried
    # the banned list: the book's comparisons are written as an excess.
    if s.get("id") == "book":
        sys_prompt += EXCESS_FRAME
    if opens:
        # The tables print BELOW the opener; the shared rule says above.
        sys_prompt = sys_prompt.replace("printed ABOVE your paragraph",
                                        "printed BELOW your paragraph")
        sys_prompt += opener_mod.frame_note(cad, s["depth"])
    return sys_prompt


BUDGETED_FRAME_NOTE = (
    "\n\nYOUR FIGURES ARE IN YOUR DATA: `figures_you_may_cite` holds every figure "
    "this paragraph may cite -- at most {cap} -- each exactly as the section's "
    "tables print it; copy them verbatim. Anything under 'In the tables (do not "
    "enumerate)' is printed below your paragraph: never list it or quantify it. "
    "{filler}")
# THE COMPARISON VOCABULARY (W-1.1 item 1.0e): the rule excess_faults enforces,
# stated in the frame so a retry is not the first the writer hears of it.
EXCESS_RULE = ("a comparison of the book's return with a benchmark's -- Book Z, "
               "cash, 60/40 -- that carries a figure is written as an EXCESS: "
               "\"an excess of +0.8 points over cash\" or \"+0.8 points relative "
               "to cash\"; never \"the book against cash\", \"vs\", \"beat\" or "
               "\"trailed\" with a figure")
EXCESS_FRAME = f"\n\nCOMPARISONS: {EXCESS_RULE}."


# THE PARENT'S FRAME OFFERS ONLY WHAT IT MAY CITE (T3.4). Three dry runs cited 9 to
# 21 figures in the parent sections through three retries; instruction did not
# hold. A parent's data is now figure_budget.parent_frame: the cap's worth of its
# largest moves and every other series by name only. This note tells the writer
# how to read that frame.
PARENT_FRAME_NOTE = (
    "\n\nYOUR FIGURES ARE IN YOUR DATA: `figures_you_may_cite` holds the figures "
    "this paragraph may cite -- at most {cap} -- each exactly as its table prints "
    "it; copy them verbatim. The series under 'In the tables (do not enumerate)' "
    "are printed in the tables beneath: do not list them and do not quantify "
    "them. " + "{filler}")
# NO FILLER (W-1.1 item 1.0d). The 9 Oct dry run turned the also-moved names into
# sentences that say nothing ("the 10-year, 30-year and 2-year all moved
# alongside..."). The frame bans the form; filler_faults withholds it.
FILLER_RULE = ("Never write a sentence that only says other series moved: no "
               "\"X, Y and Z also moved\", \"all moved\", \"moved alongside\", "
               "\"moved through the week\", and no list of three or more series "
               "names without a figure among them.")
# The tape's levels (T3.4b): the close and the Weekly only.
TAPE_LEVEL_CADENCES = ("daily", "weekly")
TAPE_LEVEL_NOTE = (
    "\n\nLEVELS YOU MAY CITE: `levels_you_may_cite` holds the tape's levels, each by "
    "its label and value exactly as listed, with its status; they count inside the "
    "same cap as the moves. Say a level held or broke only as its status says.")


def is_parent(s: dict, cadence: str = "daily") -> bool:
    from . import figure_budget                                 # noqa: PLC0415
    return figure_budget.is_parent(s, cadence_of(cadence).get("figure_budget_parents"))


def parent_frame_note(cadence: str = "daily", sid: Optional[str] = None) -> str:
    from . import cadence as cadence_mod                        # noqa: PLC0415
    return PARENT_FRAME_NOTE.format(
        cap=cadence_mod.figure_word(section_figure_cap(sid, cadence)).lower(),
        filler=FILLER_RULE)


def section_figure_cap(sid: Optional[str], cadence: str = "daily") -> int:
    """The figures one section's paragraph may cite at `cadence`: its override
    under `figure_budget_sections` (T3.4c), else the cadence's cap."""
    from . import figure_budget                                 # noqa: PLC0415
    return figure_budget.section_cap(sid, cadence_of(cadence))[0]


# THE FOUR FRAMES THE BUDGET DID NOT COVER (W-1.1 item 1.0a): on the Weekly the
# read, Mechanics, What doesn't fit and Ahead get a budgeted frame each. The 9 Oct
# dry run cited 15, 12, 7 and 7 figures in them against six.
BUDGETED_FRAMES = {"weekly": ("mechanics", "misfit", "ahead", "book")}


def _groups(sid: str, ed: dict, cadence: str) -> Optional[list]:
    """The figure groups a section's count treats as one (W-1.1a item 2): the
    Book Z line, in the book, wherever the book's frame is budgeted."""
    if sid != "book" or sid not in BUDGETED_FRAMES.get(cadence, ()):
        return None
    from .figure_budget import book_groups                      # noqa: PLC0415
    return book_groups(ed) or None


def section_slice(s: dict, ed: dict, cadence: str = "daily") -> dict:
    """What a section's writer is handed: a parent's budgeted frame, one of the
    four other budgeted frames, or the section's slice."""
    from . import figure_budget                                 # noqa: PLC0415
    cad = cadence_of(cadence)
    if is_parent(s, cadence):
        from . import cadence as cadence_mod                    # noqa: PLC0415
        # T3.4b: the close's and the Weekly's tape keep their levels, counted
        # inside the cap; the Monthly's tape is unchanged.
        lv = (figure_budget.tape_levels(s, ed)
              if s.get("id") == "tape" and cadence in TAPE_LEVEL_CADENCES else None)
        cap, per_block = figure_budget.section_cap(s.get("id"), cad)
        return figure_budget.parent_frame(s, ed, cap, cad["period"], cad.get("column"),
                                          levels=lv, per_block=per_block)
    if s.get("id") in BUDGETED_FRAMES.get(cadence, ()):
        cap = section_figure_cap(s.get("id"), cadence)
        return figure_budget.FRAMES[s["id"]](s, ed, cap, cad["period"])
    return _slice(s, ed)


def runaway(chars: float) -> int:
    """A ceiling as a RUNAWAY GUARD (D19/D20, 24 Oct 2026): the depth's old
    ceiling doubled, so a reply that merely runs long prints in full, and never
    above RUNAWAY_CEILING, under the model call's output cap
    (narrative.MAX_TOKENS, about 8,000 characters), so no reply is cut off by the
    provider mid-sentence. It catches a reply that lost the thread; it is not a
    reading budget."""
    return int(min(chars * RUNAWAY_SCALE, RUNAWAY_CEILING))


def section_max_chars(s: dict, cadence: str = "daily") -> int:
    """The section's runaway guard at `cadence` (not a style rule)."""
    return runaway(MAX_CHARS.get(s["depth"], 900) * float(cadence_of(cadence)["chars_scale"]))


def read_prompt(cadence: str = "daily", base=None) -> str:
    """The read's system prompt at `cadence`."""
    if base is None:
        from daily_cascade import narrative as base             # noqa: PLC0415
    sp = stack_system_prompt(base) + READ_RULES.format(period=cadence_of(cadence)["period"])
    sp += (CADENCE_NOTES.get(cadence, {}).get("read", "")
           if cadence == "weekly" else "")
    if cadence in READ_FRAME_CADENCES:
        sp += READ_FRAME_NOTE.format(
            cap=read_figure_cap(cadence), filler=FILLER_RULE)
    # W-1.1 items 1.0e and 1.6: the comparison vocabulary and the connectors, in
    # the frame rather than first heard in a retry.
    sp += EXCESS_FRAME + COINCIDENCE_FRAME
    # W-1.3a item 3.0: on a cadence with an opener The read takes the shape too,
    # at its depth's band (its claim line stays under 90 characters).
    return sp + opener_mod.frame_note(cadence_of(cadence), READ_DEPTH)


def read_figure_cap(cadence: str = "daily") -> int:
    """The figures The read may cite in all: its override under
    `figure_budget_sections`, else the cadence's cap (six)."""
    return section_figure_cap("read", cadence)


# THE READ'S OWN FRAME (W-1.1 item 1.0a), on the Weekly: the sections' claims with
# their figures masked, and the figures it may cite -- the five lines' worth --
# ranked across the edition. The 9 Oct dry run's read cited 15.
READ_FRAME_CADENCES = ("weekly",)
READ_FRAME_NOTE = (
    "\n\nYOUR FIGURES ARE IN YOUR DATA: `figures_you_may_cite` holds every figure "
    "The read may cite -- at most {cap} in all -- each exactly as its section's "
    "table prints it, with the section it comes from. The sections' claims are "
    "given with their figures masked, for what each section says; never copy one. "
    "{filler}")
# COINCIDENCE, NOT CAUSATION (W-1.1 item 1.6): the read states what happened
# alongside what, never why.
CONNECTORS = ("alongside", "coincided with", "the same session as")
COINCIDENCE_FRAME = (
    "\n\nCOINCIDENCE, NEVER CAUSE: when two things happened together, join them "
    "only with \"alongside\", \"coincided with\" or \"the same session as\". Never "
    "\"because\", \"on the back of\", \"in response to\", \"reacting to\", "
    "\"driven by\" or \"due to\" in your own voice; a quoted source's words are "
    "its own, inside quotation marks.")


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
    depth_of = {s["id"]: (READ_DEPTH if s["id"] == "read" else s.get("depth"))
                for s in ed["sections"]}

    def run(sid: str, payload: dict, system: str, max_chars: int) -> dict:
        """One audited draft; if the audit withholds it, ONE revision (W8-1):
        the same payload, the draft, the failing rule and span, fix that and
        change nothing else; a second failure withholds with the second reason.
        A fault (the API, the payload guard) is not retried: the reason is not
        the prose's to fix (Reader's Guide 5.3). Both attempts are logged."""
        def call(note: Optional[str]) -> dict:
            if note is None:
                return attempt(sid, payload, system, max_chars)
            # THE RETRY MAY KEEP A REPEATED SENTENCE (T2.5 item 4): the code
            # check after the prose withholds it in the later section, so a Read
            # that repeats one sentence is not lost whole.
            return attempt(sid, payload, system + note.replace(
                "YOUR PREVIOUS DRAFT WAS", "YOUR PREVIOUS DRAFT OF THIS SECTION WAS", 1),
                max_chars, dup_ok=True)
        return audit_retry.run(call, report=cadence, section=sid,
                               retryable=lambda r: not not_retried(r))

    def attempt(sid: str, payload: dict, system: str, max_chars: int,
                dup_ok: bool = False) -> dict:
        try:
            from altdata import model_meter  # noqa: PLC0415
            with model_meter.scope(section=sid):
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
                      + (book_window_faults(text, ed) if sid == "book" else [])
                      + na_signed_zero(text)
                      + outlook_misprints(text, outlooks or [], venue_percents(ed))
                      + (level_status_faults(text, lstatus, lrows)
                         if sid in ("tape", "read") else [])
                      + figure_faults(text, read_figure_cap(cadence) if sid == "read"
                                      else section_figure_cap(sid, cadence),
                                      _groups(sid, ed, cadence))
                      + filler_faults(text, filler_names(payload))
                      # THE FLAG WORDS (brief v2 section 4; 6b part 2): pinned,
                      # held, amplified and dampened only where a named
                      # session's flag is True. The close has no scored session
                      # at prose time, so it carries none.
                      + (dealer_flag_faults(text, ed) if sid == "mechanics" else [])
                      + tail_faults(text, stored_tails(ed))
                      # THE OPENER'S SHAPE (W-1.3a item 3.0): in band, one
                      # Takeaway, last, carrying no figure.
                      + opener_mod.faults(text, cad, depth_of.get(sid))
                      # W-1.3c items 5 and 2 on a cadence with an opener: the
                      # first sentence is the finding, and no sentence restates
                      # the terms box.
                      + (opener_mod.finding_faults(text) + opener_mod.terms_faults(text)
                         if opener_mod.band(cad, depth_of.get(sid)) else [])
                      # THE DIRECTION AUDIT (W-1.1a item 3) and the stance and
                      # level-word rules (item 4).
                      + direction.faults(text, direction.edition_moves(
                          ed, None if sid == "read" else sid,
                          cad.get("column") or "Week"))
                      + readability.stance_faults(text)
                      # NO SENTENCE TWICE (T2.5 item 4): The read is written
                      # last, over the sections' claims, so it is the one held
                      # to them; what survives the retry is withheld where it
                      # repeats (readability.withhold_duplicates).
                      + ([f"repeats a section's sentence: '{x[:80]}'" for x in
                          readability.duplicates_of(text,
                                                    readability.section_sentences(ed))]
                         if sid == "read" and not dup_ok else []))
        if faults:
            # The printed line keeps the first four; the retry hears them all.
            return {"state": "tape_rules", "published": False,
                    "reason": "withheld: " + "; ".join(faults[:4]),
                    "retry_reason": "withheld: " + "; ".join(faults),
                    "rejected_text": text}
        if not r.published:
            return {"state": r.state, "published": False,
                    "reason": r.withheld_note() or r.reason,
                    "rejected_text": getattr(r, "rejected_text", None)}
        # A DIRECTIONAL VERB CARRIES THE SIGN (W-1.1a item 4): "fell -3 bp"
        # prints "fell 3 bp", after every audit, and the rewrite is counted.
        text, n_unsigned = readability.unsign_after_verbs(text)
        return {"state": "published", "published": True, "text": text,
                "model": r.model, "unsigned_rewrites": n_unsigned}

    for s in ed["sections"]:
        if s["id"] == "read":
            continue
        # EMPTY MEANS ONE LINE (T2.5 item 5): no new facts, no model call.
        if s.get("empty"):
            results[s["id"]] = {"state": "empty", "published": False}
            continue
        paras = DEPTH_PARAGRAPHS.get(s["depth"], "0")
        res = run(s["id"], section_slice(s, ed, cadence), section_prompt(s, cadence, base),
                  section_max_chars(s, cadence))
        results[s["id"]] = res
        if res.get("published"):
            sents = _sentences(res["text"].split("\n\n")[0])
            s["claim"] = sents[0] if sents else res["text"]
            rest = res["text"][len(s["claim"]):].strip()
            # D19/D20 (24 Oct 2026): nothing is cut for length, so a section
            # asked for its claim alone (`paras` "0") still prints the rest of
            # an audited reply in full; the prompt's shape is a target.
            s["paragraphs"] = [re.sub(r"\s+", " ", rest)] if rest else []
            if rest and paras == "0":
                s["over_target"] = True
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
    if cadence in READ_FRAME_CADENCES:
        # THE READ'S BUDGETED FRAME (W-1.1 item 1.0a): claims masked, the
        # figures it may cite ranked across the edition, the week by day's
        # largest sessions only, and the press's attributions as theirs.
        from . import figure_budget                             # noqa: PLC0415
        rp = figure_budget.read_frame(ed, read_figure_cap(cadence), cad["period"])
    elif cadence == "weekly":
        # THE WEEK BY DAY (T2.2 item 3): the opening reads from The read's own
        # table, and a press attribution is the outlet's, never ours.
        rp["week_by_day"] = read.get("table")
        rp["press_attributions"] = [i["text"] for i in read["items"]
                                    if i["key"].startswith("read:attr")]
    res = run("read", rp, read_sys, runaway(int(cad["read_chars"])))
    results["read"] = res
    if res.get("published"):
        sents = _sentences(res["text"])
        read["claim"] = sents[0] if sents else res["text"]
        read["paragraphs"] = [" ".join(sents[1:])] if len(sents) > 1 else []
    else:
        read["withheld"] = res.get("reason")
    ed["prose"] = {k: {kk: v.get(kk) for kk in ("state", "published", "reason",
                                                 "rejected_text", "attempts",
                                                 "first_reason", "unsigned_rewrites")}
                   for k, v in results.items()}
    ed["unsigned_rewrites"] = sum(int(v.get("unsigned_rewrites") or 0)
                                  for v in results.values())
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

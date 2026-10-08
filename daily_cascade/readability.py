"""
The readability pass on every stacked report. (T2.5, ruled 5 Oct 2026, eleven items)

    from daily_cascade import readability as rd

ONE FACT, ONCE, IN A FIXED ORDER. Every section of the daily close and the Weekly
prints, in this order and no other: its claim line, its table(s), its chart(s),
ONE paragraph of at most 120 words citing at most six figures, and its footnote.
The figures live in the tables; the paragraph interprets them and never re-lists
them. Nothing prints as a bullet list. A section with no new facts prints its
footnote alone and makes no model call.

What this module owns, all of it code:

  figures / figure_count    what counts as a figure in a paragraph (item 1)
  mark_empty                a section with no new facts, and its one line (item 5)
  read_duplicates /         a sentence in another section that repeats The read
  withhold_duplicates       is withheld there, with its reason (item 4)
  finalize                  one paragraph, at most 120 words, per section (item 2);
                            the Monthly's allowance from its cadence (T2.6)
  polish / polish_edition   plurals by count, dates in prose as "28 Sep", "±"
                            never "+-", the true minus sign (item 6)
  stamp_et, reading_minutes the header's timestamp and reading time (items 6-7),
                            every cadence's, against reading_target
  subject                   the email subject carries The read's claim (item 8)
  pm_table                  prediction markets as one table (item 9)
  pdf_bytes                 the PDF, from the same HTML, with print CSS (item 11)

The renderer (stack_render.py) and the prose (stack_prose.py) call into this; the
gate is tools/validate_readability.py.
"""

from __future__ import annotations

import base64
import datetime as dt
import difflib
import math
import re
from typing import Any, Optional
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

PARAGRAPH_WORDS = 120
PARAGRAPH_FIGURES = 6
SUBJECT_CLAIM_CHARS = 90
MAX_TABLE_COLUMNS = 6
PDF_MAX_BYTES = 5 * 1024 * 1024
WORDS_PER_MINUTE = 250
SECONDS_PER_CHART = 20

READERS_GUIDE = "The Reporting System: A Reader's Guide"
READERS_GUIDE_PATH = "docs/whitepapers/reporting-system-whitepaper.md"

# THE STANDING NOTES THAT LEFT THE BODY (item 3). Each was a sentence about the
# system's own method -- how a count is read, why an empty table is not broken --
# printed to a reader who wanted the market. They live in the glossary now.
STANDING_NOTES = [
    {"term": "figures and odds",
     "text": "every figure is read from the store, the register or the ledger, and "
             "none is a recommendation; prediction-market odds are the markets' own "
             "prices, and every probability the reports state is a ledger entry."},
    {"term": "◆",
     "text": "marks a line whose figures changed since the prior edition of the same "
             "report."},
]


# ---------------------------------------------------------------------------
# 6. Formatting
# ---------------------------------------------------------------------------
def plural(n: Any, word: str, many: Optional[str] = None) -> str:
    """'1 session', '4 charts', '0 decisions'. Counts print with thousands
    separators; a float count prints as given."""
    try:
        one = float(n) == 1
    except (TypeError, ValueError):
        one = False
    num = f"{n:,}" if isinstance(n, int) else f"{n:g}" if isinstance(n, float) else str(n)
    return f"{num} {word if one else (many or word + 's')}"


def prose_date(iso: str, year: Optional[int] = None) -> str:
    """'2026-09-28' -> '28 Sep'; the year only when it is not the edition's."""
    d = dt.date.fromisoformat(str(iso)[:10])
    return f"{d.day} {d:%b}" + ("" if year in (None, d.year) else f" {d.year}")


def stamp_et(iso: Optional[str]) -> str:
    """An instant as the header prints it: 'Sun 4 Oct, 05:04 ET'."""
    if not iso:
        return "time not recorded"
    t = dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    t = t.astimezone(ET)
    return f"{t:%a} {t.day} {t:%b}, {t:%H:%M} ET"


def minutes_of(hours: Optional[float]) -> int:
    return int(round(float(hours or 0) * 60))


# A date inside a URL or a timestamp is left alone; one standing in prose is not.
_ISO = re.compile(r"(?<![\w/.:=-])(\d{4})-(\d{2})-(\d{2})(?![\w/:=]|-\w)")
_PLURAL = re.compile(r"(\d[\d,]*(?:\.\d+)?)(\s+(?:[A-Za-z'-]+\s+){0,2}?)"
                     r"([A-Za-z]+)\(s\)")
_PLURAL_BARE = re.compile(r"\b([A-Za-z]+)\(s\)")
_ASCII_MINUS = re.compile(r"(?<![\w.)/\-−])-(?=\d)")
_IES = {"story": "stories", "entry": "entries", "party": "parties"}


def _pl(word: str, n: Optional[float]) -> str:
    if n is not None and n == 1:
        return word
    return _IES.get(word, word + "s")


def polish(text: Optional[str], year: Optional[int] = None,
           dates: bool = True) -> Optional[str]:
    """Item 6 over one string: plurals by count, '±' never '+-', the true minus
    sign, and -- outside tables -- ISO dates as '28 Sep'."""
    if not text or not isinstance(text, str):
        return text

    def num(m: re.Match) -> str:
        try:
            n = float(m.group(1).replace(",", ""))
        except ValueError:
            n = None
        return f"{m.group(1)}{m.group(2)}{_pl(m.group(3), n)}"
    out = _PLURAL.sub(num, text)
    out = _PLURAL_BARE.sub(lambda m: _pl(m.group(1), None), out)
    out = out.replace("+-", "±").replace("+/-", "±")
    out = _ASCII_MINUS.sub("−", out)
    if dates:
        out = _ISO.sub(lambda m: prose_date(m.group(0), year), out)
    return out


def _polish_table(t: Optional[dict]) -> None:
    if not t:
        return
    t["columns"] = [polish(c, dates=False) for c in t.get("columns") or []]
    t["rows"] = [[polish(v, dates=False) if isinstance(v, str) else v for v in r]
                 for r in t.get("rows") or []]


def polish_edition(ed: dict, charts: Optional[dict] = None) -> dict:
    """Every code-written and model-written string of an edition, in place."""
    year = None
    try:
        year = dt.date.fromisoformat(str(ed.get("session"))[:10]).year
    except ValueError:
        pass
    P = lambda x: polish(x, year)                               # noqa: E731
    ed["changed_since"] = [P(x) for x in ed.get("changed_since") or []]
    for s in ed.get("sections") or []:
        for k in ("claim", "legend", "table_note", "empty_note", "withheld"):
            s[k] = P(s.get(k))
        s["paragraphs"] = [P(x) for x in s.get("paragraphs") or []]
        s["not_tracked"] = [P(x) for x in s.get("not_tracked") or []]
        s["notes"] = [P(x) for x in s.get("notes") or []]
        for it in s.get("items") or []:
            it["text"] = P(it["text"])
        _polish_table(s.get("table"))
        for t in s.get("tables") or []:
            _polish_table(t)
        for ss in s.get("subsections") or []:
            for k in ("paragraph", "table_note", "title"):
                ss[k] = P(ss.get(k))
            ss["lines"] = [P(x) for x in ss.get("lines") or []]
            ss["not_tracked"] = [P(x) for x in ss.get("not_tracked") or []]
            _polish_table(ss.get("table"))
            _polish_more(ss, P)
    # THE DETAIL BLOCKS (T2.6): the close's state and contradiction tables, the
    # Monthly's record -- their notes and lines are code-written prose too.
    for d in ed.get("detail") or []:
        d["notes"] = [P(x) for x in d.get("notes") or []]
        d["lines"] = [P(x) for x in d.get("lines") or []]
        _polish_table(d.get("table"))
        for t in d.get("tables") or []:
            _polish_table(t)
        _polish_more(d, P)
        for ss in d.get("subsections") or []:
            ss["lines"] = [P(x) for x in ss.get("lines") or []]
            _polish_table(ss.get("table"))
            _polish_more(ss, P)
    for c in (charts or {}).values():
        if c.get("caption"):
            c["caption"] = P(c["caption"])
        if c.get("unavailable"):
            c["unavailable"] = P(c["unavailable"])
    return ed


def _polish_more(b: dict, P) -> None:
    """What a Monthly block may carry beyond the close's and the Weekly's: its
    own paragraphs, notes and "not yet tracked", and further tables -- polished
    where the block carries them, and never added where it does not. A block's
    reading `entries` are STORED TEXT and are not touched (T2.7)."""
    for k in ("paragraphs", "notes", "not_tracked"):
        if k in b:
            b[k] = [P(x) for x in b.get(k) or []]
    for t in b.get("tables") or []:
        _polish_table(t)


def stored_words(ed: dict) -> int:
    """Words of STORED TEXT the edition prints verbatim -- each reading entry's
    summary, or its one line where it has no summary (T2.7, the Monthly's
    Reading chapter). A reader reads them, so they count in the reading time;
    they are not this edition's prose, so never in the word budget and never
    cut. An empty section prints none."""
    n = 0
    for s in ed.get("sections") or []:
        if s.get("empty"):
            continue
        for b in [s] + list(s.get("subsections") or []):
            for e in b.get("entries") or []:
                n += len(str(e.get("summary") or e.get("line") or "").split())
    return n


def reading_minutes(ed: dict, charts: Optional[int] = None) -> int:
    """Prose words at 250 a minute plus 20 seconds a chart, rounded up; at
    least one minute. The words are the edition's prose (stack.edition_words:
    every section and any detail block) and the stored text it prints
    (stored_words, T2.7); `charts` defaults to the edition's count. One
    estimate for every cadence (T2.6)."""
    from .stack import edition_words                            # noqa: PLC0415
    if charts is None:
        charts = int(ed.get("chart_count") or 0)
    return max(1, math.ceil((edition_words(ed) + stored_words(ed)) / WORDS_PER_MINUTE
                            + charts * SECONDS_PER_CHART / 60.0))


def reading_target(cadence: str) -> Optional[int]:
    """The cadence's reading-time target in minutes (config
    `reading_targets_minutes`): daily 5, Weekly 20, Monthly 40."""
    from .cadence import get                                    # noqa: PLC0415
    return get(cadence).get("reading_target_minutes")


# ---------------------------------------------------------------------------
# 1. What counts as a figure
# ---------------------------------------------------------------------------
# NAMES THAT CARRY DIGITS ARE NOT FIGURES: "the 10-year", "the 20-day average",
# "S&P 500", "2s10s", "Nasdaq-100", a date. Each is removed before counting.
_NOT_FIGURES = [
    re.compile(r"S&P\s?500|Russell\s?2000|Nasdaq-100|Dow\s?30", re.I),
    re.compile(r"\b\d+(?:[.,]\d+)?\s?-\s?(?:year|month|week|day|session|minute|hour|"
               r"quarter)s?(?:-[a-z]+)?\b", re.I),
    re.compile(r"\b\d+s\d+s\b", re.I),
    re.compile(r"\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
               r"(?:\s\d{4})?\b"),
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{1,2}"
               r"(?:,?\s\d{4})?\b"),
    re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b"),
    re.compile(r"\b(?:19|20)\d{2}\b(?!\s?(?:%|bp|pts))"),
    re.compile(r"\b(?:Q[1-4]|H[12]|RTAT10|W\d+|C\d)\b"),
    re.compile(r"\b10[–-]90%"),
]
_FIG = re.compile(r"(?<![\w.])[+\-−±]?\$?\d[\d,]*(?:\.\d+)?"
                  r"(?:st|nd|rd|th)?(?:\s?(?:%|bp\b|bps\b|pts\b|points\b|tn\b|bn\b|"
                  r"k\b|x\b))?")


def figures(text: Optional[str]) -> list[str]:
    """The figures a paragraph cites, in order, each once."""
    t = text or ""
    for rx in _NOT_FIGURES:
        t = rx.sub(" ", t)
    seen, out = set(), []
    for m in _FIG.finditer(t):
        f = m.group(0).strip().replace("−", "-")
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def figure_count(text: Optional[str]) -> int:
    return len(figures(text))


def _figure_core(f: str) -> str:
    return re.sub(r"[^\d.]", "", f).rstrip(".")


def table_figures(s: dict) -> set:
    """The numeric cores of every figure a section's tables print."""
    out: set = set()
    tables = [s.get("table")] + [ss.get("table") for ss in s.get("subsections") or []]
    for t in tables:
        for r in (t or {}).get("rows") or []:
            for v in r:
                for f in figures(str(v)) + [str(v)]:
                    c = _figure_core(f)
                    if c:
                        out.add(c)
    return out


def printable_items(s: dict) -> list[dict]:
    """ONE FACT, ONCE (item 1): the section's code-written lines that still
    print. An item hidden by its section, a ':none' placeholder (it is the empty
    note), or an item whose every figure already sits in the section's tables is
    data only -- printing it would say the table twice."""
    if not s.get("print_items", True):
        return []
    have = table_figures(s)
    out = []
    for it in s.get("items") or []:
        if it.get("show") is False or str(it.get("key", "")).endswith(":none"):
            continue
        figs = [_figure_core(f) for f in figures(it.get("text"))]
        figs = [f for f in figs if f]
        if figs and have and all(f in have for f in figs):
            continue
        out.append(it)
    return out


# ---------------------------------------------------------------------------
# 5. Empty means one line
# ---------------------------------------------------------------------------
def has_facts(s: dict) -> bool:
    if (s.get("table") or {}).get("rows"):
        return True
    for ss in s.get("subsections") or []:
        if (ss.get("table") or {}).get("rows") or ss.get("lines"):
            return True
    return any(it.get("show") is not False and not str(it.get("key", "")).endswith(":none")
               for it in s.get("items") or [])


def mark_empty(sections: list[dict], period: str = "session") -> None:
    """A section that collapsed, or carries no fact at all, is EMPTY: it prints
    its footnote alone and makes no model call. The Read is never empty -- it is
    written over the other sections."""
    for s in sections:
        if s["id"] == "read":
            s["empty"] = False
            continue
        if s.get("collapsed"):
            since = s.get("unchanged_since")
            try:
                since = prose_date(since) if since else None
            except ValueError:
                pass
            s["empty"] = True
            s["empty_note"] = f"Unchanged since {since}." if since else "Unchanged."
        elif not has_facts(s):
            none = next((it["text"] for it in s.get("items") or []
                         if str(it.get("key", "")).endswith(":none")), None)
            s["empty"] = True
            s["empty_note"] = none or f"Nothing new this {period}."
        else:
            s["empty"] = False


# ---------------------------------------------------------------------------
# 4. No sentence twice
# ---------------------------------------------------------------------------
def sentences(text: Optional[str]) -> list[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text or "") if x.strip()]


def _norm(s: str) -> str:
    s = s.lower().replace("−", "-").replace("’", "'")
    s = re.sub(r"[^\w%$+\-. ]", " ", s)
    return re.sub(r"\s+", " ", s).strip(" .")


def same_sentence(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    return (min(len(na), len(nb)) >= 30
            and difflib.SequenceMatcher(None, na, nb).ratio() >= 0.85)


def read_sentences(ed: dict) -> list[str]:
    r = next((s for s in ed.get("sections") or [] if s["id"] == "read"), {})
    return [x for t in [r.get("claim")] + list(r.get("paragraphs") or [])
            for x in sentences(t)]


def duplicates_of(text: str, others: list[str]) -> list[str]:
    """The sentences of `text` that repeat one of `others`."""
    return [x for x in sentences(text) if any(same_sentence(x, o) for o in others)]


def section_sentences(ed: dict) -> list[str]:
    """Every sentence the non-Read sections print -- what The read is held to."""
    out = []
    for s in ed.get("sections") or []:
        if s["id"] == "read" or s.get("empty"):
            continue
        for t in [s.get("claim")] + list(s.get("paragraphs") or []):
            out += sentences(t)
    return out


def withhold_duplicates(ed: dict) -> list[dict]:
    """Item 4. A sentence of another section that repeats The read is withheld
    THERE -- The read is first in reading order, so the later one is the copy --
    and the section's footnote says why."""
    read = read_sentences(ed)
    log = []
    if not read:
        ed["duplicates"] = log
        return log
    for s in ed.get("sections") or []:
        if s["id"] == "read" or s.get("empty"):
            continue
        if s.get("claim") and duplicates_of(s["claim"], read):
            log.append({"section": s["id"], "where": "claim", "sentence": s["claim"]})
            s["claim"] = None
            s.setdefault("notes", []).append(
                "The claim line repeated The read and was withheld.")
        paras = []
        for p in s.get("paragraphs") or []:
            keep = []
            for x in sentences(p):
                if any(same_sentence(x, o) for o in read):
                    log.append({"section": s["id"], "where": "paragraph",
                                "sentence": x})
                else:
                    keep.append(x)
            if len(keep) < len(sentences(p)):
                n = len(sentences(p)) - len(keep)
                s.setdefault("notes", []).append(
                    f"{plural(n, 'sentence')} repeated The read and "
                    f"{'was' if n == 1 else 'were'} withheld.")
            if keep:
                paras.append(" ".join(keep))
        s["paragraphs"] = paras
    ed["duplicates"] = log
    return log


# ---------------------------------------------------------------------------
# 2. One paragraph, at most 120 words (per cadence, T2.6)
# ---------------------------------------------------------------------------
def _cut(para: str, cap: int) -> tuple[str, bool]:
    """`para` cut at a sentence boundary to `cap` words; (text, was it cut)."""
    from .stack import words                                    # noqa: PLC0415
    if words(para) <= cap:
        return para, False
    keep: list[str] = []
    for x in sentences(para):
        if keep and words(" ".join(keep + [x])) > cap:
            break
        keep.append(x)
    return " ".join(keep), True


def _guard(paras: list, limit: Optional[int], cap: int) -> tuple[list[str], bool]:
    """At most `limit` paragraphs (None: any number), each cut to `cap` words."""
    kept = [p for p in paras or [] if p and p.strip()]
    trimmed = limit is not None and len(kept) > limit
    if limit is not None:
        kept = kept[:limit]
    out = []
    for p in kept:
        p, cut = _cut(p, cap)
        trimmed = trimmed or cut
        if p:
            out.append(p)
    return out, trimmed


def finalize(ed: dict, cadence: str = "daily") -> dict:
    """The paragraph guard, from the cadence's config (`cadences:`): how many
    paragraphs a section keeps, how many words each may run to, and whether a
    sub-section keeps its own. The prompt asks for the shape; this is the guard.

    The close and the Weekly: ONE paragraph per section, cut at a sentence
    boundary to 120 words, and no sub-section paragraph -- the section's one
    paragraph follows its charts (T2.5 item 2). The Monthly: its paragraphs and
    its sub-sections' kept, each cut to the section's depth allowance."""
    from .cadence import get, paragraph_cap                     # noqa: PLC0415
    from .stack import edition_words                            # noqa: PLC0415
    cad = get(cadence)
    limit = cad.get("paragraphs")
    for s in ed.get("sections") or []:
        cap = paragraph_cap(cad, s.get("depth"))
        for ss in s.get("subsections") or []:
            ss.pop("paragraph", None)
            if not cad.get("subsection_paragraphs"):
                continue
            if ss.get("paragraphs"):
                ss["paragraphs"], cut = _guard(ss["paragraphs"], None, cap)
                if cut:
                    ss["trimmed"] = s["trimmed"] = True
        if s.get("empty"):
            s["paragraphs"] = []
            continue
        paras, cut = _guard(s.get("paragraphs") or [], limit, cap)
        if cut:
            s["trimmed"] = True
        s["paragraphs"] = paras
    ed["words"] = edition_words(ed)
    return ed


# ---------------------------------------------------------------------------
# 8. The subject line
# ---------------------------------------------------------------------------
def short_claim(claim: Optional[str], limit: int = SUBJECT_CLAIM_CHARS) -> str:
    c = re.sub(r"\s+", " ", claim or "").strip()
    if len(c) <= limit:
        return c
    cut = c[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def subject(report: str, when: str, ed: dict, dry_run: bool = False) -> str:
    """'Weekly — w/e 2 Oct — <The read's claim, at most 90 characters>'."""
    read = next((s for s in ed.get("sections") or [] if s["id"] == "read"), {})
    claim = short_claim(read.get("claim"))
    out = f"{report} — {when}" + (f" — {claim}" if claim else "")
    return ("[DRY RUN] " if dry_run else "") + out


# ---------------------------------------------------------------------------
# 9. Prediction markets, one table
# ---------------------------------------------------------------------------
VENUES = ("kalshi", "polymarket")


def _pct(p: Optional[float]) -> str:
    return "—" if p is None else f"{round(p * 100):.0f}%"


def _pts(v: Optional[float]) -> Optional[str]:
    if v is None:
        return None
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{abs(v):.1f}"


def _change_cell(by_venue: dict) -> str:
    parts = [_pts(by_venue.get(v)) for v in VENUES]
    if not any(parts):
        return "—"
    return " / ".join(p or "—" for p in parts) + " pts"


def pm_table(pmb: Optional[dict], window: str = "5s") -> dict:
    """Item 9: item · Kalshi · Polymarket · change over the window · note. The
    note carries a venue's legs-sum flag and odds outside 10-90%. Kalshi's change
    is printed first, Polymarket's second, in the columns' order."""
    from .stack import _watch_cfg, side_rows                    # noqa: PLC0415
    label = "Week change" if window == "5s" else "Session change"
    cols = ["Item", "Kalshi", "Polymarket", label, "Note"]
    rows: list[list] = []
    if not pmb:
        return {"columns": cols, "rows": rows}
    lo, hi = pmb.get("legs_sum_band") or [0.95, 1.05]
    key = f"change_{window}_points"
    try:
        from altdata.prediction_markets import classify_fomc     # noqa: PLC0415
    except Exception:                                           # noqa: BLE001
        classify_fomc = None
    odds = pmb.get("fomc_odds") or {}
    fomc_rows = ((pmb.get("watch") or {}).get("fomc_decision") or [])
    for d in sorted(odds)[:4]:
        by_v = odds[d]
        sums = {v: sum((o or {}).values()) for v, o in by_v.items()}
        for side in ("hold", "hike", "cut"):
            probs = {v: (by_v.get(v) or {}).get(side) for v in VENUES}
            if max((p or 0) for p in probs.values()) < 0.05:
                continue
            ch: dict = {}
            for r in fomc_rows:
                if not classify_fomc or r.get(key) is None:
                    continue
                dd = str(r.get("decision_date") or "")[:10]
                try:
                    near = abs((dt.date.fromisoformat(dd)
                                - dt.date.fromisoformat(d)).days) <= 2
                except ValueError:
                    near = False
                if near and classify_fomc(r.get("question") or "",
                                          r.get("outcome") or "") == side:
                    ch[r["venue"]] = (ch.get(r["venue"]) or 0) + r[key]
            note = []
            for v in VENUES:
                if v in sums and not lo <= sums[v] <= hi:
                    note.append(f"{v.title()} legs sum to {round(sums[v] * 100):.0f}%")
            if any(p is not None and not 0.1 <= p <= 0.9 for p in probs.values()):
                note.append("outside 10–90%")
            rows.append([f"FOMC {d}: {side}", _pct(probs.get("kalshi")),
                         _pct(probs.get("polymarket")), _change_cell(ch),
                         "; ".join(dict.fromkeys(note)) or "—"])
    wcfg = _watch_cfg()
    for wid, wrows in (pmb.get("watch") or {}).items():
        if wid == "fomc_decision" or not wrows:
            continue
        w = wcfg.get(wid) or {}
        name = str(w.get("label") or wid)
        name = name[0].upper() + name[1:]
        picked = side_rows(wrows, w)
        if w.get("compare") is False:
            for v, r in sorted(picked.items()):
                q = str(r.get("question") or "")
                q = q if len(q) <= 70 else q[:69].rsplit(" ", 1)[0] + "…"
                rows.append([f"{name}: \"{q}\"",
                             _pct(r["probability"]) if v == "kalshi" else "—",
                             _pct(r["probability"]) if v == "polymarket" else "—",
                             _change_cell({v: r.get(key)}),
                             "outside 10–90%" if r.get("bias_zone") else "—"])
            continue
        side = w.get("side") or "Yes"
        rows.append([f"{name} ({side})",
                     _pct((picked.get("kalshi") or {}).get("probability")),
                     _pct((picked.get("polymarket") or {}).get("probability")),
                     _change_cell({v: r.get(key) for v, r in picked.items()}),
                     "outside 10–90%" if any(r.get("bias_zone")
                                             for r in picked.values()) else "—"])
    return {"columns": cols, "rows": rows}


def pm_outages(pmb: Optional[dict]) -> list[str]:
    from .stack import _venue_name                              # noqa: PLC0415
    return [f"{_venue_name(v)}: nothing stored since {info.get('as_of') or 'never'}"
            for v, info in ((pmb or {}).get("venues") or {}).items()
            if info.get("outage")]


# ---------------------------------------------------------------------------
# 11. The PDF
# ---------------------------------------------------------------------------
PAGE_SIZE = "Letter"
PRINT_CSS = """
@page { size: %(size)s; margin: 16mm 14mm 18mm 14mm;
  @bottom-center { content: "Page " counter(page) " of " counter(pages);
                   font-family: Helvetica, Arial, sans-serif; font-size: 8.5pt;
                   color: #6b7785; } }
body { margin: 0; }
figure, img, svg { break-inside: avoid; page-break-inside: avoid; }
tr { break-inside: avoid; page-break-inside: avoid; }
h1, h2, h3 { break-after: avoid; page-break-after: avoid; }
div { max-width: none !important; }
"""


def pdf_html(html: str, inline_images: Optional[list] = None) -> str:
    """The emailed HTML as a print document: each cid: chart replaced by its own
    PNG as a data URI, so the PDF carries exactly what the email shows."""
    body = html
    for cid_, png in inline_images or []:
        uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        body = body.replace(f"cid:{cid_}", uri)
    return ("<!doctype html><html><head><meta charset=\"utf-8\"><style>"
            + PRINT_CSS % {"size": PAGE_SIZE} + "</style></head><body>"
            + body + "</body></html>")


def pdf_bytes(html: str, inline_images: Optional[list] = None
              ) -> tuple[Optional[bytes], str]:
    """(pdf, detail). Never raises: a PDF that cannot be built leaves the email
    and the archive exactly as they were, and says why."""
    try:
        import weasyprint                                       # noqa: PLC0415
    except Exception as exc:                                    # noqa: BLE001
        return None, f"WeasyPrint unavailable ({type(exc).__name__}: {exc})"[:300]
    try:
        pdf = weasyprint.HTML(string=pdf_html(html, inline_images)).write_pdf()
    except Exception as exc:                                    # noqa: BLE001
        return None, f"PDF render failed ({type(exc).__name__}: {exc})"[:300]
    if len(pdf) > PDF_MAX_BYTES:
        return None, (f"PDF is {len(pdf):,} bytes, over the {PDF_MAX_BYTES:,}-byte "
                      f"limit; not attached")
    return pdf, f"{len(pdf):,} bytes"

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
                        ledger entry (rule 6; 1.3 rule 3)

A section that fails any of them is withheld alone, with its reason; the items
and table beneath it still print.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from altdata import levels as levels_mod

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
the daily close, in a desk's register. Every other rule above still holds -- every
figure from the data given, signs and percentile ordinals copied from their
_signed and _ordinal fields, no recommendation.

THE SECTION: {title}. Its depth today is {depth}{why}.

SHAPE. Your FIRST SENTENCE is the section's claim line: the one thing this section
says about the session, with its figure. {body} At most {words} words in all.
No headings, no bullets, no bold,
no tables -- the section's table is printed beside your text.

THE TAPE'S RULES:
1. Frames in order: the session first, then the day, then where it sits in the week.
2. A level is named by its label and value exactly as the data lists it ("the
   20-day average at 652.10"); never name a level the data does not list.
3. A move carries its sign and size, copied from its _signed form.
4. Co-movement, never motive. "The long end led: 30-year +9 bp against 2-year
   +2 bp" is allowed; "because", "driven by", "on fears of" are not. A cause is
   named only when a stored event coincides, as "on the day of the CPI release".
5. Say a level "held" or "broke" only when its status in the data says so.
6. A probability appears only as an outlook's, copied with its horizon.
7. No adjective does a number's work: no "plunged", "soared", "massive" without
   the figure in the same sentence.
8. Short declarative sentences; one idea per paragraph; the figure in the
   sentence, not in a parenthesis after it.
Never write about the report itself: no "the data", "the payload", "this section".
The word "because" is refused anywhere, whatever it joins.
"Gamma" beside a state word means the gamma DIAL; for one symbol write its net
GEX ("QQQ's net GEX is positive"), never "QQQ is in positive gamma".
Never write the session's date or weekday: the header carries it. Any other
date only as given (2026-10-02).
Name each level with its own market, one at a time; never "respectively".
Never compute a count, a difference or a ratio: copy the one the data carries.
"""

READ_RULES = """

THIS OVERRIDES THE ONE-PARAGRAPH FRAMING ABOVE. Write THE READ: the five lines
that matter about the session, as ONE paragraph of exactly five sentences, most
important first, each with its figure. Draw only on the section claims and items
given. Every other rule above still holds; no recommendation; a probability only
as an outlook's; no motive words; never write about the report itself.
The word "because" is refused anywhere. "Gamma" beside a state word means the
gamma DIAL; for one symbol write its net GEX. Never write the session's date
or weekday. A level is named with the market it belongs to, one at a time.
"""


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
    for s in _sentences(text):
        for w in st.get("intensity_words") or []:
            if re.search(rf"\b{re.escape(w)}\b", s, re.I) and not re.search(r"\d", s):
                out.append(f"'{w}' with no figure in its sentence")
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


def outlook_misprints(text: str, outlooks: list[dict]) -> list[str]:
    ok = {round(o["probability"] * 100) for o in outlooks
          if o.get("state") == "computed" and o.get("ledger_id")}
    return [f"{m.group(1)}% is not an outlook in the ledger"
            for m in _ODDS.finditer(text or "") if round(float(m.group(1))) not in ok]


def _slice(s: dict, ed: dict) -> dict:
    return {"section": s["title"], "depth": s["depth"],
            "depth_reason": s.get("depth_reason"), "session": ed["session"],
            "items": [i["text"] for i in s["items"]], "table": s.get("table"),
            # The bar-completeness counts stay out: they are about the feed, and
            # prose given them writes about the feed. Its gaps are in not_tracked.
            "data": {k: v for k, v in (s.get("data") or {}).items()
                     if k != "intraday"},
            "not_tracked": s.get("not_tracked")}


def write(ed: dict, *, market_states: Optional[dict] = None, client=None,
          model: Optional[str] = None, outlooks: Optional[list] = None) -> dict:
    """Fill each section's claim and paragraphs; then The read. Never raises."""
    from daily_cascade import narrative as base                  # noqa: PLC0415
    from altdata import bars as bars_mod                         # noqa: PLC0415
    cfg = bars_mod.load_config()
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    lstatus = (tape.get("data") or {}).get("level_status") or {}
    lrows = (tape.get("data") or {}).get("levels") or []
    results: dict[str, dict] = {}

    def run(sid: str, payload: dict, system: str, max_chars: int) -> dict:
        try:
            r = base.generate(payload, model=model, client=client,
                              system_prompt=system, max_chars=max_chars,
                              one_paragraph=False, citable_ids=[],
                              unit_constants=UNIT_CONSTANTS,
                              market_states=market_states)
        except Exception as exc:                                # noqa: BLE001
            return {"state": "fault", "published": False,
                    "reason": f"FAULT {type(exc).__name__}: {exc}"}
        text = r.text if r.published else None
        faults = []
        if text:
            faults = (style_faults(text, cfg) + outlook_misprints(text, outlooks or [])
                      + (level_status_faults(text, lstatus, lrows)
                         if sid in ("tape", "read") else []))
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
        if s["collapsed"] and s.get("prior_claim"):
            s["claim"] = s["prior_claim"]
            results[s["id"]] = {"state": "reused", "published": True}
            continue
        paras = DEPTH_PARAGRAPHS.get(s["depth"], "0")
        body = ("Then write {} paragraphs of commentary.".format(paras)
                if paras != "0" else "Write ONLY that one sentence.")
        why = f" ({s['depth_reason']})" if s.get("depth_reason") else ""
        sys_prompt = base.SYSTEM_PROMPT + RULES.format(
            title=s["title"], depth=s["depth"], why=why, body=body,
            words=(cfg.get("depth_words") or {}).get(s["depth"], 35))
        res = run(s["id"], _slice(s, ed), sys_prompt,
                  MAX_CHARS.get(s["depth"], 900))
        results[s["id"]] = res
        if res.get("published"):
            sents = _sentences(res["text"].split("\n\n")[0])
            s["claim"] = sents[0] if sents else res["text"]
            rest = res["text"][len(s["claim"]):].strip()
            s["paragraphs"] = [p.strip() for p in rest.split("\n\n") if p.strip()] \
                if paras != "0" else []
        else:
            s["claim"] = None
            s["withheld"] = res.get("reason")
    # THE READ, over the other sections' claims and items.
    read = next(s for s in ed["sections"] if s["id"] == "read")
    rp = {"session": ed["session"],
          "sections": [{"section": s["title"], "claim": s.get("claim"),
                        "items": [i["text"] for i in s["items"]]}
                       for s in ed["sections"] if s["id"] != "read"],
          "levels": (tape.get("data") or {}).get("levels")}
    res = run("read", rp, base.SYSTEM_PROMPT + READ_RULES, 1600)
    results["read"] = res
    if res.get("published"):
        sents = _sentences(res["text"])
        read["claim"] = sents[0] if sents else res["text"]
        read["paragraphs"] = [" ".join(sents[1:])] if len(sents) > 1 else []
    else:
        read["withheld"] = res.get("reason")
    ed["prose"] = {k: {kk: v.get(kk) for kk in ("state", "published", "reason",
                                                 "rejected_text")}
                   for k, v in results.items()}
    return ed


def prose_levels(text: str, book: dict) -> list[str]:
    """Level labels the prose names that are not in the level list (gate)."""
    known = {lab.lower() for _, lab, _ in levels_mod.labelled(book)}
    out = []
    for _, lab in levels_mod.LEVEL_TYPES:
        if re.search(rf"\b{re.escape(lab)}\b", text or "", re.I) and lab.lower() not in known:
            out.append(lab)
    return out

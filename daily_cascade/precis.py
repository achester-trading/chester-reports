"""
THE PRÉCIS, WRITTEN LAST (W-1.2 items 2.1-2.3 and 2.5; change order of 11 Oct
2026, section 3; the three open points settled 11 Oct: a SECOND PASS over the ten
finished commentaries, six verdict assets, a one-week stance horizon).

    from daily_cascade import precis
    res = precis.write(ed, prior, client=client)     # after stack_prose.write
    precis.apply(ed, res)                            # relevance, terms, the block

WHAT IT READS. The ten section commentaries as they will print -- each section's
claim and paragraph, or the fact that it was withheld -- and the prior edition's
précis from the archive. Never the payload's tables: the précis's figures are the
commentaries' figures, and the union of the figures they cite is its allowed set.

WHAT IT WRITES, in a fixed tagged form the code parses and audits:
  (a) the one tension of the week, and the evidence on each side;
  (b) a verdict for each of six assets -- equities, rates, credit, the dollar,
      commodities, volatility -- each exactly one of up / down / chop /
      transition;
  (c) a confidence line naming the two or three pieces of evidence the verdicts
      rest on;
  (d) "what would change our mind": three or four observables due within the
      coming week, each naming a series and a date or window;
  (e) what changed in the OUTLOOK since the prior edition -- or, with no prior
      précis in the archive, "first edition with a précis" (written by code);
  the stance: P(SPY higher at the next Weekly's close than at this one's),
      graded by Brier (item 2.2; ruling 5 of 11 Oct);
  one relevance sentence per present section (item 2.3, the second design: the
      sections are written first and the précis emits the sentence each opens
      with; the renderer prepends it).

THE AUDIT (the précis's own, not the payload numeral audit): every figure in its
prose is one a commentary cites; the six verdicts in the vocabulary; three or four
observables, each with a series and a window; a probability in (0, 1) on the side
of the equity verdict; a relevance sentence for every present section, with no
figure; the style list. One retry with the faults fed back; then withheld.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Any, Optional

from . import readability

log = logging.getLogger(__name__)

VERDICT_ASSETS = (
    ("equities", "Equities (SPY)", "up is higher prices"),
    ("rates", "Rates (the 10-year yield)", "up is higher yields"),
    ("credit", "Credit (high-yield spreads)", "up is wider spreads"),
    ("dollar", "The dollar (DXY)", "up is a stronger dollar"),
    ("commodities", "Commodities (oil and gold)", "up is higher prices"),
    ("volatility", "Volatility (the VIX)", "up is higher implied volatility"),
)
VERDICTS = ("up", "down", "chop", "transition")
STANCE_SOURCE = "weekly_stance"
DRY_RUN_NAMESPACE = "dryrun."
# weekly-fixes-7 item 7: "archived". The comparison reads the ARCHIVED editions
# (prior_dir), which carry no précis before the first live one; the stance
# ledger's n counts graded stances wherever they were recorded, dry runs
# included (dryrun.weekly_stance). Dry run 7 printed "First edition with a
# précis" beside "p = 0.40 (n=1)": both true, of different stores. The word
# says which store the first line is about, so the two no longer contradict.
FIRST_EDITION = "First archived edition with a précis."
WITHHELD = "(précis withheld — audit)"

# A WINDOW names a date or a span inside the coming week.
_WINDOW = re.compile(
    r"\b(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|"
    r"sep|oct|nov|dec)[a-z]*\b|\d{4}-\d{2}-\d{2}|\bthis week\b|\bthe week\b|"
    r"\bby\b|\bbefore\b|\bthrough\b|\buntil\b|\bnext\b", re.I)

SYSTEM = """You write the PRÉCIS of a weekly market report: its opening page, read
by someone who may read nothing else. You are given the ten section commentaries
exactly as they will print, and the previous edition's précis when there is one.
You never see the report's tables; you write only from the commentaries.

FIGURES. Cite only figures that appear in the commentaries, exactly as they print
them -- `figures_you_may_cite` lists every one. No other number may appear in your
prose: no figure you derive, round, convert or recall. Dates are not figures.

THE STANCE IS GRADED. Your STANCE line is the probability that SPY closes HIGHER at
the next Weekly's week-ending close than at this one's. It is written to a
scoring ledger at publication and graded by Brier score a week from now: 0.50 is
no view; move away from it only as far as the commentaries justify. It must sit on
the side of your equities verdict (above 0.50 for "up", below for "down").

Reply in EXACTLY this form, one item per line, nothing else:
{week}TENSION: <the one tension of the week, one or two sentences>
FOR: <the evidence on one side, one or two sentences>
AGAINST: <the evidence on the other side, one or two sentences>
VERDICT equities: <up|down|chop|transition>
VERDICT rates: <up|down|chop|transition>
VERDICT credit: <up|down|chop|transition>
VERDICT dollar: <up|down|chop|transition>
VERDICT commodities: <up|down|chop|transition>
VERDICT volatility: <up|down|chop|transition>
CONFIDENCE: <one sentence naming the two or three pieces of evidence the verdicts rest on>
CHANGE: <series> | <date or window inside the coming week> | <what it would show>
CHANGE: <series> | <date or window> | <what it would show>
CHANGE: <series> | <date or window> | <what it would show>
{outlook}STANCE: p = 0.xx
{relevance}
Verdict directions: {directions}. "chop" is range-bound without a direction;
"transition" is a market changing regime. Three or four CHANGE lines, each due
within the coming week. Prose only in the free-text fields: no bullets, no
headings, no bold. Coincidence, never cause: write "alongside", never "because"
or "driven by". Never write about this report, its sections or its checks."""
# THE PRÉCIS'S OPENER (W-1.3a item 3.0): the week in one paragraph, in the
# sections' shape, ending in its Takeaway. Printed first; the tension and its two
# sides stay in the reply for the record and the next week's outlook.
# THE TENSION FIRST (W-1.3c item 8). Dry run #6's WEEK paragraph opened on SPY's
# figures -- "SPY rose 1.16% this week and broke its gamma flip at 775.54 ..." --
# and reached the tension three sentences later. The first sentence now states
# the tension in words (the audit allows it one figure at most); the two or three
# figures that carry it follow.
WEEK_LINE = ("WEEK: <the week in ONE paragraph of {lo} to {hi} words, on one line. "
             "Its FIRST sentence states the week's tension in words -- what is "
             "pulling against what -- with at most one figure; then the two or "
             "three figures that carry it, the evidence on each side; each system "
             "term the terms box does not cover explained in plain words where it "
             "first appears; ending with exactly one sentence that begins "
             "\"Takeaway:\" and states the implication for the coming week -- "
             "never a restatement, and with no figure>\n")
WEEK_FIRST_FIGURES = 1
OUTLOOK_LINE = ("OUTLOOK: <what changed in the outlook since the previous précis -- "
                "the view, not the data; one or two sentences>\n")
# THE FINDING FIRST (W-1.3c item 5). The relevance sentence prints first in each
# section's opener, and dry run #6 wrote all of them with the section as subject:
# "The read frames...", "The tape shows...", "Mechanics locates...". It is now
# asked for as the finding, and opener.self_subject withholds the old form.
RELEVANCE_LINE = ("RELEVANCE {sid}: <one sentence: what {title} found, as it bears on "
                  "the tension -- a claim about markets, never with the section or "
                  "the report as its subject; no figures>")


def _norm(f: str) -> str:
    return re.sub(r"\s+", "", str(f).replace("−", "-").lstrip("+")).rstrip(".,;:")


def _figs(text: Optional[str]) -> list[str]:
    return [f for f in readability.figures(text or "") if re.search(r"\d", f)]


# ---------------------------------------------------------------------------
# What it reads
# ---------------------------------------------------------------------------
def commentaries(ed: dict) -> list[dict]:
    """The ten commentaries as they will print: claim and paragraphs, or withheld."""
    out = []
    for s in ed.get("sections") or []:
        text = " ".join(x for x in [s.get("claim")] + list(s.get("paragraphs") or [])
                        if x)
        out.append({"id": s["id"], "section": s.get("title"),
                    "commentary": text or None,
                    "state": ("empty" if s.get("empty") else
                              "withheld" if not text else "published")})
    return out


def allowed_figures(comms: list[dict]) -> list[str]:
    """The union of the figures the commentaries cite, as printed."""
    seen: dict[str, str] = {}
    for c in comms:
        for f in _figs(c.get("commentary")):
            seen.setdefault(_norm(f), f)
    return list(seen.values())


def present(comms: list[dict]) -> list[dict]:
    return [c for c in comms if c["state"] == "published"]


def grader_block(ed: dict) -> Optional[dict]:
    """W8-1b: the grader's table as Ahead prints it -- resolved counts and mean
    Brier by source over four weeks, the total resolved and open, and the coin
    -- so a figure the précis takes from it is in the précis's own block."""
    s = next((x for x in ed.get("sections") or [] if x.get("id") == "ahead"), None)
    gc = ((s or {}).get("data") or {}).get("graded_calls") or {}
    if not gc:
        return None
    return {"since": gc.get("since"), "resolved": gc.get("resolved"),
            "unresolved": gc.get("unresolved"), "coin_brier": gc.get("coin_brier"),
            "by_source": [{"source": r.get("source"), "resolved": r.get("n"),
                           "mean_brier": (None if r.get("mean_brier") is None
                                          else f"{r['mean_brier']:.3f}"),
                           "against_a_coin": (None if r.get("vs_coin") is None
                                              else f"{r['vs_coin']:+.3f}")}
                          for r in gc.get("rows") or []]}


def stance_block(prior: Optional[dict], n: Optional[int]) -> dict:
    """W8-1b: the stance ledger's n (graded stances to date) and the previous
    edition's p."""
    pp = ((prior or {}).get("precis") or {}).get("parsed") or {}
    p = pp.get("stance_p")
    return {"graded_n": n, "previous_p": None if p is None else f"{float(p):.2f}"}


def block_figures(block: Any) -> list[str]:
    """Every figure a block carries, as it prints."""
    out: list[str] = []
    if isinstance(block, dict):
        for v in block.values():
            out += block_figures(v)
    elif isinstance(block, (list, tuple)):
        for v in block:
            out += block_figures(v)
    elif isinstance(block, bool) or block is None:
        pass
    elif isinstance(block, (int, float)):
        out.append(f"{block:g}")
    else:
        out += _figs(str(block))
    return out


def frame(ed: dict, prior: Optional[dict], stance_n: Optional[int] = None) -> dict:
    """THE PRÉCIS'S DATA BLOCK (W8-1b, weekly-fixes-8): the ten commentaries, the
    grader's table, the stance ledger's n and p, and the "Changed since last
    Weekly" box. The figures it may cite are those four and nothing else -- this
    morning's précis cited the grader's 17, which only Ahead's data carried."""
    comms = commentaries(ed)
    pp = ((prior or {}).get("precis") or {}).get("parsed")
    grader = grader_block(ed)
    stance = stance_block(prior, stance_n)
    changed = [x for x in ed.get("changed_since") or [] if isinstance(x, str)]
    seen: dict[str, str] = {_norm(f): f for f in allowed_figures(comms)}
    for f in block_figures([grader, stance, changed]):
        seen.setdefault(_norm(f), f)
    return {"week_ending": ed.get("week_ending"),
            "commentaries": comms,
            "graded_calls": grader,
            "stance_ledger": stance,
            "changed_since_last_weekly": changed,
            "figures_you_may_cite": list(seen.values()),
            "previous_precis": ({k: pp.get(k) for k in ("tension", "verdicts",
                                                         "stance_p", "change")}
                                if pp else None)}


def system_prompt(fr: dict) -> str:
    rel = "\n".join(RELEVANCE_LINE.format(sid=c["id"], title=c["section"])
                    for c in present(fr["commentaries"]))
    b = week_band()
    return SYSTEM.format(
        week=WEEK_LINE.format(lo=b[0], hi=b[1]) if b else "",
        outlook=OUTLOOK_LINE if fr.get("previous_precis") else "",
        relevance=rel,
        directions="; ".join(f"{a} -- {why}" for a, _, why in VERDICT_ASSETS))


# ---------------------------------------------------------------------------
# What it writes: parse and audit
# ---------------------------------------------------------------------------
def parse(text: str) -> dict:
    out: dict[str, Any] = {"verdicts": {}, "change": [], "relevance": {}}
    for raw in (text or "").splitlines():
        line = raw.strip()
        m = re.match(r"^(WEEK|TENSION|FOR|AGAINST|CONFIDENCE|OUTLOOK):\s*(.+)$", line)
        if m:
            out[m.group(1).lower()] = m.group(2).strip()
            continue
        m = re.match(r"^VERDICT\s+(\w+):\s*(\S+)\s*$", line, re.I)
        if m:
            out["verdicts"][m.group(1).lower()] = m.group(2).lower().strip(".")
            continue
        m = re.match(r"^CHANGE:\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$", line)
        if m:
            out["change"].append({"series": m.group(1).strip(),
                                  "window": m.group(2).strip(),
                                  "what": m.group(3).strip()})
            continue
        m = re.match(r"^STANCE:\s*p\s*=\s*([0-9.]+)\s*$", line, re.I)
        if m:
            try:
                out["stance_p"] = float(m.group(1))
            except ValueError:
                out["stance_p"] = None
            continue
        m = re.match(r"^RELEVANCE\s+(\w+):\s*(.+)$", line)
        if m:
            out["relevance"][m.group(1)] = m.group(2).strip()
    return out


def week_band() -> Optional[tuple[int, int]]:
    """The précis paragraph's band (config `cadences.weekly.opener.precis`)."""
    from . import cadence as cadence_mod, opener                # noqa: PLC0415
    try:
        return opener.precis_band(cadence_mod.get("weekly"))
    except Exception:                                           # noqa: BLE001
        return None


def prose_fields(p: dict) -> list[str]:
    return ([p.get(k) for k in ("week", "tension", "for", "against", "confidence",
                                "outlook")]
            + [c["what"] for c in p.get("change") or []]
            + [c["series"] for c in p.get("change") or []])


def audit(p: dict, fr: dict) -> list[str]:
    faults: list[str] = []
    allowed = {_norm(f) for f in fr["figures_you_may_cite"]}
    for k in ("tension", "for", "against", "confidence"):
        if not p.get(k):
            faults.append(f"no {k.upper()} line")
    if week_band():
        from . import cadence as cadence_mod, opener            # noqa: PLC0415
        if not p.get("week"):
            faults.append("no WEEK paragraph")
        else:
            faults += opener.faults(p["week"], cadence_mod.get("weekly"), "precis",
                                    "the WEEK paragraph")
            # W-1.3c item 8: the tension first, in words.
            first = (opener.sentences(p["week"]) or [""])[0]
            n1 = len(_figs(first))
            if n1 > WEEK_FIRST_FIGURES:
                faults.append(f"the WEEK paragraph's first sentence carries {n1} "
                              f"figures (at most {WEEK_FIRST_FIGURES}): state the "
                              f"tension in words first: '{first[:90]}'")
            faults += opener.finding_faults(p["week"], "the WEEK paragraph")
    if fr.get("previous_precis") and not p.get("outlook"):
        faults.append("no OUTLOOK line though a previous précis exists")
    for a, _, _ in VERDICT_ASSETS:
        v = p["verdicts"].get(a)
        if v not in VERDICTS:
            faults.append(f"verdict for {a} is {v!r}, not one of {', '.join(VERDICTS)}")
    extra = sorted(set(p["verdicts"]) - {a for a, _, _ in VERDICT_ASSETS})
    if extra:
        faults.append(f"verdicts for assets not in the six: {', '.join(extra)}")
    ch = p.get("change") or []
    if not 3 <= len(ch) <= 4:
        faults.append(f"{len(ch)} CHANGE lines; three or four are wanted")
    for c in ch:
        if not c["series"] or not _WINDOW.search(c["window"]):
            faults.append(f"a CHANGE line without a series and a date or window: "
                          f"'{c['series']} | {c['window']}'")
    sp = p.get("stance_p")
    eq = p["verdicts"].get("equities")
    if sp is None or not 0.0 < sp < 1.0:
        faults.append(f"STANCE p = {sp!r} is not a probability in (0, 1)")
    elif (eq == "up" and sp <= 0.5) or (eq == "down" and sp >= 0.5):
        faults.append(f"STANCE p = {sp:.2f} is on the wrong side of the equities "
                      f"verdict '{eq}'")
    bad = sorted({f for t in prose_fields(p) for f in _figs(t)
                  if _norm(f) not in allowed})
    if bad:
        faults.append("figures in no block of the précis's data: " + ", ".join(bad[:8])
                      + " -- cite only figures_you_may_cite, exactly as printed")
    want = [c["id"] for c in present(fr["commentaries"])]
    missing = [s for s in want if not p["relevance"].get(s)]
    if missing:
        faults.append("no RELEVANCE sentence for: " + ", ".join(missing))
    from . import opener as opener_mod                          # noqa: PLC0415
    for sid, t in p["relevance"].items():
        if _figs(t):
            faults.append(f"the RELEVANCE sentence for {sid} carries a figure")
        # W-1.3c items 5 and 2: the section's first printed sentence.
        faults += opener_mod.finding_faults(t, f"the RELEVANCE sentence for {sid}")
        faults += opener_mod.terms_faults(t)
    try:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        from . import stack_prose as sp_mod                     # noqa: PLC0415
        cfg = bars_mod.load_config()
        for t in prose_fields(p) + list(p["relevance"].values()):
            faults += sp_mod.style_faults(t or "", cfg) + sp_mod.id_faults(t or "")
    except Exception:                                           # noqa: BLE001
        log.warning("précis style audit unavailable", exc_info=True)
    return faults


# ---------------------------------------------------------------------------
# The call
# ---------------------------------------------------------------------------
def _call(fr: dict, system: str, client, model: Optional[str]) -> str:
    from . import narrative as base                             # noqa: PLC0415
    prompt = base.build_prompt(fr, None)
    kwargs: dict = {"model": model or base.DEFAULT_MODEL, "max_tokens": base.MAX_TOKENS,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                    "thinking": {"type": "disabled"}}
    from altdata import model_meter                             # noqa: PLC0415
    with model_meter.scope(section="precis"):
        try:
            resp = model_meter.create(client, **kwargs)
        except TypeError:
            kwargs.pop("thinking")
            resp = model_meter.create(client, **kwargs)
    return "".join(getattr(b, "text", "") for b in resp.content
                   if getattr(b, "type", "") == "text").strip()


from .audit_retry import ATTEMPTS                               # noqa: E402  (W8-1: one revision)


def write(ed: dict, prior: Optional[dict] = None, *, client=None,
          model: Optional[str] = None, stance_n: Optional[int] = None) -> dict:
    """The précis over the finished edition: one draft and, when the audit
    withholds it, ONE revision told the withhold message, the rule behind each
    fault, the failing span and the draft (W8-1; three attempts before). Both
    attempts are logged. Never raises."""
    fr = frame(ed, prior, stance_n)
    if client is None:
        from . import narrative as base                         # noqa: PLC0415
        client, why = base._client()                            # noqa: SLF001
        if client is None:
            return {"state": "unavailable", "published": False, "reason": why,
                    "frame": fr}
    from . import audit_retry                                   # noqa: PLC0415
    system = system_prompt(fr)
    reasons = []
    for attempt in range(1, ATTEMPTS + 1):
        try:
            text = _call(fr, system, client, model)
        except Exception as exc:                                # noqa: BLE001
            return {"state": "call_failed", "published": False, "frame": fr,
                    "reason": f"FAULT {type(exc).__name__}: {exc}", "attempts": attempt}
        p = parse(text)
        faults = audit(p, fr)
        audit_retry.log_attempt("weekly", "precis", attempt, not faults,
                                None if not faults else "withheld: " + "; ".join(faults),
                                None if not faults else text)
        if not faults:
            if not fr.get("previous_precis"):
                p["outlook"] = FIRST_EDITION
            return {"state": "published", "published": True, "parsed": p,
                    "text": text, "frame": fr, "attempts": attempt,
                    "first_reason": reasons[0] if reasons else None}
        reasons.append("withheld: " + "; ".join(faults))
        system = system_prompt(fr) + audit_retry.revision_note(reasons[-1], text)
    return {"state": "audit_failed", "published": False, "frame": fr,
            "reason": reasons[-1], "first_reason": reasons[0], "attempts": ATTEMPTS,
            "rejected_text": text, "reasons": reasons}


# ---------------------------------------------------------------------------
# The stance (item 2.2): the ledger at publication, Brier a week later
# ---------------------------------------------------------------------------
def source_name(dry_run: bool) -> str:
    """A dry run writes under its own namespace, never the live source."""
    return (DRY_RUN_NAMESPACE if dry_run else "") + STANCE_SOURCE


def horizon(ending: str) -> str:
    """The next Weekly's week-ending date: a week on."""
    return (dt.date.fromisoformat(ending) + dt.timedelta(days=7)).isoformat()


def spy_close(st, day: str, cutoff: Optional[str] = None) -> Optional[tuple[str, float]]:
    """SPY's close on the last session on or before `day`."""
    rows = [(str(r["observed_at"])[:10], r["value_num"])
            for r in st.as_of("yfinance.mkt_spy", cutoff)
            if r.get("value_num") is not None and str(r["observed_at"])[:10] <= day]
    return max(rows) if rows else None


def record_stance(res: dict, ending: str, emitted_at: str, db_path: Optional[str],
                  dry_run: bool, base_close: Optional[tuple]) -> Optional[str]:
    """Write the stance to the probability ledger at publication."""
    if not res.get("published"):
        return None
    from altdata import probability_ledger as pl                # noqa: PLC0415
    p = float(res["parsed"]["stance_p"])
    hz = horizon(ending)
    base = (f"{base_close[1]:.2f} on {base_close[0]}" if base_close
            else f"its close on {ending}")
    with pl.ProbabilityLedger(db_path) as led:
        return led.record(
            source=source_name(dry_run),
            claim=f"SPY closes higher at the Weekly of {hz} than at the Weekly of "
                  f"{ending} ({base})",
            probability=p, horizon_date=hz, emitted_at=emitted_at,
            emitted_by="weekly_stack.precis", missing_inputs=[],  # LL-3
            resolution_criterion=(
                f"SPY's daily close (yfinance.mkt_spy) on the last session on or "
                f"before {hz}, against its close on the last session on or before "
                f"{ending}: higher resolves 1; equal or lower resolves 0"))


def grade_stances(db_path: Optional[str], ending: str, st, dry_run: bool) -> list[dict]:
    """When the next Weekly runs: resolve every stance in this namespace whose
    horizon has come, by SPY's close against the base close."""
    from altdata import probability_ledger as pl                # noqa: PLC0415
    out = []
    src = source_name(dry_run)
    with pl.ProbabilityLedger(db_path) as led:
        for r in led.due(ending + "T23:59:59"):
            if r["source"] != src:
                continue
            m = re.search(r"Weekly of (\d{4}-\d{2}-\d{2}) \(", r["claim"])
            if not m:
                continue
            a, b = spy_close(st, m.group(1)), spy_close(st, r["horizon_date"])
            if not a or not b or b[0] <= a[0]:
                continue
            out.append(led.resolve(r["probability_id"], int(b[1] > a[1]),
                                   note=f"SPY {a[1]:.2f} on {a[0]} -> {b[1]:.2f} "
                                        f"on {b[0]}"))
    return out


def graded_n(db_path: Optional[str], dry_run: bool = False) -> int:
    from . import weekly_sections as wsec                       # noqa: PLC0415
    return wsec.graded_count(source_name(dry_run), db_path)


def stance_line(p: float, n: int) -> str:
    return f"SPY higher at the next Weekly: p = {p:.2f} (n={n}, unvalidated)."


# ---------------------------------------------------------------------------
# Applying it to the edition
# ---------------------------------------------------------------------------
def apply(ed: dict, res: dict, n: int = 0) -> None:
    """The précis block, and each present section's relevance sentence."""
    ed["precis"] = {k: res.get(k) for k in ("state", "published", "reason",
                                            "first_reason", "attempts", "parsed",
                                            "rejected_text")}
    if not res.get("published"):
        return
    p = res["parsed"]
    ed["precis"]["stance_line"] = stance_line(p["stance_p"], n)
    for s in ed.get("sections") or []:
        r = p["relevance"].get(s["id"])
        if r and s.get("claim"):
            s["relevance"] = r


def terms_line(ed: dict, enforcement: Optional[dict]) -> Optional[str]:
    """Item 2.5: what the regime band permits, what the book is positioned for,
    and the three observables from the précis's (d) that would make its caution
    wrong. Code-written from the stored band, the book's exposure and the
    précis."""
    p = ((ed.get("precis") or {}).get("parsed")) or {}
    view = (enforcement or {}).get("view") or {}
    rg = view.get("regime") or {}
    band = rg.get("band")
    if band:
        permits = (f"the regime band ({rg.get('regime')}) permits Book A a net beta "
                   f"of {band[0]:g}% to {band[1]:g}%")
    else:
        permits = ("the regime band is not available"
                   + (f" ({rg.get('reason')})" if rg.get("reason") else ""))
    nb = view.get("net_beta_pct")
    if isinstance(nb, (int, float)) and band:
        mid = (band[0] + band[1]) / 2
        lean = ("below the band's midpoint -- cautious" if nb < mid else
                "above the band's midpoint -- leaning in" if nb > mid else
                "at the band's midpoint")
        held = f"the book is positioned at {nb:g}% net beta, {lean}"
    elif isinstance(nb, (int, float)):
        held = f"the book is positioned at {nb:g}% net beta"
    else:
        held = "the book's exposure is not available"
    obs = [f"{c['series']} ({c['window']})" for c in (p.get("change") or [])[:3]]
    wrong = ("its caution would be wrong if these move against it: " + "; ".join(obs)
             if obs else "the précis named no observables this week")
    return f"Stance: {permits}; {held}; {wrong}."


# ---------------------------------------------------------------------------
# The terms box (item 2.6), after the précis, verbatim
# ---------------------------------------------------------------------------
TERMS_BOX = (
    "A contradiction is two markets that normally move together but have diverged; "
    "the z-score says how unusual the gap is (above 2 happens a few times a year) and "
    "the dates say how long it has been open. An exception is a reading at the top or "
    "bottom of its five-year range. The narrative ledger is the list of stories the "
    "market is telling itself; each week the system files new evidence for or against "
    "each one, counted by independent event, so \"4 clusters for, 0 against\" means "
    "four separate pieces of evidence for and none against. Voices are the tracked "
    "officials, strategists and investors; silent means nothing on record this week. "
    "Dealer gamma is the options market's hedging effect: above the flip level, "
    "dealers' hedging damps the index's moves; below it, their hedging amplifies them; "
    "walls are strikes with heavy open interest where the index tends to stall. The "
    "regime is the growth-and-inflation quadrant the economy is in; the Doctrine is "
    "the operator's rulebook; Book A is the paper portfolio whose permitted exposure "
    "depends on the regime. Packets are trade proposals and the sitting is the weekly "
    "review that rules on them. A Brier score measures forecast accuracy: 0 is "
    "perfect, 0.25 is a coin flip. Every classification in this edition is "
    "descriptive and unvalidated until the scorecard has graded it; n is the count "
    "graded so far.")


# The terms the box defines, as the opener frame names them (W-1.3c item 2):
# the writer is told not to define any of them again.
TERM_NAMES = ("a contradiction", "the z-score", "an exception", "the narrative "
              "ledger", "voices", "dealer gamma", "the flip level", "walls",
              "the regime", "the Doctrine", "Book A", "packets", "the sitting",
              "the Brier score")


def subject_claim(ed: dict) -> Optional[str]:
    """W-1.3c item 3: what the email subject carries on an edition with a précis
    -- the précis's Takeaway without its label, else the stance line; never an
    opener sentence. None when neither exists."""
    pr = ed.get("precis") or {}
    week = ((pr.get("parsed") or {}).get("week")) if pr.get("published") else None
    if week:
        from . import opener                                    # noqa: PLC0415
        tk = opener.takeaway(week)
        if tk:
            body = opener._TAKEAWAY_HEAD.sub("", tk).strip()    # noqa: SLF001
            if body:
                return body[0].upper() + body[1:]
    return pr.get("stance_line") or None


def withheld_line(pr: dict) -> str:
    """W8-1c: the précis's withheld line carries its reason, as a section's does
    ("Commentary withheld by the audit: ..."); WITHHELD only when none is kept."""
    why = re.sub(r"^(?:narrative\s+)?withheld:\s*", "", str(pr.get("reason") or ""),
                 flags=re.I).strip()
    return f"Précis withheld by the audit: {why}" if why else WITHHELD


def summary_row(ed: dict) -> Optional[str]:
    """W8-1c: the précis as its own row of the run's stack listing, beside the
    sections', so the operator sees its state and reason without grepping."""
    pr = ed.get("precis") or {}
    if pr.get("state") in (None, "skipped"):
        return None
    flag = ("ok" if pr.get("published") else
            "withheld: " + str(pr.get("reason") or "no reason kept")[:90])
    n = pr.get("attempts")
    return f"    {'precis':<12} {'-':<6} {flag}" + (f"  ({n} attempt(s))" if n else "")


def precis_html(ed: dict) -> str:
    """The edition's opening: the précis, or its withheld note."""
    from .stack_render import CLAIM, H3, PARA, SECTION, esc     # noqa: PLC0415
    pr = ed.get("precis") or {}
    out = [f'<h2 style="{SECTION}" id="precis">The précis</h2>']
    if not pr.get("published"):
        if pr.get("state") in (None, "skipped"):
            return ""
        out.append(f'<p style="{PARA}"><i>{esc(withheld_line(pr))}</i></p>')
        return "".join(out)
    p = pr["parsed"]
    if p.get("week"):
        # W-1.3a item 3.0: the week in one paragraph, its Takeaway in bold.
        from . import opener                                    # noqa: PLC0415
        tk = opener.takeaway(p["week"])
        body = p["week"][: len(p["week"]) - len(tk)].rstrip()             if tk and p["week"].endswith(tk) else p["week"]
        tail = (f' <span class="takeaway"><b>{opener.TAKEAWAY}:</b> '
                f'{esc(opener._TAKEAWAY_HEAD.sub("", tk).strip())}</span>'
                if tk else "")
        out.append(f'<p style="{PARA}" class="opener precis">{esc(body)}{tail}</p>')
    else:
        out.append(f'<p style="{CLAIM}">{esc(p["tension"])}</p>')
        out.append(f'<p style="{PARA}">On one side: {esc(p["for"])} On the other: '
                   f'{esc(p["against"])}</p>')
    # PAGE 1 HOLDS THE PRÉCIS (W-1.3c item 10). Dry run #6's PDF ran the six
    # verdicts as a list, so page 1 filled before the stance line, which sat
    # alone on page 2 ahead of a forced break before the terms box. The verdicts
    # are now a compact three-column grid, the stance prints directly under "What
    # changed in the outlook", and the terms box no longer forces a page.
    cells = [f'{esc(lab)}: <b>{esc(p["verdicts"][a])}</b>'
             for a, lab, _ in VERDICT_ASSETS]
    grid = "".join("<tr>" + "".join(f'<td style="{PARA};padding:1px 12px 1px 0">'
                                    f'{c}</td>' for c in cells[i:i + 3]) + "</tr>"
                   for i in range(0, len(cells), 3))
    out.append(f'<h3 style="{H3}" id="verdicts">Verdicts, the coming week</h3>'
               f'<table style="border-collapse:collapse;margin:0 0 4px 0">{grid}'
               f'</table>')
    out.append(f'<p style="{PARA}">{esc(p["confidence"])}</p>')
    out.append(f'<h3 style="{H3}" id="change">What would change our mind</h3>'
               + "".join(f'<p style="{PARA};margin:0 0 2px 0">· {esc(c["series"])} '
                         f'({esc(c["window"])}): {esc(c["what"])}</p>'
                         for c in p["change"]))
    out.append(f'<h3 style="{H3}" id="outlook">What changed in the outlook</h3>'
               f'<p style="{PARA}" id="stance" class="stance"><b>'
               f'{esc(pr.get("stance_line") or "")}</b></p>'
               f'<p style="{PARA}">{esc(p["outlook"])}</p>')
    return '<div class="precis-page" style="break-inside:auto">' + "".join(out) + "</div>"


def terms_box_html() -> str:
    """The terms box, in full, every week, straight after the précis."""
    from .stack_render import H3, PARA, esc                     # noqa: PLC0415
    # No forced page (W-1.3c item 10): the box follows the précis where it
    # falls, and is kept whole.
    return (f'<div style="break-inside:avoid;page-break-inside:avoid;'
            f'border:1px solid #cbd5e1;padding:10px 14px;margin:16px 0" id="terms">'
            f'<h3 style="{H3}">Terms</h3><p style="{PARA}">{esc(TERMS_BOX)}</p></div>')

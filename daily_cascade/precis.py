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
FIRST_EDITION = "First edition with a précis."
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
TENSION: <the one tension of the week, one or two sentences>
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
OUTLOOK_LINE = ("OUTLOOK: <what changed in the outlook since the previous précis -- "
                "the view, not the data; one or two sentences>\n")
RELEVANCE_LINE = "RELEVANCE {sid}: <one sentence tying {title} to the tension, no figures>"


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


def frame(ed: dict, prior: Optional[dict]) -> dict:
    comms = commentaries(ed)
    pp = ((prior or {}).get("precis") or {}).get("parsed")
    return {"week_ending": ed.get("week_ending"),
            "commentaries": comms,
            "figures_you_may_cite": allowed_figures(comms),
            "previous_precis": ({k: pp.get(k) for k in ("tension", "verdicts",
                                                         "stance_p", "change")}
                                if pp else None)}


def system_prompt(fr: dict) -> str:
    rel = "\n".join(RELEVANCE_LINE.format(sid=c["id"], title=c["section"])
                    for c in present(fr["commentaries"]))
    return SYSTEM.format(
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
        m = re.match(r"^(TENSION|FOR|AGAINST|CONFIDENCE|OUTLOOK):\s*(.+)$", line)
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


def prose_fields(p: dict) -> list[str]:
    return ([p.get(k) for k in ("tension", "for", "against", "confidence", "outlook")]
            + [c["what"] for c in p.get("change") or []]
            + [c["series"] for c in p.get("change") or []])


def audit(p: dict, fr: dict) -> list[str]:
    faults: list[str] = []
    allowed = {_norm(f) for f in fr["figures_you_may_cite"]}
    for k in ("tension", "for", "against", "confidence"):
        if not p.get(k):
            faults.append(f"no {k.upper()} line")
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
        faults.append("figures no commentary cites: " + ", ".join(bad[:8])
                      + " -- cite only figures_you_may_cite, exactly as printed")
    want = [c["id"] for c in present(fr["commentaries"])]
    missing = [s for s in want if not p["relevance"].get(s)]
    if missing:
        faults.append("no RELEVANCE sentence for: " + ", ".join(missing))
    for sid, t in p["relevance"].items():
        if _figs(t):
            faults.append(f"the RELEVANCE sentence for {sid} carries a figure")
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
    try:
        resp = client.messages.create(**kwargs)
    except TypeError:
        kwargs.pop("thinking")
        resp = client.messages.create(**kwargs)
    return "".join(getattr(b, "text", "") for b in resp.content
                   if getattr(b, "type", "") == "text").strip()


def write(ed: dict, prior: Optional[dict] = None, *, client=None,
          model: Optional[str] = None) -> dict:
    """The précis over the finished edition: one audited attempt and one retry
    with the faults fed back. Never raises."""
    fr = frame(ed, prior)
    if client is None:
        from . import narrative as base                         # noqa: PLC0415
        client, why = base._client()                            # noqa: SLF001
        if client is None:
            return {"state": "unavailable", "published": False, "reason": why,
                    "frame": fr}
    system = system_prompt(fr)
    reasons = []
    for attempt in (1, 2):
        try:
            text = _call(fr, system, client, model)
        except Exception as exc:                                # noqa: BLE001
            return {"state": "call_failed", "published": False, "frame": fr,
                    "reason": f"FAULT {type(exc).__name__}: {exc}", "attempts": attempt}
        p = parse(text)
        faults = audit(p, fr)
        if not faults:
            if not fr.get("previous_precis"):
                p["outlook"] = FIRST_EDITION
            return {"state": "published", "published": True, "parsed": p,
                    "text": text, "frame": fr, "attempts": attempt,
                    "first_reason": reasons[0] if reasons else None}
        reasons.append("withheld: " + "; ".join(faults[:6]))
        system = (system_prompt(fr) + "\n\nYOUR PREVIOUS DRAFT WAS WITHHELD BY THE "
                  "AUDIT: " + reasons[-1][:900] + "\nWrite it again, fixing exactly "
                  "that and changing nothing else.")
    return {"state": "audit_failed", "published": False, "frame": fr,
            "reason": reasons[-1], "first_reason": reasons[0], "attempts": 2,
            "rejected_text": text}


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
            emitted_by="weekly_stack.precis",
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
    return f"Terms: {permits}; {held}; {wrong}."


# ---------------------------------------------------------------------------
# The terms box (item 2.6), page 2, verbatim
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


def precis_html(ed: dict) -> str:
    """The edition's opening: the précis, or its withheld note."""
    from .stack_render import CLAIM, H3, PARA, SECTION, esc     # noqa: PLC0415
    pr = ed.get("precis") or {}
    out = [f'<h2 style="{SECTION}" id="precis">The précis</h2>']
    if not pr.get("published"):
        if pr.get("state") in (None, "skipped"):
            return ""
        out.append(f'<p style="{PARA}">{esc(WITHHELD)}</p>')
        return "".join(out)
    p = pr["parsed"]
    out.append(f'<p style="{CLAIM}">{esc(p["tension"])}</p>')
    out.append(f'<p style="{PARA}">On one side: {esc(p["for"])} On the other: '
               f'{esc(p["against"])}</p>')
    out.append(f'<h3 style="{H3}">Verdicts, the coming week</h3><ul>'
               + "".join(f'<li style="{PARA}">{esc(lab)}: {esc(p["verdicts"][a])}</li>'
                         for a, lab, _ in VERDICT_ASSETS) + "</ul>")
    out.append(f'<p style="{PARA}">{esc(p["confidence"])}</p>')
    out.append(f'<h3 style="{H3}">What would change our mind</h3><ul>'
               + "".join(f'<li style="{PARA}">{esc(c["series"])} ({esc(c["window"])}): '
                         f'{esc(c["what"])}</li>' for c in p["change"]) + "</ul>")
    out.append(f'<h3 style="{H3}">What changed in the outlook</h3>'
               f'<p style="{PARA}">{esc(p["outlook"])}</p>')
    out.append(f'<p style="{PARA}"><b>{esc(pr.get("stance_line") or "")}</b></p>')
    return "".join(out)


def terms_box_html() -> str:
    """Page 2: the terms box, in full, every week."""
    from .stack_render import H3, PARA, esc                     # noqa: PLC0415
    return (f'<div style="page-break-before:always;break-before:page;'
            f'border:1px solid #cbd5e1;padding:10px 14px;margin:16px 0" id="terms">'
            f'<h3 style="{H3}">Terms</h3><p style="{PARA}">{esc(TERMS_BOX)}</p></div>')

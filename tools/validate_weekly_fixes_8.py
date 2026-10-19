#!/usr/bin/env python3
"""
WEEKLY-FIXES-8: the fixes from the first live Weekly (18 Oct 2026).

    python tools/validate_weekly_fixes_8.py

A code gate: synthetic fixtures in temporary stores and fake model clients. It
never reads the live store, fetches or calls a model, and renders nothing.

  A  W8-1   THE AUDIT RETRY: a 159-word draft in an 80-150 band is revised once
            and published; a draft that fails twice is withheld with the second
            reason; the revision is told the draft, the failing rule and span;
            the data block is never changed between the two calls; a fault that
            is not the prose's is not retried; both attempts are logged; the
            close's and the anchor's narrative path takes the same retry
  B  W8-2   NUMERAL BINDING: "Technology (XLK) falling 5.52%" (QQQ's figure) and
            "JPY futures ... slipped 1.6 points of open interest" (a z) fail,
            naming both; the right figures pass; a sentence naming no series is
            left to the plain audit; the failure feeds the retry's rule
  C  W8-3   ONE MEETING TEMPLATE: "the 9 December meeting", "the 17 March 2027
            meeting", wherever a meeting is named in prose
  D  W8-5   THE IMPLIED MOVE'S EXPIRY: an after-close event on an expiry day
            reads the next expiry; before the open, its own
  E  W8-6   THE AI CLAUSE: AI names only; TSLA the plain clause
  F  W8-8   DAYS TO COVER'S CHANGE to the level's two decimals; "unch" for zero
  G  W8-9   NO AS-OF AFTER THE EDITION'S SESSION, unless the registry declares
            the series forward-dated (IORB: "effective 19 Oct")
  H  W8-13  THE BUYBACKS' 30-YEAR from the tape, its source dated; FRED's where
            the tape has no point
  I  NOTHING ELSE: no model client built, no network import
"""

from __future__ import annotations

import datetime as dt
import logging
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

TMP = Path(mkdtemp("gate_weekly_fixes_8_"))
LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


_N = 0


def store(rows: list[dict]):
    from altdata import observations
    global _N
    _N += 1
    st = observations.ObservationStore(str(TMP / f"s{_N}.sqlite"))
    st.write_many(rows)
    return st


def row(key, day, value, avail=None, instrument=None):
    return {"registry_key": key, "instrument": instrument, "observed_at": str(day),
            "available_at": avail or f"{day}T21:00:00+00:00", "value": float(value),
            "source": "fixture", "availability_kind": "reconstructed"}


class Captured(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines: list[str] = []

    def emit(self, rec):
        self.lines.append(rec.getMessage())


# ---------------------------------------------------------------------------
def words(n: int, tail: str = "") -> str:
    body = " ".join(["Credit"] + ["spreads"] * (n - 2 - len(tail.split())))
    return f"{body} held. {tail}".strip()


def group_a() -> None:
    head("A. W8-1: THE AUDIT RETRY")
    from daily_cascade import audit_retry, cadence, narrative, opener
    cad = cadence.get("weekly")
    check(opener.band(cad, "medium") == (80, 150),
          "the fixture's band is the Weekly's medium one, 80 to 150 words")
    take = "Takeaway: the credit market is not pricing stress."
    long_draft = words(159 - len(take.split())) + " " + take
    short_draft = words(120 - len(take.split())) + " " + take
    check(opener.words(long_draft) == 159 and opener.words(short_draft) == 120,
          "the drafts run 159 and 120 words")
    data = {"oas": {"label": "EM high-yield OAS", "change_bp": 5}}
    seen: list = []

    def make(obey: bool):
        seen.clear()

        def call(note):
            seen.append({"data": repr(data), "note": note})
            text = long_draft if note is None or not obey else short_draft
            f = opener.faults(text, cad, "medium", "Narratives")
            if f:
                return {"state": "tape_rules", "published": False,
                        "reason": "withheld: " + "; ".join(f), "rejected_text": text}
            return {"state": "published", "published": True, "text": text}
        return call

    cap = Captured()
    lg = logging.getLogger("daily_cascade.audit_retry")
    lg.addHandler(cap)
    lg.setLevel(logging.INFO)
    r = audit_retry.run(make(True), report="weekly", section="narratives",
                        retryable=lambda x: True)
    check(r["published"] and r["attempts"] == 2 and len(seen) == 2,
          f"159 words in an 80-150 band: withheld, revised once, published "
          f"({r['attempts']} attempts)")
    note = seen[1]["note"] or ""
    check("WITHHELD BY THE AUDIT: withheld: Narratives runs 159 words; its band is "
          "80 to 150" in note and "THE OPENER SHAPE" in note
          and "THE FAILING SPAN: the draft as a whole" in note
          and "YOUR DRAFT:\n<<<\n" + long_draft in note
          and "change nothing else" in note,
          "the revision is told the reason, the rule, the span (the draft as a whole "
          "for a length fault) and the draft itself, to fix that and change nothing else")
    check(seen[0]["data"] == seen[1]["data"],
          "the data block is the same on both calls")
    check(sum("attempt 1 of 2 withheld" in x for x in cap.lines) == 1
          and sum("attempt 2 of 2 published" in x for x in cap.lines) == 1
          and any("draft (NOT published)" in x for x in cap.lines),
          "both attempts are in the run log, the withheld draft with them")
    r2 = audit_retry.run(make(False), report="weekly", section="narratives",
                         retryable=lambda x: True)
    check(not r2["published"] and r2["attempts"] == 2 and len(seen) == 2
          and r2["reason"].startswith("withheld: Narratives runs 159 words")
          and r2["first_reason"] == r2["reason"],
          "a draft that fails twice is withheld with the second reason, after one "
          "revision and no third call")
    calls = []

    def faulted(note):
        calls.append(note)
        return {"state": "call_failed", "published": False, "reason": "FAULT x"}
    from daily_cascade import stack_prose
    r3 = audit_retry.run(faulted, report="weekly", section="plumbing",
                         retryable=lambda x: not stack_prose.not_retried(x))
    check(r3["attempts"] == 1 and len(calls) == 1,
          "a failed call is not the prose's to fix: not retried")
    filler = ("withheld: filler: a bare figure with nothing to read it against: "
              "'EM high-yield OAS widened +5 bp'")
    draft = ("High-yield credit was calm. EM high-yield OAS widened +5 bp. "
             "Takeaway: credit is not pricing stress.")
    rn = audit_retry.revision_note(filler, draft)
    check("THE FAILING SPAN:\n- EM high-yield OAS widened +5 bp." in rn
          and "THE FILLER RULE" in rn,
          "Plumbing's filler fault: the failing span is its sentence, with the filler rule")
    check(stack_prose.attempts_of(cad) == 2 == audit_retry.ATTEMPTS
          and stack_prose.attempts_of(cadence.get("daily")) == 2,
          "one draft and one revision at every cadence: the extra cost is one model "
          "call per failed audit, bounded to one")
    # THE NARRATIVE PATH (the closes and the anchors): the real generate and its
    # real numeral audit, a fake client that answers wrong and then right.
    msgs: list = []
    replies = iter(["SPY rose 1.5% on the day.", "SPY rose 1.2% on the day."])

    def create(**kw):
        msgs.append(kw)
        txt = next(replies)
        return types.SimpleNamespace(
            model="fixture-model", stop_reason="end_turn",
            content=[types.SimpleNamespace(type="text", text=txt)],
            usage=types.SimpleNamespace(output_tokens=10))
    client = types.SimpleNamespace(messages=types.SimpleNamespace(create=create))
    nr = audit_retry.generate({"spy": {"symbol": "SPY", "change_pct": 1.2}},
                              report="close", client=client)
    check(nr.published and nr.attempts == 2 and "1.5" in str(nr.first_reason),
          f"the close's narrative: the audit withholds 1.5%, the revision publishes "
          f"({nr.state}, {nr.attempts} attempts)")
    check(len(msgs) == 2 and msgs[0]["messages"] == msgs[1]["messages"]
          and msgs[1]["system"].startswith(msgs[0]["system"])
          and "YOUR DRAFT:" in msgs[1]["system"]
          and "SPY rose 1.5% on the day." in msgs[1]["system"],
          "the retry never changes the data block: the user message is byte for "
          "byte the first call's; only the system prompt carries the revision")
    msgs.clear()
    replies = iter(["SPY rose 1.5%.", "SPY rose 1.6%."])
    nr2 = audit_retry.generate({"spy": {"symbol": "SPY", "change_pct": 1.2}},
                               report="anchor", client=client)
    check(not nr2.published and nr2.attempts == 2 and "1.6" in nr2.reason
          and "1.5" in str(nr2.first_reason),
          "twice wrong: withheld, printing the second reason")
    src = {n: (REPO / "daily_cascade" / n).read_text(encoding="utf-8")
           for n in ("close_report.py", "morning_anchor.py", "precis.py",
                     "stack_prose.py")}
    check("audit_retry.generate(" in src["close_report.py"]
          and "audit_retry.generate(" in src["morning_anchor.py"]
          and "audit_retry.revision_note(" in src["precis.py"]
          and "audit_retry.run(" in src["stack_prose.py"],
          "every report that uses the loop takes it: the stack (Weekly, closes, "
          "Monthly), the précis, the classic close, the morning anchor")
    from daily_cascade import precis
    check(precis.ATTEMPTS == 2, "the précis: one draft and one revision")
    lg.removeHandler(cap)


# ---------------------------------------------------------------------------
READ = {"figures_you_may_cite": [
    {"cite": {"series": "Technology (XLK)", "change_pct": -7.70, "where": "Breadth"}},
    {"cite": {"series": "Nasdaq 100 (QQQ)", "change_pct": -5.52, "where": "The tape"}}]}
POS = {"tff": [{"contract": "JPY", "category": "lev_funds", "net_oi_pct": 23.4,
                "level_z": 0.3, "change_z_4w": -1.6}],
       "table": {"columns": ["Contract", "Trader type", "Net, % of open interest",
                             "Level z, two years", "Four-week change z", "As of"],
                 "rows": [["JPY futures", "Leveraged funds", "+23.4%", "+0.3", "-1.6",
                           "2026-10-13"]]}}


def group_b() -> None:
    head("B. W8-2: NUMERAL BINDING")
    from altdata import numeral_audit as na
    from daily_cascade import opener
    a = na.audit("Technology (XLK) falling 5.52% led the week's losses.", READ)
    check(not a.passed and "5.52% is bound to XLK but belongs to QQQ" in a.reason(),
          f"the Read's case fails, naming both ({a.reason()})")
    b = na.audit("JPY futures positioning slipped 1.6 points of open interest.", POS)
    check(not b.passed and "1.6 is bound to JPY futures but is its four_week_change_z "
          "(a z), not a share of open interest" in b.reason(),
          f"Positioning's case fails: a z is not points of open interest ({b.reason()})")
    for t, p, what in (
            ("Technology (XLK) falling 7.70% led the week's losses.", READ, "XLK's own"),
            ("Technology (XLK) fell 7.70% while the Nasdaq 100 (QQQ) fell 5.52%.", READ,
             "each figure bound to the name nearest it"),
            ("Leveraged funds held 23.4 points of open interest in JPY futures.", POS,
             "the share of open interest"),
            ("JPY futures positioning slipped, its four-week change z at -1.6.", POS,
             "the z called a z")):
        r = na.audit(t, p)
        check(r.passed, f"the right figure passes: {what} ({r.reason()})")
    lv = {"levels": [{"symbol": "SPY", "ma_20d": 515.06},
                     {"symbol": "Y10", "aliases": ["10-year yield"], "week_high": 4.30}]}
    e = na.audit("SPY sat near its 20-day average at 515.06; the 10-year yield held "
                 "under its week high of 4.30.", lv)
    check(e.passed, "a clause ends at a semicolon, and the series named BEFORE a "
                    f"figure wins over one named just after it ({e.reason()[:90]})")
    c = na.audit("Stocks fell 5.52% on the week.", READ)
    check(c.passed and not any(f.bind_conflict for f in c.figures),
          "a sentence with a figure and no series named is left to the plain audit")
    d = na.audit("Technology (XLK) falling 9.99% led.", READ)
    check(not d.passed and not any(f.bind_conflict for f in d.unmatched),
          "a figure in no row fails the plain audit as before, not the binding")
    check(any(r.startswith("THE BINDING RULE") for r in opener.rules_for(a.reason())),
          "the binding's failure text feeds the retry with its own rule")


# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. W8-3: ONE MEETING TEMPLATE")
    from daily_cascade import readability as rd, stack
    for raw, want in (("Odds of a cut at the December 9 Dec meeting rose.",
                       "Odds of a cut at the 9 December meeting rose."),
                      ("the March 17 Mar 2027 meeting", "the 17 March 2027 meeting"),
                      ("a hold at the 2026-12-09 meeting", "a hold at the 9 December meeting"),
                      ("the December 9 meeting", "the 9 December meeting"),
                      ("the December meeting", "the December meeting")):
        got = rd.polish(raw, 2026)
        check(got == want, f"{raw!r} -> {got!r}")
    check(rd.meeting_name("2027-03-17", 2026) == "17 March 2027"
          and rd.meeting_name("2026-12-09", 2026) == "9 December",
          "the template names the year only when it is not the edition's")
    subj = stack.market_subject({"watch_id": "fomc_decision",
                                 "decision_date": "2026-12-09",
                                 "question": "Fed decision in December?",
                                 "outcome": "No change"})
    check("the 9 December meeting" in subj or "9 December" in subj,
          f"the code-written subject uses the template ({subj})")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check('label = f"hold at the {nxt[0]' not in ws and "readability.meeting_name(" in ws,
          "the W7 odds panel's label uses it too")


# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. W8-5: THE IMPLIED MOVE'S EXPIRY")
    from daily_cascade import ahead
    ex = ["2026-10-21", "2026-10-23", "2026-10-30"]
    check(ahead.straddle_expiry(ex, "2026-10-21", "after the close") == "2026-10-23",
          "META, Wed 21 Oct after the close, on an expiry day: the next expiry, 23 Oct")
    check(ahead.straddle_expiry(ex, "2026-10-21", "time not stated") == "2026-10-23"
          and ahead.straddle_expiry(ex, "2026-10-21", "16:05") == "2026-10-23",
          "an unknown time, or one after the close: strictly after the event date")
    check(ahead.straddle_expiry(ex, "2026-10-21", "before the open") == "2026-10-21"
          and ahead.straddle_expiry(ex, "2026-10-21", "07:00") == "2026-10-21",
          "before the open, the event date's own expiry may serve")
    chain = TMP / "chains" / "2026-10-16"
    chain.mkdir(parents=True, exist_ok=True)
    lines = ["expiry,dte,right,strike,bid,ask,last_price,volume,last_trade_date,"
             "fetched_at,spot"]
    for e, (c, p) in (("2026-10-21", (9.9, 9.9)), ("2026-10-23", (20.0, 20.0))):
        for right, mid in (("C", c), ("P", p)):
            lines.append(f"{e},5,{right},700.0,{mid - 0.1},{mid + 0.1},,100,,"
                         f"2026-10-16T20:00:00Z,700.0")
    (chain / "META_200000.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    mv = ahead.implied_move("META", "2026-10-21", "2026-10-16T22:00:00+00:00",
                            TMP / "chains", time="after the close")
    check(mv == "implied move ±5.7% (straddle to 2026-10-23)",
          f"end to end on a fixture chain: the 23 Oct straddle, (20 + 20) / 700 ({mv})")
    row_ = ahead.earnings_row({"symbol": "META", "event": "META earnings",
                               "date": "2026-10-21", "time": "after the close"},
                              ahead.load_config(), "2026-10-16T22:00:00+00:00",
                              TMP / "chains")
    check("straddle to 2026-10-23" in str(row_.get("implied_move")),
          "the Ahead matrix's row carries the release time into the choice")
    import yaml
    rs = yaml.safe_load((REPO / "config" / "reporting_stack.yaml").read_text(
        encoding="utf-8"))
    txt = str(rs)
    check("first expiry strictly after the event date" in txt
          and "first expiry on or after the event" not in txt,
          "the technical appendix line says the same")


# ---------------------------------------------------------------------------
def group_e() -> None:
    head("E. W8-6: THE AI CLAUSE")
    import yaml
    from daily_cascade import ahead
    cfg = ahead.load_config()
    c = cfg["classes"]["earnings_mega"]
    ai = ahead.ai_names(cfg)
    plain = ahead.why_of({"symbol": "TSLA", "cls": "earnings_mega"}, c, ai)
    nv = ahead.why_of({"event": "NVDA earnings", "cls": "earnings_mega"}, c, ai)
    check(plain == "an index-weight leader: its move is the index's move"
          and "AI trade" not in plain,
          f"TSLA, an index-weight leader not in the AI bucket: the plain clause ({plain})")
    check(nv.endswith("its capital spending is the AI trade's"),
          f"NVDA, an AI name: the AI clause ({nv})")
    fcf = yaml.safe_load((REPO / "config" / "ai_fcf.yaml").read_text(encoding="utf-8"))
    check(set(fcf["revision"]["names"]) <= ai and ai - set(fcf["revision"]["names"]) <= {"GOOG"},
          "the Weekly's AI names are the forward-EPS block's own (GOOG beside GOOGL)")
    fake = TMP / "repo"
    (fake / "config").mkdir(parents=True, exist_ok=True)
    (fake / "config" / "ai_buckets.yaml").write_text(
        "buckets:\n  compute: [NVDA, AMD]\n  hyperscalers: [MSFT]\n", encoding="utf-8")
    own = {str(s).upper() for s in (cfg.get("earnings") or {}).get("ai_names") or []}
    check(ahead.ai_names(cfg, fake) == {"NVDA", "AMD", "MSFT"} | own,
          "config/ai_buckets.yaml, where it exists, joins the Weekly's own list "
          "(the chain-2 stitch: GTM-4 names members for the hyperscalers only)")


# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F. W8-8: DAYS TO COVER'S CHANGE")
    from daily_cascade.stack import _change
    base = {"unit": "", "level": 2.41}
    got = [_change({**base, "change": c, "dp": 2}) for c in (-1.27, -0.12, 0.004, 0.5)]
    check(got == ["−1.27", "−0.12", "unch", "+0.50"],
          f"to the level's two decimals; 'unch' for zero ({got})")
    check(_change({**base, "change": -1.27}) == "−1",
          "a series that declares no decimals keeps the old rule")
    src = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check('x["dp"] = 2          # W8-8' in src, "the Weekly's days to cover declares two")


# ---------------------------------------------------------------------------
NOW, THEN = "2026-10-18T09:00:00+00:00", "2026-10-11T09:00:00+00:00"


def group_g() -> None:
    head("G. W8-9: NO AS-OF AFTER THE EDITION'S SESSION")
    from altdata import derived
    from daily_cascade import weekly_stack as ws
    check(ws.edition_session(NOW) == "2026-10-16",
          "the edition of Sunday 18 Oct is of the session of Friday 16 Oct")
    rows = [row("fred.iorb", "2026-10-09", 3.90), row("fred.iorb", "2026-10-16", 3.90),
            row("fred.iorb", "2026-10-19", 3.90, "2026-10-16T21:00:00+00:00"),
            row("fred.sofr", "2026-10-09", 4.10), row("fred.sofr", "2026-10-16", 4.12),
            row("fred.sofr", "2026-10-19", 9.99, "2026-10-16T21:00:00+00:00")]
    with store(rows) as st:
        io = ws.change_over(st, "fred.iorb", NOW, THEN)
        so = ws.change_over(st, "fred.sofr", NOW, THEN)
    check(derived.forward_dated("fred.iorb") and not derived.forward_dated("fred.sofr"),
          "the registry declares IORB forward-dated (its effective day), SOFR not")
    check(io and io.get("effective") and ws.asof_cell(io) == "effective 19 Oct"
          and ws.window(io) == "effective 19 Oct",
          f"IORB dated 19 Oct in the edition of the 16th prints 'effective 19 Oct' "
          f"({ws.asof_cell(io) if io else None})")
    check(so and so["observed_at"] == "2026-10-16" and so["level"] == 4.12
          and not so.get("effective"),
          "an undeclared series dated after the session is read at its newest "
          "observation on or before it")
    cells = [ws.asof_cell(x) for x in (io, so)]
    check(all(c.startswith("effective ") or c <= "2026-10-16" for c in cells),
          f"no as-of later than the session unless declared ({cells})")
    import yaml
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    fd = reg.get("forward_dated") or {}
    check(fd and all(derived.registry_entry(k) for k in fd)
          and all(isinstance(v, str) and len(v) > 20 for v in fd.values()),
          "every forward-dated key is registered and carries its reason")


# ---------------------------------------------------------------------------
def group_h() -> None:
    head("H. W8-13: THE BUYBACKS' 30-YEAR")
    from altdata import batch3
    from daily_cascade import batch3_block as b3
    inst = "Liquidity Support | 10Y to 20Y"
    base = [row(batch3.BUYBACK_KEYS[0], "2026-10-14", 6.0e9, instrument=inst),
            row(batch3.BUYBACK_KEYS[1], "2026-10-14", 5.19e9, instrument=inst),
            row("fred.yield_30y", "2026-10-13", 4.66), row("fred.yield_30y", "2026-10-14", 4.70)]
    tape = [row("yfinance.mkt_tyx", "2026-10-14", 4.70),
            row("yfinance.mkt_tyx", "2026-10-15", 4.75)]
    with store(base + tape) as st:
        ops = batch3.buyback_operations(st, NOW, "2026-10-09", "2026-10-16")
        sub = b3.buyback_subsection(st, NOW, "2026-10-09T09:00:00+00:00")
    o = ops[0] if ops else {}
    check(o.get("y30_next_bp") == 5.0 and o.get("y30_next_day") == "2026-10-15"
          and o.get("y30_source") == "Yahoo Finance",
          f"FRED's leg lags a session; the tape's 30-year reads +5.0 bp to 15 Oct ({o})")
    cell = sub["table"]["rows"][0][-1] if sub.get("table") else None
    check(cell == "+5.0 bp (Yahoo Finance, 15 Oct)",
          f"the cell names its source and its date, not 'not yet stored' ({cell})")
    with store(base) as st:
        o2 = batch3.buyback_operations(st, NOW, "2026-10-09", "2026-10-16")[0]
    check(o2["y30_next_bp"] is None,
          "with neither leg past the operation it is still 'not yet stored'")
    check("Yahoo Finance" in sub["table_note"] and "^TYX" not in sub["table_note"],
          "the note names the tape's source in words, no symbol string")


# ---------------------------------------------------------------------------
def group_j() -> None:
    head("J. W8-1b AND W8-1c: THE PRÉCIS'S BLOCK AND ITS WITHHELD LINE")
    from daily_cascade import precis
    ed = {"week_ending": "2026-10-16",
          "changed_since": ["The book's net beta moved to 0.42 from 0.35."],
          "sections": [
              {"id": "tape", "title": "The tape", "claim": "Stocks fell 2.10% on the week.",
               "paragraphs": []},
              {"id": "ahead", "title": "Ahead", "claim": None, "paragraphs": [],
               "data": {"graded_calls": {"since": "2026-09-18", "resolved": 17,
                                         "unresolved": 5, "coin_brier": 0.25,
                                         "rows": [{"source": "daily_close_outlook",
                                                   "n": 17, "mean_brier": 0.2314,
                                                   "vs_coin": -0.0186,
                                                   "base_rate": True}]}}}]}
    prior = {"precis": {"parsed": {"stance_p": 0.55}}}
    fr = precis.frame(ed, prior, stance_n=3)
    cite = {precis._norm(f) for f in fr["figures_you_may_cite"]}
    check(cite == {"17", "5", "0.25", "0.231", "-0.019", "0.55", "3", "0.42", "0.35",
                   "2.10%"},
          f"the block carries the grader's table, the stance ledger's n and p and "
          f"the changed-since box beside the commentaries ({sorted(cite)[:14]})")
    check(fr["graded_calls"]["by_source"][0]["resolved"] == 17
          and fr["stance_ledger"] == {"graded_n": 3, "previous_p": "0.55"}
          and fr["changed_since_last_weekly"] == ed["changed_since"],
          "each block by name, as the frame hands it to the writer")

    def fig_faults(week: str) -> list[str]:
        p = precis.parse("WEEK: " + week)
        return [f for f in precis.audit(p, fr) if f.startswith("figures in no block")]
    ok = fig_faults("Base-rate outlooks resolved 17 times in four weeks.")
    bad = fig_faults("Base-rate outlooks resolved 19 times in four weeks.")
    check(not ok and bad and "19" in bad[0],
          f"a précis citing the grader's 17 passes; one citing a figure in no block "
          f"fails ({bad[:1]})")
    check(not fig_faults("Stocks fell 2.10% while the book's beta moved to 0.42."),
          "a commentary's figure and the box's still pass")
    pr = {"state": "audit_failed", "published": False, "attempts": 2,
          "reason": "withheld: figures in no block of the précis's data: 19"}
    line = precis.withheld_line(pr)
    check(line == "Précis withheld by the audit: figures in no block of the précis's "
                  "data: 19",
          f"the withheld line carries its reason, as a section's does ({line})")
    html = precis.precis_html({"precis": pr})
    check("Précis withheld by the audit: figures in no block" in html
          and precis.WITHHELD not in html, "and it is the line the edition prints")
    row_ = precis.summary_row({"precis": pr})
    check(row_ and row_.split()[0] == "precis" and "withheld: withheld: figures in no "
          "block" in row_ and "(2 attempt(s))" in row_,
          f"the précis is its own row of the run's stack listing ({row_})")
    check(precis.summary_row({"precis": {"state": "published", "published": True,
                                         "attempts": 1}}).endswith("ok  (1 attempt(s))"),
          "a published précis's row reads ok")
    src = (REPO / "daily_cascade" / "weekly_report.py").read_text(encoding="utf-8")
    check("_precis.summary_row(ed)" in src
          and src.index("_precis.summary_row(ed)") < src.index('for s in ed["sections"]:'),
          "the Weekly's run prints it first in the listing, before the sections")


# ---------------------------------------------------------------------------
def group_i() -> None:
    head("I. NOTHING ELSE")
    check("anthropic" not in sys.modules,
          "no model client was built: every call went to a fake")
    import ast
    src = (REPO / "daily_cascade" / "audit_retry.py").read_text(encoding="utf-8")
    imps = {n.names[0].name if isinstance(n, ast.Import) else (n.module or "")
            for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.Import, ast.ImportFrom))}
    check(not imps & {"requests", "urllib", "http", "socket", "anthropic", "subprocess"},
          f"the retry module imports no network or model library ({sorted(imps)})")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_j, group_i):
        g()
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

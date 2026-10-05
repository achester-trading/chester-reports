#!/usr/bin/env python3
"""
Validation gate for the ten-section stack on the daily close. (reporting-stack T1)

    python tools/validate_stack.py

The brief's section 5, for the daily cadence, on a SYNTHETIC fixture session in a
temporary store -- a code gate never reads the live store, and no figure here is
a real position or a real price:

  A STACK      ten sections in order; an unchanged section collapses to its claim
               line; the plumbing trigger fires on a tier-1 event and on a
               threshold crossing, and stays silent without either.
  B LEVELS     every level named in the prose is in the level list; every level
               drawn is in it; the label audit holds a wrong 20-day value.
  C TAPE       a motive word, an adjective with no figure, an outlook probability
               not in the ledger, and a "held" the level list does not show are
               each withheld; a clean section publishes.
  D CHARTS     C1-C3 render to PNG and SVG; PNG <= 150 KB; the email's Content-ID
               set matches the charts the body references; a chart that cannot
               render prints its reason.
  E INTRADAY   fewer than 90% of the session's bars: "bars incomplete", C1 omitted;
               the bars feed (16:10 eod) retries a missing final bar for five
               minutes and owns the table; the close fetches nothing.
  F BUDGET     an over-budget edition drops low-priority lines and prints
               "(trimmed)" at the section.
  G LEDGER     outlooks are computed from stored closes, recorded before printing,
               recorded once per session, and NOT recorded on a dry run.
  H SCORECARD  the dealer-scorecard row the Monthly will read is stored.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
import sys
import tempfile
import types
from email import message_from_bytes
from email.policy import default as email_default
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0
SESSION = "2026-09-30"          # a Wednesday; the fixture is synthetic


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
def weekdays_back(end: dt.date, n: int) -> list[dt.date]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def seed(db: str, *, bars_5m: int = 78, cpi_today: bool = False,
         y10_jump: float = 0.0) -> dict:
    from altdata import bars as bars_mod, observations, events, session
    import regime
    days = weekdays_back(dt.date.fromisoformat(SESSION), 320)
    with bars_mod.BarStore(db, create=True) as bst:
        rows = []
        for t in bars_mod.tape():
            base = {"y10": 4.0, "y30": 4.5}.get(t["id"], 500.0)
            for k, d in enumerate(days):
                c = base * (1 + 0.04 * math.sin(k / 23.0)) if t["kind"] == "price" \
                    else base + 0.3 * math.sin(k / 23.0)
                o = c * (1 - 0.001) if t["kind"] == "price" else c - 0.01
                rows.append({"instrument": t["id"], "symbol": t["bars"],
                             "interval": "1d", "observed_at": d.isoformat(),
                             "open": o, "high": max(o, c) * 1.002,
                             "low": min(o, c) * 0.998, "close": c, "volume": 1e6,
                             "available_at": f"{d.isoformat()}T21:00:00+00:00"})
        first, _, _ = bars_mod.session_window("spy", SESSION)
        t0 = dt.datetime.fromisoformat(first)
        last_close = next(r["close"] for r in reversed(rows)
                          if r["instrument"] == "spy")
        for k in range(bars_5m):
            px = last_close * (1 + 0.002 * math.sin(k / 6.0))
            rows.append({"instrument": "spy", "symbol": "SPY", "interval": "5m",
                         "observed_at": (t0 + dt.timedelta(minutes=5 * k)).isoformat(),
                         "open": px * 0.9995, "high": px * 1.001, "low": px * 0.999,
                         "close": px, "volume": 1000 + k,
                         "available_at": f"{SESSION}T20:30:00+00:00"})
        bst.write_many([r for r in rows if r["interval"] == "5m"])
    # T2.1: daily frames read the store's daily OHLC, so the fixture's daily
    # bars are written as each tape instrument's `daily` series and its
    # _open / _high / _low beside it; the bars table holds the 5-minute bars only.
    daily_obs = []
    keys = {t["id"]: t.get("daily") for t in bars_mod.tape()}
    for r in rows:
        k = keys.get(r["instrument"])
        if r["interval"] != "1d" or not k:
            continue
        for suf, f in (("", "close"), ("_open", "open"), ("_high", "high"),
                       ("_low", "low")):
            daily_obs.append({"registry_key": k + suf, "instrument": None,
                              "observed_at": r["observed_at"],
                              "available_at": r["available_at"], "value": r[f],
                              "source": "synthetic"})
    with observations.ObservationStore(db) as st:
        st.write_many(daily_obs)
        prev = days[-2].isoformat()
        obs = []
        for key, a, b in (("fred.yield_2y", 3.90, 3.92),
                          ("fred.yield_10y", 4.00, 4.00 + y10_jump),
                          ("fred.yield_30y", 4.50, 4.51),
                          ("fred.hy_oas", 3.00, 3.01),
                          ("fred.breakeven_10y", 2.30, 2.31)):
            for d, v in ((prev, a), (SESSION, b)):
                obs.append({"registry_key": key, "instrument": None,
                            "observed_at": d, "available_at": f"{d}T21:00:00+00:00",
                            "value": v, "source": "synthetic"})
        st.write_many(obs)
        obj = None
        for k, d in enumerate(days[-12:]):
            obj = {"session": d.isoformat(),
                   "computed_at": f"{d.isoformat()}T21:00:00+00:00",
                   "dials": {"gamma": {"state": "negative"}, "vol": {"state": "normal"},
                             "macro": {"state": "mixed"}},
                   "dimensions": {"volatility": {"state": "subdued"}},
                   "contradictions": [{"id": "fixture_pair", "open": k > 6,
                                       "open_state": "open" if k > 6 else "closed",
                                       "magnitude": 1.0 + 0.15 * k,
                                       "threshold_z": 2.0, "persistence_days": max(0, k - 6),
                                       "legs": ["a", "b"]}],
                   "exceptions": []}
            regime.store_object(obj, st)
    if cpi_today:
        with events.EventStore(db) as ev:
            ev.conn.execute(
                "INSERT INTO events (content_hash, type, observed_at, available_at,"
                " ingested_at, source, title, payload) VALUES (?,?,?,?,?,?,?,?)",
                ("fixture-cpi", "release", f"{SESSION}T12:30:00+00:00",
                 f"{SESSION}T12:30:00+00:00", session.utc_iso(), "bls_cpi",
                 "Consumer Price Index -- release date", "{}"))
            ev.conn.commit()
    return {"market_state": obj}


def payload(obj: dict) -> dict:
    from altdata import session
    return {"report": "daily_close", "session": SESSION, "as_of": session.utc_iso(),
            "run_id": "fixture", "tolerance_bps": 25.0, "universe": {},
            "exposure": [{"symbol": "SPY", "spot": 500.0, "net_gex": -1.0e9,
                          "gamma_flip": 505.0, "call_wall": 520.0, "put_wall": 480.0,
                          "max_pain": 500.0, "dollar_gamma_per_1pct": -5.0e9}],
            "pins": [], "pin_hits": {}, "market_state": obj, "what_changed": None,
            "portfolio": {"state": "absent", "reason": "fixture", "positions": [],
                          "account": {}},
            "enforcement": {"state": "ok", "rule_breaks": [], "rule_breaks_total": 0,
                            "view": {"text": ""}},
            "grades": {}, "warnings": [], "method_notes": []}


class Resp:
    def __init__(self, t):
        self.content = [types.SimpleNamespace(type="text", text=t)]
        self.model = "fixture-model"
        self.stop_reason = "end_turn"


def client(replies: dict, calls: list):
    """A model that answers by section title; default: a clean, figure-free line."""
    def create(**k):
        calls.append(k["system"])
        for title, text in replies.items():
            if f"THE SECTION: {title}." in k["system"] or (
                    title == "READ" and "Write THE READ" in k["system"]):
                return Resp(text)
        return Resp("The session left this section's picture where it was.")
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


# ---------------------------------------------------------------------------
# The groups
# ---------------------------------------------------------------------------
def main() -> int:
    from altdata import bars as bars_mod, config, levels as levels_mod, session
    from altdata import probability_ledger as pl
    from daily_cascade import charts as charts_mod, deliver, outlooks
    from daily_cascade import stack as stack_mod, stack_close, stack_prose
    from daily_cascade import stack_render

    print(f"{LINE}\nThe ten-section stack on the daily close (T1) -- fixture "
          f"session {SESSION}\n{LINE}")
    td = tempfile.mkdtemp(prefix="validate_stack_")
    config.COMPUTED_DIR = str(Path(td) / "computed")          # no live profiles
    db = str(Path(td) / "stack.db")
    arch = str(Path(td) / "reports")
    seeded = seed(db)
    p = payload(seeded["market_state"])
    with bars_mod.BarStore(db) as bst:
        book = levels_mod.compute(SESSION, p["exposure"], store=bst)
    spy = next(i for i in book["instruments"] if i["id"] == "spy")
    ma20 = next(lv for lv in spy["levels"] if lv["type"] == "ma_20d")
    calls: list = []
    clean = client({"The tape": f"SPY sat near its 20-day average at "
                                f"{ma20['value']:.2f}.\n\nThe session stayed inside "
                                f"the week's range."}, calls)

    # --- A. THE STACK -----------------------------------------------------------
    print(f"\n{LINE}\nA. THE STACK\n{LINE}")
    out1 = stack_close.produce(p, archive_dir=arch, dry_run=False,
                               client=clean, db_path=db)
    ed1 = out1["edition"]
    ids = [s["id"] for s in ed1["sections"]]
    check(ids == list(stack_mod.SECTION_ORDER),
          f"ten sections in the brief's order ({ids})")
    check(all(s.get("claim") for s in ed1["sections"]),
          "every section opens with a claim line")
    html1 = out1["html_archive"]
    pos = [html1.find(f">{n} &middot; {stack_render.esc(s['title'])}") for n, s in
           enumerate(ed1["sections"], start=1)]
    check(all(x >= 0 for x in pos) and pos == sorted(pos)
          and html1.count("font-style:italic;color:#5a6b7a\">&mdash; ") == 10,
          "and the HTML prints them in that order, as 'number · name — subtitle' "
          "with the subtitle styled apart from the body's bold (T2.2 item 1)")
    check(not any(s["collapsed"] for s in ed1["sections"]),
          "with no prior edition nothing collapses")
    stack_close.save_edition(ed1, SESSION, arch)
    # The SAME session again: everything unchanged against the archived edition.
    p2 = dict(p)
    p2["session"] = (dt.date.fromisoformat(SESSION) + dt.timedelta(days=1)).isoformat()
    prior = json.loads((Path(arch) / stack_close.edition_name(SESSION))
                       .read_text(encoding="utf-8"))
    ed_same = stack_mod.build(p, book, ed1["outlooks"], prior, db)
    mech = next(s for s in ed_same["sections"] if s["id"] == "mechanics")
    check(mech["collapsed"] and mech["unchanged_since"] == SESSION
          and mech["prior_claim"],
          "an unchanged section collapses, citing the edition it is unchanged since "
          "and reusing its claim")
    stack_prose.write(ed_same, client=clean, outlooks=ed1["outlooks"])
    sh = stack_render.section_html(mech, 3, {}, "archive")
    check("(unchanged since" in sh and "<ul" not in sh and "<table" not in sh,
          "and prints its claim line and '(unchanged since ...)' and nothing else")
    check(all(not i["changed"] for s in ed_same["sections"] for i in s["items"]),
          "no item carries a change mark when nothing changed")
    p_moved = json.loads(json.dumps(p))
    p_moved["exposure"][0]["call_wall"] = 525.0
    ed_mv = stack_mod.build(p_moved, book, ed1["outlooks"], prior, db)
    mv = next(s for s in ed_mv["sections"] if s["id"] == "mechanics")
    check(not mv["collapsed"] and any(i["changed"] for i in mv["items"]),
          "a moved call wall un-collapses the section and marks the line with "
          "◆")
    check("◆ " in stack_render.section_html(mv, 3, {}, "archive"),
          "and the mark prints")
    plumb = next(s for s in ed1["sections"] if s["id"] == "plumbing")
    check(plumb["depth"] == "light" and not plumb["depth_reason"],
          "Plumbing stays light with no tier-1 event and no threshold crossing")
    for label, kw, want in (("a CPI release this session", {"cpi_today": True},
                             "Consumer Price Index"),
                            ("a 10-year move of +12 bp", {"y10_jump": 0.12},
                             "yield_10y")):
        db2 = str(Path(td) / f"trig_{len(label)}.db")
        s2 = seed(db2, **kw)
        with bars_mod.BarStore(db2) as bst:
            bk = levels_mod.compute(SESSION, p["exposure"], store=bst)
        e2 = stack_mod.build(payload(s2["market_state"]), bk, [], None, db2)
        pl2 = next(s for s in e2["sections"] if s["id"] == "plumbing")
        check(pl2["depth"] == "deep" and want in (pl2["depth_reason"] or ""),
              f"Plumbing goes deep on {label}, and says so ({pl2['depth_reason']})")
    check("deep: " not in html1.split("Plumbing")[1][:80],
          "the header names no trigger when none fired")

    # --- B. LEVELS ----------------------------------------------------------------
    print(f"\n{LINE}\nB. LEVELS -- one object for the prose and the charts\n{LINE}")
    allprose = " ".join(" ".join([s.get("claim") or ""] + (s.get("paragraphs") or []))
                        for s in ed1["sections"])
    check(not stack_prose.prose_levels(allprose, book),
          "every level the prose names is in the level list")
    listed = {(lv["label"], lv["value"]) for lv in spy["levels"]}
    drawn = [d for c in out1["charts"].values() for d in c.get("drawn") or []]
    check(drawn and all((d["label"], d["value"]) in listed for d in drawn),
          f"every level drawn ({len(drawn)}) is in the level list")
    check(any("20-day average" in (s.get("claim") or "") + " ".join(
        s.get("paragraphs") or []) for s in ed1["sections"] if s["id"] == "tape"),
          "the tape names the 20-day average by its listed label and value")
    from altdata import numeral_audit as na
    na._VOCAB = None
    good = na.audit(f"SPY held its 20-day average at {ma20['value']:.2f}.",
                    {"levels": [spy["row"]]})
    bad = na.audit(f"SPY held its 20-day average at {ma20['value'] + 3:.2f}.",
                   {"levels": [spy["row"], {"symbol": "X", "z": ma20['value'] + 3}]})
    check(good.passed and not bad.passed and "20-day average" in bad.reason(),
          "the label audit covers the new level types: a 20-day printed at another "
          "level's value is withheld")
    check(stack_mod.SECTION_ORDER and levels_mod.status_of(100, 101, {
        "low": 99.9, "high": 102, "close": 101}, 25) == "held"
          and levels_mod.status_of(100, 101, {"low": 98, "high": 102, "close": 99},
                                   25) == "broke"
          and levels_mod.status_of(100, 105, {"low": 104, "high": 106, "close": 105},
                                   25) == "untested",
          "held / broke / untested by the declared rule")
    y10 = next(i for i in book["instruments"] if i["id"] == "y10")
    y10_wh = next(lv["value"] for lv in y10["levels"] if lv["type"] == "week_high")
    rows_all = [i["row"] for i in book["instruments"]]
    al = na.audit(f"SPY sat near its 20-day average at {ma20['value']:.2f}; the "
                  f"10-year yield held under its week high of {y10_wh:.2f}.",
                  {"levels": rows_all})
    check(al.passed, f"a level after an alias ('the 10-year yield ... week high "
                     f"{y10_wh:.2f}') is held to that instrument, not to the last "
                     f"ticker named ({al.reason()[:80]})")
    al2 = na.audit(f"The 10-year yield sat under its week high of "
                   f"{next(lv['value'] for lv in spy['levels'] if lv['type'] == 'week_high'):.2f}.",
                   {"levels": rows_all})
    check(not al2.passed, "and SPY's week high printed as the 10-year's is withheld")
    ls = {i["id"]: [{"label": lv["label"], "value": lv["value"],
                     "status": lv.get("status")} for lv in i["levels"]]
          for i in book["instruments"]}
    ls["spy"] = [dict(lv, status="broke") if lv["label"] == "20-day average" else lv
                 for lv in ls["spy"]]
    ls["qqq"] = [dict(lv, status="held") if lv["label"] == "20-day average" else lv
                 for lv in ls["qqq"]]
    check(not stack_prose.level_status_faults(
              "SPY broke its 20-day average; QQQ held its 20-day average.",
              ls, rows_all)
          and stack_prose.level_status_faults(
              "QQQ broke its 20-day average.", ls, rows_all),
          "held / broke is checked per instrument: QQQ cannot borrow SPY's break")

    # --- C. TAPE RULES --------------------------------------------------------------
    print(f"\n{LINE}\nC. THE TAPE'S RULES\n{LINE}")
    cases = (("motive", "SPY rose because investors cheered the data.", "motive"),
             ("intensity", "SPY plunged into the close.", "no figure"),
             ("odds", "There is a 62% chance that SPY holds the week's low.",
              "62%"),
             ("held", f"SPY broke its 20-day average at {ma20['value']:.2f}.",
              "SPY's 20-day average did not"))
    for label, text, why in cases:
        c2: list = []
        e = stack_mod.build(p, book, ed1["outlooks"], None, db)
        stack_prose.write(e, client=client({"The tape": text}, c2),
                          outlooks=ed1["outlooks"])
        t = next(s for s in e["sections"] if s["id"] == "tape")
        check(t.get("claim") is None and why in str(t.get("withheld")),
              f"{label}: '{text[:48]}' is withheld ({str(t.get('withheld'))[:70]})")
    live1 = [o for o in ed1["outlooks"] if o["state"] == "computed"][:1]
    pct1 = round(live1[0]["probability"] * 100) if live1 else 0
    n1 = live1[0]["n"] if live1 else 0
    check(stack_prose.outlook_misprints("a 62% chance that it holds", ed1["outlooks"])
          and not stack_prose.outlook_misprints(
              f"The base rate for the week's low holding is {pct1}% (n={n1}).", live1),
          "the odds rule itself: a probability that is not a ledgered outlook's is "
          "refused; an outlook's, written as a base rate with its n, passes")
    for bad_line, why in ((f"{pct1}% that the week's low holds.", "without 'base rate'"),
                          (f"The base rate for the week's low holding is {pct1}%.",
                           "without 'base rate' and its n"),
                          (f"We expect the low to hold: the base rate is {pct1}% "
                           f"(n={n1}).", "framed as a view")):
        f = stack_prose.outlook_misprints(bad_line, live1)
        check(any(why in x for x in f),
              f"an outlook's figure is never our view: '{bad_line[:52]}' is refused "
              f"({f[:1]})")
    ok_out = live1[0] if live1 else None
    if ok_out:
        c3: list = []
        e = stack_mod.build(p, book, ed1["outlooks"], None, db)
        line = (f"The base rate for {ok_out['claim']} is "
                f"{round(ok_out['probability'] * 100)}% (n={ok_out['n']}).")
        stack_prose.write(e, client=client({"Ahead": line}, c3),
                          outlooks=ed1["outlooks"])
        a = next(s for s in e["sections"] if s["id"] == "ahead")
        check(a.get("claim") and not a.get("withheld"),
              f"an outlook written as a base rate, with its ledger entry, publishes "
              f"({str(a.get('withheld'))[:60]})")
        item_txt = next(i["text"] for i in a["items"]
                        if i["key"] == f"ahead:outlook:{ok_out['id']}")
        check(item_txt.startswith("The base rate for ") and f"(n={ok_out['n']})"
              in item_txt and ok_out.get("kind") == "base_rate",
              f"and the Ahead line itself reads as a base rate ({item_txt[:70]}...)")
    # T2.1 RULING 3: an audited section retries once with the audit's reason.
    seq = iter(["SPY rose because investors cheered.", "SPY rose on the session."])
    c_r: list = []

    def create_seq(**k):
        c_r.append(k["system"])
        return Resp(next(seq) if "THE SECTION: The tape." in k["system"] else
                    "The session left this section's picture where it was.")
    er = stack_mod.build(p, book, ed1["outlooks"], None, db)
    stack_prose.write(er, client=types.SimpleNamespace(
        messages=types.SimpleNamespace(create=create_seq)), outlooks=ed1["outlooks"])
    tr = next(s for s in er["sections"] if s["id"] == "tape")
    tape_calls = [c for c in c_r if "THE SECTION: The tape." in c]
    check(tr.get("claim") == "SPY rose on the session." and len(tape_calls) == 2
          and "WITHHELD BY THE AUDIT" in tape_calls[1] and "motive" in tape_calls[1]
          and er["prose"]["tape"]["attempts"] == 2,
          "a withheld section retries once with the audit's reason fed back, and "
          "publishes if the retry passes")
    c3b: list = []
    eb = stack_mod.build(p, book, ed1["outlooks"], None, db)
    stack_prose.write(eb, client=client({"The tape": "SPY plunged."}, c3b),
                      outlooks=ed1["outlooks"])
    tb = next(s for s in eb["sections"] if s["id"] == "tape")
    check(tb.get("claim") is None and eb["prose"]["tape"]["attempts"] == 2
          and eb["prose"]["tape"].get("first_reason"),
          "and withholds, as before, if the retry fails too")
    check(len([c for c in calls if "THE SECTION:" in c]) == 9
          and any("Write THE READ" in c for c in calls),
          f"one audited call per section and one for The read "
          f"({len(calls)} calls)")

    # --- D. CHARTS ------------------------------------------------------------------
    print(f"\n{LINE}\nD. CHARTS\n{LINE}")
    ch = out1["charts"]
    for k in ("C1", "C2", "C3"):
        c = ch.get(k) or {}
        check(c.get("png") and c["png"][:4] == b"\x89PNG" and c.get("png_bytes")
              <= charts_mod.MAX_PNG_BYTES and c.get("svg_path")
              and Path(c["svg_path"]).exists(),
              f"{k} renders to PNG ({c.get('png_bytes')} bytes, <= 150 KB) and SVG "
              f"({c.get('caption', c.get('unavailable'))[:60]})")
    body_cids = set(re.findall(r'src="cid:([^"]+)"', out1["html_email"]))
    msg = deliver.build_message({"user": "a@x.invalid", "rcpt": "b@x.invalid"},
                                "s", out1["html_email"], "t",
                                inline_images=out1["inline_images"])
    parsed = message_from_bytes(msg.as_bytes(), policy=email_default)
    part_cids = {str(pp.get("Content-ID", "")).strip("<>") for pp in parsed.walk()
                 if pp.get_content_type() == "image/png"}
    check(body_cids and body_cids == part_cids,
          f"the email's Content-ID set matches the charts the body references "
          f"({sorted(body_cids)})")
    rel = [pp for pp in parsed.walk() if pp.get_content_type() == "multipart/related"]
    check(len(rel) == 1, "inside one multipart/related body")
    check('src="cid:' not in html1 and ".svg" in html1,
          "the archived edition points at its SVGs instead")
    bad_c = charts_mod.c2(book, [], "x", None)
    check(bad_c.get("unavailable") and "chart unavailable" in
          stack_render._chart_html(bad_c, "email"),
          f"a chart that cannot render prints its reason ({bad_c['unavailable']})")
    check(all(not re.search(r"\b(buy|sell)\b", c.get("caption", ""), re.I)
              for c in ch.values()), "no chart caption carries a verdict")

    # --- E. INTRADAY ----------------------------------------------------------------
    print(f"\n{LINE}\nE. INTRADAY -- the bars-incomplete rule\n{LINE}")
    db3 = str(Path(td) / "thin.db")
    s3 = seed(db3, bars_5m=60)
    with bars_mod.BarStore(db3) as bst:
        it = bars_mod.intraday(bst, "spy", SESSION)
        bk3 = levels_mod.compute(SESSION, p["exposure"], store=bst)
    check(not it["complete"] and it["reason"] == "bars incomplete (n=60 of 78)",
          f"60 of 78 bars is incomplete ({it['reason']})")
    o3 = stack_close.produce(payload(s3["market_state"]), archive_dir=None,
                             dry_run=True, client=clean, db_path=db3)
    c1 = o3["charts"]["C1"]
    check(c1.get("unavailable") == "bars incomplete (n=60 of 78)"
          and "chart unavailable: bars incomplete" in o3["html_email"],
          "C1 is omitted with that reason")
    spy3 = next(i for i in bk3["instruments"] if i["id"] == "spy")
    check("vwap" not in {lv["type"] for lv in spy3["levels"]}
          and "incomplete" in spy3["absent"].get("vwap", ""),
          "and no VWAP is computed from an incomplete session")
    # THE FEED (ruled 2 Oct 2026): the pull lives in the 16:10 eod run, retries a
    # missing final bar for up to five minutes, and creates and owns the table.
    import pandas as pd

    def make_fetcher(served: list):
        """Serves `served[k]` bars on the k-th intraday call (the last repeats)."""
        calls = {"n": 0}

        def fetcher(symbol, **kw):
            if kw.get("interval") == "5m":
                n = served[min(calls["n"], len(served) - 1)]
                calls["n"] += 1
                idx = pd.date_range(f"{SESSION} 09:30", periods=n, freq="5min",
                                    tz="America/New_York")
            else:
                idx = pd.DatetimeIndex([pd.Timestamp(SESSION)])
            return pd.DataFrame({"Open": 1.0, "High": 1.1, "Low": 0.9, "Close": 1.0,
                                 "Volume": 10.0}, index=idx)
        return fetcher, calls

    class Clock:
        def __init__(self):
            self.t, self.slept = 0.0, []

        def __call__(self):
            return self.t

        def sleep(self, s):
            self.slept.append(s)
            self.t += s

    from altdata import feeds
    import inspect
    fetch1, _ = make_fetcher([78])
    with bars_mod.BarStore(str(Path(td) / "pull.db"), create=True) as bst:
        rep = bars_mod.pull(SESSION, store=bst, fetcher=fetch1)
        n5 = len(bst.read("spy", "5m"))
        first = bst.read("spy", "5m")[0]
    check(rep["instruments"]["spy"].get("5m") == 78 and n5 == 78
          and first["available_at"] and first["ingested_at"] and first["observed_at"],
          "the bars feed stores the session's 5-minute bars with the three clocks")
    spec = [t for t in bars_mod.tape() if t["id"] == "spy"]
    clk = Clock()
    fetch2, calls2 = make_fetcher([77, 77, 78])
    orig = bars_mod.load_config
    bars_mod.load_config = lambda path=None: {**orig(path), "tape": spec}
    try:
        with bars_mod.BarStore(str(Path(td) / "retry.db"), create=True) as bst:
            r2 = bars_mod.pull(SESSION, store=bst, fetcher=fetch2, sleep=clk.sleep,
                               clock=clk)["instruments"]["spy"]
        check(r2["attempts"] == 3 and r2["final_bar"] and r2["5m"] == 78
              and clk.slept == [30.0, 30.0],
              f"a missing final bar is fetched again every 30 s until it arrives "
              f"({r2['attempts']} attempts, slept {clk.slept})")
        clk = Clock()
        fetch3, _ = make_fetcher([70])
        with bars_mod.BarStore(str(Path(td) / "short.db"), create=True) as bst:
            r3 = bars_mod.pull(SESSION, store=bst, fetcher=fetch3, sleep=clk.sleep,
                               clock=clk)["instruments"]["spy"]
            it3 = bars_mod.intraday(bst, "spy", SESSION)
        check(not r3["final_bar"] and sum(clk.slept) <= 300 and r3["attempts"] == 11
              and r3["5m"] == 70,
              f"and gives up inside five minutes, storing what arrived "
              f"({r3['attempts']} attempts, {sum(clk.slept):.0f} s slept)")
        check(it3["reason"] == "bars incomplete (n=70 of 78)",
              f"which the close then prints ({it3['reason']})")
    finally:
        bars_mod.load_config = orig
    fresh = str(Path(td) / "never_fed.db")
    import sqlite3
    sqlite3.connect(fresh).close()
    with bars_mod.BarStore(fresh) as bst:
        none = bars_mod.intraday(bst, "spy", SESSION)
    with sqlite3.connect(fresh) as c:
        made = c.execute("SELECT 1 FROM sqlite_master WHERE name='bars'").fetchone()
    check(made is None and none["reason"] == "bars incomplete (n=0 of 78)",
          "a reader never creates the bars table: the feed owns it, and an unfed "
          "store reads as 'bars incomplete (n=0 of 78)'")
    try:
        with bars_mod.BarStore(fresh) as bst:
            bst.write_many([])
        wrote = True
    except RuntimeError:
        wrote = False
    check(not wrote, "and a reader cannot write bars")
    src = "".join(inspect.getsource(m) for m in (stack_close, stack_mod,
                                                 charts_mod, stack_prose))
    src += (REPO / "daily_cascade" / "close_report.py").read_text(encoding="utf-8")
    check("bars_mod.pull" not in src and "import yfinance" not in src
          and "create=True" not in src,
          "the close fetches nothing: no bars pull, no yfinance, no table creation "
          "in the close's modules (30.4)")
    check("bars" in feeds.FEEDS and "bars" in inspect.getsource(feeds.pull)
          and "bars" in re.search(r'skip = \(([^)]*)\)',
                                  inspect.getsource(feeds.pull)).group(1),
          "bars is a feed, run by the eod pull and skipped by the 06:45 early set")
    eod = (REPO / "scripts" / "run_eod_cron.sh").read_text(encoding="utf-8")
    close_sh = (REPO / "scripts" / "run_daily_close.sh").read_text(encoding="utf-8")
    check("altdata.feeds pull --skip loggers" in eod
          and "altdata.feeds pull --only prices" in close_sh,
          "the 16:10 eod run pulls it; the 16:45 close's feed step is prices only")

    # --- F. BUDGET ------------------------------------------------------------------
    print(f"\n{LINE}\nF. BUDGET\n{LINE}")
    check(ed1["words"] <= 1000, f"the fixture edition is inside 1,000 words "
                                f"({ed1['words']})")
    e = stack_mod.build(p, book, ed1["outlooks"], None, db)
    stack_prose.write(e, client=clean, outlooks=ed1["outlooks"])
    # PROSE ONLY (T2.2, ruled 4 Oct 2026): items and tables are data, never
    # counted and never cut; over budget, later paragraphs go first.
    deep = next(s for s in e["sections"] if s["depth"] == "deep" and s.get("claim"))
    deep["paragraphs"] = ["One more paragraph of prose for the cut to take. " * 4] * 3
    items_before = {i["key"] for s in e["sections"] for i in s["items"]}
    tables_before = [s.get("table") for s in e["sections"]]
    prose_only = sum(stack_mod.words(s.get("claim")) + sum(
        stack_mod.words(x) for x in s.get("paragraphs") or [])
        for s in e["sections"] if not s.get("collapsed"))
    before = sum(stack_mod.section_words(s) for s in e["sections"])
    check(before == prose_only,
          f"words count prose only: claims and paragraphs, never items ({before})")
    limit = before - 40
    e["budget"] = {"words": limit, "charts": 3}
    stack_mod.enforce_budget(e)
    trimmed = [s["id"] for s in e["sections"] if s["trimmed"]]
    check(trimmed and len(deep["paragraphs"]) < 3,
          f"over budget ({before} words against {limit}), the later paragraphs go "
          f"first ({trimmed}; {e['words']} words)")
    check(items_before == {i["key"] for s in e["sections"] for i in s["items"]}
          and tables_before == [s.get("table") for s in e["sections"]],
          "and no item and no table is cut -- they are data")
    check(all(s.get("claim") for s in e["sections"] if not s.get("withheld")),
          "and no claim line is cut")
    sh = stack_render.section_html(next(s for s in e["sections"]
                                        if s["id"] == trimmed[0]), 1, {}, "email")
    check("(trimmed)" in sh, "the cut section prints '(trimmed)'")

    # --- G. LEDGER ------------------------------------------------------------------
    print(f"\n{LINE}\nG. ODDS IN THE LEDGER\n{LINE}")
    comp = [o for o in ed1["outlooks"] if o["state"] == "computed"]
    check(comp and all(0 < o["probability"] < 1 and o["n"] >= 20 for o in comp),
          f"{len(comp)} outlook(s) computed from stored closes, each with its n "
          f"({[(o['id'], o['probability'], o['n']) for o in comp]})")
    with pl.ProbabilityLedger(db) as led:
        rows = [r for r in led.all_rows() if r["source"] == outlooks.LEDGER_SOURCE]
    check(len(rows) == len(comp) and all(o["ledger_id"] == next(
        r["probability_id"] for r in rows if r["claim"] == o["claim"]) for o in comp),
          "each is in the ledger, with a resolution criterion, before the edition "
          "printed it")
    again = outlooks.record(outlooks.build(SESSION, bars_mod.BarStore(db)), SESSION,
                            db_path=db)
    with pl.ProbabilityLedger(db) as led:
        n2 = len([r for r in led.all_rows() if r["source"] == outlooks.LEDGER_SOURCE])
    check(n2 == len(rows), "a re-run of the session reuses its entries rather than "
                           "emitting the forecast twice")
    dry = outlooks.record(outlooks.build(SESSION, bars_mod.BarStore(db3)), SESSION,
                          dry_run=True, db_path=db3)
    with pl.ProbabilityLedger(db3) as led:
        n3 = len(led.all_rows())
    check(n3 == 0 and all("dry-run" in str(o.get("ledger_id"))
                          for o in dry if o["state"] == "computed"),
          "a dry run records nothing and says so")

    # --- H. SCORECARD ---------------------------------------------------------------
    print(f"\n{LINE}\nH. THE DEALER SCORECARD ROW\n{LINE}")
    from altdata import observations
    with observations.ObservationStore(db) as st:
        r = st.latest_as_of(stack_close.SCORECARD_KEY, instrument="SPY")
    card = json.loads(r["value_text"]) if r else {}
    want = {"gamma_regime", "net_gex_close", "net_gex_morning", "flip_morning",
            "flip_crossed", "session_range_pct", "session_return_pct",
            "pin_max_pain_hit", "realized_vol_5m_ann_pct"}
    check(r and want <= set(card) and card["gamma_regime"] == "negative"
          and card["realized_vol_5m_ann_pct"],
          f"the close stores {stack_close.SCORECARD_KEY} for SPY with the fields "
          f"the Monthly's retrospective reads")
    with observations.ObservationStore(db3) as st:
        check(st.latest_as_of(stack_close.SCORECARD_KEY, instrument="SPY") is None,
              "and a dry run stores none")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

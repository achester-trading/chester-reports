#!/usr/bin/env python3
"""
Validation gate for the Digital Assets addendum to the Sunday Weekly (Batch 8
item 51, Phase 1, ST-R6.51a, and item 49c's event entries; 6e-digital, 17 Oct
2026).

    python tools/validate_digital_addendum.py

On a SYNTHETIC crypto week in a temporary store, a temporary inbox, a temporary
register and a temporary events store -- a code gate never reads the live store,
fetches or calls a model, and no figure here is real (the register's paper
exposures are fixture placeholders, not position figures):

  A CONFIG       nine sections in the ruling's order; the budgets; the calendar's
                 dated entries, each with its source, the "to verify" marker on
                 MSCI's effective date, the undated watch
  B TAPE         the weekly bar from the dailies against a hand computation: the
                 week, the day, the 30 days, the range, the realised vol; a close
                 available after the cutoff is not read
  C TWO STATES   an empty store prints "awaiting Tranche A" in every Tranche A
                 cell (SR-29 its own reason); a seeded store prints the figures,
                 the week's ETF sum and the stablecoin change
  D ATTENTION    the ledgers and digests from the inbox: themes, shocks,
                 disagreement pairs only with both URLs, new voices, the Saturday
                 scan; the no-rows state; a file copied after the cutoff is not
                 read; the Drive export's escapes parse
  E AHEAD        the dates and markers on the page; the Weekly's Ahead prints
                 the entries in their week with the marker; the undated watch
                 prints "date not published"
  F BOOK         Book D's crypto paper decisions from the register, opened
                 read-only and left byte-identical
  G THE READ     the narrative step publishes a paragraph made of the page's
                 figures and withholds one citing a figure not on the page
  H BUDGETS      words, reading minutes and charts within the budgets; a
                 swollen week is trimmed back inside and marked
  I PUBLISH      the second page on a fixture Sunday: archived beside the
                 Weekly, attached to its message, one link line in the Weekly; a
                 failed addendum costs only the addendum
  J ISOLATION    no socket opened, no model reached, no fetch in the module
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import socket
import sqlite3
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
ENDING = "2026-10-30"                       # the Weekly's Friday; all synthetic
SUN, SAT = "2026-10-25", "2026-10-31"       # the crypto week
AS_OF = "2026-11-01T09:00:00+00:00"         # Sunday 05:00 ET
TD = Path(gate_mkdtemp("digital_addendum_"))

# J: NO NETWORK. Any socket the gate opens is a failure, not a fetch.
_SOCKETS: list = []


class _NoSocket(socket.socket):
    def __init__(self, *a, **k):                                # noqa: D401
        _SOCKETS.append(a)
        raise OSError("validate_digital_addendum: no network in a code gate")


socket.socket = _NoSocket                                       # type: ignore[misc]
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["CHESTER_INBOX_DIR"] = str(TD / "inbox-none")


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def near(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def days(first: str, last: str) -> list[str]:
    d, e, out = dt.date.fromisoformat(first), dt.date.fromisoformat(last), []
    while d <= e:
        out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


DAYS = days("2026-08-01", SAT)


def close(sym: str, i: int) -> float:
    base = {"BTC": 60000.0, "ETH": 3000.0, "SOL": 150.0, "ZEC": 40.0}[sym]
    return base * (1.0 + 0.002 * i + 0.01 * math.sin(i))


def seed_store(path: str, *, tranche_a: bool = False, late: bool = False) -> None:
    from altdata import observations
    rows = []

    def put(key, day, v, avail=None, inst=None, text=None):
        rows.append({"registry_key": key, "instrument": inst, "observed_at": day,
                     "available_at": avail or f"{dt.date.fromisoformat(day) + dt.timedelta(days=1)}T00:30:00+00:00",
                     "value": text if text is not None else v, "source": "synthetic"})
    for sym, key in (("BTC", "yfinance.mkt_btc_usd"), ("ETH", "yfinance.mkt_eth_usd"),
                     ("SOL", "yfinance.mkt_sol_usd"), ("ZEC", "yfinance.mkt_zec_usd")):
        for i, d in enumerate(DAYS):
            put(key, d, round(close(sym, i), 2))
    if late:
        # Saturday's BTC bar revised AFTER the cutoff: never read.
        put("yfinance.mkt_btc_usd", SAT, 1.0, avail="2026-11-01T12:00:00+00:00")
    if tranche_a:
        for i, d in enumerate(DAYS[-10:]):
            put("deribit.dvol_btc", d, 50.0 + i)
            put("deribit.dvol_eth", d, 70.0 + i)
            put("calc.funding_agg", d, 0.01, inst="BTC")
            put("calc.funding_agg", d, 0.02, inst="ETH")
            put("calc.oi_usd", d, 40e9 + 1e9 * i)
            put("farside.btc_total", d, 1e7 * (i - 4))
            put("farside.eth_total", d, -5e6)
            put("gt.new_pools_24h", d, 140.0, inst="solana")
            put("btcdata.lth_supply_share", d, 74.25)
    for i, d in enumerate(DAYS[-15:]):
        put("llama.stable_total", d, 300e9 + 0.5e9 * i)
    put("scan.crypto_basket_item", "2026-10-31", None, inst="PRL",
        text=json.dumps({"kind": "listing", "title": "PRL listed on a venue",
                         "url": "https://example.invalid/prl"}))
    with observations.ObservationStore(path) as st:
        st.write_many(rows)


def stamp(p: Path, when: str) -> None:
    p.with_name(p.name + ".copied_at").write_text(when + "\n", encoding="utf-8")


DIGEST = """\\# X digest {day}
\\#\\# 0. Run
Source: X post search. Posts reviewed: ~300.

\\#\\# 1. Attention map
| theme | volume | trend | post |

\\#\\# 2. Items
https://x.com/acct\\_one/status/1001 | @acct\\_one | {day} 03:45 UTC | An exchange paused withdrawals for two hours | 2h | likes 8 | incident | https://example.invalid/a
https://x.com/acct_two/status/1002 | @acct_two | {day} 05:00 UTC | The SEC published a custody proposal | 760 pages | likes 3 | regulation |
https://x.com/acct_three/status/1003 | @acct_three | {day} 06:00 UTC | ETF outflows on the day | -82.4 | likes 1 | flows |
no-url-row | @acct_four | {day} | An unsourced incident claim | | | incident |

\\#\\# 3. Disagreements
Question: Does an index exclusion force bitcoin sales?
Side A (forced selling): https://x.com/side\\_a/status/2001 (passive funds sell)
Side B (no coins sold): https://x.com/side_b/status/2002 (the company keeps its coins)
Question: A pair with one side unsourced
Side A (yes): https://x.com/side_c/status/2003
Side B (no): an assertion with no post

\\#\\# 5. Incidents
Prose that is not printed.
"""


def seed_inbox(base: Path, *, late_ledger: bool = False) -> None:
    tri, dig = base / "x-triage", base / "x-digest"
    tri.mkdir(parents=True, exist_ok=True)
    dig.mkdir(parents=True, exist_ok=True)
    a = tri / "x-attention-ledger.csv"
    a.write_text(
        "date,theme,volume_class,grok_estimate,representative_url,shock_flag,notes\n"
        "2026-10-20,flows,high,high,https://x.com/f/status/1,yes,before the week\n"
        "2026-10-26,flows,medium,medium,https://x.com/f/status/2,no,\n"
        "2026-10-27,flows,high,high,https://x.com/f/status/3,yes,\n"
        "2026-10-27,treasury-co,medium,medium,https://x.com/t/status/4,yes,\n"
        "2026-10-28,privacy,low,low,,no,no URL supplied\n", encoding="utf-8")
    stamp(a, "2026-11-01T08:00:00+00:00" if late_ledger is False
          else "2026-11-01T12:00:00+00:00")
    v = tri / "x-voices-ledger.csv"
    v.write_text("handle,first_seen,role,incentive_tag,track_record_notes\n"
                 "@old,2026-10-17,analyst,analyst,\n"
                 "@newvoice,2026-10-27,\"protocol team, official\",protocol-team,\n",
                 encoding="utf-8")
    stamp(v, "2026-11-01T08:00:00+00:00")
    for day in ("2026-10-27", "2026-10-29"):
        p = dig / f"x-digest-{day}.md"
        p.write_text(DIGEST.format(day=day), encoding="utf-8")
        stamp(p, f"{day}T11:00:00+00:00")
    late = dig / "x-digest-2026-10-31.md"           # copied after the cutoff
    late.write_text(DIGEST.format(day="2026-10-31"), encoding="utf-8")
    stamp(late, "2026-11-01T12:00:00+00:00")


def seed_register(path: Path) -> None:
    from register import store as reg
    reg.Register(str(path)).close()
    con = sqlite3.connect(str(path))
    cols = {r[1] for r in con.execute("PRAGMA table_info(decisions)")}
    base = {"decision_time": "2026-10-20T15:00:00+00:00", "thesis": "fixture",
            "edge_type": "fixture", "horizon": "swing", "invalidation": "fixture",
            "superseded_by": None}
    # FIXTURE PLACEHOLDERS, not position figures: round synthetic numbers.
    for i, (inst, book, status, notional) in enumerate((
            ("IBIT", "D", "active", 1000.0), ("MSTR 2026-11-20 C 150", "D", "active", 2000.0),
            ("BTC-USD", "D", "draft", 3000.0), ("SPY", "D", "active", 4000.0),
            ("ETHA", "A", "active", 5000.0))):
        row = {**base, "id": f"fx-{i}", "created_at": f"2026-10-2{i}T15:00:00+00:00",
               "instrument": inst, "instrument_norm": inst.upper(),
               "direction": "long", "status": status, "book": book,
               "notional_usd": notional, "vega_usd": None}
        row = {k: v for k, v in row.items() if k in cols}
        con.execute(f"INSERT INTO decisions ({', '.join(row)}) VALUES "
                    f"({', '.join('?' for _ in row)})", list(row.values()))
    con.commit()
    con.close()


def seed_events(path: str) -> None:
    from altdata import events as ev_mod
    with ev_mod.EventStore(path) as es:
        es.write_many([ev_mod.Event(
            type="scheduled", observed_at="2026-12-09T19:00:00+00:00",
            source="fed_calendar", title="FOMC Meeting -- two-day meeting",
            key="fedcal:fixture:fomc")], available_at="2026-10-01T00:00:00+00:00")


class Resp:
    def __init__(self, t):
        self.content = [types.SimpleNamespace(type="text", text=t)]
        self.model = "fixture-model"
        self.stop_reason = "end_turn"


def client(text: str, seen: list):
    def create(**k):
        seen.append(k)
        return Resp(text)
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


def sec(ed: dict, sid: str) -> dict:
    return next(s for s in ed["sections"] if s["id"] == sid)


def cells(ed: dict, sid: str) -> dict:
    return {c["label"]: c for c in (sec(ed, sid).get("data") or {}).get("cells") or []}


def main() -> int:
    from daily_cascade import digital_addendum as da

    db_a = str(TD / "obs_a.sqlite")
    seed_store(db_a)
    db_b = str(TD / "obs_b.sqlite")
    seed_store(db_b, tranche_a=True, late=True)
    inbox = TD / "inbox"
    seed_inbox(inbox)
    regp = TD / "register.db"
    seed_register(regp)
    reg_hash = hashlib.sha256(regp.read_bytes()).hexdigest()
    evdb = str(TD / "events.sqlite")
    seed_events(evdb)
    cfg = da.config()
    kw = dict(register=regp, events_db=evdb, chain_base=TD / "chains")

    # --- A --------------------------------------------------------------------
    head("A. CONFIG AND CALENDAR")
    check([s for s, _ in da.SECTIONS] == ["read", "tape", "flows", "mechanics",
                                          "onchain", "attention", "incidents",
                                          "ahead", "book"],
          "nine sections in the ruling's order: the read; tape; flows; mechanics; "
          "on-chain; narratives and attention; incidents and regulation; ahead; "
          "the book")
    b = cfg["budget"]
    check(b["reading_minutes"] == 5 and b["words"] == 1100 and b["charts"] == 2
          and b["read_words"] == 120,
          "the session-set budgets: five minutes, 1,100 words, two charts, a read "
          "of 120 words")
    cal = da.load_calendar(cfg=cfg)
    ents = {(e["date"].isoformat() if hasattr(e["date"], "isoformat") else str(e["date"]),
             e["body"]): e for e in cal["entries"]}
    check(all(e.get("source") and e.get("event") for e in cal["entries"]),
          f"every dated entry carries its event and its source ({len(ents)})")
    check(("2026-10-28", "Strategy (MSTR)") in ents
          and "STRC" in ents[("2026-10-28", "Strategy (MSTR)")]["event"],
          "28 Oct: the STRC shareholder vote")
    m11 = ents.get(("2026-11-11", "MSCI"))
    check(m11 and m11.get("time") == "after the US close" and not m11.get("marker"),
          "11 Nov: MSCI's review announcement, after the US close")
    m30 = ents.get(("2026-11-30", "MSCI"))
    check(m30 and not m30.get("marker") and m30["event"].endswith(
        "implemented at the close of 30 Nov, effective 1 Dec"),
          "30 Nov: MSCI's review \"implemented at the close of 30 Nov, effective 1 Dec\", "
          "the marker off (ruling (f) of 17 Oct: verify item 2 closed)")
    v15 = ents.get(("2026-11-15", "SEC"))
    check(v15 and v15.get("marker") == "15 Nov, to verify",
          "15 Nov: the VanEck JitoSOL decision keeps its \"to verify\" marker (ruling (e))")
    check(("2026-12-11", "FTSE Russell") in ents and ("2026-11-13", "FTSE Russell") in ents,
          "FTSE Russell's published December reconstitution dates (13 Nov lists, "
          "11 Dec effective)")
    und = {w["body"]: w for w in cal["watch_undated"]}
    check(set(und) == {"S&P Dow Jones Indices", "Nasdaq"}
          and all(w.get("reason") for w in und.values()),
          "S&P DJI and Nasdaq are the undated watch, each with its reason")

    # --- B --------------------------------------------------------------------
    head("B. THE TAPE: THE WEEKLY BAR FROM THE DAILIES")
    ed_a = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=TD / "empty-inbox",
                    narrative=False, cfg=cfg, **kw)
    check(da.crypto_week(ENDING) == (SUN, SAT),
          "the crypto week of the Weekly of Fri 30 Oct is Sun 25 Oct to Sat 31 Oct")
    coins = {c["coin"]: c for c in sec(ed_a, "tape")["data"]["coins"]}
    n = len(DAYS) - 1
    c = [close("BTC", i) for i in range(len(DAYS))]
    c = [round(x, 2) for x in c]
    want_week = 100 * (c[n] / c[n - 7] - 1)
    want_day = 100 * (c[n] / c[n - 1] - 1)
    want_30 = 100 * (c[n] / c[n - 30] - 1)
    r = [math.log(c[i] / c[i - 1]) for i in range(n - 29, n + 1)]
    mu = sum(r) / len(r)
    want_vol = 100 * math.sqrt(365) * math.sqrt(sum((x - mu) ** 2 for x in r) / (len(r) - 1))
    btc = coins["BTC"]
    check(btc["as_of"] == SAT and abs(btc["close"] - c[n]) < 1e-6,
          f"BTC's bar closes on Sat 31 Oct at the stored close ({c[n]:,.2f})")
    check(abs(btc["week_pct"] - want_week) < 0.01 and abs(btc["day_pct"] - want_day) < 0.01
          and abs(btc["month_pct"] - want_30) < 0.01,
          f"the week {want_week:+.2f}%, the day {want_day:+.2f}% and the 30 days "
          f"{want_30:+.2f}% match the hand computation")
    check(abs(btc["vol_pct"] - want_vol) < 0.01,
          f"realised vol, 30 log returns annualised over 365 days: {want_vol:.2f}%")
    check(abs(btc["week_low"] - min(c[n - 6:n + 1])) < 1e-6
          and abs(btc["week_high"] - max(c[n - 6:n + 1])) < 1e-6,
          "the week's range is the seven daily closes' low and high")
    t0 = sec(ed_a, "tape")["tables"][0]
    check(t0["columns"] == ["Coin", "Close", "Day", "Week", "30 days",
                            "Realised vol (30d)"]
          and [r_[0] for r_ in t0["rows"]] == ["BTC", "ETH", "SOL", "ZEC"],
          "the tape's table: BTC, ETH, SOL, ZEC, six columns")
    ed_late = da.build(ENDING, as_of=AS_OF, db_path=db_b, inbox=TD / "empty-inbox",
                       narrative=False, cfg=cfg, **kw)
    bl = {x["coin"]: x for x in sec(ed_late, "tape")["data"]["coins"]}["BTC"]
    check(abs(bl["close"] - c[n]) < 1e-6,
          "a BTC close revised after the cutoff is not read (point in time)")

    # --- C --------------------------------------------------------------------
    head("C. TWO STATES: ABSENT (AWAITING / NOT TRACKED), AND THE DATA PRESENT")
    aw = "awaiting the first pull"
    ca = {**cells(ed_a, "tape"), **cells(ed_a, "flows"), **cells(ed_a, "mechanics"),
          **cells(ed_a, "onchain")}
    built = ["BTC implied vol (DVOL)", "ETH implied vol (DVOL)",
             "BTC funding, OI-weighted (annualised)",
             "ETH funding, OI-weighted (annualised)",
             "Open interest (BTC + ETH)", "BTC ETF net flow, the week",
             "ETH ETF net flow, the week"]
    check(all(ca[k]["text"] == aw for k in built),
          f"with no rows, the {len(built)} built series' cells print \"{aw}\"")
    check(ca["Basis (futures over spot)"]["text"].startswith("not tracked")
          and ca["Liquidations"]["text"] == "not tracked (D-1: no CoinGlass)"
          and ca["Exchange net flows"]["text"].startswith("not tracked")
          and ca["Exchange balances"]["text"].startswith("not tracked"),
          "a series nobody writes prints \"not tracked\" with its reason")
    check(ca["Deribit skew and term structure"]["text"] == "awaiting EL-12"
          and ca["Crypto GEX"]["text"] == "awaiting EL-12",
          "skew, term structure and crypto GEX print \"awaiting EL-12\"")
    check(ca["MSTR mNAV (item 49a; lines 1.2 and 1.0)"]["text"].startswith("not tracked (")
          and "share count" in ca["MSTR mNAV (item 49a; lines 1.2 and 1.0)"]["text"],
          "mNAV with no inputs prints \"not tracked\" and names what is missing")
    check(ca["Froth sample, Solana new pools 24h (unscored)"]["text"].startswith("not sampled"),
          "the froth sample says why it has no sample")
    check(ca["BTC long-term-holder supply share (SR-29)"]["text"].startswith(
        "not stored: SR-29 is by hand"),
          "SR-29's row prints as it does today (Tranche C computes it)")
    check(ca["Stablecoin supply, change on the week"]["text"] == "+$3.5bn",
          f"the stablecoin supply prints its week's change "
          f"({ca['Stablecoin supply, change on the week']['text']})")
    html_a = da.render(ed_a)
    every = [c for c in ca.values()]
    check(all(c["text"] not in ("", "—", "0", "$0") for c in every)
          and html_a.count(aw) >= len(built),
          "no panel cell is a blank or a zero; the rendered page carries each phrase")
    cb = {**cells(ed_late, "tape"), **cells(ed_late, "flows"), **cells(ed_late, "onchain")}
    check(cb["BTC implied vol (DVOL)"]["text"] == "59.0"
          and cb["Open interest (BTC + ETH)"]["text"] == "$49.0bn"
          and cb["BTC funding, OI-weighted (annualised)"]["text"] == "0.01%"
          and cb["ETH funding, OI-weighted (annualised)"]["text"] == "0.02%",
          "with the series stored the cells print their figures: DVOL 59.0, OI $49.0bn, "
          "funding 0.01%")
    want_etf = sum(1e7 * (i - 4) for i, d in enumerate(DAYS[-10:]) if SUN <= d <= SAT)
    check(cb["BTC ETF net flow, the week"]["value"] == round(want_etf, 4)
          and cb["BTC ETF net flow, the week"]["text"] == f"${want_etf / 1e6:,.0f}m",
          f"the BTC ETF row is the sum of the week's seven days, stored in dollars "
          f"(${want_etf / 1e6:,.0f}m)")
    check(cb["BTC long-term-holder supply share (SR-29)"]["text"] == "74.25%"
          and cb["Froth sample, Solana new pools 24h (unscored)"]["text"] == "140",
          "SR-29's share and the froth sample print where stored")

    # --- D --------------------------------------------------------------------
    head("D. NARRATIVES AND ATTENTION, FROM THE INBOX")
    ed_d = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=inbox, narrative=False,
                    cfg=cfg, **kw)
    at = sec(ed_d, "attention")
    tabs = {t["title"]: t for t in at["tables"]}
    th = {r_[0]: r_ for r_ in tabs["The week's attention map"]["rows"]}
    check(set(th) == {"flows", "treasury-co", "privacy"},
          "the attention map holds the week's themes only (20 Oct's row is outside)")
    check(th["flows"][1:4] == ["2", "high", "1"] and th["flows"][4] == "https://x.com/f/status/3",
          "flows: two days, peak high, one shock day, its newest post's URL")
    check(th["privacy"][4] == "no post URL in the row",
          "a theme whose row has no URL says so rather than inventing one")
    pairs = tabs["Disagreement pairs"]["rows"]
    check(len(pairs) == 2 and all(p[2] == "https://x.com/side_a/status/2001"
                                  and p[3] == "https://x.com/side_b/status/2002"
                                  for p in pairs),
          "one disagreement pair a digest (two digests in the week), both URLs; the "
          "pair with an unsourced side is dropped; the Drive export's \\_ parses")
    check(at["data"]["digests"] == ["2026-10-27", "2026-10-29"],
          "the digest copied after the cutoff (31 Oct, stamped 12:00 UTC) is not read")
    check([r_[0] for r_ in tabs["New voices (the voices ledger)"]["rows"]] == ["@newvoice"],
          "new voices: the handles first seen in the week")
    check(tabs["The Saturday scan"]["rows"][0][1] == "PRL",
          "the Saturday scan's stored item prints with its URL")
    inc = {t["title"]: t for t in sec(ed_d, "incidents")["tables"]}
    ir = inc["From the week's digests"]["rows"]
    check({r_[2] for r_ in ir} == {"incident", "regulation"}
          and all(r_[4].startswith("https://x.com/") for r_ in ir) and len(ir) == 2,
          "incidents and regulation: the digests' incident and regulation items, "
          "each with its post's URL; the URL-less row and the flows row do not print")
    check(any("VanEck JitoSOL" in r_[2] for r_ in inc["Regulatory calendar"]["rows"]),
          "the regulatory calendar prints the dated SEC decision")
    ed_none = ed_a
    check(f"X attention: {da.NO_DIGEST}." in sec(ed_none, "attention")["lines"]
          and f"Incidents from X: {da.NO_DIGEST}." in sec(ed_none, "incidents")["lines"]
          and not sec(ed_none, "attention")["tables"][:0],
          "an empty inbox prints \"no digest rows this week\", never a guess")
    late_inbox = TD / "inbox-late"
    seed_inbox(late_inbox, late_ledger=True)
    for p in (late_inbox / "x-digest").glob("*.md"):
        p.unlink()
    ed_l = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=late_inbox,
                    narrative=False, cfg=cfg, **kw)
    check(f"X attention: {da.NO_DIGEST}." in sec(ed_l, "attention")["lines"],
          "a ledger copied after the cutoff is not read: no rows this week")
    ls = TD / "inbox-nostamp" / "x-triage"
    ls.mkdir(parents=True)
    (ls / "x-attention-ledger.csv").write_text(
        (inbox / "x-triage" / "x-attention-ledger.csv").read_text(encoding="utf-8"),
        encoding="utf-8")
    os.utime(ls / "x-attention-ledger.csv", (1792000000, 1792000000))   # 2026-10-14
    ed_m = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=TD / "inbox-nostamp",
                    narrative=False, cfg=cfg, **kw)
    check(sec(ed_m, "attention")["tables"]
          and "modification time" in sec(ed_m, "attention")["footnote"],
          "a file without its copy stamp falls back to its modification time and the "
          "footnote says so")

    # --- E --------------------------------------------------------------------
    head("E. AHEAD: DATED ENTRIES, MARKERS, THE WEEKLY'S AHEAD")
    ed_e = da.build("2026-10-23", as_of="2026-10-25T09:00:00+00:00", db_path=db_a,
                    inbox=TD / "empty-inbox", narrative=False, cfg=cfg, **kw)
    ah = sec(ed_e, "ahead")
    rows = ah["tables"][0]["rows"]
    txt = {r_[0]: r_ for r_ in rows}
    check(txt["28 Oct"][1].startswith("Strategy (MSTR): STRC shareholder vote"),
          "28 Oct prints the STRC vote")
    check(txt["11 Nov"][2] == "after the US close" and "MSCI" in txt["11 Nov"][1],
          "11 Nov prints MSCI's announcement, after the US close")
    check(txt["30 Nov"][2] == "at the US close" and txt["30 Nov"][1].endswith(
        "implemented at the close of 30 Nov, effective 1 Dec"),
          "30 Nov prints \"implemented at the close of 30 Nov, effective 1 Dec\", no marker")
    check(txt["15 Nov"][2] == "15 Nov, to verify",
          "15 Nov prints the VanEck decision with its \"to verify\" marker")
    check("27 Nov" in txt and "Deribit" in txt["27 Nov"][1]
          and "to verify" in txt["27 Nov"][2] and "30 Oct" in txt,
          "Deribit's month-end expiries (30 Oct, 27 Nov) by rule, marked to verify")
    check(any("FOMC" in r_[1] for r_ in rows if r_[0] == "9 Dec"),
          "the FOMC date comes from the events store")
    check("11 Dec" not in txt,
          "the window is 45 days: 11 Dec is outside the 25 Oct page")
    check(len(ah["lines"]) == 1 and ah["lines"][0].startswith("Date not published:")
          and "S&P Dow Jones Indices" in ah["lines"][0] and "Nasdaq" in ah["lines"][0],
          "S&P DJI and Nasdaq print \"date not published\" with their reasons, one line "
          "(the Phase 2 line budget)")
    from daily_cascade import ahead
    acfg = ahead.load_config()
    check(acfg["classes"]["crypto_index_event"]["tier"] == 2
          and any(h["path"] == "config/digital_asset_calendar.yaml"
                  for h in acfg["hand_calendars"]),
          "the Weekly's Ahead reads the calendar as class crypto_index_event (tier 2)")
    hr, _ = ahead.hand_rows(acfg, dt.date(2026, 11, 9), dt.date(2026, 11, 14))
    check(any(r_["event"].startswith("MSCI: November 2026 Index Review announced")
              and r_["time"] == "after the US close" and r_["cls"] == "crypto_index_event"
              for r_ in hr),
          "the Weekly of the week of 9 Nov prints MSCI's 11 Nov announcement")
    hr2, _ = ahead.hand_rows(acfg, dt.date(2026, 11, 30), dt.date(2026, 12, 5))
    check(any(r_["event"] == "MSCI: November 2026 Index Review implemented at the "
              "close of 30 Nov, effective 1 Dec" and r_["time"] == "at the US close"
              for r_ in hr2),
          "and the week of 30 Nov prints MSCI's implementation date")

    # --- F --------------------------------------------------------------------
    head("F. THE BOOK: BOOK D FROM THE REGISTER, READ-ONLY")
    bk = sec(ed_d, "book")
    br = bk["tables"][0]["rows"]
    check([r_[0] for r_ in br] == ["IBIT", "MSTR 2026-11-20 C 150"],
          "Book D's active crypto decisions print (IBIT, an MSTR option); SPY and "
          "Book A's ETHA do not")
    check(br[0][2] == "$1,000" and br[0][3] == "not recorded",
          "the paper notional prints as the register holds it; an absent vega says "
          "\"not recorded\" (fixture placeholders, no position figures)")
    check(any("1 crypto draft in Book D" in x for x in bk["lines"]),
          "a Book D draft is counted, not printed as an exposure")
    check(hashlib.sha256(regp.read_bytes()).hexdigest() == reg_hash,
          "the register file is byte-identical after every build's read "
          "(opened mode=ro)")
    ro = sqlite3.connect(f"file:{regp.as_posix()}?mode=ro", uri=True)
    try:
        ro.execute("DELETE FROM decisions")
        wrote = True
    except sqlite3.OperationalError:
        wrote = False
    ro.close()
    check(not wrote, "the read-only connection refuses a write")
    ed_nb = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=TD / "empty-inbox",
                     narrative=False, cfg=cfg, register=TD / "absent.db",
                     events_db=evdb, chain_base=TD / "chains")
    check("not readable here" in sec(ed_nb, "book")["lines"][0],
          "no register file: the section says so")

    # --- G --------------------------------------------------------------------
    head("G. THE READ: THE NARRATIVE STEP, FROM THE PAGE'S FIGURES")
    t_rows = {r_[0]: r_ for r_ in sec(ed_a, "tape")["tables"][0]["rows"]}
    good = (f"Bitcoin closed the week at {t_rows['BTC'][1]}, {t_rows['BTC'][3]} on the "
            f"week and {t_rows['BTC'][4]} over 30 days, alongside ether at "
            f"{t_rows['ETH'][1]}. Implied volatility, funding and open interest are "
            f"not yet measured on this page.")
    seen: list = []
    ed_g = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=TD / "empty-inbox",
                    narrative=True, client=client(good, seen), cfg=cfg, **kw)
    rd_ = sec(ed_g, "read")
    check(ed_g["prose"]["published"] and rd_["paragraphs"] == [good],
          f"a paragraph made of the page's figures publishes "
          f"({ed_g['prose'].get('state')}: {ed_g['prose'].get('reason')})")
    sysmsg = seen[0]["system"] if seen else ""
    prompt = json.dumps(seen[0]["messages"]) if seen else ""
    check("DIGITAL ASSETS ADDENDUM'S READ" in sysmsg and "at most 120 words" in sysmsg,
          "the existing narrative step, with the addendum's frame")
    check("yfinance." not in prompt and "awaiting the first pull" in prompt,
          "the model sees the page's tables, not the store's keys")
    bad = good.replace(t_rows["BTC"][1], "$71,234")
    ed_b = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=TD / "empty-inbox",
                    narrative=True, client=client(bad, []), cfg=cfg, **kw)
    check(not ed_b["prose"]["published"]
          and sec(ed_b, "read")["lines"][0].startswith("The read is withheld:"),
          f"a figure not on the page withholds the read, with its reason "
          f"({str(ed_b['prose'].get('reason'))[:90]})")
    long_ = " ".join([good] * 4)
    ed_long = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=TD / "empty-inbox",
                       narrative=True, client=client(long_, []), cfg=cfg, **kw)
    check(not ed_long["prose"]["published"],
          "a read past its words or figures is withheld")
    check(sec(ed_a, "read")["lines"] == ["The read was not written (no narrative on "
                                         "this run)."],
          "with no narrative, the read says so")

    # --- H --------------------------------------------------------------------
    head("H. BUDGETS")
    for name, e in (("empty inbox", ed_a), ("full fixture week", ed_d),
                    ("with the read", ed_g)):
        check(e["words"] <= 1100 and e["minutes"] <= 5 and e["chart_count"] <= 2
              and not e["over_budget"],
              f"{name}: {e['words']} words, about {e['minutes']} minutes, "
              f"{e['chart_count']} charts -- inside 1,100 / 5 / 2")
    cap = ed_d["words"] - 40
    tight = {**cfg, "budget": {**cfg["budget"], "words": cap}}
    ed_t = da.build(ENDING, as_of=AS_OF, db_path=db_a, inbox=inbox, narrative=False,
                    cfg=tight, **kw)
    check(ed_t["words"] <= cap and any(s.get("trimmed") for s in ed_t["sections"])
          and "(trimmed)" in da.render(ed_t),
          f"over a {cap}-word budget the page is trimmed back inside ({ed_t['words']}) "
          f"and the trimmed section says so")

    # --- I --------------------------------------------------------------------
    head("I. PUBLISH: THE SECOND PAGE ON A FIXTURE SUNDAY")
    arch = TD / "reports"
    p = {"week_ending": ENDING, "as_of": AS_OF, "run_id": "fixture-run"}
    rendered: list = []
    # A FIXTURE PDF RENDERER: the gate never renders a PDF (CI renders the real one
    # through the Weekly's own step).
    fake_pdf = lambda html: (rendered.append(html) or b"%PDF-1.4 fixture", "fixture")  # noqa: E731
    out = da.produce(p, archive_dir=str(arch), db_path=db_a, narrative=False,
                     inbox=inbox, cfg=cfg, pdf_renderer=fake_pdf, **kw)
    names = sorted(x.name for x in arch.iterdir())
    check(out["state"] == "built" and names == [
        f"weekly_digital_{ENDING}.html", f"weekly_digital_{ENDING}.pdf",
        f"weekly_digital_{ENDING}_appendix.md", f"weekly_digital_{ENDING}_edition.json"]
          and rendered and rendered[0] == out["html"],
          f"the page, its PDF (from the page's own HTML), its edition and its appendix "
          f"line archive beside the Weekly ({', '.join(names)})")
    check(p["addendum"]["state"] == "built" and p["addendum"]["name"]
          == f"weekly_digital_{ENDING}.html",
          "the Weekly's payload records the addendum for its link line")
    from daily_cascade import digital_addendum, deliver, weekly_stack
    ln_e = digital_addendum.link_line(p["addendum"], "email")
    ln_a = digital_addendum.link_line(p["addendum"], "archive")
    check(ln_e.endswith("attached to this message.") and ln_a.endswith("beside this edition.")
          and f"weekly_digital_{ENDING}.pdf" in ln_e,
          f"the link line: \"{ln_e}\"")
    ed_w = {"sections": [], "week_ending": ENDING, "as_of": AS_OF, "chart_count": 0,
            "words": 0, "config_version": "fixture"}
    try:
        w_html = weekly_stack.render(p, ed_w, {}, "email")
        w_plain = weekly_stack.render({k: v for k, v in p.items() if k != "addendum"},
                                      ed_w, {}, "email")
        check(ln_e in w_html.replace("&#x27;", "'") and "Digital Assets addendum"
              not in w_plain and len(w_html) - len(w_plain) < 400 + len(ln_e),
              "the Weekly gains one line and nothing else; without an addendum it is "
              "unchanged")
    except Exception as exc:                                    # noqa: BLE001
        check(False, f"the Weekly renders with the link line ({type(exc).__name__}: {exc})")
    att = digital_addendum.attachment(out)
    msg = deliver.build_message({"user": "from@example.invalid", "rcpt": "to@example.invalid"},
                                "Weekly", "<p>body</p>", "text",
                                attachments=[("weekly_tactical.pdf", b"%PDF-1.4", "pdf")]
                                + att)
    parts = {pt.get_filename(): pt.get_content_type() for pt in msg.iter_attachments()}
    check(parts == {"weekly_tactical.pdf": "application/pdf",
                    f"weekly_digital_{ENDING}.pdf": "application/pdf"},
          "the Weekly's own email carries the addendum as a second PDF (ruling (e))")
    nopdf = da.produce({"week_ending": ENDING, "as_of": AS_OF}, archive_dir=str(TD / "rp"),
                       db_path=db_a, narrative=False, inbox=inbox, cfg=cfg,
                       pdf_renderer=lambda h: (None, "WeasyPrint unavailable"), **kw)
    check(digital_addendum.attachment(nopdf)[0][2] == "html",
          "a PDF that cannot be built leaves the HTML attached in its place")
    src = (REPO / "daily_cascade" / "deliver.py").read_text(encoding="utf-8")
    check("attachments: Optional[list] = None" in src and "+ extra or None" in src,
          "deliver() passes the addendum beside the PDF (the one change to the "
          "publish path)")
    wr = (REPO / "daily_cascade" / "weekly_report.py").read_text(encoding="utf-8")
    check(wr.count("attachments=digital_addendum.attachment(add)") == 2
          and wr.find("digital_addendum.produce(") < wr.find("weekly_stack.produce("),
          "the Sunday run builds the addendum before the Weekly and attaches it on "
          "both sends (the live one and the mailed dry run)")
    p3 = {"week_ending": "2026-10-23", "as_of": "2026-10-25T09:00:00+00:00"}
    arch3 = TD / "reports3"
    out3 = da.produce(p3, archive_dir=str(arch3), db_path=db_a, pdf_renderer=fake_pdf, narrative=False,
                      inbox=inbox, cfg=cfg, **kw)
    check(out3["state"] == "dry_run" and "addendum" not in p3
          and digital_addendum.attachment(out3) == []
          and (arch3 / "dryrun" / "weekly_digital_2026-10-23.html").is_file()
          and not (arch3 / "weekly_digital_2026-10-23.html").exists(),
          "the Weekly of 25 Oct (before the first edition of 1 Nov): a dry-run page "
          "under dryrun/, not attached, no link line")
    p2 = {"week_ending": ENDING, "as_of": AS_OF}
    out2 = da.produce(p2, archive_dir=str(TD / "reports2"), db_path=db_a, pdf_renderer=fake_pdf,
                      narrative=False, cfg={"tape": {"coins": [{"sym": "X"}]}}, calendar={}, **kw)
    check(out2["state"] == "failed" and p2["addendum"]["state"] == "failed"
          and "not built this week" in digital_addendum.link_line(p2["addendum"])
          and digital_addendum.attachment(out2) == [],
          "a failed addendum costs only the addendum: the link line says it was not "
          "built and nothing is attached")
    al = (arch / f"weekly_digital_{ENDING}_appendix.md").read_text(encoding="utf-8")
    check("Draft for Ari's accept-all" in al and "**Week to 31 Oct 2026.** BTC $" in al
          and "never the model's" in al,
          "the appendix line: dated, code-written from the page, a draft for "
          "Ari's accept-all")

    # --- J --------------------------------------------------------------------
    head("J. ISOLATION")
    check(not _SOCKETS, "no socket was opened by any build, render or publish")
    msrc = (REPO / "daily_cascade" / "digital_addendum.py").read_text(encoding="utf-8")
    check(not any(x in msrc for x in ("urllib", "requests", "http_get", "urlopen")),
          "the module fetches nothing")
    check("mode=ro" in msrc and "INSERT" not in msrc and "write_many" not in msrc,
          "the module writes no store, ledger or register row")

    ed_full = da.build(ENDING, as_of=AS_OF, db_path=db_b, inbox=inbox, narrative=False,
                       cfg=cfg, **kw)
    phase2(cfg, {"full": ed_full, "client": client})
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


def phase2(cfg: dict, kw: dict) -> None:
    """ST-R6.51b and items 49a/49b (digital-49-51b, 17 Oct 2026)."""
    from daily_cascade import digital_addendum as da
    from altdata.sources import crypto_derived as D, treasury as T
    from altdata.sources import _crypto as C
    head("K. ITEM 49a: mNAV, THE WATCH LINE AND THE FLAG")
    html = (REPO / "tests" / "fixtures" / "treasury" / "bitbo_public_companies.html"
            ).read_text(encoding="utf-8")
    hold = T.parse_holdings(html, 20)
    check(hold[0]["ticker"] == "MSTR" and hold[0]["btc"] == 848250.0 and len(hold) <= 20,
          f"BitcoinTreasuries.com's table (the real page, trimmed): Strategy holds "
          f"{hold[0]['btc']:,.0f} BTC, the ticker read from Symbol:Exchange")
    sh = T.parse_shares(json.loads((REPO / "tests" / "fixtures" / "treasury" /
                                    "edgar_shares_mstr.json").read_text(encoding="utf-8")))
    check(sh == ("2026-09-30", 420500000.0, "2026-10-30"),
          "EDGAR companyconcept (the documented shape): the latest filing's stated "
          "share count, filed under its end date")
    spot, shares, held, btc = 135.24, 420.5e6, 848250.0, 81000.0
    want = spot * shares / (held * btc)
    check(near(D.mnav(spot, shares, held, btc), want, 1e-12) and abs(want - 0.8277) < 1e-3,
          f"mNAV reconciles to the hand figure: {spot} x {shares:,.0f} / ({held:,.0f} x "
          f"{btc:,.0f}) = {want:.4f}")
    db = str(TD / "mnav.sqlite")
    from altdata import observations
    rows = []
    days = [(dt.date(2026, 10, 12) + dt.timedelta(days=k)).isoformat() for k in range(5)]

    def put(key, d, v, inst=None):
        rows.append(C.row(key, d, v, f"{d}T22:00:00+00:00", "synthetic", inst))
    put("treasury.mstr_shares", "2026-09-30", 420.5e6)
    put("treasury.btc_holdings", days[0], 848250.0, "MSTR")
    for k, d in enumerate(days):
        put("yfinance.mkt_btc_usd", d, 81000.0)
        # 1.01, 1.00, then below
        target = (1.01, 1.0, 0.9, 0.85, 0.83)[k]
        put("treasury.mstr_spot", d, target * 848250.0 * 81000.0 / 420.5e6, "MSTR")
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        out = D.mnav_rows(st, None, AS_OF)
        mn = {r["observed_at"]: r["value"] for r in out}
        check(near(mn[days[0]], 1.01, 1e-6) and near(mn[days[1]], 1.0, 1e-6),
              "calc.mnav per session from the spot, the share count and holdings as of "
              "that day, and the day's BTC close")
        # Each session's mNAV knowable that evening (the gate reads it day by day).
        st.write_many([dict(r, available_at=f"{r['observed_at']}T22:30:00+00:00")
                       for r in out])
        c = {"label": "MSTR mNAV", "key": "calc.mnav", "instrument": "MSTR", "panel": "mnav"}
        at101 = da.mnav_cell(st, c, f"{days[0]}T23:00:00+00:00", cfg)
        at100 = da.mnav_cell(st, c, f"{days[1]}T23:00:00+00:00", cfg)
        last = da.mnav_cell(st, c, AS_OF, cfg)
    check("FLAG" not in at101["text"] and "at or below the 1.2 watch line" in at101["text"],
          f"at 1.01 no flag prints; the watch line does (\"{at101['text']}\")")
    check("FLAG: at or below 1 on 13 Oct" in at100["text"],
          f"at 1.00 the flag prints with its date (\"{at100['text']}\")")
    check("percentile from" in last["text"] and "0.83" in last["text"],
          "before 60 sessions: the level and \"percentile from <date>\"")

    head("L. ITEM 49b: WHO IS BUYING")
    db2 = str(TD / "wib.sqlite")
    rows = []
    sept = [(dt.date(2026, 9, 1) + dt.timedelta(days=k)).isoformat() for k in range(30)]
    for d in sept:
        put("farside.btc_total", d, 81e6)                       # 1,000 BTC a session at 81,000
        put("yfinance.mkt_btc_usd", d, 81000.0)
    put("treasury.btc_holdings", "2026-08-31", 800000.0, "MSTR")
    put("treasury.btc_holdings", "2026-09-30", 805000.0, "MSTR")
    put("treasury.btc_holdings", "2026-09-30", 1000.0, "NEW")    # not at both ends
    put("mempool.tip_height", "2026-08-31", 900000.0)
    put("mempool.tip_height", "2026-09-30", 904320.0)           # 4,320 blocks
    with observations.ObservationStore(db2) as st:
        st.write_many(rows)
        st.write_many(D.net_purchase_rows(st, "2026-10-17T00:00:00+00:00", "2026-10-16T23:00:00+00:00"))
        w = da.who_is_buying(st, "2026-10-17T00:00:00+00:00", cfg)
    d_ = w["data"]
    check(near(d_["etf"], 30000.0) and near(d_["treasury"], 5000.0)
          and near(d_["supply"], 4320 * 3.125)
          and near(d_["residual"], 30000.0 + 5000.0 - 13500.0),
          f"the decomposition sums: ETF {d_['etf']:,.0f} + treasury {d_['treasury']:,.0f} "
          f"- new supply {d_['supply']:,.0f} = residual {d_['residual']:,.0f} BTC "
          f"(a company not at both month ends is left out)")
    db3 = str(TD / "wib2.sqlite")
    with observations.ObservationStore(db3) as st:
        st.write_many([r for r in rows if r["registry_key"] != "mempool.tip_height"])
        st.write_many(D.net_purchase_rows(st, "2026-10-17T00:00:00+00:00", "2026-10-16T23:00:00+00:00"))
        w2 = da.who_is_buying(st, "2026-10-17T00:00:00+00:00", cfg)
    rr = {r[0].split(" (")[0]: r[1] for r in w2["table"]["rows"]}
    check(w2["data"]["residual"] is None and rr["New supply mined"].startswith("not tracked")
          and rr["Residual: the two buyers beyond new supply"].startswith("withheld"),
          "a leg with no reading prints \"not tracked\" and the residual is withheld")

    head("M. THE LINE BUDGET AND THE READ'S AUDITS")
    full = kw["full"]
    n = sum(len(t.get("rows") or []) for s_ in full["sections"] for t in s_.get("tables") or []) \
        + sum(len(s_.get("lines") or []) + len(s_.get("paragraphs") or [])
              for s_ in full["sections"])
    check(cfg["max_lines"] == 52 and n <= cfg["max_lines"],
          f"the panels hold Phase 1's line budget: {n} lines against 52 on the full "
          f"fixture week")
    check(full["words"] <= 1100 and full["minutes"] <= 5,
          f"and the word budget: {full['words']} words, about {full['minutes']} minutes")
    from daily_cascade import digital_addendum as da_
    payload = da_.read_payload(full)
    check(any("Who is buying" in (p.get("table") or "") for p in payload["page"]),
          "the narrative step's payload carries the computed panels (the read's inputs)")
    t_rows = {r[0]: r for r in next(s_ for s_ in full["sections"]
                                    if s_["id"] == "tape")["tables"][0]["rows"]}
    flagged = (f"Bitcoin closed the week at {t_rows['BTC'][1]}, {t_rows['BTC'][3]} on "
               f"the week, alongside the mNAV flag for Strategy.")
    r = da_.write_read(full, cfg, client=kw["client"](flagged, []))
    check(not r["published"] and "flag" in str(r["reason"]).lower(),
          f"THE FLAG-WORD AUDIT: a read naming a flag the page does not print is "
          f"withheld ({str(r['reason'])[:80]})")
    plain = (f"Bitcoin closed the week at {t_rows['BTC'][1]}, {t_rows['BTC'][3]} on the "
             f"week and {t_rows['BTC'][4]} over 30 days, alongside ether at "
             f"{t_rows['ETH'][1]}.")
    r2 = da_.write_read(full, cfg, client=kw["client"](plain, []))
    check(r2["published"], f"a read of the page's figures publishes ({r2.get('reason')})")


if __name__ == "__main__":
    sys.exit(main())

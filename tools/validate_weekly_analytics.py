"""
Validation gate for W-1.3b -- the Weekly's descriptive analytics (change order of
11 Oct 2026, section 4, items 3.1-3.5). On the Weekly's fixture payload with a
scripted writer, a seeded voices store and seeded positioning series; no network,
no box, no register write (register rows are dicts in memory).

  A  NARRATIVES (3.1). Items carry a source class and an event cluster; the count
     is by cluster ("2 clusters for, 0 against") on a fixture of duplicate items,
     never by item; a steelman row for every story -- found, or "none found after
     search" with its queries; the status from the fixed vocabulary by rule
     (tradeable, priced, catalysed, long-term theme); an unreachable source with
     its last clean scan and the theses that depend on it; the excerpt beside the
     label in the ledger.
  B  EXCEPTIONS (3.2). The three tiers as the tables' grouping and order; the
     level / change / extreme labels; resolution path, catalyst and invalidation.
  C  POSITIONING (3.3). The four-week change z's arithmetic against an
     independent computation; TFF categories as % of open interest and ETF share
     counts with level and change z; a thin sentiment sample marked and kept out
     of the composite; TIC's reference month and release date.
  D  WHAT'S PRICED (3.4). The event x venue matrix: the venues' probabilities of
     one outcome and the disagreement column, flagged at the threshold; different
     contracts are not compared; no consensus feed prints a dash.
  E  THE PLAYBOOK (3.5). On the CPI fixture: three outcomes x transmission,
     amplifying positioning and the read -- nine cells; the amplifier rule; a read
     with a figure withheld and retried.

    python tools/validate_weekly_analytics.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import os
import sys
import types
from pathlib import Path
from statistics import mean, pstdev

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import validate_weekly_stack as W                              # noqa: E402

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


T0 = "2026-10-01T15:00:00+00:00"


def seed_voices(db: str, sid: str) -> None:
    """Three items from one speech page (one cluster), one from another outlet,
    all FOR the story; a counter-case voice; a source now unreachable whose
    evidence the story leans on."""
    from altdata import narratives, voices as vmod
    # The story itself, in the gate's temporary register (never a real one).
    with narratives.NarrativeRegister(db) as reg:
        reg.conn.execute(
            "INSERT OR IGNORE INTO narratives (narrative_id, name, status, state, "
            "direction, linked_dimensions, linked_instruments, implied_outcome, "
            "origin, created_at, updated_at) VALUES (?, 'Fixture story', 'active', "
            "'emerging', 'up', '{}', '[\"NVDA\"]', '{}', 'fixture', ?, ?)",
            (sid, T0, T0))
        reg.conn.commit()
    with vmod.VoicesStore(db) as vs:
        c = vs.conn

        def voice(n, outlet, url, kind, view, source_id, day="2026-10-01"):
            cur = c.execute(
                "INSERT INTO voices (voice, voice_key, affiliation, kind, view, "
                "directions, source_id, outlet, source_url, published_at, "
                "retrieved_at, tier, origin, created_at) VALUES "
                "(?, ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?, 1, 'fixture', ?)",
                (n, n.lower().replace(" ", "_"), outlet, kind, view, source_id, outlet,
                 url, f"{day}T14:00:00+00:00", T0, T0))
            return cur.lastrowid

        def evid(vid, side, url, outlet, summary):
            c.execute("INSERT INTO narrative_evidence (narrative_id, side, voice_id, "
                      "summary, outlet, source_url, published_at, retrieved_at, tier, "
                      "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
                      (sid, side, vid, summary, outlet, url, "2026-10-01T14:00:00+00:00",
                       T0, T0))
        for i, nm in enumerate(("Governor A", "Governor B", "Governor C")):
            u = f"https://www.federalreserve.gov/newsevents/speech/x{i}.htm"
            evid(voice(nm, "Federal Reserve Board", u, "official",
                       f"Spending holds up ({i})", "fed_speeches"), "for", u,
                 "Federal Reserve Board", f"The governor said spending holds up ({i}).")
        u = "https://www.example-desk.com/notes/outlook"
        evid(voice("Desk D", "Example Desk", u, "sell_side", "Spending keeps rising",
                   "desk_d"), "for", u, "Example Desk", "The desk sees spending rising.")
        voice("Skeptic E", "Example Press", "https://press.example.com/a",
              "independent", "A capex cut is coming at the largest buyers", "press_e")
        c.execute("INSERT INTO voice_scan_runs (run_id, source_id, source_name, "
                  "started_at, state) VALUES ('r0', 'desk_d', 'Example Desk', "
                  "'2026-09-28T10:00:00+00:00', 'ok')")
        c.execute("INSERT INTO voice_scan_runs (run_id, source_id, source_name, "
                  "started_at, state, reason) VALUES ('r1', 'desk_d', 'Example Desk', "
                  "'2026-10-02T10:00:00+00:00', 'unreachable', 'HTTP 403')")
        c.commit()
        vmod.steelman_pass(vs, {sid: {}}, {"narratives": {"stories": {
            sid: {"steelman_queries": ["capex cut", "overbuild"]}}}}, "2026-10-02", "r1")


def seed_positioning(db: str) -> None:
    from altdata import observations
    end = dt.date.fromisoformat(W.ENDING)
    rows = []
    for k in range(110):                      # weekly, two years
        d = (end - dt.timedelta(days=7 * (109 - k))).isoformat()
        rows.append({"registry_key": "cftc.tff_lev_money_net_oi", "instrument": "JPY",
                     "observed_at": d, "available_at": f"{d}T21:00:00+00:00",
                     "value": -10.0 + (k % 5) * 0.5 + (12.0 if k == 109 else 0.0),
                     "source": "fixture"})
    for k in range(400):                      # daily share counts
        d = (end - dt.timedelta(days=399 - k)).isoformat()
        rows.append({"registry_key": "etf.gld_shares", "instrument": None,
                     "observed_at": d, "available_at": f"{d}T22:00:00+00:00",
                     "value": 300e6 + (k % 7) * 1e5 + (5e6 if k >= 395 else 0),
                     "source": "fixture"})
    with observations.ObservationStore(db) as st:
        st.write_many(rows)


def reads_client(bad_first: bool = True):
    n = {"k": 0}

    def create(**k):
        n["k"] += 1
        fig = " by 2%" if bad_first and n["k"] == 1 else ""
        return W.Resp("HOT: Rates would reprice the path higher and stocks would "
                      f"give ground{fig}.\nIN-LINE: The week would turn to the "
                      "other releases.\nCOOL: The rate path would ease and stocks "
                      "would find support.")
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create)), n


def main() -> int:
    from altdata import config
    from daily_cascade import analytics as an, weekly_stack as ws
    print(f"{LINE}\nW-1.3b -- THE WEEKLY'S DESCRIPTIVE ANALYTICS (synthetic week ending "
          f"{W.ENDING})\n{LINE}")
    acfg = an.load_config()
    td = W.gate_mkdtemp(prefix="validate_weekly_analytics_")
    config.COMPUTED_DIR = str(Path(td) / "computed")
    db = str(Path(td) / "weekly.db")
    logp = Path(td) / "attention-log.md"
    logp.write_text("| date | kind | minutes | note |\n|---|---|---|---|\n",
                    encoding="utf-8")
    seeded = W.seed(db)
    p = W.payload(seeded)
    sid = str(((p.get("narratives") or {}).get("narratives") or [{}])[0].get("id"))
    seed_voices(db, sid)
    seed_positioning(db)
    import validate_weekly_edits as E
    E.seed_calendar(db, W.ENDING)
    out = ws.produce(p, archive_dir=str(Path(td) / "reports"), client=W.client([]),
                     db_path=db, log_path=logp, dry_run=True)
    ed = out["edition"]
    sec = {s["id"]: s for s in ed["sections"]}
    det = {d["title"]: d for d in ed.get("detail") or []}

    # --- A ------------------------------------------------------------------
    print(f"\n{LINE}\nA. NARRATIVES\n{LINE}")
    dup = an.annotate([
        {"narrative_id": "s", "side": "for", "source_url": "https://www.fed.gov/a",
         "published_at": "2026-10-01T14:00", "kind": "official", "outlet": "Fed"},
        {"narrative_id": "s", "side": "for", "source_url": "https://fed.gov/b",
         "published_at": "2026-10-01T16:00", "kind": "official", "outlet": "Fed"},
        {"narrative_id": "s", "side": "for", "source_url": "https://fed.gov/c",
         "published_at": "2026-10-01T18:00", "kind": "official", "outlet": "Fed"},
        {"narrative_id": "s", "side": "for", "source_url": "https://desk.com/x",
         "published_at": "2026-10-01T18:00", "kind": "sell_side", "outlet": "Desk"},
        {"narrative_id": "s", "side": "for", "source_url": "https://fed.gov/d",
         "published_at": "2026-10-02T18:00", "kind": "official", "outlet": "Fed"}],
        acfg)
    cc = an.cluster_counts(dup)
    check(cc == {"for": 3, "against": 0, "items": 5}
          and an.count_text(cc) == "3 clusters for, 0 against",
          f"five items, three clusters (URL root, date, subject): counted by cluster ({cc})")
    check([r["source_class"] for r in dup][:4] == ["official", "official", "official",
                                                   "sell-side"]
          and an.source_class({"kind": "independent", "outlet": "BLS release"}, acfg)
          == "data"
          and an.source_class({"kind": "independent", "outlet": "Reuters"}, acfg)
          == "press",
          "source classes: official / data / sell-side / press")
    nar = sec["narratives"]
    st_tab = next((ss["table"] for ss in nar.get("subsections") or []
                   if ss["title"] == "Stories"), {})
    row = (st_tab.get("rows") or [[]])[0]
    check(row and row[3] == "2 clusters for, 0 against",
          f"in the edition: four items, two clusters ({row[3] if row else None})")
    check(row and row[4].startswith("Skeptic E (Example Press") and "capex cut" in row[4],
          f"the steelman row prints what the scan's search found ({row[4] if row else None})")
    check(an.steelman_text({"found": [], "queries": ["a", "b"]}, ["a", "b"])
          == "none found after search: a; b"
          and an.steelman_text(None, ["a"]).startswith("not searched this week"),
          "none found after search prints with its queries; no search says so")
    check(all(len(r) >= 5 and r[4] for r in st_tab.get("rows") or []),
          "a steelman cell on every story row")
    statuses = {r[2].split(" (")[0] for r in st_tab.get("rows") or []}
    check(statuses and statuses <= set(an.STATUSES),
          f"every status is in the vocabulary ({statuses})")
    sp = {"linked_instruments": ["NVDA"]}
    cfg2 = {"narratives": {"catalyst_window_days": 30, "stories": {"x": {
        "catalysts": [{"date": "2026-10-20", "what": "the event"}],
        "priced": {"key": "k", "level": 1.0, "side": "above", "label": "k at 1.0"}}}}}
    now = "2026-10-04T09:00:00+00:00"
    s1 = an.story_status("x", sp, cfg2, now=now, latest=lambda k, i=None: 0.5,
                         register_rows=[{"instrument": "NVDA", "status": "draft"}])
    s2 = an.story_status("x", sp, cfg2, now=now, latest=lambda k, i=None: 1.2)
    s3 = an.story_status("x", sp, cfg2, now=now, latest=lambda k, i=None: 0.5)
    s4 = an.story_status("y", sp, cfg2, now=now, latest=lambda k, i=None: 0.5,
                         earnings_dates={"NVDA": "2026-12-20"})
    s5 = an.story_status("y", sp, cfg2, now=now, earnings_dates={"NVDA": "2026-10-14"})
    check([s1[0], s2[0], s3[0], s4[0], s5[0]] == ["tradeable", "priced", "catalysed",
                                                  "long-term theme", "catalysed"],
          f"the rules: a drafted packet, the implied level, a catalyst inside 30 days "
          f"(declared or a linked name's earnings), else long-term "
          f"({[s1[0], s2[0], s3[0], s4[0], s5[0]]})")
    un = next((ss["table"] for ss in nar.get("subsections") or []
               if ss["title"] == "Sources the scan could not read"), {})
    ur = (un.get("rows") or [[]])[0]
    check(ur and ur[0] == "Example Desk" and ur[1] == "HTTP 403"
          and ur[2] == "2026-09-28" and ur[3] not in ("", "no active thesis"),
          f"an unreachable source: its last clean scan and the theses on it ({ur})")
    led = det.get("The narrative ledger, this week: every item with its class, "
                  "cluster and excerpt") or {}
    lr = (led.get("table") or {}).get("rows") or []
    check(lr and any(r[5] == "The desk sees spending rising." and
                     r[4] == "Desk D (Example Desk)" for r in lr)
          and {r[2] for r in lr} >= {"official", "sell-side"},
          "the ledger: each item's excerpt beside its label, with its class")

    # --- B ------------------------------------------------------------------
    print(f"\n{LINE}\nB. EXCEPTIONS\n{LINE}")
    from daily_cascade.cadence import Period
    subs, data = ws.exception_subsections(
        ["extreme:yfinance.mkt_spy", "contradiction:equities_vs_credit",
         "extreme:fred.hy_oas"], {"exceptions_opened": ["extreme:fred.hy_oas"]},
        {}, None, now, Period.of("weekly"))
    check([s["tier"] for s in subs] == ["leading", "contradiction", "extreme"]
          and subs[0]["title"].endswith("potential leading indicator"),
          f"three tiers, in order, as the tables' grouping ({[s['tier'] for s in subs]})")
    r0 = subs[0]["table"]["rows"][0]
    check(subs[0]["table"]["columns"] == ["Exception", "Labels", "Exception since",
                                          "Resolution path", "Catalyst", "Invalidation"]
          and all(x not in ("", None) for x in r0[3:]) and "opened this week" in r0[2],
          "each exception carries resolution path, catalyst and invalidation")
    base = [(f"2021-{1 + i // 28:02d}-{1 + i % 28:02d}", 100 + (i % 9) * 0.1)
            for i in range(300)]
    hi = base + [("2022-01-15", 140.0)]
    labs = an.series_labels([(f"{2021 + (i // 336)}-{1 + (i // 28) % 12:02d}-"
                              f"{1 + i % 28:02d}", v) for i, (_, v) in enumerate(hi)],
                            acfg)
    mid = an.series_labels([(f"2021-{1 + i // 28:02d}-{1 + i % 28:02d}",
                             100 + (i % 9) * 0.1 + (0.4 if i == 299 else 0))
                            for i in range(300)], acfg)
    check(labs == ["level", "change", "extreme"] and "extreme" not in mid,
          f"level / change / extreme: all three at a jump to a new bound ({labs}); "
          f"none of extreme mid-range ({mid})")
    check("extreme" in [x["tier"] for x in data] and all("labels" in x for x in data),
          "every exception row carries its labels")

    # --- C ------------------------------------------------------------------
    print(f"\n{LINE}\nC. POSITIONING\n{LINE}")
    pts = [((dt.date(2025, 1, 6) + dt.timedelta(days=7 * k)).isoformat(),
            float((k * 3) % 11) + (20.0 if k == 59 else 0.0)) for k in range(60)]
    got = an.change_z(pts, 4)
    vals = [v for _, v in pts]
    ch = [vals[i] - vals[i - 4] for i in range(4, 60)]
    want = (ch[-1], (ch[-1] - mean(ch[:-1])) / pstdev(ch[:-1]))
    check(got and abs(got[0] - want[0]) < 1e-9 and abs(got[1] - want[1]) < 1e-9,
          f"the four-week change z: ({got[0]:.2f}, {got[1]:.2f}) against an "
          f"independent ({want[0]:.2f}, {want[1]:.2f})")
    pos = sec["positioning"]
    tff = next((ss for ss in pos.get("subsections") or []
                if ss["title"].startswith("Futures positioning by trader type")), {})
    tr = (tff.get("table") or {}).get("rows") or []
    check(tr and tr[0][0] == "JPY futures" and tr[0][1] == "Leveraged funds"
          and tr[0][2].endswith("%") and tr[0][4] not in ("—", None)
          and float(tr[0][4]) > 2,
          f"TFF as % of open interest, the level z and the change z beside it ({tr[:1]})")
    etf = next((ss for ss in pos.get("subsections") or []
                if ss["title"] == "ETF share counts"), {})
    er = (etf.get("table") or {}).get("rows") or []
    check(er and er[0][0] == "GLD shares outstanding" and "m shares" in er[0][1]
          and any("IBIT" in x for x in etf.get("not_tracked") or []),
          "ETF share counts where stored; the rest named as not stored")
    cf = next((ss for ss in pos.get("subsections") or []
               if ss["title"] == "Speculative positioning (CFTC)"), {})
    check("Four-week change z" in ((cf.get("table") or {}).get("columns") or []),
          "the CFTC table prints the change z beside the level z")
    rows_s = [{"n": 3}, {"n": 5}]
    check(an.thin_cell(3, 4) == "thin sample (n=3)" and an.thin_cell(4, 4) is None
          and an.composite_members(rows_s, 4) == [{"n": 5}],
          "a sentiment row under the threshold prints 'thin sample (n=3)' and is "
          "excluded from the composite")
    pdat = pos.get("data") or {}
    thin = [k for k, v in pdat.items() if k.startswith("rtat:") and v.get("thin")]
    check(not set(thin) & set(pdat.get("sentiment_composite_members") or []),
          "no thin row is a composite member in the edition")
    from daily_cascade import weekly_sections as wsec
    check(wsec.lag_label("tic.flow_net_foreign", "2026-07-31", "2026-09-18")
          == "lag: monthly (July, released 2026-09-18)",
          "TIC prints its reference month and release date")

    # --- D ------------------------------------------------------------------
    print(f"\n{LINE}\nD. WHAT'S PRICED: THE MATRIX\n{LINE}")
    fed = {"meetings": [{"meeting": "2026-10-28", "direction": "cut",
                         "move_probability_25bp": 0.80}]}
    odds = {"2026-10-28": {"kalshi": {"hike": 0.0, "hold": 0.4, "cut": 0.6},
                           "polymarket": {"hike": 0.0, "hold": 0.25, "cut": 0.75}}}
    cpi_m = [{"venue": "kalshi", "question": "CPI above 0.3% in September?",
              "probability": 0.40, "close_at": "2026-10-14"},
             {"venue": "polymarket", "question": "September CPI above 0.2%?",
              "probability": 0.70, "close_at": "2026-10-14"}]
    mx = an.matrix([{"event": "FOMC meeting", "date": "2026-10-28",
                     "cls": "fomc_decision"},
                    {"event": "CPI", "date": "2026-10-14", "cls": "inflation_print"},
                    {"event": "JOLTS", "date": "2026-10-13", "cls": "labour_data"}],
                   cpi_m, fed, odds, 15.0, acfg)
    t = mx["table"]
    check(t["columns"] == ["Event (outcome)", "Fed funds futures", "Kalshi",
                           "Polymarket", "Economist consensus", "Disagreement"],
          "the matrix: an event's row across fed funds, Kalshi, Polymarket and the "
          "consensus, then the disagreement")
    check(t["rows"][0][:5] == ["FOMC meeting (cut)", "80%", "60%", "75%", "—"]
          and t["rows"][0][5] == "20 pts -- at or beyond the 15-point threshold",
          f"FOMC: each venue's probability of the same outcome; 20 pts flagged "
          f"({t['rows'][0]})")
    check(t["rows"][1][5] == "not compared: the markets list different contracts"
          and len(t["rows"]) == 2,
          "different contracts are not compared; a class with no matrix is skipped")
    pm = next((ss for ss in sec["priced"].get("subsections") or []
               if ss["title"] == "Prediction markets"), {})
    check(any((x.get("columns") or [None])[0] == "Event (outcome)"
              for x in pm.get("tables") or [])
          or any("No tier-1 event" in x for x in sec["priced"].get("notes") or []),
          "What's priced carries the matrix in its prediction-market block")

    # --- E ------------------------------------------------------------------
    print(f"\n{LINE}\nE. THE PLAYBOOK (CPI)\n{LINE}")
    pos_fx = {"cftc:UST10Y": {"z_2y": 2.1, "level": 250000},
              "cftc:SP500": {"z_2y": 1.8, "level": 90000},
              "cftc:VIX": {"z_2y": -1.6, "level": -60000},
              "cftc:GOLD": {"z_2y": 0.3, "level": 1000}}
    pb = an.playbook({"event": "CPI", "cls": "inflation_print"}, pos_fx, 1.5, acfg)
    hot, inl, cool = pb["rows"]
    check(hot["transmission"] == "yields up, dollar up, equities down, vol up"
          and cool["transmission"] == "yields down, dollar down, equities up, vol down",
          "the transmission channels, per outcome, from the config map")
    check("10-year note futures" in hot["amplify"] and "S&P 500 futures" in hot["amplify"]
          and "VIX futures" in hot["amplify"]
          and cool["amplify"] == "no crowded position against it"
          and "gold" not in hot["amplify"],
          f"hot forces out the crowded longs in notes and stocks and the crowded VIX "
          f"short; cool forces out none; an uncrowded contract never prints "
          f"({hot['amplify']})")
    # THE REGIME SWITCH (ruled 12 Oct 2026): a cool growth print reads two-sided
    # on equities and vol when the fed funds path prices hikes; not otherwise.
    days = ("2026-10-28", "2026-12-09", "2027-01-27", "2027-03-17", "2027-04-28")
    rising = {"meetings": [{"meeting": d, "post_pct": 4.00 + 0.10 * i}
                           for i, d in enumerate(days)]}
    flat = {"meetings": [{"meeting": d, "post_pct": 4.00 - 0.05 * i}
                         for i, d in enumerate(days)]}
    two = "two-sided — rates relief against growth fear"
    gh = an.playbook({"event": "GDP", "cls": "growth_print"}, pos_fx, 1.5, acfg,
                     fed=rising)
    gf = an.playbook({"event": "GDP", "cls": "growth_print"}, pos_fx, 1.5, acfg,
                     fed=flat)
    check(an.hikes_priced(rising) is True and an.hikes_priced(flat) is False
          and an.hikes_priced(None) is None,
          "the regime read: hikes priced when the implied rate rises from the next "
          "meeting over the following four")
    check(gh["rows"][2]["transmission"] == f"yields down, dollar down, equities {two}, "
          f"vol {two}" and gh["regime_switched"]
          and gh["rows"][0]["transmission"] == gf["rows"][0]["transmission"],
          "with hikes priced, a cool growth print's equity and vol cells read "
          "two-sided; hot is unchanged")
    check(gf["rows"][2]["transmission"] == "yields down, dollar down, equities down, "
          "vol up" and not gf["regime_switched"],
          "without hikes priced, the map stands: equities down, vol up")
    ch_ = an.playbook({"event": "CPI", "cls": "inflation_print"}, pos_fx, 1.5, acfg,
                      fed=rising)
    check(ch_["rows"][2]["transmission"] == cool["transmission"],
          "the switch is the growth print's only: a cool CPI is unchanged")
    check("S&P 500 futures" not in gh["rows"][2]["amplify"]
          and "VIX futures" not in gh["rows"][2]["amplify"],
          "a two-sided channel amplifies no crowded position")
    cl, n = reads_client()
    an.write_playbook(pb, client=cl)
    tb = an.playbook_table(pb)
    cells = [c for r in tb["rows"] for c in r[1:]]
    check(len(tb["rows"]) == 3 and len(cells) == 9
          and all(c not in ("", None, "—") for c in cells),
          "nine cells: three outcomes x transmission, amplifying positioning, read")
    check(n["k"] == 2 and pb.get("attempts") == 2 and pb["read_state"] == "published",
          "a read sentence with a figure is withheld and the retry publishes")
    ah = sec["ahead"]
    pss = next((ss for ss in ah.get("subsections") or [] if ss.get("playbook")), {})
    check(pss.get("title") == "Playbook: CPI" and len((pss.get("table") or {})
                                                      .get("rows") or []) == 3,
          "in the edition, the CPI playbook fills Ahead's slot")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

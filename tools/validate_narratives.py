"""
Validation gate for the narrative register and the 07:00 scan (6c-2).

    python tools/validate_narratives.py

Against a TEMPORARY database -- set through CHESTER_DB before anything is imported,
so every default store in the process points at the fixture -- with synthetic
events and synthetic market-state objects. The verdict is the same on a runner with
no store as on the box. No network and no key: the model is an injected client.

  A  TRANSITIONS REPLAY EXACTLY FROM STORED EVENTS. A story is moved emerging ->
     consensus over stored sessions; replay() recomputes every evaluation from the
     stored events and objects and matches field for field -- and a tampered event
     makes it NOT match, or the replay proves nothing.
  B  A NARRATIVE WITH NO EVIDENCE CANNOT BE CONSENSUS. Attention and agreement past
     their thresholds for three times the persistence count, and no evidence: the
     story stays emerging. One evidence event, and it moves after the persistence
     count and not before.
  C  A PROPOSAL NEVER REACHES CONSENSUS WITHOUT CONFIRMATION. A proposal under the
     same winning inputs is never evaluated; the schema refuses a direct write of
     any state but emerging; only after `confirm` is it evaluated.
  D  THE NO-FETCH GUARD COVERS THE NARRATIVE BLOCK. The story block and the
     renderers name no network call, and the block builds and renders with the
     socket layer removed.
  E  narrative_vs_data: a consensus story whose linked dimension points the other
     way meets the condition, and opens on persistence, per story.
  F  GRADING. Entering consensus emitted exactly one forecast with a machine
     criterion; resolution reads the stored series at the horizon and writes the
     Brier; the Weekly's GRADES carry a narratives row.
  H  EVERY SEEDED STORY CAN REACH CONSENSUS (6c-3): each has an evidence rule
     that can yield a FOR; the yen carry's and the midterm's rules end to end.
  I  THE MIDTERM HYPOTHESES (6c-3): shrunk prior, entered once and ex ante,
     never 0 or 1, resolved on the close on or before each date.
  J  CITED EVENTS ARE QUOTED; ABSENT IS A FIELD (6c-3): the payload carries
     stored type and source and structured absences; the audit withholds a
     contradicting citation and a present row called missing.
  K  A NAMED STATE IS THE STORED ONE (6c-3): a state word beside a dial or
     dimension name must be the object's; absent means no state word at all.
  G  THE 07:00 PROSE. A PROPOSALS block is split off before the audit; a cited event
     id outside the payload withholds the block; the numeral and type verdicts are
     reported apart; a valid proposal is written as `proposed`.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# BEFORE ANY IMPORT: every default store in this process is the fixture.
_TMP = tempfile.mkdtemp(prefix="validate_narratives_")
DB = os.path.join(_TMP, "fixture.sqlite")
os.environ["CHESTER_DB"] = DB
os.environ.setdefault("CHESTER_STATE_DIR", _TMP)

from altdata import events as ev_mod  # noqa: E402
from altdata import narratives as nr  # noqa: E402
from altdata import observations, probability_ledger  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
# Real trading sessions, so the calendar's session arithmetic is exercised.
SESSIONS = ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18",
            "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25"]
QUERY = "ai_capex_durability"          # a declared query, so the seed validates


def cfg_fixture() -> dict:
    return {
        "version": "narratives-fixture",
        "probability_by_state": {"consensus": 0.70, "fading": 0.30},
        "rules": {
            "attention_sessions": {"short": 2, "long": 4},
            "evidence_window_days": 60,
            "persistence_sessions": 2,
            "consensus": {"min_attention_long": 3, "min_agreement": 0.66,
                          "min_evidence_for": 1,
                          "evidence_for_must_exceed_against": True},
            "contested": {"min_attention_long": 3, "max_agreement": 0.34,
                          "min_evidence_against": 1},
            "fading": {"max_short_to_long_rate": 0.5,
                       "require_short_delta_negative": True},
            "revive": {"min_short_to_long_rate": 1.0, "min_attention_long": 3},
        },
        "transition_alert_path": "report_only",
        "narratives": {"fixture_story": {
            "name": "Fixture story",
            "direction": "Credit keeps tightening.",
            "story_query": QUERY,
            "linked_dimensions": {"credit": "+"},
            "linked_instruments": ["AAA"],
            "prediction_market_contracts": [],
            "evidence": {"earnings": {"symbols": ["AAA"], "sign": "+"}},
            "implied_outcome": {"claim": "HY OAS lower in 30 days.",
                                "metrics": ["fred.hy_oas"], "comparison": "down",
                                "quorum": 1, "horizon_days": 30},
        }},
    }


def put_object(store, day: str, direction: str) -> None:
    obj = {"object": "market_state", "session": day,
           "computed_at": f"{day}T20:50:00.000000+00:00",
           "dimensions": {"credit": {"state": "easy", "direction": direction}},
           "contradictions": []}
    store.write("market_state", None, day, obj["computed_at"],
                json.dumps(obj, sort_keys=True), source="derived_state")


def put_headlines(day: str, n: int) -> list[int]:
    evs = [ev_mod.Event("headline", f"{day}T14:{i:02d}:00+00:00", "fixture_news",
                        f"Fixture headline {day} {i} - Reuters",
                        payload={"query": QUERY, "theme": "fixture"})
           for i in range(n)]
    with ev_mod.EventStore() as ev:
        ev.write_many(evs, available_at=f"{day}T15:00:00+00:00")
        return [r[0] for r in ev.conn.execute(
            "SELECT id FROM events WHERE observed_at LIKE ? AND type='headline'",
            (f"{day}%",))]


def put_earnings(day: str, symbol: str, surprise: float) -> int:
    e = ev_mod.Event("earnings", f"{day}T20:05:00+00:00", "fixture_earnings",
                     f"{symbol} reported", payload={"symbol": symbol,
                                                     "surprise_pct": surprise})
    with ev_mod.EventStore() as ev:
        ev.write_many([e], available_at=f"{day}T20:10:00+00:00")
        return ev.conn.execute("SELECT MAX(id) FROM events").fetchone()[0]


def evaluate(day: str, cfg: dict) -> dict:
    return nr.evaluate(day, f"{day}T21:00:00+00:00", cfg=cfg)


def state(nid: str) -> str:
    with nr.NarrativeRegister() as reg:
        return (reg.get(nid) or {}).get("state")


# ---------------------------------------------------------------------------
def groups_abc() -> None:
    cfg = cfg_fixture()
    store = observations.ObservationStore()
    try:
        with nr.NarrativeRegister() as reg:
            out = reg.seed(cfg, today=SESSIONS[0])
        check(out["inserted"] == ["fixture_story"] and not out["refused"],
              f"the fixture story seeds ({out})")
        # The implied outcome's series, known before the story moves, so the
        # forecast carries a real baseline.
        store.write("fred.hy_oas", None, "2026-09-10", "2026-09-11T12:00:00Z",
                    3.10, source="fred")

        print(f"{LINE}\nB. NO EVIDENCE, NO CONSENSUS\n{LINE}")
        # Six sessions of attention and full agreement, no evidence at all.
        for day in SESSIONS[:6]:
            put_object(store, day, "+")
            put_headlines(day, 3)
            evaluate(day, cfg)
        check(state("fixture_story") == "emerging",
              "attention past threshold and agreement 1.0 for 6 sessions (3x the "
              "persistence count) with no evidence: still emerging")
        with nr.NarrativeRegister() as reg:
            conds = [json.loads(r[0]) for r in reg.conn.execute(
                "SELECT conditions FROM narrative_evaluations WHERE "
                "narrative_id='fixture_story' ORDER BY session")]
        check(not any(c["consensus"] for c in conds),
              "and the consensus condition never held -- the evidence count is a "
              "gate, not a weight")

        # One beat: the next session meets the condition (run 1) and the one
        # after moves it (run 2 = persistence).
        eid = put_earnings(SESSIONS[6], "AAA", 5.0)
        put_object(store, SESSIONS[6], "+")
        put_headlines(SESSIONS[6], 3)
        r1 = evaluate(SESSIONS[6], cfg)
        check(state("fixture_story") == "emerging" and not r1["transitions"],
              f"one evidence event: the condition holds for its first session "
              f"(event {eid}) and the state does not move yet")
        put_object(store, SESSIONS[7], "+")
        put_headlines(SESSIONS[7], 3)
        r2 = evaluate(SESSIONS[7], cfg)
        check(state("fixture_story") == "consensus"
              and [t["to"] for t in r2["transitions"]] == ["consensus"],
              "and the next session, at the persistence count, it becomes "
              "consensus")

        print(f"{LINE}\nC. A PROPOSAL NEVER REACHES CONSENSUS UNCONFIRMED\n{LINE}")
        spec = dict(cfg["narratives"]["fixture_story"], name="Proposed story")
        with nr.NarrativeRegister() as reg:
            reg.propose("proposed_story", spec, [eid], proposed_by="validator")
        cfg["narratives"]["proposed_story"] = spec
        for day in SESSIONS[8:10]:
            put_object(store, day, "+")
            put_headlines(day, 3)
            evaluate(day, cfg)
        with nr.NarrativeRegister() as reg:
            n = reg.conn.execute(
                "SELECT COUNT(*) FROM narrative_evaluations WHERE "
                "narrative_id='proposed_story'").fetchone()[0]
            row = reg.get("proposed_story")
        check(n == 0 and row["status"] == "proposed" and row["state"] == "emerging",
              "under the same winning inputs a proposal is never evaluated and "
              "stays emerging")
        try:
            with nr.NarrativeRegister() as reg:
                reg.conn.execute("UPDATE narratives SET state='consensus' WHERE "
                                 "narrative_id='proposed_story'")
                reg.conn.commit()
            bad("the schema refuses a direct state write to a proposal")
        except Exception:                                      # noqa: BLE001
            ok("the schema refuses a direct state write to a proposal (trigger)")
        with nr.NarrativeRegister() as reg:
            reg.confirm("proposed_story", by="validator", today=SESSIONS[9])
        nxt = "2026-09-28"
        put_object(store, nxt, "+")
        put_headlines(nxt, 3)
        evaluate(nxt, cfg)
        with nr.NarrativeRegister() as reg:
            n = reg.conn.execute(
                "SELECT COUNT(*) FROM narrative_evaluations WHERE "
                "narrative_id='proposed_story'").fetchone()[0]
        check(n == 1, "after `confirm` it is evaluated like any active story")

        print(f"{LINE}\nA. REPLAY FROM STORED EVENTS\n{LINE}")
        r = nr.replay(cfg=cfg)
        check(r["compared"] >= 11 and r["matched"] == r["compared"]
              and not r["mismatches"],
              f"every stored evaluation recomputes exactly from the stored events "
              f"and objects ({r['matched']}/{r['compared']})")
        with ev_mod.EventStore() as ev:
            ev.conn.execute("UPDATE events SET payload = ? WHERE id = ?",
                            (json.dumps({"symbol": "AAA", "surprise_pct": -5.0}),
                             eid))
            ev.conn.commit()
        r = nr.replay(cfg=cfg)
        check(bool(r["mismatches"]),
              f"and a tampered evidence event makes the replay FAIL "
              f"({len(r['mismatches'])} mismatched) -- a replay that cannot fail "
              f"proves nothing")
        with ev_mod.EventStore() as ev:
            ev.conn.execute("UPDATE events SET payload = ? WHERE id = ?",
                            (json.dumps({"symbol": "AAA", "surprise_pct": 5.0}),
                             eid))
            ev.conn.commit()
        check(not nr.replay(cfg=cfg)["mismatches"], "restored, it matches again")

        print(f"{LINE}\nF. GRADING\n{LINE}")
        with probability_ledger.ProbabilityLedger() as pl:
            rows = [r for r in pl.all_rows() if r["source"] == nr.LEDGER_SOURCE]
        check(len(rows) == 1 and rows[0]["probability"] == 0.70,
              f"entering consensus emitted exactly one forecast at the declared "
              f"0.70; emerging emitted none ({len(rows)})")
        crit = json.loads(rows[0]["resolution_criterion"]) if rows else {}
        check(crit.get("kind") == nr.CRITERION_KIND
              and crit.get("metrics") == ["fred.hy_oas"]
              and crit.get("horizon_date") == "2026-10-23"
              and (crit.get("baseline") or {}).get("fred.hy_oas", {}).get("value")
              == 3.10,
              f"with a machine criterion declared at emission ({crit.get('kind')}, "
              f"horizon {crit.get('horizon_date')}, baseline 3.10 as known then)")
        # A baseline and a value past the horizon, then resolve.
        fid = rows[0]["probability_id"]
        store.write("fred.hy_oas", None, "2026-10-20", "2026-10-21T12:00:00Z", 2.90,
                    source="fred")
        early = nr.resolve_due("2026-10-01T00:00:00Z")
        check(not [x for x in early["resolved"] if x["probability_id"] == fid],
              "before the horizon nothing resolves")
        res = nr.resolve_due("2026-10-24T00:00:00Z")
        got = [x for x in res["resolved"] if x["probability_id"] == fid]
        check(len(got) == 1 and got[0]["outcome"] == 1
              and abs(got[0]["brier"] - 0.09) < 1e-9,
              f"resolution reads the store at the horizon and writes the Brier "
              f"({got[0]['outcome'] if got else '-'}, "
              f"{round(got[0]['brier'], 4) if got else '-'})")
        again = nr.resolve_due("2026-10-25T00:00:00Z")
        check(not [x for x in again["resolved"] if x["probability_id"] == fid],
              "and it resolves once")
        from daily_cascade import weekly_payload as wp
        g = wp.grades("2026-10-30")
        check((g.get("narratives") or {}).get("emitted") == 1
              and (g.get("narratives") or {}).get("resolved") == 1,
              "the Weekly's GRADES carry a narratives row (emitted 1, resolved 1)")
    finally:
        store.close()


def group_d() -> None:
    print(f"{LINE}\nD. THE NO-FETCH GUARD COVERS THE NARRATIVE BLOCK\n{LINE}")
    NET = re.compile("|".join((
        r"(?:^|\s)(?:import|from)\s+(?:requests|yfinance|urllib)\b",
        r"requests\.(?:get|post|request)\s*\(", r"urllib\.request\b",
        r"http_get_(?:json|text|bytes|response)\s*\(", r"socket\.socket\s*\(",
        r"yf\.Ticker\s*\(")))
    for rel in ("daily_cascade/story_block.py", "altdata/narratives.py",
                "daily_cascade/morning_render.py", "daily_cascade/weekly_render.py"):
        src = (REPO / rel).read_text(encoding="utf-8")
        body = "\n".join(ln for ln in src.splitlines()
                         if not ln.lstrip().startswith("#"))
        hits = sorted({m.group(0).strip() for m in NET.finditer(body)})
        check(not hits, f"{rel} names no network call ({hits or 'none'})")
    import socket
    real = socket.socket

    class NoNetwork(socket.socket):
        def __init__(self, *a, **k):
            raise AssertionError("the narrative block tried to open a socket")
    socket.socket = NoNetwork                                   # type: ignore
    try:
        from daily_cascade import morning_render, story_block
        b = story_block.build("2026-09-25", "2026-09-28T11:00:00+00:00")
        html = morning_render.stories_block({"stories": b})
        check(b["state"] == "ok" and "Fixture story" in html,
              "the story block builds and renders with NO SOCKET AVAILABLE")
    except AssertionError as exc:
        bad(str(exc))
    finally:
        socket.socket = real                                    # type: ignore


def group_j() -> None:
    print(f"{LINE}\nJ. CITED EVENTS ARE QUOTED; ABSENT IS A FIELD (6c-3)\n{LINE}")
    from daily_cascade import narrative as nv
    from daily_cascade import story_block

    # --- the payload -----------------------------------------------------------
    obj = {"session": "2026-09-25", "contradictions": [
        {"id": "price_vs_breadth", "open_state": "closed", "open": False},
        {"id": "narrative_vs_data", "open_state": "absent",
         "absent_reason": "the narrative register holds no active story"},
        {"id": "gamma_vs_trend", "open_state": "absent",
         "fault": "dial.gamma: the exposure engine's reader raised OSError: x"}]}
    b = story_block.build("2026-09-25", "2026-09-28T11:00:00+00:00",
                          market_state=obj)
    ab = {r["id"]: r for r in b["contradictions_absent"]}
    check(ab["narrative_vs_data"] == {"id": "narrative_vs_data", "absent": True,
                                      "reason": "the narrative register holds no "
                                                "active story"},
          "an absent row travels as {absent: true, reason} -- present, with why")
    check(ab["gamma_vs_trend"].get("fault") and "reason" not in ab["gamma_vs_trend"],
          "and a faulted row as {absent: true, fault}, never a reason")
    tops = [x for q in (b["events"].get("headlines_by_query") or {}).values()
            for x in (q.get("top") or []) + (q.get("shown_only") or [])]
    rows = (b["events"].get("releases") or []) + (b["events"].get("earnings")
                                                   or []) + tops
    check(bool(rows) and all(r.get("type") and r.get("source") for r in rows),
          f"every event row carries its stored type and source ({len(rows)})")
    ce = {e["event_id"]: e for e in b.get("citable_events") or []}
    check(set(ce) == set(b["citable_event_ids"])
          and all(e.get("type") and e.get("source") for e in ce.values()),
          f"and every citable id is in citable_events with both "
          f"({len(ce)} of {len(b['citable_event_ids'])})")
    np_ = story_block.narrative_payload(b)
    check("citable_events" in np_, "the model's payload carries citable_events")
    for s in (b.get("register") or {}).get("stories") or []:
        e = s.get("evaluation") or {}
        check("absent_reason" not in s and (not e.get("absent") or e.get("reason")),
              f"{s['id']}: an unevaluated story is {{absent: true, reason}}")
        break
    sp = nv.morning_system_prompt()
    check("citable_events" in sp and "absent: true" in sp,
          "the prompt says to quote type and source, and explains absent")

    # --- the audit ----------------------------------------------------------------
    class Resp:
        def __init__(self, t):
            self.content = [types.SimpleNamespace(type="text", text=t)]
            self.model = "fixture-model"
            self.stop_reason = "end_turn"

    class Client:
        def __init__(self, t):
            self.messages = types.SimpleNamespace(create=lambda **k: Resp(t))

    evs = [{"event_id": 1, "type": "release", "source": "fed_press",
            "title": "Federal Reserve Board announces approval of application"},
           {"event_id": 134, "type": "headline", "source": "google_news",
            "title": "Bank of Japan Tightening Bets Spark Yen Recovery"}]
    payload = {"citable_event_ids": [1, 134], "citable_events": evs}
    kw = dict(system_prompt="fixture", max_chars=5000, one_paragraph=False,
              citable_ids=[1, 134], citable_events=evs)

    good = nv.generate(payload, client=Client(
        'A release from fed_press, "Federal Reserve Board announces approval of '
        'application" (event 1), and a headline from google_news, "Bank of Japan '
        'Tightening Bets Spark Yen Recovery" (event 134).'), **kw)
    v = good.verdicts()
    check(good.published and v["citation"] == "pass" and v["presence"] == "pass",
          f"quoted type and source publish ({good.state}; citation "
          f"{v['citation']}; presence {v['presence']})")
    typ = nv.generate(payload, client=Client(
        "Event 1, a headline about bank approvals, is unrelated."), **kw)
    check(typ.state == "miscited" and "called headline" in typ.verdicts()["citation"],
          f"an appositive calling a release a headline withholds "
          f"({typ.verdicts()['citation'][:60]})")
    src = nv.generate(payload, client=Client(
        "The yen story drew a headline from yfinance (event 134)."), **kw)
    check(src.state == "miscited" and "attributed to yfinance"
          in src.verdicts()["citation"],
          "a source word that differs from the stored source withholds")
    ok_title = nv.generate(payload, client=Client(
        'A headline from google_news, "Yen recovery and a release of reserves" '
        '(event 134).'), **kw)
    check(ok_title.published,
          "type words INSIDE a quoted title are not the prose's claim")
    pres = nv.generate(payload, client=Client(
        "narrative_vs_data is absent from the object entirely (event 1)."), **kw)
    check(pres.state == "presence_misstated"
          and pres.verdicts()["presence"].startswith("fail"),
          "a present row called missing from the object withholds the block")
    check(nv.generate(payload, client=Client("x (event 1)."), system_prompt="f",
                      max_chars=5000, one_paragraph=False,
                      citable_ids=[1]).verdicts()["citation"] == "not_run",
          "and a brief that passes no citable_events reports the check not_run")
    tmpl = (REPO / "docs" / "narrative-template-morning.md").read_text(
        encoding="utf-8")
    para = tmpl.split("## Reference paragraph")[1].split("\n## ")[0]
    check("from google_news" in para and not nv.presence_misstatements(para),
          "the template's reference paragraph quotes its sources and calls "
          "nothing missing")


def group_k() -> None:
    print(f"{LINE}\nK. A NAMED STATE IS THE STORED ONE (6c-3)\n{LINE}")
    from daily_cascade import narrative as nv
    from daily_cascade import story_block

    obj = {"session": "2026-09-25",
           "dials": {"gamma": {"state": "positive"},
                     "vol": {"state": None, "absent_reason": "no VIX print"},
                     "macro": {"state": "mixed"}},
           "dimensions": {"trend": {"state": "flat"}, "rates": {"state": "high"},
                          "volatility": {"state": None,
                                         "absent_reason": "stale primary"}},
           "contradictions": []}
    wc = {"dial_changes": [{"dial": "gamma", "from": "negative", "to": "positive"}]}
    ms = story_block.market_states(obj, wc)
    check(ms["gamma"]["state"] == "positive" and ms["gamma"]["previous"] == "negative"
          and set(ms["gamma"]["vocabulary"]) == {"positive", "negative", "flat"},
          "market_states carries gamma's stored state, its previous one and its "
          "declared words")
    check(ms["trend"]["vocabulary"] == ["up", "flat", "down"]
          and "normal" in ms["vol"]["vocabulary"]
          and "goldilocks" in ms["macro"]["vocabulary"],
          "every dimension's, the vol dial's bands' and the macro rules' words")
    check(ms["volatility"].get("absent") and ms["volatility"].get("reason"),
          "an absent state is {absent: true, reason}")
    b = story_block.build("2026-09-25", "2026-09-28T11:00:00+00:00",
                          market_state=obj, what_changed=wc)
    check("market_states" in story_block.narrative_payload(b),
          "and the model's payload carries it")
    check("market_states" in nv.morning_system_prompt(),
          "the prompt says to use the stored words")

    cases = [
        ("gamma-vs-trend, still carrying its positive/flat state pair", True,
         "the 28 September sentence, now vouched for: positive/flat IS the pair"),
        ("gamma-vs-trend carries its negative/flat pair", False,
         "the same sentence with gamma's word wrong fails"),
        ("The gamma dial did move, flipping from negative to positive.", True,
         "a transition matching previous and stored passes"),
        ("The gamma dial did move, flipping from positive to negative.", False,
         "and reversed, fails on both ends"),
        ("a flat trend", True, "a state word before the name"),
        ("an up trend", False, "a wrong word before the name"),
        ("volatility is elevated", False,
         "any state claimed for an ABSENT dimension fails"),
        ("volatility turning up with the headlines", True,
         "a word outside the name's vocabulary is not a claim"),
        ("the vol dial reads normal", False, "the vol dial is absent too"),
        ('a headline, "Gamma is negative" (event 1)', True,
         "words inside a quoted title are not the prose's claim"),
    ]
    for text, passes, why in cases:
        got = nv.state_contradictions(text, ms)
        check((not got) == passes, f"{why} ({got or 'pass'})")

    class Resp:
        def __init__(self, t):
            self.content = [types.SimpleNamespace(type="text", text=t)]
            self.model = "fixture-model"
            self.stop_reason = "end_turn"

    class Client:
        def __init__(self, t):
            self.messages = types.SimpleNamespace(create=lambda **k: Resp(t))

    r = nv.generate({"x": 1}, client=Client("Trend is down."),
                    system_prompt="f", max_chars=5000, one_paragraph=False,
                    citable_ids=[], market_states=ms)
    check(r.state == "state_misstated" and r.verdicts()["state"].startswith("fail"),
          f"generate withholds on it and reports the state verdict apart "
          f"({r.verdicts()['state'][:50]})")
    tmpl = (REPO / "docs" / "narrative-template-morning.md").read_text(
        encoding="utf-8")
    para = tmpl.split("## Reference paragraph")[1].split("\n## ")[0]
    check(not nv.state_contradictions(para, ms),
          "the template's reference paragraph names no state against this object")


def group_l() -> None:
    print(f"{LINE}\nL. SOURCE TIERS AND FED PRESS KINDS (Weekly ed. 1, item 5)\n{LINE}")
    from altdata import source_tiers as st_
    from daily_cascade import events_block, story_block
    check(st_.tier_of("x - WSJ") == 1 and st_.tier_of("x - Seeking Alpha") == 3
          and st_.tier_of("x - The Japan Times") == 2,
          "wires tier 1, regional/trade tier 2, aggregators tier 3")
    check(st_.tier_of("x - Brand New Outlet") is None
          and not st_.counted("x - Brand New Outlet")
          and not st_.counted("no attribution at all"),
          "an unclassified outlet is not counted until it is classified")

    day = "2026-08-12"
    titles = [f"Deficit story {i} - {o}" for i, o in enumerate(
        ["Reuters", "Bloomberg", "The Japan Times", "finance.biggo.com",
         "Seeking Alpha", "Brand New Outlet"])]
    with ev_mod.EventStore() as ev:
        ev.write_many([ev_mod.Event("headline", f"{day}T1{i}:00:00+00:00", "fx", t,
                                    payload={"query": "fiscal_dominance"})
                       for i, t in enumerate(titles)],
                      available_at=f"{day}T20:00:00+00:00")
        att = nr.attention(ev.conn, "fiscal_dominance", day,
                           f"{day}T21:00:00+00:00", 5, 20)
    check(att["short"] == 3 and att["not_counted_tier3_or_unclassified"] == 3,
          f"attention counts the three tier-1/2 items and not the other three "
          f"(counted {att['short']}, not counted "
          f"{att['not_counted_tier3_or_unclassified']})")

    yc = nr.load_config()["narratives"]["yen_carry"]
    t3 = "Carry Trade Exodus Fuels Yen Gain Ahead of BOJ Rate Decision - TradingView"
    with ev_mod.EventStore() as ev:
        ev.write_many([ev_mod.Event("headline", "2026-08-13T10:00:00+00:00", "fx",
                                    t3, payload={"query": "yen_carry"})],
                      available_at="2026-08-13T12:00:00+00:00")
        eid = ev.conn.execute("SELECT MAX(id) FROM events").fetchone()[0]
        store = observations.ObservationStore()
        try:
            got = nr.evidence(ev.conn, yc, "2026-08-13T21:00:00+00:00", 60, store)
        finally:
            store.close()
    check(eid not in got["for"] and "never counted" in got["unscored"].get(
              str(eid), ""),
          "a tier-3 headline the patterns score FOR is not evidence")

    cfg = nr.load_config()
    before = nr.rules_version(cfg, "yen_carry")
    saved = st_._CFG
    try:
        st_._CFG = dict(st_.load(), counted_tiers=[1])
        after = nr.rules_version(cfg, "yen_carry")
    finally:
        st_._CFG = saved
    check(before != after,
          "a change to the tiers changes every story's rules_version")

    fed = [("Federal Reserve Board announces approval of application by Peoples "
            "Bancorp Inc.", "applications"),
           ("Federal Reserve issues FOMC statement", "monetary_policy"),
           ("Speech by Governor Waller on the economic outlook", "speeches"),
           ("Federal Reserve Board issues enforcement action with former employee "
            "of Regions Bank", "supervision")]
    check(all(st_.fed_class(t) == k for t, k in fed),
          "fed_press titles classify: applications / monetary policy / speeches "
          "/ supervision")
    with ev_mod.EventStore() as ev:
        ev.write_many([ev_mod.Event("release", f"2026-08-20T1{i}:00:00+00:00",
                                    "fed_press", t) for i, (t, _) in enumerate(fed)],
                      available_at="2026-08-20T20:00:00+00:00")
    b = story_block.build("2026-08-19", "2026-08-21T11:00:00+00:00")
    kinds = [r.get("fed_kind") for r in b["events"]["releases"]]
    check("applications" not in kinds and len(kinds) == 3
          and b["events"]["fed_press_counts"].get("applications") == 1,
          f"the morning payload lists three and counts the application ({kinds})")
    app_ids = [r[0] for r in ev_mod.EventStore().conn.execute(
        "SELECT id FROM events WHERE title LIKE 'Federal Reserve Board announces "
        "approval%' AND observed_at LIKE '2026-08-20%'")]
    check(not set(app_ids) & set(b["citable_event_ids"]),
          "and an application is never citable")
    eb = events_block.build("2026-08-19T20:00:00+00:00",
                            as_of="2026-08-21T11:00:00+00:00")
    h = events_block.html(eb)
    check("count only: 1" in h and "Peoples Bancorp" not in h
          and "(monetary_policy)" in h,
          "the events block prints applications as a count and lists the rest "
          "with their kind")


def group_e() -> None:
    print(f"{LINE}\nE. narrative_vs_data\n{LINE}")
    import contradictions as contra
    store = observations.ObservationStore()
    try:
        spec = {"id": "narrative_vs_data", "kind": contra.NARRATIVE_KIND,
                "because": "fixture"}
        cut = "2026-09-29T21:00:00+00:00"
        rows = contra.narrative_rows(spec, {"credit": {"state": "neutral",
                                                       "direction": "-"}},
                                     cut, store)
        row = next((r for r in rows if r["id"] == "narrative_vs_data.fixture_story"),
                   None)
        check(row is not None and row["narrative_state"] == "consensus"
              and row["condition_met"] and row["magnitude"] is None
              and row["dimensions_against"] == ["credit"],
              "a consensus story whose linked dimension points the other way "
              "meets the condition -- a state mismatch, no z")
        agree = contra.narrative_rows(spec, {"credit": {"state": "easy",
                                                        "direction": "+"}},
                                      cut, store)
        check(not next(r for r in agree
                       if r["id"] == "narrative_vs_data.fixture_story")
              ["condition_met"],
              "and the same story with the dimension agreeing does not")
        prior = [{"session": "2026-09-28", "condition_met": True, "open": False}]
        opened = contra.apply_persistence(dict(row), prior, "2026-09-29", 2, 5)
        first = contra.apply_persistence(dict(row), [], "2026-09-29", 2, 5)
        check(opened["open"] and not first["open"],
              "it opens on the table's persistence rule, and not on its first "
              "session")
    finally:
        store.close()


def group_g() -> None:
    print(f"{LINE}\nG. THE 07:00 PROSE\n{LINE}")
    from daily_cascade import narrative as nv

    class Resp:
        def __init__(self, t):
            self.content = [types.SimpleNamespace(type="text", text=t)]
            self.model = "fixture-model"
            self.stop_reason = "end_turn"

    class Client:
        def __init__(self, t):
            self.messages = types.SimpleNamespace(create=lambda **k: Resp(t))

    payload = {"register": {"stories": [{"id": "fixture_story",
                                         "attention_long": 12,
                                         "evidence_rows": 13}]},
               "citable_event_ids": [41, 42]}
    prop = ('PROPOSALS: [{"id": "fixture_prop", "name": "Fixture proposal", '
            '"direction": "Spreads widen.", "linked_dimensions": {"credit": "-"}, '
            '"implied_outcome": {"claim": "HY OAS up.", "metrics": ["fred.hy_oas"], '
            '"comparison": "up", "quorum": 1, "horizon_days": 60}, '
            '"basis_events": [41]}]')
    kw = dict(system_prompt="fixture", max_chars=5000, one_paragraph=False,
              split=nv.split_proposals, citable_ids=[41, 42])
    r = nv.generate(payload, client=Client(
        f"The story drew 12 headlines (event 41).\n\n{prop}"), **kw)
    check(r.published and [p["id"] for p in r.extra["proposals"]] == ["fixture_prop"],
          "the PROPOSALS block is split off before the audit -- its horizon_days "
          "(60) is not a figure the prose claims -- and the prose publishes")
    u = nv.generate(payload, client=Client("A claim (event 99)."), **kw)
    check(u.state == "untraceable" and u.untraceable == [99],
          "a cited event id outside the payload withholds the block")
    t = nv.generate(payload, client=Client("A 13-day-old story (event 42)."), **kw)
    v = t.verdicts()
    check(t.state == "audit_failed" and v["numeral"].startswith("pass")
          and v["type"].startswith("fail"),
          f"the numeral and type verdicts are reported apart ({v['numeral']}; "
          f"{v['type'][:40]})")
    m = nv.generate(payload, client=Client("An invented 77 (event 41)."), **kw)
    vm = m.verdicts()
    check(vm["numeral"].startswith("fail") and vm["type"] == "pass",
          f"and a missing figure fails the numeral audit, not the type audit "
          f"({vm['numeral'][:30]})")
    with ev_mod.EventStore() as ev:
        # available_at PINNED: left to default it is the real ingest instant,
        # which passed the later 28 Sep 11:00 cutoffs only while the wall clock
        # was earlier than that -- the gate began failing on 28 Sep itself.
        ev.write_many([ev_mod.Event("headline", "2026-09-28T09:00:00+00:00", "fx",
                                    "basis", payload={"query": QUERY})],
                      available_at="2026-09-28T09:05:00+00:00")
        basis = ev.conn.execute("SELECT MAX(id) FROM events").fetchone()[0]
    spec = dict(r.extra["proposals"][0])
    with nr.NarrativeRegister() as reg:
        reg.propose(spec["id"], spec, [basis], proposed_by="fixture-model")
        row = reg.get("fixture_prop")
    check(row["status"] == "proposed" and row["state"] == "emerging",
          "a valid proposal is written as `proposed`, emerging")


def _seed_series(store, key: str, days: list[str], values: list[float]) -> None:
    store.write_many([
        {"registry_key": key, "instrument": None, "observed_at": d,
         "available_at": f"{d}T21:00:00+00:00", "value": float(v),
         "source": "synthetic"} for d, v in zip(days, values)])


def _weekdays(end: str, n: int) -> list[str]:
    import datetime as dt
    out, d = [], dt.date.fromisoformat(end)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def _can_produce_for(kind: str, rule: dict) -> bool:
    """Whether a declared evidence rule of this kind can ever yield a FOR."""
    if kind == "earnings":
        return bool(rule.get("symbols")) and str(rule.get("sign")) in ("+", "-")
    if kind == "release_surprises":
        return bool(rule) and all(str(s) in ("+", "-") for s in rule.values())
    if kind == "series_moves":
        return bool(rule) and all(str((r or {}).get("sign")) in ("+", "-")
                                  for r in rule.values())
    if kind == "headlines":
        ex = rule.get("examples") or {}
        return any(nr.score_headline(t, rule, (lab.split("_", 1)[0]
                                               if "_" in lab else None)) == 1
                   for lab, t in ex.items() if lab.endswith("for"))
    return False


def group_h() -> None:
    print(f"{LINE}\nH. EVERY SEEDED STORY CAN, IN PRINCIPLE, REACH CONSENSUS (6c-3)\n"
          f"{LINE}")
    real = nr.load_config()
    rules = real.get("rules") or {}
    c = rules.get("consensus") or {}
    for nid, spec in (real.get("narratives") or {}).items():
        errs = nr.validate_config_story(nid, spec)
        check(not errs, f"{nid}: the definition, its evidence rule and its "
                        f"hypotheses validate{': ' + '; '.join(errs) if errs else ''}")
        ev_rules = spec.get("evidence") or {}
        producers = [k for k, r in ev_rules.items() if _can_produce_for(k, r or {})]
        check(bool(producers),
              f"{nid}: has an evidence rule that can yield evidence FOR "
              f"({', '.join(producers) or 'none'})")
        # The consensus rule is satisfiable given one FOR: attention at the
        # declared minimum, every linked dimension agreeing, one fact for.
        links = spec.get("linked_dimensions") or {}
        inputs = {"attention": {"long": int(c.get("min_attention_long", 0)),
                                "short": int(c.get("min_attention_long", 0)),
                                "delta_short": 0},
                  "agreement": {"share": 1.0 if links else None},
                  "evidence": {"for": [1], "against": []}}
        check(nr.conditions(inputs, rules)["consensus"],
              f"{nid}: with {len(links)} linked dimension(s) agreeing, attention "
              f"at the minimum and one fact FOR, the consensus condition holds")
    empty = dict(real["narratives"]["yen_carry"], evidence={})
    check(any("no evidence rule" in e for e in nr.validate_config_story(
              "yen_carry", empty)),
          "and a config story with NO evidence rule is refused at seed")

    # --- the yen carry's headline rule, end to end -------------------------
    yc = real["narratives"]["yen_carry"]
    ex = yc["evidence"]["headlines"]["examples"]
    day = "2026-09-24"
    with ev_mod.EventStore() as ev:
        ev.write_many([ev_mod.Event("headline", f"{day}T0{i}:00:00+00:00", "fx",
                                    t if " - " in t else f"{t} - Reuters",
                                    payload={"query": "yen_carry"})
                       for i, t in enumerate([ex["for"], ex["against"],
                                              "Yen carry explained"])],
                      available_at=f"{day}T12:00:00+00:00")
        ids = [r[0] for r in ev.conn.execute(
            "SELECT id FROM events WHERE json_extract(payload,'$.query')='yen_carry' "
            "ORDER BY id")]
        store = observations.ObservationStore()
        try:
            got = nr.evidence(ev.conn, yc, f"{day}T21:00:00+00:00", 60, store)
        finally:
            store.close()
    check(got["for"] == [ids[0]] and got["against"] == [ids[1]]
          and ids[2] not in got["for"] + got["against"],
          f"yen carry: a BoJ headline for the unwind counts FOR, one against it "
          f"AGAINST, and one naming no institution is not this rule's "
          f"(for {got['for']}, against {got['against']})")

    # --- the midterm's calendar phase ----------------------------------------
    mc = real["narratives"]["midterm_cycle"]
    with ev_mod.EventStore() as ev:
        ev.write_many([ev_mod.Event(
            "scheduled", "2026-11-03T13:30:00+00:00", "claims_registry",
            "US federal midterm election day", key="cal.midterm_election_2026",
            payload={"claim_id": "cal.midterm_election_2026"})],
            available_at="2026-09-23T12:00:00+00:00")
        titles = [("2026-10-20", "Stocks slump on midterm uncertainty"),
                  ("2026-10-21", "Stocks rally into the midterms"),
                  ("2026-11-10", "Stocks rally after the midterm vote"),
                  ("2026-11-11", "Stocks slump after the midterm vote")]
        ev.write_many([ev_mod.Event("headline", f"{d}T15:00:00+00:00", "fx",
                                    f"{t} - Reuters",
                                    payload={"query": "midterm_cycle"})
                       for d, t in titles],
                      available_at="2026-11-12T00:00:00+00:00")
        mids = [r[0] for r in ev.conn.execute(
            "SELECT id FROM events WHERE json_extract(payload,'$.query')="
            "'midterm_cycle' ORDER BY observed_at")]
        store = observations.ObservationStore()
        try:
            got = nr.evidence(ev.conn, mc, "2026-11-12T21:00:00+00:00", 60, store)
            early = nr.evidence(ev.conn, mc, "2026-09-22T21:00:00+00:00", 60, store)
        finally:
            store.close()
    check(got["for"] == [mids[0], mids[2]] and got["against"] == [mids[1], mids[3]],
          f"midterm: weakness BEFORE election day and a rally AFTER count FOR, "
          f"their opposites AGAINST -- the calendar signs the same words both "
          f"ways (for {got['for']}, against {got['against']})")
    check(not early["for"] and not early["against"],
          "and before the calendar event is knowable nothing is scored")

    # --- a series move -------------------------------------------------------
    days = _weekdays("2026-09-25", 300)
    vals = [150.0 + (0.1 if i % 2 else -0.1) for i in range(len(days) - 5)]
    vals += [vals[-1] * (1 - 0.01 * k) for k in range(1, 6)]
    store = observations.ObservationStore()
    try:
        _seed_series(store, "fred.usd_jpy", days, vals)
        rule = yc["evidence"]["series_moves"]["fred.usd_jpy"]
        mv = nr.series_move("fred.usd_jpy", rule, "2026-09-25T21:00:00+00:00",
                            store)
        check(mv.get("sign") == 1 and mv["item"]["percentile"] <= 10,
              f"yen carry: a five-session fall in USD/JPY at the "
              f"{mv.get('item', {}).get('percentile')} percentile is FOR the "
              f"unwind")
        stale = nr.series_move("fred.usd_jpy", rule, "2026-10-09T21:00:00+00:00",
                               store)
        check(stale.get("sign") == 0 and "stale" in stale.get("reason", ""),
              f"and the same move ten sessions later is unscored as stale "
              f"({stale.get('reason', '')[:60]})")
        cmin = int((rules.get("consensus") or {}).get("min_attention_long", 0))
        conds = nr.conditions(
            {"attention": {"long": cmin, "short": cmin, "delta_short": 0},
             "agreement": {"share": 1.0},
             "evidence": {"for": [], "against": [], "series_for": [mv["item"]],
                          "series_against": []}}, rules)
        check(conds["consensus"],
              "and a series fact alone satisfies min_evidence_for -- the rules "
              "count it like an event")
    finally:
        store.close()


def group_i() -> None:
    print(f"{LINE}\nI. THE MIDTERM HYPOTHESES: EX ANTE, SHRUNK, NEVER CERTAIN (6c-3)\n"
          f"{LINE}")
    real = nr.load_config()
    mc = real["narratives"]["midterm_cycle"]
    table = {"computed_at": "2026-09-27T00:00:00+00:00",
             "method_version": "base-rates-method-1",
             "primary": {"n": 19, "hits": 19, "hit_rate": 1.0,
                         "binomial_p_vs_all_years": 0.004608},
             "primary_unconditional": {"all_years": {"n": 73, "hit_rate": 0.7534}},
             "secondary": {"n": 19, "hits": 17, "hit_rate": 0.8947,
                           "binomial_p_vs_all_years": 0.04502},
             "secondary_unconditional": {"all_years": {"n": 73,
                                                       "hit_rate": 0.6986}}}
    pp = nr.hypothesis_prior(mc["hypotheses"]["primary"]["prior"], table)
    ps = nr.hypothesis_prior(mc["hypotheses"]["secondary"]["prior"], table)
    check(pp["probability"] == 0.915 and ps["probability"] == 0.8271,
          f"the prior is (hits + k p0) / (n + k) with k=10: 19/19 against 0.7534 "
          f"gives {pp['probability']}, 17/19 against 0.6986 gives "
          f"{ps['probability']} -- not the raw 1.0 and 0.8947")
    check(pp["conditional"]["n"] == 19 and pp["unconditional"]["n"] == 73
          and pp["k"] == 10 and pp["conditional"]["hit_rate"] == 1.0
          and pp["conditional"]["binomial_p_vs_unconditional"] == 0.004608,
          "and it carries the rule, k, the raw rate with its n, the "
          "unconditional rate with its n, and the binomial p beside it")
    certain = dict(table, primary_unconditional={"all_years": {"n": 73,
                                                               "hit_rate": 1.0}})
    held = nr.hypothesis_prior(mc["hypotheses"]["primary"]["prior"], certain)
    check(held["probability"] is None and "0 or 1" in held["reason"],
          f"a rule that yields 1.0 enters nothing ({held['reason'][:50]})")

    store = observations.ObservationStore()
    try:
        store.write("baserate.midterm_from_election", None, "2026-09-25",
                    "2026-09-26T08:00:00+00:00", json.dumps(table),
                    source="derived_base_rate")
        out = nr.emit_hypotheses("midterm_cycle", mc, "2026-09-28",
                                 "2026-09-28T21:00:00+00:00", store, None, "fx")
        check(sorted(e["hypothesis"] for e in out["emitted"])
              == ["primary", "secondary"] and not out["held"],
              f"on 28 September both are entered ({out})")
        again = nr.emit_hypotheses("midterm_cycle", mc, "2026-09-29",
                                   "2026-09-29T21:00:00+00:00", store, None, "fx")
        check(not again["emitted"],
              "and the next close enters nothing: a hypothesis is one forecast")
        late = nr.emit_hypotheses("fixture_midterm", mc, "2026-10-02",
                                  "2026-10-02T21:00:00+00:00", store, None, "fx")
        check([e["hypothesis"] for e in late["emitted"]] == ["primary"]
              and "secondary" in late["held"],
              f"on 2 October the secondary window (from 1 October) is already "
              f"open and is HELD, not entered: {late['held'].get('secondary', '')[:50]}")
        with probability_ledger.ProbabilityLedger() as led:
            rows = {r["scenario_set"]: r for r in led.all_rows()}
        row = rows["hypothesis:midterm_cycle:primary"]
        crit = json.loads(row["resolution_criterion"])
        check(row["probability"] == 0.915 and crit["baseline_date"] == "2026-11-03"
              and crit["horizon_date"] == "2027-11-03"
              and crit["claims_cited"] == ["cal.midterm_election_2026"]
              and "Base Rates" in crit["statement_cited"],
              "the ledger row: 0.915, election day to election day, the claim "
              "cited by id and the paper for the statement")

        # Resolution reads the close ON OR BEFORE each date, once final.
        sec = json.loads(rows["hypothesis:midterm_cycle:secondary"]
                         ["resolution_criterion"])
        _seed_series(store, "yfinance.mkt_gspc",
                     ["2026-09-30", "2026-10-01", "2027-03-31"],
                     [99.0, 100.0, 110.0])
        wait = nr.resolve_one(sec, store, "2027-04-01T21:00:00+00:00")
        check(wait["outcome"] is None and "not final" in wait["reason"],
              "with no print after 31 March the close on it is not final yet")
        _seed_series(store, "yfinance.mkt_gspc", ["2027-04-01"], [90.0])
        res = nr.resolve_one(sec, store, "2027-04-02T21:00:00+00:00")
        d = res["detail"]["yfinance.mkt_gspc"]
        check(res["outcome"] == 1 and d["baseline"]["value"] == 100.0
              and d["at_horizon"]["value"] == 110.0,
              "then it resolves on 1 October's 100 against 31 March's 110 -- not "
              "on the later 90, and not on the level at emission")
    finally:
        store.close()


def main() -> int:
    print(f"{LINE}\nThe narrative register and the 07:00 scan (6c-2)\n{LINE}")
    for g in (groups_abc, group_d, group_e, group_g, group_h, group_i,
              group_j, group_k, group_l):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

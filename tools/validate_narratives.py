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
                        f"Fixture headline {day} {i}",
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
        ev.write_many([ev_mod.Event("headline", "2026-09-28T09:00:00+00:00", "fx",
                                    "basis", payload={"query": QUERY})])
        basis = ev.conn.execute("SELECT MAX(id) FROM events").fetchone()[0]
    spec = dict(r.extra["proposals"][0])
    with nr.NarrativeRegister() as reg:
        reg.propose(spec["id"], spec, [basis], proposed_by="fixture-model")
        row = reg.get("fixture_prop")
    check(row["status"] == "proposed" and row["state"] == "emerging",
          "a valid proposal is written as `proposed`, emerging")


def main() -> int:
    print(f"{LINE}\nThe narrative register and the 07:00 scan (6c-2)\n{LINE}")
    for g in (groups_abc, group_d, group_e, group_g):
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

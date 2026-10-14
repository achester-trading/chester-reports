"""
Validation gate for AQ-6: the thesis register (change order of 10 Oct 2026, s.6).

Every case runs on fixtures in a temporary directory -- a thesis file written
here, a synthetic observation store, a throwaway ledger and register. It never
reads the live store, so its verdict is about the commit.

  A LOADER     the refusals: a prose criterion, weights not summing to one, a
               past date, a missing falsifier; an unregistered series; an example
               outside a dry run; a deep family sitting out; a Thailand draft.
  B SEED       sources, set ids, emitted_by and the vintage; idempotent re-seed;
               an edited forecast, a second file for the quarter and a backdated
               first seeding refused; the dry run writes nothing.
  C DRAFTS     the draft-per-horizon rule; every entry written as draft and never
               active, with the portfolio role and the cost row in its packet; the
               no-draft line with its reason; the Brookfield refusal at the dry run.
  D RESOLUTION from a synthetic store as of: waiting until the period is final,
               then resolved with the observation read kept; the manual path needs
               a note and is logged; Brier against hand-computed values; the set's
               ordering-and-direction score.
  E RENDERERS  the graded table (the Quarterly's chapter opener) and the seed
               table (the Monthly's slow layers, after the base rates); the
               ledger's coherence on every alt_asset set; the show view.

    python tools/validate_thesis_register.py
"""

from __future__ import annotations

import copy
import io
import sqlite3
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml                                             # noqa: E402

from altdata import observations                         # noqa: E402
from altdata import probability_ledger as pl             # noqa: E402
from altdata import thesis_register as tr                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

WRITTEN = "2026-11-07T15:00:00+00:00"
SEED_AT = "2026-11-08T12:00:00+00:00"
GLD = "yfinance.mkt_gld"


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def crit(comp, level, date, series=GLD):
    return {"series": series, "comparator": comp, "level": level, "date": date}


def family(series=GLD, book_3m=None, book_12m=None, lo=330, hi=400):
    return {
        "scenarios_12m": [
            {"name": "bid holds", "probability": 0.45, "horizon": "2027-12-31",
             "criterion": crit(">=", hi, "2027-12-31", series)},
            {"name": "range", "probability": 0.35, "horizon": "2027-12-31",
             "criterion": crit("between", [lo, hi], "2027-12-31", series)},
            {"name": "unwind", "probability": 0.20, "horizon": "2027-12-31",
             "criterion": crit("<", lo, "2027-12-31", series)}],
        "thesis_3m": {"claim": "closes 1Q27 above 360", "probability": 0.6,
                      "criterion": crit(">", 360, "2027-03-31", series),
                      "falsifier": crit("<", 320, "2027-02-26", series),
                      "book": "B", "chester_read": "from the drivers"},
        "book": {"3m": book_3m if book_3m is not None else {
                     "instrument": "GLD", "direction": "long",
                     "thesis": "the 3-month thesis as a position",
                     "edge": "structural_flow", "horizon": "positional",
                     "size": "one unit", "invalidation": "settled close below 320",
                     "counter_thesis": "real rates rise faster than priced",
                     "portfolio_role": "proxy", "quantity": 10,
                     "price_series": GLD, "status": "active"},
                 "12m": book_12m if book_12m is not None else {
                     "no_draft": "no edge beyond the allocation already held"}}}


def doc(**over) -> dict:
    fams = {f: family() for f in tr.DEEP_FAMILIES}
    fams["real_estate"] = {"not_this_quarter": "the CMBS rows are not stored yet"}
    d = {"quarter": "2027q1", "written_at": WRITTEN, "families": fams}
    d.update(over)
    return d


def write(d: Path, content: dict, name: str = "2027q1.yaml") -> Path:
    p = d / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(content, sort_keys=False), encoding="utf-8")
    return p


def refused(path, **kw) -> list[str]:
    try:
        tr.seed(path, **{"now": SEED_AT, "dry_run": True, **kw})
    except tr.ThesisFileError as exc:
        return exc.reasons
    return []


def store_at(d: Path) -> str:
    """A synthetic store: GLD at emission, at the falsifier date, at the
    3-month date and after it, at the 12-month date and after it."""
    path = str(d / "store.db")
    with observations.ObservationStore(path) as st:
        for day, v in (("2026-11-06", 340.0), ("2027-02-26", 335.0),
                       ("2027-03-31", 372.0), ("2027-04-01", 370.0),
                       ("2027-12-31", 410.0), ("2028-01-03", 411.0)):
            st.write(GLD, None, day, f"{day}T21:00:00+00:00", v, "synthetic")
    return path


# ---------------------------------------------------------------------------
def group_a(d: Path) -> None:
    print("\nA. The loader's refusals")
    base = doc()
    x = copy.deepcopy(base)
    x["families"]["metals"]["thesis_3m"]["criterion"] = "gold outperforms"
    r = refused(write(d / "a1", x))
    check(any("prose, not a measurable" in s for s in r),
          "a prose criterion is refused, not accepted as text")
    x = copy.deepcopy(base)
    x["families"]["oil"]["scenarios_12m"][0]["probability"] = 0.5
    r = refused(write(d / "a2", x))
    check(any("sum to 1.0500" in s and "never normalised" in s for s in r),
          "weights summing to 1.05 are refused and reported, never normalised")
    x = copy.deepcopy(base)
    x["families"]["currency"]["thesis_3m"]["criterion"]["date"] = "2026-10-01"
    r = refused(write(d / "a3", x))
    check(any("not in the future at emission" in s for s in r),
          "a criterion dated before emission is refused")
    x = copy.deepcopy(base)
    del x["families"]["em"]["thesis_3m"]["falsifier"]
    r = refused(write(d / "a4", x))
    check(any("no falsifier" in s for s in r), "a missing falsifier is refused")
    x = copy.deepcopy(base)
    x["families"]["china"]["scenarios_12m"][1]["criterion"]["series"] = "made.up"
    r = refused(write(d / "a5", x))
    check(any("not a registered store key" in s for s in r),
          "an unregistered series is refused")
    x = copy.deepcopy(base)
    x["families"]["crypto"]["thesis_3m"]["book"] = None
    r = refused(write(d / "a6", x))
    check(any("the Book it informs" in s for s in r),
          "a 3-month thesis without its Book is refused")
    x = copy.deepcopy(base)
    x["families"]["metals"] = {"not_this_quarter": "busy"}
    r = refused(write(d / "a7", x))
    check(any("deep family cannot sit out" in s for s in r),
          "a deep family cannot sit out a quarter")
    x = copy.deepcopy(base)
    x["families"]["thailand"] = family(book_3m={
        "instrument": "THB", "direction": "short", "thesis": "t", "edge": "e",
        "horizon": "positional", "size": "s", "invalidation": "i",
        "counter_thesis": "c", "portfolio_role": "tactical"})
    r = refused(write(d / "a8", x))
    check(any("isolated" in s for s in r),
          "a Thailand draft is refused: its book may only say no_draft")
    x = copy.deepcopy(base)
    x["example"] = True
    p = write(d / "a9", x)
    try:
        tr.seed(p, str(d / "a9" / "l.db"), now=SEED_AT)
        r = []
    except tr.ThesisFileError as exc:
        r = exc.reasons
    check(any("example" in s for s in r), "a file marked example is never seeded")
    r = refused(REPO / "config" / "alt_asset_theses" / "TEMPLATE.yaml",
                allow_example=True, store_path=str(d / "none.db"),
                db_path=str(d / "none-ledger.db"))
    check(r == [], f"the shipped template validates under --dry-run ({r[:2]})")
    x = copy.deepcopy(base)
    x["families"]["oil"]["scenarios_12m"][2]["criterion"]["comparator"] = "≈"
    x["families"]["oil"]["scenarios_12m"][2]["criterion"]["level"] = "about 70"
    r = refused(write(d / "a10", x))
    check(sum("oil.scenarios_12m[2]" in s for s in r) >= 2,
          "every reason is reported, not the first (comparator and level both)")
    x = copy.deepcopy(base)
    p = write(d / "a11", x, name="2027q2.yaml")
    r = refused(p)
    check(any("must be <YYYY>q<N>.yaml and match" in s for s in r),
          "a file whose name does not match its quarter is refused")


def group_b(d: Path) -> dict:
    print("\nB. The seed")
    db = str(d / "chester.db")
    st = store_at(d)
    p = write(d / "b", doc())
    dry = tr.seed(p, db, dry_run=True, now=SEED_AT, store_path=st)
    check(dry["dry_run"] and dry["forecasts"] == 24 and dry["new"] == 24,
          f"the dry run states 24 forecasts, six families x (3 + 1) "
          f"({dry['forecasts']})")
    check(not Path(db).exists(), "and writes nothing: no ledger is created")
    res = tr.seed(p, db, now=SEED_AT, store_path=st, register_db=db)
    check(res["recorded"] == 24, f"the seed records 24 ({res['recorded']})")
    with pl.ProbabilityLedger(db) as led:
        rows = led.all_rows()
    sources = {r["source"] for r in rows}
    check(sources == {f"alt_asset:{f}" for f in tr.DEEP_FAMILIES},
          "each row's source is alt_asset:<family>")
    sets = {r["scenario_set"] for r in rows}
    check("metals-2027q1-12m" in sets and "metals-2027q1-3m" in sets
          and len(sets) == 12, "scenario_set is <family>-<YYYYqN>-12m or -3m")
    check({r["emitted_by"] for r in rows} == {"operator"}
          and {r["emitted_at"] for r in rows} == {WRITTEN},
          "emitted_by operator, emitted_at the file's written_at")
    check(all(r["resolution_criterion"].startswith("measurable: yfinance.mkt_gld")
              for r in rows), "the criterion is the measurable's canonical text")
    conn = sqlite3.connect(db)
    side = conn.execute("SELECT DISTINCT file_sha256, written_at, file_name FROM "
                        "alt_asset_theses").fetchall()
    emv = conn.execute("SELECT DISTINCT value_at_emission FROM "
                       "alt_asset_theses").fetchall()
    conn.close()
    check(len(side) == 1 and side[0][0] == tr._sha(p) and side[0][2] == "2027q1.yaml",
          "the file's vintage (sha256, written_at, name) is kept with every row")
    check(emv == [(340.0,)], "the value at emission is read from the store as of "
                             "written_at (340, the 6 Nov close)")
    again = tr.seed(p, db, now="2026-11-20T12:00:00+00:00", store_path=st,
                    register_db=db)
    with pl.ProbabilityLedger(db) as led:
        n2 = len(led.all_rows())
    check(again["recorded"] == 0 and again["drafts_written"] == 0 and n2 == 24,
          "re-seeding the same file is idempotent (through probability_id), even "
          "past the backdating window")
    x = doc()
    x["families"]["metals"]["thesis_3m"]["probability"] = 0.7
    r = refused(write(d / "b2", x), db_path=db, store_path=st)
    check(any("a forecast is immutable" in s for s in r),
          "an edited probability under the same written_at is refused")
    x = doc(written_at="2026-11-08T09:00:00+00:00")
    r = refused(write(d / "b3", x), db_path=db, store_path=st)
    check(any("already seeded" in s for s in r),
          "a second file for a quarter already seeded is refused")
    x = doc(quarter="2027q2", written_at="2026-10-01T15:00:00+00:00")
    r = refused(write(d / "b4", x, name="2027q2.yaml"), db_path=db,
                store_path=st)
    check(any("days before this seeding" in s for s in r),
          "a first seeding more than seven days after written_at is refused")
    x = doc(written_at="2026-11-09T15:00:00+00:00")
    r = refused(write(d / "b5", x, name="2027q1.yaml"),
                db_path=str(d / "b5.db"))
    check(any("in the future" in s for s in r),
          "a written_at after the seeding instant is refused")
    return {"db": db, "store": st, "file": p}


def group_c(d: Path, b: dict) -> None:
    print("\nC. The draft-per-horizon rule")
    from register import store as rstore
    with rstore.Register(b["db"]) as reg:
        rows = [r for r in reg.all() if (r.get("note") or "").startswith("alt_asset")]
    check(len(rows) == 6, f"one draft per deep family for the 3-month book "
                          f"({len(rows)})")
    check(all(r["status"] == "draft" for r in rows),
          "every entry is a draft -- the file's `status: active` is ignored")
    check(all(r["book"] == "B" and r["horizon"] == "positional"
              and r["engine_id"] == "operator" and r["time_stop"] == "2027-03-31"
              for r in rows),
          "Book B, positional, engine operator, time stop at the thesis date")
    check(all("portfolio role: proxy" in r["note"] for r in rows),
          "the portfolio role, in XVII's words, is on the entry")
    check(all('"measurable: yfinance.mkt_gld < 320' in (r["falsifiers"] or "")
              for r in rows), "the thesis's falsifier travels to the draft")
    with rstore.Register(b["db"]) as reg:
        pk = reg.packet(rows[0]["id"]) if rows else None
    import json
    cost = json.loads((pk or {}).get("expected_cost_json") or "{}")
    check(cost.get("cost_source") == "estimated_from_schedule"
          and cost.get("price") == 340.0 and cost.get("commission") is not None
          and "not priced" in cost.get("spread", ""),
          "the packet carries the cost row from the IBKR costs writer, priced at "
          "the emission close, with spread, roll, borrow and FX hedge named")
    conn = sqlite3.connect(b["db"])
    lines = conn.execute("SELECT family, horizon_kind, kind, reason FROM "
                         "alt_asset_books ORDER BY family, horizon_kind").fetchall()
    conn.close()
    nd = [x for x in lines if x[2] == "no_draft"]
    check(len(lines) == 12 and len(nd) == 6
          and all("no edge" in x[3] for x in nd),
          "every deep family has a line per horizon: six drafts, six no-draft "
          "lines with their reason")
    x = doc()
    del x["families"]["oil"]["book"]["12m"]
    r = refused(write(d / "c1", x))
    check(any("oil.book.12m: no book entry" in s for s in r),
          "the gate: a deep family with neither a draft nor a no_draft fails")
    plan = tr.load(write(d / "c2", doc()), now=SEED_AT)
    plan["families"]["crypto"]["book"].pop("3m")
    check(tr.draft_rule_faults(plan) == ["crypto 3m: neither a draft nor a "
                                         "no_draft"],
          "draft_rule_faults names the family and the horizon")
    x = doc()
    x["families"]["em"]["book"]["3m"]["instrument"] = "BN"
    r = refused(write(d / "c3", x))
    check(any("RestrictedInstrumentError" in s for s in r),
          "a Brookfield-related draft is refused by the register at the dry run")
    src = Path(tr.__file__).read_text(encoding="utf-8")
    check(src.count('status="draft",') == 1 and 'status="active"' not in src,
          "the writer's one register call hard-codes status draft")


def group_d(d: Path, b: dict) -> None:
    print("\nD. Resolution by code, from the store, as of")
    db, st = b["db"], b["store"]
    res = tr.resolve_due(db, store_path=st, now="2027-04-01T12:00:00+00:00")
    check(not res["resolved"] and len(res["waiting"]) == 6
          and "not yet final" in res["waiting"][0]["why"],
          "on 1 Apr the 31 Mar close is not final (no later period knowable, "
          "grace not passed): six theses wait, each saying why")
    res = tr.resolve_due(db, store_path=st, now="2027-04-02T12:00:00+00:00")
    check(len(res["resolved"]) == 6 and all(r["outcome"] == 1 and r["value"] == 372
                                            for r in res["resolved"]),
          "on 2 Apr the six 3-month theses resolve from the 31 Mar close (372 > "
          "360)")
    rows = tr.theses(db)
    t3 = [r for r in rows if r["horizon_kind"] == "3m"]
    check(all(abs(r["brier"] - 0.16) < 1e-12 for r in t3),
          "Brier (0.6 - 1)^2 = 0.16, hand-computed")
    check(all('"observed_at": "2027-03-31' in r["resolution_note"] for r in t3),
          "the observation read is kept in the resolution note, so it replays")
    g = [x for x in tr.grades(db, now="2027-04-02T12:00:00+00:00")
         if x["family"] == "metals"]
    g3 = [x for x in g if x["horizon_kind"] == "3m"][0]
    g12 = [x for x in g if x["horizon_kind"] == "12m"][0]
    check(g3["grade"] == "hit" and g3["direction_right"] is True,
          "the 3-month grade: hit, direction right (340 -> 372, target 360)")
    check(g12["grade"] == "not yet due" and g12["ordering"] is None,
          "the 12-month set is not yet due and carries no ordering score")
    with observations.ObservationStore(st) as store:
        fs = tr.falsifier_state(t3[0], store, "2027-04-02T12:00:00+00:00")
    check(fs == "held", "the falsifier (< 320 on 26 Feb; 335) held")
    res = tr.resolve_due(db, store_path=st, now="2028-01-05T12:00:00+00:00")
    check(len(res["resolved"]) == 18 and not res["waiting"],
          f"on 5 Jan 2028 the 18 scenario weights resolve scenario by scenario "
          f"({len(res['resolved'])})")
    g = [x for x in tr.grades(db, now="2028-01-05T12:00:00+00:00")
         if x["family"] == "metals" and x["horizon_kind"] == "12m"][0]
    check(g["grade"] == "hit" and g["ordering"] is True
          and g["occurred_rank"] == [1] and g["direction_right"] is True
          and g["exclusive"],
          "the set: the highest weight (>= 400) occurred, ordering right at rank "
          "1, direction right (340 -> 410)")
    exp = (0.45 - 1) ** 2 + (0.35 - 0) ** 2 + (0.20 - 0) ** 2
    check(abs(g["mean_brier"] - exp / 3) < 1e-12,
          f"the set's mean Brier is (0.3025 + 0.1225 + 0.04) / 3 = "
          f"{exp / 3:.4f}, against the coin's 0.25")
    # The manual path, on a fresh ledger.
    d2 = d / "manual"
    d2.mkdir()
    db2 = str(d2 / "chester.db")
    tr.seed(write(d2, doc()), db2, now=SEED_AT, store_path=st, register_db=db2)
    pid = [r for r in tr.theses(db2) if r["horizon_kind"] == "3m"][0]
    try:
        tr.resolve_manual(pid["probability_id"], 1, "  ", db2)
        ok_ = False
    except ValueError:
        ok_ = True
    check(ok_, "a manual resolution without a note is refused")
    out = tr.resolve_manual(pid["probability_id"], 0, "series retired; the "
                            "outcome read from the issuer's page", db2,
                            now="2027-04-10T12:00:00+00:00")
    conn = sqlite3.connect(db2)
    logged = conn.execute("SELECT COUNT(*) FROM alt_asset_manual_resolutions"
                          ).fetchone()[0]
    note = conn.execute("SELECT resolution_note FROM probabilities WHERE "
                        "probability_id = ?", (pid["probability_id"],)
                        ).fetchone()[0]
    conn.close()
    check(out["outcome"] == 0 and logged == 1 and note.startswith("MANUAL: "),
          "the manual path is logged and marked in the ledger's note")
    gm = [x for x in tr.grades(db2, now="2027-04-10T12:00:00+00:00")
          if x["family"] == pid["family"] and x["horizon_kind"] == "3m"][0]
    check(gm["manual"] == 1 and "by hand" in gm["why"],
          "and the grading view says it was resolved by hand")


def group_e(d: Path, b: dict) -> None:
    print("\nE. The two renderers, coherence and the show view")
    db = b["db"]
    t = tr.graded_table("2027q1", db, now="2028-01-05T12:00:00+00:00")
    check(t["columns"] == tr.GRADED_COLUMNS and len(t["rows"]) == 12
          and all(len(r) == len(t["columns"]) for r in t["rows"]),
          f"the graded table: a row per family and horizon, "
          f"{len(tr.GRADED_COLUMNS)} columns ({len(t['rows'])} rows)")
    met = [r for r in t["rows"] if r[0] == "metals"]
    check(any(r[1] == "3-month" and r[4] == "hit" and r[5] == "0.1600"
              and "read 372 against > 360" in r[6] for r in met),
          "the 3-month row: hit, Brier 0.1600, one line of why from the read")
    check(any(r[1] == "12-month set" and r[4] == "hit"
              and "bid holds occurred" in r[6] for r in met),
          "the 12-month row: hit, with which scenario occurred")
    e = tr.graded_table("2026q4", db, now="2028-01-05T12:00:00+00:00")
    check(not e["rows"] and "no theses for 4Q26" in e["lines"][0],
          "a quarter with no theses says so")
    s = tr.seed_table("2026-12-01T12:00:00Z", str(d / "manual" / "chester.db"))
    check(s["quarter"] == "2027q1" and s["label"] == "1Q27"
          and s["line"].startswith("The ledger holds 12 theses for 1Q27; 6 "
                                   "twelve-month scenario sets (18 weights) and 6 "
                                   "three-month theses")
          and s["columns"] == tr.SEED_COLUMNS and len(s["rows"]) == 24,
          f"the seed table, in the ledger's form: {s['line'][:72]}...")
    check(all(r[-1] == "pending" for r in s["rows"]
              if r[1] == "12-month"),
          "weights not yet graded at the cutoff print 'pending' beside them")
    s0 = tr.seed_table("2026-11-01T12:00:00Z", str(d / "manual" / "chester.db"))
    check(s0["count"] == 0 and "no theses for 1Q27 yet" in s0["line"],
          "before written_at, the Monthly sees no theses (as of)")
    # Wired into the Monthly's slow layers, after the base rates, read only.
    from monthly_macro import stack as ms
    ledger = d / "manual" / "chester.db"
    before = ledger.stat().st_mtime_ns
    sl = ms.slow_layers({}, {}, None, "2026-12-01T12:00:00+00:00", str(ledger))
    titles = [x["title"] for x in sl["subsections"]]
    i = titles.index("Base rates: Top & Bottom")
    check(titles[i + 1] == "Theses: the ledger's seed for 1Q27"
          and sl["subsections"][i + 1]["table"]["rows"]
          and "chart" not in str(sl["subsections"][i + 1].keys()),
          "the Monthly's slow layers carry the seed table after the base rates, "
          "no chart")
    check(sl["data"]["theses_seed"]["count"] == 12
          and ledger.stat().st_mtime_ns == before,
          "and the Monthly wrote nothing to the ledger")
    empty = ms.slow_layers({}, {}, None, "2026-12-01T12:00:00+00:00",
                           str(d / "nowhere.db"))
    sub = [x for x in empty["subsections"] if x["title"].startswith("Theses")][0]
    check("no theses for 1Q27 yet" in sub["lines"][0] and "table" not in sub
          and not (d / "nowhere.db").exists(),
          "with no ledger the line says so, and no database is created")
    from monthly_macro import v2
    src = Path(v2.__file__).read_text(encoding="utf-8")
    check("source NOT LIKE 'alt_asset:%'" in src,
          "Ahead's scenario list leaves the theses to the seed table (each fact "
          "once)")
    check(tr.coherence(db) == [] and tr.coherence(str(d / "manual" / "chester.db"))
          == [], "the ledger's coherence holds on every alt_asset set")
    with pl.ProbabilityLedger(str(d / "manual" / "chester.db")) as led:
        led.record(source="alt_asset:oil", claim="a stray second 3m row",
                   probability=0.5, horizon_date="2027-03-31",
                   resolution_criterion="x", scenario_set="oil-2027q1-3m",
                   emitted_at=WRITTEN)
    bad = tr.coherence(str(d / "manual" / "chester.db"))
    check([x["scenario_set"] for x in bad] == ["oil-2027q1-3m"],
          "a 3-month set with two rows is incoherent (the binary exemption is "
          "for one row only)")
    lines = tr.show(db, now="2028-01-05T12:00:00+00:00")
    joined = "\n".join(lines)
    check("metals" in joined and "vs coin 0.25" in joined
          and "ordering right (occurred at rank [1])" in joined
          and "hit 12" in joined,
          "show --source alt_asset: per family and horizon, Brier against the "
          "coin, hit/miss/not yet due, ordering and direction")
    buf = io.StringIO()
    sys.argv = ["probability_ledger", "show", "--source", "alt_asset",
                "--db", db]
    with redirect_stdout(buf):
        rc = pl.main()
    check(rc == 0 and "The thesis register" in buf.getvalue(),
          "python -m altdata.probability_ledger show --source alt_asset runs")
    buf = io.StringIO()
    sys.argv = ["probability_ledger", "seed-alt-asset", "--file",
                str(write(d / "e9", doc(written_at="2026-11-09T15:00:00+00:00"))),
                "--dry-run", "--db", str(d / "e9" / "l.db")]
    with redirect_stdout(buf):
        rc = pl.main()
    check(rc == 2 and "REFUSED" in buf.getvalue(),
          "seed-alt-asset --dry-run prints the refusals and exits 2")


def main() -> int:
    print(f"{LINE}\nAQ-6 -- the thesis register (fixtures only)\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        d = Path(td)
        group_a(d)
        b = group_b(d)
        group_c(d, b)
        group_d(d, b)
        group_e(d, b)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

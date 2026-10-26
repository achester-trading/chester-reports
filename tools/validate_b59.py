"""
B59 (session B, 24 Oct 2026): D15, the one-day 10-year trigger, and D26, the
three new sources (GDELT, NOAA CPC degree days, the Hugging Face model-release
watch). Rulings of 24 Oct 2026.

  A  D15'S TRIGGER. The five-year 97.5th percentile of absolute one-day changes
     by hand; firing on both signs; silence below it; "not read" under 1,000
     changes; the attribution over one session with "awaiting" and partial legs.
  B  D15'S LEDGER. The outcomes by hand; the ledger row and resolve's new vintage;
     the pre-registration's SHA-256 and its commit before the scoring code; the
     rule's INSUFFICIENT, PASS and FAIL on fixtures; the first edition as written;
     the script opens no store.
  C  THE HYPOTHESES. The batch validates (alpha-lab-hypotheses/v1, model_idea_rule
     true, within the sitting's budget); H-B59-3's rule compiles in the grammar,
     the other two need code; the batch committed alone and before each reader.
  D  GDELT. A fixture export in both layouts: the family mapping (actors,
     locations, dyads), the measures, the tone, the share per 10,000, the
     narratives' whole-word URL match, a malformed row and another day's row left
     out; every family and story a row, zero included; a failed export marks the
     day STALE and writes nothing; a stored day is not read again.
  E  NOAA CPC. A fixture file parsed (a non-number cell left out); the 1991-2020
     normal and the seven-day departure by hand; no normal under 20 years; an
     unchanged re-read writes nothing; a failed fetch is listed and writes nothing.
  F  HUGGING FACE. The weekly count by hand; the declared-organisation filter;
     the Link-header paging and its stop; a failed organisation is STALE and the
     total not written; an event is available at the pull, never createdAt.
  G  PLACEMENT. The close's flag line in the event area and its ledger row; the
     Weekly's Mechanics, narratives and tail lines; the Monthly's Factor III and
     Factor I-b after the Factor lines; the hooks, the steps, the rosters and the
     EOD resolve.
  H  HYGIENE. Every new key registered, trigger-ineligible and barred from the
     market-state object (named in neither its config nor regime.py); the sources
     registered with their checks; the publication lag; no composite,
     market-state, register, vendor or by-hand import; no unit file; no person's
     name, handle or email in the new files; the generic User-Agent.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_b59.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "calibration"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402

from altdata import derived, observations  # noqa: E402
from altdata import oneday_10y as od  # noqa: E402
from altdata.sources import cpc_degree_days as cpc  # noqa: E402
from altdata.sources import gdelt  # noqa: E402
from altdata.sources import hf_releases as hf  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
NOW = "2026-10-24T23:00:00+00:00"
PREREG = REPO / "docs" / "ledgers" / "oneday-10y-preregistration-2026-10.md"
PREREG_SHA = "a6423e64a90e81ace210f814e645d32224d701e94b7c730736a98e67615320d3"
BATCH = REPO / "alpha" / "research" / "hypotheses-2026-10-24-b59-sources.yaml"
EDITION = REPO / "docs" / "ledgers" / "d15-ledger-2026-10-24.md"
READERS = ["altdata/sources/gdelt.py", "altdata/sources/cpc_degree_days.py",
           "altdata/sources/hf_releases.py"]
NEW_CODE = [REPO / p for p in READERS + ["altdata/oneday_10y.py",
                                          "daily_cascade/b59_block.py",
                                          "tools/calibration/d15_oneday_10y.py"]]
NEW_CONFIG = [REPO / "config" / f for f in ("oneday_10y.yaml", "gdelt.yaml",
                                           "cpc_degree_days.yaml", "ai_release_watch.yaml")]
NEW_KEYS = [od.LEDGER_KEY] + gdelt.ROSTER_KEYS + cpc.ROSTER_KEYS + \
    [hf.ORG_KEY, hf.TOTAL_KEY, hf.EVENT_KEY]


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


def store(rows: list[dict]) -> str:
    db = str(Path(gate_tmp.mkdtemp("b59_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    return db


def obs(key, day, v, inst=None, src="fixture"):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": day + "T21:00:00+00:00", "value": v, "source": src}


def pct_by_hand(xs: list[float], q: float) -> float:
    s = sorted(xs)
    r = q / 100.0 * (len(s) - 1)
    lo = int(r)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (r - lo)


def days_from(start: str, n: int) -> list[str]:
    d = dt.date.fromisoformat(start)
    return [(d + dt.timedelta(days=i)).isoformat() for i in range(n)]


def yield_fixture(n: int = 1100, tail: tuple = (30.0,)) -> list[tuple[str, float]]:
    """A 10-year path of n one-day changes cycling 1..10 bp with alternating
    signs, then the `tail` changes (bp)."""
    days = days_from("2022-01-01", n + 1 + len(tail))
    v, out = 4.0, [(days[0], 4.0)]
    for i in range(n):
        m = (i % 10) + 1
        v += (m if i % 2 else -m) / 100.0
        out.append((days[i + 1], round(v, 6)))
    for j, t in enumerate(tail):
        v += t / 100.0
        out.append((days[n + 1 + j], round(v, 6)))
    return out


def first_commit(path: str) -> list[str]:
    return subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", path],
                          cwd=REPO, capture_output=True, text=True, timeout=30).stdout.split()


def shallow() -> bool:
    return subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=REPO,
                          capture_output=True, text=True, timeout=30).stdout.strip() == "true"


def ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=REPO,
                          timeout=30).returncode == 0


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. D15'S TRIGGER AND ATTRIBUTION")
    cfg = od.config()
    t = cfg["trigger"]
    check(float(t["percentile"]) == 97.5 and int(t["window_years"]) == 5
          and int(t["min_changes"]) == 1000, "the ruling's numbers: 97.5th, five years, "
          "at least 1,000 changes")
    for sign in (+1, -1):
        y = yield_fixture(tail=(30.0 * sign,))
        day = y[-1][0]
        prior = [abs((y[i][1] - y[i - 1][1]) * 100) for i in range(1, len(y) - 1)]
        thr = pct_by_hand(prior, 97.5)
        tr = od.trigger(y, day, cfg)
        check(tr["state"] == "computed" and tr["fired"] and abs(tr["threshold_bp"] - round(thr, 1))
              < 1e-9 and tr["n"] == len(prior) and tr["change_bp"] == 30.0 * sign,
              f"a {30 * sign:+.0f} bp day fires against the 97.5th percentile by hand "
              f"({thr:.2f} bp, n={len(prior)})")
    y = yield_fixture(tail=(9.0,))
    tr = od.trigger(y, y[-1][0], cfg)
    check(tr["state"] == "computed" and not tr["fired"],
          f"a +9 bp day does not fire (threshold {tr.get('threshold_bp')} bp)")
    y = yield_fixture(tail=(10.0,))
    prior = [abs((y[i][1] - y[i - 1][1]) * 100) for i in range(1, len(y) - 1)]
    check(not od.trigger(y, y[-1][0], cfg)["fired"] and pct_by_hand(prior, 97.5) >= 10.0 - 1e-9,
          "a move equal to the window's maximum does not pass a threshold at it "
          "(\"beyond\" is strictly greater)")
    y = yield_fixture(n=500, tail=(40.0,))
    tr = od.trigger(y, y[-1][0], cfg)
    check(tr["state"] == "not read" and not tr["fired"] and "1000" in tr["line"],
          "under 1,000 prior changes the trigger is not read, and says so")
    y = yield_fixture(tail=(30.0,))
    lo = od._years_back(y[-1][0], 5)
    check(od.trigger(y, "2099-01-01", cfg)["state"] == "absent"
          and all(d > lo for d, _ in y[1:]), "a day not stored is absent; the window keeps "
          "the five years before the day")
    # The attribution, over one session.
    day, prev = y[-1][0], y[-2][0]
    ser = {"yield": y, "kw": [], "acm": []}
    ev = od.evaluate(ser, day, cfg)
    check(ev["fired"] and ev["state"] == "awaiting" and "awaiting" in ev["line"]
          and ev["attribution"]["horizon"] == 1,
          "with no model stored on the day the attribution prints \"awaiting\"")
    ser = {"yield": y, "kw": [(prev, 1.00), (day, 1.20)], "acm": [(prev, 0.5)]}
    ev = od.evaluate(ser, day, cfg)
    kw = next(m for m in ev["attribution"]["models"] if m["model"] == "kw")
    acm = next(m for m in ev["attribution"]["models"] if m["model"] == "acm")
    check(ev["state"] == "partial" and kw["premium_bp"] == 20.0
          and kw["premium_share"] == round(20 / 30, 2) and kw["carried"] == "the term premium"
          and acm["state"] == "awaiting" and "awaiting" in ev["line"],
          "KW's one-session share by hand (20 of 30 bp, 0.67: the term premium); ACM "
          "awaiting; the read is partial")
    ser["acm"] = [(prev, 0.5), (day, 0.55)]
    ev = od.evaluate(ser, day, cfg)
    check(ev["state"] == "computed" and "disagree" in ev["line"],
          "KW on the premium and ACM on expected short rates (5 of 30 bp): the models "
          "disagree, and the line says so")
    check(od.flag_line(ev) == ev["line"] and od.flag_line({"fired": False}) is None,
          "the close's flag line on a trigger day, nothing otherwise")


def group_b() -> None:
    head("B. D15'S LEDGER")
    cfg = od.config()
    y = yield_fixture(tail=(30.0,))
    day = y[-1][0]
    fwd = [(d, y[-1][1] + 0.01 * (i + 1)) for i, d in enumerate(days_from(
        (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat(), 25))]
    path = y + fwd
    base = dict(path)[day]
    oc = od.outcomes(day, path, 30.0, cfg)
    check(oc["y10_5d_bp"] == round((fwd[4][1] - base) * 100, 1)
          and oc["y10_20d_bp"] == round((fwd[19][1] - base) * 100, 1)
          and oc["continued"] is True and oc["resolved"],
          f"the 5- and 20-session outcomes by hand ({oc['y10_5d_bp']}, {oc['y10_20d_bp']} "
          f"bp); continued on the 5-session sign")
    oc2 = od.outcomes(day, path, -30.0, cfg)
    check(oc2["continued"] is False, "a fall followed by a rise did not continue")
    oc3 = od.outcomes(day, y, 30.0, cfg)
    check(oc3["resolved"] is False and oc3["y10_5d_bp"] is None,
          "a horizon not yet stored is None, and the row unresolved")
    ev = od.evaluate({"yield": y, "kw": [], "acm": []}, day, cfg)
    row = od.ledger_row(ev, NOW, oc3)
    body = json.loads(row["value"])
    check(row["registry_key"] == od.LEDGER_KEY and row["instrument"] == day
          and body["state"] == "awaiting" and body["threshold_bp"] == ev["trigger"]["threshold_bp"],
          "the ledger row: keyed by the day, the trigger and the awaiting attribution")
    prev = y[-2][0]
    ser = {"yield": path, "kw": [(prev, 1.0), (day, 1.2)], "acm": [(prev, 0.5), (day, 0.7)]}
    new = od.resolve_rows([body], ser, "2026-11-30T23:00:00+00:00", cfg)
    nb = json.loads(new[0]["value"]) if new else {}
    check(len(new) == 1 and nb["state"] == "computed" and nb["outcomes"]["resolved"]
          and "the term premium carried the move" in nb["verdict"],
          "resolve writes a new vintage once the models land: both on the term premium")
    check(od.resolve_rows([nb], ser, "2026-12-01T23:00:00+00:00", cfg) == [],
          "a resolved row writes nothing again")
    raw = PREREG.read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == PREREG_SHA,
          f"the pre-registration holds its SHA-256 ({PREREG_SHA[:16]}...)")
    try:
        reg, mod, scr = (first_commit(p) for p in (
            "docs/ledgers/oneday-10y-preregistration-2026-10.md", "altdata/oneday_10y.py",
            "tools/calibration/d15_oneday_10y.py"))
        if reg and mod and scr and not shallow():
            check(ancestor(reg[-1], mod[-1]) and ancestor(reg[-1], scr[-1])
                  and reg[-1] not in (mod[-1], scr[-1]),
                  "the pre-registration was committed alone, before the scoring code")
        else:
            print("  note  history too shallow to order the commits; the SHA pin stands")
    except Exception as exc:                                    # noqa: BLE001
        print(f"  note  git unavailable ({type(exc).__name__}); the SHA pin stands")
    import d15_oneday_10y as S
    src = (REPO / "tools" / "calibration" / "d15_oneday_10y.py").read_text(encoding="utf-8")
    check("ObservationStore" not in src and "open_writer" not in src
          and "oneday-10y-preregistration-2026-10.md" in src,
          "the script names its registration and opens no store")

    def r(leg, cont, day):
        return {"day": day, "leg": leg, "continued": cont, "move_bp": 20.0,
                "threshold_bp": 15.0, "kw_share": 0.4, "acm_share": 0.4,
                "y10_5s_bp": 5.0, "y10_20s_bp": 5.0}
    data = {"yield": [("2026-01-01", 4.0)], "kw": [], "acm": []}
    few = [r(S.PREMIUM, True, f"2000-01-{i + 1:02d}") for i in range(5)]
    v = S.verdict(few, data, "fixture", ["2026-01-01"])
    check(v["verdict"].startswith("INSUFFICIENT"), "fewer than 15 in a group: INSUFFICIENT")
    rows = []
    for i in range(40):
        leg = S.PREMIUM if i % 2 else S.PATH
        rows.append(r(leg, leg == S.PREMIUM or i % 4 == 0, f"{1990 + i}-06-01"))
    v = S.verdict(rows, data, "fixture", ["2026-01-01"])
    check(v["verdict"].startswith("PASS"), f"20 and 20, shares 1.00 against 0.50 with "
          f"the same sign by half: PASS ({v['verdict'][:40]})")
    flat = [r(S.PREMIUM if i % 2 else S.PATH, i % 4 < 2, f"{1990 + i}-06-01")
            for i in range(40)]
    v = S.verdict(flat, data, "fixture", ["2026-01-01"])
    check(v["verdict"].startswith("FAIL"), "equal shares: FAIL")
    txt = EDITION.read_text(encoding="utf-8")
    check(re.search(r"\| Verdict \| \*\*INSUFFICIENT \(term premium 2, expected short "
                    r"rates 65", txt) and "| n | 67 |" in txt
          and "Rights consequence | None." in txt
          and (REPO / "docs" / "ledgers" / "d15-ledger-2026-10-24-episodes.csv").is_file(),
          "the laptop first edition is on file as printed: INSUFFICIENT, n 67, no rights")


def group_c() -> None:
    head("C. THE HYPOTHESES, REGISTERED FIRST")
    from alpha import hypotheses as H
    from alpha import rules
    doc = H.load_batch(BATCH.read_text(encoding="utf-8"))
    check(H.validate_batch(doc) == [] and H.budget_errors(doc) == [],
          "the batch validates against alpha-lab-hypotheses/v1 and the sitting's budget")
    check(doc["model_idea_rule"] is True and doc["source"] == "model"
          and len(doc["hypotheses"]) == 3, "three hypotheses, a model's, under the "
          "model-idea rule")
    hs = {h["local_id"]: h for h in doc["hypotheses"]}
    try:
        c = rules.compile_rule(hs["H-B59-3"]["rule_dsl"])
        ok = c.instruments == ["SMH", "SPY"] and "ai.model_releases_week_total" in c.keys
    except Exception as exc:                                    # noqa: BLE001
        ok = False
        print(f"  ({type(exc).__name__}: {exc})")
    check(ok and hs["H-B59-3"]["needs_code"] is False,
          "H-B59-3 (model releases, SMH against SPY) compiles in the grammar")
    check(all(hs[k]["needs_code"] is True and not hs[k].get("rule_dsl")
              and any("needs code" in g for g in hs[k]["data"]["gaps"])
              for k in ("H-B59-1", "H-B59-2")),
          "H-B59-1 (GDELT) and H-B59-2 (degree days) need code, each with its reason")
    check(not list((REPO / "alpha" / "research").rglob("*B59*report*")),
          "no backtest of them is committed")
    try:
        b = first_commit("alpha/research/hypotheses-2026-10-24-b59-sources.yaml")
        rd = [first_commit(p) for p in READERS]
        if b and all(rd) and not shallow():
            files = subprocess.run(["git", "show", "--name-only", "--format=", b[-1]],
                                   cwd=REPO, capture_output=True, text=True,
                                   timeout=30).stdout.split()
            check(files == ["alpha/research/hypotheses-2026-10-24-b59-sources.yaml"],
                  "the batch was committed alone")
            check(all(ancestor(b[-1], x[-1]) and b[-1] != x[-1] for x in rd),
                  "the batch was committed before each of the three readers")
        else:
            print("  note  history too shallow to order the commits")
    except Exception as exc:                                    # noqa: BLE001
        print(f"  note  git unavailable ({type(exc).__name__})")


# ---------------------------------------------------------------------------
def v2row(a1="", a2="", root="01", tone="0", geo="", added="20261023120000", url=""):
    c = [""] * 61
    c[7], c[17], c[28], c[34], c[53], c[59], c[60] = a1, a2, root, tone, geo, added, url
    return "\t".join(c)


def v1row(a1="", a2="", root="01", tone="0", geo="", added="20261023", url=""):
    c = [""] * 58
    c[7], c[17], c[28], c[34], c[51], c[56], c[57] = a1, a2, root, tone, geo, added, url
    return "\t".join(c)


def zipped(text: str) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x.export.CSV", text)
    return b.getvalue()


def group_d() -> None:
    head("D. GDELT")
    cfg = gdelt.config()
    lines = [
        v2row(a1="TWN", root="19", tone="-5", url="https://x.example/2026/10/23/taiwan-drills-near-data-center"),
        v2row(a1="CHN", a2="USA", root="16", tone="-2", url="https://x.example/a"),
        v2row(geo="IR", root="18", tone="-8", url="https://x.example/b"),
        v2row(a1="USA", a2="GBR", root="04", tone="3", url="https://y.example/midterm-elections-poll"),
        v2row(a1="TWN", root="19", tone="-5", added="20261024000000", url="https://x.example/c"),
        "too\tshort",
        v1row(a1="RUS", root="20", tone="-6", url="https://z.example/d"),
        v2row(root="01", tone="1", url="https://z.example/bojangles-opens-store"),
    ]
    acc = gdelt.accumulate(gdelt.new_acc(), "\n".join(lines), cfg, "20261023")
    f = acc["fam"]
    check(acc["events"] == 6 and acc["bad_lines"] == 1,
          "six events on the day: another day's row and a malformed row left out "
          "(the malformed one counted)")
    check(f["taiwan_strait"]["n"] == 2 and f["taiwan_strait"]["conflict"] == 1
          and f["taiwan_strait"]["reduce_relations"] == 1
          and f["taiwan_strait"]["tone_sum"] / f["taiwan_strait"]["tone_n"] == -3.5,
          "Taiwan Strait: an actor (TWN, root 19: conflict) and a dyad (CHN-USA, root 16: "
          "reduce relations); tone -3.5 by hand")
    check(f["us_china"]["reduce_relations"] == 1 and f["us_china"]["conflict"] == 0,
          "an event counts in every family it matches (the CHN-USA dyad in US-China too)")
    check(f["middle_east_gulf"]["conflict"] == 1 and f["russia_ukraine"]["conflict"] == 1
          and "korean_peninsula" not in f,
          "the action's FIPS location (IR) and the 1.0 layout's actor (RUS, root 20)")
    check(len(acc["narr"].get("ai_capex_durability") or ()) == 1
          and len(acc["narr"].get("midterm_cycle") or ()) == 1
          and not acc["narr"].get("yen_carry"),
          "narratives match whole words of the address (data-center, midterm-elections); "
          "\"boj\" inside \"bojangles\" does not")
    rows = gdelt.rows_for_day("2026-10-23", acc, cfg, NOW, gdelt.SOURCE_V2)
    by = {(r["registry_key"], r["instrument"]): r["value"] for r in rows}
    check(by[(gdelt.SHARE_KEY, "taiwan_strait")] == round(10000 / 6, 3)
          and by[(gdelt.CONFLICT_KEY, "korean_peninsula")] == 0
          and by[(gdelt.NARR_KEY, "yen_carry")] == 0
          and all((gdelt.NARR_KEY, n) in by for n in cfg["narratives"])
          and by[(gdelt.EVENTS_KEY, None)] == 6 and by[(gdelt.URLS_KEY, None)] == 6,
          "the share per 10,000 by hand (1 of 6: 1,666.667); every family and story a "
          "row, zero included")
    check({f["id"] for f in cfg["families"]} >= {"taiwan_strait", "middle_east_gulf",
                                                  "russia_ukraine", "korean_peninsula"}
          and all(f.get("factor") == "III" and f.get("scenario") for f in cfg["families"])
          and cfg["measures"]["conflict"] == ["18", "19", "20"],
          "the families map to the Twenty-Five's Family D and Factor III, from config")
    good = zipped("\n".join(lines[:4]))
    calls, pauses = [], []

    def ok_fetch(url):
        calls.append(url)
        return good

    def bad_fetch(url):
        calls.append(url)
        if "20261023120000" in url:
            raise RuntimeError("HTTP 404")
        return good
    day = dt.date(2026, 10, 23)
    acc2, why = gdelt.fetch_day_v2(day, cfg, bad_fetch, pauses.append)
    check(acc2 is None and why.startswith("STALE") and "20261023120000" in why,
          "a failed export: the day is STALE with its reason")
    db = store([])
    cfg1 = dict(cfg, catch_up_days=1)
    now = dt.datetime(2026, 10, 24, 21, 25, tzinfo=dt.timezone.utc)
    with observations.ObservationStore(db) as st:
        out = gdelt.daily(now=now, cfg=cfg1, fetch=bad_fetch, sleep=lambda s: None, db=st,
                          record=False)
        n_rows = len(st.as_of(gdelt.EVENTS_KEY, NOW))
    check(out["stale"].get("2026-10-23") and out["written"] == 0 and n_rows == 0,
          "the daily step writes nothing for a STALE day (never filled)")
    calls.clear()
    pauses.clear()
    with observations.ObservationStore(db) as st:
        out = gdelt.daily(now=now, cfg=cfg1, fetch=ok_fetch, sleep=pauses.append, db=st,
                          record=False)
        stored = st.as_of(gdelt.SHARE_KEY, "2099-01-01T00:00:00+00:00", "taiwan_strait")
    check(len(calls) == 96 and len(pauses) == 95 and out["written"] > 0
          and stored and stored[0]["observed_at"][:10] == "2026-10-23",
          "a good day: 96 exports, paced (95 pauses of the configured length), written")
    calls.clear()
    with observations.ObservationStore(db) as st:
        out = gdelt.daily(now=now, cfg=cfg1, fetch=ok_fetch, sleep=lambda s: None, db=st,
                          record=False)
    check(not calls and out["rows"] == 0, "a stored day is not read again")
    check(gdelt.last_complete_day(dt.datetime(2026, 10, 24, 0, 10, tzinfo=dt.timezone.utc))
          == dt.date(2026, 10, 22), "before 00:30 UTC the day before is not yet complete")
    src = (REPO / "altdata" / "sources" / "gdelt.py").read_text(encoding="utf-8")
    check("api.gdeltproject.org" not in src + (REPO / "config" / "gdelt.yaml").read_text(
        encoding="utf-8").split("DOC API")[0], "the DOC API is not read")


def group_e() -> None:
    head("E. NOAA CPC DEGREE DAYS")
    cfg = cpc.config()
    txt = ("Product: Daily Heating Degree Days\nRegions: CPC::Regions::CensusDivisions\n"
           "Weights: Population\nRegion|20260101|20260102|20260103\n1|30|31|x\n"
           "CONUS|20|22|25\n")
    p = cpc.parse(txt, cfg)
    check(p["conus"] == [("2026-01-01", 20.0), ("2026-01-02", 22.0), ("2026-01-03", 25.0)]
          and p["new_england"] == [("2026-01-01", 30.0), ("2026-01-02", 31.0)],
          "the file parsed by region; a cell that is not a number is left out, never filled")
    pts = []
    for y in range(1991, 2021):
        pts += [(f"{y}-01-{d:02d}", float(y - 1990)) for d in range(1, 8)]
    pts += [(f"2026-01-{d:02d}", 20.0) for d in range(1, 8)]
    w = cpc.window_read(pts, cfg)
    check(w["sum"] == 140.0 and w["normal"] == 108.5 and w["departure"] == 31.5
          and w["lens"] is not None,
          "the seven-day sum 140 against a 1991-2020 normal of 108.5 (7 x 15.5) by hand: "
          "+31.5")
    short = [(d, v) for d, v in pts if d >= "2011"]
    w2 = cpc.window_read(short, cfg)
    check(w2["normal_state"] == "not read" and "departure" not in w2,
          "with 10 of the normal years stored there is no normal")
    known = {("conus", "2026-01-01"): 20.0}
    rs = cpc.rows("hdd", p, NOW, since="2026-01-01", known=known)
    check(len(rs) == 4 and all(r["source"] == cpc.SOURCE for r in rs)
          and not any(r["instrument"] == "conus" and r["observed_at"] == "2026-01-01"
                      for r in rs),
          "a re-read day with an unchanged value writes nothing; the rest are written")

    def bad(url):
        raise RuntimeError("HTTP 503")
    out = cpc.daily(dry_run=True, today="2026-10-24", cfg=cfg, fetch=bad,
                    sleep=lambda s: None, record=False)
    check(out["failed"].get(cpc.HDD_KEY) and out["rows"] == 0,
          "a failed fetch is listed and writes nothing")
    seen = []
    out = cpc.daily(dry_run=True, today="2026-01-05", cfg=cfg,
                    fetch=lambda u: (seen.append(u), txt)[1], sleep=lambda s: None,
                    record=False)
    check(any("/2025/" in u for u in seen) and any("/2026/" in u for u in seen),
          "in early January the year before is read too")
    lines = cpc.lines({"hdd": {"state": "absent"}, "cdd": {"state": "absent"}})
    check(any("not read" in ln for ln in lines) and any("not stored" in ln for ln in lines),
          "with nothing stored the lines say not read")


def group_f() -> None:
    head("F. THE HUGGING FACE MODEL-RELEASE WATCH")
    check(hf.weekly_counts(["2026-10-12", "2026-10-18", "2026-10-19"],
                           ["2026-10-12", "2026-10-19"]) == {"2026-10-12": 2, "2026-10-19": 1},
          "the weekly count by hand (Monday to Sunday)")
    check(hf.last_complete_week(dt.date(2026, 10, 24)) == dt.date(2026, 10, 12),
          "on Saturday 24 Oct the newest complete week is that of 12 Oct")
    cfg = {"api": "https://hub.example/api/models", "page_size": 2, "pause_seconds": 0,
           "reread_weeks": 4,
           "organisations": [{"id": "lab-a", "group": "china"}, {"id": "lab-b", "group": "peer"}]}
    pages = {
        None: ([{"id": "lab-a/m3", "createdAt": "2026-10-14T01:00:00.000Z"},
                {"id": "other/x", "createdAt": "2026-10-13T00:00:00.000Z"}],
               {"link": '<https://hub.example/p2>; rel="next"'}),
        "https://hub.example/p2": ([{"id": "lab-a/m2", "createdAt": "2026-10-13T00:00:00.000Z"},
                                    {"id": "lab-a/m1", "createdAt": "2026-09-01T00:00:00.000Z"}],
                                   {"link": '<https://hub.example/p3>; rel="next"'}),
        "https://hub.example/p3": ([{"id": "lab-a/m0", "createdAt": "2025-01-01T00:00:00.000Z"}], {}),
    }
    asked = []

    def fetch(url, params):
        key = None if params else url
        asked.append(key)
        return pages[key]
    got = hf.list_org("lab-a", cfg, fetch, lambda s: None, stop_before="2026-09-21")
    check([r["id"] for r in got] == ["lab-a/m3", "lab-a/m2", "lab-a/m1"]
          and asked == [None, "https://hub.example/p2"],
          "only the declared organisation's repositories; paging stops once a page "
          "reaches past the recount window")

    def fetch2(url, params):
        if params and params.get("author") == "lab-b":
            raise RuntimeError("HTTP 429")
        return fetch(url, params)
    db = store([])
    with observations.ObservationStore(db) as st:
        out = hf.daily(today="2026-10-24", cfg=cfg, fetch=fetch2, sleep=lambda s: None,
                       db=st, record=False)
        tot = st.as_of(hf.TOTAL_KEY, "2099-01-01T00:00:00+00:00")
        org = {r["observed_at"][:10]: r["value_num"] for r in
               st.as_of(hf.ORG_KEY, "2099-01-01T00:00:00+00:00", "lab-a")}
        evs = st.as_of(hf.EVENT_KEY, "2099-01-01T00:00:00+00:00", "lab-a/m3")
    check(out["failed"].get("lab-b", "").startswith("STALE") and not tot
          and str(out["total"]).startswith("not written"),
          "a refused organisation is STALE and the total is not written")
    check(org == {"2026-09-21": 0.0, "2026-09-28": 0.0, "2026-10-05": 0.0, "2026-10-12": 2.0},
          "lab-a's four recounted weeks by hand (two in the week of 12 Oct)")
    check(evs and evs[0]["observed_at"][:10] == "2026-10-14"
          and evs[0]["available_at"][:10] == dt.datetime.now(dt.timezone.utc).date().isoformat()
          and json.loads(evs[0]["value_text"])["created"] == "2026-10-14",
          "a release event is observed on its creation day and available at the pull "
          "that saw it, never createdAt")
    asked.clear()
    with observations.ObservationStore(db) as st:
        out = hf.daily(today="2026-10-24", cfg=cfg, fetch=fetch, sleep=lambda s: None,
                       db=st, record=False)
        tot = {r["observed_at"][:10]: r["value_num"]
               for r in st.as_of(hf.TOTAL_KEY, "2099-01-01T00:00:00+00:00")}
        n_ev = len(st.instruments(hf.EVENT_KEY))
    check(tot.get("2026-10-12") == 2.0 and n_ev == 2,
          "with every organisation read the total is written; a repository seen before "
          "is not a second event")
    val = (REPO / "altdata" / "sources" / "hf_releases.py").read_text(encoding="utf-8")
    check("downloads" not in re.sub(r'"""[\s\S]*?"""', "", val)
          and "likes" not in re.sub(r'"""[\s\S]*?"""', "", val),
          "counts and dates only: no downloads or likes are read into a row")


# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G. PLACEMENT")
    from daily_cascade import absorption_block, b59_block
    y = yield_fixture(tail=(30.0,))
    db = store([obs("fred.yield_10y", d, v, src="fred") for d, v in y])
    day = y[-1][0]
    built = {"mechanics": {"items": [], "subsections": [{"title": "Volatility event"},
                                                        {"title": "Other"}]}}
    with observations.ObservationStore(db) as st:
        b59_block.close_extras(built, st, day, NOW)
        subs = built["mechanics"]["subsections"]
        rows = b59_block.store_rows(built["mechanics"]["data"], NOW)
        blk = od.block(st, NOW, y[-5][0], day)
        quiet = od.block(st, NOW, y[-5][0], y[-2][0])
    check(subs[1]["title"] == b59_block.ONEDAY_CLOSE_TITLE and "awaiting" in subs[1]["lines"][0]
          and any(i["key"] == "mech:oneday_10y" for i in built["mechanics"]["items"]),
          "the close: the flag line in the event area, right after item 52's block")
    check(len(rows) == 1 and rows[0]["registry_key"] == od.LEDGER_KEY,
          "the close stores the trigger day's ledger row")
    check(blk["table"]["rows"][0][0] == day and blk["table"]["rows"][0][-1] == "awaiting"
          and quiet["lines"][0].startswith("No 10-year one-day move"),
          "the Weekly's and Monthly's block: the trigger days in a table, or one line")
    with observations.ObservationStore(store([])) as st:
        sec: dict = {}
        b59_block.weekly_narratives(sec, st, NOW)
        mech = b59_block.mechanics_subsections([{"title": "The oil-shock signature"},
                                                {"title": "Gold events"}, {"title": "Z"}],
                                               st, NOW, "2026-10-19", "2026-10-23")
        slow = b59_block.place_slow([{"title": absorption_block.FACTOR_TITLE}, {"title": "Y"}],
                                    st, NOW)
        tail = b59_block.tail_subsection(st, NOW)
    titles = [s["title"] for s in sec["subsections"]]
    check(titles == [b59_block.GDELT_STORIES_TITLE, "AI: open model releases"]
          and "not read" in sec["subsections"][0]["lines"][0]
          and "not read" in sec["subsections"][1]["lines"][0],
          "the Weekly's narratives: the stories' GDELT counts and the model-release line, "
          "\"not read\" before the first pull")
    mt = [s["title"] for s in mech]
    check(mt == ["The oil-shock signature", cpc.TITLE, "Gold events", od.BLOCK_TITLE, "Z"],
          "Mechanics: the degree days after the oil-shock signature, D15's block after "
          "the event blocks")
    check([s["title"] for s in slow] == [absorption_block.FACTOR_TITLE,
                                          b59_block.GDELT_FACTOR_TITLE, hf.TITLE, "Y"],
          "the Monthly's slow layers: Factor III's GDELT lines and Factor I-b's block "
          "right after the Factor lines")
    check(tail and "not read" in tail["lines"][0], "the Weekly's tail register line")
    rd = lambda p: (REPO / p).read_text(encoding="utf-8")       # noqa: E731
    check("b59_block.close_extras(built, st, p[\"session\"], cutoff)" in rd("daily_cascade/stack.py")
          and "b59_block.store_rows" in rd("daily_cascade/stack_close.py")
          and rd("daily_cascade/weekly_stack.py").count("b59_block.") >= 3
          and rd("monthly_macro/stack.py").count("b59_block.") >= 3,
          "the hooks: the close, its store, the Weekly (three) and the Monthly (three)")
    sh, eod, fd = rd("scripts/run_crypto_basket.sh"), rd("scripts/run_eod_cron.sh"), \
        rd("altdata/feeds.py")
    check(all(f"altdata.sources.{m} daily" in sh for m in ("gdelt", "cpc_degree_days",
                                                            "hf_releases"))
          and "altdata.oneday_10y resolve" in eod and "printf '%s\\n' \"$OD_OUT\"" in eod
          and all(x in fd for x in ("_gd.ROSTER", "_cpc.ROSTER", "_hf.ROSTER")),
          "the basket's three steps (no new timer), the rosters and the EOD resolve")


def group_h() -> None:
    head("H. HYGIENE")
    import yaml
    reg = [derived.registry_entry(k) for k in NEW_KEYS]
    check(all(reg) and all(e.get("trigger_eligible") is False for e in reg),
          f"the {len(NEW_KEYS)} new keys are registered, none trigger-eligible")
    fams = {k: derived.family_of(k)[0] for k in NEW_KEYS}
    mr = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    excl = mr.get("lens_excluded") or {}
    check(all(fams[k] or k in excl for k in NEW_KEYS),
          "each has a lens family, or is excluded with its reason (the two JSON records)")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    rg = (REPO / "regime.py").read_text(encoding="utf-8")
    check(not any(k in ms or k in rg for k in NEW_KEYS)
          and not any(p in ms or p in rg for p in ("gdelt", "noaa.", "model_release",
                                                   "oneday")),
          "barred from the market-state object: named in neither its config nor regime.py")
    sr = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    srcs = sr.get("sources") or sr
    check(all(s in srcs for s in ("gdelt", "noaa_cpc", "huggingface", "oneday_10y"))
          and all("24 Oct 2026" in str(srcs[s].get("license")) for s in
                  ("gdelt", "noaa_cpc", "huggingface")),
          "the four sources registered, each external one with its dated check")
    for c in NEW_CONFIG[1:]:
        t = c.read_text(encoding="utf-8")
        check("24 Oct 2026" in t and "robots" in t, f"{c.name} records its robots.txt and "
                                                    f"terms check")
    lags = yaml.safe_load((REPO / "config" / "publication_lags.yaml").read_text(encoding="utf-8"))
    nf = next((f for f in lags["families"] if f["id"] == "noaa_cpc_degree_days"), None)
    check(nf and nf["lag_sessions"] <= nf["max_lag"] and set(nf["keys"]) == set(cpc.ROSTER_KEYS),
          "the degree days' publication lag, within its bound")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8"))
    cmds = cat.get("commands") or cat
    check(all(m in cmds for m in ("altdata.sources.gdelt", "altdata.sources.cpc_degree_days",
                                  "altdata.sources.hf_releases", "altdata.oneday_10y")),
          "the four commands catalogued")
    src = "\n".join(p.read_text(encoding="utf-8") for p in NEW_CODE)
    imports = "\n".join(l for l in src.splitlines() if re.match(r"\s*(from|import)\s", l))
    check(not re.search(r"regime|market_state|composite|register|manual_input|flashalpha|vendor",
                        imports),
          "no composite, market-state, register, by-hand or vendor import in the new code")
    check(not re.search(r"\.execute\(\s*\"(?:INSERT|UPDATE|DELETE)", src),
          "no direct SQL write (the writers go through open_writer)")
    units = [p for p in (REPO / "deploy" / "systemd").glob("*")
             if re.search(r"gdelt|degree|hf_|release|oneday", p.name)]
    check(not units, "no unit file")
    check("User-Agent" not in src and "_base import" in src,
          "every request goes through _base, with the generic User-Agent")
    mine = "\n".join([src] + [p.read_text(encoding="utf-8") for p in NEW_CONFIG] + [
        PREREG.read_text(encoding="utf-8"), EDITION.read_text(encoding="utf-8"),
        BATCH.read_text(encoding="utf-8")])
    check(not re.search(r"(?<![\w./])@[A-Za-z_]\w+|[\w.+-]+@[\w-]+\.[a-z]{2,}", mine),
          "no handle and no email address in the new files")
    check(not re.search(r"\b(Mr|Ms|Mrs|Dr)\.? [A-Z][a-z]+", mine),
          "no person named by title in the new files")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())

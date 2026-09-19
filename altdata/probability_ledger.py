"""
The probability ledger -- every number this system states as a likelihood, scored.

-----------------------------------------------------------------------------
THE POINT IS CALIBRATION, NOT ACCURACY
-----------------------------------------------------------------------------
A forecaster who says 70% and is right 70% of the time is perfectly calibrated and
wrong three times in ten. One who says 95% and is right 70% of the time is
confidently miscalibrated, and no amount of being "usually right" fixes it. Nothing
in this system has ever been able to tell those two apart, because no probability
it emitted was ever written down in a form that could be scored.

So every probability gets a row, at EMISSION, and the row carries the thing that
makes scoring honest:

    THE RESOLUTION CRITERION IS DECLARED BEFORE THE OUTCOME IS KNOWN.
    This is the whole ledger. "Recession in 2026" resolves differently depending
    on whether you meant two negative quarters, an NBER declaration, or a feeling
    -- and a criterion chosen after the fact is chosen to flatter. The column is
    NOT NULL for that reason, and resolution refuses to run without one.

-----------------------------------------------------------------------------
THE SCORE IS BRIER, AND WHAT IT DOES AND DOES NOT MEAN
-----------------------------------------------------------------------------
    brier = (p - outcome)^2,  outcome in {0, 1}.  Lower is better.

        0.00  certain and right
        0.25  what you get by always saying 50%
        1.00  certain and wrong

A source whose running Brier is ABOVE 0.25 is worse than a coin, and that is the
first thing the report should be able to say. Below it, the number alone cannot
separate a well-calibrated forecaster from a lucky one: Brier conflates
calibration with resolution (the willingness to say anything other than the base
rate), and separating them needs the reliability/resolution/uncertainty
decomposition, which needs an n this ledger will not have for a year. The running
score is therefore reported WITH its n and against the 0.25 reference, and the
decomposition is named as owed rather than faked.

-----------------------------------------------------------------------------
A SCENARIO SET MUST SUM TO ONE
-----------------------------------------------------------------------------
The Monthly emits scenario WEIGHTS -- mutually exclusive, collectively exhaustive.
If they do not sum to 1 the set is incoherent and every score computed from it is
measuring the wrong thing, so a set_id ties them together and coherence() checks
the sum. A set that does not add up is reported, not normalised: silently rescaling
somebody's stated weights would hide the error and change what they claimed.

-----------------------------------------------------------------------------
WHAT IS NOT IN HERE YET, AND WHY
-----------------------------------------------------------------------------
Nothing, as of 19 September 2026 -- because nothing in this system emits a
machine-readable probability. The Monthly's section III is literally
`*[Manual — scenarios and probabilities]*`; every `%` in the rendered report is a
measured level (CPI, HY OAS, unemployment), not a weight. The tail-scenario
reference carries no probabilities at all and says why: "effective n is
approximately zero for all 25 ... they are conditioners, never triggers."

seed_from_monthly() therefore parses the Monthly for a scenario table and reports
what it finds, which today is nothing. It is written now so that the moment section
III becomes machine-readable the ledger fills by itself, and `record` exists so the
operator can put a probability in by hand before then. No weights are invented to
give the table something to hold: a made-up number in a scoring ledger is worse
than an empty one, because it will be scored and believed.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

from . import observations, session

log = logging.getLogger("altdata.probability_ledger")

REPO = Path(__file__).resolve().parent.parent

# What a coin gets. The reference every running score is read against.
COIN_BRIER = 0.25

SCHEMA = """
CREATE TABLE IF NOT EXISTS probabilities (
    -- Deterministic from source + claim + emitted_at, so re-seeding the same
    -- report is a no-op rather than a duplicate. A genuinely NEW forecast of the
    -- same claim has a different emitted_at and is a different row -- which is
    -- correct: revising 30% to 55% is two forecasts and both should be scored.
    probability_id TEXT PRIMARY KEY,
    source        TEXT NOT NULL,
    scenario_set  TEXT,
    claim         TEXT NOT NULL,
    probability   REAL NOT NULL CHECK (probability >= 0.0 AND probability <= 1.0),
    emitted_at    TEXT NOT NULL,
    horizon_date  TEXT NOT NULL,

    -- DECLARED AT EMISSION, NOT NULL. The ledger's whole integrity rests here:
    -- a criterion chosen after the outcome is chosen to flatter.
    resolution_criterion TEXT NOT NULL,

    -- Written once, on resolution.
    resolved_at   TEXT,
    outcome       INTEGER CHECK (outcome IS NULL OR outcome IN (0, 1)),
    resolution_note TEXT,
    brier         REAL,

    emitted_by    TEXT,
    method_version TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS prob_by_source ON probabilities (source, emitted_at);
CREATE INDEX IF NOT EXISTS prob_by_set    ON probabilities (scenario_set);
CREATE INDEX IF NOT EXISTS prob_open      ON probabilities (resolved_at, horizon_date);

-- A FORECAST IS IMMUTABLE IN ITS FORECAST. The probability, the claim, the
-- criterion and the emission instant can never change; only the resolution
-- fields may be written, and only from NULL. Anything else would let a forecaster
-- edit his prediction after seeing the outcome, which is the one thing a scoring
-- ledger exists to prevent -- so it is a schema constraint and not a convention.
CREATE TRIGGER IF NOT EXISTS probabilities_forecast_immutable
BEFORE UPDATE ON probabilities
WHEN OLD.probability   IS NOT NEW.probability
  OR OLD.claim         IS NOT NEW.claim
  OR OLD.resolution_criterion IS NOT NEW.resolution_criterion
  OR OLD.emitted_at    IS NOT NEW.emitted_at
  OR OLD.source        IS NOT NEW.source
BEGIN SELECT RAISE(ABORT, 'a forecast is immutable; emit a new one to revise'); END;

CREATE TRIGGER IF NOT EXISTS probabilities_resolve_once
BEFORE UPDATE OF outcome ON probabilities
WHEN OLD.outcome IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'already resolved; a resolution is written once'); END;

CREATE TRIGGER IF NOT EXISTS probabilities_no_delete
BEFORE DELETE ON probabilities
BEGIN SELECT RAISE(ABORT, 'a forecast is not deletable; it is the record'); END;
"""

METHOD_VERSION = "brier-v1"


def probability_id(source: str, claim: str, emitted_at: str) -> str:
    raw = f"{source}\x1f{claim}\x1f{emitted_at}".encode()
    return hashlib.sha256(raw).hexdigest()[:32]


def brier(p: float, outcome: int) -> float:
    """(p - outcome)^2. The whole score."""
    return (float(p) - float(outcome)) ** 2


class ProbabilityLedger:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or observations.DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ProbabilityLedger":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- emission ----------------------------------------------------------
    def record(self, *, source: str, claim: str, probability: float,
               horizon_date: str, resolution_criterion: str,
               scenario_set: Optional[str] = None,
               emitted_at: Optional[str] = None,
               emitted_by: Optional[str] = None) -> str:
        """Write one forecast. Refuses a claim with no resolution criterion."""
        if not str(resolution_criterion or "").strip():
            raise ValueError(
                "a forecast needs a resolution criterion declared at emission -- "
                "without one the outcome is decided after the fact, which is the "
                "one thing this ledger exists to prevent")
        p = float(probability)
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"probability {p} is not in [0, 1]")
        at = emitted_at or session.utc_iso()
        pid = probability_id(source, claim, at)
        self.conn.execute(
            "INSERT OR IGNORE INTO probabilities (probability_id, source, "
            " scenario_set, claim, probability, emitted_at, horizon_date, "
            " resolution_criterion, emitted_by, method_version) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pid, source, scenario_set, claim, p, at, horizon_date,
             resolution_criterion, emitted_by, METHOD_VERSION))
        self.conn.commit()
        return pid

    # -- resolution --------------------------------------------------------
    def resolve(self, probability_id_: str, outcome: int, *,
                note: Optional[str] = None,
                resolved_at: Optional[str] = None) -> dict:
        """Resolve one forecast and score it. Writes once, by trigger."""
        row = self.conn.execute(
            "SELECT * FROM probabilities WHERE probability_id = ?",
            (probability_id_,)).fetchone()
        if row is None:
            raise KeyError(f"no forecast {probability_id_!r}")
        if int(outcome) not in (0, 1):
            raise ValueError("outcome must be 0 or 1")
        b = brier(row["probability"], int(outcome))
        self.conn.execute(
            "UPDATE probabilities SET outcome = ?, resolved_at = ?, "
            "       resolution_note = ?, brier = ? WHERE probability_id = ?",
            (int(outcome), resolved_at or session.utc_iso(), note, b,
             probability_id_))
        self.conn.commit()
        return {"probability_id": probability_id_, "probability": row["probability"],
                "outcome": int(outcome), "brier": b, "claim": row["claim"]}

    # -- reads -------------------------------------------------------------
    def all_rows(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM probabilities ORDER BY emitted_at")]

    def due(self, as_of: Optional[str] = None) -> list[dict]:
        """Unresolved forecasts whose horizon has passed -- the work queue."""
        today = (as_of or session.utc_iso())[:10]
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM probabilities WHERE outcome IS NULL "
            "  AND horizon_date <= ? ORDER BY horizon_date", (today,))]

    def score_by_source(self) -> dict:
        """Running Brier per source, with n and the coin reference.

        Reported WITH n and against 0.25 because the number alone says less than
        it looks like it does: above the coin line is unambiguous, below it the
        score cannot separate calibration from resolution without a decomposition
        this ledger has nowhere near the sample for.
        """
        out: dict[str, dict] = {}
        for r in self.conn.execute(
                "SELECT source, brier FROM probabilities WHERE brier IS NOT NULL"):
            out.setdefault(r["source"], {"n": 0, "sum": 0.0})
            out[r["source"]]["n"] += 1
            out[r["source"]]["sum"] += r["brier"]
        for src, agg in out.items():
            agg["brier"] = agg["sum"] / agg["n"]
            agg["vs_coin"] = agg["brier"] - COIN_BRIER
            agg["verdict"] = ("worse than always saying 50%"
                              if agg["brier"] > COIN_BRIER else
                              "better than a coin, magnitude unknown at this n")
            del agg["sum"]
        return out

    def coherence(self) -> list[dict]:
        """Scenario sets whose weights do not sum to 1.

        Reported, never normalised: rescaling somebody's stated weights would hide
        the error and change what they claimed.
        """
        bad = []
        for r in self.conn.execute(
                "SELECT scenario_set, COUNT(*) n, SUM(probability) total "
                "  FROM probabilities WHERE scenario_set IS NOT NULL "
                " GROUP BY scenario_set"):
            total = r["total"] or 0.0
            if abs(total - 1.0) > 1e-6:
                bad.append({"scenario_set": r["scenario_set"], "n": r["n"],
                            "total": total, "off_by": total - 1.0})
        return bad


# ---------------------------------------------------------------------------
# Seeding from the Monthly.
# ---------------------------------------------------------------------------
# The shape this looks for, once section III is machine-readable:
#
#   | Scenario | Probability | ... |
#   | Soft landing | 45% | ... |
#
# A table row whose first cell is a label and whose second is a percentage. Loose
# on purpose -- the section is hand-written today and will not arrive in a schema.
_ROW = re.compile(r"^\|\s*([^|]{3,80}?)\s*\|\s*(\d{1,3}(?:\.\d+)?)\s*%\s*\|",
                  re.M)
_SECTION = re.compile(r"^##\s*III\..*?Probabilities\s*$(.*?)(?=^##\s|\Z)",
                      re.M | re.S)


def parse_monthly_scenarios(text: str) -> list[dict]:
    """Scenario weights out of a Monthly's section III, or an empty list."""
    m = _SECTION.search(text or "")
    body = m.group(1) if m else ""
    out = []
    for label, pct in _ROW.findall(body):
        label = label.strip()
        if label.lower() in ("scenario", "---", "probability"):
            continue
        out.append({"claim": label, "probability": float(pct) / 100.0})
    return out


def newest_monthly(reports_dir: Optional[str] = None) -> Optional[Path]:
    d = Path(reports_dir or (REPO / "reports"))
    if not d.is_dir():
        return None
    cands = sorted(d.glob("monthly_macro_*.md"))
    return cands[-1] if cands else None


def seed_from_monthly(db_path: Optional[str] = None, *,
                      reports_dir: Optional[str] = None,
                      horizon_days: int = 92,
                      dry_run: bool = False) -> dict:
    """Seed the ledger from the most recent Monthly's scenario weights.

    Finds nothing today, and that is the honest outcome rather than a bug: the
    Monthly's section III is a manual placeholder. Written now so the ledger fills
    itself the moment that section becomes machine-readable.

    horizon_days defaults to 92 -- the `strategic` window's near edge and the
    Monthly's own cadence to the next stance. A scenario weight with no stated
    resolution date is a forecast about nothing in particular, so a default is
    applied rather than leaving the column empty, and it is stated in the
    criterion so the reader knows it was assumed.
    """
    path = newest_monthly(reports_dir)
    if path is None:
        return {"ok": False, "reason": "no monthly_macro_*.md in reports/",
                "found": 0, "recorded": 0, "source_file": None}
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = parse_monthly_scenarios(text)
    if not rows:
        placeholder = "[Manual" in text or "*[Manual" in text
        return {
            "ok": True, "found": 0, "recorded": 0,
            "source_file": str(path),
            "reason": (
                "the Monthly emits no machine-readable scenario weights. Section "
                "III is a manual placeholder (*[Manual - scenarios and "
                "probabilities]*), and every percentage in the rendered report is "
                "a measured level -- CPI, HY OAS, unemployment -- not a weight. "
                "Nothing was invented to fill the table."
                if placeholder else
                "section III parsed but contained no `| label | NN% |` rows"),
        }

    stamp = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    emitted = (stamp.group(1) + "T00:00:00+00:00") if stamp else session.utc_iso()
    horizon = (dt.date.fromisoformat(emitted[:10])
               + dt.timedelta(days=horizon_days)).isoformat()
    set_id = f"monthly_macro:{stamp.group(1) if stamp else 'unknown'}"

    recorded = []
    if not dry_run:
        with ProbabilityLedger(db_path) as led:
            for r in rows:
                recorded.append(led.record(
                    source="monthly_macro", scenario_set=set_id,
                    claim=r["claim"], probability=r["probability"],
                    emitted_at=emitted, horizon_date=horizon,
                    emitted_by=str(path.name),
                    resolution_criterion=(
                        f"Resolved at {horizon} against the Monthly's own stated "
                        f"scenario definition. Horizon assumed as {horizon_days} "
                        f"days from emission because section III states no "
                        f"resolution date; if it later does, that date governs.")))
    return {"ok": True, "found": len(rows), "recorded": len(recorded),
            "source_file": str(path), "scenario_set": set_id,
            "emitted_at": emitted, "horizon_date": horizon, "reason": ""}


def main() -> int:
    import argparse  # noqa: PLC0415
    import sys       # noqa: PLC0415
    ap = argparse.ArgumentParser(description="The probability ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("seed-monthly", help="seed from the newest Monthly")
    sp.add_argument("--db", default=None)
    sp.add_argument("--reports-dir", default=None)
    sp.add_argument("--dry-run", action="store_true")

    rp = sub.add_parser("record", help="record one probability by hand")
    rp.add_argument("--db", default=None)
    rp.add_argument("--source", required=True)
    rp.add_argument("--claim", required=True)
    rp.add_argument("--probability", type=float, required=True,
                    help="0..1, not a percentage")
    rp.add_argument("--horizon-date", required=True)
    rp.add_argument("--resolution-criterion", required=True,
                    help="HOW this resolves. Declared now, never later.")
    rp.add_argument("--scenario-set", default=None)

    vp = sub.add_parser("resolve", help="resolve one probability")
    vp.add_argument("--db", default=None)
    vp.add_argument("--id", required=True)
    vp.add_argument("--outcome", type=int, choices=(0, 1), required=True)
    vp.add_argument("--note", default=None)

    lp = sub.add_parser("score", help="running Brier per source, and the queue")
    lp.add_argument("--db", default=None)

    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    line = "=" * 78

    if args.cmd == "seed-monthly":
        res = seed_from_monthly(args.db, reports_dir=args.reports_dir,
                                dry_run=args.dry_run)
        print(f"{line}\nProbability ledger -- seed from the Monthly\n{line}")
        print(f"  source file : {res.get('source_file')}")
        print(f"  found       : {res['found']} scenario weight(s)")
        print(f"  recorded    : {res['recorded']}")
        if res.get("reason"):
            print(f"\n  {res['reason']}")
        print(line)
        return 0

    if args.cmd == "record":
        with ProbabilityLedger(args.db) as led:
            pid = led.record(source=args.source, claim=args.claim,
                             probability=args.probability,
                             horizon_date=args.horizon_date,
                             resolution_criterion=args.resolution_criterion,
                             scenario_set=args.scenario_set,
                             emitted_by="cli")
        print(f"recorded {pid}")
        return 0

    if args.cmd == "resolve":
        with ProbabilityLedger(args.db) as led:
            out = led.resolve(args.id, args.outcome, note=args.note)
        print(f"resolved {out['probability_id']}  p={out['probability']:.3f}  "
              f"outcome={out['outcome']}  brier={out['brier']:.4f}")
        print(f"  claim: {out['claim']}")
        return 0

    with ProbabilityLedger(args.db) as led:
        rows = led.all_rows()
        scores = led.score_by_source()
        due = led.due()
        bad = led.coherence()
    print(f"{line}\nProbability ledger -- {METHOD_VERSION}\n{line}")
    print(f"  forecasts   : {len(rows)}   resolved: "
          f"{sum(1 for r in rows if r['outcome'] is not None)}")
    if not rows:
        print("\n  EMPTY. Nothing in this system emits a machine-readable")
        print("  probability yet: the Monthly's section III is a manual")
        print("  placeholder and the tail list carries none by design. Record one")
        print("  by hand with `record`, or seed once section III is structured.")
        print(line)
        return 0
    print(f"\n  RUNNING BRIER PER SOURCE  (lower is better; {COIN_BRIER} is what")
    print(f"  always saying 50% gets you)")
    for src, s in sorted(scores.items()):
        print(f"    {src:<22} n={s['n']:<4} brier {s['brier']:.4f}  "
              f"({s['vs_coin']:+.4f} vs coin)  {s['verdict']}")
    if due:
        print(f"\n  DUE FOR RESOLUTION ({len(due)})")
        for r in due[:10]:
            print(f"    {r['probability_id'][:12]}  {r['horizon_date']}  "
                  f"p={r['probability']:.2f}  {r['claim'][:52]}")
    if bad:
        print(f"\n  INCOHERENT SCENARIO SETS ({len(bad)}) -- weights must sum to 1")
        for b in bad:
            print(f"    {b['scenario_set']}  n={b['n']}  sums to {b['total']:.4f} "
                  f"({b['off_by']:+.4f})")
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

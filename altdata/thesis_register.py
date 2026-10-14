"""
The thesis register -- the papers' quarterly ritual, ledgered (AQ-6; change order
of 10 Oct 2026, section 6).

-----------------------------------------------------------------------------
WHAT A THESIS IS, AND WHERE IT LIVES
-----------------------------------------------------------------------------
Per family, each quarter, the operator writes one file,
config/alt_asset_theses/<YYYY>q<N>.yaml:

    the 12-month scenario set   the paper's scenarios with this quarter's
                                probabilities, each with a horizon date and a
                                resolution criterion; the set sums to one
    the 3-month thesis          one measurable with a probability, a falsifier
                                (also a measurable) and the Book it informs
    the book                    per horizon, the register's draft fields, or
                                `no_draft: <reason>`

Every probability goes into the probability ledger under source
`alt_asset:<family>`, scenario_set `<family>-<YYYYqN>-12m` or `-3m`, emitted_by
`operator`. The ledger is the only place a thesis's number lives: the Monthly's
seed table and the Quarterly's opener READ it, and neither writes one. The code
never writes a thesis of its own -- the seed command loads the operator's file
and nothing else, and it is the operator's to run.

-----------------------------------------------------------------------------
A CRITERION IS A MEASURABLE OR IT IS REFUSED
-----------------------------------------------------------------------------
    {series: <a registered store key>, instrument: <optional>,
     comparator: ">=" | ">" | "<=" | "<" | "between",
     level: <number, or [low, high] for between>, date: YYYY-MM-DD}

Prose is not a criterion: "gold outperforms" resolves however the reader wants it
to on the day, which is the thing the ledger exists to prevent. The loader refuses
a string, an unregistered series, an unknown comparator, a non-numeric level and a
date that is not in the future at emission. The ledger's resolution_criterion
column carries the canonical text of the measurable; the structure itself, the
file's vintage (its sha256 and written_at) and the value at emission are kept in
`alt_asset_theses`, beside the ledger's own table in the same database.

-----------------------------------------------------------------------------
RESOLUTION IS BY CODE, FROM THE STORE, AS OF
-----------------------------------------------------------------------------
When a thesis is due, its series is read through ObservationStore.as_of at the
resolution cutoff, and the last period observed on or before the horizon date is
compared with the level. It resolves only once that period is final -- a later
period is stored, or the series' grace has passed -- and only when the period is
fresh enough to stand for the date; otherwise it waits and says why. The
observation read goes into the ledger's resolution_note, so the grade replays.
The one exception is `resolve_manual`, which needs a note and is logged to
`alt_asset_manual_resolutions`; the grading views mark every manual outcome.

-----------------------------------------------------------------------------
THE DRAFT-PER-HORIZON RULE
-----------------------------------------------------------------------------
Each deep family yields a register entry per horizon -- a Book B draft for the
3-month thesis, a Book A draft for the 12-month set -- or an explicit no-draft
line with its reason. Every entry is written with status `draft`, and the writer
asserts it read back as draft: it can never create an active decision. Promoting
one stays the operator's, through decide.py. Thailand is isolated (section 4.10:
"informs the private conversion decision and nothing in the trading system"), so
its book may only say no_draft.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import re
import sqlite3
import tempfile
import uuid
from pathlib import Path
from typing import Any, Optional

from . import observations, session
from . import probability_ledger as pl

log = logging.getLogger("altdata.thesis_register")

REPO = Path(__file__).resolve().parent.parent
THESES_DIR = REPO / "config" / "alt_asset_theses"
TEMPLATE = THESES_DIR / "TEMPLATE.yaml"

SOURCE_PREFIX = "alt_asset"
# The families of the Quarterly (section 2 and 4). DEEP families owe a book entry
# per horizon; Thailand is isolated; the rest are light.
DEEP_FAMILIES = ("metals", "oil", "currency", "em", "china", "crypto")
LIGHT_FAMILIES = ("real_estate", "credit", "intl_equities", "agriculture")
ISOLATED_FAMILIES = ("thailand",)
FAMILIES = DEEP_FAMILIES + ("real_estate", "credit", "intl_equities", "thailand",
                            "agriculture")
HORIZON_KINDS = ("3m", "12m")
COMPARATORS = (">=", ">", "<=", "<", "between")
# XVII's words for a position's role in the portfolio (section 4.1 item 10).
PORTFOLIO_ROLES = ("structural", "proxy", "direct", "convex", "carry", "growth",
                   "tactical")
# The register's horizon each thesis horizon maps to (grader.HORIZON_DAYS:
# positional is three months, strategic twelve) and the Book it defaults to.
REGISTER_HORIZON = {"3m": "positional", "12m": "strategic"}
DEFAULT_BOOK = {"3m": "B", "12m": "A"}
BOOK_FIELDS = ("instrument", "direction", "thesis", "edge", "horizon", "size",
               "invalidation", "counter_thesis", "portfolio_role")
# Typo guards on the horizon, in days from emission. Loose on purpose: the first
# set is written 7-8 Nov for 1Q27, so its "3-month" thesis runs ~144 days.
MAX_DAYS = {"3m": 200, "12m": 550}
MIN_DAYS = {"3m": 1, "12m": 180}
# A seeding more than this long after the file's written_at is refused on its
# first run: a thesis written after the data it forecasts is not a forecast.
MAX_EMISSION_LAG_DAYS = 7
# How old the period read may be, and how long after the date before a period
# with no successor counts as final, by the series' frequency.
FRESH_DAYS = {"daily": 10, "weekly": 14, "monthly": 45, "quarterly": 120}
GRACE_DAYS = {"daily": 7, "weekly": 14, "monthly": 50, "quarterly": 120}
FILE_RE = re.compile(r"^(\d{4})q([1-4])\.yaml$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS alt_asset_theses (
    -- One row per ledger probability the thesis register wrote. The forecast
    -- itself is the ledger's row; this carries what the ledger has no column
    -- for: the measurable's structure, the falsifier, the file's vintage.
    probability_id   TEXT PRIMARY KEY,
    family           TEXT NOT NULL,
    quarter          TEXT NOT NULL,
    horizon_kind     TEXT NOT NULL CHECK (horizon_kind IN ('3m', '12m')),
    label            TEXT NOT NULL,
    measurable_json  TEXT NOT NULL,
    falsifier_json   TEXT,
    book             TEXT,
    statement_json   TEXT,
    value_at_emission REAL,
    emission_read_json TEXT,
    file_name        TEXT NOT NULL,
    file_sha256      TEXT NOT NULL,
    written_at       TEXT NOT NULL,
    seeded_at        TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS alt_asset_theses_immutable
BEFORE UPDATE ON alt_asset_theses
BEGIN SELECT RAISE(ABORT, 'a thesis is immutable; write a new file to revise'); END;
CREATE TRIGGER IF NOT EXISTS alt_asset_theses_no_delete
BEFORE DELETE ON alt_asset_theses
BEGIN SELECT RAISE(ABORT, 'a thesis is not deletable; it is the record'); END;

CREATE TABLE IF NOT EXISTS alt_asset_books (
    -- The draft-per-horizon rule's record: a draft's decision id, or the no
    -- draft line with its reason.
    family        TEXT NOT NULL,
    quarter       TEXT NOT NULL,
    horizon_kind  TEXT NOT NULL CHECK (horizon_kind IN ('3m', '12m')),
    kind          TEXT NOT NULL CHECK (kind IN ('draft', 'no_draft')),
    decision_id   TEXT,
    reason        TEXT,
    portfolio_role TEXT,
    cost_json     TEXT,
    file_sha256   TEXT NOT NULL,
    written_at    TEXT NOT NULL,
    seeded_at     TEXT NOT NULL,
    PRIMARY KEY (family, quarter, horizon_kind, written_at)
);
CREATE TRIGGER IF NOT EXISTS alt_asset_books_immutable
BEFORE UPDATE ON alt_asset_books
BEGIN SELECT RAISE(ABORT, 'a book line is immutable'); END;

CREATE TABLE IF NOT EXISTS alt_asset_manual_resolutions (
    -- Every outcome NOT read from the store, with the operator's note. Append
    -- only: the log is what makes a manual outcome visible.
    probability_id TEXT NOT NULL,
    outcome        INTEGER NOT NULL CHECK (outcome IN (0, 1)),
    note           TEXT NOT NULL CHECK (length(trim(note)) > 0),
    logged_at      TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS alt_asset_manual_append_only
BEFORE UPDATE ON alt_asset_manual_resolutions
BEGIN SELECT RAISE(ABORT, 'the manual log is append-only'); END;
"""


class ThesisFileError(ValueError):
    """The file is refused. Carries every reason, not the first."""

    def __init__(self, reasons: list[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


# ---------------------------------------------------------------------------
# Quarters
# ---------------------------------------------------------------------------
def quarter_label(q: str) -> str:
    """'2027q1' -> '1Q27', the form the reports print."""
    m = re.fullmatch(r"(\d{4})q([1-4])", str(q))
    return f"{m.group(2)}Q{m.group(1)[2:]}" if m else str(q)


def quarter_of(day: Any) -> str:
    d = dt.date.fromisoformat(str(day)[:10])
    return f"{d.year}q{(d.month - 1) // 3 + 1}"


def next_quarter(q: str) -> str:
    y, n = int(q[:4]), int(q[-1])
    return f"{y + 1}q1" if n == 4 else f"{y}q{n + 1}"


def previous_quarter(q: str) -> str:
    y, n = int(q[:4]), int(q[-1])
    return f"{y - 1}q4" if n == 1 else f"{y}q{n - 1}"


def source_for(family: str) -> str:
    return f"{SOURCE_PREFIX}:{family}"


def set_id(family: str, quarter: str, kind: str) -> str:
    return f"{family}-{quarter}-{kind}"


# ---------------------------------------------------------------------------
# The measurable
# ---------------------------------------------------------------------------
def _date(v: Any) -> Optional[dt.date]:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def check_measurable(m: Any, where: str, emitted: dt.date,
                     registry=None) -> tuple[Optional[dict], list[str]]:
    """(normalised measurable, reasons). A string is refused as prose."""
    if registry is None:
        from . import derived  # noqa: PLC0415
        registry = derived.registry_entry
    if isinstance(m, str) or not isinstance(m, dict):
        return None, [f"{where}: the criterion is prose, not a measurable -- "
                      f"write it as {{series, comparator, level, date}}"]
    bad = []
    series = str(m.get("series") or "").strip()
    if not series:
        bad.append(f"{where}: no series (a registered store key)")
    elif not registry(series):
        bad.append(f"{where}: series {series!r} is not a registered store key "
                   f"(metrics_registry.yaml)")
    comp = m.get("comparator")
    if comp not in COMPARATORS:
        bad.append(f"{where}: comparator {comp!r} is not one of {COMPARATORS}")
    lvl = m.get("level")
    if comp == "between":
        ok = (isinstance(lvl, (list, tuple)) and len(lvl) == 2
              and all(_num(x) is not None for x in lvl)
              and _num(lvl[0]) < _num(lvl[1]))
        if not ok:
            bad.append(f"{where}: `between` needs level [low, high], low < high")
        level = [_num(x) for x in lvl] if ok else None
    else:
        level = _num(lvl)
        if level is None:
            bad.append(f"{where}: level {lvl!r} is not a number")
    d = _date(m.get("date"))
    if d is None:
        bad.append(f"{where}: no date (YYYY-MM-DD)")
    elif d <= emitted:
        bad.append(f"{where}: date {d} is not in the future at emission "
                   f"({emitted})")
    if bad:
        return None, bad
    out = {"series": series, "comparator": comp, "level": level,
           "date": d.isoformat()}
    if m.get("instrument"):
        out["instrument"] = str(m["instrument"])
    return out, []


def _fmt(x: float) -> str:
    return f"{x:,.4f}".rstrip("0").rstrip(".")


def criterion_text(m: dict) -> str:
    """The canonical text the ledger's resolution_criterion carries."""
    s = m["series"] + (f" [{m['instrument']}]" if m.get("instrument") else "")
    if m["comparator"] == "between":
        cond = f"between {_fmt(m['level'][0])} and {_fmt(m['level'][1])}"
    else:
        cond = f"{m['comparator']} {_fmt(m['level'])}"
    return (f"measurable: {s} {cond} on {m['date']} -- the last period observed "
            f"on or before that date, read from the store as of resolution")


def holds(m: dict, value: float) -> bool:
    c, lvl = m["comparator"], m["level"]
    if c == "between":
        return lvl[0] <= value <= lvl[1]
    return {">=": value >= lvl, ">": value > lvl, "<=": value <= lvl,
            "<": value < lvl}[c]


def target(m: dict) -> float:
    """The level a measurable points at -- a range's midpoint."""
    return (sum(m["level"]) / 2.0) if m["comparator"] == "between" else m["level"]


def direction_of(m: dict, start: Optional[float]) -> Optional[int]:
    """+1 if the measurable says the series rises from its emission value, -1 if
    it falls, None where emission was not read or it sits at the level."""
    if start is None:
        return None
    t = target(m)
    return 1 if t > start else (-1 if t < start else None)


# ---------------------------------------------------------------------------
# The loader
# ---------------------------------------------------------------------------
def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _book_block(fam: str, kind: str, b: Any, where: str,
                theses: dict) -> tuple[Optional[dict], list[str]]:
    from register import store as rstore  # noqa: PLC0415
    if b is None:
        return None, [f"{where}: no book entry -- a draft or `no_draft: <reason>`"]
    if not isinstance(b, dict):
        return None, [f"{where}: the book entry is not a mapping"]
    if "no_draft" in b:
        reason = str(b.get("no_draft") or "").strip()
        if not reason:
            return None, [f"{where}: no_draft needs its reason (no edge, "
                          f"liquidity, data quality ...)"]
        return {"kind": "no_draft", "reason": reason}, []
    if fam in ISOLATED_FAMILIES:
        return None, [f"{where}: {fam} is isolated (section 4.10) -- it informs "
                      f"the private conversion decision and nothing in the "
                      f"trading system, so its book may only say no_draft"]
    bad = [f"{where}: missing {f}" for f in BOOK_FIELDS
           if not str(b.get(f) or "").strip()]
    if b.get("direction") and b["direction"] not in rstore.DIRECTIONS:
        bad.append(f"{where}: direction {b['direction']!r} is not one of "
                   f"{rstore.DIRECTIONS}")
    if b.get("horizon") and b["horizon"] not in rstore.HORIZONS:
        bad.append(f"{where}: horizon {b['horizon']!r} is not one of "
                   f"{rstore.HORIZONS}")
    if b.get("portfolio_role") and b["portfolio_role"] not in PORTFOLIO_ROLES:
        bad.append(f"{where}: portfolio_role {b['portfolio_role']!r} is not "
                   f"XVII's ({', '.join(PORTFOLIO_ROLES)})")
    book = b.get("book") or (theses.get("book") if kind == "3m" else None) \
        or DEFAULT_BOOK[kind]
    if book not in rstore.BOOKS:
        bad.append(f"{where}: book {book!r} is not one of {rstore.BOOKS}")
    if b.get("quantity") is not None and _num(b.get("quantity")) is None:
        bad.append(f"{where}: quantity is not a number")
    if bad:
        return None, bad
    out = {k: (str(b[k]).strip() if isinstance(b[k], str) else b[k])
           for k in b if b[k] is not None}
    out.update({"kind": "draft", "book": book})
    fal = b.get("falsifiers")
    out["falsifiers"] = ([str(x) for x in fal] if isinstance(fal, list)
                         else [str(fal)] if fal else [])
    return out, []


def load(path: Any, *, now: Optional[str] = None, registry=None,
         allow_example: bool = False) -> dict:
    """Validate a thesis file. Returns the normalised plan or raises
    ThesisFileError with every reason. Writes nothing."""
    import yaml  # noqa: PLC0415
    p = Path(path)
    reasons: list[str] = []
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception as exc:                                    # noqa: BLE001
        raise ThesisFileError([f"{p.name}: not readable YAML ({exc})"])
    example = bool(doc.get("example"))
    if example and not allow_example:
        raise ThesisFileError([f"{p.name}: is marked `example: true` -- an "
                               f"example is never seeded as a real thesis"])
    quarter = str(doc.get("quarter") or "")
    if not re.fullmatch(r"\d{4}q[1-4]", quarter):
        reasons.append(f"quarter {quarter!r} is not YYYYqN")
    fm = FILE_RE.match(p.name)
    if not example and (not fm or f"{fm.group(1)}q{fm.group(2)}" != quarter):
        reasons.append(f"the file name {p.name!r} must be <YYYY>q<N>.yaml and "
                       f"match its quarter {quarter!r}")
    w = doc.get("written_at")
    written = None
    try:
        written = dt.datetime.fromisoformat(str(w).replace("Z", "+00:00"))
        if written.tzinfo is None:
            raise ValueError("no offset")
        written = written.astimezone(dt.timezone.utc)
    except (TypeError, ValueError):
        reasons.append(f"written_at {w!r} is not an ISO instant with an offset "
                       f"(the emission instant every row carries)")
    now_dt = dt.datetime.fromisoformat(
        (now or session.utc_iso()).replace("Z", "+00:00"))
    if written is not None and written > now_dt:
        reasons.append(f"written_at {written.isoformat()} is in the future -- a "
                       f"forecast cannot be emitted later than it is seeded")
    if reasons:
        raise ThesisFileError(reasons)
    emitted = written.date()
    fams = doc.get("families") or {}
    if not isinstance(fams, dict):
        raise ThesisFileError(["families is not a mapping"])
    for f in fams:
        if f not in FAMILIES:
            reasons.append(f"family {f!r} is not one of {FAMILIES}")
    if not example:
        for f in DEEP_FAMILIES:
            if f not in fams:
                reasons.append(f"deep family {f} has no block -- its theses and "
                               f"its book are owed every quarter")
    plan = {"quarter": quarter, "file": str(p), "file_name": p.name,
            "file_sha256": _sha(p), "written_at": written.isoformat(),
            "example": example, "families": {}, "skipped": {}}
    for fam, blk in fams.items():
        if fam not in FAMILIES:
            continue
        blk = blk or {}
        if "not_this_quarter" in blk:
            why = str(blk.get("not_this_quarter") or "").strip()
            if fam in DEEP_FAMILIES:
                reasons.append(f"{fam}: a deep family cannot sit out a quarter "
                               f"(not_this_quarter) -- write its theses, or a "
                               f"no_draft book with the reason")
            elif not why:
                reasons.append(f"{fam}: not_this_quarter needs its reason")
            else:
                plan["skipped"][fam] = why
            continue
        fp = {"scenarios": [], "thesis": None, "book": {}}
        # -- the 12-month scenario set ------------------------------------
        scen = blk.get("scenarios_12m") or []
        if not isinstance(scen, list) or len(scen) < 2:
            reasons.append(f"{fam}: scenarios_12m needs at least two scenarios")
            scen = scen if isinstance(scen, list) else []
        total = 0.0
        names = set()
        for i, s in enumerate(scen):
            where = f"{fam}.scenarios_12m[{i}]"
            s = s or {}
            name = str(s.get("name") or "").strip()
            if not name:
                reasons.append(f"{where}: no name")
            elif name in names:
                reasons.append(f"{where}: name {name!r} repeats")
            names.add(name)
            pr = _num(s.get("probability"))
            if pr is None or not 0.0 < pr < 1.0:
                reasons.append(f"{where}: probability {s.get('probability')!r} "
                               f"is not in (0, 1)")
                pr = None
            else:
                total += pr
            crit = s.get("criterion")
            hz = _date(s.get("horizon"))
            if hz is None:
                reasons.append(f"{where}: no horizon date")
            if isinstance(crit, dict) and hz and "date" not in crit:
                crit = {**crit, "date": hz.isoformat()}
            m, bad = check_measurable(crit, where, emitted, registry)
            reasons += bad
            if m and hz and m["date"] != hz.isoformat():
                reasons.append(f"{where}: horizon {hz} and the criterion's date "
                               f"{m['date']} differ")
            if m:
                days = (_date(m["date"]) - emitted).days
                if not MIN_DAYS["12m"] <= days <= MAX_DAYS["12m"]:
                    reasons.append(f"{where}: {days} days from emission is not a "
                                   f"12-month horizon ({MIN_DAYS['12m']} to "
                                   f"{MAX_DAYS['12m']})")
            if name and pr is not None and m:
                fp["scenarios"].append({"name": name, "probability": pr,
                                        "measurable": m})
        if scen and abs(total - 1.0) > 1e-6:
            reasons.append(f"{fam}: the 12-month weights sum to {total:.4f}, not "
                           f"one -- reported, never normalised")
        # -- the 3-month thesis --------------------------------------------
        t = blk.get("thesis_3m")
        from register import store as rstore  # noqa: PLC0415
        if not isinstance(t, dict):
            reasons.append(f"{fam}: no thesis_3m")
            t = {}
        else:
            where = f"{fam}.thesis_3m"
            claim = str(t.get("claim") or "").strip()
            if not claim:
                reasons.append(f"{where}: no claim")
            pr = _num(t.get("probability"))
            if pr is None or not 0.0 < pr < 1.0:
                reasons.append(f"{where}: probability {t.get('probability')!r} "
                               f"is not in (0, 1)")
            m, bad = check_measurable(t.get("criterion"), where, emitted, registry)
            reasons += bad
            if m:
                days = (_date(m["date"]) - emitted).days
                if not MIN_DAYS["3m"] <= days <= MAX_DAYS["3m"]:
                    reasons.append(f"{where}: {days} days from emission is not a "
                                   f"3-month horizon (up to {MAX_DAYS['3m']})")
            if not t.get("falsifier"):
                reasons.append(f"{where}: no falsifier -- a thesis states what "
                               f"would show it wrong, as a measurable")
                fm_ = None
            else:
                fm_, bad = check_measurable(t.get("falsifier"),
                                            f"{where}.falsifier", emitted,
                                            registry)
                reasons += bad
                if fm_ and m and fm_["date"] > m["date"]:
                    reasons.append(f"{where}.falsifier: its date {fm_['date']} "
                                   f"is after the thesis's {m['date']}")
            book = t.get("book")
            if book not in rstore.BOOKS:
                reasons.append(f"{where}: book {book!r} -- the Book it informs, "
                               f"one of {rstore.BOOKS}")
            stmt = {k: str(t[k]).strip() for k in (
                "market_expectation", "chester_read", "difference", "evidence",
                "what_changes_the_view") if t.get(k)}
            if claim and pr is not None and 0 < pr < 1 and m and fm_ \
                    and book in rstore.BOOKS:
                fp["thesis"] = {"claim": claim, "probability": pr,
                                "measurable": m, "falsifier": fm_, "book": book,
                                "statement": stmt}
        # -- the book, per horizon -----------------------------------------
        bk = blk.get("book") or {}
        for kind in HORIZON_KINDS:
            entry = bk.get(kind) if isinstance(bk, dict) else None
            if entry is None and fam not in DEEP_FAMILIES \
                    and fam not in ISOLATED_FAMILIES:
                continue                     # a light family's book is optional
            if entry is None and fam in ISOLATED_FAMILIES:
                continue
            b, bad = _book_block(fam, kind, entry, f"{fam}.book.{kind}", t)
            reasons += bad
            if b:
                fp["book"][kind] = b
        plan["families"][fam] = fp
    if reasons:
        raise ThesisFileError(reasons)
    return plan


def draft_rule_faults(plan: dict) -> list[str]:
    """The gate's rule: a deep family with neither a draft nor a no_draft, per
    horizon, fails."""
    out = []
    for fam in DEEP_FAMILIES:
        fp = (plan.get("families") or {}).get(fam)
        if fp is None:
            if not plan.get("example"):
                out.append(f"{fam}: no block")
            continue
        for kind in HORIZON_KINDS:
            b = (fp.get("book") or {}).get(kind)
            if not b or b.get("kind") not in ("draft", "no_draft"):
                out.append(f"{fam} {kind}: neither a draft nor a no_draft")
    return out


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _connect(db_path: Optional[str]) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or observations.DEFAULT_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    ensure_schema(conn)
    return conn


def _freq(series: str) -> str:
    from . import derived  # noqa: PLC0415
    f = str((derived.registry_entry(series) or {}).get("freq") or "daily").lower()
    for k in FRESH_DAYS:
        if f.startswith(k[:5]) or f == k[0]:
            return k
    return "daily"


def read_at(store, m: dict, cutoff: str, day: Optional[str] = None) -> dict:
    """The last period observed on or before `day` (default the measurable's
    date), knowable at `cutoff`. Says whether it is final and fresh enough."""
    day = day or m["date"]
    rows = store.as_of(m["series"], cutoff, m.get("instrument"))
    before = [r for r in rows if str(r["observed_at"])[:10] <= day
              and r.get("value_num") is not None]
    after = [r for r in rows if str(r["observed_at"])[:10] > day]
    freq = _freq(m["series"])
    if not before:
        return {"ok": False, "why": f"no observation of {m['series']} on or "
                                    f"before {day} is knowable at {cutoff[:10]}"}
    r = before[-1]
    age = (_date(day) - _date(r["observed_at"])).days
    if age > FRESH_DAYS[freq]:
        return {"ok": False, "why": f"the last {m['series']} period on or before "
                                    f"{day} is {r['observed_at'][:10]}, {age} days "
                                    f"old -- too old to stand for the date "
                                    f"({freq}: {FRESH_DAYS[freq]})"}
    grace = (_date(cutoff) - _date(day)).days >= GRACE_DAYS[freq]
    if not after and not grace:
        return {"ok": False, "why": f"{r['observed_at'][:10]} is not yet final -- "
                                    f"no later period is stored and the {freq} "
                                    f"grace ({GRACE_DAYS[freq]} days) has not "
                                    f"passed"}
    return {"ok": True, "value": float(r["value_num"]),
            "observed_at": str(r["observed_at"]),
            "available_at": str(r.get("available_at")), "cutoff": cutoff,
            "series": m["series"], "instrument": m.get("instrument")}


def emission_read(store, m: dict, written_at: str) -> dict:
    """The series' value knowable at emission -- the base a direction is judged
    from. Read once at seeding and stored; never re-read."""
    if store is None:
        return {"ok": False, "why": "no store given"}
    rows = store.as_of(m["series"], written_at, m.get("instrument"))
    rows = [r for r in rows if r.get("value_num") is not None]
    if not rows:
        return {"ok": False, "why": f"no {m['series']} observation knowable at "
                                    f"{written_at}"}
    r = rows[-1]
    return {"ok": True, "value": float(r["value_num"]),
            "observed_at": str(r["observed_at"]),
            "available_at": str(r.get("available_at"))}


# ---------------------------------------------------------------------------
# The seed
# ---------------------------------------------------------------------------
def _forecasts(plan: dict) -> list[dict]:
    """Every probability the file states, in ledger form."""
    out = []
    q = plan["quarter"]
    for fam, fp in sorted(plan["families"].items()):
        for s in fp["scenarios"]:
            out.append({"family": fam, "kind": "12m", "label": s["name"],
                        "claim": f"{fam} 12m ({quarter_label(q)}): {s['name']}",
                        "probability": s["probability"],
                        "measurable": s["measurable"], "falsifier": None,
                        "book": None, "statement": {}})
        t = fp.get("thesis")
        if t:
            # A 3-month thesis is a one-row set: it sums to its own probability,
            # which is not one, so it carries no scenario_set and coherence()
            # does not read it as an incoherent set. Its set id is kept in the
            # side table's horizon_kind and quarter.
            out.append({"family": fam, "kind": "3m", "label": t["claim"],
                        "claim": f"{fam} 3m ({quarter_label(q)}): {t['claim']}",
                        "probability": t["probability"],
                        "measurable": t["measurable"],
                        "falsifier": t["falsifier"], "book": t["book"],
                        "statement": t["statement"]})
    return out


def _read_conn(db_path: Optional[str]) -> Optional[sqlite3.Connection]:
    """A read-only connection for the dry run, or None where no database is."""
    p = Path(db_path or observations.DEFAULT_DB)
    if not p.exists():
        return None
    conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _open_store(store_path: Optional[str], dry_run: bool):
    """The observation store, for the emission reads. A dry run never creates
    one where none exists."""
    p = Path(store_path or observations.DEFAULT_DB)
    if dry_run and not p.exists():
        return None
    return observations.ObservationStore(str(p))


def seed(path: Any, db_path: Optional[str] = None, *, dry_run: bool = False,
         now: Optional[str] = None, store_path: Optional[str] = None,
         register_db: Optional[str] = None, registry=None,
         allow_example: bool = False, cost_fn=None) -> dict:
    """Load, validate and record a thesis file. Idempotent: a re-run of the same
    file writes nothing. Refused, with every reason: a changed forecast under the
    same written_at (a forecast is immutable), a second file for a quarter
    already seeded (the set would no longer sum to one), and a first seeding more
    than MAX_EMISSION_LAG_DAYS after written_at. The dry run reads the ledger
    and the store and writes neither."""
    now = now or session.utc_iso()
    plan = load(path, now=now, registry=registry, allow_example=allow_example)
    faults = draft_rule_faults(plan)
    if faults:
        raise ThesisFileError([f"draft-per-horizon: {f}" for f in faults])
    if plan["example"] and not dry_run:
        raise ThesisFileError(["an example file is validated with --dry-run only"])
    fc = _forecasts(plan)
    written = plan["written_at"]
    store = _open_store(store_path, dry_run)
    conn = _read_conn(db_path) if dry_run else _connect(db_path)
    try:
        existing, side = {}, {}
        if conn is not None and _has_table(conn, "probabilities"):
            existing = {r["probability_id"]: dict(r) for r in conn.execute(
                "SELECT * FROM probabilities WHERE source LIKE ?",
                (f"{SOURCE_PREFIX}:%",))}
        if conn is not None and _has_table(conn, "alt_asset_theses"):
            side = {r["probability_id"]: dict(r) for r in conn.execute(
                "SELECT * FROM alt_asset_theses WHERE quarter = ?",
                (plan["quarter"],))}
        reasons = []
        # ONE FILE PER QUARTER. A second written_at for a quarter already seeded
        # would put two sets under one scenario_set id and the weights would sum
        # to two; a revision is the next quarter's file.
        other = sorted({s["written_at"] for s in side.values()
                        if s["written_at"] != written
                        and s["family"] in plan["families"]})
        if other:
            reasons.append(f"{quarter_label(plan['quarter'])} is already seeded "
                           f"from a file written at {other[0]}; a forecast is "
                           f"immutable and a quarter has one set -- revise in "
                           f"the next quarter's file")
        pids = [pl.probability_id(source_for(f["family"]), f["claim"], written)
                for f in fc]
        first = not any(p in existing for p in pids)
        lag = (dt.datetime.fromisoformat(now.replace("Z", "+00:00"))
               - dt.datetime.fromisoformat(written)).days
        if first and lag > MAX_EMISSION_LAG_DAYS:
            reasons.append(
                f"written_at {written} is {lag} days before this seeding; a "
                f"first seeding must follow the writing within "
                f"{MAX_EMISSION_LAG_DAYS} days, or the forecast is written after "
                f"the data it forecasts")
        rows = []
        for f, pid in zip(fc, pids):
            crit = criterion_text(f["measurable"])
            old = existing.get(pid)
            if old and (abs(old["probability"] - f["probability"]) > 1e-12
                        or old["resolution_criterion"] != crit
                        or old["horizon_date"] != f["measurable"]["date"]):
                reasons.append(f"{f['claim']}: the ledger already holds this "
                               f"forecast at p={old['probability']} with "
                               f"{old['resolution_criterion']!r} -- a forecast "
                               f"is immutable; revise with a new file")
            rows.append({**f, "probability_id": pid,
                         "source": source_for(f["family"]),
                         "scenario_set": set_id(f["family"], plan["quarter"],
                                                f["kind"]),
                         "criterion": crit, "new": old is None,
                         "emission": emission_read(store, f["measurable"],
                                                   written)})
        # Forecasts the ledger holds for this file that the file no longer
        # states: an edited claim reads as a new forecast beside the old one.
        gone = [s["label"] for p, s in side.items()
                if s["written_at"] == written and p not in pids]
        if gone:
            reasons.append(f"the ledger holds {len(gone)} forecast(s) from this "
                           f"written_at that the file no longer states "
                           f"({'; '.join(gone[:3])}) -- a forecast is immutable")
        if reasons:
            raise ThesisFileError(reasons)
        drafts = plan_drafts(plan, store=store, cost_fn=cost_fn)
        refused = check_drafts(drafts, plan)["refused"]
        if refused:
            raise ThesisFileError(refused)
        result = {"ok": True, "dry_run": dry_run, "quarter": plan["quarter"],
                  "file": plan["file_name"], "file_sha256": plan["file_sha256"],
                  "written_at": written, "forecasts": len(rows),
                  "new": sum(1 for r in rows if r["new"]),
                  "families": sorted(plan["families"]),
                  "skipped": plan["skipped"], "rows": rows,
                  "drafts": drafts, "recorded": 0, "drafts_written": 0}
        if dry_run:
            return result
        with pl.ProbabilityLedger(db_path) as led:
            for r in rows:
                if not r["new"]:
                    continue
                led.record(source=r["source"], claim=r["claim"],
                           probability=r["probability"],
                           horizon_date=r["measurable"]["date"],
                           resolution_criterion=r["criterion"],
                           scenario_set=r["scenario_set"], emitted_at=written,
                           emitted_by="operator")
                result["recorded"] += 1
        for r in rows:
            em = r["emission"]
            conn.execute(
                "INSERT OR IGNORE INTO alt_asset_theses (probability_id,"
                " family, quarter, horizon_kind, label, measurable_json,"
                " falsifier_json, book, statement_json, value_at_emission,"
                " emission_read_json, file_name, file_sha256, written_at,"
                " seeded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r["probability_id"], r["family"], plan["quarter"], r["kind"],
                 r["label"], json.dumps(r["measurable"], sort_keys=True),
                 (json.dumps(r["falsifier"], sort_keys=True)
                  if r["falsifier"] else None), r["book"],
                 json.dumps(r["statement"], sort_keys=True),
                 em.get("value") if em.get("ok") else None,
                 json.dumps(em, sort_keys=True), plan["file_name"],
                 plan["file_sha256"], written, now))
        conn.commit()
        result["drafts_written"] = write_drafts(drafts, plan, conn,
                                                register_db=register_db, now=now)
        return result
    finally:
        if store is not None:
            store.close()
        if conn is not None:
            conn.close()


def _has_table(conn, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                        "name=?", (name,)).fetchone() is not None


# ---------------------------------------------------------------------------
# The draft-per-horizon rule
# ---------------------------------------------------------------------------
COST_GAPS = {
    "spread": "not priced: the costs writer prices commission and margin "
              "from the rate card, never the spread",
    "roll": "not priced by the costs writer (schedule_v1)",
    "borrow": "not priced by the costs writer (schedule_v1)",
    "fx_hedge": "not priced by the costs writer (schedule_v1)",
}


def cost_row(b: dict, store=None, written_at: Optional[str] = None) -> dict:
    """The instrument's cost row from the IBKR costs writer's rate card. Never
    contacts a broker: no baseline, so the margin fields stay None, which is the
    writer's honest shape for "we know the rate card but not the account". The
    components the writer does not price are named rather than left out."""
    from .sources import ibkr_costs  # noqa: PLC0415
    qty = _num(b.get("quantity"))
    price, price_src = None, "none"
    if b.get("price_series") and store is not None and written_at:
        em = emission_read(store, {"series": b["price_series"]}, written_at)
        if em.get("ok"):
            price, price_src = em["value"], f"store {b['price_series']} " \
                                            f"{em['observed_at'][:10]}"
    row = {"instrument": b["instrument"], **COST_GAPS}
    if qty is None:
        row.update({"available": False, "commission": None,
                    "reason": "no quantity on the draft -- the rate card prices "
                              "an order, and the draft names a size in words"})
        return row
    try:
        est = ibkr_costs.estimate(b["instrument"], b["direction"], qty, price,
                                  sec_type=str(b.get("sec_type") or "STK"),
                                  price_source=price_src)
    except Exception as exc:                                    # noqa: BLE001
        row.update({"available": False, "commission": None,
                    "reason": f"the costs writer refused: {exc}"})
        return row
    row.update({"available": True, "cost_source": est["cost_source"],
                "method_version": est["method_version"],
                "commission": est["commission"]["estimate"],
                "commission_card": est["commission"]["rate_card"],
                "notional": est["notional"], "price": price,
                "price_source": price_src, "quantity": qty,
                "is_floor_not_all_in": est["is_floor_not_all_in"],
                "schedule_verified": est["schedule"]["verified"]})
    return row


def draft_id(family: str, quarter: str, kind: str, written_at: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL,
                          f"chester:alt_asset:{family}:{quarter}:{kind}:"
                          f"{written_at}"))


def plan_drafts(plan: dict, store=None, cost_fn=None) -> list[dict]:
    """Every book line the file states, as the register will receive it."""
    out = []
    q, written = plan["quarter"], plan["written_at"]
    cost_fn = cost_fn or cost_row
    for fam, fp in sorted(plan["families"].items()):
        t = fp.get("thesis") or {}
        for kind in HORIZON_KINDS:
            b = (fp.get("book") or {}).get(kind)
            if not b:
                continue
            line = {"family": fam, "quarter": q, "horizon_kind": kind,
                    "kind": b["kind"]}
            if b["kind"] == "no_draft":
                line["reason"] = b["reason"]
                out.append(line)
                continue
            fals = list(b.get("falsifiers") or [])
            if kind == "3m" and t.get("falsifier"):
                fals.append(criterion_text(t["falsifier"]))
            dates = ([t["measurable"]["date"]] if kind == "3m" and t else
                     [s["measurable"]["date"] for s in fp["scenarios"]])
            tag = " [counter-structural]" if b.get("counter_structural") else ""
            line.update({
                "decision_id": draft_id(fam, q, kind, written),
                "instrument": b["instrument"], "direction": b["direction"],
                "thesis": b["thesis"], "edge_type": b["edge"],
                "horizon": b["horizon"], "size": str(b["size"]),
                "invalidation": b["invalidation"],
                "counter_thesis": b["counter_thesis"],
                "portfolio_role": b["portfolio_role"], "book": b["book"],
                "falsifiers": fals,
                "time_stop": max(dates) if dates else None,
                "currency_exposure": b.get("currency_exposure"),
                "expression_currency": b.get("expression_currency", "USD"),
                "counter_structural": bool(b.get("counter_structural")),
                "note": (f"alt_asset {fam} {quarter_label(q)} {kind} draft; "
                         f"portfolio role: {b['portfolio_role']}{tag}; from "
                         f"{plan['file_name']} sha256 "
                         f"{plan['file_sha256'][:12]}"),
                "cost": cost_fn(b, store, written)})
            out.append(line)
    return out


def _record_draft(reg, d: dict, written: str) -> str:
    return reg.record(
        instrument=d["instrument"], direction=d["direction"], thesis=d["thesis"],
        edge_type=d["edge_type"], horizon=d["horizon"],
        invalidation=d["invalidation"], size=d["size"],
        status="draft",                     # NEVER anything else
        decision_time=written, decision_id=d["decision_id"],
        currency_exposure=d["currency_exposure"], note=d["note"],
        book=d["book"], time_stop=d["time_stop"], engine_id="operator",
        falsifiers=d["falsifiers"], counter_thesis=d["counter_thesis"],
        expression_currency=d["expression_currency"], becoming_active=False)


def check_drafts(drafts: list[dict], plan: dict,
                 register_db: Optional[str] = None) -> dict:
    """Run every draft through the register's own write path against a
    throwaway register, so the Brookfield refusal, the currency guard and the
    vocabularies speak at the dry run rather than at the seed."""
    from register import store as rstore  # noqa: PLC0415
    refused = []
    with tempfile.TemporaryDirectory() as td:
        with rstore.Register(str(Path(td) / "check.db")) as reg:
            for d in drafts:
                if d["kind"] != "draft":
                    continue
                try:
                    _record_draft(reg, d, plan["written_at"])
                except Exception as exc:                        # noqa: BLE001
                    refused.append(f"{d['family']} {d['horizon_kind']} draft "
                                   f"({d['instrument']}): the register refuses "
                                   f"it -- {type(exc).__name__}: {exc}")
    return {"refused": refused}


def write_drafts(drafts: list[dict], plan: dict, conn: sqlite3.Connection,
                 register_db: Optional[str] = None,
                 now: Optional[str] = None) -> int:
    """Write the draft-status register entries and the book lines. Idempotent by
    decision id. Asserts every entry reads back as draft."""
    from register import manifest, store as rstore  # noqa: PLC0415
    n = 0
    written = plan["written_at"]
    now = now or session.utc_iso()
    with rstore.Register(register_db) as reg:
        for d in drafts:
            done = conn.execute(
                "SELECT 1 FROM alt_asset_books WHERE family=? AND quarter=? AND "
                "horizon_kind=? AND written_at=?",
                (d["family"], d["quarter"], d["horizon_kind"], written)).fetchone()
            if done:
                continue
            did = None
            if d["kind"] == "draft":
                if reg.get(d["decision_id"]) is None:
                    did = _record_draft(reg, d, written)
                    row = reg.get(did) or {}
                    if row.get("status") != "draft":
                        raise RuntimeError(
                            f"the thesis register wrote {did} as "
                            f"{row.get('status')!r}; it may only write drafts")
                    pkt = manifest.build_packet(
                        f"alt_asset-{plan['quarter']}-{d['family']}-"
                        f"{d['horizon_kind']}", written, written,
                        [Path(plan["file"])],
                        {"decision": {k: d[k] for k in (
                            "family", "quarter", "horizon_kind", "instrument",
                            "direction", "thesis", "edge_type", "horizon",
                            "invalidation", "counter_thesis", "portfolio_role",
                            "book", "falsifiers", "time_stop")}})
                    pkt["expected_cost"] = d["cost"]
                    reg.attach_packet(did, pkt)
                    n += 1
                else:
                    did = d["decision_id"]
            conn.execute(
                "INSERT INTO alt_asset_books (family, quarter, horizon_kind, kind,"
                " decision_id, reason, portfolio_role, cost_json, file_sha256,"
                " written_at, seeded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (d["family"], d["quarter"], d["horizon_kind"], d["kind"], did,
                 d.get("reason"), d.get("portfolio_role"),
                 json.dumps(d.get("cost"), sort_keys=True, default=str)
                 if d.get("cost") else None, plan["file_sha256"], written, now))
            conn.commit()
    return n


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------
def theses(db_path: Optional[str] = None, conn=None) -> list[dict]:
    """Every alt_asset thesis with its ledger row, joined."""
    # READ ONLY: the Monthly and the Quarterly read through here, and neither
    # writes to the ledger -- not even the side table's schema.
    own = conn is None
    conn = conn or _read_conn(db_path)
    if conn is None:
        return []
    try:
        if not (_has_table(conn, "probabilities")
                and _has_table(conn, "alt_asset_theses")):
            return []
        rows = [dict(r) for r in conn.execute(
            "SELECT p.*, t.family, t.quarter, t.horizon_kind, t.label,"
            "       t.measurable_json, t.falsifier_json, t.book,"
            "       t.value_at_emission, t.file_sha256, t.written_at,"
            "       (SELECT COUNT(*) FROM alt_asset_manual_resolutions m"
            "         WHERE m.probability_id = p.probability_id) AS manual"
            "  FROM probabilities p JOIN alt_asset_theses t"
            "    ON t.probability_id = p.probability_id"
            " WHERE p.source LIKE ? ORDER BY t.family, t.quarter,"
            "       t.horizon_kind, p.probability DESC",
            (f"{SOURCE_PREFIX}:%",))]
    finally:
        if own:
            conn.close()
    for r in rows:
        r["measurable"] = json.loads(r.pop("measurable_json"))
        fj = r.pop("falsifier_json")
        r["falsifier"] = json.loads(fj) if fj else None
    return rows


def resolve_due(db_path: Optional[str] = None, *, store_path: Optional[str] = None,
                now: Optional[str] = None, dry_run: bool = False) -> dict:
    """Resolve every due alt_asset thesis from the store, as of `now`."""
    now = now or session.utc_iso()
    out = {"resolved": [], "waiting": []}
    rows = [r for r in theses(db_path) if r["outcome"] is None
            and r["horizon_date"] <= now[:10]]
    if not rows:
        return out
    with observations.ObservationStore(store_path) as store:
        reads = [(r, read_at(store, r["measurable"], now)) for r in rows]
    with pl.ProbabilityLedger(db_path) as led:
        for r, rd in reads:
            if not rd["ok"]:
                out["waiting"].append({"probability_id": r["probability_id"],
                                       "claim": r["claim"], "why": rd["why"]})
                continue
            oc = 1 if holds(r["measurable"], rd["value"]) else 0
            note = json.dumps({"method": "store_as_of", **rd,
                               "comparator": r["measurable"]["comparator"],
                               "level": r["measurable"]["level"]},
                              sort_keys=True)
            if not dry_run:
                led.resolve(r["probability_id"], oc, note=note, resolved_at=now)
            out["resolved"].append({"probability_id": r["probability_id"],
                                    "claim": r["claim"], "outcome": oc,
                                    "value": rd["value"],
                                    "observed_at": rd["observed_at"]})
    return out


def resolve_manual(probability_id: str, outcome: int, note: str,
                   db_path: Optional[str] = None,
                   now: Optional[str] = None) -> dict:
    """The declared manual path: a note is required and the outcome is logged.
    For a thesis the store cannot resolve (a series retired, a period never
    published) -- never a shortcut past the store."""
    if not str(note or "").strip():
        raise ValueError("a manual resolution needs its note -- why the store "
                         "could not resolve it, and where the outcome came from")
    now = now or session.utc_iso()
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT * FROM alt_asset_theses WHERE probability_id"
                           " = ?", (probability_id,)).fetchone()
        if row is None:
            raise KeyError(f"{probability_id!r} is not an alt_asset thesis")
        done = conn.execute("SELECT outcome FROM probabilities WHERE "
                            "probability_id = ?", (probability_id,)).fetchone()
        if done is not None and done["outcome"] is not None:
            raise ValueError(f"{probability_id} is already resolved")
        conn.execute("INSERT INTO alt_asset_manual_resolutions (probability_id,"
                     " outcome, note, logged_at) VALUES (?,?,?,?)",
                     (probability_id, int(outcome), note.strip(), now))
        conn.commit()
    finally:
        conn.close()
    log.warning("MANUAL resolution of %s -> %s: %s", probability_id, outcome, note)
    with pl.ProbabilityLedger(db_path) as led:
        return led.resolve(probability_id, int(outcome),
                           note=f"MANUAL: {note.strip()}", resolved_at=now)


# ---------------------------------------------------------------------------
# Grading views
# ---------------------------------------------------------------------------
def _resolved_value(r: dict) -> Optional[float]:
    try:
        return float(json.loads(r.get("resolution_note") or "{}").get("value"))
    except (TypeError, ValueError, AttributeError):
        return None


def _inst(x: Any) -> str:
    """An instant as canonical UTC ISO, so string comparisons hold whether a
    caller wrote Z or +00:00."""
    d = dt.datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc).isoformat()


def thesis_grade(r: dict, now: Optional[str] = None) -> str:
    """hit / miss / not yet due / due, unresolved / no call (at p = 0.5)."""
    now = now or session.utc_iso()
    if r.get("outcome") is None:
        return "not yet due" if r["horizon_date"] > now[:10] \
            else "due, unresolved"
    p = r["probability"]
    if abs(p - 0.5) < 1e-12:
        return "no call"
    return "hit" if (p > 0.5) == bool(r["outcome"]) else "miss"


def direction_right(r: dict) -> Optional[bool]:
    d = direction_of(r["measurable"], r.get("value_at_emission"))
    v = _resolved_value(r)
    if d is None or v is None or r.get("value_at_emission") is None:
        return None
    moved = v - r["value_at_emission"]
    return None if moved == 0 else (moved > 0) == (d > 0)


def grade_set(rows: list[dict], now: Optional[str] = None) -> dict:
    """A 12-month scenario set: Brier per scenario, and the ordering-and-
    direction score -- did the highest-weighted scenario occur, was the
    measurable's direction right."""
    now = now or session.utc_iso()
    top = max(rows, key=lambda r: r["probability"])
    resolved = [r for r in rows if r.get("outcome") is not None]
    occurred = [r for r in resolved if r["outcome"] == 1]
    out = {"n": len(rows), "resolved": len(resolved),
           "top": top["label"], "top_probability": top["probability"],
           "briers": [r["brier"] for r in resolved],
           "mean_brier": (sum(r["brier"] for r in resolved) / len(resolved)
                          if resolved else None),
           "occurred": [r["label"] for r in occurred],
           "manual": sum(1 for r in rows if r.get("manual"))}
    if len(resolved) < len(rows):
        out["grade"] = ("not yet due" if min(r["horizon_date"] for r in rows)
                        > now[:10] else "due, unresolved")
        out["ordering"] = None
        out["direction_right"] = None
        return out
    out["ordering"] = top["outcome"] == 1
    # The rank (1 = the highest weight) of the scenario that occurred.
    ranked = sorted(rows, key=lambda r: -r["probability"])
    out["occurred_rank"] = [i + 1 for i, r in enumerate(ranked) if r["outcome"]]
    out["exclusive"] = len(occurred) == 1
    out["direction_right"] = direction_right(top)
    out["grade"] = "hit" if out["ordering"] else "miss"
    return out


def grades(db_path: Optional[str] = None, *, now: Optional[str] = None,
           family: Optional[str] = None, conn=None) -> list[dict]:
    """Per family, quarter and horizon: the grade, the Brier against the coin's
    0.25, and the ordering-and-direction score for a set."""
    now = _inst(now or session.utc_iso())
    by: dict[tuple, list] = {}
    for r in theses(db_path, conn=conn):
        if family and r["family"] != family:
            continue
        if _inst(r["emitted_at"]) > now:
            continue
        by.setdefault((r["family"], r["quarter"], r["horizon_kind"]), []).append(r)
    out = []
    for (fam, q, kind), rows in sorted(by.items()):
        if kind == "12m":
            g = grade_set(rows, now)
        else:
            r = rows[0]
            g = {"n": 1, "resolved": int(r.get("outcome") is not None),
                 "top": r["label"], "top_probability": r["probability"],
                 "mean_brier": r.get("brier"), "grade": thesis_grade(r, now),
                 "direction_right": direction_right(r),
                 "manual": int(bool(r.get("manual")))}
        g.update({"family": fam, "quarter": q, "horizon_kind": kind,
                  "rows": rows, "coin": pl.COIN_BRIER,
                  "vs_coin": (g["mean_brier"] - pl.COIN_BRIER
                              if g.get("mean_brier") is not None else None)})
        g["why"] = why_line(g)
        out.append(g)
    return out


def why_line(g: dict) -> str:
    """One line of why, written by code from the resolution it read."""
    rows = g["rows"]
    if g["grade"] in ("not yet due", "due, unresolved"):
        hz = min(r["horizon_date"] for r in rows)
        return (f"resolves {hz}" if g["grade"] == "not yet due" else
                f"due {hz}; the store has not yet given a final period")
    man = " (resolved by hand, logged)" if g.get("manual") else ""
    if g["horizon_kind"] == "3m":
        r = rows[0]
        v = _resolved_value(r)
        m = r["measurable"]
        cond = (f"between {_fmt(m['level'][0])} and {_fmt(m['level'][1])}"
                if m["comparator"] == "between" else
                f"{m['comparator']} {_fmt(m['level'])}")
        held = "held" if r["outcome"] else "did not hold"
        d = g.get("direction_right")
        dl = ("" if d is None else
              "; direction right" if d else "; direction wrong")
        return (f"{m['series']} read {_fmt(v) if v is not None else '—'} "
                f"against {cond}: the measurable {held}{dl}{man}")
    occ = ", ".join(g["occurred"]) or "none of the scenarios"
    d = g.get("direction_right")
    dl = ("" if d is None else
          "; the top scenario's direction right" if d else
          "; the top scenario's direction wrong")
    ex = "" if g.get("exclusive", True) else \
        f" ({len(g['occurred'])} scenarios held: the set was not exclusive)"
    return (f"{occ} occurred; the highest weight was {g['top']} at "
            f"{g['top_probability']:.2f}{dl}{ex}{man}")


def falsifier_state(r: dict, store, now: str) -> str:
    """held / fired / not yet -- read, never stored."""
    f = r.get("falsifier")
    if not f or store is None:
        return "—"
    day = min(f["date"], now[:10])
    rd = read_at(store, f, now, day=day)
    if not rd["ok"]:
        return "not yet" if f["date"] > now[:10] else "unread"
    if holds(f, rd["value"]):
        return "fired"
    return "held" if f["date"] <= now[:10] else "not yet"


# ---------------------------------------------------------------------------
# The two renderers
# ---------------------------------------------------------------------------
GRADED_COLUMNS = ["Family", "Horizon", "Thesis", "Probability", "Grade",
                  "Brier (coin 0.25)", "Why"]
SEED_COLUMNS = ["Family", "Horizon", "Thesis", "Weight", "Resolves",
                "Brier"]


def graded_table(quarter: str, db_path: Optional[str] = None, *,
                 now: Optional[str] = None, family: Optional[str] = None,
                 conn=None) -> dict:
    """The Quarterly's chapter opener: last quarter's theses with their grades
    and one line of why. `quarter` is the quarter the theses were written FOR
    (the edition's previous quarter). The 12-month sets of earlier quarters are
    re-graded until due, so they are included while open."""
    now = now or session.utc_iso()
    rows = []
    for g in grades(db_path, now=now, family=family, conn=conn):
        current = g["quarter"] == quarter
        carried = (g["horizon_kind"] == "12m" and g["quarter"] < quarter
                   and (g["grade"] in ("not yet due", "due, unresolved")
                        or max(r["resolved_at"] or "" for r in g["rows"])
                        >= _quarter_start(quarter)))
        if not (current or carried):
            continue
        b = g.get("mean_brier")
        rows.append([g["family"].replace("_", " "),
                     ("12-month set" if g["horizon_kind"] == "12m"
                      else "3-month") + ("" if current else
                                         f" ({quarter_label(g['quarter'])})"),
                     g["top"], f"{g['top_probability']:.2f}", g["grade"],
                     f"{b:.4f}" if b is not None else "pending", g["why"]])
    return {"quarter": quarter, "label": quarter_label(quarter),
            "columns": GRADED_COLUMNS, "rows": rows,
            "lines": [] if rows else
            [f"The ledger holds no theses for {quarter_label(quarter)} to grade."]}


def _quarter_start(q: str) -> str:
    return dt.date(int(q[:4]), 3 * (int(q[-1]) - 1) + 1, 1).isoformat()


def seed_table(cutoff: str, db_path: Optional[str] = None, *,
               quarter: Optional[str] = None, conn=None) -> dict:
    """The Monthly's slow-layer table: the theses the ledger holds for the coming
    quarter, in the ledger's form, each weight beside its Brier where graded.
    READ ONLY: the Monthly prints the ledger and never writes a weight."""
    cutoff = _inst(cutoff)
    q = quarter or next_quarter(quarter_of(cutoff))
    lab = quarter_label(q)
    held = [r for r in theses(db_path, conn=conn)
            if r["quarter"] == q and _inst(r["emitted_at"]) <= cutoff]
    rows = []
    for r in held:
        graded = (r.get("brier") is not None and r.get("resolved_at")
                  and _inst(r["resolved_at"]) <= cutoff)
        rows.append([r["family"].replace("_", " "),
                     "12-month" if r["horizon_kind"] == "12m" else "3-month",
                     r["label"], f"{r['probability']:.2f}", r["horizon_date"],
                     f"{r['brier']:.4f}" if graded else "pending"])
    sets = {(r["family"]) for r in held if r["horizon_kind"] == "12m"}
    n3 = sum(1 for r in held if r["horizon_kind"] == "3m")
    n12 = sum(1 for r in held if r["horizon_kind"] == "12m")
    fams = sorted({r["family"] for r in held})
    nt = len(sets) + n3
    if held:
        line = (f"The ledger holds {nt} theses for {lab}; {len(sets)} twelve-month "
                f"scenario sets ({n12} weights) and {n3} three-month theses across "
                f"{len(fams)} families, each written to the probability ledger "
                f"before it printed here, none graded yet"
                if not any(x[-1] != "pending" for x in rows) else
                f"The ledger holds {nt} theses for {lab}; {len(sets)} twelve-month "
                f"scenario sets ({n12} weights) and {n3} three-month theses across "
                f"{len(fams)} families, each weight beside its Brier where graded")
    else:
        line = (f"The ledger holds no theses for {lab} yet; the set is the "
                f"operator's, seeded from config/alt_asset_theses/{q}.yaml")
    return {"quarter": q, "label": lab, "columns": SEED_COLUMNS, "rows": rows,
            "line": line + ".", "count": nt, "weights": len(held)}


# ---------------------------------------------------------------------------
# The show view
# ---------------------------------------------------------------------------
def show(db_path: Optional[str] = None, *, now: Optional[str] = None,
         family: Optional[str] = None) -> list[str]:
    now = now or session.utc_iso()
    out = []
    gs = grades(db_path, now=now, family=family)
    if not gs:
        return ["  no alt_asset thesis in the ledger -- seed one with "
                "seed-alt-asset --file config/alt_asset_theses/<YYYY>q<N>.yaml"]
    tot = {"hit": 0, "miss": 0, "not yet due": 0}
    for g in gs:
        b = g.get("mean_brier")
        bl = (f"Brier {b:.4f} ({b - pl.COIN_BRIER:+.4f} vs coin {pl.COIN_BRIER})"
              if b is not None else "Brier pending")
        extra = ""
        if g["horizon_kind"] == "12m" and g.get("ordering") is not None:
            d = g.get("direction_right")
            extra = (f"  ordering {'right' if g['ordering'] else 'wrong'}"
                     f" (occurred at rank {g.get('occurred_rank') or '—'})"
                     f"  direction {'—' if d is None else 'right' if d else 'wrong'}")
        elif g["horizon_kind"] == "3m" and g.get("direction_right") is not None:
            extra = f"  direction {'right' if g['direction_right'] else 'wrong'}"
        tot[g["grade"]] = tot.get(g["grade"], 0) + 1
        out.append(f"  {g['family']:<14} {quarter_label(g['quarter']):<5} "
                   f"{g['horizon_kind']:<4} {g['grade']:<16} n={g['n']:<2} "
                   f"{bl}{extra}{'  MANUAL' if g.get('manual') else ''}")
        out.append(f"      {g['why']}")
    out.append(f"\n  hit {tot.get('hit', 0)}  miss {tot.get('miss', 0)}  "
               f"not yet due {tot.get('not yet due', 0)}")
    return out


def coherence(db_path: Optional[str] = None) -> list[dict]:
    """The ledger's coherence check, applied to every alt_asset set."""
    with pl.ProbabilityLedger(db_path) as led:
        sets = {r["scenario_set"] for r in led.all_rows()
                if str(r["source"]).startswith(SOURCE_PREFIX + ":")
                and r["scenario_set"]}
        return [b for b in led.coherence() if b["scenario_set"] in sets]


# ---------------------------------------------------------------------------
# The command line (reached through python -m altdata.probability_ledger)
# ---------------------------------------------------------------------------
def cli(args, line: str) -> int:
    if args.cmd == "show":
        if args.source != SOURCE_PREFIX:
            print(f"show reads the thesis register's source only: --source "
                  f"{SOURCE_PREFIX}")
            return 2
        print(f"{line}\nThe thesis register -- grades per family and horizon "
              f"(coin {pl.COIN_BRIER})\n{line}")
        for s in show(args.db, family=args.family):
            print(s)
        bad = coherence(args.db)
        for b in bad:
            print(f"  INCOHERENT {b['scenario_set']}: n={b['n']} sums to "
                  f"{b['total']:.4f}")
        print(line)
        return 1 if bad else 0

    if args.cmd == "resolve-alt-asset":
        res = resolve_due(args.db, store_path=args.db, dry_run=args.dry_run)
        print(f"{line}\nThe thesis register -- resolution from the store"
              f"{' (DRY RUN)' if args.dry_run else ''}\n{line}")
        for r in res["resolved"]:
            print(f"  resolved {r['probability_id'][:12]} outcome={r['outcome']} "
                  f"({r['value']} at {r['observed_at'][:10]})  {r['claim'][:60]}")
        for r in res["waiting"]:
            print(f"  waiting  {r['probability_id'][:12]}  {r['why']}")
        if not res["resolved"] and not res["waiting"]:
            print("  nothing due")
        print(line)
        return 0

    if args.cmd == "resolve-manual":
        out = resolve_manual(args.id, args.outcome, args.note, args.db)
        print(f"MANUAL resolution logged: {out['probability_id']}  "
              f"outcome={out['outcome']}  brier={out['brier']:.4f}")
        return 0

    # seed-alt-asset
    print(f"{line}\nThe thesis register -- seed from {args.file}"
          f"{' (DRY RUN: nothing written)' if args.dry_run else ''}\n{line}")
    try:
        res = seed(args.file, args.db, dry_run=args.dry_run,
                   store_path=args.db, register_db=args.db)
    except ThesisFileError as exc:
        print(f"  REFUSED -- {len(exc.reasons)} reason(s):")
        for r in exc.reasons:
            print(f"    - {r}")
        print(line)
        return 2
    print(f"  quarter     : {quarter_label(res['quarter'])}  written_at "
          f"{res['written_at']}  sha256 {res['file_sha256'][:12]}")
    print(f"  forecasts   : {res['forecasts']} ({res['new']} new)  families: "
          f"{', '.join(res['families'])}")
    for fam, why in sorted(res["skipped"].items()):
        print(f"  not this quarter: {fam} -- {why}")
    for r in res["rows"]:
        em = r["emission"]
        base = (f"at emission {em['value']} ({em['observed_at'][:10]})"
                if em.get("ok") else f"emission unread: {em.get('why')}")
        print(f"    {r['scenario_set']:<26} p={r['probability']:.2f}  "
              f"{r['label'][:44]}  -- {base}")
    for d in res["drafts"]:
        if d["kind"] == "no_draft":
            print(f"  book {d['family']} {d['horizon_kind']}: no draft -- "
                  f"{d['reason']}")
        else:
            c = d["cost"]
            cl = (f"commission ${c['commission']:,.2f} ({c['cost_source']})"
                  if c.get("available") else f"cost row: {c.get('reason')}")
            print(f"  book {d['family']} {d['horizon_kind']}: DRAFT "
                  f"{d['direction']} {d['instrument']} (Book {d['book']}, "
                  f"{d['horizon']}, {d['portfolio_role']})  {cl}")
    if not args.dry_run:
        print(f"\n  recorded {res['recorded']} forecast(s); wrote "
              f"{res['drafts_written']} draft register entr"
              f"{'y' if res['drafts_written'] == 1 else 'ies'} (status draft; "
              f"promoting one is decide.py's, by the operator)")
    print(line)
    return 0

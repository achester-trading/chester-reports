"""
Tells as hypotheses (X-3.6; docs/change-order-alpha-lab-2026-10-12.md section 5).

    python -m alpha.tells import [--dry-run] [--store PATH] [--ledger PATH]
    python -m alpha.tells list   [--ledger PATH]

"Every Weekly tell, Doctrine tell, scanner setup (config/setups.yaml) and graded
forecast source in the probability ledger is imported as a pre-registered
hypothesis -- 'predicts at horizon h after costs?' -- with its mechanism text
quoted from the paper that states it. This is how the reports' intelligence
reaches the lab; the reports never drive it."

THE FOUR SOURCES, READ, NEVER WRITTEN:

  weekly    config/book_b_scanner.yaml `tells:` -- the style pairs (SR-1), the
            consumer ratios (SR-5) and the move screen's print -- the tells the
            Weekly's scanner prints
  doctrine  the Operating Doctrine's section 5.3 trust matrix, one tell per row,
            parsed from the paper's table, and the extra Doctrine tells declared
            in config/alpha_tells.yaml (Rule 9)
  setup     every setup in config/setups.yaml (unclassified and retired ones
            aside)
  forecast  every source in the probability ledger with at least one graded row
            (brier not null), read with SQL over the lab's read-only store
            connection; the probability ledger's module is never imported

Each becomes ONE hypothesis: "<tell> predicts at <h> sessions after costs?", its
mechanism the quote from the paper that states it (file and section cited, the
quote checked word for word against the section), its horizon from the tell's own
window, its instrument and its exit rule. None has a rule in the grammar, so each
registers `needs_code`: queued for the research sitting, which writes its code.
NOTHING HERE TESTS ANYTHING; the fortnightly loop tests on its own cadence.

IDEMPOTENT. A tell is identified by `<kind>:<id>` and fingerprinted by the hash of
its definition (the source's own fields, the quote, the horizon, the exit). An
import finds the newest registration of each tell id:

  * the same hash        -> nothing is written;
  * a different hash     -> a NEW registration, `supersedes` the old one, which
                            the register marks superseded (status refined, its
                            superseded_by set, the reason "the tell changed");
  * not registered yet   -> registered.

Nothing new -> no batch, no manifest, no row. Something new -> ONE batch
(`tells-<stamp>`, source tell, channel importer), its manifest written first
(alpha/manifest.py), every hypothesis pre-registered at the manifest's instant and
counted in its family's variants (10.2 c), as everything the register takes is.

A tell whose quote is not in its cited section, or that no paper states, is not
imported; the import report lists it with the reason. The lab writes no tell: it
reads them and registers questions about them, in alpha.db only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from altdata import session

from . import config as acfg
from . import hypotheses as hyp

REPO = acfg.REPO
CONFIG = REPO / "config" / "alpha_tells.yaml"
SETUPS = REPO / "config" / "setups.yaml"
SCANNER = REPO / "config" / "book_b_scanner.yaml"
KINDS = ("weekly", "doctrine", "setup", "forecast")
FAMILY = {"weekly": "tell-weekly", "doctrine": "tell-doctrine", "setup": "tell-setup",
          "forecast": "tell-forecast"}
SESSIONS_PER_DAY = 252 / 365.25


# ---------------------------------------------------------------------------
# Quotes: the section by its heading, the quote word for word inside it
# ---------------------------------------------------------------------------
def _norm(s: str) -> str:
    s = str(s or "").replace("**", "").replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def section_text(path: Path, section: str) -> Optional[str]:
    """The text under the first heading whose title starts with `section`, up to
    the next heading at the same level or above; None if no heading matches."""
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"^(#+)\s+(.*)$", ln)
        if not m or not m.group(2).strip().startswith(section):
            continue
        level, out = len(m.group(1)), []
        for nxt in lines[i + 1:]:
            m2 = re.match(r"^(#+)\s", nxt)
            if m2 and len(m2.group(1)) <= level:
                break
            out.append(nxt)
        return "\n".join(out)
    return None


def verify_quote(cite: Optional[dict], root: Optional[Path] = None) -> Optional[str]:
    """None when the quote is in the cited section, else why it is not."""
    if not cite:
        return "no paper is cited"
    p = Path(root or REPO) / str(cite.get("file") or "")
    body = section_text(p, str(cite.get("section") or ""))
    if body is None:
        return f"no section {cite.get('section')!r} in {cite.get('file')}"
    if _norm(cite.get("quote")) not in _norm(body):
        return (f"the quote is not in {cite.get('file')}, section "
                f"{cite.get('section')!r}")
    return None


# ---------------------------------------------------------------------------
# The sources
# ---------------------------------------------------------------------------
def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def _tell(kind: str, tid: str, title: str, definition: Any, cite: Optional[dict],
          horizon: Optional[dict], instrument: Any, exit_rule: str,
          extra: Optional[dict] = None) -> dict:
    return {"kind": kind, "id": f"{kind}:{tid}", "title": title,
            "definition": definition, "cite": cite, "horizon": horizon,
            "instrument": instrument, "exit": exit_rule, **(extra or {})}


def weekly_tells(cfg: dict, scanner_path: Optional[Path] = None) -> list[dict]:
    sc = yaml.safe_load(Path(scanner_path or SCANNER).read_text(encoding="utf-8")) or {}
    t = _find(sc, "tells") or {}
    w = cfg.get("weekly") or {}
    out = []
    sp = w.get("style_pairs") or {}
    for p in t.get("style_pairs") or []:
        out.append(_tell(
            "weekly", f"style-{p['growth'].lower()}-{p['value'].lower()}",
            f"The style-regime tell ({p['growth']}/{p['value']})",
            {"pair": p, "average_sessions": t.get("style_average_sessions"),
             "off_high_pct": t.get("style_off_high_pct")},
            sp.get("cite"), sp.get("horizon"),
            [p["value"], p["growth"]], sp.get("exit") or "",
            {"rule": (f"{p['growth']}/{p['value']} below its "
                      f"{t.get('style_average_sessions')}-session average, or more than "
                      f"{t.get('style_off_high_pct')}% off its 52-week high, names the "
                      f"value side: long {p['value']}, short {p['growth']}")}))
    cr = w.get("consumer_ratios") or {}
    for r in t.get("consumer_ratios") or []:
        slug = re.sub(r"[^a-z0-9]+", "-", f"{r['num']}-{r['den']}".lower()).strip("-")
        out.append(_tell(
            "weekly", f"ratio-{slug}", f"The consumer relative-strength tell ({r['label']})",
            {"ratio": r, "average_sessions": t.get("ratio_average_sessions"),
             "change_sessions": t.get("ratio_change_sessions")},
            cr.get("cite"), cr.get("horizon"),
            [r["num"]] + ([r["den"]] if r.get("name_den", True) else []),
            cr.get("exit") or "",
            {"rule": (f"{r['num']}/{r['den']} above its {t.get('ratio_average_sessions')}"
                      f"-session average and higher than "
                      f"{t.get('ratio_change_sessions')} sessions ago names {r['num']} "
                      f"long" + (f" and {r['den']} short" if r.get("name_den", True)
                                 else "") + "; the mirror names the reverse")}))
    if t.get("move_screen_module"):
        ms = w.get("move_screen") or {}
        out.append(_tell(
            "weekly", "move-screen", "The move screen's 2.5-sigma print",
            {"module": t.get("move_screen_module"), "sigma": t.get("move_sigma")},
            ms.get("cite"), None, "the instrument printed", "",
            {"why_not": ms.get("why_not")}))
    return out


def _find(doc: Any, key: str) -> Any:
    if isinstance(doc, dict):
        if key in doc and isinstance(doc[key], dict):
            return doc[key]
        for v in doc.values():
            r = _find(v, key)
            if r is not None:
                return r
    return None


def _slug(s: str) -> str:
    s = re.sub(r"\s*[—–-]\s*", "-", _norm(s).lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def doctrine_tells(cfg: dict, root: Optional[Path] = None) -> list[dict]:
    """The section 5.3 trust matrix's rows, from the paper, and the extras."""
    d = cfg.get("doctrine") or {}
    f = cfg.get("doctrine_file")
    body = section_text(Path(root or REPO) / f, d.get("section", "")) or ""
    hz = d.get("horizons") or {}
    out = []
    for ln in body.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not ln.lstrip().startswith("|") or len(cells) < 6 or \
                cells[0] in ("Signal family", "") or set(cells[0]) <= set("-: "):
            continue
        sid = _slug(cells[0])
        out.append(_tell(
            "doctrine", sid, f"The Doctrine's trust matrix: {_norm(cells[0])}",
            {"row": [_norm(c) for c in cells]},
            {"file": f, "section": d.get("section"), "quote": ln.strip(),
             "framing": d.get("framing_quote")},
            hz.get(sid), _norm(cells[1]),
            "the time stop at the horizon; trusted only in the regime columns "
            "the row marks High or Medium",
            {"rule": (f"{_norm(cells[0])} from {_norm(cells[1])}; trust by regime -- "
                      f"Calm/Positive {_norm(cells[2])}; Rising/Flip-zone "
                      f"{_norm(cells[3])}; Stressed or Crisis/Negative "
                      f"{_norm(cells[4])}; Transition {_norm(cells[5])}")}))
    for x in d.get("extra") or []:
        out.append(_tell("doctrine", x["id"], x["title"], {"extra": x["id"]},
                         x.get("cite"), x.get("horizon"), "index instruments (Book C)",
                         x.get("exit") or "", {"rule": x["title"]}))
    return out


def setup_tells(cfg: dict, setups_path: Optional[Path] = None) -> list[dict]:
    doc = yaml.safe_load(Path(setups_path or SETUPS).read_text(encoding="utf-8")) or {}
    skip = set(cfg.get("setups_skipped") or [])
    books = cfg.get("book_horizons") or {}
    decl = cfg.get("setups") or {}
    out = []
    for sid, s in (doc.get("setups") or {}).items():
        if sid in skip or s.get("retired"):
            continue
        book = s.get("book")
        out.append(_tell(
            "setup", sid, f"The {s.get('name')} setup (Book {book})",
            {k: s.get(k) for k in ("book", "name", "doctrine", "mechanism",
                                    "claimed_edge", "target_n", "kill", "status")},
            (decl.get(sid) or {}).get("cite"), books.get(book),
            "the instrument a packet names (any in the store, the blocklist applied)",
            f"Book {book}'s exit: its invalidation level, else the book's time stop",
            {"rule": f"{s.get('name')}: {s.get('doctrine')}"}))
    return out


def forecast_tells(cfg: dict, store) -> list[dict]:
    """Every probability-ledger source with a graded row, read-only."""
    if store is None:
        return []
    conn = store.conn
    have = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                        "name='probabilities'").fetchone()
    if not have:
        return []
    rows = conn.execute(
        "SELECT source, emitted_at, horizon_date, brier FROM probabilities "
        "ORDER BY source, emitted_at").fetchall()
    by: dict[str, dict] = {}
    for r in rows:
        b = by.setdefault(r["source"], {"n": 0, "graded": 0, "days": []})
        b["n"] += 1
        if r["brier"] is not None:
            b["graded"] += 1
        try:
            e = dt.date.fromisoformat(str(r["emitted_at"])[:10])
            h = dt.date.fromisoformat(str(r["horizon_date"])[:10])
            b["days"].append((h - e).days)
        except ValueError:
            pass
    decl = cfg.get("forecast_sources") or {}
    pre = cfg.get("forecast_source_prefixes") or {}
    out = []
    for src, b in sorted(by.items()):
        if not b["graded"]:
            continue
        entry = decl.get(src) or next((v for p, v in pre.items() if src.startswith(p)),
                                      None)
        med = statistics.median(b["days"]) if b["days"] else None
        sessions = max(1, int(round(med * SESSIONS_PER_DAY))) if med is not None else None
        out.append(_tell(
            "forecast", _slug(src) or "source", f"The {src} forecasts",
            {"source": src},
            (entry or {}).get("cite"),
            {"sessions": sessions, "from": f"the median of its rows' horizon_date "
                                           f"less emitted_at ({med} days)"} if sessions
            else None,
            "the instrument each claim resolves on",
            "each claim's own horizon date (its resolution criterion)",
            {"rule": (f"a {src} probability above the source's own base rate names "
                      f"the claim's side"),
             "counts": {"rows": b["n"], "graded": b["graded"]}}))
    return out


def collect(cfg: dict, store, root: Optional[Path] = None,
            setups_path: Optional[Path] = None,
            scanner_path: Optional[Path] = None) -> list[dict]:
    return (weekly_tells(cfg, scanner_path) + doctrine_tells(cfg, root)
            + setup_tells(cfg, setups_path) + forecast_tells(cfg, store))


# ---------------------------------------------------------------------------
# The hypothesis
# ---------------------------------------------------------------------------
def fingerprint(t: dict) -> str:
    body = {k: t.get(k) for k in ("definition", "cite", "horizon", "instrument",
                                   "exit", "rule")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str)
                          .encode("utf-8")).hexdigest()


def horizon_class(h: int) -> str:
    return "short" if h <= 10 else ("medium" if h <= 63 else "long")


def to_hypothesis(t: dict, local_id: str, con: Optional[dict] = None) -> dict:
    h = int(t["horizon"]["sessions"])
    cite = t["cite"]
    quote = _norm(cite["quote"])
    mech = (f"Quoted from {cite['file']}, section \"{cite['section']}\": "
            f"\"{quote}\"")
    if cite.get("framing"):
        mech += f" The section's question: \"{_norm(cite['framing'])}\""
    con = con or acfg.constitution()
    cadence = "daily" if h <= 5 else "weekly"
    need = int((con.get("validation") or {}).get("min_signals", {}).get(cadence, 40))
    inst = t["instrument"]
    return {
        "local_id": local_id,
        "title": f"{t['title']} predicts at {h} sessions after costs?",
        "horizon_class": horizon_class(h), "horizon_sessions": h,
        "family": FAMILY[t["kind"]], "mechanism": mech,
        "universe": inst if isinstance(inst, list) else str(inst),
        "rule_text": (f"{t.get('rule') or t['title']}. Enter at the next session's close "
                      f"in the tell's direction; exit: {t['exit'] or 'the time stop'}; "
                      f"time stop {h} sessions ({t['horizon'].get('from')}); costed by "
                      f"the lab's cost model."),
        "conditioning": [], "expected": {"sign": "positive_expectancy_after_costs"},
        "sample": {"min_independent_signals": need},
        "data": {"in_store": [], "gaps": ["the tell's rule in code (the research sitting)"]},
        "needs_code": True, "kill": "constitution",
        "state_at_registration": (f"Imported from the {t['kind']} source by "
                                  f"alpha/tells.py; not tested at registration."),
        "tell": {"kind": t["kind"], "id": t["id"], "hash": fingerprint(t),
                 "cited": {"file": cite["file"], "section": cite["section"]},
                 "horizon_from": t["horizon"].get("from")},
    }


def registered_tells(ledger) -> dict[str, dict]:
    """The newest registration of each tell id (source tell), superseded ones
    aside."""
    out: dict[str, dict] = {}
    for h in hyp.Register(ledger).all():
        if h.get("source") != "tell":
            continue
        t = (h.get("spec") or {}).get("tell") or {}
        if not t.get("id") or h.get("superseded_by"):
            continue
        prev = out.get(t["id"])
        if prev is None or h["id"] > prev["id"]:
            out[t["id"]] = h
    return out


def plan(ledger, tells: list[dict], root: Optional[Path] = None) -> dict:
    """What an import would do: new, changed, unchanged, and refused, each tell
    with its reason."""
    have = registered_tells(ledger)
    out: dict[str, list] = {"new": [], "changed": [], "unchanged": [], "refused": []}
    for t in tells:
        if t.get("why_not") or not t.get("cite"):
            out["refused"].append({"id": t["id"], "why": t.get("why_not")
                                   or "no paper is declared that states it"})
            continue
        bad = verify_quote(t["cite"], root)
        if bad:
            out["refused"].append({"id": t["id"], "why": bad})
            continue
        if not (t.get("horizon") or {}).get("sessions"):
            out["refused"].append({"id": t["id"], "why": "no horizon: the source names "
                                   "no window and none is declared"})
            continue
        old = have.get(t["id"])
        if old is None:
            out["new"].append(t)
        elif ((old.get("spec") or {}).get("tell") or {}).get("hash") != fingerprint(t):
            out["changed"].append({**t, "_supersedes": old["id"]})
        else:
            out["unchanged"].append(t["id"])
    return out


def import_tells(ledger, store, as_of: Optional[str] = None,
                 cfg: Optional[dict] = None, root: Optional[Path] = None,
                 setups_path: Optional[Path] = None,
                 scanner_path: Optional[Path] = None, dry_run: bool = False) -> dict:
    """One import. Writes nothing when nothing is new or changed."""
    from . import manifest                                      # noqa: PLC0415
    cfg = cfg or load_config()
    now = as_of or session.utc_iso(timespec="microseconds")
    tells = collect(cfg, store, root, setups_path, scanner_path)
    p = plan(ledger, tells, root)
    todo = p["new"] + p["changed"]
    report = {"seen": len(tells), "new": [t["id"] for t in p["new"]],
              "changed": [t["id"] for t in p["changed"]],
              "unchanged": len(p["unchanged"]), "refused": p["refused"],
              "registered": {}, "batch_id": None}
    if not todo or dry_run:
        return report
    stamp = dt.datetime.fromisoformat(now.replace("Z", "+00:00")).strftime("%Y%m%dT%H%M%S")
    con = acfg.constitution()
    hyps = []
    for i, t in enumerate(todo, 1):
        h = to_hypothesis(t, f"T-{i:03d}", con)
        if t.get("_supersedes"):
            h["supersedes"] = t["_supersedes"]
        hyps.append(h)
    batch = {"schema": hyp.SCHEMA_ID, "batch_id": f"tells-{stamp}", "source": "tell",
             "proposer": "alpha/tells.py (X-3.6)", "channel": "importer",
             "written_at": now, "model_idea_rule": False,
             "inputs": ["config/book_b_scanner.yaml tells", "the Doctrine's section 5.3",
                        "config/setups.yaml", "the probability ledger's graded sources",
                        "config/alpha_tells.yaml"],
             "hypotheses": hyps}
    errs = hyp.validate_batch(batch)
    if errs:
        raise ValueError("the import batch fails the v1 schema: " + "; ".join(errs[:6]))
    m = manifest.write(batch, now)
    reg = hyp.Register(ledger)
    reg.record_batch(batch, m["written_at"], now, m["name"], m["sha256"],
                     m["written_at"], None)
    for h in hyps:
        hid = reg.register(h, batch, m["written_at"], now, "needs_code",
                           "a tell imported as a question; its rule in code is the "
                           "research sitting's", rule_origin=None)
        report["registered"][h["tell"]["id"]] = hid
    report["batch_id"] = batch["batch_id"]
    report["manifest"] = m
    ledger.event("tells", "tells_imported", now, None,
                 after={k: report[k] for k in ("batch_id", "new", "changed",
                                               "unchanged")})
    return report


def counts(ledger) -> dict[str, int]:
    """Registered tells by source (the newest registration of each, superseded
    ones aside) -- the lab line's and the Lab report's count."""
    out = {k: 0 for k in KINDS}
    for tid in registered_tells(ledger):
        k = tid.split(":", 1)[0]
        if k in out:
            out[k] += 1
    return out


def counts_line(c: dict[str, int]) -> str:
    total = sum(c.values())
    if not total:
        return "tells imported: none yet"
    return (f"tells imported: {total} (Weekly {c['weekly']} · Doctrine {c['doctrine']} · "
            f"setups {c['setup']} · forecasts {c['forecast']})")


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.tells",
                                 description="import the reports' tells as hypotheses")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    im = sub.add_parser("import", help="register new and changed tells (box write)")
    im.add_argument("--dry-run", action="store_true")
    sub.add_parser("list", help="the registered tells, by source")
    a = ap.parse_args(argv)
    from .ledger import Ledger                                  # noqa: PLC0415
    if a.cmd == "list":
        with Ledger(a.ledger, read_only=True) as lg:
            print(counts_line(counts(lg)))
            for tid, h in sorted(registered_tells(lg).items()):
                print(f"  {h['id']}  {h['status']:<11} {tid}")
        return 0
    from .store import ReadOnlyStore                            # noqa: PLC0415
    with Ledger(a.ledger) as lg:
        st = ReadOnlyStore(a.store)
        try:
            out = import_tells(lg, st, dry_run=a.dry_run)
        finally:
            st.close()
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

"""
The alternative-assets quarterly scan's ingest (AQ-7).

    python -m altdata.alt_scan ingest docs/scans/alt-assets-2026q4.md
    python -m altdata.alt_scan ingest <file> --no-files     # the store only
    python -m altdata.alt_scan check <file>                 # parse; write nothing

Change order of 10 Oct 2026, section 8: a scheduled task, "Alternative assets --
quarterly scan", fires the Monday of the edition's week and delivers
docs/scans/alt-assets-YYYYqN.md in three parts, each ingested by the mechanism
already ruled for it. Its prompt is docs/scans/PROMPT-alt-assets-quarterly.md;
what it may read and how it is classed is config/alt_asset_scan.yaml; its
standing search list is config/alt_asset_gaps.yaml.

PART 1 -- THE AGENCY REFERENCE TABLES -> SOURCED FIGURES. Each row becomes a row
of the scans ingest's own table (altdata/scans.py, `scan_figures`): no stored
source, not printed. A row without a source URL, a published date, a period or a
vintage is refused, as is a publisher section 8 does not name. The figure's
identity is publisher, table, metric and PERIOD, so a later vintage of the same
period is a revision: its `comparison` carries the prior vintage's figure and the
revision against it ("the quarter's revisions diffed against the stored
vintage"). The Bank of Thailand's and NESDC's figures are stored under their own
scan family, `alt-assets-thailand`, which scans.latest() leaves out unless asked
(section 4.10's isolation).

PART 2 -- STORIES -> VOICES ROWS, STATUS COMPUTED. Each story is a voices row
(altdata/voices.py), its direction kept only on a subject the voices config
declares. The scan NEVER declares a status: a table carrying a Status column has
every row refused, and the ingest computes NEW / REITERATED / INFLECTED from the
stored rows (voices.compute_status) over the quarter against the quarter before.
China's political reporting is filed under source_id `china.<outlet>`, which the
China chapter reads. Rumour is never stored; it is listed, flagged. Thailand's
items are never voices rows -- the voices register prints in the close, the
Weekly and the Monthly, and the Thailand chapter feeds nothing.
The CALENDAR entries -- China's and Thailand's -- and the policy LADDER are
PROPOSALS: written to docs/scans/proposals-YYYYqN.md for the operator to seed
the two hand-seeded political calendars under config/ by hand. This module never
opens, reads or names either file: the Thailand calendar is read by the Thailand
chapter alone (tools/validate_quarterly_stack.py, the isolation check).

PART 3 -- CANDIDATES -> DRAFT INTAKE ENTRIES. Each candidate series or analytic
becomes an entry on the signal intake template (docs/templates/signal-intake.md),
in docs/scans/intake-drafts-YYYYqN.md, unnumbered and marked DRAFT: the register
assigns an SR number when the operator rules, and this module never writes the
register (docs/signal-triage-register.md).

WHERE IT RUNS. The store half (`ingest_store`: figures and voices) is idempotent
and touches no file, so altdata.scans.ingest() calls it for every committed scan
on each Monthly run, the box included. The two Markdown files are written only by
this CLI (`write_files`), in a session, and committed by a human: the box writes
nothing into its checkout.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Optional

from . import scans

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "alt_asset_scan.yaml"
GAPS_PATH = REPO / "config" / "alt_asset_gaps.yaml"
SCANS_DIR = REPO / "docs" / "scans"
FILE_RE = re.compile(r"^alt-assets-(\d{4})q([1-4])\.md$")
FAMILY = "alt-assets"
THAI_FAMILY = "alt-assets-thailand"
PART_RE = re.compile(r"^##\s+([123])\.\s+(.*)$")
SUB_RE = re.compile(r"^###\s+(2[a-d])\.\s+(.*)$")
NOTHING = "nothing this quarter"
STATUS_WORDS = ("NEW", "REITERATED", "INFLECTED", "SILENT", "UNREACHABLE")
PART_NAMES = {"1": "agency reference tables", "2": "emerging stories and issues",
              "3": "candidate series and analytics"}


class AltScanError(ValueError):
    """A scan file the ingest refuses whole."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def load_config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG_PATH).read_text(encoding="utf-8")) or {}


def load_gaps(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load(Path(path or GAPS_PATH).read_text(encoding="utf-8")) or {}


def quarter_of_file(path: Path) -> Optional[str]:
    m = FILE_RE.match(Path(path).name)
    return f"{m.group(1)}q{m.group(2)}" if m else None


def quarter_label(q: str) -> str:
    return f"{q[-1]}Q{q[2:4]}"


def quarter_bounds(q: str) -> tuple[str, str, str]:
    """(prior quarter's start, this quarter's start, the next quarter's start)."""
    y, n = int(q[:4]), int(q[-1])
    start = dt.date(y, 3 * (n - 1) + 1, 1)
    nxt = dt.date(y + (n == 4), 1 if n == 4 else 3 * n + 1, 1)
    prior = dt.date(y - (n == 1), 10 if n == 1 else 3 * (n - 2) + 1, 1)
    return prior.isoformat(), start.isoformat(), nxt.isoformat()


def in_hierarchy(outlet: str, names: list[str]) -> bool:
    o = str(outlet or "").strip().lower()
    return any(o == n.lower() or re.search(rf"\b{re.escape(n.lower())}\b", o)
               for n in names)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------
def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _tables(lines: list[str]) -> list[list[dict]]:
    """Every pipe table in `lines`, as rows keyed by lower-cased header."""
    out, cols, cur = [], None, None
    for ln in lines + [""]:
        if ln.lstrip().startswith("|"):
            cells = _cells(ln)
            if cols is None:
                cols = [c.lower() for c in cells]
                cur = []
                continue
            if all(set(c) <= set("-: ") for c in cells):
                continue
            cur.append(dict(zip(cols, cells)))
        elif cols is not None:
            out.append(cur)
            cols, cur = None, None
    return out


def _date(v: str) -> Optional[str]:
    try:
        return dt.date.fromisoformat(str(v).strip()[:10]).isoformat()
    except ValueError:
        return None


def _blank(v) -> bool:
    return str(v or "").strip() in ("", "—", "-", "n/a")


def parse(path: Path) -> dict:
    """The file's header, its three parts' rows, and every refusal with its
    reason. Reads only."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    head = {"scan_id": path.stem, "scan_path": path.as_posix(),
            "quarter": quarter_of_file(path), "read_on": None, "title": None}
    for ln in lines[:20]:
        if ln.startswith("# ") and not head["title"]:
            head["title"] = ln[2:].strip()
        if "**Read on:**" in ln:
            head["read_on"] = _date(ln.split("**Read on:**", 1)[1].strip())
        if "**Quarter:**" in ln:
            q = ln.split("**Quarter:**", 1)[1].strip()[:6].lower()
            if head["quarter"] and q != head["quarter"]:
                head["quarter_mismatch"] = q
    parts: dict[str, list[str]] = {}
    subs: dict[str, list[str]] = {}
    part = sub = None
    for ln in lines:
        m = PART_RE.match(ln)
        if m:
            part, sub = m.group(1), None
            parts[part] = []
            continue
        m = SUB_RE.match(ln)
        if m and part == "2":
            sub = m.group(1)
            subs[sub] = []
            continue
        if part:
            parts[part].append(ln)
            if sub:
                subs[sub].append(ln)
    out = {**head, "missing": [], "refused": [], "figures": [], "stories": [],
           "ladder": [], "china_calendar": [], "thailand": [], "rumours": [],
           "candidates": []}
    if not head["quarter"]:
        out["missing"].append("the file name is not alt-assets-YYYYqN.md")
    if not head["read_on"]:
        out["missing"].append("no **Read on:** date")
    if head.get("quarter_mismatch"):
        out["missing"].append(f"the header's quarter {head['quarter_mismatch']} is "
                              f"not the file's {head['quarter']}")
    for n, name in PART_NAMES.items():
        if n not in parts:
            out["missing"].append(f"part {n} ({name}) is absent")
        elif not _tables(parts[n]) and NOTHING not in " ".join(parts[n]).lower():
            out["missing"].append(f"part {n} ({name}) has no table and does not "
                                  f"say \"{NOTHING.capitalize()}\"")
    for k in ("2a", "2b", "2c", "2d"):
        if "2" in parts and k not in subs:
            out["missing"].append(f"part 2 has no section {k}")
    out["_parts"], out["_subs"] = parts, subs
    return out


# ---------------------------------------------------------------------------
# Classify: the rows each part yields, and each refusal
# ---------------------------------------------------------------------------
def classify(parsed: dict, cfg: Optional[dict] = None,
             gaps: Optional[dict] = None) -> dict:
    """Fill the parsed file's rows by the rules; every row refused carries its
    reason. Pure: reads config, writes nothing."""
    from . import voices as vmod  # noqa: PLC0415
    cfg = cfg or load_config()
    gap_ids = {g["id"] for g in (gaps or load_gaps()).get("gaps") or []}
    vcfg = vmod.load_config()
    declared = set(vmod.subjects(vcfg))
    kinds = set(vcfg.get("kinds") or {})
    dirs = set(vcfg.get("directions") or ())
    agencies = cfg.get("agencies") or {}
    fams = cfg.get("families") or {}
    classes = cfg.get("classes") or []
    ladder = cfg.get("ladder") or []
    hier = cfg.get("hierarchies") or {}
    p = parsed
    read_on = p.get("read_on") or ""

    def refuse(part: str, what: str, why: str) -> None:
        p["refused"].append({"part": part, "item": what, "reason": why})

    def status_declared(rows: list[dict]) -> bool:
        return bool(rows) and any(k.strip() == "status" for k in rows[0])

    # -- part 1 ---------------------------------------------------------------
    for t in _tables(p["_parts"].get("1") or []):
        for r in t:
            what = f"{r.get('publisher')} {r.get('metric')}"
            pub = str(r.get("publisher") or "").strip()
            if pub not in agencies:
                refuse("1", what, f"publisher {pub!r} is not one section 8 names "
                                  f"(config/alt_asset_scan.yaml agencies)")
                continue
            miss = [k for k in ("table", "metric", "period", "value", "vintage")
                    if _blank(r.get(k))]
            if miss:
                refuse("1", what, f"no {', no '.join(miss)}")
                continue
            published = _date(r.get("published") or "")
            if not published:
                refuse("1", what, "no published date (YYYY-MM-DD)")
                continue
            if read_on and published > read_on:
                refuse("1", what, f"published {published}, after the scan's read "
                                  f"on {read_on}")
                continue
            fig = {"scan_id": p["scan_id"], "scan_path": p["scan_path"],
                   "family": THAI_FAMILY if agencies[pub].get("isolated") else FAMILY,
                   "title": p.get("title") or p["scan_id"],
                   "edition": str(r["vintage"]).strip(),
                   "metric": f"{pub} · {r['table'].strip()} · {r['metric'].strip()}"
                             f" · {r['period'].strip()}",
                   "value": " ".join(x for x in (str(r["value"]).strip(),
                                                 str(r.get("unit") or "").strip())
                                     if x and x != "—"),
                   "comparison": None, "source_url": _url(r.get("source")),
                   "section_ref": "§1", "slide": None, "as_of": published,
                   "read_on": read_on, "raw_value": str(r["value"]).strip()}
            why = scans.refusal(fig)
            if why:
                refuse("1", what, why)
                continue
            p["figures"].append(fig)

    # -- part 2 ---------------------------------------------------------------
    def evidence(r: dict, part: str, what: str, country: Optional[str]) -> Optional[dict]:
        """The shared fields of a part 2 row, or None (refused)."""
        cls = str(r.get("class") or "").strip().lower()
        if cls not in classes:
            refuse(part, what, f"class {cls!r} is not one of {classes}")
            return None
        url = _url(r.get("source"))
        if not url:
            refuse(part, what, "no source URL -- no stored source, not printed")
            return None
        pub = _date(r.get("published") or "")
        if not pub:
            refuse(part, what, "no published date")
            return None
        if read_on and pub > read_on:
            refuse(part, what, f"published {pub}, after the read on {read_on}")
            return None
        outlet = str(r.get("outlet") or "").strip()
        if cls == "authoritative" and country and not in_hierarchy(
                outlet, hier.get(country) or []):
            refuse(part, what, f"classed authoritative, but {outlet!r} is not on "
                               f"the {country} source hierarchy")
            return None
        if cls == "rumour":
            p["rumours"].append({**r, "part": part, "source_url": url,
                                 "published": pub})
            return None
        return {"class": cls, "source_url": url, "published": pub, "outlet": outlet}

    subs = p["_subs"]
    for key in ("2a", "2b", "2c", "2d"):
        for t in _tables(subs.get(key) or []):
            if status_declared(t):
                for r in t:
                    refuse("2", f"{key} {r.get('voice') or r.get('event') or r.get('measure')}",
                           "declares a status; NEW / REITERATED / INFLECTED is "
                           "computed by the voices register from stored rows, "
                           "never declared by the scan")
                continue
            for r in t:
                if key == "2a":
                    fam = str(r.get("family") or "").strip()
                    what = f"2a {fam} {r.get('voice')}"
                    if fam not in fams:
                        refuse("2", what, f"family {fam!r} is not a chapter")
                        continue
                    if any(str(v).strip().upper() in STATUS_WORDS for v in r.values()):
                        refuse("2", what, "a cell declares a status; the register "
                                          "computes it")
                        continue
                    country = ("china" if fam == "china" else
                               "thailand" if fam == "thailand" else None)
                    ev = evidence(r, "2", what, country)
                    if ev is None:
                        continue
                    if fams[fam].get("isolated"):
                        p["thailand"].append({**r, **ev, "kind_of": "story"})
                        continue
                    subj = str(r.get("subject") or "").strip()
                    d = str(r.get("direction") or "").strip().lower()
                    if subj and not _blank(subj):
                        if subj not in declared or subj not in (fams[fam].get("subjects") or []):
                            refuse("2", what, f"subject {subj!r} is not one the "
                                              f"voices config declares for {fam}")
                            continue
                        if d not in dirs:
                            refuse("2", what, f"direction {d!r} is not one of "
                                              f"{sorted(dirs)}")
                            continue
                    kind = str(r.get("kind") or "").strip()
                    if kind not in kinds:
                        refuse("2", what, f"kind {kind!r} is not one of {sorted(kinds)}")
                        continue
                    try:
                        tier = int(str(r.get("tier") or "").strip())
                    except ValueError:
                        tier = None
                    gap = str(r.get("gap") or "").strip()
                    if gap and not _blank(gap) and gap not in gap_ids:
                        refuse("2", what, f"gap {gap!r} is not in "
                                          f"config/alt_asset_gaps.yaml")
                        continue
                    sid = (f"{cfg.get('china_reporting_prefix', 'china.')}"
                           f"{slug(ev['outlet'])}" if fams[fam].get("political")
                           else f"altscan.{fam}")
                    row = {"voice": str(r.get("voice") or "").strip(),
                           "affiliation": str(r.get("affiliation") or "").strip(),
                           "kind": kind, "view": str(r.get("view") or "").strip(),
                           "directions": ([{"subject": subj, "direction": d}]
                                          if subj and not _blank(subj) else []),
                           "source_id": sid, "outlet": ev["outlet"],
                           "source_url": ev["source_url"],
                           "title": f"{fam}: {ev['class']}",
                           "published_at": ev["published"],
                           "retrieved_at": f"{read_on}T12:00:00+00:00",
                           "tier": tier, "origin": "alt_asset_scan",
                           "run_id": p["scan_id"], "family": fam}
                    errs = vmod.validate(row, vcfg)
                    if errs:
                        refuse("2", what, "; ".join(errs))
                        continue
                    p["stories"].append(row)
                elif key == "2b":
                    what = f"2b {r.get('measure')}"
                    rung = str(r.get("rung") or "").strip().lower()
                    if rung not in ladder:
                        refuse("2", what, f"rung {rung!r} is not on the ladder "
                                          f"({' → '.join(ladder)})")
                        continue
                    ev = evidence(r, "2", what, "china")
                    if ev is not None:
                        p["ladder"].append({**r, **ev, "rung": rung})
                elif key in ("2c", "2d"):
                    what = f"{key} {r.get('event') or r.get('event or item')}"
                    country = "china" if key == "2c" else "thailand"
                    day = _date(r.get("date") or "")
                    if key == "2c" and not day:
                        refuse("2", what, "a calendar proposal needs its announced "
                                          "date (an expected date is not an entry)")
                        continue
                    ev = evidence(r, "2", what, country)
                    if ev is None:
                        continue
                    target = p["china_calendar"] if key == "2c" else p["thailand"]
                    target.append({**r, **ev, "date": day,
                                   "kind_of": "calendar" if day else "item"})

    # -- part 3 ---------------------------------------------------------------
    for t in _tables(p["_parts"].get("3") or []):
        for r in t:
            what = f"3 {r.get('candidate')}"
            miss = [k for k in ("candidate", "family", "definition", "cadence", "why")
                    if _blank(r.get(k))]
            if miss:
                refuse("3", what, f"no {', no '.join(miss)} (the definition rule: "
                                  f"numerator, denominator, window, source)")
                continue
            if str(r["family"]).strip() not in fams:
                refuse("3", what, f"family {r['family']!r} is not a chapter")
                continue
            if not _url(r.get("source")):
                refuse("3", what, "no source URL")
                continue
            gap = str(r.get("gap") or "").strip()
            if gap and not _blank(gap) and gap not in gap_ids:
                refuse("3", what, f"gap {gap!r} is not in config/alt_asset_gaps.yaml")
                continue
            p["candidates"].append({**r, "source_url": _url(r.get("source"))})
    return p


def _url(v) -> Optional[str]:
    m = re.search(r"https?://[^\s)>\]|]+", str(v or ""))
    return m.group(0).rstrip(".,") if m else None


def load(path: Path, cfg: Optional[dict] = None, gaps: Optional[dict] = None) -> dict:
    """Parse and classify. Raises AltScanError when the file is refused whole."""
    p = parse(path)
    if p["missing"]:
        raise AltScanError("; ".join(p["missing"]))
    return classify(p, cfg, gaps)


# ---------------------------------------------------------------------------
# The store half: figures and voices (idempotent; no file is written)
# ---------------------------------------------------------------------------
def _number(v: str) -> Optional[float]:
    m = re.search(r"[-+−]?\d[\d,]*(?:\.\d+)?", str(v or ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", "").replace("−", "-"))
    except ValueError:
        return None


def prior_vintage(conn, fig: dict) -> Optional[dict]:
    """The newest stored figure of the same identity read before this scan."""
    r = conn.execute(
        "SELECT * FROM scan_figures WHERE family = ? AND metric = ? AND read_on < ? "
        "ORDER BY read_on DESC, id DESC LIMIT 1",
        (fig["family"], fig["metric"], fig["read_on"])).fetchone()
    return dict(r) if r else None


def revision_text(fig: dict, prior: Optional[dict]) -> Optional[str]:
    """The diff against the prior vintage, as the comparison column prints it."""
    if prior is None:
        return "first stored vintage"
    a, b = _number(prior["value"]), _number(fig["raw_value"])
    if a is None or b is None:
        return f"prior vintage {prior.get('edition') or '—'}: {prior['value']}"
    d = b - a
    sign = "+" if d > 0 else "−" if d < 0 else "±"
    return (f"revised from {prior['value']} ({prior.get('edition') or 'prior vintage'}, "
            f"read {prior['read_on']}): {sign}{abs(d):,.4g}" if d else
            f"unrevised from {prior.get('edition') or 'the prior vintage'} "
            f"(read {prior['read_on']})")


def statuses(rows: list[dict], quarter: str, read_on: str,
             db_path: Optional[str]) -> list[dict]:
    """NEW / REITERATED / INFLECTED for the scan's voices, computed by the
    register's own function over the quarter (to the read) against the quarter
    before, from stored rows retrieved by the read."""
    from . import voices as vmod  # noqa: PLC0415
    prior, start, _ = quarter_bounds(quarter)
    end = (dt.date.fromisoformat(read_on) + dt.timedelta(days=1)).isoformat()
    keys = {vmod.voice_key(r["voice"], r["affiliation"]) for r in rows}
    with vmod.VoicesStore(db_path, readonly=True) as vs:
        stored = [r for r in vs.rows(as_of=f"{read_on}T23:59:59+00:00", until=end)
                  if r["voice_key"] in keys]
    return [x for x in vmod.compute_status(stored, start, end, prior)
            if x["status"] in ("NEW", "REITERATED", "INFLECTED")]


def ingest_store(path: Path, db_path: Optional[str] = None,
                 cfg: Optional[dict] = None, gaps: Optional[dict] = None) -> dict:
    """Part 1's figures and part 2's voices into the store. Idempotent. Touches
    no file -- safe on the box (altdata.scans.ingest calls it)."""
    from . import voices as vmod  # noqa: PLC0415
    p = load(Path(path), cfg, gaps)
    conn = scans._connect(db_path, readonly=False)
    added = 0
    try:
        for fig in p["figures"]:
            fig["comparison"] = revision_text(fig, prior_vintage(conn, fig))
            added += scans.write(conn, {k: v for k, v in fig.items()
                                        if k != "raw_value"})
        conn.commit()
    finally:
        conn.close()
    nv = 0
    with vmod.VoicesStore(db_path) as vs:
        for row in p["stories"]:
            nv += vs.write({k: v for k, v in row.items() if k != "family"})["inserted"]
    p["figures_added"], p["voices_added"] = added, nv
    p["statuses"] = statuses(p["stories"], p["quarter"], p["read_on"], db_path) \
        if p["stories"] else []
    return p


# ---------------------------------------------------------------------------
# The file half: the proposals and the draft intake entries (sessions only)
# ---------------------------------------------------------------------------
def _md(v) -> str:
    return str(v if v is not None else "—").replace("|", "\\|").replace("\n", " ")


def proposals_md(p: dict) -> str:
    q = p["quarter"]
    lab = quarter_label(q)
    L = [f"# Proposals from the alternative-assets quarterly scan, {lab}", "",
         f"**From:** `{p['scan_path']}` (read on {p['read_on']}), by "
         f"`python -m altdata.alt_scan ingest`.", "",
         "**Nothing here is seeded.** Each calendar entry below is a PROPOSAL. The "
         "operator copies the ones that hold into the hand-seeded political "
         "calendars under `config/` (China's and Thailand's) by hand; this ingest "
         "never writes either file. An entry from commentary waits for an "
         "authoritative release; a rumour is never an entry.", ""]
    L += ["## 1. China: political calendar proposals", ""]
    if p["china_calendar"]:
        L += ["| Date | Body | Event | Class | Outlet | Published | Source | Proposable |",
              "|---|---|---|---|---|---|---|---|"]
        for r in sorted(p["china_calendar"], key=lambda r: r["date"]):
            ok = ("yes" if r["class"] == "authoritative" else
                  "not yet — commentary; wait for an authoritative release")
            L.append(f"| {r['date']} | {_md(r.get('body'))} | {_md(r.get('event'))} | "
                     f"{r['class']} | {_md(r['outlet'])} | {r['published']} | "
                     f"{r['source_url']} | {ok} |")
    else:
        L.append("No China calendar proposal this quarter.")
    L += ["", "## 2. China: measures on the ladder (announced → authorised → funded "
          "→ implemented)", "",
          "Only the last two rungs count as demand (section 4.5).", ""]
    if p["ladder"]:
        L += ["| Measure | Body | Rung | Counts as demand | Class | Outlet | Published "
              "| Source |", "|---|---|---|---|---|---|---|---|"]
        for r in p["ladder"]:
            L.append(f"| {_md(r.get('measure'))} | {_md(r.get('body'))} | {r['rung']} | "
                     f"{'yes' if r['rung'] in ('funded', 'implemented') else 'no'} | "
                     f"{r['class']} | {_md(r['outlet'])} | {r['published']} | "
                     f"{r['source_url']} |")
    else:
        L.append("No measure placed on the ladder this quarter.")
    L += ["", "## 3. Thailand: calendar proposals and items (namespace thailand; "
          "isolated)", "",
          "Never voices rows and never figures a report outside the Thailand "
          "chapter reads (section 4.10).", ""]
    if p["thailand"]:
        L += ["| Date | Body | Event or item | Class | Outlet | Published | Source |",
              "|---|---|---|---|---|---|---|"]
        for r in p["thailand"]:
            ev = r.get("event or item") or r.get("event") or r.get("view")
            L.append(f"| {r.get('date') or '—'} | {_md(r.get('body') or r.get('voice'))} | "
                     f"{_md(ev)} | {r['class']} | {_md(r['outlet'])} | "
                     f"{r['published']} | {r['source_url']} |")
    else:
        L.append("No Thailand item this quarter.")
    L += ["", "## 4. Rumour, flagged and not stored", ""]
    if p["rumours"]:
        for r in p["rumours"]:
            what = (r.get("view") or r.get("event") or r.get("measure")
                    or r.get("event or item"))
            L.append(f"- RUMOUR ({r['part']}): {_md(what)} — {_md(r.get('outlet'))}, "
                     f"{r['published']}, {r['source_url']}")
    else:
        L.append("None.")
    L += ["", "## 5. The scan's voices, status computed by the register", "",
          "Computed by `altdata.voices.compute_status` over the quarter against the "
          "quarter before, from stored rows; the scan declared none.", ""]
    if p.get("statuses"):
        L += ["| Voice | Status | Subjects |", "|---|---|---|"]
        for s in p["statuses"]:
            subj = ", ".join(f"{x['subject']}: {x.get('was', '') + ' → ' if x.get('was') else ''}"
                             f"{x['now']}" for x in s.get("subjects") or []) or "—"
            L.append(f"| {_md(s['row']['voice'])} ({_md(s['row']['affiliation'])}) | "
                     f"{s['status']} | {subj} |")
    else:
        L.append("No voice stored from this scan.")
    L += ["", "## 6. Refused at ingest", ""]
    L += ([f"- part {r['part']}, {_md(r['item'])}: {r['reason']}" for r in p["refused"]]
          or ["None."])
    return "\n".join(L) + "\n"


def intake_md(p: dict) -> str:
    lab = quarter_label(p["quarter"])
    L = [f"# Draft intake entries from the alternative-assets quarterly scan, {lab}",
         "", f"**From:** `{p['scan_path']}` (read on {p['read_on']}).", "",
         "**DRAFT — not filed.** Each entry is on the signal intake template "
         "(`docs/templates/signal-intake.md`), unnumbered. The operator rules on "
         "it; a session files a ruled entry in `docs/signal-triage-register.md` "
         "as its next free SR number. Nothing here has rights.", ""]
    if not p["candidates"]:
        L.append("No candidate this quarter.")
    for r in p["candidates"]:
        gap = str(r.get("gap") or "").strip()
        L += [f"### SR-? (DRAFT) {r['candidate']} (alt-assets scan, {p['read_on']}) "
              f"— Thread X", "",
              f"**Register status.** DRAFT — not filed; numbered at ruling.", "",
              f"**1. Home.** The Alternative Assets Quarterly, the {r['family']} "
              f"chapter.", "",
              f"**2. Mechanism.** {r['why']}"
              + (f" Closes the standing gap `{gap}` (config/alt_asset_gaps.yaml)."
                 if gap and not _blank(gap) else ""), "",
              f"**3. Data.** {r['source_url']}; cost {r.get('cost') or 'not stated'}; "
              f"cadence {r['cadence']}.", "",
              f"**Definition (§1.6).** {r['definition']}", "",
              "**4. Signal rights requested.** none (a lens), until a gate passes.", "",
              "**5. Validation.** To be written at ruling.", "",
              "**6. Disposition.** For the operator.", ""]
    return "\n".join(L) + "\n"


def write_files(p: dict, out_dir: Optional[Path] = None) -> list[Path]:
    """The two Markdown files beside the scan. Never a config, never the
    register."""
    d = Path(out_dir or SCANS_DIR)
    d.mkdir(parents=True, exist_ok=True)
    a = d / f"proposals-{p['quarter']}.md"
    b = d / f"intake-drafts-{p['quarter']}.md"
    a.write_text(proposals_md(p), encoding="utf-8", newline="\n")
    b.write_text(intake_md(p), encoding="utf-8", newline="\n")
    return [a, b]


def ingest(path: Path, db_path: Optional[str] = None, out_dir: Optional[Path] = None,
           files: bool = True) -> dict:
    p = ingest_store(path, db_path)
    p["written"] = [str(x) for x in write_files(p, out_dir)] if files else []
    return p


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.alt_scan")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("ingest", "check"):
        s = sub.add_parser(name)
        s.add_argument("file")
        if name == "ingest":
            s.add_argument("--no-files", action="store_true")
            s.add_argument("--out-dir")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "check":
            p = load(Path(args.file))
        else:
            p = ingest(Path(args.file), out_dir=args.out_dir,
                       files=not args.no_files)
    except AltScanError as exc:
        print(f"REFUSED: {exc}")
        return 2
    print(f"{p['scan_id']}: {len(p['figures'])} figures, {len(p['stories'])} voices, "
          f"{len(p['ladder'])} ladder measures, {len(p['china_calendar'])} China "
          f"calendar proposals, {len(p['thailand'])} Thailand items, "
          f"{len(p['rumours'])} rumours flagged, {len(p['candidates'])} candidates")
    if args.cmd == "ingest":
        print(f"  stored: {p['figures_added']} figures, {p['voices_added']} voices")
        for s in p.get("statuses") or []:
            print(f"  {s['status']:<11} {s['row']['voice']}")
        for w in p.get("written") or []:
            print(f"  wrote {w}")
    for r in p["refused"]:
        print(f"  refused part {r['part']} {r['item']}: {r['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

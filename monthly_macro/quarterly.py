"""
The Alternative Assets Quarterly -- the stack's fourth cadence (AQ-1; change
order of 10 Oct 2026, sections 3 and 4.1).

ONE STACK, FOUR CADENCES. The Quarterly is not a parallel pipeline: its front
matter is the Monthly's stack, built by monthly_macro.stack.build at cadence
"quarterly" from the same payload builders over the previous calendar quarter
(payload.build(period="quarter") -> v2.month_bounds), and rendered by the shared
renderer (daily_cascade.stack_render) at the quarterly column of
config/reporting_stack.yaml. Its slow layers are the eleven family chapters
(config `quarterly_chapters`), each a shell on the section 4.1 template (config
`quarterly_template`).

ONE EDITION, TWO PATHS (section 3). Every section and every chapter item carries
a tier: `lead` or `reference`. A chapter prints its lead items first, then a
divider, then its reference items. The READ is the executive summary, the
lead-tier sections and every chapter's lead items, timed at the house rate
(readability: 250 words a minute, 20 seconds a chart) and held to a 90-minute
target the gate WARNS on and never withholds; the REFERENCE is unbudgeted. The
header prints both: "the read: n min; the whole edition: m min".

WHAT IS BUILT HERE AND WHAT IS NOT. The chapter items are AQ-2's: every item
prints "not yet built -- AQ-2" in the stack's not-yet-tracked form, except the
three an existing module fills, each through a NAMED HOOK that degrades to "not
yet" when its module is absent:

    thesis_graded     item 1   altdata.thesis_register.graded_table   (AQ-6)
    thesis_seed       item 2   altdata.thesis_register.seed_table     (AQ-6)
    correlation_rows  item 8   altdata.correlation peer_table, named  (AQ-5)

The executive summary is one paragraph per chapter, built LAST from the
finished chapters by the Monthly's machinery (prose.summary_plan over the
chapters, prose.write_all, the same audit).
"""

from __future__ import annotations

import datetime as dt
import importlib
import json
import logging
import math
import re
from pathlib import Path
from typing import Any, Callable, Optional

from daily_cascade import readability as rd
from daily_cascade import stack as stack_mod
from daily_cascade import stack_render as sr

log = logging.getLogger("monthly_macro.quarterly")

CADENCE = "quarterly"
PREFIX = "alt_asset"
STATE_KEY = "alt_asset"
NOT_BUILT = "not yet built — AQ-2"
CHANGED_HEAD = "Changed since last Quarterly"
LEAD, REFERENCE = "lead", "reference"
TIERS = (LEAD, REFERENCE)
REFERENCE_DIVIDER = "The reference"
REFERENCE_NOTE = ("Beneath the lead page, the full chapter: unbudgeted, organised "
                  "identically in every chapter.")

# THE HOOKS' MODULES, named once so a gate can point a hook at a module that is
# absent and watch it degrade. A hook never raises: an absent module, or one
# that faults, prints "not yet" with the reason.
HOOK_MODULES = {"thesis": "altdata.thesis_register",
                "correlation": "altdata.correlation"}
NOT_YET = {"thesis": "not yet — the thesis register (AQ-6) is not on this build",
           "correlation": "not yet — the correlation layer (AQ-5) is not on this "
                          "build"}


def _module(kind: str):
    try:
        return importlib.import_module(HOOK_MODULES[kind])
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Quarters
# ---------------------------------------------------------------------------
def quarter_of(day: Any) -> str:
    d = dt.date.fromisoformat(str(day)[:10])
    return f"{d.year}q{(d.month - 1) // 3 + 1}"


def next_quarter(q: str) -> str:
    y, n = int(q[:4]), int(q[-1])
    return f"{y + 1}q1" if n == 4 else f"{y}q{n + 1}"


def quarter_label(q: str) -> str:
    return f"{q[-1]}Q{q[2:4]}"


def edition_quarter(ed: dict) -> str:
    """The quarter the edition covers: its window's last session's."""
    return quarter_of((ed.get("window") or {}).get("last") or ed.get("report_date"))


# ---------------------------------------------------------------------------
# The hooks
# ---------------------------------------------------------------------------
def thesis_graded(ch: dict, ctx: dict) -> dict:
    """Item 1: last quarter's theses, graded (AQ-6's chapter opener)."""
    tr = _module("thesis")
    if tr is None:
        return {"not_tracked": [NOT_YET["thesis"]]}
    try:
        t = tr.graded_table(ctx["quarter"], ctx.get("db_path"), now=ctx["now"],
                            family=ch.get("thesis_family"))
    except Exception as exc:                                    # noqa: BLE001
        return {"notes": [f"FAULT (code, not data) -- the thesis register: "
                          f"{type(exc).__name__}"]}
    out = {"lines": list(t.get("lines") or [])}
    if t.get("rows"):
        out["table"] = {"columns": t["columns"], "rows": t["rows"]}
    return out


def thesis_seed(ch: dict, ctx: dict) -> dict:
    """Item 2: the theses the ledger holds for the coming quarter (AQ-6's seed
    view), this chapter's family only."""
    tr = _module("thesis")
    if tr is None:
        return {"not_tracked": [NOT_YET["thesis"]]}
    try:
        q = next_quarter(ctx["quarter"])
        t = tr.seed_table(ctx["now"], ctx.get("db_path"), quarter=q)
    except Exception as exc:                                    # noqa: BLE001
        return {"notes": [f"FAULT (code, not data) -- the thesis register: "
                          f"{type(exc).__name__}"]}
    fam = str(ch.get("thesis_family") or "").replace("_", " ")
    rows = [r for r in t.get("rows") or [] if r and r[0] == fam]
    if not rows:
        return {"lines": [f"The ledger holds no {quarter_label(q)} theses for "
                          f"this chapter yet."]}
    return {"lines": [f"The ledger holds {len(rows)} weights for "
                      f"{quarter_label(q)} in this chapter."],
            "table": {"columns": t["columns"], "rows": rows}}


CORR_COLUMNS = ["Pair or row", "Latest", "Long-run (median or mean)",
                "Divergence or percentile", "As of"]


def correlation_rows(ch: dict, ctx: dict) -> dict:
    """Item 8: the chapter's named rows and peer pairs from the correlation
    layer (AQ-5), read from the store at the edition's cutoff."""
    co = _module("correlation")
    if co is None:
        return {"not_tracked": [NOT_YET["correlation"]]}
    assets = set(ch.get("correlation_assets") or [])
    if not assets:
        return {"lines": ["No correlation-layer asset is assigned to this chapter."]}
    st = ctx.get("store")
    if st is None:
        return {"not_tracked": ["the correlation rows: no store at this cutoff"]}
    rows, gaps = [], []
    try:
        for r in co.peer_table(st, ctx["now"]):
            if r["asset"] not in assets and r["peer"] not in assets:
                continue
            name = f"{co.label(r['asset'])}-{co.label(r['peer'])}, 60 days"
            if r.get("absent_reason"):
                gaps.append(f"{name}: {r['absent_reason']}")
                continue
            rows.append([name, f"{r['latest']:+.2f}", f"{r['median']:+.2f} (median)",
                         f"{r['divergence']:+.2f}", r["as_of"]])
        for n in co.config().get("named") or []:
            legs = n["a"] if isinstance(n["a"], list) else [n["a"]]
            if not (set(legs) | {n["b"]}) & assets:
                continue
            t = co.triple(st, n["key"], ctx["now"])
            if t is None:
                gaps.append(f"{n['label']}: no row stored at this cutoff")
                continue
            rows.append([n["label"], f"{t['latest']:+.2f}",
                         f"{t['mean']:+.2f} (mean)" if t.get("mean") is not None
                         else "—",
                         (f"{t['percentile']:.0f}th percentile"
                          if t.get("percentile") is not None else "—"), t["as_of"]])
    except Exception as exc:                                    # noqa: BLE001
        return {"notes": [f"FAULT (code, not data) -- the correlation layer: "
                          f"{type(exc).__name__}"]}
    out: dict = {"not_tracked": gaps}
    if rows:
        out["table"] = {"columns": CORR_COLUMNS, "rows": rows}
    else:
        out["lines"] = ["No correlation row for this chapter is stored at this "
                        "cutoff."]
    return out


HOOKS: dict[str, Callable[[dict, dict], dict]] = {
    "thesis_graded": thesis_graded,
    "thesis_seed": thesis_seed,
    "correlation_rows": correlation_rows,
}


# ---------------------------------------------------------------------------
# The chapters
# ---------------------------------------------------------------------------
def chapter_items(ch: dict, cfg: dict) -> list[dict]:
    """The template's items this chapter carries (section 4.1's last
    paragraph: light chapters 1-4, 7, 8, 10; Thailand all but 11)."""
    w = ch.get("weight") or "deep"
    return [t for t in cfg.get("quarterly_template") or [] if w in (t.get("in") or [])]


def item_subsection(t: dict, ch: dict, ctx: dict) -> dict:
    ss = {"title": f"{t['n']} · {t['title']}", "item": t["id"], "tier": t["tier"],
          "not_tracked": [], "lines": []}
    hook = HOOKS.get(t.get("hook") or "")
    if hook is None:
        ss["not_tracked"] = [NOT_BUILT]
        return ss
    filled = hook(ch, ctx) or {}
    for k, v in filled.items():
        ss[k] = v
    ss["hook"] = t["hook"]
    return ss


def build_chapter(ch: dict, cfg: dict, ctx: dict) -> dict:
    """One chapter: its lead items, the divider, its reference items."""
    subs = [item_subsection(t, ch, ctx) for t in chapter_items(ch, cfg)]
    lead = [x for x in subs if x["tier"] == LEAD]
    ref = [x for x in subs if x["tier"] == REFERENCE]
    ordered = lead + ([{"divider": REFERENCE_DIVIDER, "divider_note": REFERENCE_NOTE,
                        "tier": REFERENCE}] if ref else []) + ref
    fp = stack_mod._fp([ch["id"]] + [json.dumps(x, sort_keys=True, default=str)
                                     for x in subs])
    return {"id": ch["id"], "title": ch["title"], "subtitle": ch.get("subtitle"),
            "chapter": True, "weight": ch.get("weight"), "tier": "chapter",
            "depth": "deep" if ch.get("weight") != "light" else "medium",
            "depth_reason": None, "items": [], "table": None, "charts": [],
            "data": {"family": ch.get("thesis_family"),
                     "items": [x["item"] for x in subs]},
            "not_tracked": [], "legend": None, "print_items": False,
            "subsections": ordered, "fingerprint": fp, "collapsed": False,
            "claim": None, "paragraphs": [], "trimmed": False, "period": "quarter",
            "phase_a": [], "notes": [], "prose_wanted": False, "empty": False}


def build_chapters(ed: dict, cfg: dict, db_path: Optional[str], st=None) -> list[dict]:
    ctx = {"quarter": edition_quarter(ed), "now": (ed.get("window") or {}).get("now")
           or ed.get("as_of"), "db_path": db_path, "store": st}
    return [build_chapter(ch, cfg, ctx) for ch in cfg.get("quarterly_chapters") or []]


def chapters(ed: dict) -> list[dict]:
    return [s for s in ed.get("sections") or [] if s.get("chapter")]


# ---------------------------------------------------------------------------
# The two paths
# ---------------------------------------------------------------------------
def lead_view(ed: dict) -> dict:
    """The read: the lead-tier sections and each chapter's lead items, with the
    executive summary -- what the read's time counts."""
    secs = []
    for s in ed.get("sections") or []:
        if s.get("chapter"):
            secs.append({**s, "subsections": [x for x in s.get("subsections") or []
                                              if x.get("tier") == LEAD]})
        elif s.get("tier") == LEAD:
            secs.append(s)
    return {"sections": secs, "summary": ed.get("summary") or []}


def lead_charts(ed: dict) -> int:
    n = 0
    for s in lead_view(ed)["sections"]:
        n += len(s.get("charts_rendered") or [])
        for ss in s.get("subsections") or []:
            n += len(ss.get("charts_rendered") or [])
    return n


def read_minutes(ed: dict) -> int:
    """The read's time: the summary's words and the lead items' prose at the
    house rate, plus 20 seconds a lead chart. Never the reference."""
    v = lead_view(ed)
    words = (sum(stack_mod.words(e.get("text")) for e in v["summary"])
             + sum(stack_mod.section_words(s) for s in v["sections"]))
    return max(1, math.ceil(words / rd.WORDS_PER_MINUTE
                            + lead_charts(ed) * rd.SECONDS_PER_CHART / 60.0))


def read_warning(ed: dict) -> Optional[str]:
    """Over the target the gate WARNS; nothing is withheld or cut."""
    t = ed.get("reading_target_minutes")
    if t and ed.get("read_minutes") and ed["read_minutes"] > int(t):
        return (f"the read runs {ed['read_minutes']} minutes against a "
                f"{t}-minute target")
    return None


def tier_faults(ed: dict) -> list[str]:
    """Every section and every chapter item carries a tier."""
    out = []
    for s in ed.get("sections") or []:
        if s.get("chapter"):
            for ss in s.get("subsections") or []:
                if ss.get("tier") not in TIERS:
                    out.append(f"{s['id']}: {ss.get('title') or ss.get('divider')}")
        elif s.get("tier") not in TIERS:
            out.append(s["id"])
    return out


# ---------------------------------------------------------------------------
# The executive summary: one paragraph per chapter, built last
# ---------------------------------------------------------------------------
def apply_summary(ed: dict, written: dict, narrative: bool = True) -> dict:
    """One entry per chapter, in chapter order: its paragraph as published, or
    "(summary withheld — audit)" with the reason kept."""
    from . import prose as prose_mod                             # noqa: PLC0415
    if not narrative:
        ed["summary"] = []
        return ed
    out = []
    for s in chapters(ed):
        e = {"id": s["id"], "title": s["title"], "text": None}
        r = written.get(f"summary:{s['id']}") or {}
        if r.get("published") and r.get("text"):
            e["text"] = rd.polish(" ".join(p for p in re.split(r"\n\s*\n", r["text"])
                                           if p.strip()))
        else:
            e["note"] = prose_mod.SUMMARY_WITHHELD
            e["withheld"] = r.get("reason") or r.get("state") or "not written"
        out.append(e)
    ed["summary"] = out
    return ed


# ---------------------------------------------------------------------------
# The edition
# ---------------------------------------------------------------------------
def edition_name(report_date: str) -> str:
    return f"{PREFIX}_{report_date}_stack.json"


def load_prior(report_date: str, archive_dir: Optional[str]) -> Optional[dict]:
    """The newest Quarterly archived strictly before `report_date` -- the marks
    compare against the prior QUARTERLY, never a Monthly."""
    if not archive_dir or not Path(archive_dir).exists():
        return None
    best = None
    for f in Path(archive_dir).glob(f"{PREFIX}_*_stack.json"):
        m = re.match(rf"{PREFIX}_(\d{{4}}-\d{{2}}-\d{{2}})_stack\.json$", f.name)
        if m and m.group(1) < report_date and (best is None or m.group(1) > best[0]):
            best = (m.group(1), f)
    if not best:
        return None
    try:
        return json.loads(best[1].read_text(encoding="utf-8"))
    except ValueError:
        return None


def save_edition(ed: dict, archive_dir: Optional[str]) -> Optional[str]:
    from daily_cascade import deliver                            # noqa: PLC0415
    return deliver.archive(json.dumps(ed, indent=2, default=str, sort_keys=True),
                           edition_name(ed["report_date"]), archive_dir)


def title(ed: dict) -> str:
    return f"Alternative Assets Quarterly — {ed.get('month') or ed.get('report_date')}"


def html(ed: dict, mode: str = "email", charts: Optional[dict] = None) -> str:
    return sr.page_html(ed, CADENCE, title(ed), mode, charts, CHANGED_HEAD,
                        "Quarterly")


def markdown(ed: dict) -> str:
    return sr.markdown(ed, CADENCE, title(ed), CHANGED_HEAD, "Quarterly",
                       charts=None)


def produce(p: dict, *, archive_dir: Optional[str], client=None,
            model: Optional[str] = None, narrative: bool = True,
            db_path: Optional[str] = None, prior_dir: Optional[str] = None) -> dict:
    """Build, write, polish, time and render the Quarterly. Archives nothing --
    run.py does. `p` is a payload built with period "quarter"."""
    from altdata import observations                             # noqa: PLC0415
    from . import prose as prose_mod                             # noqa: PLC0415
    from . import stack as ms                                    # noqa: PLC0415
    cfg = stack_mod.config()
    prior = load_prior(str(p.get("report_date")),
                       prior_dir if prior_dir is not None else archive_dir)
    book = ms.level_book(p, db_path)
    ed = ms.build(p, prior, db_path, book=book, cadence=CADENCE)
    ed["report"] = "alt_asset_quarterly"
    ed["quarter"] = edition_quarter(ed)
    with observations.ObservationStore(db_path) as st:
        ed["sections"] += build_chapters(ed, cfg, db_path, st)
    # THE FRONT MATTER'S PROSE, by the Monthly's machinery in the Quarterly's
    # voice (prose.voice): the stack's sections and their blocks. The Monthly v2
    # long-form sections are the Monthly's and are not asked for here.
    written: dict = {}
    if narrative:
        try:
            written = prose_mod.write_all(
                p, model=model, client=client, ed=ed,
                secs=prose_mod.stack_plan(ed) + prose_mod.block_plan(ed))
        except Exception:                                       # noqa: BLE001
            log.exception("the front matter's prose faulted; it prints withheld")
    ms.apply_prose(ed, written)
    ed["chart_count"] = 0
    ms.polish(ed, {})
    rd.finalize(ed, CADENCE)
    rd.withhold_duplicates(ed)
    # THE EXECUTIVE SUMMARY, LAST, FROM THE FINISHED CHAPTERS.
    sw: dict = {}
    if narrative:
        try:
            sw = prose_mod.write_all(p, model=model, client=client, ed=ed,
                                     secs=prose_mod.summary_plan(ed, chapters(ed)))
        except Exception:                                       # noqa: BLE001
            log.exception("the executive summary faulted; each paragraph prints "
                          "as withheld")
    apply_summary(ed, sw, narrative)
    stack_mod.enforce_budget(ed, CADENCE)
    ed["reading_minutes"] = rd.reading_minutes(ed)
    ed["read_minutes"] = read_minutes(ed)
    ed["read_warning"] = read_warning(ed)
    if ed["read_warning"]:
        log.warning("the Quarterly's read: %s (warned, never withheld)",
                    ed["read_warning"])
    ed["archive_path"] = (str(Path(archive_dir) / f"{PREFIX}_{p.get('report_date')}.html")
                          if archive_dir else None)
    ed.pop("_retro", None)
    return {"edition": ed, "written": written, "summary_written": sw,
            "charts": {}, "inline_images": [],
            "html_email": html(ed, mode="email", charts={}),
            "html_archive": html(ed, mode="archive", charts={}),
            "markdown": markdown(ed)}

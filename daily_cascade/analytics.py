"""
THE WEEKLY'S DESCRIPTIVE ANALYTICS (W-1.3b, items 3.1-3.5; change order of 11 Oct
2026, section 4). Config: config/weekly_analytics.yaml.

Every function here LABELS what stored data shows by a declared rule. None
forecasts, and none is graded yet: forward-outcome statistics are the scorecard
track's (change order section 6).

  3.1 NARRATIVES   each ledger item's source class and event cluster; counts by
                   cluster ("4 clusters for, 0 against"), never by item; the
                   steelman row from the scan's stored counter-case search; the
                   status from a fixed vocabulary by rule; unreachable sources
                   with their last good scan and the theses that lean on them
  3.2 EXCEPTIONS   three tiers by kind (and by series); the level / change /
                   extreme labels; resolution path, catalyst and invalidation
                   from a template per tier
  3.3 POSITIONING  TFF categories as % of open interest; ETF share counts; the
                   four-week change as a z against two years beside the level z;
                   thin sentiment samples marked and kept out of any composite
  3.4 PRICED       the event x venue matrix with a disagreement column
  3.5 PLAYBOOK     hot / in-line / cool x the transmission channels x the
                   positioning that would amplify each; one frame sentence each
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Optional
from urllib.parse import urlparse

import yaml

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "weekly_analytics.yaml"
STATUSES = ("long-term theme", "catalysed", "priced", "tradeable")


def load_config(path: Optional[Path] = None) -> dict:
    try:
        with open(path or CONFIG_PATH, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except OSError:
        return {}


def _z(hist: list[float], x: float) -> Optional[float]:
    if len(hist) < 8:
        return None
    sd = pstdev(hist)
    return None if sd == 0 else (x - mean(hist)) / sd


# ===========================================================================
# 3.1 NARRATIVES
# ===========================================================================
def source_class(row: dict, cfg: Optional[dict] = None) -> str:
    """official / data / sell-side / press, from the voice's kind; an outlet the
    config names as a data agency is "data" whatever the kind."""
    n = (cfg if cfg is not None else load_config()).get("narratives") or {}
    outlet = str(row.get("outlet") or "")
    if any(d.lower() in outlet.lower() for d in n.get("data_outlets") or []):
        return "data"
    return str((n.get("source_classes") or {}).get(row.get("kind")) or "press")


def url_root(url: Optional[str]) -> str:
    try:
        u = urlparse(str(url or ""))
        return f"{u.scheme}://{u.netloc.lower().removeprefix('www.')}"
    except ValueError:
        return str(url or "")


def cluster_id(row: dict) -> str:
    """Items on the same speech, release or report share one cluster: the source
    URL's root, the published date and the subject (the story)."""
    return (f"{url_root(row.get('source_url'))}|{str(row.get('published_at'))[:10]}"
            f"|{row.get('narrative_id')}")


def annotate(rows: list[dict], cfg: Optional[dict] = None) -> list[dict]:
    """Each ledger item with its source class and cluster id."""
    return [{**r, "source_class": source_class(r, cfg), "cluster": cluster_id(r)}
            for r in rows]


def cluster_counts(rows: list[dict]) -> dict:
    """Clusters for and against: a cluster counts once, on the side its items
    take (both sides when its items split)."""
    out = {"for": set(), "against": set()}
    for r in rows:
        if r.get("side") in out:
            out[r["side"]].add(r.get("cluster") or cluster_id(r))
    return {"for": len(out["for"]), "against": len(out["against"]),
            "items": len(rows)}


def count_text(c: dict) -> str:
    def n(k):
        return f"{c[k]} cluster{'s' if c[k] != 1 else ''}"
    return f"{n('for')} for, {c['against']} against"


def steelman_text(row: Optional[dict], queries: list[str]) -> str:
    """The steelman row: what the scan's counter-case search found, or that it
    found none, with the queries; or that it has not searched."""
    if row is None:
        return ("not searched this week: the scan has written no counter-case "
                "search (queries: " + "; ".join(queries) + ")" if queries else
                "no counter-case queries declared")
    found = row.get("found") or []
    if not found:
        return "none found after search: " + "; ".join(row.get("queries") or queries)
    f = found[0]
    more = f" (+{len(found) - 1} more)" if len(found) > 1 else ""
    return (f"{f.get('voice')} ({f.get('outlet')}, {str(f.get('published_at'))[:10]}): "
            f"{f.get('view')}{more}")


def story_status(sid: str, story: dict, cfg: dict, *, now: str,
                 latest=None, earnings_dates: Optional[dict] = None,
                 register_rows: Optional[list[dict]] = None) -> tuple[str, str]:
    """(status, reason) by the config's rules, first that holds:
    tradeable  a linked instrument carries a register decision (draft or active)
               -- a drafted packet
    priced     the variable the story names is at its implied level
    catalysed  a catalyst -- declared, or a linked name's earnings -- within the
               window
    long-term theme  otherwise."""
    n = cfg.get("narratives") or {}
    sc = (n.get("stories") or {}).get(sid) or {}
    linked = {str(x).upper() for x in story.get("linked_instruments") or []}
    for r in register_rows or []:
        if str(r.get("instrument") or "").upper() in linked and \
                r.get("status") in ("draft", "active") and not r.get("superseded_by"):
            return "tradeable", f"a drafted packet on {r['instrument']}"
    pr = sc.get("priced")
    if pr and latest is not None:
        try:
            x = latest(pr["key"], pr.get("instrument"))
        except Exception:                                       # noqa: BLE001
            x = None
        if x is not None and ((pr.get("side") == "above" and x >= pr["level"]) or
                              (pr.get("side") == "below" and x <= pr["level"])):
            return "priced", f"{pr.get('label') or pr['key']} is reached"
    win = int(n.get("catalyst_window_days") or 30)
    d0 = dt.date.fromisoformat(now[:10])
    cands = [(c.get("date"), c.get("what")) for c in sc.get("catalysts") or []]
    cands += [(d, f"{sym} earnings") for sym, d in (earnings_dates or {}).items()
              if sym.upper() in linked]
    for d, what in sorted((str(d)[:10], w) for d, w in cands if d):
        try:
            dd = dt.date.fromisoformat(d)
        except ValueError:
            continue
        if d0 <= dd <= d0 + dt.timedelta(days=win):
            return "catalysed", f"{what} on {d}"
    return "long-term theme", "no catalyst inside the window"


def unreachable_rows(runs: dict, last_ok: dict, depends: dict) -> list[list]:
    """Each source the scan could not read: the date it was last scanned
    cleanly, and the active theses whose evidence came from it."""
    out = []
    for sid, r in sorted(runs.items()):
        if r.get("state") == "ok":
            continue
        th = sorted(depends.get(sid) or [])
        out.append([r.get("source_name") or sid, r.get("reason") or r.get("state"),
                    last_ok.get(sid) or "never scanned cleanly",
                    ", ".join(th) if th else "no active thesis"])
    return out


# ===========================================================================
# 3.2 EXCEPTIONS
# ===========================================================================
def exception_tier(eid: str, cfg: Optional[dict] = None) -> str:
    e = (cfg if cfg is not None else load_config()).get("exceptions") or {}
    kind, _, series = str(eid).partition(":")
    return str((e.get("series_tier") or {}).get(series)
               or (e.get("kind_tier") or {}).get(kind) or "extreme")


def tier_order(cfg: Optional[dict] = None) -> list[dict]:
    return list(((cfg if cfg is not None else load_config()).get("exceptions") or {})
                .get("tiers") or [])


def series_labels(points: list[tuple[str, float]], cfg: Optional[dict] = None
                  ) -> list[str]:
    """The level / change / extreme labels of one series (dated values, oldest
    first, inside the window already): level -- in its top or bottom decile;
    change -- its latest `change_days` change at |z| >= the threshold against
    the same-length changes; extreme -- at the window's bound."""
    lb = (((cfg if cfg is not None else load_config()).get("exceptions") or {})
          .get("labels") or {})
    if len(points) < 10:
        return []
    vals = [v for _, v in points]
    x = vals[-1]
    out = []
    dec = float(lb.get("level_decile") or 10)
    pct = 100.0 * sum(1 for v in vals if v <= x) / len(vals)
    if pct >= 100 - dec or pct <= dec:
        out.append("level")
    days = int(lb.get("change_days") or 7)
    dates = [dt.date.fromisoformat(d[:10]) for d, _ in points]
    ch = []
    j = 0
    for i, d in enumerate(dates):
        while j < i and (d - dates[j]).days > days:
            j += 1
        if j < i and (d - dates[j]).days >= days - 3:
            ch.append(vals[i] - vals[j])
    if len(ch) >= 9:
        z = _z(ch[:-1], ch[-1])
        if z is not None and abs(z) >= float(lb.get("change_z") or 2.0):
            out.append("change")
    if x >= max(vals) or x <= min(vals):
        out.append("extreme")
    return out


def exception_fields(name: str, tier: str, cfg: Optional[dict] = None) -> dict:
    t = ((((cfg if cfg is not None else load_config()).get("exceptions") or {})
          .get("templates") or {}).get(tier) or {})
    return {k: str(t.get(k) or "—").format(name=name)
            for k in ("resolution", "catalyst", "invalidation")}


# ===========================================================================
# 3.3 POSITIONING
# ===========================================================================
def change_z(points: list[tuple[str, float]], weeks: int = 4) -> Optional[tuple]:
    """(the latest `weeks`-week change, its z against every such change in the
    points given). Points are dated, oldest first; the change is to the latest
    point at least `weeks` weeks before (within three days)."""
    if len(points) < 3:
        return None
    span = 7 * weeks
    dates = [dt.date.fromisoformat(d[:10]) for d, _ in points]
    vals = [v for _, v in points]
    ch = []
    for i, d in enumerate(dates):
        back = [k for k in range(i) if span - 3 <= (d - dates[k]).days <= span + 3]
        if back:
            ch.append(vals[i] - vals[back[-1]])
    if not ch:
        return None
    return ch[-1], _z(ch[:-1], ch[-1])


def zfmt(z: Optional[float]) -> str:
    return "—" if z is None else f"{z:+.1f}"


def thin_cell(n: int, min_n: int) -> Optional[str]:
    return f"thin sample (n={n})" if n < min_n else None


def composite_members(rows: list[dict], min_n: int) -> list[dict]:
    """The sentiment rows a composite may use: never a thin sample."""
    return [r for r in rows if int(r.get("n") or 0) >= min_n]


# ===========================================================================
# 3.4 WHAT'S PRICED: the event x venue matrix
# ===========================================================================
def _short(q: str, n: int = 48) -> str:
    q = re.sub(r"\s+", " ", str(q or "")).strip()
    return q if len(q) <= n else q[: n - 1].rsplit(" ", 1)[0] + "…"


def venue_markets(markets: list[dict], words: list[str], date: str,
                  slack: int = 2) -> dict:
    """{venue: [markets]} whose question names one of `words` and closes within
    `slack` days of the event."""
    d0 = dt.date.fromisoformat(date[:10])
    out: dict = {}
    for m in markets or []:
        q = str(m.get("question") or m.get("event_title") or "")
        if not any(w.lower() in q.lower() for w in words):
            continue
        ca = str(m.get("close_at") or "")[:10]
        try:
            if abs((dt.date.fromisoformat(ca) - d0).days) > slack:
                continue
        except ValueError:
            continue
        out.setdefault(str(m.get("venue")), []).append(m)
    return out


def fomc_row(event: dict, fed: Optional[dict], odds: dict) -> dict:
    """The FOMC row: each venue's probability of the same outcome -- the fed
    funds path's modal one -- so the disagreement compares like with like."""
    cells: dict[str, Optional[float]] = {}
    modal = None
    meet = None
    for m in (fed or {}).get("meetings") or []:
        if abs((dt.date.fromisoformat(m["meeting"][:10])
                - dt.date.fromisoformat(event["date"][:10])).days) <= 2:
            meet = m
            break
    if meet:
        p = float(meet.get("move_probability_25bp") or 0.0)
        imp = {"hike": 0.0, "hold": 0.0, "cut": 0.0}
        if meet["direction"] == "hold":
            imp["hold"] = 1.0
        else:
            imp[meet["direction"]], imp["hold"] = p, 1.0 - p
        modal = max(imp, key=imp.get)
        cells["fed_funds"] = imp[modal]
    for day, by_venue in (odds or {}).items():
        if abs((dt.date.fromisoformat(day[:10])
                - dt.date.fromisoformat(event["date"][:10])).days) > 2:
            continue
        for venue, v in by_venue.items():
            tot = sum(x for x in v.values() if x) or 0.0
            if not tot:
                continue
            norm = {k: (x or 0.0) / tot for k, x in v.items()}
            if modal is None:
                modal = max(norm, key=norm.get)
            cells[venue] = norm.get(modal)
    return {"outcome": modal, "cells": cells}


def matrix(events: list[dict], markets: list[dict], fed: Optional[dict],
           odds: dict, threshold: float, cfg: Optional[dict] = None) -> dict:
    """The event x venue matrix for Ahead's top events. Each venue cell is that
    venue's probability of the row's outcome; the disagreement is the spread in
    points between the highest and the lowest, flagged at the cross-venue
    threshold. Contracts that differ across venues are not compared."""
    pc = (cfg if cfg is not None else load_config()).get("priced_matrix") or {}
    classes = pc.get("classes") or {}
    venues = list(pc.get("venues") or [])
    labels = pc.get("venue_labels") or {}
    rows, data = [], []
    for ev in events:
        c = classes.get(ev.get("cls") or "")
        if not c:
            continue
        if c.get("fed_funds"):
            fr = fomc_row(ev, fed, odds)
            outcome = fr["outcome"]
            cells = dict(fr["cells"])
            comparable = True
        else:
            vm = venue_markets(markets, c.get("words") or [], ev["date"])
            cells, qs = {}, {}
            for v, ms in vm.items():
                top = max(ms, key=lambda m: m.get("probability") or -1.0)
                cells[v], qs[v] = top.get("probability"), _short(top.get("question"))
            outcome = next(iter(qs.values()), None)
            comparable = len(set(qs.values())) <= 1
        ps = [p for p in cells.values() if isinstance(p, (int, float))]
        if len(ps) >= 2 and comparable:
            spread = 100.0 * (max(ps) - min(ps))
            dis = f"{spread:.0f} pts" + (f" -- at or beyond the {threshold:g}-point "
                                         f"threshold" if spread >= threshold else "")
        elif len(ps) >= 2:
            dis = "not compared: the markets list different contracts"
        else:
            dis = "one market or none"
        cons = (pc.get("consensus_feed") and ev.get("consensus")) or None
        row = [ev["event"] + (f" ({outcome})" if outcome else "")]
        for v in venues:
            if v == "consensus":
                row.append(cons or "—")
            else:
                p = cells.get(v)
                row.append("—" if p is None else f"{100 * p:.0f}%")
        row.append(dis)
        rows.append(row)
        data.append({"event": ev["event"], "outcome": outcome, "cells": cells,
                     "disagreement": dis})
    return {"table": {"columns": ["Event (outcome)"] + [labels.get(v, v) for v in venues]
                      + ["Disagreement"], "rows": rows}, "data": data}


# ===========================================================================
# 3.5 AHEAD'S PLAYBOOK
# ===========================================================================
_WORD = {"+": "up", "-": "down", "0": "little changed"}


def hikes_priced(fed: Optional[dict], meetings: int = 4,
                 min_bp: float = 1.0) -> Optional[bool]:
    """Whether the stored fed funds path prices hikes: the implied rate after
    the meeting `meetings` on from the next stands at least `min_bp` above the
    rate after the next meeting. None when no path is stored."""
    ms = [m for m in (fed or {}).get("meetings") or []
          if isinstance(m.get("post_pct"), (int, float))]
    if len(ms) < 2:
        return None
    last = ms[min(meetings, len(ms) - 1)]
    return 100.0 * (last["post_pct"] - ms[0]["post_pct"]) >= min_bp


def playbook(top: Optional[dict], pos: Optional[dict], z_min: float,
             cfg: Optional[dict] = None, fed: Optional[dict] = None
             ) -> Optional[dict]:
    """The top event's playbook: one row per outcome, its transmission across
    the channels and the crowded positions that outcome would force out. A
    position amplifies an outcome when the outcome moves its channel against
    it: sign(position) x the contract's exposure x the channel's move < 0."""
    if not top:
        return None
    pb = (cfg if cfg is not None else load_config()).get("playbook") or {}
    outs = (pb.get("outcomes") or {}).get(top.get("cls") or "")
    if not outs:
        return None
    from .ahead import cftc_names                               # noqa: PLC0415
    names = cftc_names()
    crowded = []
    for k, x in (pos or {}).items():
        if not k.startswith("cftc:") or (x or {}).get("z_2y") is None:
            continue
        if abs(x["z_2y"]) >= z_min:
            crowded.append((k[5:], x))
    # THE REGIME SWITCH (ruled 12 Oct 2026): code, from the stored path.
    rs = pb.get("regime_switch") or {}
    hikes = hikes_priced(fed, int(rs.get("meetings") or 4),
                         float(rs.get("min_bp") or 1.0)) if rs else None
    switched = bool(hikes) and top.get("cls") in (rs.get("classes") or [])
    rows, cells = [], []
    for oc in ("hot", "in-line", "cool"):
        mv = dict(outs.get(oc) or {})
        if switched and oc == rs.get("outcome"):
            for ch in rs.get("channels") or []:
                mv[ch] = "two-sided"
        trans = ", ".join(f"{ch} {rs.get('text')}" if mv.get(ch) == "two-sided"
                          else f"{ch} {_WORD.get(str(mv.get(ch)), '—')}"
                          for ch in pb.get("channels") or [])
        amp = []
        for inst, x in crowded:
            ex = (pb.get("exposures") or {}).get(inst)
            if not ex:
                continue
            m = str(mv.get(ex["channel"]) or "0")
            if m in ("0", "two-sided"):
                continue
            pnl = (1 if (x.get("level") or 0) > 0 else -1) * \
                (1 if ex["sign"] == "+" else -1) * (1 if m == "+" else -1)
            if pnl < 0:
                amp.append(f"speculators {'net long' if (x.get('level') or 0) > 0 else 'net short'} "
                           f"{names.get(inst, inst)} (z {x['z_2y']:+.1f})")
        rows.append({"outcome": oc,
                     "label": (pb.get("outcome_words") or {}).get(oc, oc),
                     "transmission": trans,
                     "amplify": "; ".join(amp) or "no crowded position against it",
                     "read": None})
    return {"event": top.get("event"), "cls": top.get("cls"), "rows": rows,
            "hikes_priced": hikes, "regime_switched": switched}


def playbook_table(p: dict) -> dict:
    return {"columns": ["Outcome", "Transmission (yields, dollar, equities, vol)",
                        "Positioning that would amplify it", "Read"],
            "rows": [[r["label"], r["transmission"], r["amplify"], r["read"] or "—"]
                     for r in p["rows"]]}


PLAYBOOK_SYSTEM = """You write the READ column of a weekly report's playbook for
one scheduled event: one sentence per outcome, saying what that outcome would mean
for the coming week, from the transmission and positioning given. Reply in exactly
this form and nothing else:
HOT: <one sentence>
IN-LINE: <one sentence>
COOL: <one sentence>
Each sentence at most {words} words. No figures at all. No recommendation, no
"we expect", no probability. Coincidence, never cause: never "because" or "driven
by". Plain words; no bullets, no bold."""


def playbook_faults(lines: dict, words: int) -> list[str]:
    out = []
    for k in ("hot", "in-line", "cool"):
        t = lines.get(k)
        if not t:
            out.append(f"no {k.upper()} sentence")
            continue
        if len(t.split()) > words:
            out.append(f"the {k} sentence runs past {words} words")
        if re.search(r"\d", t):
            out.append(f"the {k} sentence carries a figure")
        if re.search(r"\b(because|driven by|we expect|buy|sell)\b", t, re.I):
            out.append(f"the {k} sentence uses a refused word")
    return out


def write_playbook(p: Optional[dict], *, client=None, model: Optional[str] = None,
                   cfg: Optional[dict] = None) -> Optional[dict]:
    """One audited call for the three frame sentences, one retry; a playbook
    whose sentences are withheld keeps its code-built cells and prints a dash."""
    if not p:
        return p
    words = int(((cfg if cfg is not None else load_config()).get("playbook") or {})
                .get("sentence_words") or 30)
    if client is None:
        p["read_state"] = "no model client"
        return p
    from . import narrative as base                             # noqa: PLC0415
    system = PLAYBOOK_SYSTEM.format(words=words)
    frame = {"event": p["event"], "outcomes": [{k: r[k] for k in
                                                ("label", "transmission", "amplify")}
                                               for r in p["rows"]]}
    reason = None
    for attempt in (1, 2):
        sp = system if reason is None else (
            system + "\n\nYOUR PREVIOUS DRAFT WAS WITHHELD: " + reason
            + "\nWrite it again, fixing exactly that.")
        try:
            from altdata import model_meter                     # noqa: PLC0415
            with model_meter.scope(section="playbook"):
                resp = model_meter.create(
                    client, model=model or base.DEFAULT_MODEL, max_tokens=400,
                    system=sp, messages=[{"role": "user",
                                          "content": base.build_prompt(frame, None)}])
            text = "".join(getattr(b, "text", "") for b in resp.content
                           if getattr(b, "type", "") == "text")
        except Exception as exc:                                # noqa: BLE001
            p["read_state"] = f"call failed: {type(exc).__name__}"
            return p
        lines = {}
        for ln in text.splitlines():
            m = re.match(r"^\s*(HOT|IN-LINE|COOL):\s*(.+)$", ln.strip(), re.I)
            if m:
                lines[m.group(1).lower()] = m.group(2).strip()
        faults = playbook_faults(lines, words)
        if not faults:
            for r in p["rows"]:
                r["read"] = lines[r["outcome"]]
            p["read_state"] = "published"
            p["attempts"] = attempt
            return p
        reason = "; ".join(faults)
    p["read_state"] = "withheld: " + str(reason)
    return p

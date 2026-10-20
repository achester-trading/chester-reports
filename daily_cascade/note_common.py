"""
What the two secondary notes share (docs/change-order-secondary-notes-2026-10-19.md,
ruled 19 Oct 2026): the clock, the stored bars, the news since a time, the
prose under the model meter, the subject's audit, the one chart, and delivery.

THE NOTES READ THE STORE ONLY. altdata/note_fetch.py writes it before each note
(the overnight fetch's split, 30.4); nothing here opens a socket, and
tools/validate_secondary_notes.py proves it with the network patched out.

THE NOTES ARE SECONDARY. The 07:00 anchor, the 12:30 alert and the 16:45 close
remain the reports of record. Neither note creates a packet, a candidate, a
flag or a tell, writes the register, enters the market-state object or
computes a regime: each reads what the anchor or the close stored.
"""

from __future__ import annotations

import datetime as dt
import html as _html
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("daily_cascade.note_common")

UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def config() -> dict:
    """reporting_stack.yaml's `secondary_notes`, with the notes' budgets and
    reading targets folded in."""
    from altdata import bars as bars_mod                        # noqa: PLC0415
    cfg = bars_mod.load_config()
    out = dict(cfg.get("secondary_notes") or {})
    out["budget"] = {k: v for k, v in (cfg.get("budget") or {}).items()
                     if k.startswith(("open_note", "evening_note"))}
    out["reading"] = {k: v for k, v in (cfg.get("reading_targets_minutes") or {}).items()
                      if k.startswith(("open_note", "evening_note"))}
    out["note_bars"] = {t["id"]: t for t in cfg.get("note_bars") or []}
    return out


def is_dry(day: str, flag: bool, cfg: Optional[dict] = None) -> bool:
    """A dry run when asked, and every run before `live_from` (the order,
    section 6)."""
    lf = str((cfg or config()).get("live_from") or "9999-12-31")
    return bool(flag) or day < lf


# ---------------------------------------------------------------------------
# The clock
# ---------------------------------------------------------------------------
def et(day: str, hm: str) -> dt.datetime:
    """`hm` ET on `day`, aware."""
    from altdata import session                                 # noqa: PLC0415
    h, m = (int(x) for x in hm.split(":"))
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                               tzinfo=session._eastern_tz())     # noqa: SLF001


def iso(t: dt.datetime) -> str:
    return t.astimezone(UTC).isoformat()


def parse(s: Any) -> Optional[dt.datetime]:
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def hm_et(s: Any) -> str:
    """"HH:MM ET" of an instant, or "time n/a"."""
    from altdata import session                                 # noqa: PLC0415
    t = parse(s)
    return session.to_eastern(t).strftime("%H:%M ET") if t else "time n/a"


def local_open_et(day_et: str, tz: str, hm: str) -> dt.datetime:
    """A foreign market's open in ET, through zoneinfo: the open on the local
    date that begins during the ET evening of `day_et` (Asia's next morning)."""
    from zoneinfo import ZoneInfo                               # noqa: PLC0415
    local_day = dt.date.fromisoformat(day_et) + dt.timedelta(days=1)
    h, m = (int(x) for x in hm.split(":"))
    return dt.datetime.combine(local_day, dt.time(h, m), tzinfo=ZoneInfo(tz))


# ---------------------------------------------------------------------------
# The bars
# ---------------------------------------------------------------------------
def read_bars(inst: str, first: dt.datetime, last: dt.datetime, as_of: str,
              db_path: Optional[str] = None) -> list[dict]:
    """5-minute bars of `inst` that START in [first, last], knowable at as_of."""
    from altdata import bars as bars_mod                        # noqa: PLC0415
    try:
        with bars_mod.BarStore(db_path) as bst:
            return bst.read(inst, "5m", iso(first), iso(last), as_of=as_of)
    except Exception:                                           # noqa: BLE001
        return []


def last_ending_by(bars: list[dict], t: dt.datetime) -> Optional[dict]:
    """The last bar that ENDS at or before t."""
    got = [b for b in bars
           if (parse(b["observed_at"]) or t) + dt.timedelta(minutes=5) <= t]
    return max(got, key=lambda b: str(b["observed_at"])) if got else None


def first_from(bars: list[dict], t: dt.datetime) -> Optional[dict]:
    """The first bar that STARTS at or after t."""
    got = [b for b in bars if (parse(b["observed_at"]) or t) >= t]
    return min(got, key=lambda b: str(b["observed_at"])) if got else None


def newest(bars: list[dict]) -> Optional[dict]:
    return max(bars, key=lambda b: str(b["observed_at"])) if bars else None


def pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a in (None, 0) or b is None:
        return None
    return round(100.0 * (float(b) / float(a) - 1.0), 2)


def bp(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """A yield index quoted in percent, its change in basis points."""
    if a is None or b is None:
        return None
    return round((float(b) - float(a)) * 100.0, 1)


def signed(v: Optional[float], unit: str = "%", dp: int = 2) -> str:
    if v is None:
        return "n/a"
    return f"{v:+.{dp}f}{unit}" if unit == "%" else f"{v:+.{dp}f} {unit}"


def daily_close_before(key: str, day: str, cutoff: str,
                       db_path: Optional[str] = None) -> Optional[tuple[str, float]]:
    """The newest stored daily value of `key` dated before `day`."""
    from altdata import observations                            # noqa: PLC0415
    from altdata.absorption import series                       # noqa: PLC0415
    try:
        with observations.ObservationStore(db_path) as st:
            pts = [(d, v) for d, v, _ in series(st, key, cutoff) if d < day]
    except Exception:                                           # noqa: BLE001
        return None
    return pts[-1] if pts else None


# ---------------------------------------------------------------------------
# The news since a time
# ---------------------------------------------------------------------------
def news(since: dt.datetime, cutoff: str, until: Optional[dt.datetime] = None,
         max_n: int = 5, db_path: Optional[str] = None) -> dict:
    """The agencies' press items (the events ingest's news source) and the voices
    scan's items, each PUBLISHED in [since, until) by the source's own stated
    time and knowable at the cutoff, newest first. No stored source, not printed."""
    from altdata import events as ev_mod                        # noqa: PLC0415
    from altdata.sources import news as news_src                # noqa: PLC0415
    until = until or parse(cutoff)
    items: list[dict] = []
    feeds = set(news_src.FEEDS)
    try:
        with ev_mod.EventStore(db_path) as ev:
            for r in ev.since(iso(since), as_of=cutoff, types=["release"]):
                pl = r.get("payload") or {}
                pub = parse(pl.get("published_at") or r.get("observed_at"))
                if pl.get("feed") not in feeds or not pub or not (since <= pub < until):
                    continue
                items.append({"outlet": str(pl.get("feed")), "title": r.get("title"),
                              "url": r.get("url"), "published_at": iso(pub),
                              "at": hm_et(pub), "ingested_at": r.get("available_at"),
                              "kind": "press"})
    except Exception:                                           # noqa: BLE001
        log.warning("news: the events read faulted", exc_info=True)
    try:
        from altdata import voices as vmod                      # noqa: PLC0415
        with vmod.VoicesStore(_voices_db(db_path), readonly=True) as vs:
            for r in vs.rows(as_of=cutoff, since=iso(since), until=iso(until)):
                items.append({"outlet": r.get("outlet"), "title": r.get("title") or r.get("view"),
                              "voice": r.get("voice"), "url": r.get("source_url"),
                              "published_at": r.get("published_at"),
                              "at": hm_et(r.get("published_at")),
                              "ingested_at": r.get("retrieved_at"), "kind": "voice"})
    except Exception:                                           # noqa: BLE001
        log.info("news: no voices store readable")
    items.sort(key=lambda x: str(x["published_at"]), reverse=True)
    return {"items": items[:max_n], "count": len(items),
            "since": iso(since), "until": iso(until)}


def _voices_db(db_path: Optional[str]) -> Optional[str]:
    return db_path


def news_lines(nw: dict, empty: str) -> list[str]:
    if not nw.get("items"):
        return [empty]
    return [f"{x['at']}, {x['outlet']}: {x['title']}" for x in nw["items"]]


# ---------------------------------------------------------------------------
# Prose
# ---------------------------------------------------------------------------
def words(text: Optional[str]) -> int:
    return len(re.findall(r"\S+", text or ""))


NOTE_RULES = (
    "\n\nTHIS IS A SECONDARY NOTE, not the close and not the 07:00 anchor. Write ONE "
    "paragraph of at most {words} words over the payload's blocks, the most material "
    "first. Every block's lines are already printed beneath your paragraph: say what "
    "they add up to, not each figure again. State no cause: a move is consistent or "
    "inconsistent with an item, never caused by it ('attributions, not causes'). No "
    "recommendation, no flag, no tell, no regime of your own: the regime is the one "
    "the anchor or the close stamped. {extra}")


def prose(payload: dict, *, report: str, words_cap: int, run_id: str,
          extra: str = "", model: Optional[str] = None) -> dict:
    """One audited paragraph, or the reason it was withheld. Through
    narrative.generate with the one-revision retry, under the model meter. A
    reply past the word cap is withheld, never trimmed."""
    from altdata import model_meter                             # noqa: PLC0415
    from . import audit_retry, narrative as nm                  # noqa: PLC0415
    system = nm.SYSTEM_PROMPT + NOTE_RULES.format(words=words_cap, extra=extra)
    try:
        with model_meter.scope(report=report, run_id=run_id):
            r = audit_retry.generate(
                payload, report=report, model=model or nm.MORNING_MODEL,
                system_prompt=system, guide_path=nm.REPO / "docs" / "narrative-template-notes.md",
                max_chars=words_cap * 8, one_paragraph=True)
    except Exception as exc:                                    # noqa: BLE001
        return {"state": "call_failed", "text": None,
                "reason": f"{type(exc).__name__}: {exc}"[:200]}
    if not r.published:
        return {"state": r.state, "text": None, "reason": r.reason}
    n = words(r.text)
    if n > words_cap:
        return {"state": "too_long", "text": None,
                "reason": f"the paragraph runs {n} words; the cap is {words_cap}"}
    return {"state": "published", "text": r.text, "reason": None, "words": n,
            "model": r.model}


def subject(text: str, payload: dict, fallback: str) -> tuple[str, bool]:
    """The code-written subject if every figure in it passes the numeral audit
    against the note's own payload, else the figure-free fallback."""
    from altdata import numeral_audit as na                     # noqa: PLC0415
    from . import precision                                     # noqa: PLC0415
    try:
        p = na.with_signed(na.with_ordinals(precision.apply(payload)))
        ok = na.audit(text, p).passed
    except Exception:                                           # noqa: BLE001
        ok = False
    return (text, True) if ok else (fallback, False)


# ---------------------------------------------------------------------------
# The one chart
# ---------------------------------------------------------------------------
def chart(bars: list[dict], title: str, name: str) -> Optional[dict]:
    """ES's 5-minute candles over the window, or None."""
    if len(bars) < 2:
        return None
    try:
        from . import charts                                    # noqa: PLC0415
        plt = charts._plt()                                     # noqa: SLF001
        fig, ax = plt.subplots(figsize=(charts.CHART_W, 2.6))
        charts._candles(ax, bars)                               # noqa: SLF001
        ax.set_title(title, fontsize=9, loc="left")
        n = len(bars)
        ticks = list(range(0, n, max(1, n // 6)))
        ax.set_xticks(ticks)
        ax.set_xticklabels([hm_et(bars[i]["observed_at"])[:5] for i in ticks], fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.set_xlim(-1, n)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        out = charts._finish(fig, name, None)                   # noqa: SLF001
        return {"cid": name, "png": out["png"], "title": title}
    except Exception:                                           # noqa: BLE001
        log.warning("the note's chart faulted", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------
NAVY = "#0d2b45"


def page(title: str, intro: list[str], blocks: list[dict], prose_text: Optional[str],
         footer: list[str], chart_img: Optional[str] = None) -> str:
    """One plain HTML page: the paragraph (when written), the chart, then each
    block with its as-of time and lines."""
    e = _html.escape
    out = [f'<div style="font-family:Georgia,serif;max-width:640px;color:#1f2933">',
           f'<h2 style="color:{NAVY};margin:0 0 6px 0">{e(title)}</h2>']
    out += [f'<p style="font-size:12px;color:#52606d;margin:2px 0">{e(x)}</p>' for x in intro]
    if prose_text:
        out.append(f'<p style="font-size:15px;line-height:1.5">{e(prose_text)}</p>')
    if chart_img:
        out.append(f'<p><img src="{chart_img}" style="max-width:100%" alt="chart"></p>')
    for b in blocks:
        out.append(f'<h3 style="color:{NAVY};font-size:14px;margin:14px 0 2px 0">'
                   f'{e(b["title"])} <span style="font-weight:normal;color:#7b8794;'
                   f'font-size:11px">as of {e(b.get("as_of") or "n/a")}</span></h3>')
        out.append('<ul style="margin:2px 0 0 18px;padding:0;font-size:13px">')
        out += [f"<li>{e(x)}</li>" for x in b.get("lines") or []]
        out.append("</ul>")
    out += [f'<p style="font-size:11px;color:#7b8794">{e(x)}</p>' for x in footer]
    out.append("</div>")
    return "\n".join(out)


def text_page(title: str, intro: list[str], blocks: list[dict],
              prose_text: Optional[str], footer: list[str]) -> str:
    out = [title, *intro, ""]
    if prose_text:
        out += [prose_text, ""]
    for b in blocks:
        out.append(f"{b['title']} (as of {b.get('as_of') or 'n/a'})")
        out += [f"  - {x}" for x in b.get("lines") or []]
        out.append("")
    return "\n".join(out + footer)


def block_words(blocks: list[dict]) -> int:
    return sum(words(" ".join(b.get("lines") or [])) + words(b["title"]) for b in blocks)


def reading_minutes(blocks: list[dict], prose_text: Optional[str], charts_n: int) -> float:
    """The house estimate (daily_cascade/readability.py): 250 words a minute plus
    20 seconds a chart."""
    return round((block_words(blocks) + words(prose_text)) / 250.0 + charts_n / 3.0, 1)


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------
def dryrun_dir(archive_dir: Optional[str], dry: bool) -> Optional[str]:
    """The weekly's rule: a dry run with no archive named goes to dryrun/."""
    from . import deliver as delivery                           # noqa: PLC0415
    if dry and not archive_dir:
        return str(Path(delivery.ARCHIVE_DIR) / "dryrun")
    return archive_dir


def ship(*, name: str, subject_line: str, payload: dict, mail_html: str,
         archive_html: str, text: str, dry: bool, email: bool,
         archive_dir: Optional[str], chart_obj: Optional[dict]) -> dict:
    """Archive the page and its payload; mail it unless a dry run was not asked
    to (a dry run before live_from IS mailed, under "[DRY RUN]"). Never raises."""
    from . import deliver as delivery                           # noqa: PLC0415
    subj = ("[DRY RUN] " if dry else "") + subject_line
    delivery.archive(json.dumps(payload, indent=1, default=str, sort_keys=True),
                     name.replace(".html", "_payload.json"), archive_dir)
    imgs = [(chart_obj["cid"], chart_obj["png"])] if chart_obj else None
    if dry and not email:
        path = delivery.archive(archive_html, name, archive_dir)
        return {"delivery": "dry_run", "archive_path": path, "subject": subj}
    out = delivery.deliver(subj, mail_html, name, text_fallback=text,
                           archive_dir=archive_dir, archive_html=archive_html,
                           inline_images=imgs)
    out["subject"] = subj
    return out


def data_uri(png: bytes) -> str:
    import base64                                               # noqa: PLC0415
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")

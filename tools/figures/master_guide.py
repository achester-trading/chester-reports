#!/usr/bin/env python3
"""
The Master Guide's two generated figures (docs/master-guide.md; the
specification of 19 Oct 2026, section 4). Regenerate them whenever a timer, a
chat-side task or the library's roster changes:

    python tools/figures/master_guide.py            # writes both
    python tools/figures/master_guide.py --check    # exits 1 if either is stale

  fig-02-clock.svg     the clock: a 24-hour weekday dial of the box's timers
                       (deploy/systemd/*.timer) and the chat-side tasks
                       (docs/master-guide/chat-tasks.yaml) in a second colour,
                       Ari's touches ringed; a week strip and a month strip
  fig-05-library.svg   the library map: the roster's papers (the library guide's
                       at-a-glance table) in the four groups of what they help
                       decide, each with the books it serves

Each SVG carries its own panel and switches its palette with
prefers-color-scheme, so it reads on a light page and a dark one, and its text
is sized for a phone held upright (viewBox 720 wide, nothing under 15 units).
"""

from __future__ import annotations

import argparse
import html
import math
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent
OUT = REPO / "docs" / "figures" / "master-guide"
UNITS = REPO / "deploy" / "systemd"
TASKS = REPO / "docs" / "master-guide" / "chat-tasks.yaml"
LIBRARY = REPO / "docs" / "white-paper-library-guide.md"

STYLE = """<style>
.bg{fill:#ffffff}.panel{fill:#f3f5f8}.ink{fill:#16202e}.mute{fill:#5b6675}
.line{stroke:#9aa5b4}.grid{stroke:#d5dbe3}.box{fill:#0f5c9e}.chat{fill:#c06a12}
.touch{stroke:#16202e}.boxs{stroke:#0f5c9e}.chats{stroke:#c06a12}.onbox{fill:#ffffff}
.pill{fill:#e6ecf3}.bA{fill:#2b6cb0}.bB{fill:#2f855a}.bC{fill:#b7791f}.bD{fill:#9b2c2c}
@media (prefers-color-scheme: dark){
.bg{fill:#121821}.panel{fill:#1b2330}.ink{fill:#e8edf3}.mute{fill:#a3adbb}
.line{stroke:#5f6b7b}.grid{stroke:#2c3646}.box{fill:#5aa2e6}.chat{fill:#f0a14a}
.touch{stroke:#e8edf3}.boxs{stroke:#5aa2e6}.chats{stroke:#f0a14a}.onbox{fill:#121821}
.pill{fill:#243042}.bA{fill:#63a4ff}.bB{fill:#5cc28a}.bC{fill:#e8b04e}.bD{fill:#e07a7a}}
text{font-family:Aptos,'Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif}
</style>"""

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def svg_open(w: int, h: int, title: str, desc: str) -> list[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t d">',
            f"<title id=\"t\">{esc(title)}</title><desc id=\"d\">{esc(desc)}</desc>",
            STYLE, f'<rect class="bg" x="0" y="0" width="{w}" height="{h}" rx="14"/>']


def text(x: float, y: float, s: str, cls: str = "ink", size: int = 16,
         anchor: str = "start", weight: str = "400") -> str:
    return (f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>')


# ---------------------------------------------------------------------------
# The timers and the tasks, as clock items
# ---------------------------------------------------------------------------
def timers() -> list[dict]:
    """[{name, label, cal}] from deploy/systemd: each timer's Description and
    its OnCalendar lines (or OnUnitActiveSec)."""
    out = []
    for p in sorted(UNITS.glob("*.timer")):
        t = p.read_text(encoding="utf-8")
        desc = next((ln.split("=", 1)[1].strip() for ln in t.splitlines()
                     if ln.startswith("Description=")), p.stem)
        cal = [ln.split("=", 1)[1].strip() for ln in t.splitlines()
               if ln.startswith("OnCalendar=")]
        every = [ln.split("=", 1)[1].strip() for ln in t.splitlines()
                 if ln.startswith("OnUnitActiveSec=")]
        out.append({"name": p.stem, "desc": desc, "cal": cal, "every": every})
    return out


_HM = re.compile(r"(\d{1,2}):(\d{2})")


def classify(cal: str) -> dict:
    """One OnCalendar line -> {kind, days, hours, minute, dom}."""
    s = cal.replace("America/New_York", "").strip()
    days = ""
    m = re.match(r"^((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[\w.,-]*)\s+(.*)$", s)
    if m:
        days, s = m.group(1), m.group(2)
    date, _, clock = s.rpartition(" ") if " " in s else ("", "", s)
    out = {"days": days, "date": date}
    hm = re.match(r"^(\d{1,2})(?:\.\.(\d{1,2}))?:([\d,/]+)(?::\d+)?$", clock)
    if hm:
        out["h0"] = int(hm.group(1))
        out["h1"] = int(hm.group(2) or hm.group(1))
        out["mins"] = hm.group(3)
    if out.get("h0") is None:
        out["kind"] = "interval"
    elif date and re.match(r"^\*-\*-0?\d+$", date):
        out["kind"] = "monthly"
        out["dom"] = int(date.rsplit("-", 1)[1])
    elif date and re.search(r"-0?1,0?4,0?7,10-", date):
        out["kind"] = "quarterly"
    elif days in ("Sat", "Sun") or (days and "Mon" not in days and "Fri" not in days):
        out["kind"] = "weekly"
    elif out.get("h0") is not None and out["h0"] != out["h1"]:
        out["kind"] = "range"
    else:
        out["kind"] = "daily"
    return out


SHORT = {
    "ibgateway-restart": "IB Gateway restart", "chester-backup": "Backup sweep",
    "chester-voices": "Voices scan", "chester-overnight": "Overnight fetch",
    "chester-morning-anchor": "Morning anchor", "chester-heartbeat": "Heartbeat",
    "chester-dealer-0945": "Dealer capture", "chester-dealer-1230": "Capture + 12:30 alert gates",
    "chester-auction": "Auction sampler", "chester-eod": "EOD options pass",
    "chester-flashalpha": "Vendor writer", "chester-vendor-chains": "Vendor chains",
    "chester-daily-close": "The close", "chester-crypto-basket": "Crypto basket",
    "chester-alpha-nightly": "Alpha nightly", "chester-alpha-proposer": "Alpha proposer",
    "chester-meme-ingest": "Meme ingest", "chester-prices-saturday": "Saturday prices",
    "chester-weekly": "The Weekly", "chester-alpha-weekly": "Alpha weekly",
    "chester-restore-test": "Restore test", "chester-monthly": "The Monthly",
    "chester-quarterly": "Alt Assets Quarterly", "chester-restore-drill": "Restore drill",
    "chester-ibkr-sync": "IBKR sync", "chester-deploy": "Self-deploy",
    "ibgateway-watchdog": "Gateway watchdog",
}
# The reports Ari reads, ringed on the dial (his touches).
# Timers that never run as shipped: the Quarterly ships disabled; the restore
# drill is superseded by the weekly restore test and never enabled.
OFF = {"chester-quarterly", "chester-restore-drill"}
TOUCHES = {"chester-morning-anchor", "chester-dealer-1230", "chester-daily-close",
           "chester-weekly", "chester-monthly"}


def load_tasks() -> list[dict]:
    doc = yaml.safe_load(TASKS.read_text(encoding="utf-8")) or {}
    return [t for t in doc.get("tasks") or [] if t.get("status") != "retired"]


# ---------------------------------------------------------------------------
# Figure 2: the clock
# ---------------------------------------------------------------------------
def clock_svg() -> str:
    W, H = 720, 1500
    cx, cy, R = 360, 420, 230
    out = svg_open(W, H, "Figure 2. The clock",
                   "The box's timers and the chat-side tasks on a 24-hour weekday dial, "
                   "with the week and the month below. Generated from deploy/systemd and "
                   "docs/master-guide/chat-tasks.yaml.")
    out.append(text(24, 44, "Figure 2. The clock (ET)", size=24, weight="700"))
    out.append(text(24, 72, "Blue: the box's timers. Orange: chat-side tasks. "
                            "Ringed: a report you read.", "mute", 16))
    out.append(f'<circle class="panel" cx="{cx}" cy="{cy}" r="{R + 50}"/>')
    out.append(f'<circle fill="none" class="line" stroke-width="2" cx="{cx}" cy="{cy}" r="{R}"/>')

    def pt(hours: float, r: float) -> tuple[float, float]:
        a = (hours / 24.0) * 2 * math.pi - math.pi / 2
        return cx + r * math.cos(a), cy + r * math.sin(a)
    for h in range(24):
        x0, y0 = pt(h, R - 8)
        x1, y1 = pt(h, R + 8 if h % 3 == 0 else R)
        out.append(f'<line class="line" stroke-width="2" x1="{x0:.1f}" y1="{y0:.1f}" '
                   f'x2="{x1:.1f}" y2="{y1:.1f}"/>')
        if h % 3 == 0:
            x, y = pt(h, R + 30)
            out.append(text(x, y + 6, f"{h:02d}", "mute", 17, "middle", "600"))

    daily, ranges, weekly, monthly = [], [], [], []
    for t in timers():
        if t["every"] and not t["cal"]:
            ranges.append((t["name"], 0.0, 24.0, f"every {t['every'][0]}"))
            continue
        for c in t["cal"]:
            k = classify(c)
            if t["name"] == "chester-deploy":
                continue
            if k["kind"] == "interval":
                ranges.append((t["name"], 0.0, 23.99, c))
                continue
            if k["kind"] == "daily":
                mins = int(k["mins"].split(",")[0])
                daily.append({"name": t["name"], "h": k["h0"] + mins / 60.0,
                              "hm": f"{k['h0']:02d}:{mins:02d}", "src": "box"})
            elif k["kind"] == "range":
                ranges.append((t["name"], k["h0"], k["h1"] + 0.5, k["mins"]))
            elif k["kind"] == "weekly":
                weekly.append({"name": t["name"], "days": k["days"],
                               "hm": f"{k.get('h0', 0):02d}:{int(k['mins'].split(',')[0]):02d}",
                               "src": "box"})
            elif k["kind"] in ("monthly", "quarterly"):
                monthly.append({"name": t["name"], "dom": k.get("dom"), "kind": k["kind"],
                                "hm": f"{k.get('h0', 0):02d}:{int(k['mins'].split(',')[0]):02d}",
                                "src": "box"})
    # the self-deploy's operating windows, as one arc pair
    ranges.append(("chester-deploy", 9.0, 15.67, "windows"))
    ranges.append(("chester-deploy", 17.33, 23.5, "windows"))
    for task in load_tasks():
        w = task.get("when") or {}
        if w.get("kind") == "daily":
            hh, mm = (int(x) for x in str(w["time_et"]).split(":"))
            daily.append({"name": task["name"], "h": hh + mm / 60.0,
                          "hm": f"{hh:02d}:{mm:02d}", "src": "chat"})
        elif w.get("kind") == "weekly":
            weekly.append({"name": task["name"], "days": w.get("days", ""),
                           "hm": str(w.get("time_et", "")), "src": "chat"})
        elif w.get("kind") in ("monthly", "quarterly", "event"):
            monthly.append({"name": task["name"], "dom": w.get("dom"), "kind": w["kind"],
                            "hm": str(w.get("time_et", "")), "src": "chat",
                            "label": w.get("label")})

    # interval arcs inside the dial
    rr = R - 34
    for name, h0, h1, _ in ranges:
        x0, y0 = pt(h0, rr)
        x1, y1 = pt(h1, rr)
        large = 1 if (h1 - h0) > 12 else 0
        dash = ' stroke-dasharray="4 6"' if name in ("ibgateway-watchdog", "chester-deploy") else ""
        out.append(f'<path fill="none" class="boxs" stroke-width="6" opacity="0.55"{dash} '
                   f'd="M{x0:.1f},{y0:.1f} A{rr},{rr} 0 {large} 1 {x1:.1f},{y1:.1f}"/>')
        rr -= 12
    out.append(text(cx, cy - 8, "weekdays", "mute", 18, "middle"))
    out.append(text(cx, cy + 18, "inner arcs: sync,", "mute", 15, "middle"))
    out.append(text(cx, cy + 38, "deploy windows, watchdog", "mute", 15, "middle"))

    # the points on the dial, numbered; close points stagger inward
    daily.sort(key=lambda d: (d["h"], d["src"]))
    prev_h, lane = -9.0, 0
    for i, d in enumerate(daily, 1):
        lane = (lane + 1) % 3 if d["h"] - prev_h < 0.45 else 0
        prev_h = d["h"]
        x, y = pt(d["h"], R - lane * 30)
        cls = "box" if d["src"] == "box" else "chat"
        out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="13"/>')
        if d["name"] in TOUCHES:
            out.append(f'<circle fill="none" class="touch" stroke-width="3" cx="{x:.1f}" '
                       f'cy="{y:.1f}" r="18"/>')
        out.append(text(x, y + 5, str(i), "onbox", 14, "middle", "700"))

    y = 760
    out.append(text(24, y, "Weekdays, by time", size=20, weight="700"))
    y += 12
    col_w, line_h = 336, 30
    half = (len(daily) + 1) // 2
    for i, d in enumerate(daily, 1):
        col = 0 if i <= half else 1
        row = (i - 1) % half
        x = 24 + col * (col_w + 24)
        yy = y + 24 + row * line_h
        cls = "box" if d["src"] == "box" else "chat"
        out.append(f'<circle class="{cls}" cx="{x + 12}" cy="{yy - 6}" r="11"/>')
        out.append(text(x + 12, yy - 1, str(i), "onbox", 13, "middle", "700"))
        lab = SHORT.get(d["name"], d["name"])
        mark = " ◉" if d["name"] in TOUCHES else ""
        out.append(text(x + 30, yy, f"{d['hm']}  {lab}{mark}", "ink", 16))
    y = y + 24 + half * line_h + 24

    def listed(items: list[dict], y: float, when) -> float:
        for it in items:
            cls = "box" if it["src"] == "box" else "chat"
            lab = it.get("label") or SHORT.get(it["name"], it["name"])
            mark = " ◉" if it["name"] in TOUCHES else ""
            off = " (not enabled)" if it["name"] in OFF else ""
            out.append(f'<rect class="{cls}" x="24" y="{y - 15}" width="10" height="20" rx="3"/>')
            out.append(text(42, y, f"{when(it)}  {lab}{mark}{off}", "ink", 16))
            y += 28
        return y

    # the week strip: a mark on each day that carries something, then the list
    out.append(text(24, y, "The week", size=20, weight="700"))
    y += 16
    cw = (W - 48) / 7.0
    weekly.sort(key=lambda w: (DAYS.index(w["days"][:3]) if w["days"][:3] in DAYS else 9,
                               w["hm"]))
    for j, dn in enumerate(DAYS):
        x = 24 + j * cw
        out.append(f'<rect class="panel" x="{x + 2:.1f}" y="{y}" width="{cw - 4:.1f}" '
                   f'height="34" rx="6"/>')
        out.append(text(x + cw / 2, y + 23, dn, "ink", 16, "middle", "700"))
        here = [w for w in weekly if w["days"][:3] == dn]
        for k, w in enumerate(here):
            cls = "box" if w["src"] == "box" else "chat"
            out.append(f'<circle class="{cls}" cx="{x + 14 + k * 16:.1f}" cy="{y + 46}" r="6"/>')
    y += 82
    y = listed(weekly, y, lambda w: f"{w['days'][:3]} {w['hm']}")
    y += 16

    # the month strip
    out.append(text(24, y, "The month and the quarter", size=20, weight="700"))
    y += 16
    mw = (W - 48) / 31.0
    out.append(f'<rect class="panel" x="24" y="{y}" width="{W - 48}" height="34" rx="6"/>')
    for d in (1, 8, 15, 22, 29):
        out.append(text(24 + (d - 0.5) * mw, y + 23, str(d), "mute", 15, "middle"))
    monthly.sort(key=lambda m: (m.get("dom") or 99, m["name"]))
    for m in monthly:
        if m.get("dom"):
            cls = "box" if m["src"] == "box" else "chat"
            out.append(f'<circle class="{cls}" cx="{24 + (m["dom"] - 0.5) * mw:.1f}" '
                       f'cy="{y + 46}" r="6"/>')
    y += 82
    y = listed(monthly, y, lambda m: (f"day {m['dom']}, {m['hm']}" if m.get("dom") else
                                      f"quarterly, {m['hm']}" if m["kind"] == "quarterly"
                                      else f"by event, {m['hm']}"))
    y += 10
    out.append(text(24, y, "Times are ET. A task held in UTC moves an hour", "mute", 15))
    out.append(text(24, y + 22, "when daylight saving ends on 1 Nov.", "mute", 15))
    y += 40
    out.append("</svg>")
    return "\n".join(out).replace(f'viewBox="0 0 {W} {H}"', f'viewBox="0 0 {W} {y}"', 1) \
        .replace(f'height="{H}" rx="14"', f'height="{y}" rx="14"', 1)


# ---------------------------------------------------------------------------
# Figure 5: the library map
# ---------------------------------------------------------------------------
# numeral -> (group, books). The group is what the paper helps decide; the
# books are the Doctrine's four it serves. Refined against each paper's own
# "Companion to" column in the library guide.
GROUPS = [
    ("How to decide and judge evidence", ["XVIII", "XXXIII", "XIX", "XXIII", "XVII", "XXXII"]),
    ("The big frame (Book A, the Monthly)", ["XXVII", "I", "III", "IV", "II", "XX", "X",
                                              "XXXI"]),
    ("Asset classes (A's sleeves, B's non-equity)", ["V", "VI", "VII", "VIII", "IX",
                                                       "XXXIV", "XV", "XXI", "XXIV"]),
    ("Price, positioning, expression (B, C, D)", ["XXV", "XVI", "XIII", "XI", "XXII",
                                                    "XIV", "XII",
                                                    "XXX"]),
]
BOOKS = {
    "XVIII": "ABCD", "XXXIII": "ABCD", "XXXII": "ABCD", "XIX": "C", "XXIII": "ABCD", "XVII": "A",
    "XXVII": "A", "I": "A", "III": "A", "IV": "AB", "II": "AD", "XX": "AB", "X": "AB",
    "XXXI": "A",
    "V": "AB", "VI": "AB", "VII": "AB", "VIII": "AB", "IX": "AD", "XXXIV": "A",
    "XV": "AB", "XXI": "AB", "XXIV": "BC",
    "XXV": "BC", "XVI": "BCD", "XIII": "C", "XI": "CD", "XXII": "BCD", "XIV": "BC",
    "XII": "C",
    "XXX": "BCD",
}


def roster() -> dict[str, str]:
    """numeral -> short name, from the library guide's at-a-glance table."""
    lines = LIBRARY.read_text(encoding="utf-8").split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.startswith("| Layer | # | Paper |"))
    out = {}
    for ln in lines[start + 2:]:
        if not ln.startswith("|"):
            break
        c = ln.split("|")
        m = re.search(r"\*\*([IVX]+)\*\*", c[2])
        if m:
            out[m.group(1)] = c[4].strip().strip("*")
    return out


def library_svg() -> str:
    names = roster()
    missing = sorted(set(names) - {n for _, g in GROUPS for n in g})
    if missing:
        raise SystemExit(f"papers in the roster with no group: {missing}")
    W = 720
    out_rows: list[str] = []
    y = 100
    for title, nums in GROUPS:
        nums = [n for n in nums if n in names]
        h = 52 + 36 * len(nums) + 10
        out_rows.append(f'<rect class="panel" x="16" y="{y}" width="{W - 32}" height="{h}" rx="12"/>')
        out_rows.append(text(32, y + 32, title, "ink", 19, weight="700"))
        yy = y + 64
        for n in nums:
            out_rows.append(f'<rect class="pill" x="32" y="{yy - 22}" width="{W - 64}" '
                            f'height="30" rx="15"/>')
            out_rows.append(text(48, yy, f"{n}", "mute", 15, weight="700"))
            out_rows.append(text(110, yy, names[n], "ink", 17))
            for k, b in enumerate("ABCD"):
                bx = W - 168 + k * 34
                if b in BOOKS.get(n, ""):
                    out_rows.append(f'<circle class="b{b}" cx="{bx}" cy="{yy - 6}" r="13"/>')
                    out_rows.append(text(bx, yy - 1, b, "onbox", 14, "middle", "700"))
                else:
                    out_rows.append(f'<circle fill="none" class="grid" stroke-width="2" '
                                    f'cx="{bx}" cy="{yy - 6}" r="12"/>')
            yy += 36
        y += h + 16
    H = y + 24
    out = svg_open(W, H, "Figure 5. The library map",
                   "The 27 papers of the library in four groups by the decisions they "
                   "support, each with the books (A to D) it serves. Generated from the "
                   "library guide's roster.")
    out.append(text(24, 44, "Figure 5. The library map", size=24, weight="700"))
    out.append(text(24, 74, "Grouped by what each paper helps you decide; "
                            "filled letters are the books it serves.", "mute", 16))
    return "\n".join(out + out_rows + ["</svg>"])


def write(check: bool) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stale = 0
    for name, body in (("fig-02-clock.svg", clock_svg()), ("fig-05-library.svg", library_svg())):
        p = OUT / name
        if check:
            if not p.is_file() or p.read_text(encoding="utf-8") != body + "\n":
                print(f"stale: {p.relative_to(REPO).as_posix()}")
                stale += 1
        else:
            p.write_text(body + "\n", encoding="utf-8", newline="\n")
            print(f"wrote {p.relative_to(REPO).as_posix()}")
    return 1 if stale else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    sys.exit(write(ap.parse_args().check))

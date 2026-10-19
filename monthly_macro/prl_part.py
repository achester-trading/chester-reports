"""
THE MONTHLY'S DIGITAL ASSET MECHANISM WATCH PART (ST-14, the order's 2.7.6;
st-t5-render, 18 Oct 2026). Pearl, the Security Master's crypto.watch instrument.

Inside the Monthly's digital-assets material in the slow layers, after the crypto
data layer's tables. Report-only (MW-2): nothing here alters the composite, a
dial, an overlay or a band, and the thesis status prints with its trace as an
informational label, never as a recommendation.

  1  the thesis status with its rule trace and what moved, code-written lines
  2  the S1-S8 table: baseline (19 Sep 2026) / prior month / now / change, with
     "not tracked" and ESTIMATED where the inputs say so
  3  the supply figure (M13, monthly_macro/charts.py) only once the explorer has
     read; otherwise no figure and one line
  4  the candidates found this month and the status changes made (the
     mechanism-watch register, altdata/mechanism_watch.py)
  5  the narrative-register entries the scan drafted this month

IT READS, IT DOES NOT COMPUTE. Every figure is a stored row read as of the
cutoff: the calc.prl_* rows (altdata/prl.py writes them), the explorer's
pearl.chain_* rows and the crypto basket's PRL price -- nothing is derived here
but a change between two stored values. The Security Master entry is read
through its resolver.

THE GUARDS (the row's validators, which also run in tools/validate_st_t5_render.py):
  - the Security Master entry: coingecko_id "pearl-2" and name "Pearl", class
    crypto.watch -- else the part prints its refusal and nothing else;
  - the explorer's supply within 2% of the formula at the explorer's height;
  - every row read carries its available_at;
  - STALE, never empty: a calc.prl_* row older than its allowance prints its
    last value with its available_at and STALE.

No words count against the Monthly's 10,000 (tables and lines, no paragraph),
and no PRL string reaches any daily output: this module is the Monthly's.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

TITLE = "Digital Asset Mechanism Watch: Pearl"
TITLE_REGISTER = "Mechanism Watch: candidates and status changes"
TITLE_ENTRIES = "Mechanism Watch: narrative-register entries"
# The part prints after the last of the digital-assets material's sub-sections:
# the family block, the basket and the crypto data layer's tables.
AFTER_TITLES = ("Themes: digital", "Factor V: stablecoins", "Watch names:",
                "VC raises", "Token unlocks", "Unlocks")
STALE_DAYS = 3                    # the daily compute's allowance: a weekend and a day
SUPPLY_TOLERANCE_PCT = 2.0        # the row's validator
SIGNPOST_COLUMNS = ["Signpost", "Baseline (19 Sep 2026)", "Prior month", "Now", "Change"]
# The order's 2.7.3 baselines, as dated content.
BASELINE = {
    "S1": "1 (Together AI)",
    "S2": "none",
    "S3": "3 venues; top ~91%; no tier-1",
    "S4": "difficulty ~21.4M (block 113,770)",
    "S5": "overhang 38.9%; gap 57.7M",
    "S6": "~$1.00-1.15; ~1.04M PRL/day",
    "S7": "inference only; no incident known",
    "S8": "no funding news known",
}
NARRATIVE = "not read: a narrative signpost (manual input, fed by the scan)"


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
def _latest(st, key: str, at: str) -> Optional[dict]:
    rs = [r for r in st.as_of(key, at)
          if r.get("value_num") is not None or r.get("value_text")]
    return max(rs, key=lambda r: (str(r["observed_at"]), str(r["available_at"]))) \
        if rs else None


def _day(s: str) -> dt.date:
    return dt.date.fromisoformat(str(s)[:10])


def guard_master() -> list[str]:
    """The Security Master entry's guard: [] when it holds."""
    from altdata import security_master as sm                   # noqa: PLC0415
    try:
        e = sm.Master().by_coingecko("pearl-2")
    except Exception as exc:                                    # noqa: BLE001
        return [f"no Security Master entry resolves coingecko:pearl-2 ({type(exc).__name__})"]
    w = e.get("watch") or {}
    out = []
    if w.get("coingecko_id") != "pearl-2":
        out.append(f"its coingecko_id is {w.get('coingecko_id')!r}, not 'pearl-2'")
    if e.get("name") != "Pearl" or w.get("name") != "Pearl":
        out.append(f"its name is {e.get('name')!r}, not 'Pearl'")
    if e.get("asset_class") != "crypto.watch":
        out.append(f"its class is {e.get('asset_class')!r}, not crypto.watch")
    return out


def read(st, now: str, then: str) -> dict:
    """Every stored figure the part prints, now and at the prior month's cutoff,
    with its available_at; and the faults of the read guards."""
    from altdata import prl                                     # noqa: PLC0415
    keys = dict(prl.KEYS)
    keys.update({"height": prl.HEIGHT_KEY, "supply": prl.SUPPLY_KEY,
                 "difficulty": prl.DIFFICULTY_KEY, "price": "yfinance.crypto_prl"})
    out: dict[str, Any] = {"now": {}, "then": {}, "faults": [], "stale": []}
    for when, at in (("now", now), ("then", then)):
        for name, k in keys.items():
            r = _latest(st, k, at)
            if r is None:
                continue
            if not r.get("available_at"):
                out["faults"].append(f"{k}: a row without its available_at")
                continue
            out[when][name] = r
    sc = out["now"].get("supply_code")
    if sc and (_day(now) - _day(sc["available_at"])).days > STALE_DAYS:
        out["stale"].append(f"calc.prl_* last computed {str(sc['available_at'])[:10]}")
    h, s = out["now"].get("height"), out["now"].get("supply")
    if h and s and str(h["observed_at"])[:10] == str(s["observed_at"])[:10]:
        f = prl.supply_code(float(h["value_num"]))
        gap = 100.0 * (float(s["value_num"]) / f - 1.0)
        out["supply_check"] = {"pct": gap, "ok": abs(gap) <= SUPPLY_TOLERANCE_PCT}
        if abs(gap) > SUPPLY_TOLERANCE_PCT:
            out["faults"].append(
                f"the explorer's supply ({float(s['value_num']) / 1e6:,.2f}M) is "
                f"{gap:+.1f}% from the formula at its height "
                f"({int(h['value_num']):,}): outside {SUPPLY_TOLERANCE_PCT:g}%")
    return out


def explorer_read(st, now: str) -> bool:
    """Has the explorer stored a height and a supply? (M13 draws only then.)"""
    from altdata import prl                                     # noqa: PLC0415
    return bool(_latest(st, prl.HEIGHT_KEY, now) and _latest(st, prl.SUPPLY_KEY, now))


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def _v(r: Optional[dict]) -> Optional[float]:
    return None if not r or r.get("value_num") is None else float(r["value_num"])


def _estimated(rd: dict, when: str) -> bool:
    e, s = rd[when].get("height_estimated"), rd[when].get("supply_code")
    return bool(e and s and str(e["observed_at"])[:10] == str(s["observed_at"])[:10])


def _stale(rd: dict, when: str, name: str) -> str:
    r = rd[when].get(name)
    return (f" STALE (as of {str(r['available_at'])[:10]})"
            if when == "now" and rd["stale"] and r else "")


def _cell(rd: dict, when: str, name: str, fmt) -> str:
    r = rd[when].get(name)
    if r is None:
        return "not stored"
    est = " ESTIMATED" if name in ("supply_code", "overhang", "reward") and \
        _estimated(rd, when) else ""
    return fmt(float(r["value_num"])) + est + _stale(rd, when, name)


def _chg(a: Optional[float], b: Optional[float], fmt) -> str:
    if a is None or b is None:
        return "—"
    d = b - a
    return "unch" if abs(d) < 1e-12 else fmt(d)


def signpost_rows(rd: dict) -> list[list[str]]:
    def pct(v):
        return f"{v:.1f}%"

    def pp(v):
        return f"{v:+.1f} pp"
    nar = [NARRATIVE] * 2 + ["—"]
    s4_now = _cell(rd, "now", "difficulty", lambda v: f"difficulty {v / 1e6:,.1f}M")
    s4_then = _cell(rd, "then", "difficulty", lambda v: f"difficulty {v / 1e6:,.1f}M")
    if s4_now == "not stored":
        s4_now = "not stored: the explorer has not read (G-26)"
    d2n, d2t = _v(rd["now"].get("overhang")), _v(rd["then"].get("overhang"))
    gap = rd["now"].get("supply_gap")
    s5_now = (_cell(rd, "now", "overhang", lambda v: f"overhang {v:.1f}%") + "; gap "
              + (f"{_v(gap) / 1e6:,.1f}M" if gap else "ESTIMATED (the explorer has not read)"))
    s5_then = _cell(rd, "then", "overhang", lambda v: f"overhang {v:.1f}%")
    d4 = lambda v: f"emission-to-volume {v:.2f}"                 # noqa: E731
    pxn, pxt = _v(rd["now"].get("price")), _v(rd["then"].get("price"))
    s6_now = (_cell(rd, "now", "emission_to_volume", d4)
              + (f"; ${pxn:,.4f}" if pxn is not None else ""))
    s6_then = (_cell(rd, "then", "emission_to_volume", d4)
               + (f"; ${pxt:,.4f}" if pxt is not None else ""))
    return [
        ["S1 Paid-compute partners", BASELINE["S1"], *nar],
        ["S2 PRL demand sink", BASELINE["S2"], *nar],
        ["S3 Exchange access", BASELINE["S3"],
         "not tracked (source retired)", "not tracked (source retired): calc.prl_venue_conc",
         "—"],
        ["S4 Mining composition", BASELINE["S4"], s4_then,
         s4_now + "; pool share NOT AVAILABLE (G-27)",
         _chg(_v(rd["then"].get("difficulty")), _v(rd["now"].get("difficulty")),
              lambda v: f"{v / 1e6:+,.1f}M")],
        ["S5 Holder structure", BASELINE["S5"], s5_then, s5_now, _chg(d2t, d2n, pp)],
        ["S6 Price vs emission", BASELINE["S6"], s6_then, s6_now,
         _chg(pxt, pxn, lambda v: f"${v:+,.4f}")],
        ["S7 Technical and chain integrity", BASELINE["S7"], *nar],
        ["S8 Team, funding, regulatory", BASELINE["S8"], *nar],
    ]


def thesis_lines(rd: dict) -> list[str]:
    t = rd["now"].get("thesis_status")
    if not t:
        return ["Thesis status: not stored yet (the daily compute writes it)."]
    try:
        doc = json.loads(t.get("value_text") or "{}")
    except ValueError:
        doc = {}
    out = [f"Thesis status, an informational label by the rule of 2.7.5 with no "
           f"decision rights: {doc.get('status', 'unread')} (as of "
           f"{str(t['observed_at'])[:10]}){_stale(rd, 'now', 'thesis_status')}.",
           f"The rule's trace: {doc.get('trace', 'none stored')}"]
    tp = rd["then"].get("thesis_status")
    if tp:
        try:
            was = json.loads(tp.get("value_text") or "{}").get("status")
        except ValueError:
            was = None
        out.append(f"What moved: the status was {was} at the prior month's cutoff"
                   + ("; unchanged." if was == doc.get("status") else
                      f"; now {doc.get('status')}."))
    f = rd["now"].get("idle_gpu_flag")
    out.append("Idle-GPU flag (D6; Factor I attention, no scoring effect): "
               + ("not computed (difficulty or price over 30 days not stored)" if not f
                  else ("ON" if _v(f) else "off") + f" ({str(f['observed_at'])[:10]})")
               + ".")
    return out


# ---------------------------------------------------------------------------
# The part
# ---------------------------------------------------------------------------
def build(st, now: str, then: str, db_path: Optional[str] = None) -> list[dict]:
    """The part's sub-sections, in 2.7.6's order. Never raises."""
    g = guard_master()
    if g:
        return [{"title": TITLE, "paragraph_wanted": False,
                 "lines": ["Mechanism Watch not printed: the Security Master entry fails "
                           "its guard -- " + "; ".join(g) + "."]}]
    rd = read(st, now, then)
    lines = thesis_lines(rd)
    if rd["stale"]:
        lines.append("STALE: " + "; ".join(rd["stale"]) + " -- the last good values "
                     "print with their dates.")
    lines += [f"CHECK: {f}." for f in rd["faults"]]
    if explorer_read(st, now):
        if rd.get("supply_check", {}).get("ok"):
            lines.append(f"The explorer's supply is within {SUPPLY_TOLERANCE_PCT:g}% of "
                         f"the formula at its height ({rd['supply_check']['pct']:+.2f}%).")
    else:
        lines.append("Supply figure: not drawn -- the explorer has not read (G-26), so "
                     "the height and the supply here are ESTIMATED from the emission "
                     "formula.")
    part = {"title": TITLE, "paragraph_wanted": False, "lines": lines,
            "table": {"columns": list(SIGNPOST_COLUMNS), "rows": signpost_rows(rd)},
            "table_note": ("Baselines are the order's 19 Sep 2026 figures (2.7.3). Price "
                           "is Yahoo's at the basket's symbol; venues are not tracked "
                           "(CoinGecko retired, 18 Oct 2026); S1, S2, S7 and S8 are "
                           "narrative. A figure from an estimated height is marked "
                           "ESTIMATED. Report-only: nothing here alters the composite."),
            "data": {"prl": {w: {k: _v(v) for k, v in rd[w].items()} for w in ("now", "then")},
                     "faults": rd["faults"], "stale": rd["stale"]}}
    out = [part]
    start, end = then[:10], now[:10]
    try:
        from altdata import mechanism_watch as mw              # noqa: PLC0415
        with mw.Register(db_path, readonly=True) as reg:
            m = reg.month(start, end)
    except Exception:                                           # noqa: BLE001
        m = None
    if m is None:
        out.append({"title": TITLE_REGISTER, "paragraph_wanted": False,
                    "lines": ["The mechanism-watch register is not on the store yet "
                              "(the scan's first run creates it)."]})
        return out
    rows = [[c["id"], c["name"], c.get("mechanism_class") or "—", c.get("stage") or "—",
             c["status"] + (" (draft)" if c.get("draft") else "")]
            for c in m["candidates"]]
    ch = [f"{x['at'][:10]}: {x.get('name') or x['mw_id']} {x.get('from_status') or 'new'} "
          f"-> {x['to_status']} ({x['by']}: {x['reason']})." for x in m["changes"]]
    out.append({"title": TITLE_REGISTER, "paragraph_wanted": False,
                "table": ({"columns": ["ID", "Name", "Mechanism", "Stage", "Status"],
                           "rows": rows} if rows else None),
                "lines": (ch or ["No status change this month."])
                + ([] if rows else ["No candidate found this month."])})
    out.append({"title": TITLE_ENTRIES, "paragraph_wanted": False,
                "lines": [f"{e['at'][:10]} · class={e['cls']} · factor={e['factor']} · "
                          f"{e['grade']} · {e['text']} · {e['source']} (draft)"
                          for e in m["entries"]] or ["No entry drafted this month."]})
    return out

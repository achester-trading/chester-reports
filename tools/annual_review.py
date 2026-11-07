"""
The annual-review tooling: Instruments 2 and 3 of Audit 2 section 5.1 (the
library programme's L-5 and R-6, docs/change-order-library-programme-2026-11-06.md;
The Annual Structural Review's Part II). A131, 6 Nov 2026.

    python -m tools.annual_review figures [--paper SLUG] [--db PATH] [--date D] [--out DIR]
    python -m tools.annual_review relationships [--paper SLUG] [--db PATH] [--date D] [--out DIR]
    python -m tools.annual_review all [--db PATH] [--date D]        # make annual-review
    python -m tools.annual_review count                             # parse only, no store

INSTRUMENT 2, THE DATED-FIGURE RECOMPUTATION. Every figure in a paper's dated
appendices (config/annual_review.yaml `figures`) that names its series by the D7
convention -- "(FRED DGS10)" or a backticked store key -- with a value and a date
is recomputed from the point-in-time store as of its appendix's stated date
(available_at respected), diffed against the printed value under its family's
tolerance, and written to docs/reviews/annual-review-figures-<date>.md: a table
per paper (figure, printed, recomputed, diff, verdict), the unrecomputable list
(a figure with no series key, an unknown key or no date -- listed, never
guessed) and a one-line count.

INSTRUMENT 3, THE RELATIONSHIP HEALTH CHECK. Every relationship row in a paper's
Assumptions and Falsifiers appendix, part (b) -- two series, a sign or a range,
a window -- is recomputed over its stated window and over the trailing window to
the last stored month, and graded holding / weakening / broken / re-attached by
the config's rule. A paper with no such appendix is listed, never failed.
Written to docs/reviews/annual-review-relationships-<date>.md.

READ-ONLY. The store is opened `mode=ro`; no paper is ever written; nothing is
stored. NOT A GATE: `all` (the make target) always exits 0 and prints the two
paths, so the review never sets a CI exit code.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import sqlite3
import statistics
import sys
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import yaml

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CONFIG = REPO / "config" / "annual_review.yaml"
ET = ZoneInfo("America/New_York")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
GRADES = ("holding", "weakening", "broken", "re-attached")

# A number a reader would quote: a decimal, a % / bp / pp, or a $.
NUM_RE = re.compile(r"(?<![\w.])(\$)?([−-]?\d[\d,]*(?:\.\d+)?)\s*(%|bps?\b|pp\b)?")
DATE_RE = re.compile(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
                     r"\.?(?:\s+(\d{4}))?\b|\b(\d{4})-(\d{2})-(\d{2})\b")
FRED_RE = re.compile(r"\bFRED\s+([A-Z][A-Z0-9_]{2,})\b")
KEY_RE = re.compile(r"`([a-z][a-z0-9_]*\.[a-z0-9_.]+)`")
ASOF_RE = re.compile(r"as of\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})")
WINDOW_RE = re.compile(r"\b(\d{4})(?:-(\d{2}))?\s*(?:to|–|—|-)\s*(\d{4})(?:-(\d{2}))?\b")
RANGE_RE = re.compile(r"between\s+([−-]?\d*\.?\d+)\s+and\s+([−-]?\d*\.?\d+)")
LAG_RE = re.compile(r"\blag\s+(\d+)\s+months?\b", re.I)


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8")) or {}


def papers(cfg: dict, slug: Optional[str] = None, root: Path = REPO) -> list[Path]:
    out = sorted(root.glob(cfg.get("papers_glob") or "docs/whitepapers/*-whitepaper.md"))
    if slug:
        out = [p for p in out if p.name == f"{slug}-whitepaper.md" or p.stem == slug]
    return out


def _num(s: str) -> float:
    return float(s.replace(",", "").replace("−", "-"))


def _date(m: re.Match, year: Optional[int]) -> Optional[str]:
    if m.group(4):
        return f"{m.group(4)}-{m.group(5)}-{m.group(6)}"
    y = int(m.group(3)) if m.group(3) else year
    if not y:
        return None
    try:
        return dt.date(y, MONTHS[m.group(2).lower()[:3]], int(m.group(1))).isoformat()
    except ValueError:
        return None


def _long_date(s: str) -> Optional[str]:
    try:
        return dt.datetime.strptime(s, "%d %B %Y").date().isoformat()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Parsing: sections, sentences, keys
# ---------------------------------------------------------------------------
def sections(text: str, heading_re: str) -> list[tuple[int, str, list[tuple[int, str]]]]:
    """[(line number, heading, [(line number, line)])] for each level-2 section
    whose heading matches, to the next level-2 heading."""
    rx = re.compile(heading_re)
    out, cur = [], None
    for i, ln in enumerate(text.splitlines(), start=1):
        if ln.startswith("## "):
            cur = (i, ln, []) if rx.search(ln) else None
            if cur:
                out.append(cur)
            continue
        if cur is not None:
            cur[2].append((i, ln))
    return out


def sentences(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Paragraphs joined (blockquote marks and emphasis dropped), then split into
    sentences, each with the line number it starts on."""
    paras, buf, start = [], [], None
    for i, ln in lines:
        s = re.sub(r"^\s*>\s?", "", ln).strip()
        if not s or s.startswith("#") or set(s) <= {"-", "|", " ", ":"}:
            if buf:
                paras.append((start, " ".join(buf)))
            buf, start = [], None
            continue
        if start is None:
            start = i
        buf.append(s)
    if buf:
        paras.append((start, " ".join(buf)))
    out = []
    for i, p in paras:
        p = re.sub(r"(?<!\*)\*(?!\*)|\*\*", "", p)
        for s in re.split(r"(?<=[.;])\s+(?=[A-Z(\"'*])", p):
            if s.strip():
                out.append((i, s.strip()))
    return out


def fred_map() -> dict[str, str]:
    from altdata import config as acfg                          # noqa: PLC0415
    return {s.fred_id: f"fred.{s.key}" for s in acfg.FRED_PULL_SERIES}


_REG: Optional[set] = None


def registered(key: str) -> bool:
    """Is a backticked token a registered store key? (A file name or a config
    path in backticks is not a series.)"""
    global _REG
    if _REG is None:
        _REG = set(fred_map().values())
    if key in _REG:
        return True
    try:
        from altdata import derived                             # noqa: PLC0415
        return bool(derived.registry_entry(key))
    except Exception:                                           # noqa: BLE001
        return False


def keys_in(s: str, fmap: dict[str, str]) -> list[tuple[int, str, Optional[str]]]:
    """[(position, label, store key or None)] for each series named: "FRED <ID>"
    (None when the pull does not carry the ID) or a backticked registered key."""
    out = [(m.start(), f"FRED {m.group(1)}", fmap.get(m.group(1))) for m in FRED_RE.finditer(s)]
    out += [(m.start(), m.group(1), m.group(1)) for m in KEY_RE.finditer(s)
            if registered(m.group(1))]
    return sorted(out)


# A value is paired with a date only when the date follows it as "on <date>" (or
# "at <date>"), or precedes it as "<date> (<value>)"; otherwise only a sentence's
# single date is used. "5.25% in the week of 5 Oct" is not a close on 5 Oct.
ON_RE = re.compile(r"^\s*(?:,\s*)?(?:on|at)\s+$")


def figure_tokens(s: str) -> list[tuple[int, float, str]]:
    """[(position, value, unit)] for the numbers a reader would quote, dates and
    identifiers excluded."""
    spans = [m.span() for m in DATE_RE.finditer(s)] + \
        [m.span() for m in FRED_RE.finditer(s)] + [m.span() for m in KEY_RE.finditer(s)]
    out = []
    for m in NUM_RE.finditer(s):
        if any(a <= m.start() < b for a, b in spans):
            continue
        dollar, raw, unit = m.group(1), m.group(2), (m.group(3) or "").lower()
        if not (dollar or unit or "." in raw):
            continue
        if re.search(r"(SR|ST|OS|D|V|L|R|item|items|Batch|batch|Part|§)[-\s]?$",
                     s[max(0, m.start() - 8):m.start()]):
            continue
        try:
            v = _num(raw)
        except ValueError:
            continue
        out.append((m.start(), v, "$" if dollar else unit))
    return out


# ---------------------------------------------------------------------------
# Instrument 2: the figures
# ---------------------------------------------------------------------------
def parse_figures(path: Path, cfg: dict, fmap: Optional[dict] = None) -> dict:
    """{figures: [...], unrecomputable: [...], appendices: n}."""
    fmap = fred_map() if fmap is None else fmap
    fc = cfg.get("figures") or {}
    text = path.read_text(encoding="utf-8")
    figs, unrec = [], []
    secs = sections(text, fc.get("appendix_heading") or r"^## Appendix\b.*\b[Dd]ated\b")
    for hline, heading, lines in secs:
        am = ASOF_RE.search(heading)
        asof = _long_date(am.group(1)) if am else None
        hyear = int(asof[:4]) if asof else None
        for ln, s in sentences(lines):
            toks = figure_tokens(s)
            if not toks:
                continue
            ks = keys_in(s, fmap)
            dates = [(m.start(), m) for m in DATE_RE.finditer(s)]
            years = [int(m.group(3)) for _, m in dates if m.group(3)] or \
                    [int(m.group(4)) for _, m in dates if m.group(4)]
            syear = years[0] if years else hyear
            for pos, val, unit in toks:
                ex = s if len(s) <= 160 else s[:157] + "..."
                base = {"paper": path.name, "line": ln, "appendix": heading[3:].strip(),
                        "text": ex, "printed": val, "unit": unit, "as_of": asof}
                prior = [k for k in ks if k[0] < pos]
                key = (prior[-1] if prior else (ks[0] if ks else None))
                if key is None:
                    unrec.append({**base, "reason": "no series key in the sentence"})
                    continue
                if key[2] is None:
                    unrec.append({**base, "reason": f"{key[1]} is not a stored series"})
                    continue
                num_end = pos + len(NUM_RE.match(s, pos).group(0))
                after = [m for p, m in dates
                         if 0 <= p - num_end <= 6 and ON_RE.match(s[num_end:p])]
                before = [m for p, m in dates
                          if m.end() <= pos and re.fullmatch(r"\s*\(\s*", s[m.end():pos])]
                d = (_date(after[0], syear) if after else
                     _date(before[-1], syear) if before else None)
                if (d is None and len(dates) == 1 and len(toks) == 1
                        and re.search(r"\b[Oo]n\s+$", s[:dates[0][0]])):
                    # one figure and one date, the date said as "on <date>"
                    # ("On 5 Oct 2026 the 10-year closed at 4.50%"): unambiguous.
                    # "in the week of <date>" is not.
                    d = _date(dates[0][1], syear)
                if d is None:
                    unrec.append({**base, "reason": "no date for the value"})
                    continue
                figs.append({**base, "series": key[1], "key": key[2], "date": d})
    return {"figures": figs, "unrecomputable": unrec, "appendices": len(secs)}


def ro(db: Optional[str]) -> Optional[sqlite3.Connection]:
    from altdata import observations                            # noqa: PLC0415
    p = Path(db or observations.DEFAULT_DB)
    if not p.is_file():
        return None
    return sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)


def cutoff_of(asof: Optional[str], figure_date: str, grace_days: int) -> str:
    """End of the as-of day ET, in UTC; the figure's date plus the grace when the
    appendix states none."""
    d = dt.date.fromisoformat(asof) if asof else \
        dt.date.fromisoformat(figure_date) + dt.timedelta(days=grace_days)
    end = dt.datetime.combine(d, dt.time(23, 59, 59), tzinfo=ET)
    return end.astimezone(dt.timezone.utc).isoformat()


def value_at(conn: sqlite3.Connection, key: str, day: str, cutoff: str) -> Optional[float]:
    """The newest vintage of `key`'s observation AT `day`, knowable at `cutoff`."""
    rows = conn.execute(
        "SELECT value_num, available_at FROM observations WHERE registry_key = ? "
        "AND substr(observed_at, 1, 10) = ? AND value_num IS NOT NULL",
        (key, day)).fetchall()
    ok = [(a, v) for v, a in rows if _instant(a) <= _instant(cutoff)]
    return max(ok)[1] if ok else None


def _instant(s: str) -> dt.datetime:
    x = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)


def family(key: str) -> Optional[str]:
    try:
        from altdata import derived                             # noqa: PLC0415
        return derived.family_of(key)[0]
    except Exception:                                           # noqa: BLE001
        return None


def judge(printed: float, unit: str, recomputed: Optional[float], fam: Optional[str],
          cfg: dict) -> tuple[Optional[float], str]:
    """(diff, verdict) under the family's tolerance."""
    if recomputed is None:
        return None, "not stored at its date"
    p = printed / 100.0 if unit in ("bp", "bps") else printed
    diff = recomputed - p
    tol = (cfg.get("figures") or {}).get("tolerance") or {}
    t = tol.get(fam or "default") or tol.get("default") or {"rel": 0.01}
    lim = t["abs"] if "abs" in t else abs(p) * float(t["rel"])
    return diff, ("within tolerance" if abs(diff) <= lim + 1e-12 else "beyond tolerance")


def run_figures(cfg: dict, db: Optional[str], slug: Optional[str] = None,
                root: Path = REPO) -> dict:
    fc = cfg.get("figures") or {}
    fmap = fred_map()
    conn = ro(db)
    per: dict[str, dict] = {}
    try:
        for p in papers(cfg, slug, root):
            parsed = parse_figures(p, cfg, fmap)
            for f in parsed["figures"]:
                if conn is None:
                    f["recomputed"], f["diff"], f["verdict"] = None, None, "no store"
                    continue
                cut = cutoff_of(f["as_of"], f["date"], int(fc.get("grace_days", 7)))
                f["cutoff"] = cut
                v = value_at(conn, f["key"], f["date"], cut)
                f["recomputed"] = v
                f["family"] = family(f["key"])
                f["diff"], f["verdict"] = judge(f["printed"], f["unit"], v, f["family"], cfg)
            per[p.name] = parsed
    finally:
        if conn is not None:
            conn.close()
    return per


def _fmt(v: Optional[float], nd: int = 4) -> str:
    return "—" if v is None else f"{v:,.{nd}f}".rstrip("0").rstrip(".")


def figures_md(per: dict, day: str, db: Optional[str]) -> str:
    nf = sum(len(x["figures"]) for x in per.values())
    nu = sum(len(x["unrecomputable"]) for x in per.values())
    beyond = sum(1 for x in per.values() for f in x["figures"]
                 if f.get("verdict") == "beyond tolerance")
    L = [f"# Annual review: the dated-figure recomputation ({day})", "",
         "Instrument 2 of the Annual Structural Review (Audit 2 section 5.1; the library "
         "programme's L-5). Each figure a dated appendix names by its series is "
         "recomputed from the point-in-time store as of its appendix's stated date, "
         "available_at respected, and compared under its family's tolerance "
         "(`config/annual_review.yaml`). Read-only: no paper is changed.", "",
         f"**Count:** {nf} recomputable figure(s) in {len(per)} paper(s); "
         f"{beyond} beyond tolerance; {nu} unrecomputable.", "",
         f"Store: `{db or 'the default store'}`.", ""]
    for name, x in per.items():
        if not x["figures"]:
            continue
        L += [f"## {name}", "",
              "| Line | Figure | Series | Date | Printed | Recomputed | Diff | Verdict |",
              "|---|---|---|---|---|---|---|---|"]
        for f in x["figures"]:
            L.append(f"| {f['line']} | {f['text'].replace('|', '/')} | {f['series']} | "
                     f"{f['date']} | {_fmt(f['printed'])}{f['unit'] if f['unit'] not in ('$',) else ''} "
                     f"| {_fmt(f.get('recomputed'))} | {_fmt(f.get('diff'))} | "
                     f"{f.get('verdict')} |")
        L.append("")
    L += ["## Unrecomputable", "",
          "Listed, never guessed: a figure without a series key in its sentence, with a "
          "key the store does not carry, or without a date.", "",
          "| Paper | Line | Reason | Text |", "|---|---|---|---|"]
    for name, x in per.items():
        for u in x["unrecomputable"]:
            L.append(f"| {name} | {u['line']} | {u['reason']} | "
                     f"{u['text'].replace('|', '/')} |")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# Instrument 3: the relationships
# ---------------------------------------------------------------------------
def parse_relationships(path: Path, cfg: dict, fmap: Optional[dict] = None) -> dict:
    """{has_appendix, rows: [...], unparsed: [...]}"""
    fmap = fred_map() if fmap is None else fmap
    rc = cfg.get("relationships") or {}
    text = path.read_text(encoding="utf-8")
    secs = sections(text, rc.get("appendix_heading") or r"^## Appendix\b.*Assumptions and Falsifiers")
    if not secs:
        return {"has_appendix": False, "has_part_b": False, "rows": [], "unparsed": []}
    start = re.compile(rc.get("part_b_start") or r"^\*\*(\(b\)|Regularities)")
    end = re.compile(rc.get("part_end") or r"^\*\*\([c-e]\)")
    rows, unparsed, has_b = [], [], False
    for _, _, lines in secs:
        inb = False
        for ln, raw in lines:
            s = raw.strip()
            if start.search(s):
                inb, has_b = True, True
            elif inb and end.search(s):
                inb = False
            if not inb or not s:
                continue
            body = re.sub(r"\*\*|(?<!\*)\*(?!\*)", "", s)
            ks = [k for k in keys_in(body, fmap)]
            win = WINDOW_RE.search(body)
            rng = RANGE_RE.search(body)
            sign = (1 if re.search(r"\bpositive\b", body, re.I) else
                    -1 if re.search(r"\bnegative\b", body, re.I) else None)
            claimish = bool(ks) or bool(win) or sign is not None or bool(rng) \
                or len(body) > 20
            if len(ks) >= 2 and win and (sign is not None or rng) \
                    and all(k[2] for k in ks[:2]):
                lag = LAG_RE.search(body)
                rows.append({"paper": path.name, "line": ln, "text": body[:160],
                             "a": ks[0][2], "b": ks[1][2],
                             "a_label": ks[0][1], "b_label": ks[1][1],
                             "start": f"{win.group(1)}-{win.group(2) or '01'}",
                             "end": f"{win.group(3)}-{win.group(4) or '12'}",
                             "sign": sign if not rng else None,
                             "range": (sorted((_num(rng.group(1)), _num(rng.group(2))))
                                       if rng else None),
                             "lag": int(lag.group(1)) if lag else 0,
                             "levels": bool(re.search(r"\blevels\b", body, re.I))})
            elif claimish and (not start.search(s) or len(body) > 40):
                # Every other line of part (b) is listed with why it is not a
                # relationship row (the part's own heading line only when it
                # carries a claim of its own).
                why = ("a claim in prose: no stored series named" if not ks else
                       "fewer than two stored series" if len(ks) < 2
                       or not all(k[2] for k in ks[:2]) else
                       "no window" if not win else "no sign or range")
                unparsed.append({"paper": path.name, "line": ln, "text": body[:160],
                                 "reason": why})
    return {"has_appendix": True, "has_part_b": has_b, "rows": rows, "unparsed": unparsed}


def monthly(conn: sqlite3.Connection, key: str) -> dict[str, float]:
    """The newest vintage of each observation, the last of each month."""
    rows = conn.execute(
        "SELECT substr(observed_at, 1, 10), value_num, available_at FROM observations "
        "WHERE registry_key = ? AND value_num IS NOT NULL ORDER BY observed_at, available_at",
        (key,)).fetchall()
    day: dict[str, float] = {}
    for d, v, _ in rows:
        day[d] = float(v)
    out: dict[str, float] = {}
    for d in sorted(day):
        out[d[:7]] = day[d]
    return out


def _months(a: str, b: str) -> list[str]:
    y, m = int(a[:4]), int(a[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def _shift(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7]) + k
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"


def corr_window(a: dict, b: dict, start: str, end: str, lag: int, levels: bool
                ) -> tuple[Optional[float], int]:
    xs, ys = [], []
    for ym in _months(start, end):
        prev, nb, nbp = _shift(ym, -1), _shift(ym, lag), _shift(ym, lag - 1)
        if levels:
            if ym in a and nb in b:
                xs.append(a[ym])
                ys.append(b[nb])
        elif ym in a and prev in a and nb in b and nbp in b:
            xs.append(a[ym] - a[prev])
            ys.append(b[nb] - b[nbp])
    n = len(xs)
    if n < 3:
        return None, n
    try:
        return statistics.correlation(xs, ys), n
    except statistics.StatisticsError:
        return None, n


def grade(row: dict, stated: Optional[float], trailing: Optional[float],
          middle: Optional[float], n_s: int, n_t: int, n_m: int, cfg: dict) -> str:
    rc = cfg.get("relationships") or {}
    need = int(rc.get("min_months", 24))
    if stated is None or trailing is None or n_s < need or n_t < need:
        return f"insufficient (n={min(n_s, n_t)} of {need})"
    wr, mn = float(rc.get("weak_ratio", 0.5)), float(rc.get("min_abs", 0.10))
    if row.get("range"):
        lo, hi = row["range"]
        claim_sign = 1 if (lo + hi) / 2 >= 0 else -1
        inside = lo <= trailing <= hi
        mid_out = (middle is not None and n_m >= need and not (lo <= middle <= hi)
                   and math.copysign(1, middle) != claim_sign)
    else:
        claim_sign = row["sign"]
        inside = (math.copysign(1, trailing) == claim_sign and abs(trailing) >= mn
                  and abs(trailing) >= wr * abs(stated))
        mid_out = (middle is not None and n_m >= need
                   and math.copysign(1, middle) != claim_sign)
    if math.copysign(1, trailing) != claim_sign and abs(trailing) >= mn:
        return "broken"
    if inside:
        return "re-attached" if mid_out else "holding"
    return "weakening"


def run_relationships(cfg: dict, db: Optional[str], slug: Optional[str] = None,
                      root: Path = REPO, today: Optional[str] = None) -> dict:
    rc = cfg.get("relationships") or {}
    fmap = fred_map()
    conn = ro(db)
    per: dict[str, dict] = {}
    try:
        for p in papers(cfg, slug, root):
            parsed = parse_relationships(p, cfg, fmap)
            for r in parsed["rows"]:
                if conn is None:
                    r["grade"] = "no store"
                    continue
                a, b = monthly(conn, r["a"]), monthly(conn, r["b"])
                last = min(max(a) if a else "0000-00", max(b) if b else "0000-00")
                if today:
                    last = min(last, today[:7])
                t_start = _shift(last, -12 * int(rc.get("trailing_years", 3)) + 1)
                rs, ns = corr_window(a, b, r["start"], r["end"], r["lag"], r["levels"])
                rt, nt = corr_window(a, b, t_start, last, r["lag"], r["levels"])
                m_start, m_end = _shift(r["end"], 1), _shift(t_start, -1)
                rm, nm = (corr_window(a, b, m_start, m_end, r["lag"], r["levels"])
                          if m_start <= m_end else (None, 0))
                r.update(stated_rho=rs, n_stated=ns, trailing_rho=rt, n_trailing=nt,
                         trailing=f"{t_start} to {last}", middle_rho=rm, n_middle=nm)
                r["grade"] = grade(r, rs, rt, rm, ns, nt, nm, cfg)
            per[p.name] = parsed
    finally:
        if conn is not None:
            conn.close()
    return per


def relationships_md(per: dict, day: str, db: Optional[str]) -> str:
    rows = [r for x in per.values() for r in x["rows"]]
    without = [n for n, x in per.items() if not x["has_appendix"] or not x["has_part_b"]]
    counts = {g: sum(1 for r in rows if r.get("grade") == g) for g in GRADES}
    L = [f"# Annual review: the relationship health check ({day})", "",
         "Instrument 3 of the Annual Structural Review (Audit 2 section 5.1; the library "
         "programme's L-5). Each relationship row in an Assumptions and Falsifiers "
         "appendix's part (b) is recomputed over its stated window and the trailing "
         "window to the last stored month, and graded by `config/annual_review.yaml`'s "
         "rule. Broken claims are the review's first agenda item. Read-only.", "",
         f"**Count:** {len(rows)} relationship(s): "
         + ", ".join(f"{counts[g]} {g}" for g in GRADES)
         + f"; {len(without)} paper(s) without an Appendix A(b), listed below.", "",
         f"Store: `{db or 'the default store'}`.", ""]
    if rows:
        L += ["| Paper | Line | Claim | Window | Stated ρ (n) | Trailing | Trailing ρ (n) "
              "| Between ρ (n) | Grade |", "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            def rho(v, n):
                return f"{v:+.2f} ({n})" if v is not None else f"— ({n})"
            L.append(f"| {r['paper']} | {r['line']} | {r['text'].replace('|', '/')} | "
                     f"{r['start']} to {r['end']} | {rho(r.get('stated_rho'), r.get('n_stated', 0))} "
                     f"| {r.get('trailing', '—')} | {rho(r.get('trailing_rho'), r.get('n_trailing', 0))} "
                     f"| {rho(r.get('middle_rho'), r.get('n_middle', 0))} | **{r.get('grade')}** |")
        L.append("")
    unp = [u for x in per.values() for u in x["unparsed"]]
    if unp:
        L += ["## Claims in part (b) not in the relationship form", "",
              "| Paper | Line | Reason | Text |", "|---|---|---|---|"]
        L += [f"| {u['paper']} | {u['line']} | {u['reason']} | {u['text'].replace('|', '/')} |"
              for u in unp]
        L.append("")
    L += ["## Papers without an Appendix A(b)", "",
          "Listed, not failed (the Annual Structural Review's section 15: the first "
          "review writes the appendix).", ""]
    L += [f"- {n}" + (" (an Assumptions and Falsifiers appendix without a part (b))"
                      if per[n]["has_appendix"] else "") for n in without]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
def _write(md: str, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / name
    p.write_text(md, encoding="utf-8", newline="\n")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.annual_review")
    ap.add_argument("cmd", choices=["figures", "relationships", "all", "count"])
    ap.add_argument("--paper", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    cfg = config()
    day = a.date or dt.datetime.now(ET).date().isoformat()
    out = Path(a.out) if a.out else REPO / (cfg.get("out_dir") or "docs/reviews")
    if a.cmd == "count":
        fmap = fred_map()
        nf = nu = nr = nup = 0
        without = 0
        for p in papers(cfg, a.paper):
            f = parse_figures(p, cfg, fmap)
            r = parse_relationships(p, cfg, fmap)
            nf += len(f["figures"])
            nu += len(f["unrecomputable"])
            nr += len(r["rows"])
            nup += len(r["unparsed"])
            without += 0 if (r["has_appendix"] and r["has_part_b"]) else 1
        print(f"figures: {nf + nu} found, {nf} recomputable, {nu} unrecomputable; "
              f"regularities: {nr} in the relationship form, {nup} claims not in it; "
              f"{without} paper(s) without an Appendix A(b)")
        return 0
    paths = []
    try:
        if a.cmd in ("figures", "all"):
            paths.append(_write(figures_md(run_figures(cfg, a.db, a.paper), day, a.db),
                                out, f"annual-review-figures-{day}.md"))
        if a.cmd in ("relationships", "all"):
            paths.append(_write(relationships_md(run_relationships(cfg, a.db, a.paper),
                                                 day, a.db),
                                out, f"annual-review-relationships-{day}.md"))
    except Exception as exc:                                    # noqa: BLE001
        print(f"annual review: {type(exc).__name__}: {exc}")
        if a.cmd != "all":
            return 1
    for p in paths:
        print(p.relative_to(REPO) if p.is_relative_to(REPO) else p)
    # NOT A GATE: the make target never sets an exit code.
    return 0


if __name__ == "__main__":
    sys.exit(main())

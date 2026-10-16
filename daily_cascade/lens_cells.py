"""
THE LENS COLUMNS, formatted once (6e; part 1 in monthly_macro/writer/render_v2.py,
moved here by 6e, the rest, 16 Oct 2026, so the Weekly and the close print the
same cells the Monthly v2 tables print). Formatting only: every figure is
altdata/derived.py lens_forms()'s, and nothing here computes a delta, a percentile
or a flag.

    cell(lens, col)      one column's cell, or None (n/a; its reason is the lens's)
    flags(lens)          the flag words
    reason_for(lens, col)  the reason a None cell carries
    compact(lens)        one short cell for a table that has room for one column:
                         each family's headline forms (the Weekly and the close)
    anchor_line(lens)    the 10-year's anchors and fair value, one line
"""

from __future__ import annotations

from typing import Any, Optional

LENS_ORDER = ("price", "rate", "spread", "release", "quantity", "conditions", "ratio")
LENS_COLUMNS: dict[str, list[tuple[str, Any]]] = {
    "price": [("1m", "return_1m"), ("3m", "return_3m"), ("12m", "return_12m"),
              ("YTD", "return_ytd"), ("From 52w high", "drawdown_52w"),
              ("Vol 20d (pctile)", "vol"), ("12m return pctile", "r12p")],
    "rate": [("1m", "change_1m_bp"), ("3m", "change_3m_bp"), ("12m", "change_12m_bp"),
             ("Pctile 5y", "p5"), ("Pctile long", "pl")],
    "spread": [("1m", "change_1m_bp"), ("3m", "change_3m_bp"), ("Pctile 5y", "p5"),
               ("Pctile long", "pl")],
    "release": [("YoY", "yoy"), ("3m ann. / 3m chg", "m3"), ("Surprise", "surprise"),
                ("Revision", "revision"), ("Level pctile", "p5opt")],
    "quantity": [("YoY", "yoy_pct"), ("3m change", "change_3m_units"),
                 ("Direction", "direction")],
    "conditions": [("Pctile 5y", "p5"), ("Pctile long", "pl"), ("z (5y)", "z_5y"),
                   ("vs 1y avg", "spike_vs_1y_avg_pct")],
    "ratio": [("Pctile 5y", "p5"), ("Pctile long", "pl"), ("3m trend", "trend_3m")],
}
REASON_KEY = {"p5": "pctile_5y", "p5opt": "pctile_5y", "pl": "pctile_long",
              "vol": "realized_vol_20d", "r12p": "return_12m_pctile",
              "m3": "annualized_3m"}
# The compact cell's columns, per family: the forms that say most about the family
# in one cell (the brief's lens table, first columns first).
COMPACT = {"price": ("drawdown_52w", "r12p"), "rate": ("p5", "pl"),
           "spread": ("change_3m_bp", "p5"), "release": ("yoy", "m3"),
           "quantity": ("yoy_pct", "direction"), "conditions": ("p5", "z_5y"),
           "ratio": ("p5", "trend_3m")}


def _v(x: Any, dp: int = 2, dash: str = "—") -> str:
    if x is None or x == "":
        return dash
    try:
        return f"{float(x):,.{dp}f}"
    except (TypeError, ValueError):
        return str(x)


def _signed(x: Any, dp: int = 2) -> str:
    try:
        return f"{float(x):+,.{dp}f}"
    except (TypeError, ValueError):
        return "—"


def _pct_cell(f: dict, tag: str, short: bool = False) -> Optional[str]:
    if f.get(tag) is None:
        return None
    if short:
        return f"{f.get(tag + '_ordinal')} ({f.get(tag + '_window')})"
    return f"{f.get(tag + '_ordinal')} ({f.get(tag + '_window')}, n={f.get(tag + '_n')})"


def cell(lens: dict, col: str, short: bool = False) -> Optional[str]:
    f = lens.get("forms") or {}
    if col in ("p5", "p5opt"):
        return _pct_cell(f, "pctile_5y", short)
    if col == "pl":
        return _pct_cell(f, "pctile_long", short)
    if col == "vol":
        if f.get("realized_vol_20d") is None:
            return None
        return (f"{_v(f['realized_vol_20d'], 1)}% "
                f"({f.get('realized_vol_20d_pctile_ordinal') or 'n/a'})")
    if col == "r12p":
        if f.get("return_12m_pctile") is None:
            return None
        if short:
            return f"12m return {f['return_12m_pctile_ordinal']} pctile"
        return f"{f['return_12m_pctile_ordinal']} (n={f.get('return_12m_pctile_n')})"
    if col == "m3":
        if f.get("annualized_3m") is not None:
            return f"{_signed(f['annualized_3m'], 1)}% ann."
        if f.get("change_3m") is not None:
            return f"{_signed(f['change_3m'], 2)} pp"
        return None
    if col == "surprise" and f.get("surprise") is None and f.get("surprise_state"):
        return str(f["surprise_state"])            # ruling (d)6: "no consensus"
    v = f.get(col)
    if v is None:
        return None
    if col.endswith("_bp"):
        return f"{_signed(v, 0)} bp"
    if col in ("return_1m", "return_3m", "return_12m", "return_ytd", "drawdown_52w",
               "yoy_pct", "spike_vs_1y_avg_pct"):
        return f"{_signed(v, 1)}%"
    if col == "yoy":
        return f"{_signed(v, 2)} pp" if f.get("yoy_unit") == "pp" else f"{_signed(v, 1)}%"
    if col == "change_3m_units":
        return f"{_signed(v, 1)} {f.get('change_3m_units_unit') or ''}".strip()
    if col == "z_5y":
        return _signed(v, 2)
    if col == "trend_3m":
        return f"{_signed(v, 3)} ({f.get('trend_3m_direction')})"
    if col == "surprise":
        return f"{_signed(v, 2)} vs {_v(f.get('consensus'))}"
    return str(v)


def reason_for(lens: dict, col: str) -> Optional[str]:
    rs = lens.get("reasons") or {}
    why = rs.get(REASON_KEY.get(col, col))
    if not why and col == "m3":
        why = rs.get("change_3m")
    return why


def flags(lens: dict) -> str:
    fl = lens.get("flags") or {}
    words = [w for w, on in (("**bear**", fl.get("bear")),
                             ("**correction**", fl.get("correction") and not fl.get("bear")),
                             ("**widening**", fl.get("widening")),
                             ("**sign flipped**", fl.get("sign_flipped")),
                             ("5y/long disagree", fl.get("percentiles_disagree"))) if on]
    return ", ".join(words) or "—"


def compact(lens: Optional[dict]) -> str:
    """One cell: the family's two headline forms and any flag. n/a where neither
    form computes; a series with no family says so."""
    if not lens or not lens.get("family"):
        return "—"
    fam = lens["family"]
    parts = [c for c in (cell(lens, k, short=True) for k in COMPACT.get(fam, ())) if c]
    if fam == "rate" and len(parts) == 2:
        parts = [f"pctile {parts[0]}, {parts[1]}"]
    fl = flags(lens)
    if fl != "—":
        parts.append(fl.replace("**", ""))
    return "; ".join(parts) if parts else "n/a"


def anchor_line(lens: dict) -> Optional[str]:
    """The 10-year's anchors (SR-43) and fair value, one line, or None when the
    lens carries no anchor forms."""
    f, r = lens.get("forms") or {}, lens.get("reasons") or {}
    if "anchors_tag" not in f:
        return None
    bits = []
    if f.get("inflation_anchor_gap_bp") is not None:
        bits.append(f"inflation anchor {_v(f['inflation_anchor_pct'])}% "
                    f"({_signed(f['inflation_anchor_gap_bp'], 0)} bp)")
    else:
        bits.append(f"inflation anchor n/a ({r.get('inflation_anchor_gap_bp')})")
    if f.get("fair_value_inflation_pct") is not None:
        bits.append(f"fair value on the inflation fit {_v(f['fair_value_inflation_pct'])}% "
                    f"({_signed(f['fair_value_inflation_gap_bp'], 0)} bp)")
    if f.get("fair_value_fiscal_pct") is not None:
        bits.append(f"on the twin-deficit fit {_v(f['fair_value_fiscal_pct'])}% "
                    f"(fitted less market {_signed(f['fair_value_fiscal_gap_bp'], 0)} bp, "
                    f"n={f.get('fair_value_fiscal_n')})")
    else:
        bits.append(f"twin-deficit fit n/a ({r.get('fair_value_fiscal_pct')})")
    if f.get("term_premium_pct") is not None:
        bits.append(f"term premium {_v(f['term_premium_pct'])}%")
    return "The 10-year's anchors: " + "; ".join(bits) + f" {f.get('anchors_tag') or ''}".rstrip() + "."


# ---------------------------------------------------------------------------
# THE LENS TABLE for a section that had none (6e, the rest: the Weekly's and the
# close's adoption, the brief's "later"). A table, so it is data: it adds no prose
# word and no chart to either budget. The figures are lens_forms()'s, the same
# call the Monthly v2 tables make, so a series reads the same in every report.
# ---------------------------------------------------------------------------
LENS_TABLE_TITLE = "The lenses: each series measured its own way"
LENS_TABLE_NOTE = ("Each family shows its own forms (the metric lenses, ratified 4 Oct "
                   "2026): rates their five-year and long percentiles, spreads the "
                   "three-month change, releases year over year and three months "
                   "annualized, prices the distance from the 52-week high.")


def lens_rows(lenses: list[tuple[str, dict]]) -> list[list[str]]:
    return [[label, lens.get("family") or "—", compact({**lens, "flags": {}}),
             flags(lens).replace("**", "")] for label, lens in lenses]


def lens_table(st, cutoff: str, keys: list[tuple[str, str]]) -> Optional[dict]:
    """A sub-section: one row per (key, label) with a lens, or None when none
    of the keys has a level knowable at the cutoff."""
    from altdata import derived                                  # noqa: PLC0415
    got = []
    for key, label in keys:
        try:
            lens = derived.lens_forms(key, cutoff, store=st)
        except Exception:                                        # noqa: BLE001
            continue
        if lens.get("level") is not None:
            got.append((label, lens))
    if not got:
        return None
    lines = [al for al in (anchor_line(lens) for _, lens in got) if al]
    return {"title": LENS_TABLE_TITLE, "paragraph_wanted": False,
            "table": {"columns": ["Series", "Family", "Lens", "Flags"],
                      "rows": lens_rows(got)},
            "table_note": LENS_TABLE_NOTE, "lines": lines,
            "data": {"lenses": {label: {"family": lens.get("family"),
                                        "forms": lens.get("forms"),
                                        "flags": lens.get("flags")}
                                for label, lens in got}}}

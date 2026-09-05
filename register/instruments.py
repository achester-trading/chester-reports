"""
Instrument identity, to the extent this system has one.

Two jobs. Normalise an instrument string to the issuer root a restriction can
be checked against, and answer whether that root is restricted.

-----------------------------------------------------------------------------
NORMALISATION
-----------------------------------------------------------------------------

The blocklist is keyed on issuer roots, so everything that refers to the same
issuer has to collapse onto one string before it is checked. Otherwise the rule
is trivially defeated by writing the instrument a different way, which is the
one failure mode a compliance restriction may not have.

    BN                        -> BN
    bn.to                     -> BN     exchange suffix
    BN.PR.A                   -> BN     preferred series
    BEP.UN                    -> BEP    unit class
    O:BN260918C00050000       -> BN     Polygon option symbol
    BN260918C00050000         -> BN     OCC / yfinance contract symbol
    BN    260918C00050000     -> BN     OCC with root padding
    BN 260918C50              -> BN     loose hand-written option

BEPC DOES NOT COLLAPSE TO BEP, and that is deliberate. Only DOTTED suffixes and
option encodings are stripped -- never trailing letters -- because BEP and BEPC
are different securities of the same complex and both are listed separately.
Stripping letters would also turn every ticker into a prefix match, which would
block half the market.

-----------------------------------------------------------------------------
NAME MATCHING
-----------------------------------------------------------------------------

Tickers alone are not enough. Two Brookfield funds trade under symbols generic
enough that blocking the bare ticker would eventually fire on an unrelated
issuer (`RA`, `INF`), so those are matched on entity name instead. Any
instrument string containing a restricted entity name is blocked regardless of
its symbol -- which also catches an instrument written as prose rather than a
ticker.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
ENTITIES_PATH = REPO / "config" / "tracked_entities.yaml"

# Root, then a 6-digit date, then C or P, then the strike. Covers the OCC
# 21-character form, yfinance's contractSymbol, and the loose hand-written
# variant; the optional O: prefix is Polygon/Massive's.
_OPTION = re.compile(r"^(?:O:)?([A-Z][A-Z0-9]{0,5})\s*(\d{6})([CP])(\d{1,8})$")

# Dotted tails that denote a listing or a class of the SAME issuer.
_DOTTED_SUFFIX = re.compile(r"\.(TO|V|NE|CN|L|AX|SI|HK|PA|DE|MI|MC|AS|BR|"
                            r"UN|PR|RT|WT|WS|A|B|C|U|X)\b.*$", re.I)


def normalise(instrument: Optional[str]) -> str:
    """Collapse an instrument string to its issuer root, uppercased."""
    if not instrument:
        return ""
    s = str(instrument).strip().upper()
    if not s:
        return ""

    # Option symbol -> underlying root. Done before suffix stripping because an
    # option symbol has no dots and would otherwise survive intact.
    m = _OPTION.match(s.replace(" ", "") if _OPTION.match(s.replace(" ", "")) else s)
    if m:
        return m.group(1)
    compact = s.replace(" ", "")
    m = _OPTION.match(compact)
    if m:
        return m.group(1)

    # Dotted suffixes: exchange, unit, preferred series, share class.
    if "." in s:
        head, _, tail = s.partition(".")
        if _DOTTED_SUFFIX.match("." + tail) or len(tail.replace(".", "")) <= 3:
            s = head
    # Vendor dash forms: BN-PA, BRK-B
    if "-" in s:
        head, _, tail = s.partition("-")
        if len(tail) <= 3 and head:
            s = head
    return s


class Restrictions:
    """The restricted-instrument rule, loaded from config/tracked_entities.yaml.

    Loaded from the file rather than hard-coded so that adding an instrument to
    the complex is a data edit that inherits every enforcement path, which is
    what the architecture means by "any instrument added to the complex
    inherits the flag".
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        import yaml  # noqa: PLC0415
        self.path = Path(path or ENTITIES_PATH)
        with self.path.open(encoding="utf-8") as fp:
            self.raw = yaml.safe_load(fp) or {}
        self.roots: dict[str, dict] = {}
        self.name_patterns: list[tuple[str, str]] = []
        for ent_id, ent in (self.raw.get("entities") or {}).items():
            if not (ent or {}).get("restricted"):
                continue
            for row in ent.get("tickers") or []:
                root = normalise(row.get("root"))
                if root:
                    self.roots[root] = {**row, "entity_id": ent_id}
            for pat in ent.get("name_patterns") or []:
                self.name_patterns.append((str(pat).lower(), ent_id))

    def check(self, instrument: Optional[str]) -> Optional[dict]:
        """Return the matching restriction, or None if the instrument is clear.

        Two nets. The root match is the precise one; the name match catches an
        instrument written as prose, and the funds whose tickers are too
        generic to block by symbol.
        """
        root = normalise(instrument)
        if root and root in self.roots:
            return {"matched_on": "root", "root": root, **self.roots[root]}
        text = str(instrument or "").lower()
        for pat, ent_id in self.name_patterns:
            if pat in text:
                return {"matched_on": "name", "root": root, "pattern": pat,
                        "entity_id": ent_id,
                        "entity": f"name match on {pat!r}"}
        return None

    def is_restricted(self, instrument: Optional[str]) -> bool:
        return self.check(instrument) is not None

    def all_roots(self) -> list[str]:
        return sorted(self.roots)


_CACHE: Optional[Restrictions] = None


def restrictions(reload: bool = False) -> Restrictions:
    """Process-wide singleton, so the YAML is parsed once per run."""
    global _CACHE
    if _CACHE is None or reload:
        _CACHE = Restrictions()
    return _CACHE

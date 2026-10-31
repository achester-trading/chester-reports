"""
The price sources, family by family: one resolver (A96; tranche 2b of the
price-source migration, decisions 4 and 5 ruled D38).

    from altdata import price_sources as ps
    ps.key("us_yields", "y10")          # the active key: Yahoo's ^TNX key today
    ps.resolve("price:dollar_index.dxy")
    ps.resolve_tree(cfg)                # every "price:..." reference in a loaded config
    ps.break_label("us_yields")         # None until the family is switched
    python -m altdata.price_sources     # each family's source and keys

config/price_sources.yaml holds one switch per family. Readers never name a
migrating key: code asks key(), config writes "price:<family>.<member>", and the
config's loader resolves it. Every family ships on yfinance, so every reader
gets the key it read before and nothing printed changes.

When a family is switched (`source: fred`, `switched_on: <session>`):
- every reader gets the new key at once;
- a block that prints the series prints break_label() once, beneath its first
  figure;
- history before `switched_on` comes from the old key and after it from the new
  (segments(), split_points()), drawn as two series with the break marked, never
  spliced into one.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

import yaml

CONFIG = Path(__file__).resolve().parent.parent / "config" / "price_sources.yaml"
PREFIX = "price:"
_CFG: Optional[dict] = None


def config(path: Optional[Path] = None) -> dict:
    global _CFG
    if path is not None:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if _CFG is None:
        _CFG = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    return _CFG


def reset() -> None:
    """Forget the cached config (a gate that edits it calls this)."""
    global _CFG
    _CFG = None


def _family(family: str, cfg: Optional[dict] = None) -> dict:
    f = ((cfg or config()).get("families") or {}).get(family)
    if f is None:
        raise KeyError(f"no price family {family!r} in config/price_sources.yaml")
    return f


def source(family: str, cfg: Optional[dict] = None) -> str:
    return str(_family(family, cfg).get("source") or "yfinance")


def key(family: str, member: str, cfg: Optional[dict] = None) -> str:
    """The active source's key for one member of a family."""
    f = _family(family, cfg)
    m = (f.get("members") or {}).get(member)
    if not m:
        raise KeyError(f"no member {member!r} in price family {family!r}")
    src = str(f.get("source") or "yfinance")
    if src not in m:
        raise KeyError(f"price family {family!r} is switched to {src!r}, which "
                       f"{member!r} has no key for")
    return str(m[src])


def old_key(family: str, member: str, cfg: Optional[dict] = None) -> str:
    return str(((_family(family, cfg).get("members") or {}).get(member) or {})["yfinance"])


def resolve(value: Any, cfg: Optional[dict] = None) -> Any:
    """A "price:<family>.<member>" reference as the active key; a pinned one,
    "price:<family>.<member>@<source>", as that source's key whatever is active
    (a deliberate cross-source comparison: DXY against the broad dollar);
    anything else as is."""
    if isinstance(value, str) and value.startswith(PREFIX):
        ref, _, pin = value[len(PREFIX):].partition("@")
        fam, _, mem = ref.partition(".")
        if pin:
            m = (_family(fam, cfg).get("members") or {}).get(mem) or {}
            if pin not in m:
                raise KeyError(f"price family {fam!r} member {mem!r} has no {pin!r} key")
            return str(m[pin])
        return key(fam, mem, cfg)
    return value


def resolve_tree(obj: Any, cfg: Optional[dict] = None) -> Any:
    """A loaded config with every reference resolved (a new object)."""
    if isinstance(obj, dict):
        return {k: resolve_tree(v, cfg) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_tree(v, cfg) for v in obj]
    return resolve(obj, cfg)


def switched(family: str, cfg: Optional[dict] = None) -> bool:
    return source(family, cfg) != "yfinance"


def family_of(series_key: str, cfg: Optional[dict] = None) -> Optional[tuple[str, str]]:
    """(family, member) whose old or new key `series_key` is; None otherwise."""
    for fam, f in ((cfg or config()).get("families") or {}).items():
        for mem, keys in (f.get("members") or {}).items():
            if series_key in (keys or {}).values():
                return fam, mem
    return None


def break_label(family: str, cfg: Optional[dict] = None) -> Optional[str]:
    """The line a block prints once beneath its first figure; None unswitched."""
    f = _family(family, cfg)
    if not switched(family, cfg):
        return None
    return " ".join(str(f.get("break_label") or "").split()).format(
        switched_on=f.get("switched_on") or "(date not set)")


def labels_for(series_keys: list[str], cfg: Optional[dict] = None) -> list[str]:
    """The break labels a block printing these keys owes, each family once."""
    out, seen = [], set()
    for k in series_keys:
        fm = family_of(str(k), cfg)
        if fm and fm[0] not in seen:
            seen.add(fm[0])
            lab = break_label(fm[0], cfg)
            if lab:
                out.append(lab)
    return out


def switch_date_of(series_key: str, cfg: Optional[dict] = None) -> Optional[str]:
    """The switch date of the family `series_key` belongs to, if it has switched."""
    fm = family_of(series_key, cfg)
    if not fm or not switched(fm[0], cfg):
        return None
    return _family(fm[0], cfg).get("switched_on") or None


def plot_split(ax, split: dict, labels: tuple[str, str],
               colours: tuple[str, str] = ("#0d2b45", "#d97706")) -> list:
    """Draw split_points()'s result: one line per series and, across a switch,
    the break as a dashed vertical line. Two lines, never one spliced."""
    import datetime as _dt                                      # noqa: PLC0415
    drawn = []
    for n, pts in enumerate(split.get("series") or []):
        if pts:
            xs = [_dt.date.fromisoformat(str(d)[:10]) for d, _ in pts]
            drawn += ax.plot(xs, [v for _, v in pts], color=colours[n % 2],
                             linewidth=0.9, label=labels[n % 2])
    if split.get("break"):
        ax.axvline(_dt.date.fromisoformat(split["break"]), color="#898781",
                   linewidth=0.8, linestyle="--")
    return drawn


def segments(family: str, member: str, cfg: Optional[dict] = None) -> list[dict]:
    """Where each stretch of a member's history comes from: one segment today;
    after a switch, the old key up to the session before `switched_on` and the
    new key from it. Two keys, never one spliced series."""
    if not switched(family, cfg):
        return [{"key": key(family, member, cfg), "from": None, "to": None}]
    on = str(_family(family, cfg).get("switched_on") or "")
    return [{"key": old_key(family, member, cfg), "from": None, "to": on, "to_exclusive": True},
            {"key": key(family, member, cfg), "from": on, "to": None}]


def split_points(old: list[tuple], new: list[tuple], switched_on: Optional[str]) -> dict:
    """A chart's two series across a switch: the old key's points before the
    switch date, the new key's from it, and the break between. Never one series."""
    if not switched_on:
        return {"series": [list(old)], "break": None}
    return {"series": [[p for p in old if str(p[0])[:10] < switched_on],
                       [p for p in new if str(p[0])[:10] >= switched_on]],
            "break": switched_on}


def _main(argv: list[str]) -> int:
    for fam, f in (config().get("families") or {}).items():
        mem = ", ".join(f"{m}={key(fam, m)}" for m in (f.get("members") or {})) or "(stub)"
        print(f"{fam:18} {source(fam):9} {mem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

"""
The rule grammar v1 (X-2.10a) and v2 (alpha-lab-4) -- an INTERPRETER, not code
generation.

A hypothesis whose rule is written in this grammar (`rule_dsl`, documented for a
reader without the code in docs/alpha-lab-rules.md) runs through the harness
with no code written for it. A rule is DATA: this module reads it, checks it
(compile_rule), and evaluates it point-in-time against the read-only store
(backtest). Nothing here generates, imports or evaluates code from a rule.

    universe      the instruments the rule may trade
    cadence       daily_close | friday_close | {release: <label>, at: day_before|day_of}
    trigger       a list of conditions, ALL of which must hold:
                    {series, transform, n|w|set|other, op, value}
    direction     long | short | {if: <condition>, then: long|short, else: long|short}
    instrument    a symbol, or {pair: {long, short, weight: equal|vol_matched, n}}
    entry         this_close | next_open | next_close
    exits         target {r|pct}; stop {r|pct|atr+n|series level}; time <sessions>
    cooldown      sessions after a trigger in which no new trigger is taken
    conditioning  [{name, state: <market-state path>, values}]
                  [{name, condition: <condition>}]   true / false
                  [{name, drop: <trigger index>}]    the rule without one condition
                  [{name, replace: {instrument|entry|exits|direction}}]
                                                     the rule with one part swapped
                  -- each value one counted variant

GRAMMAR v2 (alpha-lab-rules/v2; alpha-lab-4, 19 Oct 2026) is v1 plus one key:

    when          a list of state conditions, ALL of which must read a value
                  knowable at the decision and take one of the listed values,
                  or the rule does not trade that day:
                    {kind: state, path: <market-state path>, values: [...]}
                    {kind: zscore, key, instrument?, window, min_rows,
                     bands: {crowded_long, crowded_short},
                     values: [crowded_long|neutral|crowded_short]}
                    {kind: mean_band, key, instrument?, window,
                     bands: {on, off}, values: [on|between|off]}

A missing value is no trade, never a guess. `when` is the grammar search's
conditioning, read by ONE function here (when_value), which the search calls for
its own conditioning (alpha/search.py), so a conditioned candidate is exactly its
v2 rule. Every v1 rule is a v2 rule with no `when` and backtests to the same
trades; a v1 rule may not carry `when`.

POINT-IN-TIME, ALWAYS. A rule decides at an instant (the nightly loop's hour on
its cadence day, or 15:50 ET for a this_close entry) and reads only the vintages
knowable by then (`available_at`), the same as-of discipline as the reports. Every
trade it produces carries its decision instant and the latest availability of
anything it read; alpha/validate.py's check voids a run in which the second is
after the first. A series the store does not hold, or holds too briefly, is a
data gap, never a substitute.

PRICES ARE THE STORE'S. Nine symbols carry a stored open, high and low; the rest
carry closes only. A next_open entry needs a stored open; a stop on a close-only
instrument is checked on closes and filled at the close that breaches it (a
conservative reading, and declared on the trade).
"""

from __future__ import annotations

import ast
import bisect
import datetime as dt
import math
import operator
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from altdata import observations, session

from . import blocklist
from . import config as acfg

REPO = Path(__file__).resolve().parent.parent
SETTINGS_PATH = REPO / "config" / "alpha_rules.yaml"
GRAMMAR = "alpha-lab-rules/v1"           # the proposer writes this one (X-2.10)
GRAMMAR_V2 = "alpha-lab-rules/v2"        # v1 plus `when` (alpha-lab-4)
GRAMMARS = (GRAMMAR, GRAMMAR_V2)

KEYS = {"grammar", "universe", "cadence", "trigger", "direction", "instrument",
        "entry", "exits", "cooldown", "conditioning", "cost_class", "note", "when"}
WHEN_KINDS = ("state", "zscore", "mean_band")
WHEN_VALUES = {"zscore": ("crowded_long", "neutral", "crowded_short"),
               "mean_band": ("on", "between", "off")}
TRANSFORMS = ("level", "change", "pct_change", "zscore", "percentile", "rank",
              "crosses_above", "crosses_below", "max", "min")
OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le,
       "==": operator.eq, "!=": operator.ne}
ENTRIES = ("this_close", "next_open", "next_close")
CADENCES = ("daily_close", "friday_close")
RELEASE_AT = ("day_before", "day_of")
FIELDS = ("close", "open", "high", "low", "volume")
FIELD_SUFFIX = {"close": "", "open": "_open", "high": "_high", "low": "_low",
                "volume": "_volume"}


class RuleError(ValueError):
    """A rule that does not compile. `errors` lists every reason."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


# ---------------------------------------------------------------------------
# What a rule may name: the store's price symbols and the registry's keys
# ---------------------------------------------------------------------------
_CACHE: dict[str, Any] = {}


def settings() -> dict:
    if "settings" not in _CACHE:
        _CACHE["settings"] = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8")) or {}
    return _CACHE["settings"]


def _literal(path: Path, name: str) -> Any:
    """A module-level literal assignment, read by parsing the file -- so the
    grammar knows the fetchers' symbol tables without importing a fetcher
    (alpha/ may not: tools/validate_alpha_no_orders.py)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        tgt = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt, val = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            tgt, val = node.target, node.value
        if isinstance(tgt, ast.Name) and tgt.id == name and val is not None:
            if isinstance(val, ast.Call) and getattr(val.func, "id", "") == "frozenset":
                val = val.args[0]
            try:
                return ast.literal_eval(val)
            except ValueError:
                return None
    return None


def price_symbols() -> dict[str, str]:
    """symbol -> store key (yfinance.<key>), from the basket the price feed keeps."""
    if "symbols" not in _CACHE:
        src = REPO / "altdata" / "sources" / "yfinance_source.py"
        sym = _literal(src, "SYMBOLS") or {}
        _CACHE["symbols"] = {s.upper(): f"yfinance.{k}" for s, k in sym.items()}
        _CACHE["ohlc"] = {str(s).upper() for s in (_literal(src, "OHLC_SYMBOLS") or ())}
    return _CACHE["symbols"]


def ohlc_symbols() -> set[str]:
    price_symbols()
    return _CACHE["ohlc"]


def registry_keys() -> set[str]:
    """Every key metrics_registry.yaml registers: its metrics, and its bulk
    blocks' members, resolved without importing a fetcher (a member list in a
    fetcher's module is read from its source by parsing)."""
    if "registry" in _CACHE:
        return _CACHE["registry"]
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8")) or {}
    out = set((reg.get("metrics") or {}).keys())
    for block in (reg.get("bulk_imports") or {}).values():
        if not isinstance(block, dict) or not block.get("members_from"):
            continue
        mod, attr = str(block["members_from"]).rsplit(".", 1)
        prefix = str(block.get("key_prefix") or "")
        suffixes = list(block.get("member_suffixes") or [""])
        members: Any = None
        if mod == "altdata.config":
            from altdata import config as _c                     # noqa: PLC0415
            members = getattr(_c, attr, None)
        else:
            p = REPO / Path(*mod.split(".")).with_suffix(".py")
            if p.is_file():
                members = _literal(p, attr)
        if members is None:
            continue
        if isinstance(members, dict):
            members = list(members.values()) if block.get("members_are") == "values" \
                else list(members.keys())
        mk = block.get("member_key")
        for m in members:
            name = getattr(m, mk, None) if mk and not isinstance(m, str) else m
            if isinstance(name, str):
                for s in suffixes:
                    out.add(prefix + name + s)
    _CACHE["registry"] = out
    return out


def resolve(ref: Any, fld: str = "close") -> str:
    """A series reference -> its store key. A price symbol (SPY) is its stored
    close, or the field asked for; anything else must be a registered key."""
    if not isinstance(ref, str) or not ref.strip():
        raise RuleError([f"series {ref!r} is not a symbol or a registry key"])
    r = ref.strip()
    sym = price_symbols()
    if r.upper() in sym:
        if fld not in FIELDS:
            raise RuleError([f"field {fld!r} is not one of {FIELDS}"])
        if fld in ("open", "high", "low") and r.upper() not in ohlc_symbols():
            raise RuleError([f"{r.upper()} has no stored {fld}: the store keeps a daily "
                             f"open, high and low for {sorted(ohlc_symbols())} only"])
        return sym[r.upper()] + FIELD_SUFFIX[fld]
    if r in registry_keys():
        return r
    raise RuleError([f"series {r!r} is neither a stored price symbol nor a key in "
                     f"metrics_registry.yaml"])


def _series_refs(ref: Any) -> list[str]:
    if isinstance(ref, dict):
        for k in ("ratio", "spread"):
            if k in ref:
                return [x for part in ref[k] for x in _series_refs(part)]
        return []
    return [ref] if isinstance(ref, str) else []


def instruments(dsl: dict) -> list[str]:
    """The tradables a rule names: its universe and its instrument's legs."""
    out = [str(x).upper() for x in (dsl.get("universe") or []) if isinstance(x, str)]
    ins = dsl.get("instrument")
    if isinstance(ins, str):
        out.append(ins.upper())
    elif isinstance(ins, dict) and isinstance(ins.get("pair"), dict):
        out += [str(ins["pair"].get(k) or "").upper() for k in ("long", "short")
                if ins["pair"].get(k)]
    seen: list[str] = []
    for t in out:
        if t and t not in seen:
            seen.append(t)
    return seen


# ---------------------------------------------------------------------------
# Compiling: every check the rule can fail before anything runs
# ---------------------------------------------------------------------------
@dataclass
class Compiled:
    dsl: dict
    keys: set
    instruments: list
    variants: list           # [{name, kind, value}] -- each one counted
    horizon: str             # the constitution's horizon class for min_signals
    holding: int             # sessions, the time stop
    when: list = field(default_factory=list)   # v2's state conditions


def _check_condition(c: Any, where: str, err: list[str], keys: set,
                     allow_no_op: bool = False) -> None:
    if not isinstance(c, dict):
        err.append(f"{where}: a condition is a mapping")
        return
    tr = c.get("transform", "level")
    if tr not in TRANSFORMS:
        err.append(f"{where}: transform {tr!r} is not one of {TRANSFORMS}")
    refs = _series_refs(c.get("series"))
    if not refs:
        err.append(f"{where}: no series")
    fld = c.get("field", "close")
    for r in refs:
        try:
            keys.add(resolve(r, fld))
        except RuleError as e:
            err += [f"{where}: {m}" for m in e.errors]
    if tr in ("change", "pct_change", "max", "min"):
        n = c.get("n")
        if not (n == "week" or (isinstance(n, int) and not isinstance(n, bool) and n >= 1)):
            err.append(f"{where}: {tr} needs n, a number of observations or 'week'")
    if tr in ("zscore", "percentile"):
        w = c.get("w")
        if not (isinstance(w, int) and w >= 10):
            err.append(f"{where}: {tr} needs w, a window of at least 10 observations")
    if tr == "rank":
        s = c.get("set")
        if s not in (settings().get("sets") or {}):
            err.append(f"{where}: rank needs set, one of {sorted(settings().get('sets') or {})}")
        else:
            for m in settings()["sets"][s]:
                try:
                    keys.add(resolve(m))
                except RuleError as e:
                    err += [f"{where}: {x}" for x in e.errors]
        n = c.get("n")
        if not (n == "week" or (isinstance(n, int) and n >= 1)):
            err.append(f"{where}: rank needs n, the return window ranked over")
    if tr in ("crosses_above", "crosses_below"):
        o = c.get("other")
        if isinstance(o, (int, float)) and not isinstance(o, bool):
            pass
        else:
            orefs = _series_refs(o)
            if not orefs:
                err.append(f"{where}: {tr} needs other, a series or a number")
            for r in orefs:
                try:
                    keys.add(resolve(r))
                except RuleError as e:
                    err += [f"{where}: {m}" for m in e.errors]
        if "op" in c:
            err.append(f"{where}: {tr} is itself the test; it takes no op")
    else:
        if c.get("op") not in OPS and not allow_no_op:
            err.append(f"{where}: op {c.get('op')!r} is not one of {list(OPS)}")
        v = c.get("value")
        if not allow_no_op and not (isinstance(v, (int, float)) and not isinstance(v, bool)):
            err.append(f"{where}: value is not a number")
    if c.get("units") not in (None, "bp"):
        err.append(f"{where}: units may be 'bp' (a change in a percent series, x100)")


def compile_rule(dsl: Any, store=None) -> Compiled:
    """Check a rule and return it compiled; raise RuleError with every reason.
    With a store, also check each series and instrument is stored (a data gap
    otherwise)."""
    err: list[str] = []
    if not isinstance(dsl, dict):
        raise RuleError(["a rule is a mapping"])
    for k in dsl:
        if k not in KEYS:
            err.append(f"unknown key {k}")
    if dsl.get("grammar") not in GRAMMARS:
        err.append(f"grammar is {dsl.get('grammar')!r}, not one of {GRAMMARS}")
    keys: set = set()
    when_series: list[tuple[str, Optional[str]]] = []
    if "when" in dsl:
        if dsl.get("grammar") != GRAMMAR_V2:
            err.append(f"when is grammar v2's ({GRAMMAR_V2}); a v1 rule has no when")
        _check_when(dsl.get("when"), err, when_series)
    uni = dsl.get("universe")
    if not isinstance(uni, list) or not uni:
        err.append("universe is not a list of symbols")
    cad = dsl.get("cadence")
    if isinstance(cad, dict):
        if not cad.get("release") or cad.get("at") not in RELEASE_AT:
            err.append(f"a release cadence is {{release: <label>, at: {RELEASE_AT}}}")
        else:
            labels = release_labels()
            if cad["release"] not in labels:
                err.append(f"release {cad['release']!r} is not a label in "
                           f"config/release_calendar.yaml ({sorted(labels)[:8]}...)")
    elif cad not in CADENCES:
        err.append(f"cadence {cad!r} is not one of {CADENCES} or a release")
    trig = dsl.get("trigger")
    if not isinstance(trig, list) or not trig:
        err.append("trigger is not a non-empty list of conditions")
    for i, c in enumerate(trig or []):
        _check_condition(c, f"trigger[{i}]", err, keys)
    d = dsl.get("direction")
    if isinstance(d, dict):
        if d.get("then") not in ("long", "short") or d.get("else") not in ("long", "short"):
            err.append("direction {if, then, else}: then and else are long or short")
        _check_condition(d.get("if"), "direction.if", err, keys)
    elif d not in ("long", "short"):
        err.append("direction is long, short or {if, then, else}")
    ins = dsl.get("instrument")
    legs: list[str] = []
    if isinstance(ins, str):
        legs = [ins.upper()]
    elif isinstance(ins, dict) and isinstance(ins.get("pair"), dict):
        p = ins["pair"]
        legs = [str(p.get("long") or "").upper(), str(p.get("short") or "").upper()]
        if not all(legs):
            err.append("a pair names a long leg and a short leg")
        if p.get("weight", "equal") not in ("equal", "vol_matched"):
            err.append("a pair's weight is equal or vol_matched")
        if p.get("weight") == "vol_matched" and not (isinstance(p.get("n"), int) and p["n"] >= 10):
            err.append("a vol_matched pair needs n, at least 10 sessions")
    else:
        err.append("instrument is a symbol or {pair: {long, short, weight, n}}")
    for leg in legs:
        if not leg:
            continue
        if blocklist.check(leg) is not None:
            err.append(f"instrument {leg} is restricted: the Brookfield complex never "
                       f"reaches the lab")
            continue
        if isinstance(uni, list) and leg not in [str(u).upper() for u in uni]:
            err.append(f"instrument {leg} is not in the rule's universe")
        try:
            keys.add(resolve(leg))
        except RuleError as e:
            err += e.errors
    for u in uni or []:
        if isinstance(u, str) and blocklist.check(u) is not None:
            err.append(f"universe names {u}, restricted: the Brookfield complex never "
                       f"reaches the lab")
    entry = dsl.get("entry")
    if entry not in ENTRIES:
        err.append(f"entry {entry!r} is not one of {ENTRIES}")
    elif entry == "next_open":
        for leg in legs:
            if leg and leg not in ohlc_symbols():
                err.append(f"entry next_open needs a stored open, and {leg} has none "
                           f"(closes only): use next_close")
    ex = dsl.get("exits")
    holding = 0
    if not isinstance(ex, dict) or "time" not in ex:
        err.append("exits is a mapping with at least a time stop (sessions)")
    else:
        t = ex.get("time")
        if not (isinstance(t, int) and t >= 1):
            err.append("exits.time is a number of sessions, at least 1")
        else:
            holding = t
        st, tg = ex.get("stop"), ex.get("target")
        if st is not None:
            if not isinstance(st, dict) or not any(k in st for k in ("pct", "atr", "series")):
                err.append("exits.stop is {pct}, {atr, n} or a series level {series, "
                           "transform: max|min, n, field}")
            elif "atr" in st and not (isinstance(st.get("n"), int) and st["n"] >= 2):
                err.append("an ATR stop needs n, at least 2 sessions")
            elif "series" in st:
                _check_condition(st, "exits.stop", err, keys, allow_no_op=True)
            if isinstance(ins, dict) and isinstance(st, dict) and "pct" not in st:
                err.append("a pair's stop is in pct of the pair's return")
        if tg is not None:
            if not isinstance(tg, dict) or not any(k in tg for k in ("pct", "r")):
                err.append("exits.target is {pct} or {r}")
            elif "r" in tg and st is None:
                err.append("a target in R needs a stop: R is the entry-to-stop distance")
    cd = dsl.get("cooldown", 0)
    if not (isinstance(cd, int) and cd >= 0):
        err.append("cooldown is a number of sessions")
    variants: list[dict] = []
    for i, c in enumerate(dsl.get("conditioning") or []):
        where = f"conditioning[{i}]"
        if not isinstance(c, dict) or not c.get("name"):
            err.append(f"{where}: a conditioning entry has a name")
            continue
        if "state" in c:
            vals = c.get("values")
            if not isinstance(vals, list) or not vals:
                err.append(f"{where}: a state conditioning lists its values")
                continue
            variants += [{"name": c["name"], "kind": "state", "path": c["state"],
                          "value": v} for v in vals]
        elif "condition" in c:
            _check_condition(c["condition"], where, err, keys)
            variants += [{"name": c["name"], "kind": "condition", "value": v}
                         for v in (True, False)]
        elif "drop" in c:
            if not (isinstance(c["drop"], int) and 0 <= c["drop"] < len(trig or [])):
                err.append(f"{where}: drop names a trigger condition by its index")
            variants.append({"name": c["name"], "kind": "drop", "value": c["drop"]})
        elif "replace" in c:
            rep = c["replace"]
            if not isinstance(rep, dict) or not rep or                     any(k not in ("instrument", "entry", "exits", "direction") for k in rep):
                err.append(f"{where}: replace swaps instrument, entry, exits or direction")
            else:
                try:
                    sub = compile_rule({**{k: v for k, v in dsl.items()
                                           if k != "conditioning"}, **rep})
                    keys |= sub.keys
                except RuleError as e:
                    err += [f"{where}: {m}" for m in e.errors]
            variants.append({"name": c["name"], "kind": "replace", "value": rep})
        else:
            err.append(f"{where}: conditioning is on a state, a condition, a drop or "
                       f"a replace")
    if store is not None:
        for k in sorted(keys):
            if not store.all_vintages(k):
                err.append(f"data gap: the store holds no rows for {k}")
        for k, inst in when_series:
            if not store.all_vintages(k, inst):
                err.append(f"data gap: the store holds no rows for {k}"
                           + (f" ({inst})" if inst else ""))
    if err:
        raise RuleError(err)
    weekly = (cad == "friday_close" or isinstance(cad, dict) or holding >= 5)
    return Compiled(dsl=dsl, keys=keys, instruments=legs, variants=variants,
                    horizon="weekly" if weekly else "daily", holding=holding,
                    when=list(dsl.get("when") or []))


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _check_when(when: Any, err: list[str], series: list) -> None:
    """Grammar v2's `when`: every item one of WHEN_KINDS, with its values."""
    if not isinstance(when, list) or not when:
        err.append("when is a non-empty list of state conditions")
        return
    for i, it in enumerate(when):
        where = f"when[{i}]"
        if not isinstance(it, dict) or it.get("kind") not in WHEN_KINDS:
            err.append(f"{where}: kind is one of {WHEN_KINDS}")
            continue
        vals = it.get("values")
        if not isinstance(vals, list) or not vals:
            err.append(f"{where}: values is a non-empty list")
            continue
        kind = it["kind"]
        if kind == "state":
            if not isinstance(it.get("path"), str) or not it["path"].strip():
                err.append(f"{where}: a state condition names its path in the stored "
                           f"market-state object")
            continue
        key = it.get("key")
        if not isinstance(key, str) or key not in registry_keys():
            err.append(f"{where}: key {key!r} is not in metrics_registry.yaml")
        else:
            inst = it.get("instrument")
            if inst is not None and not isinstance(inst, str):
                err.append(f"{where}: instrument is a string")
            series.append((key, inst))
        bad = [v for v in vals if v not in WHEN_VALUES[kind]]
        if bad:
            err.append(f"{where}: values {bad} are not among {WHEN_VALUES[kind]}")
        w = it.get("window")
        b = it.get("bands") or {}
        if kind == "zscore":
            mr = it.get("min_rows", w)
            if not (isinstance(w, int) and w >= 10):
                err.append(f"{where}: a zscore's window is at least 10 observations")
            elif not (isinstance(mr, int) and 2 <= mr <= w):
                err.append(f"{where}: min_rows is between 2 and the window")
            if not (_num(b.get("crowded_long")) and _num(b.get("crowded_short"))
                    and b["crowded_short"] < b["crowded_long"]):
                err.append(f"{where}: bands are {{crowded_long, crowded_short}}, numbers, "
                           f"short below long")
        else:
            if not (isinstance(w, int) and w >= 1):
                err.append(f"{where}: a mean_band's window is at least 1 observation")
            if not (_num(b.get("on")) and _num(b.get("off")) and b["off"] <= b["on"]):
                err.append(f"{where}: bands are {{on, off}}, numbers, off at or below on")


def release_labels() -> set[str]:
    cal = yaml.safe_load((REPO / "config" / "release_calendar.yaml").read_text(
        encoding="utf-8")) or {}
    return {str(r["label"]) for r in cal.get("releases") or [] if r.get("label")}


def _release_patterns(label: str) -> list[str]:
    cal = yaml.safe_load((REPO / "config" / "release_calendar.yaml").read_text(
        encoding="utf-8")) or {}
    return [str(r["match"]).lower() for r in cal.get("releases") or []
            if r.get("label") == label]


# ---------------------------------------------------------------------------
# The data, point-in-time
# ---------------------------------------------------------------------------
class Series:
    """One stored series: per observed day, its vintages (available_at, value)
    in availability order."""

    def __init__(self, rows: list[dict]) -> None:
        by: dict[str, list] = {}
        for r in rows:
            if r.get("value_num") is None:
                continue
            by.setdefault(str(r["observed_at"])[:10], []).append(
                (str(r["available_at"]), float(r["value_num"])))
        self.days = sorted(by)
        self.vint = [sorted(by[d]) for d in self.days]

    def known(self, day: str, t: str, k: int) -> list[tuple[str, float, str]]:
        """The last k observations on or before `day` knowable at `t`, oldest
        first, each at its latest vintage knowable by then."""
        out: list[tuple[str, float, str]] = []
        i = bisect.bisect_right(self.days, day) - 1
        while i >= 0 and len(out) < k:
            vs = self.vint[i]
            j = bisect.bisect_right(vs, (t, math.inf)) - 1
            if j >= 0:
                out.append((self.days[i], vs[j][1], vs[j][0]))
            i -= 1
        out.reverse()
        return out

    def first(self, day: str) -> Optional[float]:
        """The first vintage on a day -- for the PRICES a trade is simulated
        against after its decision, where availability is not the question."""
        i = bisect.bisect_left(self.days, day)
        if i < len(self.days) and self.days[i] == day:
            return self.vint[i][0][1]
        return None


class Composite:
    """{ratio: [a, b]} or {spread: [a, b]}, on the days both are observed."""

    def __init__(self, kind: str, a, b) -> None:
        self.kind, self.a, self.b = kind, a, b

    def known(self, day: str, t: str, k: int) -> list[tuple[str, float, str]]:
        want = k + 10
        while True:
            xa = {d: (v, av) for d, v, av in self.a.known(day, t, want)}
            xb = {d: (v, av) for d, v, av in self.b.known(day, t, want)}
            common = sorted(set(xa) & set(xb))
            if len(common) >= k or want > 4 * k + 400:
                break
            want *= 2
        out = []
        for d in common[-k:]:
            va, aa = xa[d]
            vb, ab = xb[d]
            if self.kind == "ratio":
                if vb == 0:
                    continue
                v = va / vb
            else:
                v = va - vb
            out.append((d, v, max(aa, ab)))
        return out


class Data:
    """The store's series, loaded once per run, read point-in-time."""

    def __init__(self, store) -> None:
        self.store = store
        self._s: dict[str, Series] = {}
        self._ms: Optional[Series] = None
        self._ms_text: dict[str, list] = {}

    def series(self, key: str, instrument: Optional[str] = None) -> Series:
        k = key if instrument is None else f"{key}\x00{instrument}"
        if k not in self._s:
            self._s[k] = Series(self.store.all_vintages(key, instrument)
                                if instrument is not None
                                else self.store.all_vintages(key))
        return self._s[k]

    def ref(self, ref: Any, fld: str = "close"):
        if isinstance(ref, dict):
            for kind in ("ratio", "spread"):
                if kind in ref:
                    a, b = ref[kind]
                    return Composite(kind, self.ref(a, fld), self.ref(b, fld))
        return self.series(resolve(ref, fld))

    def state(self, day: str, t: str, path: str) -> Optional[str]:
        """A value from the stored market-state object for `day`, knowable at
        `t` -- read, never recomputed."""
        return self.state_vintage(day, t, path)[0]

    def state_vintage(self, day: str, t: str, path: str) -> tuple[Optional[str], str]:
        """(the value, its available_at): the latest vintage of `day`'s stored
        object knowable at `t`. A vintage stored after `t` is never read."""
        if not self._ms_text:
            for r in self.store.all_vintages("market_state"):
                if r.get("value_text"):
                    self._ms_text.setdefault(str(r["observed_at"])[:10], []).append(
                        (str(r["available_at"]), r["value_text"]))
        vs = sorted(self._ms_text.get(day) or [])
        ok = [(a, v) for a, v in vs if a <= t]
        if not ok:
            return None, ""
        import json                                             # noqa: PLC0415
        try:
            cur: Any = json.loads(ok[-1][1])
        except ValueError:
            return None, ""
        for part in str(path).split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        return (None, "") if cur is None else (str(cur), ok[-1][0])

    def release_days(self, label: str, t_last: str) -> list[tuple[str, str]]:
        """(release date, available_at) of each scheduled release matching the
        calendar's patterns for `label`, from the store's events table."""
        pats = _release_patterns(label)
        have = self.store.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                       "AND name='events'").fetchone()
        if not have or not pats:
            return []
        out: dict[str, str] = {}
        for r in self.store.conn.execute(
                "SELECT observed_at, available_at, title FROM events WHERE type IN "
                "('release','scheduled') AND available_at <= ? ORDER BY available_at",
                (t_last,)).fetchall():
            title = str(r["title"]).lower()
            if any(p in title for p in pats):
                d = str(r["observed_at"])[:10]
                out.setdefault(d, str(r["available_at"]))
        return sorted(out.items())


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def decision_instant(day: str, entry: str) -> str:
    """The instant a rule decides on `day`, canonical UTC."""
    cfg = settings()
    hhmm = cfg.get("this_close_decision_time_et" if entry == "this_close"
                   else "decision_time_et", "17:40")
    from zoneinfo import ZoneInfo                               # noqa: PLC0415
    h, m = (int(x) for x in str(hhmm).split(":"))
    local = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                                ZoneInfo("America/New_York"))
    return observations.canonical_instant(local.isoformat())


def week_base_day(day: str) -> str:
    """The last session of the week before `day`'s week: a weekly change runs
    from that close, so a holiday week is still one week."""
    d = dt.date.fromisoformat(day)
    mon = d - dt.timedelta(days=d.weekday())
    return session.previous_trading_session(mon).isoformat()


@dataclass
class Eval:
    value: Optional[float]
    avail: str = ""
    why: str = ""


def _window(s, day: str, t: str, n: Any, extra: int = 1) -> list[tuple[str, float, str]]:
    """The observations a change over n reads (n + extra of them), or, for
    n 'week', last week's final observation and everything after it."""
    if n == "week":
        base = week_base_day(day)
        xs = s.known(day, t, 15)
        keep = [x for x in xs if x[0] <= base]
        if not keep:
            return []
        b = keep[-1]
        return [b] + [x for x in xs if x[0] > b[0]]
    return s.known(day, t, int(n) + extra)


def _pct(a: float, b: float) -> Optional[float]:
    return None if not a else (b / a - 1.0) * 100.0


def evaluate(c: dict, data: Data, day: str, t: str) -> Eval:
    """One condition's transform at (day, t): the value and the latest
    availability among what it read."""
    tr = c.get("transform", "level")
    fld = c.get("field", "close")
    s = data.ref(c["series"], fld)
    if tr == "level":
        xs = s.known(day, t, 1)
        return Eval(xs[-1][1], xs[-1][2]) if xs else Eval(None, why="no value")
    if tr in ("change", "pct_change"):
        xs = _window(s, day, t, c["n"])
        need = 2 if c["n"] == "week" else int(c["n"]) + 1
        if len(xs) < need:
            return Eval(None, why="insufficient history")
        a, b = xs[0][1], xs[-1][1]
        av = max(x[2] for x in (xs[0], xs[-1]))
        if tr == "pct_change":
            v = _pct(a, b)
            return Eval(v, av) if v is not None else Eval(None, why="zero base")
        v = b - a
        return Eval(v * 100.0 if c.get("units") == "bp" else v, av)
    if tr in ("zscore", "percentile"):
        w = int(c["w"])
        xs = s.known(day, t, w)
        if len(xs) < w:
            return Eval(None, why="insufficient history")
        vals = [x[1] for x in xs]
        x = vals[-1]
        av = max(v[2] for v in xs)
        if tr == "zscore":
            sd = statistics.stdev(vals)
            return Eval((x - statistics.fmean(vals)) / sd, av) if sd else Eval(None, why="flat")
        below = sum(1 for v in vals if v < x)
        ties = sum(1 for v in vals if v == x)
        return Eval(100.0 * (below + 0.5 * (ties - 1)) / (w - 1) if w > 1 else 50.0, av)
    if tr in ("max", "min"):
        xs = _window(s, day, t, c["n"], extra=0)
        if c["n"] == "week":
            xs = xs[1:]
        if not xs:
            return Eval(None, why="no values")
        f = max if tr == "max" else min
        return Eval(f(x[1] for x in xs), max(x[2] for x in xs))
    if tr == "rank":
        members = list(settings()["sets"][c["set"]])
        target = str(c["series"]).upper()
        if target not in members:
            members.append(target)
        rets: dict[str, float] = {}
        av = ""
        for m in members:
            e = evaluate({"series": m, "transform": "pct_change", "n": c["n"]}, data, day, t)
            if e.value is not None:
                rets[m] = e.value
                av = max(av, e.avail)
        if target not in rets:
            return Eval(None, why="no return for the ranked series")
        order = sorted(rets.values(), reverse=True)
        return Eval(float(order.index(rets[target]) + 1), av)
    if tr in ("crosses_above", "crosses_below"):
        o = c.get("other")
        xs = s.known(day, t, 2)
        if len(xs) < 2:
            return Eval(None, why="insufficient history")
        if isinstance(o, (int, float)):
            ys = [(xs[0][0], float(o), ""), (xs[1][0], float(o), "")]
        else:
            ys = data.ref(o).known(day, t, 2)
            if len(ys) < 2:
                return Eval(None, why="insufficient history")
        av = max([x[2] for x in xs] + [y[2] for y in ys])
        if tr == "crosses_above":
            hit = xs[0][1] <= ys[0][1] and xs[1][1] > ys[1][1]
        else:
            hit = xs[0][1] >= ys[0][1] and xs[1][1] < ys[1][1]
        return Eval(1.0 if hit else 0.0, av)
    return Eval(None, why=f"transform {tr}")


def holds(c: dict, data: Data, day: str, t: str) -> tuple[Optional[bool], str, str]:
    """(holds?, latest availability read, why-not) for one condition."""
    e = evaluate(c, data, day, t)
    if e.value is None:
        return None, e.avail, e.why
    if c.get("transform") in ("crosses_above", "crosses_below"):
        return e.value == 1.0, e.avail, ""
    return OPS[c["op"]](e.value, float(c["value"])), e.avail, ""


# ---------------------------------------------------------------------------
# Grammar v2's `when` -- THE ONE READER of a state condition, the search's too
# ---------------------------------------------------------------------------
def when_label(it: dict) -> str:
    if it.get("name"):
        return str(it["name"])
    if it["kind"] == "state":
        return f"state:{it['path']}"
    return f"{it['kind']}:{it['key']}" + (f"@{it['instrument']}" if it.get("instrument") else "")


def when_value(it: dict, data: Data, day: str, t: str) -> tuple[Optional[str], str]:
    """(the condition's value on `day`, read as knowable at `t`, and the latest
    availability among what it read), or (None, "") where nothing is knowable.

      state      the stored market-state object's value at `path`
      zscore     the series' (and instrument's) last `window` observations: the
                 newest one's z against them, given at least `min_rows`;
                 crowded_long at or above bands.crowded_long, crowded_short at or
                 below bands.crowded_short, else neutral
      mean_band  the mean of the last `window` observations: on at or above
                 bands.on, off below bands.off, else between
    """
    kind = it["kind"]
    if kind == "state":
        return data.state_vintage(day, t, it["path"])
    w = int(it["window"])
    xs = data.series(it["key"], it.get("instrument")).known(day, t, w)
    vals = [x[1] for x in xs]
    b = it["bands"]
    if kind == "zscore":
        if len(xs) < int(it.get("min_rows") or w) or len(xs) < 2:
            return None, ""
        sd = statistics.stdev(vals)
        if not sd:
            return None, ""
        z = (vals[-1] - statistics.fmean(vals)) / sd
        v = ("crowded_long" if z >= float(b["crowded_long"]) else
             "crowded_short" if z <= float(b["crowded_short"]) else "neutral")
        return v, max(x[2] for x in xs)
    if kind == "mean_band":
        if len(xs) < w:
            return None, ""
        m = statistics.fmean(vals)
        v = "on" if m >= float(b["on"]) else ("off" if m < float(b["off"]) else "between")
        return v, max(x[2] for x in xs)
    raise ValueError(f"when kind {kind!r}")


def when_ok(cmp: Compiled, data: Data, day: str,
            t: str) -> tuple[bool, str, str, dict]:
    """(every `when` item holds?, the latest availability read, why not, the
    values read). A v1 rule has no `when` and always holds."""
    vals: dict = {}
    av = ""
    for it in cmp.when:
        v, a = when_value(it, data, day, t)
        lab = when_label(it)
        vals[lab] = v
        if v is None:
            return False, av, "when: no value knowable at the decision", vals
        if str(v) not in [str(x) for x in it["values"]]:
            return False, av, "when: not in the rule's state", vals
        av = max(av, a)
    return True, av, "", vals


# ---------------------------------------------------------------------------
# The backtest
# ---------------------------------------------------------------------------
def cadence_days(cmp: Compiled, data: Data, first: str, last: str) -> list[str]:
    cad = cmp.dsl["cadence"]
    d0, d1 = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    sessions_: list[str] = []
    d = d0
    while d <= d1:
        if session.is_trading_session(d):
            sessions_.append(d.isoformat())
        d += dt.timedelta(days=1)
    if cad == "daily_close":
        return sessions_
    if cad == "friday_close":
        out = []
        for i, s in enumerate(sessions_):
            nxt = sessions_[i + 1] if i + 1 < len(sessions_) else None
            if nxt is None:
                if dt.date.fromisoformat(s).weekday() == 4:
                    out.append(s)
            elif dt.date.fromisoformat(nxt).isocalendar()[:2] != \
                    dt.date.fromisoformat(s).isocalendar()[:2]:
                out.append(s)
        return out
    rel = data.release_days(cad["release"], decision_instant(last, cmp.dsl["entry"]))
    out = []
    for day, avail in rel:
        if day < first or day > last:
            continue
        dd = day if cad["at"] == "day_of" else \
            session.previous_trading_session(dt.date.fromisoformat(day)).isoformat()
        if session.is_trading_session(dt.date.fromisoformat(dd)) and \
                avail <= decision_instant(dd, cmp.dsl["entry"]):
            out.append(dd)
    return sorted(set(out))


class Prices:
    """An instrument's stored bars for the simulation after a decision."""

    def __init__(self, data: Data, sym: str) -> None:
        self.sym = sym
        self.close = data.series(resolve(sym))
        has = sym in ohlc_symbols()
        self.open = data.series(resolve(sym, "open")) if has else None
        self.high = data.series(resolve(sym, "high")) if has else None
        self.low = data.series(resolve(sym, "low")) if has else None
        vk = resolve(sym) + "_volume"
        self.volume = data.series(vk) if data.store.all_vintages(vk) else None
        self.days = self.close.days

    def bar(self, day: str) -> dict:
        return {"day": day, "close": self.close.first(day),
                "open": self.open.first(day) if self.open else None,
                "high": self.high.first(day) if self.high else None,
                "low": self.low.first(day) if self.low else None}

    def after(self, day: str) -> list[str]:
        return self.days[bisect.bisect_right(self.days, day):]

    def adv(self, day: str, t: str, n: int = 20) -> Optional[float]:
        if not self.volume:
            return None
        cs = {d: v for d, v, _ in self.close.known(day, t, n)}
        vs = [(d, v) for d, v, _ in self.volume.known(day, t, n)]
        x = [cs[d] * v for d, v in vs if d in cs]
        return statistics.fmean(x) if x else None


def _cost_class(cmp: Compiled, sym: str) -> str:
    cfg = settings().get("cost_classes") or {}
    return cmp.dsl.get("cost_class") or (cfg.get("by_symbol") or {}).get(sym) \
        or cfg.get("default", "etf")


def leg_cost(cc: str, price: float, direction: int, days_held: float,
             adv: Optional[float], costs=None) -> float:
    """A round trip's modelled cost as a fraction of notional, at the size a
    new engine enters at: half the spread each way, slippage each way,
    commission each way, and borrow for a short over the days held."""
    from .costs import CostModel                                # noqa: PLC0415
    cm = costs or CostModel()
    notional = float(acfg.settings().get("notional_capital") or 100000) * \
        float(settings().get("costed_size", 0.01))
    qty = notional / price if price else 0.0
    half = cm.half_spread(cc, price) / price if price else 0.0
    slip = cm.slippage_bps(cc, notional, adv) / 1e4
    comm = cm.commission(cc, qty, notional) / notional if notional else 0.0
    hold = cm.holding(cc, direction, notional, days_held)
    return 2 * (half + slip + comm) + sum(hold.values()) / notional


def _vol(s: Series, day: str, t: str, n: int) -> Optional[float]:
    xs = s.known(day, t, n + 1)
    if len(xs) < n + 1:
        return None
    r = [xs[i][1] / xs[i - 1][1] - 1 for i in range(1, len(xs)) if xs[i - 1][1]]
    return statistics.stdev(r) if len(r) > 2 else None


def _atr(p: Prices, day: str, t: str, n: int) -> Optional[float]:
    cs = p.close.known(day, t, n + 1)
    if len(cs) < n + 1:
        return None
    trs = []
    for i in range(1, len(cs)):
        d, c, _ = cs[i]
        pc = cs[i - 1][1]
        h = p.high.first(d) if p.high else None
        lo = p.low.first(d) if p.low else None
        if h is not None and lo is not None:
            trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
        else:
            trs.append(abs(c - pc))
    return statistics.fmean(trs)


def _signal(cmp: Compiled, data: Data, day: str, t: str,
            trig: list[dict]) -> tuple[bool, str, str]:
    av = ""
    for c in trig:
        ok, a, why = holds(c, data, day, t)
        if not ok:
            return False, av, why or "condition false"
        av = max(av, a)
    return True, av, ""


def backtest(cmp: Compiled, store, first: str, last: str,
             drop: Optional[int] = None, data: Optional[Data] = None) -> dict:
    """Every trade the rule takes between `first` and `last`, point-in-time,
    net of modelled costs. One position at a time; the cooldown after a
    trigger. With `drop`, the rule without that trigger condition (a variant)."""
    data = data or Data(store)
    dsl = cmp.dsl
    trig = [c for i, c in enumerate(dsl["trigger"]) if i != drop]
    entry = dsl["entry"]
    ex = dsl["exits"]
    cooldown = int(dsl.get("cooldown") or 0)
    ins = dsl["instrument"]
    pair = ins.get("pair") if isinstance(ins, dict) else None
    legs = {s: Prices(data, s) for s in cmp.instruments}
    days = cadence_days(cmp, data, first, last)
    trades: list[dict] = []
    skipped: dict[str, int] = {}
    busy_until = ""
    cool_until = ""
    for day in days:
        if day <= busy_until or day <= cool_until:
            continue
        t = decision_instant(day, entry)
        ok, avail, why = _signal(cmp, data, day, t, trig)
        if not ok:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        wv: dict = {}
        if cmp.when:
            okw, aw, whyw, wv = when_ok(cmp, data, day, t)
            if not okw:
                skipped[whyw] = skipped.get(whyw, 0) + 1
                continue
            avail = max(avail, aw)
        d = dsl["direction"]
        if isinstance(d, dict):
            hit, a2, why2 = holds(d["if"], data, day, t)
            if hit is None:
                skipped["direction: " + why2] = skipped.get("direction: " + why2, 0) + 1
                continue
            avail = max(avail, a2)
            direction = 1 if (d["then"] if hit else d["else"]) == "long" else -1
        else:
            direction = 1 if d == "long" else -1
        cond = {}
        for v in cmp.variants:
            if v["kind"] == "state":
                cond[v["name"]] = data.state(day, t, v["path"])
        for c in dsl.get("conditioning") or []:
            if "condition" in c:
                h, a3, _ = holds(c["condition"], data, day, t)
                cond[c["name"]] = h
        tr = (_pair_trade if pair else _single_trade)(cmp, data, legs, day, t,
                                                      direction, entry, ex)
        if tr is None:
            skipped["no entry price within the wait"] = \
                skipped.get("no entry price within the wait", 0) + 1
            continue
        if tr.get("open"):
            skipped["open at the end of the data"] = \
                skipped.get("open at the end of the data", 0) + 1
            break
        tr.update({"signal_day": day, "day": day, "decided_at": t,
                   "available_at": avail, "direction": direction,
                   "conditioning": cond})
        if cmp.when:
            tr["when"] = wv
        trades.append(tr)
        busy_until = tr["exit_day"]
        if cooldown:
            ses = _sessions_after(day, cooldown)
            cool_until = ses[-1] if ses else day
    return {"trades": trades, "skipped": skipped, "cadence_days": len(days),
            "first": first, "last": last}


def _sessions_after(day: str, n: int) -> list[str]:
    out, d = [], dt.date.fromisoformat(day)
    while len(out) < n:
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            out.append(d.isoformat())
    return out


def _entry(p: Prices, day: str, entry: str) -> Optional[tuple[str, float, int]]:
    """(entry day, price, index of the entry bar in p.days) or None."""
    wait = int(settings().get("max_wait_sessions", 5))
    if entry == "this_close":
        c = p.close.first(day)
        return (day, c, p.days.index(day)) if c is not None else None
    for k, d in enumerate(p.after(day)[:wait]):
        b = p.bar(d)
        px = b["open"] if entry == "next_open" else b["close"]
        if px is not None:
            return d, px, p.days.index(d)
    return None


def _levels(cmp: Compiled, data: Data, p: Prices, day: str, t: str, entry_px: float,
            direction: int, ex: dict) -> tuple[Optional[float], Optional[float], str]:
    stop = target = None
    st, tg = ex.get("stop"), ex.get("target")
    note = ""
    if st:
        if "pct" in st:
            stop = entry_px * (1 - direction * float(st["pct"]) / 100.0)
        elif "atr" in st:
            a = _atr(p, day, t, int(st["n"]))
            if a is not None:
                stop = entry_px - direction * float(st["atr"]) * a
                if p.high is None:
                    note = "ATR on closes (no stored high/low)"
        elif "series" in st:
            e = evaluate(st, data, day, t)
            stop = e.value
    if tg:
        if "pct" in tg:
            target = entry_px * (1 + direction * float(tg["pct"]) / 100.0)
        elif "r" in tg and stop is not None:
            target = entry_px + direction * float(tg["r"]) * abs(entry_px - stop)
    return stop, target, note


def _single_trade(cmp, data, legs, day, t, direction, entry, ex) -> Optional[dict]:
    sym = cmp.instruments[0]
    p = legs[sym]
    e = _entry(p, day, entry)
    if e is None:
        return None
    eday, epx, ei = e
    stop, target, note = _levels(cmp, data, p, day, t, epx, direction, ex)
    tstop = int(ex["time"])
    opened_at_open = entry == "next_open"
    for k in range(ei, len(p.days)):
        d = p.days[k]
        b = p.bar(d)
        held = k - ei + (1 if opened_at_open else 0)
        if k == ei and not opened_at_open:
            continue
        o, h, lo, c = b["open"], b["high"], b["low"], b["close"]
        exit_px, reason = None, None
        if k == ei and stop is not None and direction * (epx - stop) <= 0:
            exit_px, reason = epx, "stop (the entry is already beyond it)"
        if exit_px is None and k > ei and o is not None:
            if stop is not None and direction * (o - stop) <= 0:
                exit_px, reason = o, "stop (gap through, at the open)"
            elif target is not None and direction * (o - target) >= 0:
                exit_px, reason = o, "target (gap through, at the open)"
        if exit_px is None and h is not None and lo is not None:
            s_hit = stop is not None and ((direction > 0 and lo <= stop) or
                                          (direction < 0 and h >= stop))
            t_hit = target is not None and ((direction > 0 and h >= target) or
                                            (direction < 0 and lo <= target))
            if s_hit:
                exit_px, reason = stop, "stop"
            elif t_hit:
                exit_px, reason = target, "target"
        if exit_px is None and h is None and c is not None:
            if stop is not None and direction * (c - stop) <= 0:
                exit_px, reason = c, "stop (on the close: no stored high/low)"
            elif target is not None and direction * (c - target) >= 0:
                exit_px, reason = c, "target (on the close: no stored high/low)"
        if exit_px is None and held >= tstop and c is not None:
            exit_px, reason = c, "time"
        if exit_px is not None:
            days_held = (dt.date.fromisoformat(d) - dt.date.fromisoformat(eday)).days
            gross = direction * (exit_px / epx - 1.0)
            cc = _cost_class(cmp, sym)
            cost = leg_cost(cc, epx, direction, days_held, p.adv(day, t))
            return {"instrument": sym, "entry_day": eday, "entry_price": epx,
                    "exit_day": d, "exit_price": exit_px, "exit_reason": reason,
                    "stop": stop, "target": target, "sessions": held,
                    "gross": gross, "cost": cost, "net": gross - cost,
                    "note": note}
    return {"open": True}


def _pair_trade(cmp, data, legs, day, t, direction, entry, ex) -> Optional[dict]:
    pr = cmp.dsl["instrument"]["pair"]
    L, S = legs[str(pr["long"]).upper()], legs[str(pr["short"]).upper()]
    eL, eS = _entry(L, day, entry), _entry(S, day, entry)
    if eL is None or eS is None or eL[0] != eS[0]:
        return None
    eday = eL[0]
    if pr.get("weight") == "vol_matched":
        vl = _vol(L.close, day, t, int(pr["n"]))
        vs = _vol(S.close, day, t, int(pr["n"]))
        if not vl or not vs:
            return None
        wl, ws = (1 / vl) / (1 / vl + 1 / vs), (1 / vs) / (1 / vl + 1 / vs)
    else:
        wl = ws = 0.5
    st = (ex.get("stop") or {}).get("pct")
    tg = (ex.get("target") or {}).get("pct")
    tstop = int(ex["time"])
    days_after = [d for d in L.after(eday if entry != "next_open" else day)
                  if S.close.first(d) is not None]
    if entry == "next_open":
        days_after = [d for d in days_after if d >= eday]
    held = 0
    for d in days_after:
        cl, cs = L.close.first(d), S.close.first(d)
        if cl is None or cs is None:
            continue
        held += 1
        r = direction * (wl * (cl / eL[1] - 1) - ws * (cs / eS[1] - 1))
        reason = None
        if st is not None and r <= -float(st) / 100.0:
            reason = "stop (on the close)"
        elif tg is not None and r >= float(tg) / 100.0:
            reason = "target (on the close)"
        elif held >= tstop:
            reason = "time"
        if reason:
            days_held = (dt.date.fromisoformat(d) - dt.date.fromisoformat(eday)).days
            cost = (wl * leg_cost(_cost_class(cmp, L.sym), eL[1], direction, days_held,
                                  L.adv(day, t))
                    + ws * leg_cost(_cost_class(cmp, S.sym), eS[1], -direction,
                                    days_held, S.adv(day, t)))
            return {"instrument": f"{L.sym}/{S.sym}", "entry_day": eday,
                    "entry_price": None, "exit_day": d, "exit_price": None,
                    "exit_reason": reason, "weights": {"long": wl, "short": ws},
                    "sessions": held, "gross": r, "cost": cost, "net": r - cost,
                    "note": ""}
    return {"open": True}


# ---------------------------------------------------------------------------
# Summaries for the verdict
# ---------------------------------------------------------------------------
def summarise(trades: list[dict]) -> dict:
    x = [t["net"] for t in trades]
    if not x:
        return {"n": 0}
    return {"n": len(x), "mean_net": statistics.fmean(x),
            "hit_rate": sum(1 for v in x if v > 0) / len(x),
            "mean_gross": statistics.fmean(t["gross"] for t in trades),
            "mean_cost": statistics.fmean(t["cost"] for t in trades),
            "sd": statistics.stdev(x) if len(x) > 1 else 0.0}


def by_variant(cmp: Compiled, trades: list[dict]) -> dict:
    """The base trades split by each state or condition variant's value."""
    out: dict[str, dict] = {}
    for v in cmp.variants:
        if v["kind"] in ("state", "condition"):
            sub = [t for t in trades
                   if (t["conditioning"].get(v["name"]) == v["value"]
                       if v["kind"] == "condition"
                       else str(t["conditioning"].get(v["name"])) == str(v["value"]))]
            out[f"{v['name']}={v['value']}"] = summarise(sub)
    return out


def variant_rule(cmp: Compiled, v: dict) -> tuple[Compiled, Optional[int]]:
    """The rule a drop or replace variant runs: (compiled, trigger index to
    drop). State and condition variants are splits of the base run instead."""
    if v["kind"] == "drop":
        return cmp, int(v["value"])
    if v["kind"] == "replace":
        base = {k: x for k, x in cmp.dsl.items() if k != "conditioning"}
        return compile_rule({**base, **v["value"]}), None
    raise ValueError(f"a {v['kind']} variant is a split of the base run")

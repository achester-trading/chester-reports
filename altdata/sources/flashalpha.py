"""
The FlashAlpha vendor writer (6b part 3; brief v2 sections 5.6 and 8, ruled 16
Oct 2026): the vendor's dealer readings stored beside the engine's, for the
Weekly's vendor line and the divergence data gate.

    python -m altdata.sources.flashalpha pull     # the 16:25 ET box unit

WHAT IT STORES (instrument = the symbol, observed on the session, available at
the response's capture instant -- point in time):
  dealer.vendor_gex_per_1pct   their GEX -- dollars per 1% move, compared with our
                               dollar_gamma_per_1pct (ledger
                               gex-scale-flashalpha-2026-10-09)
  dealer.vendor_dex_raw        their DEX -- raw-signed sum of delta x OI x 100 x S,
                               compared with our dex_raw_notional
  dealer.vendor_vex            their VEX, stored with its flag: UNRECONCILED (sign
                               and scale differ from ours; the ledger's open item)
  dealer.vendor_gamma_flip, dealer.vendor_call_wall, dealer.vendor_put_wall,
  dealer.vendor_spot           their levels and spot
A field the response does not carry is absent, never guessed.

THE KEY is FLASHALPHA_API_KEY, read through altdata.secrets by its existing name,
and never printed: every error string passes through secrets.redact, and the
summary carries only whether a key was configured. THE QUOTA is a session-set
daily call budget (config/flashalpha.yaml), counted in a state file; past it the
writer makes no call and says so.

Nothing here decides anything: a divergence is a question (tools/cross_check.py's
rule), flagged by the data gate tools/validate_vendor_divergence.py.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from .. import observations, session

log = logging.getLogger(__name__)

SOURCE = "flashalpha"
REPO = Path(__file__).resolve().parents[2]
KEYS = {"gex": "dealer.vendor_gex_per_1pct", "dex": "dealer.vendor_dex_raw",
        "vex": "dealer.vendor_vex", "flip": "dealer.vendor_gamma_flip",
        "call_wall": "dealer.vendor_call_wall", "put_wall": "dealer.vendor_put_wall",
        "spot": "dealer.vendor_spot"}
VEX_FLAG = "unreconciled: sign and scale differ from the engine's (ledger 9 Oct)"
TIMEOUT = 30


def config() -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((REPO / "config" / "flashalpha.yaml").read_text(encoding="utf-8"))


def _pick(d: Any, names: list[str]) -> Optional[float]:
    """The first named numeric field, in the body or one level down."""
    if not isinstance(d, dict):
        return None
    for n in names:
        v = d.get(n)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    for v in d.values():
        if isinstance(v, dict):
            got = _pick(v, names)
            if got is not None:
                return got
    return None


def parse(levels_body: dict, gex_body: Optional[dict], cfg: Optional[dict] = None) -> dict:
    """The stored fields from the two responses; absent where not carried."""
    cfg = cfg or config()
    lv = (levels_body or {}).get("levels") or {}
    fn = cfg.get("field_names") or {}
    num = lambda v: float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) \
        else None                                               # noqa: E731
    return {"flip": num(lv.get("gamma_flip")), "call_wall": num(lv.get("call_wall")),
            "put_wall": num(lv.get("put_wall")),
            "spot": num((levels_body or {}).get("underlying_price")),
            "gex": _pick(gex_body or {}, fn.get("net_gex") or []),
            "dex": _pick(gex_body or {}, fn.get("net_dex") or []),
            "vex": _pick(gex_body or {}, fn.get("net_vex") or []),
            "as_of": (levels_body or {}).get("as_of"),
            "oi_feed": ((levels_body or {}).get("data_as_of") or {}).get("oi_feed")}


def rows_from(symbol: str, fields: dict, day: str, captured_at: str) -> list[dict]:
    out = []
    for name, key in KEYS.items():
        v = fields.get(name)
        if v is None:
            continue
        row = {"registry_key": key, "instrument": symbol, "observed_at": day,
               "available_at": captured_at, "value": v, "source": SOURCE,
               "availability_kind": "observed"}
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# The quota
# ---------------------------------------------------------------------------
def _quota_path() -> Path:
    return Path(os.environ.get("CHESTER_STATE_DIR") or Path.home() / ".chester") \
        / "flashalpha_calls.json"


def calls_today(day: str, path: Optional[Path] = None) -> int:
    p = path or _quota_path()
    try:
        return int(json.loads(p.read_text(encoding="utf-8")).get(day, 0))
    except (OSError, ValueError):
        return 0


def _count_call(day: str, path: Optional[Path] = None) -> None:
    p = path or _quota_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    d = {day: int(d.get(day, 0)) + 1}
    p.write_text(json.dumps(d), encoding="utf-8")


# ---------------------------------------------------------------------------
# The pull
# ---------------------------------------------------------------------------
def _get(url: str, key: str) -> dict:
    import requests                                             # noqa: PLC0415
    r = requests.get(url, headers={"X-Api-Key": key, "Accept": "application/json"},
                     timeout=TIMEOUT)
    try:
        body = r.json()
    except ValueError:
        body = {}
    return {"status": r.status_code, "body": body,
            "quota_remaining": r.headers.get("X-RateLimit-Remaining")}


def pull(db=None, get: Optional[Callable[[str, str], dict]] = None,
         cfg: Optional[dict] = None, day: Optional[str] = None,
         quota_path: Optional[Path] = None) -> dict:
    """One run: two calls a symbol, inside the budget. `get(url, key)` defaults to
    the REST call; the gate passes a fake. Never raises; never prints the key."""
    from .. import secrets                                      # noqa: PLC0415
    cfg = cfg or config()
    day = day or session.session_date()
    if not (secrets.present("FLASHALPHA_API_KEY")
            and secrets.present("FLASHALPHA_BASE_URL")):
        return {"status": "SKIPPED", "reason": "FLASHALPHA_API_KEY or _BASE_URL not "
                                               "configured", "key_configured": False}
    key = secrets.get("FLASHALPHA_API_KEY")
    base = secrets.get("FLASHALPHA_BASE_URL").rstrip("/")
    get = get or _get
    budget = int(cfg.get("daily_call_budget", 30))
    out: dict[str, Any] = {"status": "OK", "key_configured": True, "symbols": {},
                           "written": 0, "calls": 0}
    rows: list[dict] = []
    for sym in cfg.get("symbols") or []:
        bodies = {}
        for name, path in (("levels", cfg["endpoints"]["levels"]),
                           ("gex", cfg["endpoints"]["gex"])):
            if calls_today(day, quota_path) >= budget:
                out["symbols"][sym] = f"skipped: the daily budget of {budget} calls is spent"
                out["status"] = "BUDGET"
                break
            try:
                res = get(base + path.format(symbol=sym), key)
            except Exception as exc:                            # noqa: BLE001
                res = {"status": None, "body": {},
                       "error": secrets.redact(f"{type(exc).__name__}: {exc}")}
            _count_call(day, quota_path)
            out["calls"] += 1
            bodies[name] = res
        lv = (bodies.get("levels") or {})
        if lv.get("status") != 200:
            out["symbols"].setdefault(sym, secrets.redact(
                f"levels: status {lv.get('status')} {lv.get('error') or ''}".strip()))
            continue
        fields = parse(lv.get("body") or {}, (bodies.get("gex") or {}).get("body"), cfg)
        got = rows_from(sym, fields, day, session.utc_iso())
        rows += got
        out["symbols"][sym] = {"stored": [r["registry_key"] for r in got],
                               "absent": [KEYS[k] for k in KEYS if fields.get(k) is None]}
    if rows:
        if db is None:
            with observations.ObservationStore() as st:
                st.write_many(rows)
        else:
            db.write_many(rows)
        out["written"] = len(rows)
    return out


# ---------------------------------------------------------------------------
# The comparison: the Weekly's vendor line and the divergence gate
# ---------------------------------------------------------------------------
def stored(st, cutoff: str, symbol: str, day: Optional[str] = None) -> dict:
    """The newest stored vendor values for `symbol` (on `day` when given)."""
    out = {}
    for name, key in KEYS.items():
        rows = [r for r in st.as_of(key, cutoff, symbol)
                if r.get("value_num") is not None
                and (day is None or str(r["observed_at"])[:10] == day)]
        if rows:
            out[name] = float(rows[-1]["value_num"])
            out["day"] = str(rows[-1]["observed_at"])[:10]
            out["at"] = rows[-1].get("available_at")
    return out


def compare(vendor: dict, profile: dict, cfg: Optional[dict] = None) -> list[dict]:
    """Each pair: ours, theirs, the gap, and whether it passes the session-set
    threshold. VEX is never compared: it carries its flag."""
    cfg = cfg or config()
    d = cfg.get("divergence") or {}
    o, spot = profile.get("overall") or {}, profile.get("spot")
    out = []

    def rel(a, b):
        return abs(a - b) / max(abs(a), abs(b)) if a is not None and b is not None \
            and max(abs(a), abs(b)) else None

    def pct(a, b):
        return abs(a - b) / spot * 100.0 if a is not None and b is not None and spot \
            else None
    for name, ours, theirs, kind, lim in (
            ("GEX ($/1%)", o.get("dollar_gamma_per_1pct"), vendor.get("gex"), "rel",
             d.get("gex_rel", 0.5)),
            ("DEX, raw-signed ($)", o.get("dex_raw_notional"), vendor.get("dex"), "rel",
             d.get("dex_rel", 0.15)),
            ("Zero-gamma level", o.get("gamma_flip"), vendor.get("flip"), "pct",
             d.get("flip_pct", 1.0)),
            ("Call wall (ours: OTM)", o.get("call_wall_otm"), vendor.get("call_wall"),
             "pct", d.get("wall_pct", 1.5)),
            ("Put wall (ours: OTM)", o.get("put_wall_otm"), vendor.get("put_wall"),
             "pct", d.get("wall_pct", 1.5))):
        gap = rel(ours, theirs) if kind == "rel" else pct(ours, theirs)
        out.append({"name": name, "ours": ours, "theirs": theirs, "gap": gap,
                    "kind": kind, "threshold": lim,
                    "flag": None if gap is None else gap > float(lim)})
    out.append({"name": "VEX", "ours": o.get("vex_notional_per_volpt"),
                "theirs": vendor.get("vex"), "gap": None, "kind": "flag",
                "threshold": None, "flag": None, "note": VEX_FLAG})
    return out


def vendor_line(vendor: dict, profile: Optional[dict], cfg: Optional[dict] = None) -> list[str]:
    """The Weekly's vendor line (brief v2 section 5.6): read from the stored
    series, never fetched."""
    if not vendor:
        return ["FlashAlpha: no stored vendor reading this week (the 16:25 writer)."]
    if not profile:
        return [f"FlashAlpha, {vendor.get('day')}: stored, but no engine profile to set "
                f"it against."]
    lines = [f"FlashAlpha, {vendor.get('day')} (their capture after our 16:10; one OI "
             f"vintage; a gap is a question, never a correction):"]
    for c in compare(vendor, profile, cfg):
        if c["kind"] == "flag":
            lines.append(f"VEX: theirs {c['theirs'] if c['theirs'] is not None else 'n/a'}"
                         f" -- {c['note']}.")
            continue
        if c["ours"] is None or c["theirs"] is None:
            lines.append(f"{c['name']}: {'ours' if c['ours'] is None else 'theirs'} "
                         f"not stored.")
            continue
        unit = "%" if c["kind"] == "rel" else "% of spot"
        g = c["gap"] * 100 if c["kind"] == "rel" else c["gap"]
        lines.append(f"{c['name']}: ours {c['ours']:,.2f}, theirs {c['theirs']:,.2f}, "
                     f"gap {g:.1f}{unit}"
                     + (f" -- past the {c['threshold']:g} threshold" if c["flag"] else ""))
    return lines


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.sources.flashalpha")
    ap.add_argument("cmd", choices=["pull"])
    ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    res = pull()
    print(json.dumps(res, indent=2, default=str))
    return 0 if res.get("status") in ("OK", "SKIPPED", "BUDGET") else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

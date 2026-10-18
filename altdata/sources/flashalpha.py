"""
The FlashAlpha vendor writer (6b part 3; reconfigured by F-1, F-2 and F-4, ruled
18 Oct 2026, a43-render): the vendor's readings stored beside the engine's, for
the Weekly's vendor row and the divergence data gate.

    python -m altdata.sources.flashalpha pull [--slot 1625|0945|1230]

THE PLAN (config/flashalpha.yaml, slots), at most 60 requests a day:
  16:25  for SPY, QQQ, IWM, SPX and MSTR: the stock summary, levels, max pain,
         expected move, DEX, VEX and CHEX; the surface for SPY and QQQ; GEX by
         single expiry for the nearest five SPY and three SPX expiries -- 45
  09:45, 12:30  the summary and levels for SPY, QQQ and SPX -- 6 each
  57 in all. Every request is counted before it is made; past the budget the
  writer makes no call and says so.

WHAT IT STORES (instrument = the symbol at 16:25, "SYMBOL@0945" / "@1230" for
the intraday slots, so the 16:25 comparison never reads an intraday row;
observed on the session, available at the response's capture instant):
  dealer.vendor_*    the exposure block: net GEX ($ per 1%), net DEX (raw-signed),
                     VEX (flagged unreconciled), CHEX, the flip, the walls, max
                     pain, the regime word, spot; from max pain its compact fields
                     (the strike, pin probability, the alignment word, the put/call
                     OI ratio)
  vendor.*           the volatility block (ATM IV, 20-day realized) and the macro
                     block (VIX9D, VIX, VIX3M, VIX6M, the VIX futures front month
                     and basis, VVIX, SKEW, MOVE, Fear & Greed), instrument None
  vendor.atm_iv_20dte  ATM IV of the first listed expiry of 20 DTE or more, from
                     the 16:25 expected-move response: the ONE vendor IV compared
                     (F-2); front-expiry IVs live only in the blobs
  BLOBS              the whole responses of max pain (OI by strike, max pain by
                     expiration), expected move, DEX/VEX/CHEX by strike, the
                     surface and GEX by expiry, one JSON file each, under
                     config blob_dir/<day>/; never store rows
A field a response does not carry is absent, never guessed.

THE CONVENTIONS (F-3; the technical appendix and docs/ledgers/
vendor-divergence-notes.md carry them in full). The vendor's GEX is
sum(dealer position x gamma x OI x 100 x spot^2 x 0.01), dollars per 1% move, calls
positive and puts negative, on prior-night settled OI and THEIR OWN IV -- our
dollar_gamma_per_1pct in the same terms, on our IV. Their DEX is the customer
book's raw-signed sum (calls positive), ours the dealer position. Their walls are
all-strike peaks; ours, from Thursday, the OTM walls.

NOTHING HERE DECIDES ANYTHING. No engine, flag, tell, dial or decision reads a
vendor value; a divergence is a question (tools/cross_check.py's rule), flagged
by the data gate. THE KEY is FLASHALPHA_API_KEY through altdata.secrets, never
printed. F-4: from the day after plan_ends the writer stops and the Weekly's row
says "vendor: plan ended".
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
TIER = "vendor"
REPO = Path(__file__).resolve().parents[2]
# The comparison keys (6b part 3), unchanged.
KEYS = {"gex": "dealer.vendor_gex_per_1pct", "dex": "dealer.vendor_dex_raw",
        "vex": "dealer.vendor_vex", "flip": "dealer.vendor_gamma_flip",
        "call_wall": "dealer.vendor_call_wall", "put_wall": "dealer.vendor_put_wall",
        "spot": "dealer.vendor_spot"}
# F-1's further fields. Exposure and max pain per symbol; volatility per symbol;
# the macro block under no instrument.
EXTRA_KEYS = {"chex": "dealer.vendor_chex", "max_pain": "dealer.vendor_max_pain",
              "regime": "dealer.vendor_regime",
              "pin_probability": "dealer.vendor_pin_probability",
              "alignment": "dealer.vendor_mp_alignment",
              "pc_oi_ratio": "dealer.vendor_pc_oi_ratio",
              "atm_iv": "vendor.atm_iv", "hv_20": "vendor.hv_20",
              "atm_iv_20dte": "vendor.atm_iv_20dte"}
MACRO_KEYS = {"vix9d": "vendor.vix9d", "vix": "vendor.vix", "vix3m": "vendor.vix3m",
              "vix6m": "vendor.vix6m", "vx_front": "vendor.vx_front",
              "vx_basis_pct": "vendor.vx_basis_pct", "vvix": "vendor.vvix",
              "skew": "vendor.skew", "move": "vendor.move",
              "fear_greed": "vendor.fear_greed"}
ALL_KEYS = list(KEYS.values()) + list(EXTRA_KEYS.values()) + list(MACRO_KEYS.values())
# THE FRESHNESS ROSTER (ruling 3 of 17 Oct 2026): the levels endpoint's fields.
ROSTER_KEYS = [KEYS["flip"], KEYS["call_wall"], KEYS["put_wall"], KEYS["spot"]]
VEX_FLAG = "unreconciled: sign and scale differ from the engine's (ledger 9 Oct)"
# Ruling 2 of 18 Oct 2026: a 403 or 404 on the expected-move path stores nothing and
# says so; the 20-day IV comparison waits for it.
EM_NOT_SERVED = "expected move: not served"
PLAN_ENDED = "vendor: plan ended"
TIMEOUT = 30


def config() -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((REPO / "config" / "flashalpha.yaml").read_text(encoding="utf-8"))


def plan_ended(day: str, cfg: Optional[dict] = None) -> bool:
    end = str((cfg or config()).get("plan_ends") or "")
    return bool(end) and day > end


def _num(v) -> Optional[float]:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _pick(d: Any, names: list[str]) -> Optional[float]:
    """The first named numeric field, in the body or one level down."""
    if not isinstance(d, dict):
        return None
    for n in names:
        v = _num(d.get(n))
        if v is not None:
            return v
    for v in d.values():
        if isinstance(v, dict):
            got = _pick(v, names)
            if got is not None:
                return got
    return None


def _pick_text(d: Any, names: list[str]) -> Optional[str]:
    if not isinstance(d, dict):
        return None
    for n in names:
        v = d.get(n)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for v in d.values():
        if isinstance(v, dict):
            got = _pick_text(v, names)
            if got:
                return got
    return None


# ---------------------------------------------------------------------------
# The parsers -- each reproduced on the 16 Oct responses' shape in the gate
# ---------------------------------------------------------------------------
def parse(levels_body: dict, gex_body: Optional[dict], cfg: Optional[dict] = None) -> dict:
    """6b part 3's two-response parse (levels, and an all-expiry GEX body)."""
    cfg = cfg or config()
    lv = (levels_body or {}).get("levels") or {}
    fn = cfg.get("field_names") or {}
    return {"flip": _num(lv.get("gamma_flip")), "call_wall": _num(lv.get("call_wall")),
            "put_wall": _num(lv.get("put_wall")),
            "spot": _num((levels_body or {}).get("underlying_price")),
            "gex": _pick(gex_body or {}, fn.get("net_gex") or []),
            "dex": _pick(gex_body or {}, fn.get("net_dex") or []),
            "vex": _pick(gex_body or {}, fn.get("net_vex") or []),
            "as_of": (levels_body or {}).get("as_of"),
            "oi_feed": ((levels_body or {}).get("data_as_of") or {}).get("oi_feed")}


def parse_summary(body: dict) -> tuple[dict, dict]:
    """(per-symbol fields, macro fields) from the stock summary."""
    b = body or {}
    ex, vo, ma = b.get("exposure") or {}, b.get("volatility") or {}, b.get("macro") or {}
    price = b.get("price") or {}
    per = {"gex": _num(ex.get("net_gex")), "dex": _num(ex.get("net_dex")),
           "vex": _num(ex.get("net_vex")), "chex": _num(ex.get("net_chex")),
           "flip": _num(ex.get("gamma_flip")), "call_wall": _num(ex.get("call_wall")),
           "put_wall": _num(ex.get("put_wall")), "max_pain": _num(ex.get("max_pain")),
           "regime": ex.get("regime") if isinstance(ex.get("regime"), str) else None,
           "spot": _num(price.get("last")) or _num(price.get("mid")),
           "atm_iv": _num(vo.get("atm_iv")), "hv_20": _num(vo.get("hv_20"))}
    lv = (ma.get("vix_term_structure") or {}).get("levels") or {}
    fut = ma.get("vix_futures") or {}

    def val(k):
        x = ma.get(k)
        return _num(x.get("value")) if isinstance(x, dict) else _num(x)
    macro = {"vix9d": _num(lv.get("vix9d")), "vix": _num(lv.get("vix")) or val("vix"),
             "vix3m": _num(lv.get("vix3m")), "vix6m": _num(lv.get("vix6m")),
             "vx_front": _num(fut.get("front_month")),
             "vx_basis_pct": _num(fut.get("basis_pct")),
             "vvix": val("vvix"), "skew": val("skew"), "move": val("move"),
             "fear_greed": _num((ma.get("fear_and_greed") or {}).get("score"))}
    return per, macro


def parse_max_pain(body: dict, cfg: Optional[dict] = None) -> dict:
    """The compact fields; the curve and the per-expiration breakdown stay in the
    day's blob."""
    fn = (cfg or config()).get("field_names") or {}
    b = body or {}
    return {"max_pain": _pick(b, fn.get("max_pain_strike") or []),
            "pin_probability": _pick(b, fn.get("pin_probability") or []),
            "alignment": _pick_text(b, fn.get("alignment") or []),
            "pc_oi_ratio": _pick(b, fn.get("pc_oi_ratio") or [])}


def expiries_of(*bodies: dict) -> list[dict]:
    """[{expiry, dte, atm_iv}] listed in an expected-move or max-pain response:
    any list of dicts carrying an expiry date."""
    out: dict[str, dict] = {}

    def walk(x):
        if isinstance(x, dict):
            e = x.get("expiry") or x.get("expiration") or x.get("expiration_date")
            if isinstance(e, str) and len(e) >= 10 and e[:4].isdigit():
                d = out.setdefault(e[:10], {"expiry": e[:10]})
                for k in ("dte", "days_to_expiry", "daysToExpiry"):
                    if _num(x.get(k)) is not None:
                        d["dte"] = _num(x.get(k))
                for k in ("atm_iv", "atmIv", "iv"):
                    if _num(x.get(k)) is not None:
                        d["atm_iv"] = _num(x.get(k))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    for b in bodies:
        walk(b or {})
    return [out[k] for k in sorted(out)]


def iv_comparable(slot: str, dte: Optional[float], cfg: Optional[dict] = None) -> bool:
    """F-2: a vendor ATM IV is compared only on an expiry of 20 DTE or more and
    only from the 16:25 capture."""
    c = (cfg or config()).get("iv_compare") or {}
    return (slot == str(c.get("slot", "1625")) and dte is not None
            and dte >= float(c.get("min_dte", 20)))


def first_20dte(expiries: list[dict], day: str, cfg: Optional[dict] = None) -> Optional[dict]:
    c = (cfg or config()).get("iv_compare") or {}
    lo = float(c.get("min_dte", 20))
    d0 = dt.date.fromisoformat(day)
    for e in expiries:
        dte = e.get("dte")
        if dte is None:
            dte = (dt.date.fromisoformat(e["expiry"]) - d0).days
        if dte >= lo and e.get("atm_iv") is not None:
            return dict(e, dte=dte)
    return None


def rows_from(symbol: Optional[str], fields: dict, day: str, captured_at: str,
              keys: Optional[dict] = None) -> list[dict]:
    keys = keys or KEYS
    out = []
    for name, key in keys.items():
        v = fields.get(name)
        if v is None:
            continue
        out.append({"registry_key": key, "instrument": symbol, "observed_at": day,
                    "available_at": captured_at, "value": v, "source": SOURCE,
                    "availability_kind": "observed"})
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


def planned(cfg: Optional[dict] = None) -> dict[str, int]:
    """{slot: requests} for a full day, GEX expiries at their configured counts:
    what the budget is set against."""
    cfg = cfg or config()
    out = {}
    for slot, s in (cfg.get("slots") or {}).items():
        n = len(s.get("symbols") or []) * len(s.get("per_symbol") or [])
        n += len(s.get("surface") or [])
        n += sum(int(v) for v in (s.get("gex_by_expiry") or {}).values())
        out[slot] = n
    return out


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


def _blob(cfg: dict, day: str, slot: str, name: str, body: dict,
          blob_dir: Optional[Path] = None) -> Optional[str]:
    d = Path(blob_dir or (REPO / str(cfg.get("blob_dir") or "data/vendor/flashalpha"))) / day
    try:
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{slot}_{name}.json"
        p.write_text(json.dumps(body, default=str), encoding="utf-8")
        return str(p)
    except OSError:
        return None


def pull(db=None, get: Optional[Callable[[str, str], dict]] = None,
         cfg: Optional[dict] = None, day: Optional[str] = None,
         quota_path: Optional[Path] = None, slot: str = "1625",
         blob_dir: Optional[Path] = None) -> dict:
    """One slot's run, inside the budget. `get(url, key)` defaults to the REST call;
    the gate passes a fake. Never raises; never prints the key."""
    from .. import secrets                                      # noqa: PLC0415
    cfg = cfg or config()
    day = day or session.session_date()
    if plan_ended(day, cfg):
        return {"status": "PLAN_ENDED", "reason": f"the plan ended {cfg.get('plan_ends')}; "
                                                  "no call made", "calls": 0, "written": 0}
    if not (secrets.present("FLASHALPHA_API_KEY")
            and secrets.present("FLASHALPHA_BASE_URL")):
        return {"status": "SKIPPED", "reason": "FLASHALPHA_API_KEY or _BASE_URL not "
                                               "configured", "key_configured": False}
    key = secrets.get("FLASHALPHA_API_KEY")
    base = secrets.get("FLASHALPHA_BASE_URL").rstrip("/")
    get = get or _get
    budget = int(cfg.get("daily_call_budget", 60))
    plan = (cfg.get("slots") or {}).get(slot) or {}
    eps = cfg["endpoints"]
    out: dict[str, Any] = {"status": "OK", "slot": slot, "key_configured": True,
                           "symbols": {}, "written": 0, "calls": 0, "blobs": [],
                           "refused": []}
    rows: list[dict] = []
    now = session.utc_iso()

    def call(name: str, sym: str, query: str = "") -> Optional[dict]:
        if calls_today(day, quota_path) >= budget:
            out["status"] = "BUDGET"
            out["refused"].append(f"{name} {sym}")
            return None
        try:
            res = get(base + eps[name].format(symbol=sym) + query, key)
        except Exception as exc:                                # noqa: BLE001
            res = {"status": None, "body": {},
                   "error": secrets.redact(f"{type(exc).__name__}: {exc}")}
        _count_call(day, quota_path)
        out["calls"] += 1
        if name == "expected_move" and res.get("status") in (403, 404):
            out["symbols"].setdefault(sym, {})["expected_move"] = EM_NOT_SERVED
            out["expected_move"] = EM_NOT_SERVED
            return None
        if res.get("status") != 200:
            out["symbols"].setdefault(sym, {}).setdefault("errors", []).append(
                secrets.redact(f"{name}: status {res.get('status')} "
                               f"{res.get('error') or ''}".strip()))
            return None
        return res.get("body") or {}

    inst = (lambda s: s) if slot == "1625" else (lambda s: f"{s}@{slot}")
    macro_done = False
    for sym in plan.get("symbols") or []:
        got: dict[str, dict] = {}
        for name in plan.get("per_symbol") or []:
            b = call(name, sym)
            if b is None:
                continue
            got[name] = b
            if name in (plan.get("blobs") or []):
                p = _blob(cfg, day, slot, f"{sym}_{name}", b, blob_dir)
                if p:
                    out["blobs"].append(p)
        per, macro = parse_summary(got.get("summary") or {})
        lv = parse(got.get("levels") or {}, None, cfg)
        for k in ("flip", "call_wall", "put_wall", "spot"):
            if per.get(k) is None:
                per[k] = lv.get(k)
        mp = parse_max_pain(got.get("max_pain") or {}, cfg)
        per.update({k: v for k, v in mp.items() if v is not None
                    and (k != "max_pain" or per.get("max_pain") is None)})
        exps = expiries_of(got.get("expected_move") or {}, got.get("max_pain") or {})
        if slot == "1625":
            e20 = first_20dte(exps, day, cfg)
            if e20 and iv_comparable(slot, e20["dte"], cfg):
                per["atm_iv_20dte"] = e20["atm_iv"]
                out["symbols"].setdefault(sym, {})["iv_expiry"] = e20["expiry"]
        got_rows = rows_from(inst(sym), per, day, now, {**KEYS, **EXTRA_KEYS})
        if not macro_done and any(v is not None for v in macro.values()):
            got_rows += rows_from(None if slot == "1625" else f"@{slot}", macro, day, now,
                                  MACRO_KEYS)
            macro_done = True
        rows += got_rows
        info = out["symbols"].setdefault(sym, {})
        info["stored"] = [r["registry_key"] for r in got_rows]
        info["absent"] = [k for k in list(KEYS.values()) + list(EXTRA_KEYS.values())
                          if k not in info["stored"]]
        n = int((plan.get("gex_by_expiry") or {}).get(sym, 0))
        today = dt.date.fromisoformat(day)
        near = [e["expiry"] for e in exps if dt.date.fromisoformat(e["expiry"]) >= today][:n]
        if n and len(near) < n:
            info["gex_expiries_short"] = f"{len(near)} of {n} expiries listed"
        for e in near:
            b = call("gex", sym, f"?expiration={e}")
            if b is not None:
                p = _blob(cfg, day, slot, f"{sym}_gex_{e}", b, blob_dir)
                if p:
                    out["blobs"].append(p)
    for sym in plan.get("surface") or []:
        b = call("surface", sym)
        if b is not None:
            p = _blob(cfg, day, slot, f"{sym}_surface", b, blob_dir)
            if p:
                out["blobs"].append(p)
    if out["refused"]:
        out["budget_note"] = (f"the daily budget of {budget} requests is spent; "
                              f"{len(out['refused'])} not made")
    if rows:
        if db is None:
            with observations.ObservationStore() as st:
                st.write_many(rows)
        else:
            db.write_many(rows)
        out["written"] = len(rows)
    return out


# ---------------------------------------------------------------------------
# The comparison: the Weekly's vendor row and the divergence gate
# ---------------------------------------------------------------------------
def stored(st, cutoff: str, symbol: str, day: Optional[str] = None) -> dict:
    """The newest stored 16:25 vendor values for `symbol` (on `day` when given)."""
    out = {}
    for name, key in {**KEYS, **EXTRA_KEYS}.items():
        rows = [r for r in st.as_of(key, cutoff, symbol)
                if (r.get("value_num") is not None or r.get("value_text"))
                and (day is None or str(r["observed_at"])[:10] == day)]
        if rows:
            r = rows[-1]
            out[name] = float(r["value_num"]) if r.get("value_num") is not None \
                else r.get("value_text")
            out["day"] = str(r["observed_at"])[:10]
            out["at"] = r.get("available_at")
    return out


def our_regime(profile: dict) -> Optional[str]:
    g = (profile.get("overall") or {}).get("dollar_gamma_per_1pct")
    return None if g is None else ("negative_gamma" if g < 0 else "positive_gamma")


def compare(vendor: dict, profile: dict, cfg: Optional[dict] = None) -> list[dict]:
    """Each pair: ours, theirs, the gap, and whether it passes the threshold. VEX is
    never compared (it carries its flag); the regime is compared as a word."""
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
             d.get("flip_pct", 0.5)),
            ("Call wall (ours: OTM)", o.get("call_wall_otm"), vendor.get("call_wall"),
             "pct", d.get("wall_pct", 1.5)),
            ("Put wall (ours: OTM)", o.get("put_wall_otm"), vendor.get("put_wall"),
             "pct", d.get("wall_pct", 1.5))):
        gap = rel(ours, theirs) if kind == "rel" else pct(ours, theirs)
        out.append({"name": name, "ours": ours, "theirs": theirs, "gap": gap,
                    "kind": kind, "threshold": lim,
                    "flag": None if gap is None else gap > float(lim)})
    if d.get("regime", True):
        ours_r, theirs_r = our_regime(profile), vendor.get("regime")
        out.append({"name": "Regime", "ours": ours_r, "theirs": theirs_r, "gap": None,
                    "kind": "word", "threshold": None,
                    "flag": None if not ours_r or not theirs_r else ours_r != theirs_r})
    out.append({"name": "VEX", "ours": o.get("vex_notional_per_volpt"),
                "theirs": vendor.get("vex"), "gap": None, "kind": "flag",
                "threshold": None, "flag": None, "note": VEX_FLAG})
    return out


def mechanics_row(vendor: dict, day: Optional[str] = None,
                  cfg: Optional[dict] = None) -> dict:
    """F-4: the Weekly's mechanics table's one vendor row -- the flip, the walls,
    max pain, the regime, net GEX in both units ($ per 1% and $ per one-point
    move, the per-1% figure over 0.01 x spot)."""
    cols = ["Source", "Flip", "Call wall", "Put wall", "Max pain", "Regime",
            "Net GEX ($ per 1%)", "Net GEX ($ per point)"]
    if day and plan_ended(day, cfg):
        return {"columns": cols, "rows": [[PLAN_ENDED] + [""] * (len(cols) - 1)]}
    if not vendor:
        return {"columns": cols, "rows": [["vendor (FlashAlpha): not stored"]
                                          + [""] * (len(cols) - 1)]}

    def f(v, nd=2):
        return "n/a" if v is None else f"{v:,.{nd}f}"

    def bn(v):
        return "n/a" if v is None else f"{v / 1e9:+,.2f}bn"
    g, s = vendor.get("gex"), vendor.get("spot")
    per_pt = g / (0.01 * s) if g is not None and s else None
    return {"columns": cols,
            "rows": [[f"vendor (FlashAlpha), {vendor.get('day')}", f(vendor.get("flip")),
                      f(vendor.get("call_wall"), 0), f(vendor.get("put_wall"), 0),
                      f(vendor.get("max_pain"), 0), str(vendor.get("regime") or "n/a"),
                      bn(g), bn(per_pt)]]}


def vendor_line(vendor: dict, profile: Optional[dict], cfg: Optional[dict] = None,
                day: Optional[str] = None) -> list[str]:
    """The Weekly's vendor line (brief v2 section 5.6): read from the stored series,
    never fetched."""
    if day and plan_ended(day, cfg):
        return [f"{PLAN_ENDED} ({(cfg or config()).get('plan_ends')}); the writer "
                "stopped and nothing new is stored."]
    if not vendor:
        return ["FlashAlpha (vendor): no stored vendor reading this week (the 16:25 "
                "writer)."]
    if not profile:
        return [f"FlashAlpha (vendor), {vendor.get('day')}: stored, but no engine "
                f"profile to set it against."]
    # RULING 3 OF 17 OCT 2026: a cross-check printed beside the engine's figures,
    # labelled vendor, never in place of them.
    lines = [f"FlashAlpha (vendor), {vendor.get('day')}, beside the engine's own "
             f"figures (their capture after our 16:10; one OI vintage; a gap is a "
             f"question, never a correction):"]
    for c in compare(vendor, profile, cfg):
        if c["kind"] == "flag":
            lines.append(f"VEX: theirs {c['theirs'] if c['theirs'] is not None else 'n/a'}"
                         f" -- {c['note']}.")
            continue
        if c["kind"] == "word":
            if c["ours"] and c["theirs"]:
                lines.append(f"Regime: ours {c['ours']}, theirs {c['theirs']}"
                             + (" -- they disagree" if c["flag"] else ""))
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
    ap.add_argument("--slot", default="1625", choices=["1625", "0945", "1230"])
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    res = pull(slot=a.slot)
    if res.get("status") in ("OK", "BUDGET") and a.slot == "1625":
        from .. import feeds                                    # noqa: PLC0415
        feeds.record_attempted("vendor", ROSTER_KEYS)
    if res.get("expected_move"):
        print(res["expected_move"])
    print(json.dumps(res, indent=2, default=str))
    return 0 if res.get("status") in ("OK", "SKIPPED", "BUDGET", "PLAN_ENDED") else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

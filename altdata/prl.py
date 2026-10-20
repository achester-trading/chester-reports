"""
THE PRL DATA LAYER (ST-13, signal-triage Tranche 5; st-t5-prl, 18 Oct 2026): the
emission calculator of Appendix E, the derived metrics D1-D6 of 2.7.4 as
calc.prl_* rows, and the thesis-status rule of 2.7.5 with its trace.

    python -m altdata.prl compute [--as-of ISO] [--db PATH] [--dry-run]
    python -m altdata.prl show    [--as-of ISO] [--db PATH]          # reads only

Config: config/prl.yaml. Watch-level rights only (MW-2): no composite, overlay,
dial, band, tell or trigger reads any of this; D6 (the idle-GPU flag) is the one
narrow flag. Nothing here renders: ST-14 renders, and the Daily carries no PRL
line (the grep gate).

THE EMISSION (Appendix E). Max supply 2.1e9, K = 650,226, no halvings:

    reward(h)      = 2.1e9 * K / ((h + K) * (h - 1 + K))
    supply_code(H) = 2.1e9 * H / (H + K)          (D1; the reward's telescoping sum)

reward(1) = 3,229.6; reward(113,770) = 2,339.4; supply_code(113,770) = 312.72M
(the order's three unit tests, tools/validate_st_t5_prl.py).

THE HEIGHT. The explorer's observed height (pearl.chain_height) where one is
stored at the cutoff; otherwise ESTIMATED -- the newest observed height (else the
config's anchor, Appendix E's block 113,770 at 2026-09-15 23:53 UTC) stepped
forward at the 194 s target -- and every figure computed from it carries the
ESTIMATED marker in its trace. A fallback that reads nothing prints ESTIMATED,
never a blank (G-26).

D1 supply_code(H)                          calc.prl_supply_code      PRL
D2 week-one overhang  121.70e6 / D1        calc.prl_overhang         percent_share
D3 supply gap         D1 at the explorer's height less the explorer's supply
                      (ruling 1 of 18 Oct 2026); ESTIMATED, no row, until the
                      explorer reads           calc.prl_supply_gap       PRL
D4 emission-to-volume reward(H) * 86400/194 * price / volume_24h, Yahoo's price
                      and 24h volume at the basket's symbol
                                           calc.prl_emission_to_volume  ratio
D5 venue concentration  NOT TRACKED (source retired): its only input was
                      CoinGecko's tickers  calc.prl_venue_conc       percent_share
D6 idle-GPU flag      ON when difficulty is up > 25% over 30 days while price is
                      down > 20% over the same 30 days
                                           calc.prl_idle_gpu_flag    boolean
the thesis status     UNCHANGED / IMPROVED / DETERIORATED by rule, its trace
                      beside it (an informational label, no decision rights)
                                           calc.prl_thesis_status    label

Every row is point in time: each input is read as of the cutoff, and a row's
available_at is the latest of its inputs' (a figure is never knowable before the
data it is made of). An input that is absent leaves its figure absent, with the
reason; nothing is substituted except the declared fallbacks of config/prl.yaml,
which the trace names.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "prl.yaml"
SOURCE = "calc"
ESTIMATED = "ESTIMATED"
HEIGHT_KEY = "pearl.chain_height"
DIFFICULTY_KEY = "pearl.chain_difficulty"
SUPPLY_KEY = "pearl.chain_supply"
ROSTER = "prl"
# What the heartbeat watches (ruling 3 of 18 Oct 2026): the daily compute's keys,
# which every run writes, and the explorer's, which the weekly step writes once
# an endpoint is declared (PENDING, with no allowance running, until then).
DAILY_KEYS = ["calc.prl_reward", "calc.prl_supply_code", "calc.prl_overhang",
              "calc.prl_thesis_status"]
EXPLORER_KEYS = [HEIGHT_KEY, DIFFICULTY_KEY, SUPPLY_KEY]
ROSTER_KEYS = DAILY_KEYS + EXPLORER_KEYS

KEYS = {"reward": "calc.prl_reward", "height_estimated": "calc.prl_height_estimated",
        "supply_code": "calc.prl_supply_code", "overhang": "calc.prl_overhang",
        "supply_gap": "calc.prl_supply_gap",
        "emission_to_volume": "calc.prl_emission_to_volume",
        "venue_conc": "calc.prl_venue_conc", "idle_gpu_flag": "calc.prl_idle_gpu_flag",
        "thesis_status": "calc.prl_thesis_status"}


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# The emission (Appendix E)
# ---------------------------------------------------------------------------
def reward(h: int, cfg: Optional[dict] = None) -> float:
    """The block reward at height h >= 1, in PRL."""
    e = (cfg or config())["emission"]
    S, K = float(e["max_supply"]), float(e["K"])
    if h < 1:
        raise ValueError(f"height {h}: the first block is 1")
    return S * K / ((h + K) * (h - 1 + K))


def supply_code(H: float, cfg: Optional[dict] = None) -> float:
    """D1: the supply the code has emitted through height H, in PRL."""
    e = (cfg or config())["emission"]
    S, K = float(e["max_supply"]), float(e["K"])
    return S * H / (H + K)


def daily_emission(H: float, cfg: Optional[dict] = None) -> float:
    """PRL a day at the target pace and the reward at H."""
    e = (cfg or config())["emission"]
    return reward(max(1, int(H)), cfg) * 86400.0 / float(e["target_seconds"])


def _instant(s: str) -> dt.datetime:
    t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def estimate_height(at: str, anchor: Optional[tuple[int, str]] = None,
                    cfg: Optional[dict] = None) -> int:
    """The height at `at`, stepped from `anchor` (height, instant) at the target
    pace: the ESTIMATED fallback (G-26)."""
    e = (cfg or config())["emission"]
    h0, t0 = anchor or (int(e["anchor"]["height"]), e["anchor"]["at"])
    secs = (_instant(at) - _instant(t0)).total_seconds()
    return max(1, int(h0 + secs // float(e["target_seconds"])))


# ---------------------------------------------------------------------------
# Reading the store, as of
# ---------------------------------------------------------------------------
def _rows(st, key: str, at: str, instrument: Optional[str] = None) -> list[dict]:
    return [r for r in st.as_of(key, at, instrument=instrument)
            if r.get("value_num") is not None]


def _latest(st, key: str, at: str) -> Optional[dict]:
    rs = _rows(st, key, at)
    return max(rs, key=lambda r: (str(r["observed_at"]), str(r["available_at"]))) \
        if rs else None


def _first(st, keys: list[str], at: str) -> tuple[Optional[dict], Optional[str]]:
    for k in keys:
        r = _latest(st, k, at)
        if r:
            return r, k
    return None, None


def _on_or_before(st, key: str, at: str, day: str) -> Optional[dict]:
    rs = [r for r in _rows(st, key, at) if str(r["observed_at"])[:10] <= day]
    return max(rs, key=lambda r: str(r["observed_at"])) if rs else None


def height_at(st, at: str, cfg: Optional[dict] = None) -> dict:
    """{height, estimated, available_at, from}: the observed height if stored,
    else the estimate from the newest observed one (else the config's anchor)."""
    cfg = cfg or config()
    r = _latest(st, HEIGHT_KEY, at)
    day = _instant(at).date().isoformat()
    if r and str(r["observed_at"])[:10] == day:
        return {"height": int(r["value_num"]), "estimated": False,
                "available_at": str(r["available_at"]),
                "from": f"the explorer, {str(r['observed_at'])[:10]}"}
    anchor = ((int(r["value_num"]), str(r["observed_at"])) if r else None)
    h = estimate_height(at, anchor, cfg)
    return {"height": h, "estimated": True, "available_at": at,
            "from": (f"{ESTIMATED}: from the explorer's {anchor[0]:,} on "
                     f"{anchor[1][:10]} at the {cfg['emission']['target_seconds']} s "
                     f"target" if anchor else
                     f"{ESTIMATED}: from Appendix E's block "
                     f"{cfg['emission']['anchor']['height']:,} at the "
                     f"{cfg['emission']['target_seconds']} s target (no height stored)")}


# ---------------------------------------------------------------------------
# D1-D6
# ---------------------------------------------------------------------------
def derive(st, at: str, cfg: Optional[dict] = None) -> dict:
    """Every derived figure at the cutoff, each with its inputs and its reason
    when absent: {name: {value, available_at, trace} | {value: None, reason}}."""
    cfg = cfg or config()
    d = cfg.get("derived") or {}
    out: dict[str, dict] = {}
    H = height_at(st, at, cfg)
    h, mark = H["height"], (f" [{ESTIMATED}]" if H["estimated"] else "")
    base_av = H["available_at"]
    if H["estimated"]:
        out["height_estimated"] = {"value": float(h), "available_at": at,
                                   "trace": H["from"]}
    sc = supply_code(h, cfg)
    rw = reward(h, cfg)
    out["reward"] = {"value": rw, "available_at": base_av,
                     "trace": f"reward({h:,}) = {rw:,.1f} PRL{mark}; height {H['from']}"}
    out["supply_code"] = {"value": sc, "available_at": base_av,
                          "trace": f"2.1e9 x {h:,} / ({h:,} + K) = {sc / 1e6:,.2f}M{mark}"}
    w1 = float(cfg["emission"]["week_one_minted"])
    out["overhang"] = {"value": 100.0 * w1 / sc, "available_at": base_av,
                       "trace": f"{w1 / 1e6:.2f}M / {sc / 1e6:,.2f}M{mark}"}
    # D3 (ruling 1 of 18 Oct 2026): the formula against the explorer's supply,
    # read on the explorer's own day; ESTIMATED until the explorer reads.
    es = _latest(st, SUPPLY_KEY, at)
    if es and not H["estimated"] and str(es["observed_at"])[:10] == \
            _instant(at).date().isoformat():
        out["supply_gap"] = {"value": sc - float(es["value_num"]),
                             "available_at": max(base_av, str(es["available_at"])),
                             "trace": f"{sc / 1e6:,.2f}M (the formula at {h:,}) - "
                                      f"{float(es['value_num']) / 1e6:,.2f}M (the "
                                      f"explorer's supply, {str(es['observed_at'])[:10]})"}
    else:
        out["supply_gap"] = {"value": None, "estimated": True,
                             "reason": f"{ESTIMATED}: the gap is the formula against "
                                       f"the explorer's supply, and the explorer has "
                                       f"not read ({SUPPLY_KEY})"}
    circ, ck = _first(st, d.get("circulating") or [], at)
    if circ:
        out["circulating"] = {"value": float(circ["value_num"]), "key": ck,
                              "available_at": str(circ["available_at"])}
    px, pk = _first(st, d.get("price") or [], at)
    vol, vk = _first(st, d.get("volume") or [], at)
    if px and vol and float(vol["value_num"]) > 0:
        em = daily_emission(h, cfg) * float(px["value_num"])
        out["emission_to_volume"] = {
            "value": em / float(vol["value_num"]),
            "available_at": max(base_av, str(px["available_at"]), str(vol["available_at"])),
            "trace": f"{daily_emission(h, cfg):,.0f} PRL a day x ${float(px['value_num']):.4f} "
                     f"({pk}) / ${float(vol['value_num']):,.0f} ({vk}){mark}"}
    else:
        out["emission_to_volume"] = {"value": None, "reason": (
            "no price stored" if not px else "no 24h volume stored "
            f"({', '.join(d.get('volume') or [])})")}
    out["venue_conc"] = {"value": None, "not_tracked": True,
                         "reason": ((d.get("not_tracked") or {}).get("venue_conc")
                                    or "not tracked (source retired): calc.prl_venue_conc")}
    out["idle_gpu_flag"] = idle_gpu(st, at, cfg)
    return out


def _change_pct(st, key: str, at: str, days: int) -> Optional[tuple[float, str, str]]:
    now = _latest(st, key, at)
    if not now:
        return None
    then_day = (_instant(str(now["observed_at"])[:10] + "T00:00:00+00:00")
                - dt.timedelta(days=days)).date().isoformat()
    then = _on_or_before(st, key, at, then_day)
    if not then or not float(then["value_num"]):
        return None
    return (100.0 * (float(now["value_num"]) / float(then["value_num"]) - 1.0),
            str(then["observed_at"])[:10], str(now["observed_at"])[:10])


def idle_gpu(st, at: str, cfg: Optional[dict] = None) -> dict:
    """D6: ON when difficulty is up more than the threshold over the window while
    price is down more than its threshold over the same window."""
    cfg = cfg or config()
    g = (cfg.get("derived") or {}).get("idle_gpu") or {}
    n = int(g.get("window_days") or 30)
    dif = _change_pct(st, DIFFICULTY_KEY, at, n)
    pk = next((k for k in (cfg.get("derived") or {}).get("price") or []
               if _latest(st, k, at)), None)
    px = _change_pct(st, pk, at, n) if pk else None
    if not dif or not px:
        return {"value": None, "reason": (f"difficulty over {n} days not stored" if not dif
                                          else f"price over {n} days not stored")}
    on = dif[0] > float(g.get("difficulty_up_pct") or 25) and \
        px[0] < -float(g.get("price_down_pct") or 20)
    av = max(str(_latest(st, DIFFICULTY_KEY, at)["available_at"]),
             str(_latest(st, pk, at)["available_at"]))
    return {"value": 1.0 if on else 0.0, "available_at": av,
            "trace": f"difficulty {dif[0]:+.1f}% ({dif[1]} to {dif[2]}), price "
                     f"{px[0]:+.1f}% ({pk}, {px[1]} to {px[2]}); ON above "
                     f"+{g.get('difficulty_up_pct')}% with price below "
                     f"-{g.get('price_down_pct')}%"}


# ---------------------------------------------------------------------------
# The thesis status (2.7.5), with its trace
# ---------------------------------------------------------------------------
def thesis_status(st, at: str, signposts: Optional[dict] = None,
                  cfg: Optional[dict] = None) -> dict:
    """UNCHANGED / IMPROVED / DETERIORATED by the rule of 2.7.5, with each input
    printed beside the word. `signposts` carries the narrative signposts the scan
    feeds (S1 partner added, S2 PRL path shipped, S3 tier-1 listing, S7 incident,
    Together endpoint withdrawn, a top venue delisted) -- `manual_input` until
    ST-15; absent here means not read, and the trace says which were not read."""
    cfg = cfg or config()
    d = cfg.get("derived") or {}
    sp = signposts or {}
    days = int(d.get("review_days") or 7)
    now = derive(st, at, cfg)
    prior_at = (_instant(at) - dt.timedelta(days=days)).isoformat()
    prior = derive(st, prior_at, cfg)
    improved, deteriorated, read, unread = [], [], [], []

    def sig(name: str, label: str, bucket: list) -> None:
        v = sp.get(name)
        if v is None:
            unread.append(label)
        else:
            read.append(f"{label} {'yes' if v else 'no'}")
            if v:
                bucket.append(label)
    sig("s1_partner_added", "S1 a named paid-compute partner added", improved)
    sig("s2_prl_path_shipped", "S2 a PRL-denominated path shipped", improved)
    sig("s3_tier1_listing", "S3 a tier-1 listing", improved)
    sig("s7_incident", "S7 an exploit, chain halt or reorg", deteriorated)
    sig("together_withdrawn", "the Together endpoint withdrawn", deteriorated)
    sig("top_venue_delisted", "a top venue delisted", deteriorated)
    # D5 is not tracked (source retired), so its leg of the rule is never read.
    unread.append("D5 below 60% with volume up (D5 not tracked: source retired)")
    e2v = d.get("emission_to_volume") or {}
    weeks = int(e2v.get("weeks_above") or 4)
    reads = []
    for w in range(weeks):
        x = derive(st, (_instant(at) - dt.timedelta(days=7 * w)).isoformat(), cfg)
        reads.append(x["emission_to_volume"].get("value"))
    if all(v is not None for v in reads):
        above = all(v > float(e2v.get("not_absorbed") or 1.0) for v in reads)
        read.append("D4 the last {} weekly reads {}".format(
            weeks, ", ".join(f"{v:.2f}" for v in reads)))
        if above:
            deteriorated.append(f"D4 above {e2v.get('not_absorbed')} for {weeks} weekly reads")
    else:
        unread.append(f"D4 over {weeks} weekly reads")
    word = ("DETERIORATED" if deteriorated else "IMPROVED" if improved else "UNCHANGED")
    why = deteriorated or improved
    trace = (f"{word}: " + ("; ".join(why) if why else "no rule fired")
             + (f". Read: {'; '.join(read)}" if read else "")
             + (f". Not read: {'; '.join(unread)}" if unread else "") + ".")
    av = max([at] + [str(v.get("available_at")) for v in now.values()
                     if v.get("available_at")])
    return {"value": word, "trace": trace, "available_at": av,
            "improved": improved, "deteriorated": deteriorated, "not_read": unread}


# ---------------------------------------------------------------------------
# The rows, for the store
# ---------------------------------------------------------------------------
def rows(st, at: str, cfg: Optional[dict] = None,
         signposts: Optional[dict] = None) -> list[dict]:
    """The calc.prl_* rows at the cutoff: one per figure that is not absent,
    observed on the cutoff's UTC day, available at the latest of its inputs."""
    cfg = cfg or config()
    day = _instant(at).date().isoformat()
    out = []
    for name, x in derive(st, at, cfg).items():
        if x.get("value") is None or name not in KEYS:
            continue
        out.append({"registry_key": KEYS[name], "instrument": None, "observed_at": day,
                    "available_at": x["available_at"], "value": x["value"],
                    "source": SOURCE, "availability_kind": "ingest_instant"})
    ts = thesis_status(st, at, signposts, cfg)
    out.append({"registry_key": KEYS["thesis_status"], "instrument": None,
                "observed_at": day, "available_at": ts["available_at"],
                "value": json.dumps({"status": ts["value"], "trace": ts["trace"]}),
                "source": SOURCE, "availability_kind": "ingest_instant"})
    return out


# ---------------------------------------------------------------------------
# The two scheduled steps (ruling 3 of 18 Oct 2026): no new timer
# ---------------------------------------------------------------------------
def daily(dry_run: bool = False, at: Optional[str] = None, db=None,
          record: bool = True) -> dict:
    """The D-series compute: one line of the crypto basket's daily 17:25 run,
    after the basket's own writes. Dry run: the rows, nothing written."""
    from . import observations, session                         # noqa: PLC0415
    at = at or session.utc_iso(timespec="microseconds")
    own = db is None
    st = db or (observations.ObservationStore() if dry_run
                else observations.open_writer(__name__))
    try:
        r = rows(st, at)
        n = 0 if dry_run else st.write_many(r)
    finally:
        if own:
            st.close()
    if record and not dry_run:
        from . import feeds                                     # noqa: PLC0415
        feeds.record_attempted(ROSTER, DAILY_KEYS, merge=True)
    return {"step": "daily", "dry_run": dry_run, "written": n,
            "keys": sorted({x["registry_key"] for x in r}), "rows": r if dry_run else None}


def weekly(dry_run: bool = False, today: Optional[str] = None, force: bool = False,
           record: bool = True, **kw) -> dict:
    """The explorer read: a weekly step (Saturdays, ET) of the crypto basket's
    run. With no endpoint declared it is PENDING -- the heartbeat lists its keys
    pending, with no allowance running -- and the derived layer prints ESTIMATED."""
    from . import session                                       # noqa: PLC0415
    from .sources import pearl_explorer                         # noqa: PLC0415
    day = dt.date.fromisoformat((today or session.session_date())[:10])
    if day.weekday() != 5 and not force:
        return {"step": "weekly", "skipped": f"{day:%a} {day}: the explorer reads on "
                                            f"Saturdays"}
    res = pearl_explorer.pull(dry_run=dry_run, **kw)
    status = ("PENDING" if res.get("state") == "estimated" else
              res.get("status") or ("OK" if res.get("written") else res.get("state")))
    out = {"step": "weekly", "dry_run": dry_run, "status": status, **res}
    if record and not dry_run:
        from . import feeds                                     # noqa: PLC0415
        feeds.record_attempted(
            ROSTER, EXPLORER_KEYS, merge=True,
            awaiting=({k: f"pearl_explorer: {res.get('reason')}" for k in EXPLORER_KEYS}
                      if status == "PENDING" else None),
            failed=({k: f"pearl_explorer: {res.get('reason')}" for k in EXPLORER_KEYS}
                    if status not in ("OK", "PENDING") else None))
    return out


def _main(argv: list[str]) -> int:
    import argparse
    from . import observations, session
    ap = argparse.ArgumentParser(prog="python -m altdata.prl")
    ap.add_argument("cmd", choices=["daily", "weekly", "compute", "show"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="weekly: read on any day")
    a = ap.parse_args(argv)
    at = a.as_of or session.utc_iso(timespec="microseconds")
    if a.cmd == "daily":
        print(json.dumps(daily(a.dry_run, at), indent=2, default=str))
        return 0
    if a.cmd == "weekly":
        print(json.dumps(weekly(a.dry_run, force=a.force), indent=2, default=str))
        return 0
    if a.cmd == "show" or a.dry_run:
        with observations.ObservationStore(a.db) as st:
            print(json.dumps({"derived": derive(st, at), "thesis": thesis_status(st, at),
                              "rows": rows(st, at) if a.dry_run else None},
                             indent=2, default=str))
        return 0
    st = observations.open_writer(__name__) if a.db is None else \
        observations.ObservationStore(a.db)
    try:
        r = rows(st, at)
        n = st.write_many(r)
    finally:
        st.close()
    print(json.dumps({"written": n, "keys": sorted({x["registry_key"] for x in r})},
                     indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))

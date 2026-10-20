"""
Signal-triage Batch 12, item 59 (ST-R6.59a/b; ruled 20 Oct 2026 with filing
amendments F1-F6): the bank-stress panel, the funding-stress and deposit-flight
flags, and the correction-vs-crisis classifier.

    from altdata import bank_stress as bs
    b = bs.build(st, cutoff)           # the panel, both flags, the classifier
    bs.status_line(b)                  # the Weekly's one line
    python -m altdata.bank_stress show [--as-of ISO]

THE PANEL (config/bank_stress.yaml): SOFR less IORB and SOFR's 99th percentile
less IORB (IOER before 29 Jul 2021), financial CP less the 3-month bill, the
discount window's primary credit and any other credit extension (H.4.1), FHLB
advances (Z.1, quarterly; F2), H.8 deposits at small and large domestic banks, retail money-market
fund assets (FRED; ICI is a listed gap), KRE against XLF over 20 sessions, SLOOS, the FDIC's
unrealised securities losses, STLFSI and the OFR FSI. Each prints with dual
percentiles: the five-year window and its family's stated long window, each with
its real window and n. Bank CDS, AT1 spreads and CMBS office delinquency are listed
gaps (F2), and so is KRE's implied vol (not in the capture universe).

THE FLAGS (RULED, item 59):
  funding stress   any two of SOFR-IORB, the financial CP spread, discount-window
                   primary credit and FHLB advances above their 95th percentile
                   (the five-year window's figure, session-set)
  deposit flight   small-bank H.8 deposits falling while money-fund assets rise,
                   both over 4 weeks

THE CLASSIFIER, printed whenever KRE is down more than 10% over 20 sessions:
correction (neither flag on), funding watch (one), banking stress (both). Its third
arm, "either flag plus a CDS/AT1 move", prints "not tracked" (F2).

THE 12:30 GATE (F5, `gate`): opens only on the session a flag turns on -- on at
12:30, off as of the prior session's close -- with one code-written line.

READS THE STORE ONLY, AS OF. Flags and the classifier only: nothing here enters a
composite, a trigger, a dial or the market-state object, and no regime is computed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Optional

from . import st_r5_rates as rt

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "bank_stress.yaml"
UNITS = {"bp": "bp", "pct": "%", "usd_m": "$m", "usd_b": "$bn", "usd": "$",
         "index": "", }


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# The series, as of
# ---------------------------------------------------------------------------
def policy_rate(iorb: list, ioer: list, iorb_from: str) -> dict:
    """{day: rate}: IOER before IORB's first day, IORB from it."""
    out = {d: v for d, v in ioer if d < iorb_from}
    out.update({d: v for d, v in iorb if d >= iorb_from})
    return out


def spread_bp(a: list, b: dict) -> list[tuple[str, float]]:
    """a less b in basis points, on a's days where b has a value on or before
    the day (a rate is carried forward over a holiday)."""
    out, days = [], sorted(b)
    j, last = 0, None
    for d, v in a:
        while j < len(days) and days[j] <= d:
            last = b[days[j]]
            j += 1
        if last is not None:
            out.append((d, round((v - last) * 100.0, 2)))
    return out


def ratio_change(a: list, b: list, n: int) -> list[tuple[str, float]]:
    """The a/b ratio's change over n sessions, percent, on days both hold."""
    bb = dict(b)
    r = [(d, v / bb[d]) for d, v in a if bb.get(d)]
    return [(r[i][0], round((r[i][1] / r[i - n][1] - 1) * 100.0, 3))
            for i in range(n, len(r))]


def series(st, cutoff: str, sid: str, cfg: dict) -> list[tuple[str, float]]:
    """One panel series' points, as of the cutoff."""
    k = cfg["keys"]
    pts = lambda key: rt._pts(st, key, cutoff)                 # noqa: E731,SLF001
    if sid in ("sofr_iorb", "sofr99_iorb"):
        pol = policy_rate(pts(k["iorb"]), pts(k["ioer"]), str(k["iorb_from"]))
        return spread_bp(pts(k["sofr"] if sid == "sofr_iorb" else k["sofr_p99"]), pol)
    if sid == "fin_cp_spread":
        return spread_bp(pts(k["fin_cp"]), dict(pts(k["tbill"])))
    if sid == "kre_xlf":
        return ratio_change(pts(k["kre"]), pts(k["xlf"]),
                            int((cfg.get("classifier") or {}).get("sessions", 20)))
    return pts(cfg["series"][sid]["key"])


def panel(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    cfg = cfg or config()
    years = int(cfg.get("lens_years", 5))
    out = []
    for sid, spec in (cfg.get("series") or {}).items():
        pts = series(st, cutoff, sid, cfg)
        row = {"id": sid, "label": spec["label"], "family": spec["family"],
               "unit": spec["unit"], "source": spec["source"]}
        if not pts:
            row.update(state="absent", reason="not yet stored")
        else:
            lz = rt.lens(pts, years)
            row.update(state="ok", value=pts[-1][1], as_of=pts[-1][0], lens=lz,
                       pct_5y=lz["percentile_window"], pct_long=lz["percentile_full"])
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# The flags and the classifier (pure)
# ---------------------------------------------------------------------------
def funding_flag(rows: list[dict], cfg: dict) -> dict:
    f = cfg["funding_flag"]
    by = {r["id"]: r for r in rows}
    th = float(f.get("percentile", 95))
    read, above = [], []
    for m in f["members"]:
        r = by.get(m) or {}
        if r.get("state") != "ok" or r.get("pct_5y") is None:
            continue
        read.append(m)
        if r["pct_5y"] > th:
            above.append(m)
    need = int(f.get("min_on", 2))
    on = len(above) >= need
    return {"on": on, "above": above, "read": read, "members": list(f["members"]),
            "need": need, "percentile": th,
            "state": "on" if on else ("off" if len(read) >= need else "not read")}


def four_week_change(pts: list[tuple[str, float]], weeks: int) -> Optional[dict]:
    return rt.change(pts, 7 * weeks)


def deposit_flag(small: Optional[dict], funds: Optional[dict]) -> dict:
    if small is None or funds is None:
        return {"on": False, "state": "not read", "small": small, "funds": funds,
                "why": ("small-bank deposits not stored over 4 weeks" if small is None
                        else "money-fund assets not stored over 4 weeks")}
    on = small["change"] < 0 and funds["change"] > 0
    return {"on": on, "state": "on" if on else "off", "small": small, "funds": funds}


def drawdown(pts: list[tuple[str, float]], n: int) -> Optional[dict]:
    """The equity leg's change over the last n sessions, percent."""
    if len(pts) <= n:
        return None
    (d0, v0), (d1, v1) = pts[-1 - n], pts[-1]
    return {"from_day": d0, "to_day": d1, "change_pct": round((v1 / v0 - 1) * 100.0, 2)}


def classify(funding: dict, deposit: dict, dd: Optional[dict], cfg: dict) -> dict:
    c = cfg["classifier"]
    if dd is None:
        return {"state": "not read", "prints": False,
                "why": f"KRE not stored over {c['sessions']} sessions"}
    if dd["change_pct"] >= -float(c["drawdown_pct"]):        # "more than 10%"
        return {"state": "dormant", "prints": False, "drawdown": dd}
    n_on = int(bool(funding.get("on"))) + int(bool(deposit.get("on")))
    return {"state": c["states"][n_on], "prints": True, "drawdown": dd, "flags_on": n_on,
            "cds_at1": c["cds_at1"]}


def build(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    rows = panel(st, cutoff, cfg)
    df = cfg["deposit_flag"]
    weeks = int(df.get("weeks", 4))
    small = four_week_change(rt._pts(st, df["small_deposits"], cutoff), weeks)  # noqa: SLF001
    funds = four_week_change(rt._pts(st, df["money_funds"], cutoff), weeks)     # noqa: SLF001
    fund = funding_flag(rows, cfg)
    dep = deposit_flag(small, funds)
    c = cfg["classifier"]
    dd = drawdown(rt._pts(st, c["equity"], cutoff), int(c["sessions"]))         # noqa: SLF001
    ten = rt._pts(st, cfg["keys"]["ten_year"], cutoff)                          # noqa: SLF001
    return {"block": "bank_stress", "as_of": cutoff, "panel": rows, "funding": fund,
            "deposit": dep, "classifier": classify(fund, dep, dd, cfg),
            "ten_year": ten[-1] if ten else None, "gaps": list((cfg.get("gaps") or {}).values())}


# ---------------------------------------------------------------------------
# The printed lines (code-written)
# ---------------------------------------------------------------------------
def fmt(v: Optional[float], unit: str) -> str:
    if v is None:
        return "—"
    if unit == "bp":
        return f"{v:+.0f} bp"
    if unit == "pct":
        return f"{v:+.1f}%"
    if unit == "usd_m":
        return f"${v / 1000:,.1f}bn"
    if unit == "usd_b":
        return f"${v:,.0f}bn"
    if unit == "usd":
        return f"${v / 1e9:,.1f}bn"
    return f"{v:,.2f}"


def funding_line(f: dict) -> str:
    names = ", ".join(f["above"]) or "none"
    if f["state"] == "not read":
        return (f"Funding-stress flag: not read ({len(f['read'])} of {len(f['members'])} "
                f"members stored; it needs {f['need']}).")
    return (f"Funding-stress flag {f['state'].upper()}: {len(f['above'])} of "
            f"{len(f['read'])} read above their {f['percentile']:.0f}th five-year "
            f"percentile ({names}); it needs {f['need']}.")


def deposit_line(d: dict) -> str:
    if d["state"] == "not read":
        return f"Deposit-flight flag: not read ({d['why']})."
    s, m = d["small"], d["funds"]
    return (f"Deposit-flight flag {d['state'].upper()}: small-bank deposits "
            f"{s['change']:+,.1f}bn over 4 weeks (to {s['now_day']}), retail money-fund "
            f"assets {m['change']:+,.1f}bn (to {m['now_day']}).")


def classifier_line(c: dict) -> Optional[str]:
    """The read's line, or None when the classifier does not print."""
    if not c.get("prints"):
        return None
    dd = c["drawdown"]
    return (f"Bank equity: KRE {dd['change_pct']:+.1f}% over 20 sessions (to "
            f"{dd['to_day']}) -- the classifier reads {c['state'].upper()} "
            f"({c['flags_on']} of 2 flags on). Either flag plus a CDS/AT1 move: "
            f"{c['cds_at1']}.")


def classifier_status(c: dict) -> str:
    if c["state"] == "not read":
        return f"Correction-vs-crisis classifier: not read ({c['why']})."
    if c["state"] == "dormant":
        return (f"Correction-vs-crisis classifier: dormant (KRE "
                f"{c['drawdown']['change_pct']:+.1f}% over 20 sessions; it prints past "
                f"-10%).")
    return classifier_line(c)


def status_line(b: dict) -> str:
    """The Weekly's one line."""
    f, d, c = b["funding"], b["deposit"], b["classifier"]
    cs = (c["state"] if c["state"] not in ("dormant", "not read")
          else f"classifier {c['state']}")
    dd = c.get("drawdown")
    kre = f"KRE {dd['change_pct']:+.1f}% over 20 sessions" if dd else "KRE not stored"
    return (f"Bank stress: funding flag {f['state']} ({len(f['above'])} of "
            f"{len(f['read'])} above the 95th), deposit flag {d['state']}, {kre} "
            f"({cs}).")


def losses_line(b: dict) -> Optional[str]:
    r = next((x for x in b["panel"] if x["id"] == "unrealised_losses"), None)
    if not r or r["state"] != "ok":
        return "Unrealised securities losses (FDIC): not yet stored."
    ten = b.get("ten_year")
    tail = (f", beside the 10-year at {ten[1]:.2f}% ({ten[0]}): the higher the long "
            f"end, the larger the losses" if ten else "")
    return (f"Unrealised securities gains (losses), AFS and HTM: {fmt(r['value'], 'usd')} "
            f"at {r['as_of']} (FDIC){tail}.")


def lines(b: dict) -> list[str]:
    out = [funding_line(b["funding"]), deposit_line(b["deposit"]),
           classifier_status(b["classifier"]), losses_line(b)]
    return [x for x in out if x]


# ---------------------------------------------------------------------------
# The 12:30 gate (F5)
# ---------------------------------------------------------------------------
def turned_on(now: dict, prior: dict) -> list[str]:
    """The flags on now that were off as of the prior session's close."""
    return [k for k in ("funding", "deposit")
            if now[k].get("on") and not prior[k].get("on")]


def gate(ctx: dict) -> dict:
    """Opens only on the session a flag turns on (F5). `ctx` may carry `store`
    (an open store), `now` and `prior_cutoff`; otherwise the store is opened and
    the prior cutoff is the prior session's 17:00 ET."""
    from . import observations, session                        # noqa: PLC0415
    cfg = ctx.get("bank_stress_cfg") or config()
    day = str(ctx.get("day"))
    now = ctx.get("now") or session.utc_iso()
    prior = ctx.get("prior_cutoff")
    if not prior:
        pd = session.previous_trading_session(dt.date.fromisoformat(day)).isoformat()
        h, m = (int(x) for x in str((cfg.get("midday") or {}).get("prior_cutoff_et",
                                                               "17:00")).split(":"))
        prior = dt.datetime.combine(dt.date.fromisoformat(pd), dt.time(h, m),
                                    tzinfo=session._eastern_tz()).astimezone(  # noqa: SLF001
            dt.timezone.utc).isoformat()
    st = ctx.get("store")
    own = st is None
    if own:
        path = Path(ctx.get("db_path") or observations.DEFAULT_DB)
        if not path.is_file():
            # Never create a store to read one (A48's local-run note).
            return {"id": "bank_stress", "open": False, "line": None,
                    "why": f"no store at {path.name}"}
        st = observations.ObservationStore(str(path))
    try:
        b_now, b_prior = build(st, now, cfg), build(st, prior, cfg)
    finally:
        if own:
            st.close()
    on = turned_on(b_now, b_prior)
    if not on:
        return {"id": "bank_stress", "open": False, "line": None,
                "why": "no bank-stress flag turned on this session"}
    words = {"funding": funding_line(b_now["funding"]),
             "deposit": deposit_line(b_now["deposit"])}
    return {"id": "bank_stress", "open": True,
            "line": "Bank stress, turned on today: " + " ".join(words[k] for k in on),
            "why": f"turned on: {', '.join(on)}", "values": {"turned_on": on}}


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.bank_stress")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of")
    ap.add_argument("--db")
    a = ap.parse_args(argv)
    from . import observations, session                        # noqa: PLC0415
    with observations.ObservationStore(a.db) as st:
        b = build(st, a.as_of or session.utc_iso())
    print("\n".join(lines(b)))
    print(json.dumps({r["id"]: (r.get("value"), r.get("as_of"), r.get("pct_5y"))
                      for r in b["panel"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))

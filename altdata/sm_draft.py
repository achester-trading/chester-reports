"""
The box draft of the Security Master's store-only schemes (ruled 15 Oct 2026,
answer 6): prediction-market contracts (pm_id) and IBKR contract ids
(ibkr_conid) live only in the box's observation store, so a read-only command
prints them as master YAML to the screen, as the contract-map draft does:

    python -m altdata.security_master draft-box [--store PATH]

It opens the store `mode=ro` with query_only on and writes NOTHING -- not the
master, not the store, not a file. The operator pastes its output into chat, and
a later paste commits it. Until then both schemes stay empty in the master.

WHAT IT PRINTS:
  - each stored prediction-market contract (a pm.market row, instrument
    `<venue>:<market id>`): asset_class prediction_contract, pm_id, the
    question and outcome as the name, active_to from its close_at;
  - each stored IBKR position key (portfolio.position_con_id: instrument
    `<localSymbol>@<exchange>.<CCY>`, value the conId): ibkr_conid, the key as
    an alias, currency from the key's suffix. No position size, price or value
    is read or printed -- the con_id key carries the identifier only.

Ids are proposed from the master's next_id; every unstated fact is null and
listed as unverified, and `restricted` is never printed (computed at load).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional


def _ro(path: Optional[str]):
    from . import observations  # noqa: PLC0415
    p = Path(path or observations.DEFAULT_DB)
    if not p.is_file():
        raise FileNotFoundError(f"no observation store at {p}")
    st = observations.ObservationStore.__new__(observations.ObservationStore)
    st.path = p
    st.conn = sqlite3.connect(f"file:{p.resolve().as_posix()}?mode=ro", uri=True)
    st.conn.row_factory = sqlite3.Row
    st.conn.execute("PRAGMA query_only = ON")
    return st


def draft(store, next_id: int) -> list[dict]:
    out = []
    for inst in sorted(store.instruments("pm.market")):
        r = store.latest_as_of("pm.market", None, inst)
        try:
            meta = json.loads((r or {}).get("value_text") or "{}")
        except ValueError:
            meta = {}
        name = " -- ".join(x for x in (meta.get("question"), meta.get("outcome")) if x)
        close = str(meta.get("close_at") or "")[:10] or None
        e = {"name": name or None, "asset_class": "prediction_contract", "currency": None,
             "multiplier": None, "exchange": None,
             "identifiers": {"pm_id": inst}, "aliases": [],
             "active_from": None, "active_to": close,
             "sources": {"identifiers": "pm.market (the box's store)",
                         "rule": meta.get("rules_url")}}
        out.append(e)
    for inst in sorted(store.instruments("portfolio.position_con_id")):
        r = store.latest_as_of("portfolio.position_con_id", None, inst)
        con = (r or {}).get("value_num")
        if con is None:
            continue
        ccy = inst.rsplit(".", 1)[-1] if "@" in inst and "." in inst else None
        out.append({"name": None, "asset_class": None, "currency": ccy, "multiplier": None,
                    "exchange": None,
                    "identifiers": {"ibkr_conid": str(int(con))}, "aliases": [inst],
                    "active_from": None, "active_to": None,
                    "sources": {"identifiers": "portfolio.position_con_id (the box's store)",
                                "currency": "the instrument key's suffix" if ccy else None}})
    for i, e in enumerate(out):
        e["id"] = f"SM{next_id + i:05d}"
        e["unverified"] = sorted(f for f in ("name", "currency", "multiplier", "exchange",
                                             "asset_class") if e.get(f) is None)
    return [{"id": e.pop("id"), **e} for e in out]


def render(entries: list[dict], next_id: int) -> str:
    import yaml  # noqa: PLC0415
    head = ["# DRAFT -- python -m altdata.security_master draft-box (read-only).",
            "# Paste into chat; a later paste commits the lines Ari confirms.",
            f"# {len(entries)} entries from SM{next_id:05d}; next_id after them: "
            f"{next_id + len(entries)}"]
    body = yaml.safe_dump({"instruments": entries}, sort_keys=False, allow_unicode=True,
                          width=100) if entries else "instruments: []\n"
    return "\n".join(head) + "\n" + body


def _main(store_path: Optional[str] = None) -> int:
    from .security_master import Master  # noqa: PLC0415
    nxt = int(Master().raw.get("next_id") or 1)
    st = _ro(store_path)
    try:
        entries = draft(st, nxt)
    finally:
        st.conn.close()
    sys.stdout.write(render(entries, nxt))
    return 0

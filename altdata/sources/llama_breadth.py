"""
DefiLlama's TVL by category and by chain, daily snapshots, for the Alternative
Assets Quarterly's crypto chapter (the breadth lines beside the active-protocol
count, item 78) (b70-quarterly-readers-2; D34 of 24 Oct 2026; B67 section 16).

    python -m altdata.sources.llama_breadth [--dry-run]

STORED, NEVER REPUBLISHED. The existing source `defillama`'s terms, as the
registry quotes them: "personal, non-commercial use; no republishing of the data
without permission". So these rows are stored for the reports' own reads and
printed as the system's figures with DefiLlama named; no export carries them.
api.llama.fi publishes no robots.txt (404, no rules; re-read 25 Oct 2026).

SOURCE. Two keyless reads a day:
  /protocols      every listed protocol with its `category` and current `tvl`
                  (probed 25 Oct 2026: 8,820 protocols); a category's TVL is the
                  sum over its protocols. CEX balances are excluded -- an
                  exchange's wallets are not DeFi TVL.
  /v2/chains      every chain with its current `tvl`.

  llama.tvl.category.<slug>   USD; slugs below
  llama.tvl.chain.<slug>      USD; the layer-2 chains below

THE AERO CONVENTION (ruling D29 (3), 24 Oct 2026). A protocol DefiLlama merges
into a parent is followed under the parent from the merge onward as a labelled
break, with no restatement of stored history. A category total moves only when a
merge crosses categories; `MERGED` names each known merge, and a merged child
still listed under its old name is not counted twice.

observed_at = the UTC day of the read (a snapshot); available_at = the read
instant (ingest_instant). History before the first read is not reconstructed.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Optional

from .. import session
from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "defillama"
PROTOCOLS_URL = "https://api.llama.fi/protocols"
CHAINS_URL = "https://api.llama.fi/v2/chains"
CATEGORIES = {"rwa": "RWA", "lending": "Lending", "liquid_staking": "Liquid Staking",
              "dexs": "Dexs", "cdp": "CDP", "bridge": "Bridge", "yield": "Yield",
              "derivatives": "Derivatives", "restaking": "Restaking",
              "basis_trading": "Basis Trading"}
CHAINS = {"arbitrum": "Arbitrum", "base": "Base", "optimism": "OP Mainnet",
          "blast": "Blast", "scroll": "Scroll", "linea": "Linea",
          "zksync_era": "zkSync Era", "mantle": "Mantle", "starknet": "Starknet"}
# Known merges, child slug -> (parent, the merge's first day, the child's category
# at the merge). AERO's is D29 (3)'s precedent: on the 25 Oct 2026 listing,
# aerodrome-v1 and aerodrome-slipstream carry parentProtocol
# "parent#aero-protocol", both in Dexs, so the merge moved no category total. A
# child later listed under ANOTHER category is a labelled break in both totals
# from that day (`breaks`); a merge found later is added here by the session that
# finds it, with its date, never retro-applied.
MERGED = {"aerodrome-v1": ("aero-protocol", "2026-10-21", "Dexs"),
          "aerodrome-slipstream": ("aero-protocol", "2026-10-21", "Dexs")}


def breaks(protocols: list) -> list[str]:
    """The merged children now listed under another category than at their merge."""
    now = {str(p.get("slug")): str(p.get("category")) for p in protocols}
    return sorted(f"{c}: {cat} -> {now[c]} (merged into {par} {day})"
                  for c, (par, day, cat) in MERGED.items() if c in now and now[c] != cat)


KEYS = ([f"llama.tvl.category.{s}" for s in CATEGORIES]
        + [f"llama.tvl.chain.{s}" for s in CHAINS])


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def category_rows(protocols: list, day: str, available_at: str) -> list[dict]:
    if not isinstance(protocols, list) or not protocols:
        raise ValueError("the /protocols response is not a non-empty list")
    by_name = {v: k for k, v in CATEGORIES.items()}
    sums: dict[str, float] = {}
    for p in protocols:
        cat = by_name.get(str(p.get("category") or ""))
        tvl = p.get("tvl")
        if cat and isinstance(tvl, (int, float)) and not isinstance(tvl, bool):
            sums[cat] = sums.get(cat, 0.0) + float(tvl)
    return [{"registry_key": f"llama.tvl.category.{c}", "instrument": None,
             "observed_at": day, "available_at": available_at, "value": v,
             "availability_kind": "ingest_instant"} for c, v in sorted(sums.items())]


def chain_rows(chains: list, day: str, available_at: str) -> list[dict]:
    if not isinstance(chains, list) or not chains:
        raise ValueError("the /v2/chains response is not a non-empty list")
    by_name = {v: k for k, v in CHAINS.items()}
    out = []
    for c in chains:
        slug = by_name.get(str(c.get("name") or ""))
        tvl = c.get("tvl")
        if slug and isinstance(tvl, (int, float)) and not isinstance(tvl, bool):
            out.append({"registry_key": f"llama.tvl.chain.{slug}", "instrument": None,
                        "observed_at": day, "available_at": available_at,
                        "value": float(tvl), "availability_kind": "ingest_instant"})
    return out


def _produce() -> list[dict]:
    now = session.utc_iso(timespec="microseconds")
    day = dt.datetime.now(dt.timezone.utc).date().isoformat()
    p, _h = _fetch(PROTOCOLS_URL)
    c, _h = _fetch(CHAINS_URL, robots=False)
    protocols = json.loads(p.decode("utf-8"))
    for b in breaks(protocols):
        log.warning("llama_breadth: a merge crosses categories, a labelled break: %s", b)
    return (category_rows(protocols, day, now)
            + chain_rows(json.loads(c.decode("utf-8")), day, now))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))

"""
Weekly news-scan orchestrator.

This module ties the prompt builder to an LLM client and stores the resulting
weekly update per asset in the store so it can be included in the next
report payload.

Design:
  1. For each asset, build the per-asset prompt via weekly_scan_prompt.build_prompt()
  2. Call the LLM (Claude API or compatible) with that prompt
  3. Store the response as a 'weekly_update' metric in the store
  4. The export layer pulls 'weekly_update' into each asset's deep_dive block
  5. The dashboard renders it at the top of the Outlook section

Cost expectation per weekly run (rough, with Claude Sonnet at recent pricing):
  - ~3,000 input tokens × 18 assets × $3/M input = $0.16
  - ~600 output tokens × 18 assets × $15/M output = $0.16
  Total per run: ~$0.30. Monthly: ~$1.30 (weekly cadence).

The actual LLM call is left as a hook (`call_llm`) so the user wires in
their own client — anthropic SDK, OpenAI SDK, or another provider. A no-op
default is provided that returns a marker string so the orchestration can
be tested end-to-end without API credentials.

Required environment variables (optional, depending on which LLM):
  - ANTHROPIC_API_KEY (if using Claude)
  - OPENAI_API_KEY (if using OpenAI)
"""

from __future__ import annotations

import os
import datetime as dt
from typing import Callable, Optional, List

from ..config import ASSETS_BY_ID
from ..store import Store, Observation
from .weekly_scan_prompt import build_prompt
from .assets import build_all_summaries


# ─── LLM CLIENT HOOKS ────────────────────────────────────────────────────────

def call_claude(prompt: str, model: str = "claude-sonnet-4-5",
                max_tokens: int = 1000) -> str:
    """Call Claude via the anthropic Python SDK.

    Requires: pip install anthropic, ANTHROPIC_API_KEY env var.
    Returns the response text, or a marker string if SDK unavailable.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return "[anthropic SDK not installed; install with: pip install anthropic]"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "[ANTHROPIC_API_KEY not set in environment]"
    client = Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    # extract text from the response
    parts = [b.text for b in msg.content if hasattr(b, "text")]
    return "\n".join(parts).strip()


def call_openai(prompt: str, model: str = "gpt-4o",
                max_tokens: int = 1000) -> str:
    """Call OpenAI via the openai Python SDK.

    Requires: pip install openai, OPENAI_API_KEY env var.
    """
    try:
        from openai import OpenAI
    except ImportError:
        return "[openai SDK not installed; install with: pip install openai]"
    if not os.environ.get("OPENAI_API_KEY"):
        return "[OPENAI_API_KEY not set in environment]"
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def call_stub(prompt: str) -> str:
    """No-op default — returns a marker so orchestration runs without LLM creds.

    The marker is identifiable so the dashboard can render a 'not yet wired'
    state rather than displaying placeholder text as real content.
    """
    return "[WEEKLY_SCAN_STUB] No LLM client configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY and select call_claude or call_openai in run_weekly_scan()."


# ─── POSITIONING DATA GATHERER ───────────────────────────────────────────────

def _gather_positioning(store: Store, asset_id: str) -> dict:
    """Pull the positioning data from the store for one asset.

    Mirrors the structure that _positioning_block() in export.py produces,
    so the prompt builder gets the same data shape.
    """
    out = {}

    # COT
    cot_df = store.read(metric="cot_net_noncomm", asset_id=asset_id)
    if not cot_df.empty:
        cot_df = cot_df.sort_values("date")
        latest = cot_df.iloc[-1]
        all_data = cot_df.tail(260)
        hist_max = float(all_data["value"].max())
        hist_min = float(all_data["value"].min())
        pct_rank = None
        if hist_max != hist_min:
            pct_rank = float((latest["value"] - hist_min) / (hist_max - hist_min))
        cot_4w = None
        if len(cot_df) >= 5:
            cot_4w = float(latest["value"] - cot_df.iloc[-5]["value"])
        out["cot"] = {
            "latest_net": float(latest["value"]),
            "latest_date": str(latest["date"])[:10],
            "change_4w": cot_4w,
            "pct_rank": pct_rank,
        }

    # ETF flows
    etf_df = store.read(metric="etf_net_flow", asset_id=asset_id)
    if not etf_df.empty:
        etf_df = etf_df.sort_values("date")
        recent = etf_df.tail(30)
        latest = recent.iloc[-1]
        out["etf_flows"] = {
            "latest": float(latest["value"]),
            "latest_date": str(latest["date"])[:10],
            "sum_5d": float(recent.tail(5)["value"].sum()),
            "sum_30d": float(recent["value"].sum()),
        }

    # Fear & Greed (crypto only)
    if asset_id in ("btc", "eth", "sol", "zec"):
        fg_df = store.read(metric="fear_greed", asset_id="crypto")
        if not fg_df.empty:
            latest = fg_df.sort_values("date").iloc[-1]
            v = float(latest["value"])
            regime = "fear" if v < 25 else "greed" if v > 75 else "neutral"
            out["sentiment"] = {
                "name": "Fear & Greed Index",
                "latest": v,
                "regime": regime,
                "latest_date": str(latest["date"])[:10],
            }

    # Lens (from cases_and_positioning)
    from .cases_and_positioning import CASES_AND_POSITIONING
    out["lens"] = CASES_AND_POSITIONING.get(asset_id, {}).get("positioning_lens", [])

    return out


def _gather_price_summary(store: Store, asset_id: str) -> dict:
    """Latest price + momentum summary for the prompt context."""
    summaries = build_all_summaries(store)
    for s in summaries:
        if s.asset_id == asset_id:
            return {
                "last_price": s.last_price,
                "last_date": str(s.last_date) if s.last_date else None,
                "momentum": s.momentum or {},
                "rsi": s.rsi,
                "trend": s.trend,
            }
    return {}


# ─── MAIN ORCHESTRATION ──────────────────────────────────────────────────────

def run_weekly_scan(store: Store,
                    call_llm: Callable[[str], str] = call_stub,
                    run_id: str = "",
                    asset_ids: Optional[List[str]] = None) -> List[Observation]:
    """Run the weekly scan: build prompt + call LLM + store result per asset.

    Args:
        store: the altdata Store instance to read positioning from and write
               results back to.
        call_llm: which LLM client function to use. Default is call_stub
                  (no-op marker). Pass call_claude or call_openai to actually
                  call an LLM.
        run_id: optional run identifier for provenance tagging.
        asset_ids: optional subset of assets to scan. Defaults to all.

    Returns:
        List of Observations (one per asset, metric='weekly_update') that
        the caller should persist via store.write().
    """
    asof = dt.datetime.now(tz=dt.timezone.utc)
    today = asof.date()
    target_assets = asset_ids if asset_ids else list(ASSETS_BY_ID.keys())
    out: List[Observation] = []

    for aid in target_assets:
        try:
            positioning = _gather_positioning(store, aid)
            price_sum = _gather_price_summary(store, aid)
            prompt = build_prompt(
                asset_id=aid,
                latest_positioning=positioning,
                recent_price_action=price_sum,
            )
            response = call_llm(prompt)
        except Exception as exc:
            response = f"[weekly scan failed for {aid}: {exc}]"

        # Store the response. We use a non-numeric metric so it's stored as
        # text/json. The schema accepts arbitrary string in value via the
        # 'note' column, with 'value' set to 1.0 to satisfy the float schema.
        out.append(Observation(
            asset_id=aid,
            metric="weekly_update",
            date=today,
            value=1.0,                  # presence indicator
            source="llm_weekly_scan",
            asof=asof,
            run_id=run_id,
            note=response,              # the actual text lives here
        ))
    return out


# ─── CLI ENTRY POINT ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Run a one-shot weekly scan from the command line.

    Usage:
        python -m altdata.report.weekly_scan
        python -m altdata.report.weekly_scan --llm claude --assets btc,eth,gold
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run weekly LLM news scan per asset")
    parser.add_argument("--llm", choices=("claude", "openai", "stub"),
                        default="stub",
                        help="Which LLM client to use (default: stub for testing)")
    parser.add_argument("--assets", default=None,
                        help="Comma-separated asset IDs (default: all)")
    parser.add_argument("--store-path", default="./altdata_store",
                        help="Path to the altdata store")
    parser.add_argument("--run-id", default="",
                        help="Optional run identifier for provenance")
    args = parser.parse_args()

    store = Store(root=args.store_path)
    llm_fn = {"claude": call_claude, "openai": call_openai, "stub": call_stub}[args.llm]
    asset_ids = args.assets.split(",") if args.assets else None

    print(f"Running weekly scan with llm={args.llm}, assets={asset_ids or 'all'}")
    obs = run_weekly_scan(store, call_llm=llm_fn, run_id=args.run_id,
                          asset_ids=asset_ids)
    print(f"Generated {len(obs)} weekly updates")
    store.write(obs)
    print(f"Wrote to store at {args.store_path}")

"""
Per-asset weekly news-scan prompt builder.

This module composes an LLM prompt for each asset by interpolating asset-
specific context (sources, peers, cases, positioning, narrative) into a single
shared template. The output of running this against an LLM is a 2-3 paragraph
weekly update that prepends to (does NOT replace) the structural narrative.

Architectural design:
  1. ONE base prompt template, not 18 separate prompts. Per-asset behavior
     comes from per-asset *inputs*, not per-asset prompt logic.
  2. Inputs come from existing modules — no new data structures.
  3. The LLM gets specific sources to consult and specific cases to evaluate.
     This anchors the response and reduces hallucination.
  4. Output schema is fixed — the LLM is instructed to produce specific
     sections so the dashboard can render them reliably.

Usage:
    from altdata.report.weekly_scan_prompt import build_prompt

    prompt = build_prompt(
        asset_id="btc",
        latest_positioning=positioning_block,   # from _positioning_block()
        recent_price_action=price_summary,      # from _asset_blocks() summary
    )
    # → call your LLM of choice with this prompt
    # → store the LLM response as 'weekly_update' field in the asset's deep_dive

The orchestrator (weekly_scan.py) handles the actual LLM call and storage.
"""

from __future__ import annotations
from typing import Optional

from ..config import ASSETS_BY_ID
from .narratives import NARRATIVES
from .narratives_extended import NARRATIVES_EXTENDED
from .sources import SOURCES
from .peers import PEERS
from .cases_and_positioning import CASES_AND_POSITIONING


# ─── BASE TEMPLATE ────────────────────────────────────────────────────────────

BASE_PROMPT = """\
You are an institutional research analyst writing a weekly update on {asset_name} ({asset_category}).

# Your task

Write a concise weekly update of 2-3 paragraphs covering:

  (a) WHAT MATERIALLY CHANGED THIS WEEK in the price, positioning, fundamental
      drivers, or news flow for this asset. Focus on changes — repeating the
      durable structural picture is not useful.

  (b) WHETHER ANY OF THE BULL / BEAR / FLAT CASES has been STRENGTHENED OR
      WEAKENED by new information this week. Reference specific cases by their
      text.

  (c) SPECIFIC CATALYSTS in the next 5-7 trading days that could move the
      asset — data releases (with date and time if relevant), policy
      meetings, earnings, scheduled events.

# Style and constraints

  - 200-400 words total. Concise institutional research register.
  - No marketing voice. No hype. Use specific numbers when you have them.
  - If you don't have current data for something, say so explicitly. NEVER
    invent data, prices, or events.
  - Cite which canonical source the information would have come from when
    you make a specific claim (e.g., "per the EIA weekly status report" or
    "per CoinGlass ETF flow data").
  - If nothing material changed this week, say that directly and discuss
    what would change the read. A "nothing happened" update is honest and
    useful — do not manufacture significance.
  - End with a one-line BIAS UPDATE: "BIAS: [bull / bear / neutral] —
    [one-sentence reason]"

# Reference material

## The asset
{asset_name}, category: {asset_category}.

## Structural picture (from the durable narrative — for context, do NOT repeat)
{structural_summary}

## The bull case (as of last narrative update)
{bull_case}

## The bear case (as of last narrative update)
{bear_case}

## The flat / range-bound case (as of last narrative update)
{flat_case}

## Textbook correlation framework
{correlation_view}

## Recent trading environment
{trading_environment}

## Latest positioning data available to the pipeline
{positioning_data}

## Recent price action (from the dashboard data)
{price_summary}

## Peer pairings to consider for context
{peer_context}

## Canonical sources to draw on
You should base your weekly update on what these sources have published this
week. If you do not have access to these sources directly, state that plainly
and limit your update to what can be inferred from the positioning data,
recent price action, and the publicly known calendar of upcoming releases.

{sources_list}

# Output format

Produce ONLY the weekly update text. No preamble. No headings unless they fit
naturally within the prose. The dashboard will render your output verbatim.

"""


# ─── INPUT BUILDERS ──────────────────────────────────────────────────────────

def _structural_summary(asset_id: str) -> str:
    """One-paragraph distillation of the structural picture for context.
    Pulls from extended narrative if available, else from base narrative."""
    ext = NARRATIVES_EXTENDED.get(asset_id, {})
    base = NARRATIVES.get(asset_id, {})
    perf = ext.get("performance") or base.get("performance") or "(no performance summary available)"
    # take first paragraph only — this is reference material, not the focus
    return perf.split("\n\n")[0]


def _cases_text(cases: dict, key: str) -> str:
    items = cases.get(key, []) if cases else []
    if not items:
        return "(no cases defined for this asset)"
    return "\n".join(f"  - {it}" for it in items)


def _trading_env(asset_id: str) -> str:
    te = CASES_AND_POSITIONING.get(asset_id, {}).get("trading_environment")
    return te if te else "(no trading environment description available)"


def _correlation_view(asset_id: str) -> str:
    ext = NARRATIVES_EXTENDED.get(asset_id, {})
    base = NARRATIVES.get(asset_id, {})
    return (ext.get("correlation_txt") or base.get("correlation_txt")
            or "(no correlation framework defined)")


def _positioning_data_text(positioning: Optional[dict]) -> str:
    """Render the positioning block as readable context for the LLM."""
    if not positioning:
        return "(no positioning data available)"
    lines = []
    cot = positioning.get("cot")
    if cot:
        rank = cot.get("pct_rank")
        rank_label = ""
        if rank is not None:
            if rank > 0.85: rank_label = " (EXTREME net long, top 15% of 5y range)"
            elif rank < 0.15: rank_label = " (EXTREME net short, bottom 15% of 5y range)"
            elif rank > 0.65: rank_label = " (elevated net long)"
            elif rank < 0.35: rank_label = " (elevated net short)"
        lines.append(
            f"- CFTC COT non-commercial net (as of {cot.get('latest_date')}): "
            f"{cot.get('latest_net'):,.0f} contracts{rank_label}"
        )
        ch = cot.get("change_4w")
        if ch is not None:
            lines.append(f"  4-week change: {ch:+,.0f} contracts")
    etf = positioning.get("etf_flows")
    if etf:
        lines.append(
            f"- Spot ETF net flows (as of {etf.get('latest_date')}): "
            f"latest day {etf.get('latest'):+.0f}M USD"
        )
        if etf.get("sum_5d") is not None:
            lines.append(f"  5-day sum: {etf['sum_5d']:+.0f}M USD")
        if etf.get("sum_30d") is not None:
            lines.append(f"  30-day sum: {etf['sum_30d']:+.0f}M USD")
    sent = positioning.get("sentiment")
    if sent:
        lines.append(
            f"- {sent.get('name')}: {sent.get('latest'):.0f} "
            f"({sent.get('regime', 'unknown')} regime) as of {sent.get('latest_date')}"
        )
    inv = positioning.get("exchange_inventory")
    if inv:
        lines.append(
            f"- {inv.get('name')}: {inv.get('latest'):,.0f} {inv.get('unit')} "
            f"as of {inv.get('latest_date')}"
        )
    lens = positioning.get("lens", [])
    if lens:
        lines.append(f"- Relevant positioning lenses: {', '.join(lens)}")
    return "\n".join(lines) if lines else "(no positioning data available)"


def _price_summary_text(price_summary: Optional[dict]) -> str:
    """Render price action summary if provided."""
    if not price_summary:
        return "(price action summary not provided)"
    parts = []
    if price_summary.get("last_price") is not None:
        parts.append(f"Latest close: {price_summary['last_price']:.2f} "
                     f"as of {price_summary.get('last_date', 'n/a')}")
    mom = price_summary.get("momentum", {})
    if mom:
        mom_parts = []
        for horizon in ("1W", "1M", "3M", "1Y"):
            v = mom.get(horizon)
            if v is not None:
                mom_parts.append(f"{horizon}: {v:+.1f}%")
        if mom_parts:
            parts.append("Momentum: " + ", ".join(mom_parts))
    rsi = price_summary.get("rsi")
    if rsi is not None:
        rsi_note = ""
        if rsi > 70: rsi_note = " (overbought)"
        elif rsi < 30: rsi_note = " (oversold)"
        parts.append(f"RSI(14): {rsi:.0f}{rsi_note}")
    return "\n".join(f"- {p}" for p in parts) if parts else "(no recent price data)"


def _peer_context_text(asset_id: str) -> str:
    peers = PEERS.get(asset_id, [])
    if not peers:
        return "(no peer pairings defined)"
    lines = []
    for p in peers[:3]:  # cap at 3 to keep prompt focused
        peer_name = ASSETS_BY_ID[p["asset_id"]].name if p["asset_id"] in ASSETS_BY_ID else p["asset_id"]
        lines.append(f"- vs {peer_name}: {p['rationale']}")
    return "\n".join(lines)


def _sources_list_text(asset_id: str) -> str:
    sources = SOURCES.get(asset_id, [])
    if not sources:
        return "(no source catalog for this asset)"
    by_cat = {}
    for s in sources:
        by_cat.setdefault(s["category"], []).append(s)
    out = []
    for cat in ("official", "industry", "research", "data", "news"):
        if cat in by_cat:
            out.append(f"\n  {cat.upper()}:")
            for s in by_cat[cat]:
                out.append(f"    - {s['name']}: {s['note']}")
    return "\n".join(out)


# ─── PUBLIC API ──────────────────────────────────────────────────────────────

def build_prompt(asset_id: str,
                 latest_positioning: Optional[dict] = None,
                 recent_price_action: Optional[dict] = None) -> str:
    """Build the full LLM prompt for a single asset's weekly update.

    Args:
        asset_id: one of the asset IDs in ASSETS_BY_ID
        latest_positioning: the positioning dict from _positioning_block()
            (or None if not available)
        recent_price_action: dict with keys 'last_price', 'last_date',
            'momentum', 'rsi' (or None to skip)

    Returns:
        Full prompt string ready to send to an LLM (Claude, GPT-4, etc.).
    """
    if asset_id not in ASSETS_BY_ID:
        raise ValueError(f"Unknown asset_id: {asset_id}")
    asset = ASSETS_BY_ID[asset_id]
    cases = CASES_AND_POSITIONING.get(asset_id, {}).get("cases", {})

    return BASE_PROMPT.format(
        asset_name=asset.name,
        asset_category=asset.category,
        structural_summary=_structural_summary(asset_id),
        bull_case=_cases_text(cases, "bull"),
        bear_case=_cases_text(cases, "bear"),
        flat_case=_cases_text(cases, "flat"),
        correlation_view=_correlation_view(asset_id),
        trading_environment=_trading_env(asset_id),
        positioning_data=_positioning_data_text(latest_positioning),
        price_summary=_price_summary_text(recent_price_action),
        peer_context=_peer_context_text(asset_id),
        sources_list=_sources_list_text(asset_id),
    )


def build_prompts_for_all_assets(positioning_by_asset: dict,
                                  price_summary_by_asset: dict) -> dict:
    """Build prompts for all configured assets at once.

    Args:
        positioning_by_asset: mapping asset_id -> positioning block dict
        price_summary_by_asset: mapping asset_id -> price summary dict

    Returns:
        dict mapping asset_id -> prompt string
    """
    return {
        aid: build_prompt(
            aid,
            latest_positioning=positioning_by_asset.get(aid),
            recent_price_action=price_summary_by_asset.get(aid),
        )
        for aid in ASSETS_BY_ID.keys()
    }

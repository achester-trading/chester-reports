"""
The morning anchor, as HTML. A formatter over a payload and nothing else.

Every style constant and cell helper is imported from render.py rather than
copied. Two stylesheets for one report family would drift, and the ones here
carry real constraints -- Gmail clips a message past ~102KB, so the shared parts
live on the <table> and only alignment repeats per cell.

NO ARITHMETIC HAPPENS HERE. Changes, percentages and window legs are all read
from the payload, which read them from the store, which got them from the fetch.
That is the same boundary D3's numeral audit will enforce on prose: a number in
the report is a number in the payload. A renderer that computed a change would
put arithmetic downstream of the audit and there would be nothing to audit it
against.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from . import state_block

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from daily_cascade.render import (               # noqa: E402
    ABSENT, H1, H2, NOTE, SUB, TBL, TD, TDL, TH, THL, WARN, WRAP,
    dash, esc, num, portfolio_block, pin_table, _rows,
)


def signed(v, dp: int = 2) -> str:
    """A change, with its sign always shown and its direction coloured.

    The sign is explicit because "12.50" in a change column is ambiguous at a
    glance in a way "+12.50" is not, and this report is read at 07:00.
    """
    if v is None:
        return dash("no value in the payload")
    try:
        f = float(v)
    except (TypeError, ValueError):
        return dash("unparseable")
    colour = "#0d7a3f" if f > 0 else ("#b3261e" if f < 0 else "#43525f")
    return f'<span style="color:{colour}">{f:+,.{dp}f}</span>'


def overnight_table(payload: dict) -> str:
    block = payload.get("overnight") or {}
    if block.get("state") == "absent":
        return (f'<div style="{ABSENT}"><strong>Overnight &mdash; absent.</strong> '
                f'{esc(block.get("reason") or "no reason recorded")}</div>')

    rows = []
    for r in block.get("rows") or []:
        flag = ""
        if r.get("stale"):
            age = r.get("age_minutes")
            flag = (f' <span style="color:#b3261e" title="fetched '
                    f'{age:.0f} minutes ago">stale</span>' if age is not None
                    else ' <span style="color:#b3261e">stale</span>')
        rows.append(
            f'<tr><td style="{TDL}">{esc(r.get("label"))}{flag}</td>'
            f'<td style="{TDL}"><code>{esc(r.get("symbol"))}</code></td>'
            f'<td style="{TD}">{num(r.get("last"))}</td>'
            f'<td style="{TD}">{num(r.get("prior_settle"))}</td>'
            f'<td style="{TD}">{signed(r.get("chg"))}</td>'
            f'<td style="{TD}">{signed(r.get("chg_pct"))}%</td></tr>')

    if not rows:
        return (f'<div style="{ABSENT}"><strong>Overnight &mdash; no rows.</strong> '
                f'{esc(block.get("reason") or "")}</div>')

    return f"""<table style="{TBL}">
<thead><tr>
  <th style="{THL}">Instrument</th><th style="{THL}">Symbol</th>
  <th style="{TH}">Level</th><th style="{TH}">Prior settle</th>
  <th style="{TH}">Change</th><th style="{TH}">%</th>
</tr></thead>
<tbody>{_rows(rows)}</tbody></table>
<p style="{NOTE}">
  Change is against the <strong>prior US settlement</strong> &mdash; 16:00 ET of
  the previous US session &mdash; for every instrument, including the cash
  indices whose own last close is hours older. One interval, so the column is
  comparable down its length.
</p>"""


def attribution_block(payload: dict) -> str:
    block = payload.get("overnight") or {}
    legs = block.get("attribution") or []
    if not legs:
        return (f'<div style="{ABSENT}"><strong>Attribution &mdash; absent.</strong> '
                f'5-minute bars were unavailable for the index futures, so the '
                f'overnight move cannot be split by session.</div>')

    rows = []
    for r in legs:
        rows.append(
            f'<tr><td style="{TDL}">{esc(r.get("label"))}</td>'
            f'<td style="{TD}">{signed(r.get("tokyo"))}</td>'
            f'<td style="{TD}">{signed(r.get("europe"))}</td>'
            f'<td style="{TD}">{signed(r.get("other"))}</td></tr>')

    return f"""<table style="{TBL}">
<thead><tr>
  <th style="{THL}">Instrument</th>
  <th style="{TH}">Tokyo<br>19:00&ndash;03:00</th>
  <th style="{TH}">Europe<br>03:00&ndash;06:45</th>
  <th style="{TH}">Outside both</th>
</tr></thead>
<tbody>{_rows(rows)}</tbody></table>
<p style="{NOTE}">
  <strong>A first pass, and a window is not a cause.</strong> These are clock
  windows in ET, not causal attributions: a move inside the Tokyo window may be
  a US headline that landed at 21:00 ET. The three legs sum to the overnight
  change, so they can be checked against the level above. Backdrop context only
  &mdash; per 31.3(a) an attribution line may not generate a Book C setup.
  Computed only for the continuously traded futures; a cash index is shut for
  two of the three windows and splitting its move across them would be
  arithmetic on hours it was not trading.
</p>"""


def exposure_block(payload: dict) -> str:
    """The prior settle's dealer surface, abbreviated to the levels that matter.

    Narrower than the close report's table on purpose. At 07:00 the question is
    which levels this morning's futures are approaching, not the full surface --
    the close debrief already published that, and reprinting it would make this
    report long enough to be clipped by Gmail and skimmed instead of read.
    """
    rows = []
    for r in payload.get("exposure") or []:
        rows.append(
            f'<tr><td style="{TDL}"><code>{esc(r.get("symbol"))}</code></td>'
            f'<td style="{TD}">{num(r.get("spot"))}</td>'
            f'<td style="{TD}">{num(r.get("gamma_flip"))}</td>'
            f'<td style="{TD}">{num(r.get("call_wall"))}</td>'
            f'<td style="{TD}">{num(r.get("put_wall"))}</td>'
            f'<td style="{TDL}">{"above" if r.get("spot_above_flip") else "below"}</td>'
            f'</tr>')
    if not rows:
        return (f'<div style="{ABSENT}"><strong>Prior exposure &mdash; absent.</strong> '
                f'No scoreable profile for {esc(payload.get("prior_session"))}; '
                f'the EOD pass produced nothing for that session.</div>')
    return f"""<table style="{TBL}">
<thead><tr>
  <th style="{THL}">Symbol</th><th style="{TH}">Settle spot</th>
  <th style="{TH}">Gamma flip</th><th style="{TH}">Call wall</th>
  <th style="{TH}">Put wall</th><th style="{THL}">Spot vs flip</th>
</tr></thead>
<tbody>{_rows(rows)}</tbody></table>
<p style="{NOTE}">
  The settled 16:10 profile for {esc(payload.get('exposure_session'))} &mdash;
  the structure this morning's futures are moving inside. Inferred, not
  observed: dealer positioning is estimated from public open interest under a
  signing assumption that cannot be verified from a chain.
</p>"""


def render(payload: dict, delivery: Optional[dict] = None) -> str:
    warn = ""
    if payload.get("warnings"):
        items = "".join(f"<li>{esc(w)}</li>" for w in payload["warnings"])
        warn = (f'<div style="{WARN}"><strong>Warnings</strong>'
                f'<ul style="margin:6px 0 0 0;padding-left:18px">{items}</ul></div>')

    block = payload.get("overnight") or {}
    return f"""<div style="{WRAP}">
<h1 style="{H1}">Morning anchor &mdash; {esc(payload.get('session'))}</h1>
<p style="{SUB}">
  Data only. No narrative, by ruling: prose is added after the numeral audit
  exists to fail a block that invents a number.<br>
  Generated {esc(payload.get('generated_at'))} &middot;
  overnight fetched {esc(block.get('fetched_at') or 'n/a')} &middot;
  prior session {esc(payload.get('prior_session'))} &middot;
  run <code>{esc(payload.get('run_id') or 'n/a')}</code>
</p>
{warn}
<h2 style="{H2}">What changed</h2>
{state_block.what_changed_block(payload)}

<h2 style="{H2}">Market state</h2>
{state_block.state_table(payload)}

<h2 style="{H2}">Contradictions</h2>
{state_block.contradiction_table(payload)}

<h2 style="{H2}">Exceptions</h2>
{state_block.exceptions_block(payload)}

<h2 style="{H2}">Overnight</h2>
{overnight_table(payload)}

<h2 style="{H2}">Where it happened</h2>
{attribution_block(payload)}

<h2 style="{H2}">Prior close &mdash; dealer surface</h2>
{exposure_block(payload)}

<h2 style="{H2}">Prior close &mdash; pin verdicts</h2>
{pin_table(payload)}

<h2 style="{H2}">Portfolio truth</h2>
{portfolio_block(payload)}

<h2 style="{H2}">Provenance</h2>
<p style="{NOTE}">
  This report fetched nothing (30.4): the 06:45 timer wrote the overnight rows
  to the store and everything above was read back from it through an as-of
  cutoff, so this edition can be rebuilt for a past morning and will show what
  was knowable then. No figure here is a recommendation and nothing in this
  edition enters the decision register.<br>
  Archived to <code>{esc((delivery or {}).get('archive_path') or 'n/a')}</code>
  before this message was sent &mdash; the record does not depend on the mail
  server.
</p>
</div>"""


def text_fallback(payload: dict) -> str:
    """Plain text for a client that will not render HTML. Deliberately terse."""
    block = payload.get("overnight") or {}
    lines = [f"Morning anchor -- {payload.get('session')}",
             f"generated {payload.get('generated_at')}",
             f"overnight fetched {block.get('fetched_at') or 'n/a'}", ""]
    # Same module, same position as the HTML edition and as the close report's.
    lines += state_block.text_lines(payload)
    lines.append("")
    if block.get("state") == "absent":
        lines.append(f"OVERNIGHT ABSENT: {block.get('reason')}")
    for r in block.get("rows") or []:
        chg = r.get("chg")
        pct_ = r.get("chg_pct")
        lines.append(f"{r.get('symbol'):<10} {r.get('last')}  "
                     f"chg {chg if chg is not None else 'n/a'} "
                     f"({pct_ if pct_ is not None else 'n/a'}%)"
                     f"{'  STALE' if r.get('stale') else ''}")
    for r in block.get("attribution") or []:
        lines.append(f"{r.get('symbol'):<10} tokyo {r.get('tokyo')}  "
                     f"europe {r.get('europe')}  other {r.get('other')}")
    lines.append("")
    for w in payload.get("warnings") or []:
        lines.append(f"WARNING: {w}")
    return "\n".join(lines)

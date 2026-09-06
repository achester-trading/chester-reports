"""
Payload -> HTML. Formatting only.

NOTHING HERE COMPUTES ANYTHING. Every number in the output is a number from the
payload, passed through a formatter. That is not tidiness, it is the D4c ruling
made structural: this edition exists to prove the delivery chain while prose is
still untrusted, and a renderer that derived a ratio or summed a column would be
generating unaudited figures under a heading that says it does not.

The one thing it does decide is how to show ABSENCE. A blank cell and a missing
source render identically and mean opposite things, so nothing is ever blank: a
value the system does not have prints as a dash with a title attribute, and a
block the system has not built prints as a labelled NOT BUILT row.

EMAIL CONSTRAINTS, WHICH ARE NOT WEB CONSTRAINTS. Styles are inline because
Gmail and Outlook strip or ignore <style> blocks in the body; layout is tables
because email clients' flexbox support is a rumour; there is no JavaScript, no
external CSS, and no remote images, all of which are stripped or blocked and
the last of which would also leak a read receipt to whoever hosted it.
"""

from __future__ import annotations

from typing import Optional

# Inline everywhere. See the module docstring.
WRAP = ("font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,"
        "Arial,sans-serif;font-size:13px;color:#1a1a1a;background:#ffffff;"
        "max-width:900px;margin:0 auto;padding:16px;")
H1 = ("font-size:18px;margin:0 0 2px 0;color:#0d2b45;font-weight:600;")
SUB = "font-size:12px;color:#5a6b7a;margin:0 0 18px 0;"
H2 = ("font-size:13px;margin:22px 0 6px 0;color:#0d2b45;font-weight:600;"
      "text-transform:uppercase;letter-spacing:0.04em;")
NOTE = "font-size:11px;color:#5a6b7a;margin:4px 0 0 0;line-height:1.45;"
# The per-cell strings are kept SHORT on purpose. Gmail clips a message past
# ~102KB and shows a "view entire message" link, which on a daily report means
# the bottom half stops being read. Inline styles are unavoidable in email, so
# the shared parts (font, tabular figures, borders) live on the <table> and are
# inherited; only alignment and padding repeat per cell. That is the difference
# between a ~15KB message and a ~65KB one for the same content.
TBL = ("border-collapse:collapse;width:100%;font-size:12px;"
       "font-variant-numeric:tabular-nums;"
       "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;")
TH = "text-align:right;padding:5px 7px;border-bottom:2px solid #0d2b45;color:#0d2b45"
THL = "text-align:left;padding:5px 7px;border-bottom:2px solid #0d2b45;color:#0d2b45"
TD = "text-align:right;padding:4px 7px;border-bottom:1px solid #e6ebef"
TDL = "text-align:left;padding:4px 7px;border-bottom:1px solid #e6ebef"
WARN = ("background:#fff4e5;border-left:3px solid #d97706;padding:9px 12px;"
        "margin:0 0 14px 0;font-size:12px;color:#7c3a00;")
ABSENT = ("background:#f4f6f8;border-left:3px solid #94a3b8;padding:9px 12px;"
          "margin:6px 0;font-size:12px;color:#43525f;")


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def dash(title: str = "not available") -> str:
    """The only way a cell is ever empty."""
    return f'<span style="color:#a8b3bd" title="{esc(title)}">&mdash;</span>'


def num(v, dp: int = 2) -> str:
    return dash() if v is None else f"{float(v):,.{dp}f}"


def money(v) -> str:
    """Signed, scaled, and the scale is IN the cell, not in the header.

    A column headed "$bn" containing a value that is really millions is the
    kind of unit error the net-liquidity gotcha in CLAUDE.md exists to warn
    about. Carrying the suffix per cell costs three characters and removes the
    question.
    """
    if v is None:
        return dash()
    v = float(v)
    a = abs(v)
    if a >= 1e9:
        return f"{v / 1e9:,.2f}bn"
    if a >= 1e6:
        return f"{v / 1e6:,.1f}mm"
    if a >= 1e3:
        return f"{v / 1e3:,.1f}k"
    return f"{v:,.0f}"


def pct(v) -> str:
    return dash() if v is None else f"{float(v) * 100:,.1f}%"


def hit(v) -> str:
    if v is None:
        return dash("not scored")
    return ('<span style="color:#0b7a3b;font-weight:600">HIT</span>' if v
            else '<span style="color:#9aa5b0">miss</span>')


def _rows(rows: list[str]) -> str:
    return "\n".join(rows)


def exposure_table(payload: dict) -> str:
    rows = payload.get("exposure") or []
    if not rows:
        return f'<div style="{ABSENT}">No exposure profiles for this session.</div>'
    head = ("<tr>"
            f'<th style="{THL}">Symbol</th>'
            f'<th style="{TH}">Spot</th>'
            f'<th style="{TH}">Net GEX</th>'
            f'<th style="{TH}">$&gamma;/1%</th>'
            f'<th style="{TH}">Flip</th>'
            f'<th style="{TH}">Put wall</th>'
            f'<th style="{TH}">Call wall</th>'
            f'<th style="{TH}">Max pain</th>'
            f'<th style="{TH}">Peak |GEX|</th>'
            f'<th style="{TH}">DEX $</th>'
            f'<th style="{TH}">VEX/volpt</th>'
            f'<th style="{TH}">CHEX/day</th>'
            f'<th style="{TH}">Q</th>'
            "</tr>")
    body = []
    for r in rows:
        q = r.get("data_quality") or "?"
        qcol = "#0b7a3b" if q == "ok" else "#b45309"
        flag = ("" if not r.get("min_t_load_bearing") else
                ' <span style="color:#b45309" title="floored rows carry &gt;5%'
                ' of a bucket\'s |GEX|; the MIN_T guard is load-bearing here">'
                '&#9888;</span>')
        body.append(
            "<tr>"
            f'<td style="{TDL}"><strong>{esc(r["symbol"])}</strong>{flag}</td>'
            f'<td style="{TD}">{num(r.get("spot"))}</td>'
            f'<td style="{TD}">{money(r.get("net_gex"))}</td>'
            f'<td style="{TD}">{money(r.get("dollar_gamma_per_1pct"))}</td>'
            f'<td style="{TD}">{num(r.get("gamma_flip"))}</td>'
            f'<td style="{TD}">{num(r.get("put_wall"))}</td>'
            f'<td style="{TD}">{num(r.get("call_wall"))}</td>'
            f'<td style="{TD}">{num(r.get("max_pain"))}</td>'
            f'<td style="{TD}">{num(r.get("peak_abs_gex_strike"))}</td>'
            f'<td style="{TD}">{money(r.get("dex_notional"))}</td>'
            f'<td style="{TD}">{money(r.get("vex_per_volpt"))}</td>'
            f'<td style="{TD}">{money(r.get("chex_per_day"))}</td>'
            f'<td style="{TD}"><span style="color:{qcol}">{esc(q)}</span></td>'
            "</tr>")
    srcs = sorted({r.get("greeks_source") or "?" for r in rows})
    caps = sorted({(r.get("fetched_at") or "?")[:19] for r in rows})
    note = (f'<p style="{NOTE}">Signing is '
            f'<strong>{esc(payload.get("convention_version"))}</strong> &mdash; '
            "dealers long calls, short puts. A convention, not observed "
            "positioning; the flip-side reading inverts every sign. "
            f"Greeks source: {esc(', '.join(srcs))}. "
            f"Capture: {esc(caps[0])}"
            + (f" &hellip; {esc(caps[-1])}" if len(caps) > 1 else "")
            + " UTC. All four Greeks are one confluence cluster "
              "(<code>mechanism_group=dealer_chain_derived</code>), never four "
              "independent votes.</p>")
    return (f'<table style="{TBL}">{head}{_rows(body)}</table>{note}')


def missing_block(payload: dict) -> str:
    miss = payload.get("exposure_missing") or []
    if not miss:
        return ""
    items = "".join(f"<li><strong>{esc(m['symbol'])}</strong> &mdash; "
                    f"{esc(m['reason'])}</li>" for m in miss)
    return (f'<div style="{ABSENT}">Not in the table above:'
            f'<ul style="margin:6px 0 0 0;padding-left:18px">{items}</ul></div>')


def pin_table(payload: dict) -> str:
    rows = payload.get("pins") or []
    if not rows:
        return f'<div style="{ABSENT}">No pin-log rows for this session.</div>'
    head = ("<tr>"
            f'<th style="{THL}">Symbol</th>'
            f'<th style="{TH}">Close</th>'
            f'<th style="{TH}">Max pain</th>'
            f'<th style="{TH}">bps</th>'
            f'<th style="{TH}">&nbsp;</th>'
            f'<th style="{TH}">Peak |GEX|</th>'
            f'<th style="{TH}">bps</th>'
            f'<th style="{TH}">&nbsp;</th>'
            f'<th style="{TH}">Call wall</th>'
            f'<th style="{TH}">Put wall</th>'
            f'<th style="{TH}">vs flip</th>'
            "</tr>")
    body = []
    for r in rows:
        above = r.get("spot_above_flip")
        above_s = (dash("no flip level") if above is None else
                   ("above" if above else "below"))
        body.append(
            "<tr>"
            f'<td style="{TDL}"><strong>{esc(r["symbol"])}</strong></td>'
            f'<td style="{TD}">{num(r.get("close"))}</td>'
            f'<td style="{TD}">{num(r.get("max_pain"))}</td>'
            f'<td style="{TD}">{num(r.get("max_pain_dist_bps"), 0)}</td>'
            f'<td style="{TD}">{hit(r.get("max_pain_hit"))}</td>'
            f'<td style="{TD}">{num(r.get("peak_gex_strike"))}</td>'
            f'<td style="{TD}">{num(r.get("peak_gex_dist_bps"), 0)}</td>'
            f'<td style="{TD}">{hit(r.get("peak_gex_hit"))}</td>'
            f'<td style="{TD}">{hit(r.get("call_wall_hit"))}</td>'
            f'<td style="{TD}">{hit(r.get("put_wall_hit"))}</td>'
            f'<td style="{TD}">{above_s}</td>'
            "</tr>")
    h = payload.get("pin_hits") or {}
    n = len(rows)
    tol = payload.get("tolerance_bps")
    note = (f'<p style="{NOTE}">Out of {n}: '
            f'max pain {h.get("max_pain_hit", 0)}, '
            f'peak |GEX| {h.get("peak_gex_hit", 0)}, '
            f'call wall {h.get("call_wall_hit", 0)}, '
            f'put wall {h.get("put_wall_hit", 0)}. '
            f'Tolerance {esc(tol)}bps of spot, <strong>declared in advance and '
            'never revised after the fact</strong> &mdash; each row carries the '
            'tolerance it was graded at, so a rerun cannot regrade history at '
            'today&rsquo;s value.</p>')
    return f'<table style="{TBL}">{head}{_rows(body)}</table>{note}'


def regime_block(payload: dict) -> str:
    rows = payload.get("regime") or []
    items = "".join(
        f'<li><code>{esc(r["key"])}</code> &mdash; '
        f'<strong style="color:#b45309">{esc(r["state"].upper().replace("_", " "))}'
        f'</strong>. {esc(r["note"])}</li>' for r in rows)
    return (f'<div style="{ABSENT}">These are named and not yet built. They '
            'appear here rather than being omitted so the gap is visible in '
            'the report that will carry them, instead of only in a TODO.'
            f'<ul style="margin:6px 0 0 0;padding-left:18px">{items}</ul></div>')


def portfolio_block(payload: dict) -> str:
    p = payload.get("portfolio") or {}
    if p.get("state") != "ok":
        return (f'<div style="{ABSENT}"><strong>No Portfolio Truth.</strong> '
                f'{esc(p.get("reason") or "unknown")}</div>')
    acc = p.get("account") or {}
    arows = []
    for key, v in acc.items():
        arows.append(
            "<tr>"
            f'<td style="{TDL}"><code>{esc(key)}</code></td>'
            f'<td style="{TD}">{money(v.get("value"))}</td>'
            f'<td style="{TDL}">{esc((v.get("observed_at") or "")[:19])}</td>'
            "</tr>")
    acc_tbl = ("" if not arows else
               f'<table style="{TBL}"><tr>'
               f'<th style="{THL}">Account</th><th style="{TH}">Value</th>'
               f'<th style="{THL}">Observed</th></tr>{_rows(arows)}</table>')

    pos = p.get("positions") or []
    if not pos:
        pos_tbl = (f'<div style="{ABSENT}">No open positions in the store as '
                   'of this cutoff.</div>')
    else:
        prows = []
        for r in pos:
            prows.append(
                "<tr>"
                f'<td style="{TDL}">{esc(r["instrument"])}</td>'
                f'<td style="{TD}">{num(r.get("qty"), 0)}</td>'
                f'<td style="{TD}">{money(r.get("market_value"))}</td>'
                f'<td style="{TD}">{money(r.get("unrealized_pnl"))}</td>'
                "</tr>")
        pos_tbl = (f'<table style="{TBL}"><tr>'
                   f'<th style="{THL}">Instrument</th><th style="{TH}">Qty</th>'
                   f'<th style="{TH}">Market value</th>'
                   f'<th style="{TH}">Unrealised</th></tr>'
                   f'{_rows(prows)}</table>')
    note = (f'<p style="{NOTE}">Read-only, <code>source=ibkr_paper</code>, '
            '<code>mechanism_group=portfolio_truth</code>. Every one of these '
            'is <code>trigger_eligible: false</code> &mdash; they say what is '
            'held, never what to do about it.</p>')
    return acc_tbl + pos_tbl + note


def render(payload: dict, delivery: Optional[dict] = None) -> str:
    warn = ""
    if payload.get("warnings"):
        items = "".join(f"<li>{esc(w)}</li>" for w in payload["warnings"])
        warn = (f'<div style="{WARN}"><strong>Warnings</strong>'
                f'<ul style="margin:6px 0 0 0;padding-left:18px">{items}</ul></div>')

    u = payload.get("universe") or {}
    n_g, n_i = len(u.get("greeks") or []), len(u.get("ingestion_only") or [])

    return f"""<div style="{WRAP}">
<h1 style="{H1}">Close debrief &mdash; {esc(payload.get('session'))}</h1>
<p style="{SUB}">
  Data only. No narrative, by ruling: prose is added after the numeral audit
  exists to fail a block that invents a number.<br>
  Generated {esc(payload.get('generated_at'))} &middot;
  as-of cutoff {esc(payload.get('as_of'))} &middot;
  run <code>{esc(payload.get('run_id') or 'n/a')}</code> &middot;
  universe {n_g} with Greeks + {n_i} ingestion-only
</p>
{warn}
<h2 style="{H2}">Dealer exposure</h2>
{exposure_table(payload)}
{missing_block(payload)}

<h2 style="{H2}">Pin verdicts</h2>
{pin_table(payload)}

<h2 style="{H2}">Regime</h2>
{regime_block(payload)}

<h2 style="{H2}">Portfolio truth</h2>
{portfolio_block(payload)}

<h2 style="{H2}">Provenance</h2>
<p style="{NOTE}">
  Every figure above was read from the store or from a computed profile; this
  report fetched nothing (30.4). No figure here is a recommendation, and
  nothing in this edition enters the decision register. Delivery:
  {esc((delivery or {}).get('delivery', 'n/a'))} &middot; archive:
  <code>{esc((delivery or {}).get('archive_path') or 'n/a')}</code>
</p>
</div>"""


def text_fallback(payload: dict) -> str:
    """Plain text for a client that will not render HTML. Deliberately terse."""
    lines = [f"Close debrief -- {payload.get('session')}",
             f"generated {payload.get('generated_at')}", ""]
    for r in payload.get("exposure") or []:
        lines.append(f"{r['symbol']:<6} spot {r.get('spot')}  "
                     f"net_gex {r.get('net_gex')}  flip {r.get('gamma_flip')}")
    h = payload.get("pin_hits") or {}
    lines += ["", f"pin hits: {h}", ""]
    for w in payload.get("warnings") or []:
        lines.append(f"WARNING: {w}")
    return "\n".join(lines)

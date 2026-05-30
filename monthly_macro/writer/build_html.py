"""
Convert the Monthly Macro Report markdown into a styled, accordion HTML file.

Each top-level (## ) section becomes a <details> accordion with a navy header bar.
Executive Summary and Pillar Snapshot start expanded; all other sections collapsed.
"""

from __future__ import annotations
import re
import markdown


def build_html(md_text: str) -> str:
    """Render the markdown report to a styled HTML page."""

    lines = md_text.split("\n")
    section_re = re.compile(r"^##\s+(?!#)(.*)$")

    sections = []
    preamble_lines = []
    cur_header = None
    cur_body = []

    for line in lines:
        m = section_re.match(line)
        if m:
            if cur_header is not None:
                sections.append((cur_header, "\n".join(cur_body)))
            else:
                preamble_lines = cur_body
            cur_header = m.group(1).strip()
            cur_body = []
        else:
            cur_body.append(line)
    if cur_header is not None:
        sections.append((cur_header, "\n".join(cur_body)))
    else:
        preamble_lines = cur_body

    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])

    def render(md_text):
        md.reset()
        return md.convert(md_text)

    preamble_html = render("\n".join(preamble_lines))

    def is_open(header: str) -> bool:
        h = header.strip()
        return h.startswith("I. Executive Summary") or h.startswith("II. Pillar Snapshot")

    accordions = []
    for header, body in sections:
        body_html = render(body)
        open_attr = " open" if is_open(header) else ""
        accordions.append(f"""
    <details class="section"{open_attr}>
      <summary class="section-head">
        <span class="section-title">{header}</span>
        <span class="chev" aria-hidden="true"></span>
      </summary>
      <div class="section-body">
        {body_html}
      </div>
    </details>""")
    accordions_html = "\n".join(accordions)

    css = """
:root {
  --navy: #0f2747;
  --navy-2: #16335c;
  --navy-line: #21436f;
  --ink: #1a1f29;
  --muted: #5b6675;
  --paper: #f7f5f0;
  --card: #ffffff;
  --rule: #e4e0d6;
  --accent: #b9892f;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Georgia, 'Iowan Old Style', 'Times New Roman', serif;
  font-size: 16px;
  line-height: 1.55;
}
.wrap { max-width: 920px; margin: 0 auto; padding: 18px 14px 80px; }
.masthead {
  background: var(--navy); color: #fff; border-radius: 10px;
  padding: 22px 20px; margin-bottom: 18px;
  box-shadow: 0 2px 10px rgba(15,39,71,.18);
}
.masthead h1 { margin: 0 0 6px; font-size: 1.55rem; letter-spacing: .3px; font-weight: 700; }
.masthead p { color: #c7d4e8; margin: 4px 0; }
.masthead p strong { color: #fff; }
.controls { display: flex; gap: 8px; margin: 0 0 16px; }
.controls button {
  font-family: inherit; font-size: .78rem; letter-spacing: .04em;
  text-transform: uppercase; background: #fff; color: var(--navy);
  border: 1px solid var(--navy-line); border-radius: 6px;
  padding: 7px 12px; cursor: pointer;
}
details.section {
  background: var(--card); border: 1px solid var(--rule);
  border-radius: 9px; margin-bottom: 12px; overflow: hidden;
}
summary.section-head {
  list-style: none; cursor: pointer; background: var(--navy); color: #fff;
  padding: 14px 16px; display: flex; align-items: center; justify-content: space-between;
  gap: 10px; user-select: none;
}
summary.section-head::-webkit-details-marker { display: none; }
.section-title { font-size: 1.02rem; font-weight: 700; letter-spacing: .2px; }
.chev {
  width: 18px; height: 18px; flex: 0 0 auto;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 14px; color: #cdd9ec; transition: transform .18s ease;
}
.chev::before { content: "\\25B8"; }
details[open] .chev { transform: rotate(90deg); color: #fff; }
details[open] summary.section-head { background: var(--navy-2); }
.section-body { padding: 6px 16px 18px; }
.section-body h2 { font-size: 1.05rem; color: var(--navy); margin: 18px 0 6px;
  border-bottom: 1px solid var(--rule); padding-bottom: 4px; }
.section-body h3 { font-size: .98rem; color: var(--navy-2); margin: 16px 0 4px; }
.section-body h4 { font-size: .9rem; color: var(--muted); margin: 12px 0 4px;
  text-transform: uppercase; letter-spacing: .05em; }
.section-body p { margin: 8px 0; }
.section-body strong { color: var(--navy); }
.section-body em { color: var(--muted); }
.section-body ul { margin: 8px 0; padding-left: 20px; }
.section-body li { margin: 3px 0; }
.section-body hr { border: 0; border-top: 1px solid var(--rule); margin: 16px 0; }
.section-body table {
  width: 100%; border-collapse: collapse; margin: 10px 0;
  font-family: 'SF Mono', ui-monospace, 'Menlo', monospace;
  font-size: .72rem; line-height: 1.35;
}
.section-body th, .section-body td {
  border: 1px solid var(--rule); padding: 5px 6px; text-align: left; vertical-align: top;
}
.section-body th { background: var(--navy); color: #fff; font-weight: 600; }
.section-body tr:nth-child(even) td { background: #faf8f3; }
.section-body .tablewrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
footer { text-align: center; color: var(--muted); font-size: .75rem; margin-top: 24px; font-style: italic; }
@media (max-width: 480px) {
  body { font-size: 15px; }
  .section-body table { font-size: .66rem; }
  .masthead h1 { font-size: 1.3rem; }
}
"""

    js = """
document.querySelectorAll('.section-body table').forEach(function(t) {
  if (t.parentElement && t.parentElement.classList.contains('tablewrap')) return;
  var w = document.createElement('div'); w.className = 'tablewrap';
  t.parentNode.insertBefore(w, t); w.appendChild(t);
});
document.getElementById('expandAll').addEventListener('click', function() {
  document.querySelectorAll('details.section').forEach(function(d) { d.open = true; });
});
document.getElementById('collapseAll').addEventListener('click', function() {
  document.querySelectorAll('details.section').forEach(function(d) { d.open = false; });
});
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Monthly Macro Report</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    {preamble_html}
  </div>

  <div class="controls">
    <button id="expandAll">Expand all</button>
    <button id="collapseAll">Collapse all</button>
  </div>

  {accordions_html}

  <footer>Generated as a standalone HTML artifact — tap section headers to expand/collapse</footer>
</div>

<script>{js}</script>
</body>
</html>"""

    return html

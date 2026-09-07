#!/usr/bin/env python3
"""Build a white paper's HTML edition from its Markdown.

WHY THIS EXISTS. The HTML editions used to be made by hand, which is why the
repo spent a week with the rule "the HTML is canonical for reading, the
Markdown is canonical for editing" and a directory of HTML built from .md files
that had since been audited. A hand-built artifact drifts from its source; a
built one cannot. The .md is now canonical for everything, the figures are
files under docs/figures/, and this is the only thing that writes docs/html/.

WHAT IT PRODUCES. The house style of monthly_macro/writer/build_html.py --
navy masthead, navy accordion headers, cream paper, monospace tables -- with
two things that report does not need: an anchor table of contents across the
accordions, and inline figures.

FIGURES ARE EMBEDDED, NOT LINKED. A built edition is one file a reader can
open, mail, or keep; a page of broken image icons is not that. SVG is inlined
as an element (so it inherits the page's fonts and scales), PNG as a data URI.
Inlined SVG brings its own element ids with it -- matplotlib emits the same
glyph ids in every figure it draws -- so every id in a figure is namespaced by
its figure number before it goes in, or the eighth chart on a page renders
with the first chart's glyphs.

Usage:
    python tools/build_paper_html.py                     # every roster paper
    python tools/build_paper_html.py docs/whitepapers/earnings-whitepaper.md
"""

from __future__ import annotations

import base64
import html as htmllib
import re
import sys
from pathlib import Path

import markdown

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "docs" / "whitepapers"
OUT = ROOT / "docs" / "html"

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp"}


# ---------------------------------------------------------------- structure
def split_masthead(text):
    """Where the navy block stops.

    tools/check_library.py's rule is "everything before the first line that is
    exactly ---", and for most papers that is right. Three papers put a
    Contents list above that rule, though, and a table of contents set in the
    masthead is a wall of white-on-navy links duplicating the one this builder
    generates. So the masthead also stops at the first heading that is a
    section rather than a subtitle -- a subtitle being a heading that follows
    the title with nothing but other headings between.
    """
    lines = text.split("\n")
    stop = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "---":
            stop = i
            break
    seen_title = False
    subtitle_chain = True
    for i, line in enumerate(lines[:stop]):
        if not line.strip():
            continue
        if line.startswith("#"):
            if not seen_title:
                seen_title = True
                continue
            if subtitle_chain:
                continue
            return lines[:i], lines[i:]
        subtitle_chain = False
    return lines[:stop], lines[stop + 1:]


def split_level(body_lines):
    """Which heading level carries the paper's Parts.

    The library is not consistent: some papers put PART at '#' and chapters at
    '##', others start at '##' and never use '#' after the title. Two or more
    '#' headings in the body means the Parts live there; otherwise '##' does.
    """
    return 1 if sum(1 for l in body_lines if l.startswith("# ")) >= 2 else 2


def sections(body_lines, level):
    """[(header, body)] plus whatever precedes the first header."""
    pat = re.compile(r"^#{%d}\s+(?!#)(.*)$" % level)
    pre, out, header, buf = [], [], None, []
    for line in body_lines:
        m = pat.match(line)
        if m:
            if header is None:
                pre = buf
            else:
                out.append((header, "\n".join(buf)))
            header, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if header is None:
        pre = buf
    else:
        out.append((header, "\n".join(buf)))
    return pre, out


def anchor(i, header):
    slug = re.sub(r"[^\w\s-]", "", header.lower())
    slug = re.sub(r"\s+", "-", slug).strip("-")[:60]
    return f"s{i}-{slug}" if slug else f"s{i}"


# ------------------------------------------------------------------ figures
def namespace_ids(svg, tag):
    """Make every id in one figure unique to that figure."""
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    if not ids:
        return svg
    alt = "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))
    svg = re.sub(r'\bid="(%s)"' % alt, lambda m: 'id="%s-%s"' % (tag, m.group(1)), svg)
    svg = re.sub(r'\b((?:xlink:)?href)="#(%s)"' % alt,
                 lambda m: '%s="#%s-%s"' % (m.group(1), tag, m.group(2)), svg)
    svg = re.sub(r"url\(#(%s)\)" % alt,
                 lambda m: "url(#%s-%s)" % (tag, m.group(1)), svg)
    return svg


def inline_svg(path, tag):
    svg = path.read_text(encoding="utf-8")
    start = svg.find("<svg")
    if start == -1:
        raise ValueError(f"{path}: no <svg> element")
    svg = svg[start:]
    # A fixed pixel width overflows the column on a phone; the viewBox carries
    # the aspect ratio, so width:100% is enough.
    svg = re.sub(r'(<svg\b[^>]*?)\s(width|height)="[^"]*"', r"\1", svg, count=2)
    svg = svg.replace("<svg", '<svg width="100%" preserveAspectRatio="xMidYMid meet"', 1)
    return namespace_ids(svg, tag)


def embed_figures(html, md_path, report):
    """Replace <img src="../figures/..."> with the figure itself."""
    n = [0]

    def sub(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        if not src:
            return tag
        target = (md_path.parent / src.group(1)).resolve()
        caption = htmllib.unescape(alt.group(1)) if alt else ""
        if not target.exists():
            report.append(f"missing figure {src.group(1)}")
            return tag
        n[0] += 1
        if target.suffix == ".svg":
            art = inline_svg(target, f"f{n[0]:02d}")
        else:
            data = base64.b64encode(target.read_bytes()).decode("ascii")
            art = ('<img alt="%s" src="data:%s;base64,%s">'
                   % (htmllib.escape(caption), MIME.get(target.suffix, "image/png"), data))
        cap = ('<figcaption>%s</figcaption>' % htmllib.escape(caption)) if caption else ""
        return '<figure class="fig">%s%s</figure>' % (art, cap)

    return re.sub(r"<img\b[^>]*>", sub, html)


# ------------------------------------------------------------------- render
CSS = """
:root {
  --navy: #0f2747; --navy-2: #16335c; --navy-line: #21436f;
  --ink: #1a1f29; --muted: #5b6675; --paper: #f7f5f0; --card: #ffffff;
  --rule: #e4e0d6; --accent: #b9892f;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font-family: Georgia, 'Iowan Old Style', 'Times New Roman', serif;
  font-size: 16px; line-height: 1.55;
}
.wrap { max-width: 920px; margin: 0 auto; padding: 18px 14px 80px; }
.masthead {
  background: var(--navy); color: #fff; border-radius: 10px;
  padding: 22px 20px; margin-bottom: 18px;
  box-shadow: 0 2px 10px rgba(15,39,71,.18);
}
.masthead h1 { margin: 0 0 6px; font-size: 1.55rem; letter-spacing: .3px; font-weight: 700; }
.masthead h2, .masthead h3 { margin: 4px 0; font-size: 1rem; font-weight: 400; color: #c7d4e8; }
.masthead p { color: #c7d4e8; margin: 4px 0; }
.masthead p strong { color: #fff; }
.masthead em { color: #aebfd9; }
.masthead a { color: #dbe6f6; }
.masthead code { color: #e8eef8; background: rgba(255,255,255,.10); padding: 1px 4px; border-radius: 3px; }
.controls { display: flex; gap: 8px; margin: 0 0 16px; flex-wrap: wrap; }
.controls button {
  font-family: inherit; font-size: .78rem; letter-spacing: .04em;
  text-transform: uppercase; background: #fff; color: var(--navy);
  border: 1px solid var(--navy-line); border-radius: 6px;
  padding: 7px 12px; cursor: pointer;
}
nav.toc {
  background: var(--card); border: 1px solid var(--rule); border-radius: 9px;
  padding: 12px 16px 14px; margin-bottom: 16px;
}
nav.toc h2 {
  margin: 0 0 8px; font-size: .74rem; letter-spacing: .09em;
  text-transform: uppercase; color: var(--muted); font-family: inherit;
}
nav.toc ol { margin: 0; padding-left: 20px; }
nav.toc li { margin: 3px 0; }
nav.toc a { color: var(--navy); text-decoration: none; border-bottom: 1px solid var(--rule); }
nav.toc a:hover { border-bottom-color: var(--accent); }
details.section {
  background: var(--card); border: 1px solid var(--rule);
  border-radius: 9px; margin-bottom: 12px; overflow: hidden;
  scroll-margin-top: 8px;
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
.section-body ul, .section-body ol { margin: 8px 0; padding-left: 20px; }
.section-body li { margin: 3px 0; }
.section-body blockquote {
  margin: 10px 0; padding: 2px 14px; border-left: 3px solid var(--accent);
  color: var(--muted);
}
.section-body code {
  font-family: 'SF Mono', ui-monospace, 'Menlo', monospace; font-size: .82em;
  background: #f1eee6; padding: 1px 4px; border-radius: 3px;
}
.section-body pre { background: #f1eee6; padding: 10px 12px; border-radius: 6px; overflow-x: auto; }
.section-body pre code { background: none; padding: 0; }
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
figure.fig {
  margin: 18px 0; padding: 12px 10px 8px; background: #fff;
  border: 1px solid var(--rule); border-radius: 7px;
}
figure.fig svg { display: block; max-width: 100%; height: auto; }
figure.fig img { display: block; max-width: 100%; height: auto; }
figure.fig figcaption {
  margin-top: 8px; font-size: .74rem; line-height: 1.45; color: var(--muted);
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
}
footer { text-align: center; color: var(--muted); font-size: .75rem; margin-top: 24px; font-style: italic; }
@media print {
  .controls { display: none; }
  details.section { break-inside: auto; border: 0; }
  figure.fig { break-inside: avoid; }
}
@media (max-width: 480px) {
  body { font-size: 15px; }
  .section-body table { font-size: .66rem; }
  .masthead h1 { font-size: 1.3rem; }
}
"""

JS = """
document.querySelectorAll('.section-body table').forEach(function (t) {
  if (t.parentElement && t.parentElement.classList.contains('tablewrap')) return;
  var w = document.createElement('div'); w.className = 'tablewrap';
  t.parentNode.insertBefore(w, t); w.appendChild(t);
});
function setAll(open) {
  document.querySelectorAll('details.section').forEach(function (d) { d.open = open; });
}
document.getElementById('expandAll').addEventListener('click', function () { setAll(true); });
document.getElementById('collapseAll').addEventListener('click', function () { setAll(false); });
// A table-of-contents link into a collapsed accordion has to open it first,
// or the browser scrolls to a closed strip and nothing appears to happen.
function openTarget() {
  var id = decodeURIComponent(location.hash.slice(1));
  if (!id) return;
  var el = document.getElementById(id);
  while (el) {
    if (el.tagName === 'DETAILS') el.open = true;
    el = el.parentElement;
  }
  var t = document.getElementById(id);
  if (t) t.scrollIntoView();
}
window.addEventListener('hashchange', openTarget);
openTarget();
"""


def build(md_path: Path) -> tuple[str, list[str]]:
    text = md_path.read_text(encoding="utf-8")
    head_lines, body_lines = split_masthead(text)
    if not head_lines:  # no --- rule: the title line alone is the masthead
        head_lines, body_lines = body_lines[:1], body_lines[1:]

    title = next((l[2:].strip() for l in head_lines + body_lines
                  if l.startswith("# ")), md_path.stem)

    level = split_level(body_lines)
    pre_lines, secs = sections(body_lines, level)

    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])

    def render(t):
        md.reset()
        return md.convert(t)

    report: list[str] = []

    def block(t):
        return embed_figures(render(t), md_path, report)

    if "\n".join(pre_lines).strip():
        secs.insert(0, ("Front matter", "\n".join(pre_lines)))

    toc, accordions = [], []
    for i, (header, body) in enumerate(secs, start=1):
        aid = anchor(i, header)
        toc.append('<li><a href="#%s">%s</a></li>' % (aid, htmllib.escape(header)))
        accordions.append("""
    <details class="section" id="%s"%s>
      <summary class="section-head">
        <span class="section-title">%s</span>
        <span class="chev" aria-hidden="true"></span>
      </summary>
      <div class="section-body">
%s
      </div>
    </details>""" % (aid, " open" if i == 1 else "", htmllib.escape(header), block(body)))

    toc_html = ""
    if len(secs) > 1:
        toc_html = ('<nav class="toc"><h2>Contents</h2><ol>%s</ol></nav>'
                    % "".join(toc))

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<style>%s</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
%s
  </div>

  <div class="controls">
    <button id="expandAll">Expand all</button>
    <button id="collapseAll">Collapse all</button>
  </div>

  %s
%s

  <footer>Built from %s by tools/build_paper_html.py &mdash; the Markdown is canonical</footer>
</div>

<script>%s</script>
</body>
</html>
""" % (htmllib.escape(title), CSS, block("\n".join(head_lines)), toc_html,
       "\n".join(accordions), md_path.relative_to(ROOT).as_posix(), JS)
    return html, report


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    paths = [Path(a) for a in argv] or sorted(
        p for p in PAPERS.glob("*-whitepaper.md"))
    OUT.mkdir(parents=True, exist_ok=True)
    bad = 0
    for p in paths:
        p = p if p.is_absolute() else (ROOT / p)
        html, report = build(p)
        dest = OUT / (p.stem + ".html")
        dest.write_text(html, encoding="utf-8")
        nfig = html.count('<figure class="fig">')
        note = ("  " + "; ".join(report)) if report else ""
        print("%-46s %7.0f KB  %2d figures%s"
              % (dest.relative_to(ROOT).as_posix(), len(html) / 1024, nfig, note))
        bad += len(report)
    if bad:
        print("\n%d unresolved figure reference(s)" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

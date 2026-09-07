# Built HTML editions

**This directory is output. Do not edit anything in it, and never upload a
file into it.** Every `.html` here is generated from the paper's Markdown by
`tools/build_paper_html.py`:

```
make html          # rebuild all of them
python tools/build_paper_html.py docs/whitepapers/<slug>-whitepaper.md
```

One file per roster paper, named for its source: `<slug>-whitepaper.html`.
Figures are embedded inline, so an edition is a single self-contained file.

**The `.md` under `docs/whitepapers/` is canonical for everything** — text,
tables, and figure references alike. Figures are files under `docs/figures/`.
There is no longer a paper whose content lives only in its HTML; that rule was
retired when the figures came out of the HTML and into the repository, and
`CLAUDE.md` carries the durable statement of what replaced it.

`make library-check` warns when an edition here is older than the `.md` it was
built from — the signal to run `make html` again.

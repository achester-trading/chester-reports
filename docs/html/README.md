# Built HTML editions

The six papers that carry computed figures, plus the library guide, are
**canonical for reading in HTML** — the figures, the rendered tables and the
anchor navigation live only there, and the `.md` carries placeholders. The
canonical list is in `CLAUDE.md` and mirrored in the library guide:

| | File |
|---|---|
| V | `currencies-whitepaper.html` |
| XIII | `dealers-hand-whitepaper.html` |
| XIV | `technical-indicators-whitepaper.html` |
| XXII | `options-expression-whitepaper.html` |
| XXIII | `evidence-inference-whitepaper.html` |
| XXIV | `earnings-whitepaper.html` |

One file per paper, named for its `.md`: `<slug>-whitepaper.html`.

**Regenerate from the `.md`; never edit the HTML and never re-upload it over a
newer `.md`.** An HTML that disagrees with its `.md` is stale, not a second
opinion. `make library-check` warns when one of these is missing — a warning,
not a failure, because the editions are produced by hand today.

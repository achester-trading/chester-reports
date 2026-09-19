# Figures — evidence-inference

Delivered in the 19 September 2026 docs batch. **These are assets, not yet
wired into the paper** — `evidence-inference-whitepaper.md` still carries its
five `*[Figure N — computed figure; not yet drawn]*` placeholders, and it keeps
them until the numbering below is settled.

**Why they are not wired in.** The artwork labels itself `A1 A2 A3 A5 A6` — six
numbers in its own scheme with **A4 never drawn** — while the paper has five
placeholders numbered 1 to 5. Five files and five placeholders invite the
ordinal mapping the renderer rule prescribes (first file to first placeholder,
and so on), but that mapping puts a figure captioned "Figure 4" under artwork
that visibly reads "Figure A5", and "Figure 5" under one that reads "Figure A6".
Mapping by number instead leaves the paper's Figure 4 undrawn and A6 unused.
Neither is obviously right, and both change what a reader sees, so the choice
belongs to the operator rather than to whoever committed the files.

Filenames preserve the artwork's own numbering, so `fig-04.svg` is absent by
design rather than lost. `check_library.py` is unaffected: it requires the
paper's *Figure N* references to run from 1 without gaps (they do — the
placeholders are 1 to 5) and every image *link* to resolve (there are none yet).

| # | Self-label | Caption | File |
|---|---|---|---|
| 1 | Figure A1 | The interval on a 0.2R edge narrows slowly — a year of trading cannot exclude zero. | [`fig-01.svg`](fig-01.svg) |
| 2 | Figure A2 | A Sharpe of 1.0 measured over one year is indistinguishable from zero. | [`fig-02.svg`](fig-02.svg) |
| 3 | Figure A3 | What thirty observations do to three different priors. | [`fig-03.svg`](fig-03.svg) |
| — | *(A4)* | **Never drawn.** No artwork exists in any edition. | — |
| 5 | Figure A5 | Kelly shrinks fast when the edge is uncertain — the doctrine sizes below the quarter-Kelly line. | [`fig-05.svg`](fig-05.svg) |
| 6 | Figure A6 | Edge decay begins at week 40 and is not distinguishable from noise until about week 60. | [`fig-06.svg`](fig-06.svg) |

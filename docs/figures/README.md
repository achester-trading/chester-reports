# Figures

One directory per paper, named for the paper's slug. Files are `fig-NN.svg`
(or `.png` where the source was a raster), and each directory's `index.md`
maps figure number → caption → file.

These were lifted out of the pre-audit HTML editions in `docs/html/incoming/`,
which were the only surviving copies of the artwork. They are now source: the
`.md` papers reference them with ordinary Markdown image links, and
`make html` embeds them into the built editions under `docs/html/`.

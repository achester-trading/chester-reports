# Fixtures for altdata/sources/farside.py

NOT CAPTURED. farside.co.uk answered the laptop with 403, through Cloudflare, on 17 Oct 2026, to both the project's User-Agent and a browser-like one. The fixtures follow the page's published shape, described in the order's Appendix A:

- one table, the first column a date ("17 Oct 2026");
- an issuer column per fund, then Total;
- a fee row, and the summary rows Total, Average, Maximum and Minimum;
- negatives in parentheses, and "-" for no figure.

The figures are synthetic, except 16 Oct's totals, which match the X digest of 17 Oct: BTC -82.4, ETH -69.7, IBIT -71.8, FBTC -10.6. `btc_changed.html` adds a column, for the column-change detector.

The box's first dry run shows the real header, and the detector refuses it if config's lists differ.

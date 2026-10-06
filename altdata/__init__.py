"""altdata — shared data ingestion package.

Provides:
- config: registries (FRED series, etc.)
- store: normalized data store with provenance
- sources: per-source fetchers (FRED for v1; EIA / CFTC / etc. ship disabled)
"""

__version__ = "1.0.0"

# YFINANCE'S NUMPY NOISE (5 Oct 2026): yfinance's own utils call pd.Timedelta on a
# bare integer, which NumPy deprecates, and print the warning once per request --
# a dozen lines over every bars and price run. Filtered by the module it comes
# from, so the same warning raised by THIS repo's code still prints (CLAUDE.md:
# altdata/fx_charts.py has one to fix).
import warnings as _warnings                                    # noqa: E402

_warnings.filterwarnings("ignore", category=DeprecationWarning,
                         module=r"yfinance(\.|$)")

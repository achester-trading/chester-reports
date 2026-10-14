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
#
# WHY THE FILTER ALONE DID NOT TAKE (T2.6; 6 Oct on the box, thirteen lines from
# yfinance/utils.py:432 and :612 in `python -m altdata.bars backfill`). yfinance's
# own __init__ runs `warnings.filterwarnings('default', DeprecationWarning,
# module='^yfinance')`, which INSERTS AT THE FRONT of the filter list -- so the
# moment yfinance is imported, its "show once" rule sits ahead of ours and wins.
# A filter set here, before that import, can never hold. So every import of
# yfinance in this repo goes through import_yfinance(), which imports it and then
# puts our rule back in front; tools/validate_weekly_complete.py group L proves
# the silence in a fresh interpreter under that real import order, and refuses
# a bare `import yfinance` anywhere in the repo's code.
import warnings as _warnings                                    # noqa: E402

YF_MODULES = r"yfinance(\.|$)"


def quiet_yfinance() -> None:
    """Our filter on yfinance's DeprecationWarnings, at the FRONT of the list."""
    _warnings.filterwarnings("ignore", category=DeprecationWarning,
                             module=YF_MODULES)


def import_yfinance():
    """`import yfinance`, then quiet_yfinance() -- the one way this repo imports
    it. Raises ImportError exactly as the bare import would."""
    import yfinance                                             # noqa: PLC0415
    quiet_yfinance()
    return yfinance


quiet_yfinance()

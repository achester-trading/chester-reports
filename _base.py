"""altdata — shared data ingestion package.

Provides:
- config: registries (FRED series, etc.)
- store: normalized data store with provenance
- sources: per-source fetchers (FRED for v1; EIA / CFTC / etc. ship disabled)
"""

__version__ = "1.0.0"

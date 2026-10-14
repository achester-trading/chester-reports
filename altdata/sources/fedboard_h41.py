"""
The Fed's H.4.1 FIMA repo line -- a writer entry for altdata/feeds.py.

    python -m altdata.sources.fedboard_h41   # one pull, summary to stdout

The fetch and the parser live in altdata/sources/fedboard.py (the existing Fed
Board path, ST-B3-05); this module only gives the feed roster one writer per
module, with its KEYS literal so the freshness check can read them from source.
"""

from __future__ import annotations

from .fedboard import SOURCE_H41 as SOURCE                     # noqa: F401
from .fedboard import pull_h41 as pull                         # noqa: F401

KEYS = ["tic.fima_repo", "tic.fima_repo_weekavg"]


if __name__ == "__main__":
    import json
    import logging
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))

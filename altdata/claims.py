"""
The claims registry: cited figures the system may print and cannot compute.

    from altdata import claims
    claims.get("br.episode_1929_32")["value"]        # "-86%"
    claims.cite("pf.own_pension")                    # value + source + date
    claims.overdue()                                 # what needs rechecking

Audit row 6l; architecture 26.5, 31.1, 31.4. The file is `config/claims.yaml` and
its own header carries the reasoning; this module is the reader.

-----------------------------------------------------------------------------
WHY THERE IS A READER AT ALL, RATHER THAN A yaml.safe_load AT EACH CALL SITE
-----------------------------------------------------------------------------

Three things have to happen identically everywhere a claim is used, and each of
them is a place a call site would get it wrong:

  1. CITING RESOLVES AN ID. `cite()` returns the value WITH its source and its
     date attached, because a figure that arrives without them is a retyped
     figure by the time it reaches a page.

  2. A WARNING TRAVELS WITH THE FIGURE. 31.4 requires the three-denominator
     warning verbatim wherever the participant map is cited. Attaching it here
     means a report cannot print a Table A share without it.

  3. AN UNKNOWN ID IS AN ERROR, NOT AN EMPTY STRING. A missing claim that
     rendered as "" would put a sentence with a hole in it on a page, and the
     hole would be invisible in the one place it matters.

`overdue()` is the heartbeat's question. It never raises and never fails a run:
an ownership share past its review date is a figure to recheck, not a broken
pipeline, and an alarm that cannot be cleared by anything the pipeline does is an
alarm the reader learns to ignore.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
CLAIMS_PATH = REPO / "config" / "claims.yaml"

# The five fields the order requires of every claim. Checked by
# tools/validate_claims.py rather than trusted.
REQUIRED_FIELDS = ("id", "value", "source", "date", "review_date")

STATUSES = ("current", "stale", "superseded", "withdrawn")

_CACHE: Optional[dict] = None


class UnknownClaimError(KeyError):
    """A citation named an id the registry does not carry."""


def load(path: Optional[Path] = None, reload: bool = False) -> dict:
    """The parsed registry: {version, defaults, warnings, claims}."""
    global _CACHE
    if _CACHE is not None and not reload and path is None:
        return _CACHE
    import yaml                                                # noqa: PLC0415
    with (path or CLAIMS_PATH).open(encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}
    out = {
        "version": data.get("version"),
        "defaults": data.get("defaults") or {},
        "warnings": data.get("warnings") or {},
        "claims": {},
    }
    for cid, body in (data.get("claims") or {}).items():
        if not isinstance(body, dict):
            continue
        entry = dict(body)
        entry["id"] = cid
        entry.setdefault("status", (out["defaults"] or {}).get("status",
                                                               "current"))
        out["claims"][cid] = entry
    if path is None:
        _CACHE = out
    return out


def all_claims(path: Optional[Path] = None) -> dict:
    return load(path)["claims"]


def get(claim_id: str, path: Optional[Path] = None) -> dict:
    claims = all_claims(path)
    if claim_id not in claims:
        near = sorted(c for c in claims if c.split(".")[0]
                      == str(claim_id).split(".")[0])[:5]
        raise UnknownClaimError(
            f"no claim {claim_id!r} in {CLAIMS_PATH.name}. A report cites a claim "
            f"by id and never by retyping the figure, so an unknown id is an error "
            f"rather than an empty string"
            + (f"; did you mean one of {near}?" if near else ""))
    return claims[claim_id]


def warning_texts(claim: dict, path: Optional[Path] = None) -> list[str]:
    """The verbatim standing warnings attached to a claim."""
    decls = load(path)["warnings"]
    out = []
    for name in claim.get("warnings") or []:
        w = decls.get(name) or {}
        text = str(w.get("text") or "").strip()
        if text:
            out.append(text)
    return out


def cite(claim_id: str, path: Optional[Path] = None) -> dict:
    """The value WITH its provenance and its warnings -- what a report prints.

    Returns a dict rather than a string on purpose: a caller that wanted only the
    number would have to drop the source and the date to get one, which is the
    retyping this registry exists to prevent.
    """
    c = get(claim_id, path)
    return {
        "id": claim_id,
        "value": c.get("value"),
        "unit": c.get("unit"),
        "source": c.get("source"),
        "source_class": c.get("source_class"),
        "as_of": str(c.get("date")),
        "review_date": str(c.get("review_date")),
        "status": c.get("status"),
        "warnings": warning_texts(c, path),
        "detail": c.get("detail"),
    }


def _as_date(v: Any) -> Optional[dt.date]:
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return None


def overdue(as_of: Optional[dt.date] = None,
            path: Optional[Path] = None) -> list[dict]:
    """Claims past their review date. A WARNING, never a failure.

    Withdrawn and superseded claims are excluded: a claim kept only so an old
    citation still resolves does not need rechecking, and alarming on it would be
    asking for work that cannot be done.
    """
    today = as_of or dt.date.today()
    out = []
    for cid, c in sorted(all_claims(path).items()):
        if c.get("status") in ("withdrawn", "superseded"):
            continue
        rd = _as_date(c.get("review_date"))
        if rd is None or rd >= today:
            continue
        out.append({"id": cid, "review_date": rd.isoformat(),
                    "days_overdue": (today - rd).days,
                    "source": c.get("source"), "value": c.get("value")})
    return sorted(out, key=lambda r: -r["days_overdue"])


def summary(path: Optional[Path] = None) -> dict:
    claims = all_claims(path)
    by_prefix: dict[str, int] = {}
    for cid in claims:
        by_prefix[cid.split(".")[0]] = by_prefix.get(cid.split(".")[0], 0) + 1
    return {"version": load(path)["version"], "claims": len(claims),
            "by_prefix": by_prefix, "overdue": len(overdue(path=path)),
            "warnings": sorted(load(path)["warnings"])}


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="The claims registry.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    sub.add_parser("list")
    sub.add_parser("overdue")
    c = sub.add_parser("cite")
    c.add_argument("id")
    a = p.parse_args(argv)
    if a.cmd == "summary":
        print(json.dumps(summary(), indent=2, sort_keys=True))
    elif a.cmd == "list":
        for cid, c in sorted(all_claims().items()):
            print(f"{cid:<34} {str(c.get('value'))[:60]}")
    elif a.cmd == "overdue":
        rows = overdue()
        for r in rows:
            print(f"{r['id']:<34} review {r['review_date']} "
                  f"({r['days_overdue']}d overdue)")
        print(f"{len(rows)} claim(s) overdue")
    else:
        print(json.dumps(cite(a.id), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))

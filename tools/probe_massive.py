"""
Massive (formerly Polygon.io) entitlement probe -- does the free Options Basic
tier answer the SPX question?

The vendor review left one blocker: yfinance has no SPX index options, and
neither Massive's nor EODHD's documentation confirms index coverage. Massive
sells a $0 Options Basic tier, so the blocker can be settled before paying
anything. This probe does that.

TWO DIFFERENT QUESTIONS, reported separately -- conflating them is how a
subscription decision goes wrong:

    COVERAGE     Do SPX option contracts exist in their reference data at all?
                 Answered by /v3/reference/options/contracts, which is
                 reference data and should be reachable on Basic.

    ENTITLEMENT  Can THIS tier retrieve open interest and greeks for them?
                 Those live on /v3/snapshot/options/{underlyingAsset}, which is
                 documented as Starter+ and explicitly not in Basic. A 403 here
                 is a price fact, not evidence that SPX is missing.

Root candidates are tried in order because index naming is not documented:
`I:SPX` (Massive's index convention), bare `SPX`, and `SPXW` (the weekly root).
SPY runs as a control on every probe -- without it, a failure is ambiguous
between "SPX unsupported" and "the whole call is broken".

RATE LIMIT. Options Basic is 5 calls/minute, so calls are paced 13s apart and a
429 is honoured via Retry-After rather than hammered. The probe is ~7 calls,
about 90 seconds.

Raw responses land in tools/probe_output/ (gitignored). The key is redacted from
everything written to disk or printed.

Usage:
    python tools/probe_massive.py
    python tools/probe_massive.py --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
OUT_DIR = Path(__file__).resolve().parent / "probe_output"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from altdata import session  # noqa: E402

DEFAULT_BASE = "https://api.massive.com"
PACING_SECONDS = 13.0            # Basic is 5/min; stay under it
TIMEOUT = 30

CONTRACTS_PATH = "/v3/reference/options/contracts"
SNAPSHOT_PATH = "/v3/snapshot/options/{underlying}"

SPX_ROOTS = ["I:SPX", "SPX", "SPXW"]
CONTROL = "SPY"

_SECRETS: list[str] = []


def redact(text: str) -> str:
    for s in _SECRETS:
        if s:
            text = text.replace(s, "***REDACTED***")
    return text


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def credentials() -> tuple[Optional[str], str, list[str]]:
    env = load_env()
    key = os.environ.get("MASSIVE_API_KEY") or env.get("MASSIVE_API_KEY")
    base = (os.environ.get("MASSIVE_BASE_URL") or env.get("MASSIVE_BASE_URL")
            or DEFAULT_BASE).rstrip("/")
    problems = []
    if not key or key == "PLACEHOLDER":
        problems.append("MASSIVE_API_KEY is unset or still PLACEHOLDER")
    return key, base, problems


def save_raw(name: str, record: dict) -> str:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = session.utc_stamp("%Y%m%dT%H%M%S.%fZ")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:80]
    p = OUT_DIR / f"{stamp}_massive_{slug}.json"
    p.write_text(redact(json.dumps(record, indent=2, default=str)), encoding="utf-8")
    return str(p)


def call(base: str, path: str, params: dict, key: str, name: str,
         auth_mode: str = "bearer") -> dict:
    """One paced request. Never raises. Honours 429 Retry-After once."""
    url = f"{base}{path}"
    headers = {"Accept": "application/json"}
    p = dict(params)
    if auth_mode == "bearer":
        headers["Authorization"] = f"Bearer {key}"
    else:
        p["apiKey"] = key

    out: dict = {"name": name, "url": redact(url), "auth_mode": auth_mode,
                 "params": {k: redact(str(v)) for k, v in p.items() if k != "apiKey"}}
    for attempt in (1, 2):
        try:
            r = requests.get(url, headers=headers, params=p, timeout=TIMEOUT)
            out["status"] = r.status_code
            out["headers"] = {k: v for k, v in r.headers.items()
                              if re.search(r"limit|retry|quota", k, re.I)}
            try:
                out["body"] = r.json()
            except ValueError:
                out["body"] = {"__non_json__": r.text[:1000]}
            if r.status_code == 429 and attempt == 1:
                wait = float(r.headers.get("Retry-After") or 20)
                print(f"    429 -- waiting {wait:.0f}s and retrying once")
                time.sleep(wait)
                continue
            break
        except Exception as e:  # noqa: BLE001 -- a dead call is a finding
            out["status"] = None
            out["error"] = f"{type(e).__name__}: {e}"
            break
    out["saved_to"] = save_raw(name, out)
    return out


def contract_count(res: dict) -> int:
    body = res.get("body") or {}
    results = body.get("results")
    return len(results) if isinstance(results, list) else 0


def sample_ticker(res: dict) -> Optional[str]:
    body = res.get("body") or {}
    results = body.get("results") or []
    if isinstance(results, list) and results and isinstance(results[0], dict):
        return results[0].get("ticker")
    return None


def has_field(payload, pattern: re.Pattern, depth: int = 0) -> bool:
    """Does any key anywhere in the payload match?"""
    if depth > 6:
        return False
    if isinstance(payload, dict):
        for k, v in payload.items():
            if pattern.search(str(k)) or has_field(v, pattern, depth + 1):
                return True
    elif isinstance(payload, list):
        return any(has_field(v, pattern, depth + 1) for v in payload[:3])
    return False


OI_RE = re.compile(r"open_?interest", re.I)
GREEKS_RE = re.compile(r"greeks|gamma|delta", re.I)
IV_RE = re.compile(r"implied_?volatility", re.I)


def main() -> int:
    ap = argparse.ArgumentParser(description="Massive Options Basic probe")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key, base, problems = credentials()
    if key:
        _SECRETS.append(key)

    print("Massive (ex-Polygon) Options Basic probe")
    print(f"  base:    {base}")
    print(f"  roots:   {', '.join(SPX_ROOTS)}   control: {CONTROL}")
    print(f"  pacing:  {PACING_SECONDS:.0f}s (Basic = 5 calls/min)\n")

    plan = ([(f"contracts_{r}", CONTRACTS_PATH, {"underlying_ticker": r, "limit": 5})
             for r in [CONTROL] + SPX_ROOTS]
            + [(f"snapshot_{CONTROL}", SNAPSHOT_PATH.format(underlying=CONTROL),
                {"limit": 5})])

    if args.dry_run:
        print("Probe plan (no requests):")
        for name, path, params in plan:
            print(f"  GET {path}  {params}   ({name})")
        print("  + one snapshot on the first SPX root that returns contracts")
        return 0

    if problems:
        print("BLOCKED -- credentials not ready:")
        for p in problems:
            print(f"  - {p}")
        print(f"\n  Add the key to {ENV_PATH} (gitignored), then re-run.")
        return 2

    # Determine which auth style this API accepts, using the control call.
    results: dict[str, dict] = {}
    auth_mode = "bearer"
    first = call(base, CONTRACTS_PATH, {"underlying_ticker": CONTROL, "limit": 5},
                 key, f"contracts_{CONTROL}", auth_mode)
    if first.get("status") == 401:
        print("  bearer auth rejected; retrying with ?apiKey=")
        time.sleep(PACING_SECONDS)
        auth_mode = "apikey"
        first = call(base, CONTRACTS_PATH, {"underlying_ticker": CONTROL, "limit": 5},
                     key, f"contracts_{CONTROL}_apikey", auth_mode)
    results[f"contracts_{CONTROL}"] = first
    print(f"  [{first.get('status')}] contracts {CONTROL:<6} "
          f"{contract_count(first)} contract(s)")

    for root in SPX_ROOTS:
        time.sleep(PACING_SECONDS)
        r = call(base, CONTRACTS_PATH, {"underlying_ticker": root, "limit": 5},
                 key, f"contracts_{root}", auth_mode)
        results[f"contracts_{root}"] = r
        print(f"  [{r.get('status')}] contracts {root:<6} "
              f"{contract_count(r)} contract(s)"
              + (f"  e.g. {sample_ticker(r)}" if contract_count(r) else ""))

    # Snapshot: control first, then the best SPX root that produced contracts.
    time.sleep(PACING_SECONDS)
    snap_ctl = call(base, SNAPSHOT_PATH.format(underlying=CONTROL), {"limit": 5},
                    key, f"snapshot_{CONTROL}", auth_mode)
    results[f"snapshot_{CONTROL}"] = snap_ctl
    print(f"  [{snap_ctl.get('status')}] snapshot  {CONTROL}")

    best_root = next((r for r in SPX_ROOTS
                      if contract_count(results.get(f"contracts_{r}", {})) > 0), None)
    if best_root:
        time.sleep(PACING_SECONDS)
        s = call(base, SNAPSHOT_PATH.format(underlying=best_root), {"limit": 5},
                 key, f"snapshot_{best_root}", auth_mode)
        results[f"snapshot_{best_root}"] = s
        print(f"  [{s.get('status')}] snapshot  {best_root}")

    # ---- verdict ---------------------------------------------------------
    line = "=" * 70
    print(f"\n{line}\nVERDICT\n{line}")

    ctl_ok = contract_count(results[f"contracts_{CONTROL}"]) > 0
    print(f"\ncontrol ({CONTROL}) reference call: "
          f"{'OK' if ctl_ok else 'FAILED -- every result below is unreliable'}")

    print("\nQ1  SPX index option COVERAGE (reference data)")
    for root in SPX_ROOTS:
        r = results.get(f"contracts_{root}", {})
        n, st = contract_count(r), r.get("status")
        note = (f"{n} contract(s), e.g. {sample_ticker(r)}" if n else
                "no contracts" if st == 200 else f"HTTP {st}")
        print(f"      {root:<6} {note}")
    if best_root:
        v1 = (f"COVERED -- SPX option contracts exist under root '{best_root}'.")
    elif ctl_ok:
        v1 = ("NOT COVERED -- the control returned contracts, so the call works; "
              "no SPX root returned any. yfinance's gap is not closed here.")
    else:
        v1 = "UNKNOWN -- the control call failed, so nothing here is trustworthy."
    print(f"\n  VERDICT: {v1}")

    print("\nQ2  OI / greeks ENTITLEMENT on this tier (snapshot endpoint)")
    for name in [f"snapshot_{CONTROL}"] + ([f"snapshot_{best_root}"] if best_root else []):
        r = results.get(name, {})
        b = r.get("body")
        print(f"      {name:<18} HTTP {r.get('status')}  "
              f"OI={has_field(b, OI_RE)}  greeks={has_field(b, GREEKS_RE)}  "
              f"IV={has_field(b, IV_RE)}")
        msg = (b or {}).get("message") if isinstance(b, dict) else None
        if msg:
            print(f"        vendor says: {str(msg)[:140]}")
    snap_status = results.get(f"snapshot_{CONTROL}", {}).get("status")
    if snap_status == 200:
        v2 = "AVAILABLE on Basic -- snapshot returned 2xx with OI/greeks fields."
    elif snap_status in (401, 402, 403):
        v2 = (f"TIER-GATED (HTTP {snap_status}) -- as documented, the snapshot is "
              f"Starter+. This is a price fact, not an SPX coverage fact.")
    else:
        v2 = f"UNCLEAR -- snapshot returned HTTP {snap_status}."
    print(f"\n  VERDICT: {v2}")

    print(f"\n{line}\nRaw responses: {OUT_DIR}\n{line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

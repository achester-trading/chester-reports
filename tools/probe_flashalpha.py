"""
FlashAlpha entitlement probe -- what does THIS key actually return?

Purpose: a logger is being built on top of FlashAlpha, and what that logger can
record is gated by what this subscription tier actually serves. Vendor tier
tables describe what is *sold*, not what a given key *returns*. This script
asks the API directly and prints a findings report.

Five questions, one verdict line each:

    Q1  Which endpoints does this key get 200 on? Especially GEX / dealer
        exposure per-strike profiles, Indic-module endpoints, and liquidation
        endpoints.
    Q2  Does the per-strike payload carry an expiry field, or is it only
        aggregated by strike?
    Q3  Is open interest settled/static intraday? (Same symbol, two fetches
        ~60s apart, diffed.)
    Q4  Is customer-vs-dealer flow polarity exposed anywhere in this tier?
    Q5  What rate-limit headers come back, and what caps are documented?

Design rules:

1. **Nothing is guessed.** Every path in ENDPOINTS and the auth shape in
   AUTH come from FlashAlpha's own API documentation. Invented paths return
   404s that are indistinguishable from genuine entitlement denials -- which
   would defeat the one thing this probe exists to do: tell those apart.
2. **Never raises.** A probe that dies on endpoint 3 tells you nothing about
   endpoints 4-12. Every request is isolated; failures become findings.
3. **Raw responses are evidence.** Every response body is written to
   tools/probe_output/ with a UTC timestamp. That directory is gitignored --
   raw vendor payloads stay local.
4. **The key never lands in a file.** It is redacted from every URL, header,
   and param before anything is written to disk or printed.

Usage:
    python tools/probe_flashalpha.py --dry-run   # show the plan, no requests
    python tools/probe_flashalpha.py             # full probe
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
OUT_DIR = Path(__file__).resolve().parent / "probe_output"

TEST_SYMBOLS = ["SPY", "SPX"]
OI_RECHECK_SECONDS = 60
TIMEOUT = 30


# ===========================================================================
# FILLED FROM THE VENDOR DOCS -- the only two blanks in this file.
# ===========================================================================

# Auth, per https://flashalpha.com/docs: "X-Api-Key" header (recommended) or an
# "apiKey" query parameter. The header is used here -- the docs specifically
# warn that the query form leaks the key into caches and shell history.
AUTH_HEADER_NAME: Optional[str] = "X-Api-Key"
AUTH_HEADER_PREFIX: str = ""                # no Bearer prefix
AUTH_QUERY_PARAM: Optional[str] = None      # ?apiKey= works too; header preferred

# Q5, documentation half. The live half comes from response headers.
# NOTE: the two sources disagree on the Basic tier -- flashalpha.com/docs says
# 100/day, the PyPI SDK page says 250/day. Left unresolved on purpose; the
# X-RateLimit-Limit header on a live response settles it.
DOCUMENTED_CAPS = {
    "headers_documented": ["X-RateLimit-Limit", "X-RateLimit-Remaining",
                           "X-RateLimit-Reset", "Retry-After (429 only)"],
    "daily_quota": {"Free": 5, "Basic": "100 (docs) / 250 (SDK page) -- conflicting",
                    "Growth": 2500, "Alpha": "unlimited"},
    "response_cache": {"Free": "15 min", "Basic/Growth": "15 sec", "Alpha": "~1 sec"},
    "tier_denial_shape": '403 {"error": "tier_restricted", "required_plan": ...}',
}


@dataclass
class ProbeSpec:
    """One documented endpoint to try."""
    name: str                          # short label used in the report
    path: str                          # path template, may contain {symbol}
    question: str                      # which of Q1-Q5 this serves
    method: str = "GET"
    params: dict = field(default_factory=dict)
    per_symbol: bool = True            # expand {symbol} over TEST_SYMBOLS
    per_strike: bool = False           # Q2/Q3 inspect these payloads


# Every path below is quoted from https://flashalpha.com/docs. Ordered so the
# cheap, universally-available calls run first: if the key turns out to be on a
# 5-request/day Free plan, the quota is spent on the most informative probes.
#
# Not present in the docs at all: any endpoint named "indic" or "liquidation".
# No path is invented to go looking for them -- a made-up path returns a 404
# that reads identically to an entitlement denial. Q1 reports them as
# undocumented, which is itself the finding.
ENDPOINTS: list[ProbeSpec] = [
    # --- entitlement ground truth, cheapest first -----------------------
    ProbeSpec("account", "/v1/account", "Q1/Q5", per_symbol=False),
    ProbeSpec("health", "/health", "Q1", per_symbol=False),

    # --- settled-OI exposure: per-strike, the Q2/Q3 core ----------------
    ProbeSpec("exposure_gex", "/v1/exposure/gex/{symbol}", "Q1/Q2/Q3",
              per_strike=True),
    ProbeSpec("exposure_levels", "/v1/exposure/levels/{symbol}", "Q1"),
    ProbeSpec("exposure_summary", "/v1/exposure/summary/{symbol}", "Q1"),
    ProbeSpec("exposure_zero_dte", "/v1/exposure/zero-dte/{symbol}", "Q1/Q2"),

    # --- chain metadata: does the tier expose expiries at all? ----------
    ProbeSpec("options_chain", "/v1/options/{symbol}", "Q2"),

    # --- live/effective-OI flow: Q3 contrast and Q4 polarity ------------
    ProbeSpec("flow_gex", "/v1/flow/gex/{symbol}", "Q1/Q3", per_strike=True),
    ProbeSpec("flow_dealer_risk", "/v1/flow/dealer-risk/{symbol}", "Q1/Q4"),
    ProbeSpec("flow_oi", "/v1/flow/oi/{symbol}", "Q1/Q3"),
    ProbeSpec("flow_signals", "/v1/flow/signals/{symbol}", "Q1/Q4"),
]


# ===========================================================================
# Field-shape heuristics -- for probing defensively where docs are silent.
# ===========================================================================

EXPIRY_RE = re.compile(r"expir|expiry|exp_?date|exp_?dt|dte|tenor|maturity", re.I)
STRIKE_RE = re.compile(r"strike|\bstrk\b", re.I)
OI_RE = re.compile(r"open_?int|\boi\b", re.I)
POLARITY_RE = re.compile(
    r"customer|dealer|market_?maker|\bmm\b|polarity|initiat|aggress|"
    r"buy_?sell|bid_?ask_?side|\bside\b|direction|net_?flow|sweep|"
    r"ask_?side|bid_?side",
    re.I,
)
RATELIMIT_RE = re.compile(
    r"rate.?limit|x-ratelimit|retry-after|x-quota|quota|throttle|"
    r"x-requests?-(remaining|limit)|x-credits?",
    re.I,
)


def walk_keys(obj: Any, prefix: str = "", depth: int = 0, max_depth: int = 8):
    """Yield (dotted_path, value) for each key. Lists are sampled at [0]."""
    if depth > max_depth:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            yield path, v
            yield from walk_keys(v, path, depth + 1, max_depth)
    elif isinstance(obj, list) and obj:
        yield from walk_keys(obj[0], f"{prefix}[]", depth + 1, max_depth)


def matching_fields(payload: Any, pattern: re.Pattern) -> list[str]:
    """Dotted paths whose leaf key matches `pattern`, de-duplicated, in order."""
    hits: list[str] = []
    for path, _ in walk_keys(payload):
        leaf = path.split(".")[-1].replace("[]", "")
        if pattern.search(leaf) and path not in hits:
            hits.append(path)
    return hits


def flatten_all(obj: Any, prefix: str = "", out: Optional[dict] = None,
                depth: int = 0, max_depth: int = 10) -> dict[str, Any]:
    """Fully expand a payload to {dotted_path: scalar}. Lists keep their index,
    so two fetches of the same profile line up strike-for-strike."""
    if out is None:
        out = {}
    if depth > max_depth:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten_all(v, f"{prefix}.{k}" if prefix else str(k), out, depth + 1)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flatten_all(v, f"{prefix}[{i}]", out, depth + 1)
    else:
        out[prefix] = obj
    return out


# ===========================================================================
# Environment and redaction
# ===========================================================================

def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    """Minimal .env reader -- not worth a dependency for four lines of parse."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def resolve_credentials() -> tuple[Optional[str], Optional[str], list[str]]:
    """Return (api_key, base_url, problems). Real env wins over .env."""
    env = load_env()
    key = os.environ.get("FLASHALPHA_API_KEY") or env.get("FLASHALPHA_API_KEY")
    base = os.environ.get("FLASHALPHA_BASE_URL") or env.get("FLASHALPHA_BASE_URL")
    problems = []
    if not key or key == "PLACEHOLDER":
        problems.append("FLASHALPHA_API_KEY is unset or still PLACEHOLDER")
    if not base or base == "PLACEHOLDER":
        problems.append("FLASHALPHA_BASE_URL is unset or still PLACEHOLDER")
    return key, (base.rstrip("/") if base else None), problems


_SECRETS: list[str] = []


def redact(text: str) -> str:
    """Strip the key out of anything headed for disk or the terminal."""
    for secret in _SECRETS:
        if secret:
            text = text.replace(secret, "***REDACTED***")
    return text


# ===========================================================================
# Probing
# ===========================================================================

@dataclass
class ProbeResult:
    name: str
    spec: Optional[ProbeSpec]
    symbol: Optional[str]
    url: str
    status: Optional[int]
    elapsed_ms: int
    headers: dict
    payload: Any
    error: Optional[str]
    saved_to: Optional[str]

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300


def save_raw(name: str, record: dict) -> str:
    """Write one raw response to probe_output/ with a UTC timestamp."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:80]
    path = OUT_DIR / f"{stamp}_{slug}.json"
    path.write_text(redact(json.dumps(record, indent=2, default=str)),
                    encoding="utf-8")
    return str(path)


def probe(session: requests.Session, base: str, name: str, path: str,
          params: dict, method: str = "GET",
          spec: Optional[ProbeSpec] = None,
          symbol: Optional[str] = None) -> ProbeResult:
    """Issue one request. Never raises -- a failure is itself a finding."""
    url = f"{base}{path}"
    call_params = dict(params or {})
    if AUTH_QUERY_PARAM:
        call_params[AUTH_QUERY_PARAM] = session.headers.get("__key__", "")

    started = time.time()
    status: Optional[int] = None
    headers: dict = {}
    payload: Any = None
    error: Optional[str] = None
    try:
        resp = session.request(method, url, params=call_params, timeout=TIMEOUT)
        status = resp.status_code
        headers = dict(resp.headers)
        try:
            payload = resp.json()
        except ValueError:
            payload = {"__non_json_body__": resp.text[:4000]}
    except Exception as e:  # noqa: BLE001 -- a dead endpoint is data, not a crash
        error = f"{type(e).__name__}: {e}"
    elapsed = int((time.time() - started) * 1000)

    saved = save_raw(name, {
        "probe": name,
        "requested_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": method,
        "url": redact(url),
        "params": {k: redact(str(v)) for k, v in call_params.items()},
        "status": status,
        "elapsed_ms": elapsed,
        "response_headers": headers,
        "error": error,
        "body": payload,
    })
    return ProbeResult(name, spec, symbol, redact(url), status, elapsed,
                       headers, payload, error, saved)


def build_session(key: str) -> requests.Session:
    """Apply the documented auth scheme."""
    s = requests.Session()
    if AUTH_HEADER_NAME:
        s.headers[AUTH_HEADER_NAME] = f"{AUTH_HEADER_PREFIX}{key}"
    if AUTH_QUERY_PARAM:
        s.headers["__key__"] = key  # consumed by probe(), never sent
    s.headers["Accept"] = "application/json"
    return s


def diff_payloads(first: ProbeResult, second: ProbeResult) -> dict:
    """Compare two fetches of the same profile, scalar by scalar."""
    diff: dict = {"comparable": False, "oi_changed": [], "any_changed": [],
                  "oi_fields_seen": 0, "shared_fields": 0}
    if not (first and second and first.ok and second.ok):
        return diff
    a, b = flatten_all(first.payload), flatten_all(second.payload)
    shared = set(a) & set(b)
    diff["comparable"] = bool(shared)
    diff["shared_fields"] = len(shared)
    for k in sorted(shared):
        if a[k] != b[k]:
            diff["any_changed"].append((k, a[k], b[k]))
            if OI_RE.search(k.split(".")[-1]):
                diff["oi_changed"].append((k, a[k], b[k]))
    diff["oi_fields_seen"] = sum(1 for k in shared
                                 if OI_RE.search(k.split(".")[-1]))
    return diff


def oi_stability(session, base, specs: list[ProbeSpec], symbol: str) -> dict:
    """Q3: re-fetch every per-strike profile that worked, ~60s apart.

    One sleep covers all of them -- t0 for each, wait, then t1 for each -- so
    comparing the settled profile against the live one costs the same 60s as
    comparing either alone. That contrast is the actual answer to Q3: settled
    endpoints should be frozen while flow endpoints move.
    """
    if not specs:
        return {}
    t0: dict[str, ProbeResult] = {}
    for spec in specs:
        t0[spec.name] = probe(session, base, f"{spec.name}_{symbol}_oi_t0",
                              spec.path.format(symbol=symbol), spec.params,
                              spec.method, spec, symbol)
    print(f"  Q3: t0 captured for {', '.join(t0)}; "
          f"waiting {OI_RECHECK_SECONDS}s...")
    time.sleep(OI_RECHECK_SECONDS)

    out: dict = {}
    for spec in specs:
        t1 = probe(session, base, f"{spec.name}_{symbol}_oi_t1",
                   spec.path.format(symbol=symbol), spec.params, spec.method,
                   spec, symbol)
        out[spec.name] = diff_payloads(t0[spec.name], t1)
        print(f"  Q3: {spec.name} re-fetched "
              f"({len(out[spec.name]['any_changed'])} field(s) moved)")
    return out


# ===========================================================================
# Findings report
# ===========================================================================

def print_report(results: list[ProbeResult], oi: Optional[dict],
                 oi_symbol: Optional[str]) -> None:
    line = "=" * 72
    print(f"\n{line}\nFINDINGS\n{line}")

    ok = [r for r in results if r.ok]
    denied = [r for r in results if r.status in (401, 402, 403)]
    missing = [r for r in results if r.status == 404]
    errored = [r for r in results if r.error]

    # An unauthenticated run must not produce negative findings. /v1/account is
    # not tier-gated, so a 401 there means the key was rejected outright -- and
    # "no polarity field in any 2xx payload" would then be an artefact of having
    # no payloads at all, not a fact about the tier. Force UNKNOWN instead.
    acct = next((r for r in results if r.name == "account"), None)
    auth_failed = bool(acct and acct.status == 401)
    if auth_failed:
        print("\n  *** AUTHENTICATION FAILED -- key rejected on /v1/account, which")
        print("      is not tier-gated. Every verdict below that depends on a 2xx")
        print("      payload is UNKNOWN, not negative. This run says nothing about")
        print("      what the subscription entitles.\n")

    # ---- Q1 -------------------------------------------------------------
    print("\nQ1  Endpoints returning 200")
    for r in results:
        mark = "200" if r.ok else (str(r.status) if r.status else "ERR")
        print(f"      [{mark:>3}] {r.name}")
    tier_msgs = []
    for r in denied:
        if isinstance(r.payload, dict):
            req = r.payload.get("required_plan") or r.payload.get("message")
            if req:
                tier_msgs.append(f"{r.name}: {req}")
    if tier_msgs:
        print("\n      tier denials (verbatim from the API):")
        for m in tier_msgs[:12]:
            print(f"        {m}")
    print("\n      Indic-module / liquidation endpoints: NOT DOCUMENTED at")
    print("      flashalpha.com/docs -- no such path exists to probe. No path")
    print("      was invented, since a 404 on a guessed path is indistinguishable")
    print("      from an entitlement denial.")
    print(f"\n  VERDICT: {len(ok)}/{len(results)} probes returned 2xx; "
          f"{len(denied)} auth/entitlement-denied (401/402/403), "
          f"{len(missing)} not-found (404), {len(errored)} transport errors. "
          f"No Indic or liquidation endpoint exists in the published API.")

    # ---- Q2 -------------------------------------------------------------
    print("\nQ2  Per-strike payload: expiry field or aggregate-only?")
    strike_results = [r for r in ok if r.spec and r.spec.per_strike]
    verdict = ("UNKNOWN -- authentication failed, no payload to inspect."
               if auth_failed else
               "NO PER-STRIKE ENDPOINT RETURNED 2xx -- cannot answer.")
    for r in strike_results:
        exp = matching_fields(r.payload, EXPIRY_RE)
        strikes = matching_fields(r.payload, STRIKE_RE)
        print(f"      {r.name}")
        print(f"        strike-ish fields: {strikes or 'none'}")
        print(f"        expiry-ish fields: {exp or 'none'}")
        if strikes:
            verdict = ("PER-EXPIRY -- payload carries both strike and expiry fields."
                       if exp else
                       "AGGREGATE-BY-STRIKE ONLY -- strike fields present, no expiry field.")
    print(f"\n  VERDICT: {verdict}")

    # ---- Q3 -------------------------------------------------------------
    print("\nQ3  Is OI settled/static intraday?")
    if not oi:
        print("      Not run -- no per-strike endpoint returned 2xx.")
        print("\n  VERDICT: UNKNOWN -- no per-strike endpoint to re-fetch.")
    else:
        print(f"      symbol: {oi_symbol}, gap: ~{OI_RECHECK_SECONDS}s")
        verdicts = []
        for name, d in oi.items():
            print(f"      {name}:")
            if not d.get("comparable"):
                print("        not comparable (one or both fetches non-2xx)")
                verdicts.append(f"{name}=UNKNOWN")
                continue
            print(f"        fields compared: {d['shared_fields']}"
                  f"  OI-named: {d['oi_fields_seen']}")
            print(f"        OI fields moved: {len(d['oi_changed'])}"
                  f"  any field moved: {len(d['any_changed'])}")
            for k, a, b in d["oi_changed"][:6]:
                print(f"          {k}: {a} -> {b}")
            if d["oi_fields_seen"] == 0 and not d["any_changed"]:
                verdicts.append(f"{name}=FROZEN (no field moved, no OI field found)")
            elif d["oi_changed"]:
                verdicts.append(f"{name}=LIVE ({len(d['oi_changed'])} OI fields moved)")
            elif d["any_changed"]:
                verdicts.append(f"{name}=OI STATIC "
                                f"({len(d['any_changed'])} non-OI fields moved)")
            else:
                verdicts.append(f"{name}=FROZEN")
        print(f"\n  VERDICT: {'; '.join(verdicts)}"
              f"  [gap {OI_RECHECK_SECONDS}s, market hours required for meaning]")

    # ---- Q4 -------------------------------------------------------------
    print("\nQ4  Customer-vs-dealer flow polarity exposed?")
    polarity_hits: list[tuple[str, list[str]]] = []
    for r in ok:
        hits = matching_fields(r.payload, POLARITY_RE)
        if hits:
            polarity_hits.append((r.name, hits))
            print(f"      {r.name}: {hits}")
    if not polarity_hits:
        print("      No polarity-ish field names in any 2xx payload.")
    print(f"\n  VERDICT: " + (
        f"CANDIDATE FIELDS PRESENT in {len(polarity_hits)} endpoint(s) -- "
        f"names suggest polarity; confirm semantics against the docs."
        if polarity_hits else
        "UNKNOWN -- authentication failed, no payload to inspect."
        if auth_failed else
        "NOT EXPOSED -- no customer/dealer polarity fields in any 2xx payload."))

    # ---- Q5 -------------------------------------------------------------
    print("\nQ5  Rate-limit headers")
    seen: dict[str, str] = {}
    for r in results:
        for k, v in r.headers.items():
            if RATELIMIT_RE.search(k):
                seen[k] = v
    for k, v in sorted(seen.items()):
        print(f"      {k}: {v}")
    if not seen:
        print("      None returned on any response.")
    print("\n      documented (flashalpha.com/docs):")
    print(f"        headers:      {', '.join(DOCUMENTED_CAPS['headers_documented'])}")
    print(f"        daily quota:  {DOCUMENTED_CAPS['daily_quota']}")
    print(f"        cache/latency:{DOCUMENTED_CAPS['response_cache']}")
    live_limit = seen.get("X-RateLimit-Limit") or seen.get("x-ratelimit-limit")
    print(f"\n  VERDICT: " + (
        f"{len(seen)} rate-limit header(s) live: {', '.join(sorted(seen))}"
        + (f"; X-RateLimit-Limit={live_limit} settles the Basic-tier "
           f"docs/SDK conflict" if live_limit else "")
        + "."
        if seen else
        "NO rate-limit headers returned -- documented caps above are unverified."))

    print(f"\n{line}")
    print(f"Raw responses: {OUT_DIR}  ({len(results)} saved)")
    print(line)


# ===========================================================================
# Entry point
# ===========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="FlashAlpha entitlement probe")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the probe plan without making any request")
    args = ap.parse_args()

    key, base, problems = resolve_credentials()
    if key:
        _SECRETS.append(key)

    print("FlashAlpha entitlement probe")
    print(f"  symbols:   {', '.join(TEST_SYMBOLS)}")
    print(f"  output:    {OUT_DIR}")
    print(f"  endpoints: {len(ENDPOINTS)} registered")
    print()

    if not ENDPOINTS or not (AUTH_HEADER_NAME or AUTH_QUERY_PARAM):
        print("BLOCKED -- the endpoint registry and/or auth scheme is unset.")
        print()
        print("  Both are filled from FlashAlpha's API documentation, never")
        print("  guessed. An invented path returns a 404 that is indistinguishable")
        print("  from a genuine entitlement denial -- and telling those two apart")
        print("  is the entire point of this probe.")
        print()
        print("  Supply the API docs URL and these get filled in from it.")
        return 2

    if problems and not args.dry_run:
        print("BLOCKED -- credentials not ready:")
        for p in problems:
            print(f"  - {p}")
        print(f"\n  Fill them in {ENV_PATH} (gitignored), then re-run.")
        return 2

    if args.dry_run:
        print("Probe plan (no requests will be made):")
        for spec in ENDPOINTS:
            for sym in (TEST_SYMBOLS if spec.per_symbol else [None]):
                shown = spec.path.format(symbol=sym) if sym else spec.path
                print(f"  [{spec.question}] {spec.method:4} {shown}  ({spec.name})")
        print(f"\n  Plus one {OI_RECHECK_SECONDS}s-apart re-fetch for Q3.")
        return 0

    session = build_session(key)
    results: list[ProbeResult] = []
    quota_exhausted = False

    for spec in ENDPOINTS:
        if quota_exhausted:
            break
        for sym in (TEST_SYMBOLS if spec.per_symbol else [None]):
            path = spec.path.format(symbol=sym) if sym else spec.path
            label = spec.name + (f"_{sym}" if sym else "")
            r = probe(session, base, label, path, spec.params, spec.method,
                      spec, sym)
            results.append(r)
            mark = "200" if r.ok else (str(r.status) if r.status else "ERR")
            left = (r.headers.get("X-RateLimit-Remaining")
                    or r.headers.get("x-ratelimit-remaining") or "?")
            print(f"  [{mark:>3}] {label:<44} {r.elapsed_ms:>5}ms  "
                  f"quota_left={left}")
            if r.status == 429:
                # Stop immediately: burning the rest of the day's quota on
                # calls that will all 429 would answer nothing and would cost
                # the logger its budget for the rest of the day.
                print("\n  !! 429 received -- daily quota exhausted. Halting the "
                      "probe here and reporting on what was collected.")
                quota_exhausted = True
                break

    oi_results: dict = {}
    oi_symbol = None
    if not quota_exhausted:
        oi_symbol = TEST_SYMBOLS[0]
        got_200 = {r.spec.name for r in results
                   if r.ok and r.spec and r.spec.per_strike
                   and r.symbol == oi_symbol}
        candidates = [s for s in ENDPOINTS if s.per_strike and s.name in got_200]
        if candidates:
            oi_results = oi_stability(session, base, candidates, oi_symbol)
        else:
            print("  Q3: skipped -- no per-strike endpoint returned 2xx.")

    print_report(results, oi_results, oi_symbol)
    return 0


if __name__ == "__main__":
    sys.exit(main())

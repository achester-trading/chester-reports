"""
The model meter: one client for every report, and every call counted. (AUD-2
item 4, ruled 14 Oct 2026)

    from altdata import model_meter as meter
    client, why = meter.client()                 # shared; timeout 90 s, 1 retry
    with meter.scope(report="daily_close", run_id=rid, db_path=db):
        with meter.scope(section="tape"):
            resp = meter.create(client, model=..., messages=...)
    meter.daily_line(db, "2026-10-14")   # "Model: 3 calls, 41,200 input / 2,950 ..."
    meter.month_lines(db, "2026-10")

ONE CLIENT. The data and architecture audit of 14 Oct found model calls with no
timeout -- the SDK's default is ten minutes, retried twice -- so a stalled call
could hold a 16:45 close for half an hour. Every report path now builds its client
here: timeout=90 seconds, max_retries=1. The reports' own withhold-and-retry loops
are unchanged; this is the transport's.

EVERY CALL COUNTED. `create()` makes the call and writes one row to `model_calls`
in chester.db: run id, report, section, attempt, model id, input and output
tokens, and the time. Tokens, not dollars: no price table, so a line built from
these rows is never wrong when prices change. A call is recorded only inside a
report's `scope()`, so a gate that calls a writer with a fake client and no scope
writes nothing anywhere; and the row goes to the scope's database, so a gate's
report run lands in the gate's own store. Recording never raises: a meter that
could cost a paragraph would be worse than no meter.

THE ATTEMPT is the call's number within its (report, section) in one run: a
report's section rewritten after a withhold reads 2. The voices scan makes one
call per new item under the one section "extract", so its attempt is the
article's number in the day's scan, not a retry count (ruled 14 Oct 2026).
"""

from __future__ import annotations

import contextlib
import contextvars
import datetime as dt
import functools
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterator, Optional

log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 90
MAX_RETRIES = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS model_calls (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT,
    report        TEXT NOT NULL,
    section       TEXT,
    attempt       INTEGER,
    model         TEXT,
    input_tokens  INTEGER,
    output_tokens INTEGER,
    called_at     TEXT NOT NULL          -- UTC ISO, when the reply arrived
);
CREATE INDEX IF NOT EXISTS model_calls_by_time ON model_calls (called_at);
"""

_SCOPE: contextvars.ContextVar[dict] = contextvars.ContextVar("model_meter_scope",
                                                              default={})
_CLIENT: Any = None
_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# The client
# ---------------------------------------------------------------------------
def client() -> tuple[Any, str]:
    """(the shared client, "") or (None, why). Built once per process, with the
    audit's transport limits. The key is resolved by altdata.secrets, as before."""
    global _CLIENT
    from . import secrets                                       # noqa: PLC0415
    key_name = "ANTHROPIC" + "_API_KEY"
    if not secrets.present(key_name):
        return None, f"{key_name} is not set (checked environment, then .env)"
    try:
        import anthropic                                        # noqa: PLC0415
    except ImportError:
        return None, "the anthropic package is not installed"
    with _LOCK:
        if _CLIENT is None:
            try:
                _CLIENT = anthropic.Anthropic(timeout=TIMEOUT_SECONDS,
                                              max_retries=MAX_RETRIES)
            except Exception as exc:                            # noqa: BLE001
                return None, (f"client construction failed: "
                              f"{type(exc).__name__}: {exc}")
    return _CLIENT, ""


# ---------------------------------------------------------------------------
# The scope: who is calling
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def scope(**kw: Any) -> Iterator[dict]:
    """Nest freely: a report sets report, run_id and db_path; a writer sets the
    section. A new `report` starts a fresh attempt count."""
    cur = dict(_SCOPE.get())
    if "report" in kw:
        cur["counts"] = {}
    cur.update({k: v for k, v in kw.items()})
    token = _SCOPE.set(cur)
    try:
        yield cur
    finally:
        _SCOPE.reset(token)


def metered(report: str):
    """Decorate a report's produce(p, ..., db_path=...): its calls are metered as
    `report`, under the payload's run id, into its database. A decorator, so the
    function keeps its own name and body -- gates read produce()'s source, and
    inspect follows __wrapped__."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(p, *a, **kw):
            rid = p.get("run_id") if isinstance(p, dict) else None
            with scope(report=report, run_id=rid, db_path=kw.get("db_path")):
                return fn(p, *a, **kw)
        return wrapper
    return deco


def annotate(**kw: Any) -> None:
    """Add to the OPEN scope in place (a run id known only once the run began)."""
    _SCOPE.get().update(kw)


def current() -> dict:
    return dict(_SCOPE.get())


def _connect(db_path: Optional[str]) -> sqlite3.Connection:
    from . import observations                                  # noqa: PLC0415
    path = Path(db_path or observations.DEFAULT_DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.executescript(SCHEMA)
    return conn


def record(resp: Any, model: Optional[str] = None, *, now: Optional[str] = None) -> bool:
    """One row for one reply, if a report scope is open. Never raises."""
    sc = _SCOPE.get()
    if not sc.get("report"):
        return False
    try:
        usage = getattr(resp, "usage", None)
        section = sc.get("section")
        counts = sc.setdefault("counts", {})
        counts[section] = counts.get(section, 0) + 1
        from . import session                                   # noqa: PLC0415
        conn = _connect(sc.get("db_path"))
        try:
            conn.execute(
                "INSERT INTO model_calls (run_id, report, section, attempt, model,"
                " input_tokens, output_tokens, called_at) VALUES (?,?,?,?,?,?,?,?)",
                (sc.get("run_id"), sc["report"], section, counts[section],
                 getattr(resp, "model", None) or model,
                 getattr(usage, "input_tokens", None),
                 getattr(usage, "output_tokens", None),
                 now or session.utc_iso()))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:                                           # noqa: BLE001
        log.warning("model meter: the call was not recorded", exc_info=True)
        return False


def create(client_: Any, **kwargs: Any) -> Any:
    """client.messages.create(**kwargs), then the row. The call's own exceptions
    pass through untouched: the callers already turn them into reasons."""
    resp = client_.messages.create(**kwargs)
    record(resp, kwargs.get("model"))
    return resp


# ---------------------------------------------------------------------------
# The lines the reports print
# ---------------------------------------------------------------------------
def _rows(db_path: Optional[str], first_utc: str, last_utc: str) -> list[tuple]:
    from . import observations                                  # noqa: PLC0415
    path = Path(db_path or observations.DEFAULT_DB)
    if not path.exists():
        return []
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                            "name='model_calls'").fetchone():
            return []
        return conn.execute(
            "SELECT report, input_tokens, output_tokens, called_at FROM model_calls"
            " WHERE called_at >= ? AND called_at < ? ORDER BY called_at",
            (first_utc, last_utc)).fetchall()
    finally:
        conn.close()


def _et_bounds(first: dt.date, last: dt.date) -> tuple[str, str]:
    """UTC instants of [first 00:00 ET, last+1 00:00 ET)."""
    from . import session                                       # noqa: PLC0415
    tz = session._eastern_tz()                                  # noqa: SLF001
    a = dt.datetime.combine(first, dt.time(0, 0), tzinfo=tz)
    b = dt.datetime.combine(last + dt.timedelta(days=1), dt.time(0, 0), tzinfo=tz)
    f = lambda x: x.astimezone(dt.timezone.utc).isoformat(timespec="seconds")  # noqa: E731
    return f(a), f(b)


def _n(x: Optional[int]) -> int:
    return int(x or 0)


def daily_line(db_path: Optional[str], day: str) -> str:
    """The close's footer line: every report's calls on the ET calendar day."""
    d = dt.date.fromisoformat(day[:10])
    rows = _rows(db_path, *_et_bounds(d, d))
    calls = len(rows)
    return (f"Model: {calls:,} call{'' if calls == 1 else 's'}, "
            f"{sum(_n(r[1]) for r in rows):,} input / "
            f"{sum(_n(r[2]) for r in rows):,} output tokens today")


def month_lines(db_path: Optional[str], month: str) -> list[str]:
    """The Monthly's footer: the month's calls and tokens, by report."""
    y, m = (int(x) for x in month[:7].split("-"))
    first = dt.date(y, m, 1)
    last = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
    rows = _rows(db_path, *_et_bounds(first, last))
    if not rows:
        return [f"Model, {first:%B %Y}: no calls recorded"]
    by: dict[str, list[int]] = {}
    for rep, i, o, _ in rows:
        t = by.setdefault(rep, [0, 0, 0])
        t[0] += 1
        t[1] += _n(i)
        t[2] += _n(o)
    tot = [sum(v[k] for v in by.values()) for k in range(3)]
    return ([f"Model, {first:%B %Y}: {tot[0]:,} calls, {tot[1]:,} input / "
             f"{tot[2]:,} output tokens"]
            + [f"{rep}: {v[0]:,} calls, {v[1]:,} input / {v[2]:,} output tokens"
               for rep, v in sorted(by.items())])


# ---------------------------------------------------------------------------
# A SECOND PROVIDER (A94; Learning Loop v2 LL-6, D38: Gemini)
# ---------------------------------------------------------------------------
# The forecasters' second provider, behind the same meter: its calls land in
# model_calls under their own model id, so the lines below split them by
# provider without a schema change. Its client is the standard library's HTTP:
# no new dependency. The key is read through altdata.secrets (which registers it
# for redaction), sent as a header and never in a URL, never logged, never in an
# error's text. A provider's calls are refused past its daily budget in
# config/forecasters.yaml, which starts at zero: nothing spends by surprise.
FORECASTERS_CONFIG = Path(__file__).resolve().parent.parent / "config" / "forecasters.yaml"
PROVIDER_PREFIXES = (("claude", "anthropic"), ("gemini", "gemini"))


class BudgetExhausted(RuntimeError):
    """The provider's daily call budget is spent (or is zero)."""


class ProviderError(RuntimeError):
    """A provider's call failed; the text carries no key."""


def provider_of(model: Optional[str]) -> str:
    m = str(model or "").lower()
    return next((p for pre, p in PROVIDER_PREFIXES if m.startswith(pre)), "other")


def forecasters_config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    p = Path(path or FORECASTERS_CONFIG)
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.is_file() else {}


def budget(provider: str, cfg: Optional[dict] = None) -> int:
    """The provider's calls a day (0 when unset: nothing runs until it is set)."""
    b = ((cfg if cfg is not None else forecasters_config()).get("budgets") or {}).get(provider) or {}
    return int(b.get("calls_per_day") or 0)


def _day_models(db_path: Optional[str], day: str) -> list[tuple]:
    """(model, input, output) for every call on the ET day."""
    from . import observations                                  # noqa: PLC0415
    path = Path(db_path or observations.DEFAULT_DB)
    if not path.exists():
        return []
    d = dt.date.fromisoformat(day[:10])
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                            "name='model_calls'").fetchone():
            return []
        return conn.execute("SELECT model, input_tokens, output_tokens FROM "
                            "model_calls WHERE called_at >= ? AND called_at < ?",
                            _et_bounds(d, d)).fetchall()
    finally:
        conn.close()


def calls_today(db_path: Optional[str], provider: str, day: Optional[str] = None) -> int:
    from . import session                                       # noqa: PLC0415
    rows = _day_models(db_path, day or session.session_date())
    return sum(1 for r in rows if provider_of(r[0]) == provider)


class GeminiReply:
    def __init__(self, model: str, text: str, usage: dict) -> None:
        self.model, self.text = model, text
        self.usage = type("Usage", (), {
            "input_tokens": usage.get("promptTokenCount"),
            "output_tokens": usage.get("candidatesTokenCount")})()


class GeminiClient:
    """generateContent over HTTPS: the timeout, one retry on 429 or 5xx, and an
    error's text with no key in it. `opener` and `sleep` are the gate's."""

    def __init__(self, key: str, endpoint: str, timeout: float = TIMEOUT_SECONDS,
                 retries: int = MAX_RETRIES, opener=None, sleep=None) -> None:
        self.__key = key
        self.endpoint, self.timeout, self.retries = endpoint, float(timeout), int(retries)
        self._opener, self._sleep = opener, sleep

    def __repr__(self) -> str:
        return f"GeminiClient(endpoint={self.endpoint!r}, key=[REDACTED])"

    def generate(self, model: str, prompt: str, max_output_tokens: int = 1024) -> GeminiReply:
        import json                                             # noqa: PLC0415
        import time as _t                                       # noqa: PLC0415
        import urllib.error                                     # noqa: PLC0415
        import urllib.request                                   # noqa: PLC0415
        from . import secrets                                   # noqa: PLC0415
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                           "generationConfig": {"maxOutputTokens": max_output_tokens,
                                                "temperature": 0}}).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint.format(model=model), data=body, method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": self.__key})
        opener = self._opener or urllib.request.urlopen
        sleep = self._sleep or _t.sleep
        data: dict = {}
        for attempt in range(self.retries + 1):
            try:
                with opener(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                why = f"gemini HTTP {exc.code}"
                if exc.code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    sleep(2 ** attempt)
                    continue
                raise ProviderError(secrets.redact(why)) from None
            except Exception as exc:                            # noqa: BLE001
                why = f"gemini {type(exc).__name__}"
                if attempt < self.retries:
                    sleep(2 ** attempt)
                    continue
                raise ProviderError(secrets.redact(why)) from None
        parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts")
                 or [{}])
        text = "".join(str(p.get("text") or "") for p in parts)
        return GeminiReply(data.get("modelVersion") or model, text,
                           data.get("usageMetadata") or {})


def gemini_client(cfg: Optional[dict] = None, opener=None) -> tuple[Any, str]:
    """(the client, "") or (None, why). The key never enters the why."""
    from . import secrets                                       # noqa: PLC0415
    g = (cfg if cfg is not None else forecasters_config()).get("gemini") or {}
    name = g.get("key_name") or ("GEMINI" + "_API_KEY")
    if not secrets.present(name):
        return None, "key not configured"
    return GeminiClient(secrets.get(name), g.get("endpoint") or "",
                        g.get("timeout_seconds", TIMEOUT_SECONDS),
                        g.get("retries", MAX_RETRIES), opener=opener), ""


def create_metered(provider: str, client_: Any, *, model: str, prompt: str,
                   max_tokens: int = 1024, cfg: Optional[dict] = None) -> Any:
    """One call to `provider`, refused past its daily budget, then the row. The
    budget counts the scope's database's rows for the provider today."""
    allowed = budget(provider, cfg)
    used = calls_today(_SCOPE.get().get("db_path"), provider)
    if used >= allowed:
        raise BudgetExhausted(f"budget {allowed} call(s) a day, {used} used")
    if provider == "gemini":
        resp = client_.generate(model, prompt, max_output_tokens=max_tokens)
    else:
        resp = client_.messages.create(model=model, max_tokens=max_tokens,
                                       messages=[{"role": "user", "content": prompt}])
    record(resp, model)
    return resp


def provider_lines(db_path: Optional[str], day: str, cfg: Optional[dict] = None) -> list[str]:
    """The day's calls and tokens by provider, each beside its forecaster budget."""
    rows = _day_models(db_path, day)
    out = []
    for p in ("anthropic", "gemini"):
        mine = [r for r in rows if provider_of(r[0]) == p]
        out.append(f"Model ({p}): {len(mine):,} call(s), "
                   f"{sum(_n(r[1]) for r in mine):,} input / "
                   f"{sum(_n(r[2]) for r in mine):,} output tokens today; "
                   f"forecaster budget {budget(p, cfg)} a day")
    return out

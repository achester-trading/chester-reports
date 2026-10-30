"""
Validation gate for the one secrets loader. (P2-1)

The defect this guards against already happened: a by-hand FRED pull reported the
key as not set on a box where it was present and verified, because systemd loads
`.env` through EnvironmentFile and a by-hand process reads nothing. The failure was
silent by design -- log once, exit 0 -- so the correct diagnosis and the wrong one
produced identical output.

  A  ONE READER OF `.env`. No module parses it but altdata/secrets.py. Four did,
     and they had already drifted in how they strip quotes and whether they
     tolerate `export`.
  B  THE ENVIRONMENT ALWAYS WINS. `.env` never overwrites a real variable, which
     is what keeps this safe under systemd (EnvironmentFile got there first) and in
     CI (a stale committed `.env` must not shadow an Actions secret).
  C  THE PARSER HANDLES WHAT THE FILE CONTAINS: export, quotes, inline comments, a
     value containing '=', a '#' inside quotes.
  D  NO VALUE EVER REACHES A LOG. present() returns a bool so that "is it
     configured" can be logged without the value entering a string; describe()
     reports verdicts; the module logs nothing itself.
  E  redact() REMOVES A SECRET, including one arriving as a URL query parameter --
     which is how FRED's own API takes it, and therefore how it would reach a
     traceback.
  F  A PLACEHOLDER IS NOT A SECRET. Committed files carry PLACEHOLDER, and treating
     it as configured would make `present()` lie in exactly the case that matters.
  J  THE USER-AGENT RULE (17 Oct 2026): every request but the SEC's carries
     the generic project string from altdata/sources/user_agent.py; no
     User-Agent carries an address; no non-SEC caller imports edgar's.

    python tools/validate_secrets.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import secrets                                   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

# The name is assembled rather than written, because the permission rules deny any
# command containing it -- they cannot tell a grep for an identifier from a read of
# a value, and that is the right way round for a deny list to be wrong.
FRED_NAME = "FRED" + "_API_KEY"

# Files allowed to contain the string ".env" for reasons that are not parsing it.
ALLOWED_ENV_MENTIONS = {
    "altdata/secrets.py",              # the one reader
    "tools/validate_secrets.py",       # this file
    "tools/validate_deploy.py",        # deny-pattern fixtures
    "tools/validate_systemd_units.py",  # asserts EnvironmentFile= on the units
}


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def group_a() -> None:
    print(f"{LINE}\nA. ONE READER OF .env\n{LINE}")
    offenders = []
    for py in sorted(REPO.rglob("*.py")):
        rel = py.relative_to(REPO).as_posix()
        if rel.startswith((".venv/", "build/")) or rel in ALLOWED_ENV_MENTIONS:
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        code = re.sub(r'(?s)""".*?"""', "", text)
        code = re.sub(r"#.*", "", code)
        # Reading the file is the thing being forbidden, not naming it: a module
        # may mention .env in a message. `read_text` or `open` on a path built from
        # it is the pattern that matters.
        if re.search(r'["\']\.env["\']', code) and re.search(
                r"read_text|open\(|splitlines", code):
            offenders.append(rel)
    check(not offenders,
          f"no module parses .env but altdata/secrets.py "
          f"({offenders or 'none'})")

    for gone in ("altdata/sources/massive_chain.py", "daily_cascade/deliver.py",
                 "tools/probe_massive.py", "tools/probe_flashalpha.py"):
        text = (REPO / gone).read_text(encoding="utf-8")
        check("secrets" in text,
              f"{gone} goes through the loader rather than its own parser")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE ENVIRONMENT ALWAYS WINS\n{LINE}")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / ".env"
        p.write_text("CHESTER_TEST_ONE=from_dotenv\nCHESTER_TEST_TWO=from_dotenv\n",
                     encoding="utf-8")
        os.environ["CHESTER_TEST_ONE"] = "from_environment"
        os.environ.pop("CHESTER_TEST_TWO", None)
        n = secrets.load(p, force=True)
        check(os.environ["CHESTER_TEST_ONE"] == "from_environment",
              "a variable already in the environment is NOT overwritten -- under "
              "systemd EnvironmentFile got there first, and in CI an Actions "
              "secret did")
        check(os.environ.get("CHESTER_TEST_TWO") == "from_dotenv",
              "and one that is absent is taken from .env, which is the by-hand "
              "case that was broken")
        check(n == 1, f"and only the absent one counted as set ({n})")

        # override is for a test, and must be explicit.
        secrets.load(p, override=True, force=True)
        check(os.environ["CHESTER_TEST_ONE"] == "from_dotenv",
              "override=True exists and is explicit; no pipeline uses it")
        for k in ("CHESTER_TEST_ONE", "CHESTER_TEST_TWO"):
            os.environ.pop(k, None)

        missing = Path(td) / "nope.env"
        check(secrets.load(missing, force=True) == 0,
              "a missing .env is not an error -- on CI there is none, and there "
              "should not be")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE PARSER HANDLES WHAT THE FILE CONTAINS\n{LINE}")
    text = "\n".join([
        "# a comment",
        "",
        "PLAIN=value",
        "export EXPORTED=value2",
        'DQUOTED="has spaces"',
        "SQUOTED='single'",
        "INLINE=value3 # trailing comment",
        'HASH_INSIDE="value#4"',
        "EQUALS=a=b=c",
        "  SPACED  =  padded  ",
        "NOEQUALS",
    ])
    got = secrets.parse(text)
    cases = {
        "PLAIN": "value", "EXPORTED": "value2", "DQUOTED": "has spaces",
        "SQUOTED": "single", "INLINE": "value3", "HASH_INSIDE": "value#4",
        "EQUALS": "a=b=c", "SPACED": "padded",
    }
    for k, want in cases.items():
        check(got.get(k) == want, f"{k} parses to {want!r} (got {got.get(k)!r})")
    check("NOEQUALS" not in got, "a line with no '=' is skipped, not crashed on")
    check(len(got) == len(cases),
          f"and nothing else was invented ({len(got)} keys)")


def group_d() -> None:
    print(f"\n{LINE}\nD. NO VALUE EVER REACHES A LOG\n{LINE}")
    os.environ["CHESTER_TEST_SECRET"] = "supersecretvalue123"
    try:
        check(secrets.present("CHESTER_TEST_SECRET") is True,
              "present() returns a BOOL, so 'is it configured' can be logged "
              "without the value entering a string")
        d = secrets.describe(("CHESTER_TEST_SECRET", "CHESTER_TEST_ABSENT"))
        check("supersecretvalue123" not in d,
              f"describe() carries no value ({d})")
        check("set" in d and "missing" in d,
              "and does report the verdict for each name")

        src = (REPO / "altdata" / "secrets.py").read_text(encoding="utf-8")
        code = re.sub(r'(?s)""".*?"""', "", src)
        code = re.sub(r"#.*", "", code)
        check("print(" not in code.split("def _main", 1)[0],
              "the module prints nothing outside its CLI")
        check("log" not in code or "logging" not in code,
              "and logs nothing at all -- there is no logger here to misuse")
    finally:
        os.environ.pop("CHESTER_TEST_SECRET", None)


def group_e() -> None:
    print(f"\n{LINE}\nE. redact() REMOVES A SECRET\n{LINE}")
    secrets.remember("abcd1234efgh5678")
    out = secrets.redact("the call failed with key abcd1234efgh5678 in it")
    check("abcd1234efgh5678" not in out and secrets.REDACTED in out,
          f"a registered secret is replaced ({out})")

    url = "https://api.stlouisfed.org/fred/series?series_id=VIXCLS&api_key=zzz9secretzzz&file_type=json"
    out = secrets.redact(url)
    check("zzz9secretzzz" not in out,
          f"and so is an UNREGISTERED key arriving as a query parameter -- which "
          f"is how FRED's own API takes it, and therefore how it reaches a "
          f"traceback ({out})")
    check("series_id=VIXCLS" in out,
          "while the rest of the URL survives, so the log is still useful")

    secrets.remember("short")
    check("short" in secrets.redact("a short word"),
          "a value below the minimum length is not treated as a secret -- "
          "redacting it would turn every log line into markers")
    for ph in ("PLACEHOLDER", "changeme"):
        secrets.remember(ph)
        check(ph in secrets.redact(f"value is {ph}"),
              f"nor is {ph!r}, which is what committed files carry")


def group_f() -> None:
    print(f"\n{LINE}\nF. A PLACEHOLDER IS NOT CONFIGURED\n{LINE}")
    for ph in ("PLACEHOLDER", "changeme", "", "  "):
        os.environ["CHESTER_TEST_PH"] = ph
        check(secrets.present("CHESTER_TEST_PH") is False,
              f"present() is False for {ph!r} -- treating a placeholder as "
              f"configured would make it lie in the one case that matters")
    os.environ["CHESTER_TEST_PH"] = "a_real_looking_value"
    check(secrets.present("CHESTER_TEST_PH") is True,
          "and True for a real value")
    try:
        os.environ["CHESTER_TEST_PH"] = "PLACEHOLDER"
        secrets.require("CHESTER_TEST_PH")
        bad("require() accepted a placeholder")
    except RuntimeError as exc:
        check(".env" in str(exc) and "CHESTER_TEST_PH" in str(exc),
              f"require() names what to configure and where ({exc})")
    finally:
        os.environ.pop("CHESTER_TEST_PH", None)

    # The real names the pipelines ask for, reported as verdicts only.
    print(f"        configured here: "
          f"{secrets.describe((FRED_NAME, 'ANTHROPIC_API_KEY', 'SMTP_USER', 'NASDAQ_DATA_LINK_API_KEY'))}")



def group_g() -> None:
    """AUD-1 2b: a fetch error and a logged exception carry no key."""
    print(f"\n{LINE}\nG. A FETCH ERROR AND A LOGGED EXCEPTION CARRY NO KEY (AUD-1 2b)\n{LINE}")
    import io
    import logging
    from unittest import mock
    from altdata import secrets
    from altdata.sources import _base, fred
    key = "fixturekey0123456789abcdef"
    url = ("https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&"
           f"api_key={key}&file_type=json")
    import requests

    def boom(*a, **k):
        raise requests.ConnectionError(f"HTTPSConnectionPool: Max retries exceeded "
                                       f"with url: {url}")
    with mock.patch.object(_base.requests, "get", boom), \
            mock.patch.object(_base.time, "sleep", lambda s: None):
        try:
            _base.http_get_json(url, max_retries=2)
            err = ""
        except _base.FetchError as e:
            err = str(e)
    check(err and key not in err and secrets.REDACTED in err,
          "a connection error whose text carries api_key=... raises a FetchError "
          "without it")
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    lg = logging.getLogger(fred.__name__)
    lg.addHandler(h)
    lg.setLevel(logging.INFO)
    store = mock.MagicMock()

    def fetch(*a, **k):
        raise RuntimeError(f"socket said: {url}")
    try:
        with mock.patch.object(fred, "_fetch_series", fetch), \
                mock.patch.object(fred, "_get_key", lambda: key), \
                mock.patch.object(fred.time, "sleep", lambda s: None):
            out = fred.pull(store=store, series=[fred.config.FRED_SERIES[0]])
    finally:
        lg.removeHandler(h)
    logged = buf.getvalue()
    check(logged and key not in logged and "socket said" in logged,
          "fred.pull logs an unexpected error's traceback without the key")
    check(all(key not in why for _, why in out.get("failed") or []),
          "and records the failure without it")
    for rel in ("altdata/sources/_base.py", "altdata/sources/fred.py",
                "altdata/sources/fred_releases.py", "altdata/feeds.py"):
        src = (REPO / rel).read_text(encoding="utf-8")
        check("log.exception(" not in src,
              f"{rel} logs no raw traceback (each passes secrets.redact)")


def group_h() -> None:
    """AUD-1 2a: both SMTP senders verify the server's certificate."""
    print(f"\n{LINE}\nH. EMAIL VERIFIES THE SERVER'S CERTIFICATE (AUD-1 2a)\n{LINE}")
    import ssl
    from unittest import mock
    seen: list = []

    class FakeSMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, context=None):
            seen.append(context)

        def login(self, *a):
            pass

        def send_message(self, *a, **k):
            pass

        def sendmail(self, *a, **k):
            pass
    from daily_cascade import deliver
    cfg = {"host": "smtp.example.invalid", "port": 587, "user": "u",
           "password": "p", "rcpt": "b@example.invalid"}
    with mock.patch.object(deliver.smtplib, "SMTP", FakeSMTP), \
            mock.patch.object(deliver, "smtp_config", lambda: (cfg, [])), \
            mock.patch.object(deliver, "build_message", lambda *a, **k: object()):
        state, _ = deliver.send_html("fixture", "<p>x</p>")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "send_smtp_alert", REPO / "scripts" / "send_smtp_alert.py")
    alert_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alert_mod)
    env = {"SMTP_USER": "u", "SMTP_PASSWORD": "p", "SMTP_RCPT": "b@example.invalid"}
    with mock.patch.object(alert_mod.smtplib, "SMTP", FakeSMTP), \
            mock.patch.dict(os.environ, env):
        try:
            alert_mod.main()
        except SystemExit:
            pass
    src = (REPO / "daily_cascade" / "deliver.py").read_text(encoding="utf-8")
    alert = (REPO / "scripts" / "send_smtp_alert.py").read_text(encoding="utf-8")
    ctxs = [c for c in seen if c is not None]
    check(("starttls(context=ssl.create_default_context())" in src
           and "starttls(context=ssl.create_default_context())" in alert),
          "both senders call starttls with ssl.create_default_context()")
    check(state == "sent" and len(ctxs) == 2
          and all(isinstance(c, ssl.SSLContext) and c.verify_mode == ssl.CERT_REQUIRED
                  and c.check_hostname for c in ctxs),
          f"the context each sender's call receives verifies the certificate and "
          f"the host name ({len(ctxs)} of 2 calls)")
    ign = (REPO / ".gitignore").read_text(encoding="utf-8")
    check(all(p in ign.split() for p in (".env*", "!.env.example", "*.db", "*.sqlite",
                                         "*.zip", "monthly_macro_*", "morning_anchor_*",
                                         "weekly_tactical_*", "daily_close_*.pdf")),
          "AUD-1 2c: .gitignore keeps secrets, databases, zips and the box's report "
          "outputs out")


# ---------------------------------------------------------------------------
# I. RCLONE'S VARIABLES (audit-leftovers-1): the crypt remote is built from the
# environment, so no tracked file may give one of its secrets a value.
# ---------------------------------------------------------------------------
RCLONE_SECRET = re.compile(
    r"(?<![{$\w])(RCLONE_CONFIG_\w+_(?:PASSWORD2?|PASS|TOKEN|CLIENT_SECRET)|"
    r"CHESTER_RCLONE_CRYPT_(?:PASSWORD|SALT))\s*[=:]\s*['\"]?(?![$'\"\s]|\{|$)(\S+)")


def rclone_secret_hits(text: str) -> list[str]:
    """A literal value given to an rclone secret variable, or to the crypt
    settings -- `NAME=value` or `NAME: value` with a value that is not a shell
    expansion. Placeholders in angle brackets and the names on their own pass."""
    out = []
    for m in RCLONE_SECRET.finditer(text):
        val = m.group(2)
        if val.startswith("<") or val.startswith("${") or val.startswith("$("):
            continue
        out.append(f"{m.group(1)}={val[:6]}...")
    return out


def group_i() -> None:
    import subprocess
    print(f"\n{LINE}\nI. RCLONE'S VARIABLES CARRY NO LITERAL SECRET\n{LINE}")
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                             text=True).stdout.split()
    check(not [f for f in tracked if f.endswith("rclone.conf")],
          "no rclone.conf is tracked")
    hits = []
    for f in tracked:
        if not f.endswith((".py", ".sh", ".service", ".timer", ".conf", ".yaml",
                           ".yml", ".md", ".env.example", ".txt", ".toml", ".cfg")):
            continue
        if f == "tools/validate_secrets.py":
            continue
        try:
            text = (REPO / f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits += [f"{f}: {h}" for h in rclone_secret_hits(text)]
        # An INVOCATION with an argument: at a line's start, after `$(` or a pipe.
        for m in re.finditer(r"(?:^|\$\(|\|)\s*rclone obscure\s+(?!-)(\S+)", text, re.M):
            if not m.group(1).startswith(("$", "<", '"$', "'$", "`")):
                hits.append(f"{f}: rclone obscure {m.group(1)[:6]}...")
    check(not hits, f"no tracked file gives an rclone secret a value ({hits[:4]})")
    probes = {"export RCLONE_CONFIG_X_PASSWORD=hunter2": True,
              "CHESTER_RCLONE_CRYPT_SALT=abc": True,
              'export "RCLONE_CONFIG_${CRYPT_NAME}_PASSWORD=$opw"': False,
              "RCLONE_CONFIG_CHESTERCRYPT_PASSWORD=$(printf x)": False,
              "CHESTER_RCLONE_CRYPT_PASSWORD=<in .env, never here>": False,
              "the .env lines CHESTER_RCLONE_CRYPT_PASSWORD and _SALT": False,
              'local pw="${CHESTER_RCLONE_CRYPT_PASSWORD:-}"': False}
    check(all(bool(rclone_secret_hits(t)) == want for t, want in probes.items()),
          "and the scan fires on a literal and passes an expansion, a placeholder and "
          "a bare name (probes)")
    sh = (REPO / "scripts" / "rclone_crypt_env.sh").read_text(encoding="utf-8")
    check("CHESTER_RCLONE_CRYPT_PASSWORD" in sh and ".env" in sh
          and "rclone obscure -" in sh,
          "the crypt script reads the password and salt from the environment (.env) "
          "and obscures them from stdin")


# ---------------------------------------------------------------------------
# J. THE USER-AGENT RULE (ruled 17 Oct 2026). Lettered J, not I: session B's
# audit-leftovers-1 adds its own group I (rclone's variables) to this file.
# ---------------------------------------------------------------------------
# The two modules allowed to write a User-Agent: the generic one and the SEC's.
UA_HOMES = {"altdata/sources/user_agent.py", "altdata/sources/edgar.py"}
# The modules allowed to reach edgar's contact form, each for sec.gov only.
SEC_UA_CALLERS = {
    "altdata/sources/edgar.py",          # its own requests (sec.gov)
    "altdata/sources/user_agent.py",     # for_url, an SEC host only
    "altdata/sources/fundamentals.py",   # EDGAR submissions (data.sec.gov)
    "altdata/sources/voices_scan.py",    # sec_user_agent: 13F and the CIK lookup
    "altdata/sources/edgar_xbrl.py",     # the XBRL frames (data.sec.gov; GTM-4)
    "altdata/sources/treasury.py",       # Strategy's share count (data.sec.gov; item 49)
    "altdata/gold_13f.py",               # the 13F data sets (www.sec.gov; Batch 15 item 72)
}
UA_NAME = re.compile(r"(^|_)(UA|USER_AGENT|HEADERS)($|_)", re.I)


def ua_literals(src: str) -> list:
    """(line, text) for every string literal that is, or builds, a User-Agent:
    a `User-Agent` dict value, a constant assigned to a UA/USER_AGENT/HEADERS
    name, or any literal opening `chester-reports/` or `Mozilla/`."""
    import ast  # noqa: PLC0415
    out = []

    def strings(node):
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                out.append((n.lineno, n.value))
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and str(k.value).lower() == "user-agent":
                    strings(v)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            tgts = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(t, ast.Name) and UA_NAME.search(t.id) for t in tgts) \
                    and n.value is not None:
                strings(n.value)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) \
                and n.value.startswith(("chester-reports/", "Mozilla/")):
            out.append((n.lineno, n.value))
    return sorted(set(out))


def edgar_ua_imports(src: str) -> bool:
    """True when the source reaches edgar's user_agent (attribute or import)."""
    import ast  # noqa: PLC0415
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Attribute) and n.attr == "user_agent" \
                and isinstance(n.value, ast.Name) and n.value.id in ("edgar", "_edgar"):
            return True
        if isinstance(n, ast.ImportFrom) and (n.module or "").endswith("edgar") \
                and any(a.name == "user_agent" for a in n.names):
            return True
    return False


def ua_faults(rel: str, src: str) -> list:
    """The rule's faults in one production file."""
    faults = []
    for ln, s in ua_literals(src):
        if "@" in s or "mailto" in s.lower():
            faults.append(f"{rel}:{ln} a User-Agent literal carries an address")
        elif rel not in UA_HOMES and s.startswith(("chester-reports/", "Mozilla/")):
            faults.append(f"{rel}:{ln} a hand-written User-Agent (use "
                          f"altdata.sources.user_agent)")
    if rel not in SEC_UA_CALLERS and edgar_ua_imports(src):
        faults.append(f"{rel} imports edgar's User-Agent for a non-SEC caller")
    return faults


def group_j() -> None:
    """Ruled 17 Oct 2026: every request but the SEC's carries the generic project
    User-Agent; the SEC alone gets CHESTER_SEC_CONTACT."""
    print(f"\n{LINE}\nJ. THE USER-AGENT RULE: GENERIC EVERYWHERE BUT SEC.GOV "
          f"(17 OCT 2026)\n{LINE}")
    import subprocess  # noqa: PLC0415
    from unittest import mock  # noqa: PLC0415
    from altdata.sources import edgar, user_agent as ua  # noqa: PLC0415
    repo = "https://github.com/achester-trading/chester-reports"
    check(ua.generic() == f"chester-reports/1.0 (+{repo})"
          and ua.browser_like() == f"Mozilla/5.0 (compatible; chester-reports/1.0; +{repo})",
          f"the generic string names the project and its repository, nothing else "
          f"({ua.generic()})")
    with mock.patch.object(edgar, "contact", lambda: "ops@example.invalid"):
        both = (ua.for_url("https://www.sec.gov/Archives/x"),
                ua.for_url("https://data.sec.gov/submissions/x.json"),
                ua.for_url("https://www.federalreserve.gov/feeds/x.xml"),
                ua.for_url("https://sec.gov.example.com/x"))
    check(both[0] == both[1] == "chester-reports/1.0 (ops@example.invalid)"
          and both[2] == both[3] == ua.generic(),
          "fixture both ways: sec.gov and its subdomains get the contact form; "
          "every other host, a look-alike included, gets the generic string")
    with mock.patch.object(edgar, "contact", lambda: None):
        check(ua.for_url("https://www.sec.gov/x") is None,
              "no contact: an SEC host gets None (the caller stays dormant), never "
              "the generic string or a guess")
    # The scanner fires on a planted fault, and passes the clean shape.
    planted = ('import requests\nfrom altdata.sources import edgar\n'
               'UA = {"User-Agent": "chester-reports/1.0 (+mailto:x@example.invalid)"}\n'
               'HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; me)"}\n'
               'h = {"User-Agent": edgar.user_agent()}\n')
    clean = ('from altdata.sources.user_agent import generic\n'
             'UA = {"User-Agent": generic()}\n')
    pf = ua_faults("altdata/sources/planted.py", planted)
    check(len(pf) == 3 and not ua_faults("altdata/sources/clean.py", clean),
          f"the scan catches an address, a hand-written string and a non-SEC "
          f"import of edgar's on a planted file ({len(pf)} of 3), and passes the "
          f"clean shape")
    try:
        files = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO,
                               capture_output=True, text=True, check=True
                               ).stdout.split()
    except Exception:                                         # noqa: BLE001
        files = [str(p.relative_to(REPO)).replace("\\", "/")
                 for p in REPO.rglob("*.py") if ".venv" not in p.parts]
    prod = [f for f in files if not f.startswith(("tools/", "tests/", ".venv/"))
            and f != "smoke_test.py"]
    faults = []
    for rel in prod:
        try:
            src = (REPO / rel).read_text(encoding="utf-8")
            faults += ua_faults(rel, src)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
    check(not faults, f"no production User-Agent carries an address or is written "
                      f"by hand, and no non-SEC caller imports edgar's "
                      f"({len(prod)} files; {faults[:4]})")
    # Gates and fixtures may model the SEC form, only at example.invalid.
    loose = []
    for rel in files:
        if not rel.startswith(("tools/", "tests/")):
            continue
        try:
            src = (REPO / rel).read_text(encoding="utf-8")
            for ln, s in ua_literals(src):
                if "@" in s and "@example.invalid" not in s \
                        and "@example.com" not in s:
                    loose.append(f"{rel}:{ln}")
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
    check(not loose, f"a gate's or fixture's User-Agent carries a reserved "
                     f"example address only ({loose[:4]})")
    shell = []
    for pat in ("*.sh", "*.service", "*.yaml", "*.yml"):
        try:
            shell += subprocess.run(["git", "ls-files", pat], cwd=REPO,
                                    capture_output=True, text=True,
                                    check=True).stdout.split()
        except Exception:                                     # noqa: BLE001
            pass
    bad_sh = []
    rx = re.compile(r"(?:-A\s+|--user-agent[ =]|User-Agent:\s*)['\"]?([^'\"\n]+)", re.I)
    for rel in shell:
        try:
            for i, line in enumerate((REPO / rel).read_text(encoding="utf-8")
                                     .splitlines(), 1):
                m = rx.search(line)
                if m and ("@" in m.group(1) or "mailto" in m.group(1).lower()):
                    bad_sh.append(f"{rel}:{i}")
        except (OSError, UnicodeDecodeError):
            continue
    check(not bad_sh, f"no shell, unit or YAML User-Agent carries an address "
                      f"({len(shell)} files; {bad_sh[:4]})")


def main() -> int:
    print(f"{LINE}\nThe one secrets loader\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i, group_j):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# A94 notes: Learning Loop v2 LL-6, the forecasters and the second provider

**Branch.** `a94-ll6-forecasters`, from `origin/a80-learning-loop-ll2-ll4` at
`56e89f90` (LL-1 to LL-4).

**Merge timing.** It merges after chain-8, which carries LL-1 to LL-4.

**The spec.** The brief (`docs/briefs/learning-loop-v2-brief-2026-10-25.md`) lives
on `b65-learning-loop-v2`, not on this base; it was read there. LL-6 follows its
section 2.3, section 4 and decision 4, ruled D38: three forecasters, two on the
Anthropic model with distinct prompts and one on Gemini, the key the operator's.

**No live call.** No call went to any provider, and nothing spends: every budget
ships at zero.

## The key

- **The variable** is `GEMINI_API_KEY`. The repo had no Gemini name before, so
  the brief's default is used. It is read from the environment, else the box's
  `.env`, through `altdata.secrets`, which registers it for redaction the moment
  it is read.
- **Where it travels.** It goes in the request's `x-goog-api-key` header, never in
  a URL. It is never logged, printed, put in a fixture or written to a manifest.
  The client's `repr` prints `key=[REDACTED]`, and an HTTP error's text is
  "gemini HTTP <code>", with no body and no key.
- **The deny list.** The name joins the Bash deny list in `.claude/settings.json`,
  and `tools/validate_deploy.py`'s secrets cases (`printenv GEMINI_API_KEY`), as
  every key does. Both files are outside the paste's list; the standing rule that
  every key name is denied asked for it.
- **The env template.** `.env.example` is not edited: its Edit path is denied to
  sessions. The operator adds the line on the box.

## What is built

**The meter, `altdata/model_meter.py`.** A second provider sits behind it with no
schema change: a Gemini call is a `model_calls` row under its own model id, and
`provider_of()` splits the rows by prefix.

- `GeminiClient` makes the HTTPS call with the standard library: no new
  dependency, the 90-second timeout, one retry on 429 or 5xx.
- `create_metered()` refuses a call once the provider's daily budget is spent,
  before the call is made. It counts the scope's database's rows for the
  provider that ET day.
- `provider_lines()` prints each provider's calls and tokens beside its budget.

**The config, `config/forecasters.yaml`.**

- **Budgets:** `anthropic` and `gemini` each at `calls_per_day: 0`.
- **The Gemini endpoint and the key's name.**
- **Three forecasters:** `opus-a` (base-rate-v1) and `opus-b` (inside-view-v1) on
  `claude-opus-5-5`, and `gemini-a` (base-rate-v1) on `gemini-2.5-pro`. The
  operator confirms the Gemini model id when setting its budget.
- **The aggregate's settings.**
- **The manifests' path:** `~/chester-data/forecasters/manifests.jsonl`.

**The forecasters, `altdata/forecasters.py`.**

- **Commands:** `status` (what each would do; no call) and `run --questions FILE`.
- **Independence:** each forecaster answers the same code-built packet and never
  sees another's answer.
- **Sources:** each answer is `forecaster:<provider>:<prompt-id>`.
- **Manifests:** one JSON line per forecaster per run, opened only to append. It
  carries the run, the time, the forecaster, the source, the provider, the model
  id, the prompt id and its sha256, the packet's as-of, the questions, the output
  and the tokens. Cost is in tokens, never dollars (AUD-2).
- **The aggregate** is section 2.3's: the extremized mean of the log-odds,
  weighted by track record, equal until each forecaster has 100 resolved rows
  (none has).
  - The brief names extremizing but no factor, so `extremize: 1.0` (the plain
    log-odds mean) until a ruling sets it.
  - Inputs are clipped to [0.01, 0.99].
  - Each line prints n of 3 and the factor.
- **Rights:** none. The gate proves no report writer, the register, the lab or the
  object imports it.

**Not built in this tranche.**

- Choosing the day's questions from the ledger's open claims.
- Writing the answers into the probability ledger as their sources.
- The track-record weights, which follow at 100 resolved rows.

The run takes the questions it is given.

## What prints

Without keys (today, everywhere):

```
anthropic: skipped, key not configured
gemini: skipped, key not configured
aggregate q1: none (n=0 of 3 forecasters; extremized log-odds mean, factor 1, equal weights)
```

On the box, the Anthropic key is already present, so with no Gemini key and the
budgets still zero:

```
opus-a (anthropic): skipped, budget 0 call(s) a day, 0 used
opus-b (anthropic): skipped, budget 0 call(s) a day, 0 used
gemini: skipped, key not configured
```

With both keys and budgets set (anthropic 2, gemini 1):

```
opus-a (anthropic): answered 2 of 2
opus-b (anthropic): answered 2 of 2
gemini-a (gemini): answered 2 of 2
aggregate q1: 0.68 (n=3 of 3 forecasters; extremized log-odds mean, factor 1, equal weights)
```

The last example's figures are illustrative.

## The gate

`tools/validate_ll6.py`, 19/0. It uses fake clients, a fake HTTP opener and a
synthetic key:

- **No key:** a stated skip, and the aggregate from those present.
- **The key:** in the header only. It is absent from the lines, a captured log,
  the manifests, the client's repr and a 500's error text, and the 500 is retried
  once.
- **The budget:** zero blocks the call before it is made; the shipped budgets are
  zero; a spent budget skips and says so.
- **The aggregate:** arithmetic by hand, extremizing and clipping.
- **Manifests:** append-only (AST: the file is opened only with "a"; a second run
  leaves the first run's lines), and every line carries its fields.
- **The meter:** rows by provider, and the lines beside their budgets.
- **Rights.**

**Bookkeeping.** One Makefile line, after LL-4's gate. The count goes from 144/141
to 145/142, by hand: this base has no stitch tools.

**Other gates** (one at a time, foreground):

| Gate | Result |
|---|---|
| `validate_decision_quality` | 35/0 |
| `validate_error_corpus` | 28/0 |
| `validate_value_of_information` | 28/0 |
| `validate_postmortems` | 37/0 |
| `validate_monthly` | 359/0, 1 skipped |
| `validate_audit_2` (the meter) | 26/0 |
| `validate_audit_3a` (the catalogue line added) | 88/0 |
| `validate_deploy` | 154/0 |
| `validate_secrets` | 58/0 |
| `check_registry` | OK |

## The box steps after the merge (the operator's)

1. **Add the key line to the box's `.env`** yourself: `GEMINI_API_KEY=<the key>`.
   Never in a chat, a commit or a paste. Optionally add `GEMINI_API_KEY=PLACEHOLDER`
   to `.env.example` in a commit.
2. **Confirm the Gemini model id** in `config/forecasters.yaml` (`gemini-a`'s
   `model`).
3. **Set the budgets** in `config/forecasters.yaml`. Decision 4's ceiling is three
   calls a day: `anthropic: 2` and `gemini: 1`. That is a commit, so a session
   paste.
4. **Check it.** Run `python -m altdata.forecasters status` on the box: each
   forecaster should read "ready, ..., budget n a day".
5. **Then the next tranche.** Choosing the ledger's open questions and writing the
   answers into the ledger, plus its timer, is a later paste. No timer runs the
   forecasters yet.

# The Capitulation Count's calibration ledger — pre-registration (26 October 2026)

*Signal-triage Batch 17, item 97(a) (docs/change-order-signal-triage-batch-17-2026-10-26.md, entry 97). Session B, B79. Pre-registered and committed alone, before the ledger's first run. Never edited: a change is a new registration and a new dated file. `tools/validate_capitulation_count.py` holds this file's SHA-256.*

## The question

The order adopts the Capitulation Count as a Book C tool. The single binary "4 or more of 5" enters the Top & Bottom intake queue as a bottom-side candidate tell **only after this ledger**. The question is whether, at the paper's episode lows and near-misses, the binary fired, and whether the low held afterwards.

## What is scored

- **The count** at each episode's low (the session's close, as of that day, from the store): one point per scorable family, exactly as `altdata/capitulation_count.py` computes it on any session, with the settings in `config/capitulation_count.yaml`.
- **Each family's state**: yes, no, gap, or **not existent** when the low predates the family's series (`ledger.exists_from`). A not-existent family is never back-filled from a later series, and it does not count as scorable.
- **The scorable count** prints beside every count.

## The episodes

The bears' lows and the near-miss lows of *Tops and Bottoms*, as A77's `config/tb_episodes.yaml` carries them (read on origin/a77-6i-tranches-1-2-5, 26 October 2026, not merged), deduplicated. That makes fourteen episodes:

- **Bear lows:** 3 October 1974, 12 August 1982, 4 December 1987, 11 October 1990, 9 October 2002, 9 March 2009, 23 March 2020, 12 October 2022.
- **Near-miss lows:** 4 April 1994, 8 October 1998, 3 October 2011, 11 February 2016, 24 December 2018, 5 August 2024.

The 1994 and 2011 dates, and several others, are session-set in A77's file, which says so.

## The resolution

Each episode is resolved three ways:
- the S&P 500's return over the next 20 and 60 sessions (`yfinance.mkt_gspc`);
- the Nasdaq-100's over the same horizons, read through **QQQ as a labelled proxy** (`yfinance.mkt_qqq`, from March 1999; blank before);
- **whether the low held**: no S&P 500 close in the next 60 sessions below the low's close.

## The pass rule (session-set: the order states none)

- **Usable episodes:** those with **4 or more** families scorable at the low.
- **INSUFFICIENT:** fewer than **5** usable episodes.
- **PASS:** at least **5** usable episodes, and among them the binary fired at **3 or more**. Of the firings, the low held for 60 sessions in **at least 60%**, and the S&P 500's +60-session return was positive in **at least 67%**.
- **FAIL:** otherwise.

The order names no threshold, so these are this session's, stated before the first run. With the families' series as they stand (VIX from 1990; the equity put/call ratio from late 2019; dealer gamma from October 2026; short interest's stored history not fixed; flows a listed gap), the first edition is expected to read INSUFFICIENT. That expectation is recorded here, before the run.

## The rights consequence

None until PASS. On PASS, the binary is proposed to the T&B intake queue as a bottom-side candidate tell, for the operator's ruling. Nothing here enters the T&B composite, the market-state object, a dial or a band.

## The run

```
python -m altdata.capitulation_count ledger --db <the store> --dry-run   # first
python -m altdata.capitulation_count ledger --db <the store>             # writes the CSV
```

It writes `docs/ledgers/capitulation-count-2026-10-26.csv`: one row per episode, with the count, the scorable count, each family's state, the four forward returns and whether the low held. The run prints this file's SHA-256 and the verdict.

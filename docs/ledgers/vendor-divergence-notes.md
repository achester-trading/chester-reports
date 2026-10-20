# Vendor divergence notes -- FlashAlpha against the engine

A running record, one dated entry per reconciliation. Each entry states the
inputs, the arithmetic and where a gap comes from. A divergence is a question,
never a correction (tools/cross_check.py's rule), and no vendor value enters any
flag, tell, dial or decision. The conventions below are F-3's (ruled 18 Oct 2026).
They print in the Weekly's technical appendix and in the writer's notes
(`altdata/sources/flashalpha.py`) before the first vendor row.

## The conventions, in the same terms

| Quantity | The vendor | Ours |
|---|---|---|
| GEX | Σ dealer position × gamma × OI × 100 × spot² × 0.01, in dollars per 1% move. Calls +, puts − (the convention polarity), on prior-night settled OI, with **their own IV per contract**. | The same sum, on our capture's OI (the prior settlement's) and **our own IV per contract**. It is the report's net GEX per $1 move, times 0.01 × spot. The two are the same definition: the 9 Oct ledger (gex-scale-flashalpha-2026-10-09) found a median per-strike ratio of 1.01 on the same inputs. |
| DEX | Σ delta × OI × 100 × spot, raw option deltas: **the customer book**, calls +, puts −. | **The dealer position**, so a put's sign is opposite. Ours re-signed to theirs reconciled to 1% on 9 Oct. |
| Walls | The peaks across all strikes. | From 22 Oct 2026, the out-of-the-money walls: above spot for calls, below for puts. |

## Entry 1, 18 Oct 2026: the 16 Oct gap, on one strike

*Vendor figures removed, 19 Oct 2026, under the standing rule (no vendor figure in any committed file). The dates, the agreement words and the verdict are unchanged; our own figures stay.*

**The gap.** On 16 Oct, for SPY, the two sides printed:

| | GEX | DEX |
|---|---|---|
| The vendor | negative, several times ours (figure removed) | negative (figure removed) |
| Ours | −1.41bn per 1% | +209.94bn |

The DEX sign is the convention above. The GEX multiple is not a definition difference. So it has to come from the inputs: the OI set, gamma, the multiplier, the spot term, or the expiries covered.

**The strike.** SPY 770, the 23 Oct expiry. The vendor's single-expiry GEX was read through the FlashAlpha connector on 18 Oct, two requests in all. That response carries the 16 Oct settlement's OI (`oi_feed` 2026-10-16). The committed fixture, `tests/fixtures/dealer_block/flashalpha_gex_SPY_exp2026-10-23_770.json`, now carries synthetic values in the response's shape, and the arithmetic is `tools/vendor_reconcile.py`, which `tools/validate_a43_render.py` reproduces.

| | Call | Put |
|---|---|---|
| OI (theirs) | more calls than puts (figure removed) | (figure removed) |
| GEX (theirs) | positive (figure removed) | negative, larger (figure removed) |
| Implied gamma, their convention (GEX ÷ (OI × 100 × S² × 0.01)) | under Black-Scholes' peak | above Black-Scholes' peak |
| The IV that gamma implies (Black-Scholes, 5 calendar days) | a high IV, far above ours (or a very low one) | none: above Black-Scholes' peak for this strike and tenor (near 10% IV) |

**Where the factor comes from: the gamma term.**
- **Gamma.** A call and a put at one strike and expiry have one Black-Scholes gamma at one IV. The vendor's two legs differ by a multiple. With one IV between 12% and 20% for both legs, gamma is 0.0267 to 0.0199. The strike then nets **+40m to +54m**, where the vendor prints a negative net: the sign flips at this strike. The vendor's call leg uses a very high IV, a stale or after-hours quote on a five-day option. That suppresses the call gamma, which is the positive side, and pushes net GEX negative. That is the direction and the size of the headline gap. It is the same failure F-2 rules out of every comparison: a front-expiry vendor IV, in the 16 Oct summary about three times the 20-day realized, and far higher on a 1-DTE.
- **The OI set.** It is the same: both sides read the prior settlement. The response states `oi_feed` 2026-10-16 for the 18 Oct read, and our 16:10 capture of 16 Oct carries the 15 Oct settlement. **For the 16 Oct print, both sides read the 15 Oct settlement.** The box run (below) confirms this on the strike.
- **The multiplier and the spot term.** They are the same: 100 and S² × 0.01 on both sides, as on 9 Oct.
- **The expiries covered.** Not the source at this strike. Both sides span every listed expiry: their summary reports every listed expiry active, and our capture holds every expiry its chain lists. The aggregate's residual after the gamma term is a box question.

**Marked for the box.** Our 16 Oct capture is on the box, not the laptop. The box run sets our OI, IV and gamma for this strike beside the vendor's response, which is kept on the box (outside the checkout) and passed with `--vendor`:

```
.venv/bin/python tools/vendor_reconcile.py --vendor <the vendor's response on the box> --chain data/chains/2026-10-16/SPY_<stamp>.csv
```

Its output becomes this entry's second half: a dated addendum, with nothing above edited except the 19 Oct removal of vendor figures, and with no vendor figure in it.

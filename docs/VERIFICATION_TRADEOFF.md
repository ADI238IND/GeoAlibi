# Verification benefit and missed-change cost

The benchmark now reports `verification_tradeoff` for automatic and, when requested, assisted paths separately. Each pair includes its own confusion metrics; aggregate rates are calculated from summed pixels, not averages of per-image rates.

Pixel transitions distinguish proposal pixels retained or removed from pixels newly added to the supported mask. Counts are split by the binary reference labels. The report includes true-positive loss, false-positive removal, added true/false positives, proposal retention, net recall change and net false-positive reduction. Zero denominators produce null, not a perfect score.

Removed proposals are **not all abstentions**: they include human-review outcomes, nuisance rejection, small/omitted regions and other filtering. Pair results separately expose `all_candidates_abstained`, inspected and omitted region counts for the automatic path. No-region cases are not all-abstention cases. Metrics are pixel diagnostics, not calibrated selective risk, physical area or probability of correctness.

## Real-source development rerun — 31 October 2026

All 21 original A/B/label hashes matched REAL_SAMPLE_MANIFEST.json. The seven previously inspected author-demo pairs were frozen in DEVELOPMENT_INPUTS.json and evaluated with the RGB baseline, threshold 0.12 and minimum area 70. No pretrained inference, tuning or API requests occurred. Data remain subject to the original academic-only/Google Earth terms; imagery is not redistributed.

This is **development data, not an untouched benchmark**. Full results with source hashes, environment, per-pair metrics and transition counts are in DEVELOPMENT_BASELINE_TRADEOFF.json.

| Measurement | Observed pixels |
|---|---:|
| Reference change | 83,992 |
| Correctly proposed change | 63,822 |
| Proposal false positives | 253,487 |
| Correctly proposed pixels removed by verification | 63,822 |
| False positives removed by verification | 253,487 |
| Supported change pixels | 0 |

Proposal recall was 75.99%; supported recall was 0%. Supported precision is undefined because there are no positive predictions. All seven pairs had zero supported pixels; four pairs had every inspected candidate marked for human review, while the others also included nuisance classifications. These counts must not be collapsed into a claim that every candidate on every pair abstained.

The result demonstrates the failure cost of the current automatic path, not an improvement in accuracy. It differs from the historical optional U-Net experiment: this rerun used the RGB baseline. Do not combine their metrics.

Reproduce after obtaining the exact licensed original files:

```bash
python scripts/evaluate.py datasets/levir-author-demo --dataset-manifest docs/DEVELOPMENT_INPUTS.json --output development-results.json
```

Next: use independently reviewed registration evidence and evaluate a separately frozen broader split. Keep recall loss visible alongside false-alarm reduction; do not loosen registration gates merely to make these development results positive.

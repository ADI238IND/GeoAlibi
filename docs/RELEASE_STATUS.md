# Integrated release status — 1 November 2026

The main-targeted release PR #20 is the review entry point for the combined build. Its history preserves the original contributor/research commits. The release includes the following validated work; topic PRs retain their discussions and provenance.

| Original PR | Included contribution | Effect |
|---|---|---|
| #13, #15 | Classical and larger-context experiments | Recorded research; no production matcher promotion |
| #16–#18 | Tested geometry, raw LoFTR replay, independent research scorer | Auditable research evidence |
| #19 | Correct SAM half-open placement, invalid-mask rejection, cache version | Corrected optional SAM evidence |
| #20 | Consolidated application and reproducible offline rehearsal | One local demo command and retained CI artifacts |
| #21–#22 | Frozen source hashes and missed-change/false-alarm accounting | Reproducible evaluation and visible rejection cost |
| #23 | Prospective eight-parent-scene CPU baseline/U-Net diagnostic | New complete-scene evidence; no tuning |
| #24 | Offline blind landmark collection/review and frozen production scorer | Enables actual independent review; no real reviewed annotations yet |

## Current real-data evidence

Eight newly selected full LEVIR test scenes (8,388,608 pixels) were frozen before inference. This is a small test-subset diagnostic, not the model author's full protocol or an audited geographically/training-independent split. No thresholds were adapted to the result.

| Measured stage | Precision | Recall | F1 | IoU |
|---|---:|---:|---:|---:|
| RGB baseline proposals | 4.30% | 66.50% | 8.08% | 4.21% |
| Pinned U-Net proposals | 81.97% | 75.60% | 78.66% | 64.82% |
| Both supported arms | undefined | 0.00% | 0.00% | 0.00% |

All eight production alignments are **flagged unreliable by the current gate**, which does not independently establish their geometric error. Verification removes all 272,155 true-positive and 59,847 false-positive U-Net proposal pixels. Proposal scores cannot be presented as verified-change performance. See [all-scene protocol/results](EXPANDED_EVALUATION.md).

The older seven selected 256px demo crops remain historical development evidence. Their 91.44% U-Net proposal F1 is not the current broader result or a controlled before/after comparison. The separate LoFTR audit's 1/7 candidate-consistent result is not independently verified alignment truth.

## Reproducible deliverables

`python scripts/build_demo_bundle.py --output dist/offline-demo` creates four explicitly procedural scenario images and verified evidence ZIPs, plus a separate arithmetic-checked summary of the saved eight-scene results and their source JSON. It validates exact frozen file coverage, source hashes, pooled/per-scene confusion counts, metric denominators, transition conservation, settings and pinned-model provenance. It does not rerun model inference or access original satellite imagery, weights, credentials, an application ledger or billing. CI retains the bundle and desktop/mobile application/review screenshots for seven days.

[Blind alignment review](BLIND_ALIGNMENT_REVIEW.md) privately embeds original A/B imagery for a collector and a different reviewer. It excludes labels/predictions/transforms and scores every point against saved transforms without refitting. The real eight-scene pack has been generated locally; it remains uncommitted under source-image terms. Names and independence/review declarations remain assertions, not authentication.

## Remaining readiness work

1. Collect and separately review real stationary landmarks without viewing model evidence or labels; freeze the manifest before scoring. No real independent landmark result currently exists. Any policy change then needs a separate frozen evaluation.
2. Restore securely supplied Meta credentials and the existing ledger, reconcile the historical $0.54 reservation and account billing, and run corrected SAM/Muse on an appropriately licensed real pair. Existing parser/geometry tests and historical connectivity do not establish satellite segmentation quality; earlier spatial mask counts need rerunning.
3. Confirm authenticated participant deliverables/rules and rehearse the final recording by November 3. Submission readiness is not established by test success.

New API spend and reservations for this update: $0. The initial cumulative testing ceiling remains $10 within the user's stated $150 budget; neither account balance nor billing is established here. No submission, public deployment or infrastructure purchase is included.

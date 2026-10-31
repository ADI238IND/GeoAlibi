# Consolidated release status — 31 October 2026

## Integrated work

| Original PR | Preserved contribution | Production impact |
|---|---|---|
| #13 | SIFT/AKAZE script and 56-case recorded diagnostic | None; experimental |
| #15 | Larger-context script, six-parent-scene diagnostic and provenance | None; experimental |
| #16–#18 | Geometry tests, raw LoFTR audit/replay and independent-landmark scorer | None; experimental |
| #19 | Correct half-open SAM mask placement, malformed-geometry rejection and cache version | Corrected optional SAM evidence |

The consolidated branch retains all experiment results and checkpoint notes. Earlier PRs remain available for review until the consolidated change is accepted. No automatic registration thresholds were relaxed. Reviewer declarations remain assertions, not authenticated independence.

## What the evidence establishes

- The local workstation handles uploads, investigations, challenge logs, human reviews, evidence responses, exports and portable landmark drafts.
- A pinned pretrained change detector was exercised on seven selected real author-demo pairs: recorded proposal F1 91.44%, with automatic verification abstaining on all candidates. This is a development diagnostic, not a full benchmark.
- Classical and larger-context experiments did not solve real-pair registration. The separately reproduced LoFTR audit produced candidate consistency on 1/7 actual pairs. Those matches are not independently verified alignment truth.
- The official SAM parser/decoder regression now checks exact half-open raster placement. Earlier live requests established connectivity, but corrected satellite segmentation quality remains unmeasured. Historical mask foreground counts require rerunning.
- Offline rehearsal generation produces four explicitly procedural scenarios, evidence ZIPs with verified checksums, source hashes and environment versions. CI retains the bundle with browser screenshots for seven days. It does not package credentials, real imagery or model weights.

## Remaining submission-readiness blockers

1. Collect independent, reviewed real-image stationary landmarks without viewing model outputs; score frozen transforms on every actual pair.
2. Freeze and evaluate a broader untouched satellite split, reporting precision, recall, false alarms and abstention together. Do not tune on that split.
3. Restore authorized secure Meta credentials and the existing ledger, reconcile the historical $0.54 reservation and account billing, then validate one licensed real pair with corrected SAM/Muse. New usage in this consolidation: $0; initial cumulative ceiling remains $10 within the stated $150 budget.
4. Confirm authenticated participant deliverables/rules, rehearse the consolidated commit and prepare the final recording by November 3. This work does not submit or publicly deploy anything.

These are evidence gaps, not completed milestones. Unit/browser success does not establish satellite accuracy or winning readiness.

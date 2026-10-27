# GeoAlibi build checkpoint — 27 October 2026

## Authoritative user idea

The user's application screenshots identify **GeoAlibi**, not the earlier provisional ProofQueue proposal. GeoAlibi compares two satellite images, identifies possible changes, then attempts to falsify each prediction through alignment, lighting, segmentation and consistency checks. It should expose supporting pixels, contradictory evidence and the need for human review. The application proposes SAM 3.1 and Muse Spark and evaluation on public satellite change benchmarks.

## Completed in this build

Runnable local Python API and web workstation; deterministic RGB change baseline; registration and lighting counterfactuals; structural and local luminance checks; perturbation checks; uncertainty/abstention; optional Muse Spark and SAM integration; append-only reviews; report/image export; tests; benchmark runner; Windows/macOS startup instructions. No existing GeoAlibi repository was found in the connected GitHub installation search. No unrelated repository was modified.

## Credentials / credit state

User states $150 in Meta Model API credit. This workspace has no MODEL_API_KEY. No balance was independently verified and no live Meta call was made. Continue implementation without a credential, but do not represent mocked protocol tests as live inference. A key should be placed in the local `.env` by the user or supplied through a secure credential workflow, never committed or embedded in UI.

## Important technical debt

The detector is not trained. Local checks and thresholds are uncalibrated heuristics. Synthetic illustrations do not establish benchmark accuracy. Live SAM integration/coordinate placement and model JSON compatibility still require key-based testing. No real data was downloaded, and no accuracy claim is justified. Registration may choose an incorrect match on repetitive buildings. No GeoTIFF coordinates, multispectral cloud detection or physical area estimation. Public hosting is intentionally blocked until access control is implemented.

## Build targets

- 28 Oct: key-connected real Meta inference plus sample real imagery.
- 29 Oct: licensed pretrained change detector integration and fixed benchmark split.
- 30 Oct: precision/recall, IoU, false-alarm reduction, abstention coverage and latency comparison.
- 31 Oct–1 Nov: deployment security and independent user testing, if full rules require a hosted demo.
- 2–3 Nov: demo video and deliverables; internal readiness by 3 Nov.
- Public submission cutoff: 4 Nov 9 PM Eastern / 5 Nov 7:30 AM IST, subject to organizer updates. Full authenticated submission requirements remain unverified.

## Resume instructions

Read README and VALIDATION.md. Run tests. Obtain the intended GeoAlibi GitHub repository before pushing; do not put this project in Parchi or Fuelprint. Connect MODEL_API_KEY server-side, run the explicit low-token smoke script, then validate one small image pair with Muse and SAM. Implement the pretrained proposal detector only after reviewing its original license, checkpoint provenance, preprocessing and benchmark conventions. Save measured results and disclose fixture versus held-out evidence.


## Continuation update — 27 October

The intended repository now exists at https://github.com/ADI238IND/GeoAlibi and the connector can read/write it. Credentials are configured in a local ignored .env with mode 0600; never commit or copy it to reports. The source still needs its first complete push. Live Muse structured interpretation completed for all six illustrative candidate regions. SAM returned a valid empty result for both procedural building scenes; empty completion is protocol success, not evidence that building segmentation works. A separate nonempty decoder smoke is in progress. See LIVE_VALIDATION.json. Local reservations after the initial calls: $0.53; actual billing is unverified.

A daily scheduled improvement run is enabled around 9 AM IST through November 4. Future runs must inspect GitHub current source, tests and checkpoint; they must not recover credentials from chat history. If a secure key is unavailable, continue independent code/testing and report the blocker. Use branches/draft PRs for subsequent changes. Read-only Billing access has not been established; do not assume the remaining $150 credit balance.

Nonempty SAM decoder smoke completed: five duck objects from the official Meta example photo, with 50,090 foreground pixels. Credential file is excluded by gitignore and the staged source scan. Local reserved amount is $0.54 after this smoke; reservations are deliberately larger than estimated charges. Next highest-impact milestone: licensed pretrained change proposals and a fixed held-out satellite benchmark, followed by selective-risk/coverage reporting. Do not spend on retraining before testing a pretrained baseline.


## Trained detector continuation

Optional pinned author U-Net/ResNet-50 integration is complete, including CPU tiled inference, size/SHA-256 checks, weights_only checkpoint loading, UI/API selection, proposal mask display/export, and provenance. Weights carry CC-BY-4.0 on the author model card; code repository is MIT. LEVIR images are academic-only under the original author terms, and are not redistributed. Seven selected real demo test pairs produced 91.74% proposal precision, 91.15% recall, 91.44% F1; this is not an independent full benchmark. Every verified candidate abstained due to insufficient registration correspondence evidence. A SIFT diagnostic also failed to establish sufficient matches; no thresholds were weakened. See TRAINED_DETECTOR.md and REAL_SAMPLE_EVALUATION.json. Next work must fix or explicitly account for the registration-evidence bottleneck before claiming useful automated verification. No additional Meta API calls were made for this milestone.

The optional-detector branch also includes 21 known-no-change transformed real-source stress cases with zero proposal/accepted false pixels after registration, plus a reproducible runner. These are transformed inputs, not independent acquisitions. GitHub CI passed for the core trained-detector implementation. Retain the real-change all-abstention failure as the next priority.


## v0.3 continuation

Added per-region challenge logs, per-perturbation measurements, prioritized evidence requests, and portable ZIP evidence packets with an offline checksum verifier. Acceptance now uses the worst of the four perturbation survivals, correcting an average-masking weakness. No relaxed registration gate and no new Meta calls. Registration remains the next scientific bottleneck; this update improves auditability and gives reviewers concrete missing-evidence requests. Packet manifests are unsigned integrity checks, never authenticity certification.


## v0.4 continuation

Added explicit landmark-assisted registration for expert-supplied stable correspondences. Fit first N−2 of 6–20 points, withhold final two; bound residuals, spatial coverage and transform size; fail invalid evidence with no automatic fallback. API and upload UI accept JSON in processed original-image coordinates. Reports disclose the user-provided basis and include residuals, full point rows and hash; packets include numbered landmark overlays. Cache identity now includes alignment evidence. Known-transform and invalid-evidence tests passed; no real satellite landmark annotations were fabricated. Automatic registration on the seven demos is still unresolved. Next: collect independently checked real-image control points or larger contextual imagery, then evaluate conditional verification and false-acceptance behavior separately from the automatic path.

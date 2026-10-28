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


## v0.5 continuation

Added dual-image visual landmark picking with exact processed-image previews, click/keyboard input, numbered fit/held-out coloring, undo/clear, explicit application opt-in and stale-pick reset when files change. Manual JSON remains an alternative; picker opt-in disables it and overrides the request through FormData. Previews are not persisted and use the backend decoder. Full browser flow now selects six pairs and confirms a supplied-landmark upload. Registration evidence still needs independently correct landmarks; no real-sample accuracy claims or new API calls. Next priority is to evaluate actual real-image landmark annotations or larger-context automatic registration, then quantify conditional coverage/recall instead of adding more unchecked confidence heuristics.


## Evidence response trail — 28 October

Added append-only responses to each region's evidence requests: provided, unavailable or retracted, with source reference, observation and timestamp. Supplied evidence requires a nonblank source; all responses require a note. Unknown regions/request indices fail. History appears beside the request and exports in report JSON/evidence packets; automated verdicts and human review decisions are preserved. References are plain text and never fetched; statements are not authenticated. SQLite uses an additive table for existing stores. Combined local suite: 44 tests passed, including persistence, retraction and packet export. Added browser interaction coverage, but local Chromium download failed; require GitHub browser CI before merging. No API calls or new reservations. Registration remains independently unresolved; this feature supports collecting evidence rather than claiming it proves change.

## Integrated workstation checkpoint — 28 October

The release/integrated-evidence-workstation branch combines PRs #6–#11: reviewed-landmark paired evaluation, strict label integrity, demo runbook, selected-transform reliability, recorded 28-case real-source audit and append-only evidence responses. Individual branches passed GitHub CI; the combined branch requires its own full CI/browser validation. Combined local unit/API suite: 44 tests. No new paid calls or reservations. Historical $0.54 reserve remains unreconciled because the previous secure ledger and credentials were not restored. Real registration remains unresolved: audit engine 0.4.1 abstains on 7/7 actual pairs, accepts all 14 derived controls and rejects all 7 mismatched candidate controls. Preserve these limits in demos. Next priority is real independently reviewed tie points or larger-context imagery, followed by conditional paired evaluation; do not loosen gates to force positive results. This consolidated branch supersedes the separate draft changes once merged, preserving all of their functional work.


## Portable landmark drafts — 28 October

Added local JSON save/restore for visual landmark work. Drafts bind original Before/After file SHA-256 values and processed dimensions to coordinates, carry an explicit unreviewed notice, and contain no imagery. Restore rejects unsupported schema, wrong images/dimensions, nonfinite/out-of-bounds coordinates and >20 points; file size limited to 64 KB. Async revision checks reject images or picks changed during hashing. Restoring preserves held-out ordering and requires fresh explicit application opt-in. This is a working draft, not an independently reviewed evaluation manifest. Browser regression now covers six-pair export/clear/restore and wrong-image rejection. No paid calls; ledger/credential remain unavailable. Next priority: independently review real landmark correspondence drafts and evaluate conditional verification. Preserve strict automatic abstention.


## Larger-context experiment — 28 October

Retrieved 12 parent images (six distinct 1024x1024 scenes) from a pinned LEVIR-CD mirror archive using bounded ZIP member reads. All seven original-author demo crops matched the parent pixels exactly in both dates; original crop hashes and ZIP member CRCs checked. Parent image SHA-256s and mirror revision recorded; full archive SHA was not downloaded/verified. Engine 0.4.1 still marked all six unique scenes unreliable: feature matches 5–18, fitted inliers at most 4. Seven report rows reflect seven original crops, with test_2 repeated; they are not seven independent parent scenes. No thresholds changed or model accuracy claim. Added context_registration.py and CONTEXT_REGISTRATION.json; 44 existing tests pass. Install remotezip separately to reproduce, then run PYTHONPATH=. python scripts/context_registration.py after restoring original-author crops. Data remain academic-only, never committed. No paid API calls or reservations. Next: independently reviewed control points or separately evaluated learned correspondence methods; simply enlarging context did not solve this sample set.

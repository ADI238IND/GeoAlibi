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


## 29 October learned-matcher handoff

Current main c6be37f includes validated landmark draft preservation; PR #15 context experiment CI passed. Prior interactive LoFTR run observed one candidate pass among seven actual pairs, 0/7 mismatches, 7/7 identical and 5/7 translated controls. Raw local experiment artifacts are not recoverable in this run: compute environment unavailable. Preserve only explicitly transcribed observations in LEARNED_MATCHER_HANDOFF.md, not fabricated raw JSON. Added a separate experimental correspondence geometry checker and regression tests for holdout isolation, known translation, excessive shift, clustered/insufficient evidence and malformed inputs. It is not wired into production and adds stricter duplicate/bounds validation requiring a fresh model rerun. GitHub CI must validate this branch; no local tests or inference possible. No credentials accessed or paid calls made; new reservations $0. Historical $0.54 reserve remains unreconciled. Next: recover/reconstruct inference runner, preserve raw correspondences, independently review the passing pair, and evaluate a frozen broader split. Do not present these candidate counts as verified real alignment or change accuracy.

## 30 October replayable learned-match audit

Read main c6be37f and PR #16 b7df0cd; both had passing CI. Local execution recovered, including prior script, checkpoint and seven development pairs. Built a separate branch atop PR #16 to preserve its unmerged geometry work. Added explicit CPU LoFTR runner, raw correspondence/confidence retention, selected/held-out index mapping, input/checkpoint hashes and environment versions; atomic incomplete/complete reporting; model-free replay rejecting missing/duplicate cases or inconsistent conclusions. No production integration or weakened thresholds.

Fresh hash-verified 28-case run and replay completed: actual candidate consistency 1/7, mismatched 0/7, identical 7/7, translated 5/7. Raw results preserved in docs/LOFTR_AUDIT.json; these are selected development diagnostics, not benchmark accuracy or independently verified registration. All 57 local unit/API tests passed. Local Chromium download failed with a corrupt/zero-byte archive; use GitHub browser CI for this branch. Next: independently review stationary correspondences on the passing actual pair and freeze a broader untouched evaluation split; real-satellite Muse/SAM validation remains outstanding.

Paid API usage and reservations this run: $0. No credential or billing access established; historical $0.54 reservation remains unreconciled and must not be reset. Do not use credentials from chat history. No deployment or submission made.

## 31 October independent alignment scoring

Rechecked main c6be37f and draft #17 673b22f; latest unit/replay/browser CI passed. Added a separate research evaluator for frozen LoFTR transforms against independently collected, image-bound reviewed landmarks. All actual pairs must be included; all review points are evaluation-only, never used for fitting. Record original-image-review declaration, distinct annotator/reviewer IDs, image hashes, both manifest hashes, identity versus transform residuals and explicit missing-transform results. No favourable subset, refitting or promotion of model candidate status. Documentation gives collection procedure and clearly states that real independent annotations remain unavailable.

No API calls or new reservations ($0); historical $0.54 reserve remains unreconciled. Secure credential/billing state has not been established. Next scientific blocker: independently collect and review real stationary landmarks without viewing model outputs, then run the new check and freeze a broader evaluation split. Production gates remain unchanged; no deployment or submission.

Validation for this change: 67 local unit/API/CLI tests passed, including a full fixture command-line run and wrong-image rejection before report creation. Existing 28-case raw audit replay passed; source manifest hashes match. Fixtures exercise behaviour only, not real satellite accuracy. GitHub CI will run the full browser suite on the dedicated draft branch.


## 31 October SAM half-open bounds correction

Re-read current main c6be37f and checked CI: research PR #18 and its predecessors passed. This fix branches directly from main, independent of the research PR stack. Found that the official parser already converts wire endpoints to half-open bounds; GeoAlibi added another pixel, enlarging masks. Corrected exact mask placement, rejected ambiguous/unpaired/malformed geometry and added an adapter-version cache namespace. No production verdict thresholds changed. Real official sample payload now goes through the installed parser and decoder in an offline regression; prior mocked adapter fixture was corrected to reflect actual parser semantics.

Historical live segmentation foreground counts were generated before this fix and require rerunning before spatial validation claims. Connectivity/nonempty decoding observations remain historical facts. No paid calls or new reservations ($0); historical $0.54 reserve remains unreconciled, with secure credentials/billing/ledger unavailable to this work. Next: corrected live satellite-pair validation when those prerequisites are restored; independent real landmarks remain needed for the research registration path. No deployment or submission.

Local validation: 57 unit/API/protocol tests passed on the main-based fix branch, including the real parser/decoder payload regression and cache/failure handling. This count is separate from the 67-test research stack. Full browser CI is required on the dedicated draft PR.


## Matcher comparison — 28 October

Added a reproducible offline SIFT/AKAZE comparison on all hash-verified real demo images: 56 cases across actual, mismatched, identical and translated pairs. Fixed ratio 0.72, RANSAC residual 2.5px, >=8 inliers and >=40% consensus, bounded scale/rotation/translation and >=10% hull coverage; no sweep or test-label tuning. Neither matcher passed candidate geometry for any of 7 actual pairs; neither passed any of 7 mismatched controls. SIFT passed 14/14 derived positives, AKAZE 12/14. Candidate geometry is not independently validated alignment. Kept production behavior unchanged. Results and OpenCV version in MATCHER_COMPARISON.json. Next move beyond these classical matcher substitutions: larger surrounding imagery or independently annotated correspondences, then a separately frozen evaluation. No API calls/spend; prior secure ledger remains unavailable.


## Larger-context experiment — 28 October

Retrieved 12 parent images (six distinct 1024x1024 scenes) from a pinned LEVIR-CD mirror archive using bounded ZIP member reads. All seven original-author demo crops matched the parent pixels exactly in both dates; original crop hashes and ZIP member CRCs checked. Parent image SHA-256s and mirror revision recorded; full archive SHA was not downloaded/verified. Engine 0.4.1 still marked all six unique scenes unreliable: feature matches 5–18, fitted inliers at most 4. Seven report rows reflect seven original crops, with test_2 repeated; they are not seven independent parent scenes. No thresholds changed or model accuracy claim. Added context_registration.py and CONTEXT_REGISTRATION.json; 44 existing tests pass. Install remotezip separately to reproduce, then run PYTHONPATH=. python scripts/context_registration.py after restoring original-author crops. Data remain academic-only, never committed. No paid API calls or reservations. Next: independently reviewed control points or separately evaluated learned correspondence methods; simply enlarging context did not solve this sample set.

## 31 October consolidated release and offline deliverables

User requested all updates together. Combined unchanged, CI-passing heads of #13, #15, #18 (including #16–#17), and #19 into one main-targeted release branch. Preserved experiment JSON/scripts, all checkpoint sections, corrected SAM production adapter and research isolation. Rebuilt a single source manifest. No contributor branches were overwritten or discarded.

Added one-command offline rehearsal generation: four fixed-seed procedural scenarios, verified evidence ZIPs, local preview images, source/dependency identity and explicit limitations. Output refuses overwrites, stages generation before publishing the directory, and never loads credentials, a ledger, model weights or external imagery. CI now builds the bundle and retains it with browser screenshots for seven days. README, runbook and RELEASE_STATUS.md distinguish established evidence from missing validation.

New paid API usage/reservations $0; historical $0.54 reserve remains unreconciled. Independent real landmarks, broader frozen benchmark, corrected real-image Meta validation and authenticated submission rules remain outstanding. No deployment or submission. This consolidated PR is intended to replace the separate review stack once accepted.

Consolidated local validation: 82 tests passed; raw LoFTR audit replay passed; four-scenario rehearsal bundle generated and all four ten-file packets verified. The mixed illustration has two supported and four review regions; nuisance illustrations have no supported regions. These are behavioural fixtures, not benchmark scores. Local Chromium download again returned corrupt archives, so combined browser validation must come from GitHub CI before acceptance.


Combined CI exposed an exact-float replay comparison failure after all 82 tests passed. Added a strictly bounded absolute 1e-9 tolerance only for recomputed numerical geometry, with visible maximum-delta warnings; all raw data, match indices, holdout membership and decisions remain exact. Stored experimental results and registration thresholds are unchanged. Added regressions for tiny roundoff versus changed errors/indices. Require a fresh complete CI run before reporting consolidation as validated.

## 31 October frozen benchmark inputs

Rechecked main c6be37f and consolidated draft #20 4166fb4; both final consolidation CI runs passed. Added a benchmark input freeze/validation path on top of that consolidated branch. Exact A/B/label filename sets and original image/label SHA-256s are checked before inference; the manifest binds the explicit subset limit and refuses silent overwrites. Evaluated bytes are checked again after preflight. Outputs disclose frozen/unfrozen status and all source hashes. No model thresholds changed and no broader real benchmark or synthetic accuracy claim was made.

Existing runtime dependencies needed restoring; source remained available. No secure credential, historical ledger or account billing access was established, so no paid API calls or reservations were made ($0 new; historical $0.54 unreconciled). Next: freeze an independently selected licensed split before inspecting predictions and run it once compute/inputs are ready. Independent landmark review and corrected real-image Meta validation remain outstanding.

Validation: 90 local unit/API/CLI tests passed, including a complete frozen-evaluation CLI fixture and rejection of changed labels before any pair evaluation. Existing saved LoFTR replay passed and source hashes verified. Fixture metrics are not reported as satellite accuracy. Require full branch CI, including browser/demo generation, before accepting the follow-up.

## 31 October verification trade-off accounting

Read current main and PR #21 b5f82cf; both latest CI runs passed. Added proposal-to-supported transition counts/rates to the benchmark, separately for automatic and assisted arms, plus per-pair automatic confusion metrics, inspected/omitted counts and all-candidate-abstention indicators. Aggregate ratios use pooled pixels and zero denominators remain null. Removed proposals are explicitly not equated with abstention; additions are counted too, so new false alarms cannot be hidden.

Verified all 21 original author-demo image/label hashes and ran the RGB baseline on the frozen seven-pair development set. Proposals contained 63,822 true-positive and 253,487 false-positive pixels; verification removed all of both. Supported recall 0, precision undefined. Four pairs had all inspected candidates in review; seven had zero supported pixels. This is not the optional U-Net result, an untouched benchmark, or a success claim. Saved original-input manifest and full measured output with environment/source identity. No thresholds were tuned.

No paid API calls or reservations ($0 new); historical $0.54 remains unreconciled. Secure credential, ledger and billing access remain unavailable for live Meta validation. Next scientific priority remains independent real registration evidence and a broader frozen split. No public deployment or competition submission.

Validation: 95 local tests passed, including all-abstention cost, empty denominators, introduced false positives, pixel-weighted aggregation, invalid-mask rejection and full CLI reporting. The seven-pair measured diagnostic completed successfully; CI must additionally validate browser and offline demo workflows on this branch.


## 1 November frozen eight-scene evaluation

Continued from draft #22 4467538 (CI passed) and pre-acquisition plan commit 799ef6d. Runtime reset removed installed dependencies and interrupted acquisition; restored the CPU environment without changing the selected scenes or settings. Added deterministic filename-hash selection excluding all six previously used parents, staged ZIP member acquisition, CRC/PNG validation, original-file hashes, overwrite protection and offline regressions. No imagery or model weights committed. New work is draft #23, evaluation/frozen-eight-scenes, stacked on #22.

All 24 selected files are complete. Input hashes were committed at f6b8028 before inference. Both eight-scene baseline and pinned U-Net runs completed with identical input hashes and alignment diagnostics. Model checkpoint size, SHA-256 and strict CPU load passed. Full-frame U-Net proposal P/R/F1/IoU = 81.97/75.60/78.66/64.82 percent; baseline proposal F1 8.08 percent. Both verified arms accept zero pixels (recall 0, precision undefined), with unreliable registration on every scene. U-Net verification removes 272,155 true-positive and 59,847 false-positive proposal pixels. All eight U-Net scenes have all inspected candidates in review. Full results, per-scene failures/omissions, environment and protocol are saved under docs/EXPANDED_*; this is a small prospective test-subset diagnostic, not a full or audited training/geographic-independent benchmark. Do not tune on it and call it untouched holdout later.

Validation: 104 local tests pass; saved raw LoFTR replay passes; four-scenario procedural demo bundle builds and packet checksums verify. Both acquisition-code CI runs passed including browser and offline bundle generation (41271389893 and 41271386754). Final report commit requires a fresh complete CI pass; inspect its runs before acceptance.

API cost: $0 observed new calls/spend, $0 new reservations; historical $0.54 reserve remains unreconciled. Secure live Meta credential, billing and ledger access remain unavailable. No deployment, infrastructure purchase or competition submission. Next: independently collected/reviewed stationary landmarks for registration validation, followed by a separately frozen policy evaluation; no threshold weakening to conceal zero verified recall. Corrected-geometry live Meta validation remains blocked on secure credentials/billing reconciliation.


## 1 November blind production-alignment review workflow

Read main c6be37f and draft #23 32e896b; both final #23 CI runs passed (41271728925, 41271725454). Selected the independent-registration evidence blocker. Added a self-contained offline collection/review pack for frozen datasets, showing only processed original A/B images. It validates raw image/label hashes, never decodes or embeds label pixels, and never loads predictions, transforms, model matches, weights, credentials or billing. Per-scene point selection, zoom, portable unreviewed drafts, image/task binding, distinct reviewer IDs, explicit per-pair approval and invalidation after edits/imports/reviewer changes make real review actionable. Declarations remain unauthenticated assertions.

Added a separate scorer for saved production benchmark transforms: exact frozen dataset and reviewed coverage, original-byte binding, actual processed coordinate dimensions up to 1024px, all points evaluation-only, no refit, retained production reliability flag, full residuals and all artifact hashes. New output paths refuse overwrites. No production thresholds or acceptance rules changed. Existing LoFTR scorer and earlier measured results are preserved.

Generated the private eight-scene pack locally (39MB HTML), with all 24 source hashes verified. No real separately reviewed human annotations exist, so no independent alignment score or benchmark improvement is claimed. Generated packs remain uncommitted because they contain academic-use imagery. Added browser-to-CLI roundtrip testing with generated contract fixtures and wired it into CI. Local Chromium installation again failed with a corrupt download; require the new complete browser CI before acceptance.

Validation so far: 123 local tests pass (19 new), including full-1024px coordinates, no-refit behaviour, failed-decision preservation, wrong images/tasks, incomplete/duplicate sets, unreviewed/model-derived records, same-person IDs, invalid matrices/decisions and output preservation. Inline generated JavaScript syntax check passed. Require raw LoFTR replay, final source hash/demo checks and complete new-branch CI before acceptance.

New API usage/spend $0; new reservations $0. Historical $0.54 remains unreconciled. Secure live Meta credential, billing and ledger access remain unavailable. No submission, deployment or infrastructure purchase. Next: actual independent original-image collection and separate review before any registration-policy proposal; then a separately frozen evaluation. Other independent code/demo work can continue without credentials.

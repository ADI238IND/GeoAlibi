# Reproducible local demo runbook

## Preparation

Use a clean Python environment and README installation steps. Keep the server bound to 127.0.0.1. Run `python -m pytest -q` and `python scripts/check_ui.py`; retain terminal results and the exact Git commit. The browser check requires Playwright Chromium (`python -m playwright install chromium`). No public deployment is required for this rehearsal.

Start with Meta options disabled. Record whether the detector is the default RGB baseline or the optional pinned U-Net. Do not imply that the baseline is trained. Keep downloaded imagery and weights outside version control, preserving their licenses.

## Three-minute rehearsal

1. Introduce GeoAlibi: investigate an apparent change by challenging alignment, lighting and local consistency. Explain that supported is a diagnostic verdict, not proof of real-world change.
2. Run a built-in illustrative scenario. Explicitly call it procedural imagery. Compare before/after, proposal and supported masks. Open a region's challenge log and show unresolved explanations and requested evidence.
3. Demonstrate a nuisance scenario and human-review outcome. Show the append-only review history. Do not promise all nuisances will be rejected.
4. Export an evidence ZIP and run `python scripts/verify_packet.py evidence.zip`. Explain that unsigned checksums detect content changes relative to the manifest; they do not authenticate acquisition or correctness.
5. Disclose the current saved real-data result: eight new complete LEVIR test scenes gave 78.66% U-Net proposal F1 versus 8.08% baseline proposal F1, while both supported arms accepted zero pixels (recall 0, precision undefined). All eight alignments failed the current reliability gate. This small prospective diagnostic does not establish full-benchmark or verified-change accuracy. Show the separate recorded-research-evidence.json, including removed true-positive pixels, rather than treating procedural scenario outcomes as real-data results.
6. If demonstrating landmarks, use actual independently checked correspondences. State that the final two points are withheld from transform fitting and that geometric agreement does not authenticate the points. Never insert identity points merely to bypass abstention.

## Optional live Meta segment

Only enable Muse/SAM when a server-side authorized credential and the existing persistent budget ledger are securely available. Do not recreate an empty ledger to reset the testing ceiling. Prior recorded reservation was $0.54; this must be reconciled against the real ledger before spending. The initial cumulative ceiling is $10 within the user's stated $150 allowance. Check Billing before larger runs. Never show credentials or environment files on screen.

Show actual provider status and disclose failure if it occurs. Existing live validation used procedural scenes and a nonempty duck-photo parser smoke; it does not establish satellite segmentation accuracy. Cached results must be identified as cached. A failed provider call must preserve local evidence.

## Evidence to retain

Record commit SHA, dependency versions, detector/checkpoint identity, scenario or licensed dataset filenames and hashes, settings, complete output metrics including recall/abstention, report JSON and packet-verifier result. Keep original image permissions and private data in mind before sharing packets. Save rehearsal recording locally; no competition submission or public publication is authorized by this runbook.

## Release gates before November 3 readiness

- Complete the offline blind collection/separate-review workflow in docs/BLIND_ALIGNMENT_REVIEW.md; independently reviewed real correspondences remain missing. Larger context alone did not solve the earlier examples; evaluate automatic and assisted arms separately using docs/ASSISTED_EVALUATION.md.
- Validate Muse/SAM on appropriately licensed real imagery without claiming protocol success establishes accuracy.
- Confirm participant submission requirements from the authenticated organizer materials.
- Rehearse from a clean environment, retain exact failures and prepare an offline local demonstration if provider access fails.


## One-command offline rehearsal

Run `python scripts/build_demo_bundle.py --output dist/offline-demo` after installation. The builder verifies the checked-in source manifest, generates four fixed-seed procedural scenarios, verifies every evidence packet, and writes a summary with dependency versions and source digest. It never loads API credentials, an application ledger or downloaded imagery/weights. It refuses existing output directories; use a new directory for each rehearsal.

Read `dist/offline-demo/README.md`, inspect its local images and open the evidence ZIPs. All bundled images are procedural. The separate recorded-research-evidence.json derives the saved eight-scene results from their source JSON, with arithmetic, complete-set and frozen-hash validation. These reports are not newly inferred by the builder, and original satellite imagery, labels and weights are excluded. Undefined supported precision and zero recall remain explicit. GitHub CI retains the generated bundle and browser screenshots for seven days as `geoalibi-rehearsal-<commit>`. Download it from the successful workflow run; source scripts can reproduce it after artifact expiry. Runtime/ZIP metadata may differ across runs; source/fixture identity is recorded rather than claiming byte-identical archives.

The SAM half-open-bounds fix invalidates earlier spatial foreground counts. Do not reuse those counts in a pitch; see SAM_GEOMETRY.md before any new live demonstration.


## Continue a bounded inspection

For a new run with more than 24 eligible candidates, use the scope panel's **Inspect ranks …** button. Each click creates a separate linked investigation for the next 24 ranks (or the final smaller batch), using the saved full-scene Before/After images and proposal mask. It recomputes deterministic local checks but does not rerun the proposal detector, Muse or SAM; provider options cannot enable paid calls on this route.

The frozen context binds implementation source, NumPy/OpenCV versions, engine, settings, original/registered/normalized pixels, valid footprint, candidate mask, morphology and alignment evidence. Any mismatch refuses continuation before creating a child report. Stable global region IDs and rank bounds make batches comparable. The original report and its human notes remain intact. A child records immediate/root IDs and source asset hashes; **Open original investigation** returns to the first result.

Counts, supported masks and outside-batch omission maps are **per batch**, not a cumulative scene-level verdict. Purple regions may have been covered by earlier linked batches. Compare retained reports and do not infer scene-wide absence of change from any empty supported mask. A failed registration gate remains failed across matched-context continuations. Historical runs without a frozen context require a new original-pair run; a source-code or numerical-library upgrade may also require rerunning. Restart after a source update; the process refuses to analyse if its on-disk implementation differs from the version imported. Evidence ZIP summaries retain lineage and these scope limits.

# Reproducible local demo runbook

## Preparation

Use a clean Python environment and README installation steps. Keep the server bound to 127.0.0.1. Run `python -m pytest -q` and `python scripts/check_ui.py`; retain terminal results and the exact Git commit. The browser check requires Playwright Chromium (`python -m playwright install chromium`). No public deployment is required for this rehearsal.

Start with Meta options disabled. Record whether the detector is the default RGB baseline or the optional pinned U-Net. Do not imply that the baseline is trained. Keep downloaded imagery and weights outside version control, preserving their licenses.

## Three-minute rehearsal

1. Introduce GeoAlibi: investigate an apparent change by challenging alignment, lighting and local consistency. Explain that supported is a diagnostic verdict, not proof of real-world change.
2. Run a built-in illustrative scenario. Explicitly call it procedural imagery. Compare before/after, proposal and supported masks. Open a region's challenge log and show unresolved explanations and requested evidence.
3. Demonstrate a nuisance scenario and human-review outcome. Show the append-only review history. Do not promise all nuisances will be rejected.
4. Export an evidence ZIP and run `python scripts/verify_packet.py evidence.zip`. Explain that unsigned checksums detect content changes relative to the manifest; they do not authenticate acquisition or correctness.
5. Disclose the real-data result: seven selected author-demo pairs gave 91.44% proposal F1 in the recorded development experiment, while verification abstained on every candidate. This is neither a full benchmark nor automatic-verification accuracy.
6. If demonstrating landmarks, use actual independently checked correspondences. State that the final two points are withheld from transform fitting and that geometric agreement does not authenticate the points. Never insert identity points merely to bypass abstention.

## Optional live Meta segment

Only enable Muse/SAM when a server-side authorized credential and the existing persistent budget ledger are securely available. Do not recreate an empty ledger to reset the testing ceiling. Prior recorded reservation was $0.54; this must be reconciled against the real ledger before spending. The initial cumulative ceiling is $10 within the user's stated $150 allowance. Check Billing before larger runs. Never show credentials or environment files on screen.

Show actual provider status and disclose failure if it occurs. Existing live validation used procedural scenes and a nonempty duck-photo parser smoke; it does not establish satellite segmentation accuracy. Cached results must be identified as cached. A failed provider call must preserve local evidence.

## Evidence to retain

Record commit SHA, dependency versions, detector/checkpoint identity, scenario or licensed dataset filenames and hashes, settings, complete output metrics including recall/abstention, report JSON and packet-verifier result. Keep original image permissions and private data in mind before sharing packets. Save rehearsal recording locally; no competition submission or public publication is authorized by this runbook.

## Release gates before November 3 readiness

- Obtain independently reviewed real correspondences or larger-context registration evidence; evaluate automatic and assisted arms separately using PR #6's protocol after review/merge.
- Validate Muse/SAM on appropriately licensed real imagery without claiming protocol success establishes accuracy.
- Confirm participant submission requirements from the authenticated organizer materials.
- Rehearse from a clean environment, retain exact failures and prepare an offline local demonstration if provider access fails.

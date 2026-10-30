# Reproduce the experimental learned-match audit

This audit does **not** change production registration or turn model matches into human landmarks. A candidate pass means consistency among one model's matches, including a fixed random holdout. Shared model errors can pass it. The seven selected author-demo pairs are development diagnostics, not an untouched benchmark. Identical and translated controls are derived imagery, not independent acquisitions.

Run from the repository root using Python 3.12. Install the normal project dependencies first, then the optional research dependencies:

```bash
python -m pip install -e '.[meta,test]'
python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install kornia==0.8.1
python scripts/evaluate_loftr.py --checkpoint models/loftr_outdoor.ckpt --dataset datasets/levir-author-demo --output audit.json
python scripts/replay_loftr.py audit.json
```

Obtain the checkpoint separately from the pinned mirror in [LEARNED_MATCHER_HANDOFF.md](LEARNED_MATCHER_HANDOFF.md). The runner verifies its exact size and SHA-256 before CPU `weights_only=True` loading, uses `pretrained=None`, and never downloads weights implicitly. LoFTR's recorded model card license is MIT; retain upstream attribution. Obtain imagery under the original LEVIR academic-use/Google Earth terms; [REAL_SAMPLE_MANIFEST.json](REAL_SAMPLE_MANIFEST.json) identifies the exact author-demo files and SHA-256 values. No imagery or model weights are redistributed here.

The fixed protocol uses After-to-Before grayscale matches, confidence >=0.8, PR #16's geometry checker, and the same four cases for each of seven filenames. All input files, including labels, must match the manifest. Labels are hash-checked but never used for registration. Each result retains **all** model coordinates and confidences, selected raw indices, fit/held-out indices into that selected array, transform, residuals, source-file identities, control transform and inference/check duration. Invalid duplicate/bounds geometry abstains explicitly. Malformed or nonfinite model output stops the run.

Output is atomically replaced after each case and marked `complete` only after all cases finish. Replay rejects incomplete reports, duplicate/missing cases, altered geometry and inconsistent aggregate counts. It checks the geometry source digest and recomputes the fixed protocol without PyTorch or Kornia. Replay is an internal consistency check, not a signature or proof that the model produced the recorded matches. Cross-version OpenCV/NumPy differences may require reproducing the recorded environment.

Next scientific step: independently reviewed stationary landmarks on actual acquisitions, followed by a frozen broader split. Do not tune gates on this development set or report these counts as change-detection accuracy.

## Observed rerun — 30 October 2026

The fresh CPU run completed all 28 cases using the pinned, hash-verified checkpoint and input files. [LOFTR_AUDIT.json](LOFTR_AUDIT.json) contains raw model outputs and successfully passed model-free replay. Candidate passes: actual pairs **1/7**, mismatched **0/7**, identical **7/7**, translated **5/7**. The actual passing pair remains `test_7_0256_0512.png`. These match the earlier observation despite stricter validation, but still require independent landmark review. No production gate changed and no paid API was used.

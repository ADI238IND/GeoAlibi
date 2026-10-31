# Learned-correspondence experiment handoff

## Prior observed run (28 October 2026)

The preceding interactive run executed CPU LoFTR outdoor on the seven hash-verified original-author development crops and three controls per crop. Its terminal output recorded:

| Case | Candidate passes | Cases |
|---|---:|---:|
| Actual before/after | 1 | 7 |
| Mismatched filenames | 0 | 7 |
| Identical source | 7 | 7 |
| Translated source | 5 | 7 |

This table is transcribed from observed terminal results. The raw local JSON and inference script were not pushed before the runtime became unavailable on 29 October. They were recovered on 30 October; the new reproducible runner and raw-match protocol are documented in LOFTR_AUDIT.md. The historical table below remains a transcription, not an independent benchmark.

The passing actual pair was test_7_0256_0512.png: 48 matches, 36 fitting / 12 held out, 33 fitted inliers, held-out RMS 1.4977 pixels, and 11/12 held-out errors within 2.5 pixels. test_55_0256_0000.png had 26 matches but failed its held-out check (4/6 within 2.5 pixels; RMS 3.2165 pixels). Other actual pairs had fewer than 16 matches.

## Provenance and protocol to reproduce

- Kornia 0.8.1; CPU torch 2.6.0+cpu; LoFTR outdoor instantiated with pretrained=None.
- Checkpoint mirror: https://huggingface.co/kornia/loftr/tree/0fb3b456cf176746709c38fa9cf80695a1c82dac
- File: loftr_outdoor.ckpt; bytes: 46341978.
- SHA-256: 21f5bec5968178e8bc8b7633441836fe5de4f47d861dd2cd7dc38e271b0479ec.
- Check the full hash before loading with torch.load(..., map_location="cpu", weights_only=True). Never fall back to unrestricted pickle loading.
- Use original 256px grayscale image tensors divided by 255; image0=After, image1=Before. Retain confidence >=0.8, with no threshold sweep.
- Freeze seed 42 permutation; withhold max(4, N//4) matches, fit remaining matches with similarity RANSAC at 2.5px.
- Require >=16 matches, >=8 fitting inliers, >=40% fitting consensus, scale strictly between .95 and 1.05, rotation <=5 degrees, shift <12% of shorter dimension, >=10% inlier convex-hull coverage in both images, >=80% held-out errors within 2.5px.
- The new correspondence_checks module tests these geometry checks without downloading weights. It additionally rejects duplicate/nonfinite/out-of-bounds inputs. Prior counts must be rerun through this stricter validation before comparison.
- The original demonstration image hashes are in REAL_SAMPLE_MANIFEST.json. Images remain subject to the original academic-use terms.

## Next experiment

Recover or reconstruct the inference runner and retain raw correspondences, confidence values, input hashes, complete environment versions and holdout indices. Repeat the fixed protocol, then inspect the passing pair against independently reviewed landmarks and expand the untouched evaluation split. Correlated errors from the same matcher can survive a random holdout. None of this validates physical change, model accuracy or acquisition provenance. Do not feed model matches into the expert-landmark path disguised as human evidence.

No production registration changes are introduced. No paid API calls occurred.

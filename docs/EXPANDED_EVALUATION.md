# Frozen eight-scene evaluation

This is a prospective small LEVIR-CD test-subset diagnostic, not a full benchmark or an independently audited geographic/training split. Selection was committed before downloading the selected imagery or inspecting predictions: [plan commit 799ef6d](https://github.com/ADI238IND/GeoAlibi/commit/799ef6d92e02f731fc48b81c29c296d938bf03ee). No thresholds are tuned on this subset.

The plan excludes all six previously used parent scenes, ranks eligible matching A/B/label filenames by a fixed SHA-256 key, and takes eight complete 1024×1024 scenes. Acquisition rejects incomplete or ambiguous inventories, oversized members, invalid PNGs and wrong dimensions. Each member's ZIP CRC is checked; source-byte SHA-256s and the exact plan hash are recorded. The whole remote ZIP is not downloaded or independently SHA-256 verified. Publication is staged; failed downloads do not publish a partial dataset, and existing output is never replaced.

## Reproduce

Use Python 3.12 and install the project's test dependencies. Install the optional research download dependency and CPU detector environment separately:

```bash
python -m pip install remotezip==0.12.6
python -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install segmentation-models-pytorch==0.3.3
python scripts/download_detector.py
python scripts/prepare_evaluation_subset.py --output datasets/levir-frozen-eight
python scripts/evaluate.py datasets/levir-frozen-eight --dataset-manifest docs/EXPANDED_EVAL_INPUTS.json --detector baseline --output baseline-results.json
python scripts/evaluate.py datasets/levir-frozen-eight --dataset-manifest docs/EXPANDED_EVAL_INPUTS.json --detector unet --output unet-results.json
```

The published input manifest must match all 24 original files before inference. Frozen settings: threshold 0.12, minimum region area 70, automatic production registration, no landmarks or learned registration, no paid APIs. U-Net uses the existing pinned Corley et al. ResNet-50 checkpoint, 256px nonoverlapping tiles and class-1 probability >0.5. The complete processed footprint is scored; abstained/rejected pixels count negative. Proposal and supported scores are separate. Empty precision is undefined, not 100%.

## Attribution and limits

LEVIR-CD is provided for academic research only; commercial use is prohibited and underlying Google Earth terms apply: https://justchenhao.github.io/LEVIR/. The pinned mirror revision and URL are in EXPANDED_EVAL_PLAN.json. Imagery and weights are not redistributed in this repository. Eight newly selected parent filenames do not prove spatial independence from earlier examples or disjointness from model training.

Pretrained weights: Isaac Corley, Caleb Robinson and Anthony Ortiz, *A Change Detection Reality Check* (2024), CC-BY-4.0; https://huggingface.co/isaaccorley/a-change-detection-reality-check, revision 52e7fdb42ddf4e89661c56ef8b8900528a20df0a. Model code/provenance and checkpoint integrity are enforced in geoalibi/pretrained.py. GeoAlibi did not train this model.

## Measured results — 1 November 2026

All 24 input hashes were recorded in [commit f6b8028](https://github.com/ADI238IND/GeoAlibi/commit/f6b8028264f3bf25259f89dfee53658773a7479c) before either run. Source code: ea6c66d77342e407f338aca607cdd2ffa3912fe7; exact installed inference packages are in EXPANDED_EVAL_ENV.txt. Both runs completed on CPU with no API calls. Source manifests, original hashes, processed-input identities, alignment diagnostics, per-scene confusion counts, omissions and transitions are saved in the two EXPANDED_*_EVALUATION.json reports.

Pooled pixel metrics across 8,388,608 pixels, including 359,991 labelled change pixels:

| Stage | Precision | Recall | F1 | IoU |
|---|---:|---:|---:|---:|
| Raw RGB | 4.34% | 57.96% | 8.08% | 4.21% |
| Baseline proposals | 4.30% | 66.50% | 8.08% | 4.21% |
| U-Net proposals | 81.97% | 75.60% | 78.66% | 64.82% |
| Baseline supported | undefined | 0.00% | 0.00% | 0.00% |
| U-Net supported | undefined | 0.00% | 0.00% | 0.00% |

The pretrained model finds useful candidates, but the verified pipeline has zero recall. Automatic registration is unreliable on all eight scenes; the existing gate prevents promotion to supported change. No thresholds or production logic were relaxed. Removing 59,847 U-Net false-positive pixels also removes all 272,155 true-positive proposal pixels. All eight U-Net scenes have every inspected candidate in review; baseline has two such scenes and eight with zero supported pixels. Removed pixels also include small/omitted/filtered regions, not only abstention.

All selected scenes, with proposal F1 and U-Net region accounting:

| Scene | Baseline F1 | U-Net F1 | U-Net inspected / omitted | Registration reliable | Supported pixels (both) |
|---|---:|---:|---:|---|---:|
| test_103.png | 4.57% | 41.53% | 8 / 0 | no | 0 |
| test_112.png | 2.07% | 61.73% | 5 / 0 | no | 0 |
| test_113.png | 9.64% | 77.29% | 24 / 7 | no | 0 |
| test_13.png | 12.89% | 88.13% | 24 / 48 | no | 0 |
| test_30.png | 10.66% | 85.90% | 24 / 31 | no | 0 |
| test_37.png | 18.24% | 60.63% | 24 / 43 | no | 0 |
| test_52.png | 7.93% | 93.16% | 24 / 5 | no | 0 |
| test_88.png | 0.09% | 27.26% | 2 / 0 | no | 0 |

This evaluates GeoAlibi's existing registration, tiling and proposal postprocessing, not a reproduction of the model author's published benchmark protocol. It is not comparable to the earlier selected 256px demo-crop score as a controlled before/after improvement. The eight-scene result is now observed development evidence and must not become a tuning target presented later as untouched holdout accuracy. No confidence intervals, geographic independence or calibrated-risk claim is made.

Next: obtain independent stationary-point annotations/review to test registration validity before changing any acceptance policy. Preserve this result as a negative end-to-end baseline. Fresh corrected-geometry Meta validation still requires a securely supplied credential, billing access and reconciliation of the historical $0.54 reservation. This run incurred $0 observed API cost and $0 new reservations.

Synthetic acquisition/unit-test images are not evaluation samples.

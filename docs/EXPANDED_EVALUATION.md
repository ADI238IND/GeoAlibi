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

Results are added only after both frozen runs complete. Synthetic acquisition/unit-test images are not evaluation samples.

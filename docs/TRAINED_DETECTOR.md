# Trained proposal integration and first real-image diagnostic

## Model provenance

GeoAlibi now offers an optional early-fusion U-Net/ResNet-50 trained on LEVIR-CD by Isaac Corley, Caleb Robinson and Anthony Ortiz for **A Change Detection Reality Check** (2024), https://arxiv.org/abs/2402.06994.

- Author code: https://github.com/isaaccorley/a-change-detection-reality-check (MIT).
- Author weights: https://huggingface.co/isaaccorley/a-change-detection-reality-check (model card: CC-BY-4.0).
- Pinned weight repository revision: `52e7fdb42ddf4e89661c56ef8b8900528a20df0a`.
- Weight path: `levir-cd/unet_resnet50.ckpt`.
- SHA-256: `fd113f39d69c45cddee18d780ac8392f3d96dfc097402cd6c2b77b69565629e9`.
- Normalization verified from the authors' `src/datasets/levircd.py`: RGB / 127.5 − 1. Before and after are concatenated into six channels. Two output classes; class 1 is change.

The integration independently instantiates the architecture using segmentation-models-pytorch. No original author Python source, checkpoint or dataset image is bundled. Attribution must be retained with model use. The weights' stated license does not override any imagery terms.

Loading verifies size/hash and uses `torch.load(..., weights_only=True)`. There is no unsafe fallback. The encoder does not download ImageNet weights. Non-overlapping 256-pixel tiles are used; boundary tiles use reflect padding and crop back to original dimensions. Scores are not calibrated confidence. Tiling context/seams still require further evaluation.

## Local setup

Install a CPU build of PyTorch on your machine (or an appropriate build for your GPU), then:

```bash
python -m pip install -e '.[detector]'
python scripts/download_detector.py
python -m uvicorn geoalibi.app:app --host 127.0.0.1 --port 8080
```

Select **Trained U-Net · LEVIR-CD** under Proposal detector. If the dependencies/checkpoint are missing, the option is disabled. Explicit API requests fail instead of silently switching to the RGB baseline. The first inference verifies and loads the checkpoint; later requests reuse the in-memory model.

Checkpoint and dataset folders are gitignored. This work uses local CPU inference, not Meta API credits. See TRAINED_DETECTOR_ENV.txt for this run's tested versions.

## Real-image development sample

Seven publicly provided `test_*` image pairs with labels were downloaded from LEVIR author Hao Chen's BIT_CD demo repository. All matching test filenames in that folder were used; train/validation demo filenames and one test filename lacking a label were excluded. These are selected demonstration examples, not a random sample or an independently curated benchmark. Input hashes are recorded in REAL_SAMPLE_MANIFEST.json.

LEVIR-CD's official page restricts images/annotations to academic use and prohibits commercial use: https://justchenhao.github.io/LEVIR/. Google Earth terms also apply. This repository distributes hashes and results only, not imagery. A public commercial demo needs appropriately licensed imagery or permission.

With thresholds fixed from the earlier illustrative build, this diagnostic produced:

| Output | Precision | Recall | F1 | IoU |
| --- | ---: | ---: | ---: | ---: |
| Raw RGB differences | 20.62% | 65.37% | 31.35% | 18.59% |
| Trained proposals | 91.74% | 91.15% | 91.44% | 84.24% |
| Automatically supported pixels | Undefined: none accepted | 0% | 0% | 0% |

**The verifier abstained on every inspected candidate.** This is a failed automatic-verification result, not a precision improvement. The RGB registration gate found insufficient correspondences on these small, heavily changed patches. A SIFT diagnostic also found too few ratio-tested matches; it was not added as a supposed fix and thresholds were not relaxed to improve the reported result. The UI now explicitly reports all-candidate abstention and lets users inspect the trained proposal mask separately.

The proposal performance is encouraging but cannot be generalized from seven selected demos. The RGB and pretrained numbers are from the same processed samples. Rejected and review pixels count as negative in supported-mask metrics. Undefined precision is represented as JSON null. REAL_SAMPLE_EVALUATION.json contains counts, settings, individual image hashes, alignment diagnostics and warnings.

Reproduce with an authorized local copy of those same A/B/label files:

```bash
python scripts/evaluate.py datasets/levir-author-demo --detector unet --output benchmark-results.json
```

## Next work

1. Validate registration using larger surrounding imagery and authoritative co-registration metadata; do not infer it merely from a good change-model score.
2. Audit changes against an independent, licensed full split with separate development and evaluation sets.
3. Measure selective risk and review coverage jointly with recall. An all-review system cannot be advertised as automatically verified.
4. Add trained-model nuisance stress tests, temporal-swap consistency, seam tests, and difficult-cloud/seasonal examples.
5. Validate SAM building masks and Muse interpretations on appropriately licensed real imagery.

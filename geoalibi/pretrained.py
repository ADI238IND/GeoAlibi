"""Optional author-released early-fusion U-Net. No unsafe checkpoint loading."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

REVISION = "52e7fdb42ddf4e89661c56ef8b8900528a20df0a"
SHA256 = "fd113f39d69c45cddee18d780ac8392f3d96dfc097402cd6c2b77b69565629e9"
SIZE = 260664058
URL = f"https://huggingface.co/isaaccorley/a-change-detection-reality-check/resolve/{REVISION}/levir-cd/unet_resnet50.ckpt"
NAME = "Corley et al. LEVIR-CD U-Net / ResNet-50"
PROVENANCE = {"name": NAME, "revision": REVISION, "sha256": SHA256, "weights_license": "CC-BY-4.0",
              "authors": "Isaac Corley, Caleb Robinson, Anthony Ortiz (2024)",
              "source": "https://huggingface.co/isaaccorley/a-change-detection-reality-check",
              "preprocessing_source": "https://github.com/isaaccorley/a-change-detection-reality-check/blob/main/src/datasets/levircd.py",
              "preprocessing": "RGB / 127.5 - 1; before RGB followed by after RGB; 256px tiles; class 1 argmax",
              "note": "Model softmax scores are not calibrated confidence. External pretrained model; not trained by GeoAlibi."}


def checkpoint_path():
    return Path(os.getenv("GEOALIBI_CHECKPOINT", "models/unet_resnet50.ckpt"))


def available():
    return checkpoint_path().is_file() and all(importlib.util.find_spec(m) is not None for m in ["torch", "torchvision", "segmentation_models_pytorch"])


def verify(path):
    if not path.is_file() or path.stat().st_size != SIZE:
        raise ValueError("Trained detector checkpoint is missing or has an unexpected size. Run scripts/download_detector.py.")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != SHA256:
        raise ValueError("Trained detector checkpoint hash mismatch; inference refused.")


@lru_cache(maxsize=1)
def load_model(path_string, size, modified_ns):
    import torch
    import segmentation_models_pytorch as smp
    path = Path(path_string)
    verify(path)
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    # weights_only=True refuses arbitrary pickle execution. Never auto-fallback.
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    state = checkpoint.get("state_dict", checkpoint)
    state = {key.removeprefix("model."): value for key, value in state.items() if key.startswith("model.")}
    if not state:
        raise ValueError("Author checkpoint has no model state_dict entries.")
    model = smp.Unet(encoder_name="resnet50", encoder_weights=None, in_channels=6, classes=2)
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def infer_tiles(a, b, predict, tile=256):
    """Crop boundary tiles after reflect padding; do not resize or leave seams unfilled."""
    if a.shape != b.shape:
        raise ValueError("Trained detector requires matching RGB dimensions.")
    h, w = a.shape[:2]
    scores = np.empty((h, w), np.float32)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            aa, bb = a[y:y+tile, x:x+tile], b[y:y+tile, x:x+tile]
            th, tw = aa.shape[:2]
            pad = ((0, tile-th), (0, tile-tw), (0, 0))
            aa, bb = np.pad(aa, pad, mode="reflect"), np.pad(bb, pad, mode="reflect")
            tensor = np.concatenate([aa, bb], axis=2).transpose(2, 0, 1).astype(np.float32) / 127.5 - 1
            probability = np.asarray(predict(tensor), np.float32)
            if probability.shape != (tile, tile) or not np.isfinite(probability).all():
                raise ValueError("Detector returned invalid dimensions or nonfinite scores.")
            scores[y:y+th, x:x+tw] = probability[:th, :tw]
    return scores


def propose(a, b):
    if not available():
        raise ValueError("Trained detector is not configured. Install the detector extras and download the pinned checkpoint.")
    import torch
    path = checkpoint_path().resolve()
    stat = path.stat()
    model = load_model(str(path), stat.st_size, stat.st_mtime_ns)
    def predict(tensor):
        with torch.inference_mode():
            output = model(torch.from_numpy(tensor[None]))
            return torch.softmax(output, dim=1)[0, 1].numpy()
    scores = infer_tiles(a, b, predict)
    return scores > .5, scores

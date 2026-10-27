"""Run a held-out A/B/label benchmark. No API calls, no training, no automatic downloads."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from geoalibi.vision import decode_image, investigate


def metrics(counts):
    tp, fp, fn, tn = counts
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": tp / max(1, tp + fp), "recall": tp / max(1, tp + fn),
            "f1": 2 * tp / max(1, 2 * tp + fp + fn), "iou": tp / max(1, tp + fp + fn)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Folder containing A/, B/, label/ with matching filenames")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results.json"))
    parser.add_argument("--threshold", type=float, default=.12)
    parser.add_argument("--min-area", type=int, default=70)
    parser.add_argument("--limit", type=int, default=0, help="0 = all pairs; positive = explicitly limited subset")
    args = parser.parse_args()
    paths = sorted(p for p in (args.dataset / "A").iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    if args.limit:
        paths = paths[:args.limit]
    if not paths:
        parser.error("No image pairs found.")
    totals = {"raw": [0, 0, 0, 0], "supported": [0, 0, 0, 0]}
    pairs = []
    for path in paths:
        a = decode_image(path.read_bytes())
        b = decode_image((args.dataset / "B" / path.name).read_bytes())
        with Image.open(args.dataset / "label" / path.name) as im:
            # Binary labels only. Nonzero is change; multiclass maps need explicit remapping.
            label = np.asarray(im.convert("L"))
            if len(np.unique(label)) > 2:
                raise ValueError(f"{path.name}: label must be binary; remap multiclass labels explicitly.")
            label = cv2.resize(label, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        result = investigate(a, b, threshold=args.threshold, min_area=args.min_area)
        for name, key in [("raw", "raw_mask"), ("supported", "supported_mask")]:
            mask = result.images[key] > 0
            counts = [int((mask & label).sum()), int((mask & ~label).sum()), int((~mask & label).sum()), int((~mask & ~label).sum())]
            totals[name] = [x + y for x, y in zip(totals[name], counts)]
        pairs.append({"file": path.name, "hash": result.report["input_hash"], "elapsed_ms": result.report["elapsed_ms"], "counts": result.report["counts"]})
        print(f"Evaluated {path.name}", flush=True)
    output = {"dataset": str(args.dataset), "pairs": len(pairs), "subset_limit": args.limit, "threshold": args.threshold, "min_area": args.min_area,
              "metrics": {k: metrics(v) for k, v in totals.items()}, "pair_results": pairs,
              "note": "Pixel metrics in processed image coordinates, maximum side 1024. Rejected/abstained pixels count as negative. No calibration or real-world deployment claim."}
    args.output.write_text(json.dumps(output, indent=2))
    print(json.dumps(output["metrics"], indent=2))


if __name__ == "__main__":
    main()

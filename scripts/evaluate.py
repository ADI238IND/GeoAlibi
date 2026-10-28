"""Run a held-out A/B/label benchmark. No API calls, no training, no automatic downloads."""
import argparse
import json
from pathlib import Path

import numpy as np

from geoalibi.vision import decode_image, investigate
from geoalibi.evaluation import load_landmark_manifest, checked_landmarks, decode_binary_label


def metrics(counts):
    tp, fp, fn, tn = counts
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / max(1, 2 * tp + fp + fn), "iou": tp / max(1, tp + fp + fn)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Folder containing A/, B/, label/ with matching filenames")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results.json"))
    parser.add_argument("--threshold", type=float, default=.12)
    parser.add_argument("--min-area", type=int, default=70)
    parser.add_argument("--detector", choices=["baseline", "unet"], default="baseline")
    parser.add_argument("--limit", type=int, default=0, help="0 = all pairs; positive = explicitly limited subset")
    parser.add_argument("--landmarks", type=Path, help="Reviewed image-hash-bound manifest; run assisted and automatic arms separately")
    args = parser.parse_args()
    annotations, annotation_hash = load_landmark_manifest(args.landmarks) if args.landmarks else ({}, None)
    paths = sorted(p for p in (args.dataset / "A").iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    if args.limit:
        paths = paths[:args.limit]
    if not paths:
        parser.error("No image pairs found.")
    if args.landmarks and set(annotations) != {p.name for p in paths}:
        parser.error("Manifest must match the exact evaluated filename set (including --limit).")
    totals = {"raw_rgb": [0, 0, 0, 0], "proposals": [0, 0, 0, 0], "supported": [0, 0, 0, 0]}
    assisted_totals = {k: [0, 0, 0, 0] for k in totals}
    assisted_pairs = []
    pairs = []
    for path in paths:
        before_bytes = path.read_bytes()
        after_bytes = (args.dataset / "B" / path.name).read_bytes()
        label_bytes = (args.dataset / "label" / path.name).read_bytes()
        landmarks = checked_landmarks(annotations[path.name], before_bytes, after_bytes, label_bytes) if args.landmarks else None
        a = decode_image(before_bytes)
        b = decode_image(after_bytes)
        label = decode_binary_label(label_bytes, before_bytes, a.shape[:2])
        from geoalibi.pretrained import propose
        result = investigate(a, b, threshold=args.threshold, min_area=args.min_area, detector_fn=propose if args.detector=="unet" else None)
        for name, key in [("raw_rgb", "raw_mask"), ("proposals", "proposal_mask"), ("supported", "supported_mask")]:
            mask = result.images[key] > 0
            counts = [int((mask & label).sum()), int((mask & ~label).sum()), int((~mask & label).sum()), int((~mask & ~label).sum())]
            totals[name] = [x + y for x, y in zip(totals[name], counts)]
        pairs.append({"file": path.name, "hash": result.report["input_hash"], "elapsed_ms": result.report["elapsed_ms"], "counts": result.report["counts"],
                      "alignment": result.report["alignment"], "candidate_pixels": int((result.images['proposal_mask']>0).sum()),
                      "accepted_pixels": int((result.images['supported_mask']>0).sum()), "warnings": result.report['warnings']})
        if landmarks is not None:
            assisted = investigate(a, b, threshold=args.threshold, min_area=args.min_area,
                                   detector_fn=propose if args.detector == "unet" else None, landmarks=landmarks)
            per_pair = {}
            for name, key in [("raw_rgb", "raw_mask"), ("proposals", "proposal_mask"), ("supported", "supported_mask")]:
                mask = assisted.images[key] > 0
                counts = [int((mask & label).sum()), int((mask & ~label).sum()), int((~mask & label).sum()), int((~mask & ~label).sum())]
                assisted_totals[name] = [x + y for x, y in zip(assisted_totals[name], counts)]
                per_pair[name] = metrics(counts)
            assisted_pairs.append({"file": path.name, "metrics": per_pair, "alignment": assisted.report["alignment"],
                                   "counts": assisted.report["counts"], "elapsed_ms": assisted.report["elapsed_ms"]})
        print(f"Evaluated {path.name}", flush=True)
    output = {"dataset": str(args.dataset), "pairs": len(pairs), "subset_limit": args.limit, "threshold": args.threshold, "min_area": args.min_area, "detector": args.detector,
              "metrics": {k: metrics(v) for k, v in totals.items()}, "pair_results": pairs,
              "note": "Pixel metrics in processed image coordinates, maximum side 1024. Rejected/abstained pixels count as negative. Precision/recall are null when their denominator is zero. No calibration or real-world deployment claim."}
    if args.landmarks:
        output["assisted"] = {"manifest_sha256": annotation_hash, "metrics": {k: metrics(v) for k, v in assisted_totals.items()},
                              "pair_results": assisted_pairs,
                              "note": "Conditional on supplied reviewed correspondences. Reviewer identities are recorded assertions, not authenticated. Full processed footprint scored; invalid borders count as negative. Labels must be in BEFORE coordinates. No automatic-registration claim."}
    args.output.write_text(json.dumps(output, indent=2))
    print(json.dumps(output["metrics"], indent=2))


if __name__ == "__main__":
    main()


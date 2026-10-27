"""Known-no-change stress tests on real source images. No API calls or label tuning."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from geoalibi.pretrained import propose
from geoalibi.vision import decode_image, investigate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path)
    parser.add_argument("--output", type=Path, default=Path("stress-results.json"))
    args = parser.parse_args()
    rows = []
    for p in sorted(args.images.glob("*.png")):
        a = decode_image(p.read_bytes())
        h, w = a.shape[:2]
        transforms = {"identical": a.copy(), "global_illumination": np.clip(a.astype(float)*.75+12, 0, 255).astype(np.uint8),
                      "translation_4px_-3px": cv2.warpAffine(a, np.float32([[1,0,4],[0,1,-3]]), (w,h), borderMode=cv2.BORDER_REFLECT)}
        for name, b in transforms.items():
            r = investigate(a, b, detector_fn=propose)
            rows.append({"source": p.name, "transform": name, "hash": r.report['input_hash'], "proposal_false_pixels": int((r.images['proposal_mask']>0).sum()),
                         "accepted_false_pixels": int((r.images['supported_mask']>0).sum()), "counts": r.report['counts'], "alignment": r.report['alignment']})
            print(p.name, name, rows[-1]['proposal_false_pixels'], rows[-1]['accepted_false_pixels'], flush=True)
    if not rows:
        parser.error("No PNG inputs found.")
    args.output.write_text(json.dumps({"purpose": "Known-no-change transformed-image stress diagnostic. Transformations are not independent acquisitions. Detector receives the registered after image.",
        "configuration": {"threshold": .12, "min_area": 70, "model": "pinned LEVIR-CD U-Net"}, "results": rows,
        "summary": {"cases": len(rows), "proposal_false_pixels": sum(x['proposal_false_pixels'] for x in rows), "accepted_false_pixels": sum(x['accepted_false_pixels'] for x in rows)}}, indent=2)+'\n')


if __name__ == "__main__":
    main()

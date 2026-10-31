"""Score a replay-checked LoFTR audit against image-bound independent annotations."""
import argparse
import hashlib
import json
from pathlib import Path

from geoalibi.evaluation import load_landmark_manifest, checked_landmarks
from geoalibi.independent_alignment import evaluate_reviewed_alignment
from geoalibi.vision import decode_image
from replay_loftr import replay_report


def evaluate(audit_path, annotation_path, dataset):
    raw = audit_path.read_bytes()
    audit = json.loads(raw)
    replay_report(audit)
    annotations, annotation_hash = load_landmark_manifest(annotation_path)
    # Validate exact coverage and audit hashes before accessing any image files.
    report = evaluate_reviewed_alignment(audit, annotations)
    for name, record in annotations.items():
        before = (dataset / 'A' / name).read_bytes()
        after = (dataset / 'B' / name).read_bytes()
        label = (dataset / 'label' / name).read_bytes()
        checked_landmarks(record, before, after, label)
        if any(decode_image(data).shape[:2] != (256, 256) for data in (before, after)):
            raise ValueError('This audit requires the original 256px processed inputs.')
    return {**report, 'audit_sha256': hashlib.sha256(raw).hexdigest(),
            'annotation_manifest_sha256': annotation_hash}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audit', type=Path)
    parser.add_argument('annotations', type=Path)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.audit, args.annotations, args.dataset)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(f"Scored {report['pair_count']} pairs; no model/API calls and no transform refitting.")

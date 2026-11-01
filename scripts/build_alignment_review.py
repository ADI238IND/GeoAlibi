"""Generate a private offline blind landmark-review pack from frozen inputs."""
import argparse
from pathlib import Path
from geoalibi.alignment_review import build_review

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--dataset-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = build_review(args.dataset, args.dataset_manifest, args.output)
    print(f"Built {len(summary['pairs'])} blind pairs; open review.html locally. No model/API calls.")

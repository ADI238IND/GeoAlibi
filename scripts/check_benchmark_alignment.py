"""Score frozen production transforms on all independently reviewed landmarks; never refit."""
import argparse
import json
from pathlib import Path
from geoalibi.alignment_review import score_benchmark

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('benchmark', type=Path)
    parser.add_argument('annotations', type=Path)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--dataset-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new report path.')
    report = score_benchmark(args.benchmark, args.annotations, args.dataset, args.dataset_manifest)
    serialized = json.dumps(report, indent=2, allow_nan=False) + '\n'
    with args.output.open('x') as stream:
        stream.write(serialized)
    print(f"Scored {report['pair_count']} complete pairs; no refitting, model calls or production promotion.")

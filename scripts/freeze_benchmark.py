"""Freeze a benchmark split before inference; no API/model calls or downloads."""
import argparse
import json
from pathlib import Path
from geoalibi.benchmark_manifest import freeze_dataset

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--description', required=True, help='Source, selection protocol and image terms; does not certify them')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = freeze_dataset(args.dataset, args.description, args.limit)
    # Never silently replace a preregistered manifest.
    with args.output.open('x') as output:
        output.write(json.dumps(manifest, indent=2) + '\n')
    print(f"Frozen {len(manifest['pairs'])} pairs. Store this manifest before evaluation; hashes do not prove a held-out split.")

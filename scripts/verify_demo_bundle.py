"""Verify an extracted offline rehearsal using the matching source checkout; no model/API calls."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

from geoalibi.demo_verification import verify_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--expected-source-sha256', help='Source manifest SHA-256 obtained independently from the matching checkout/CI')
    args = parser.parse_args()
    try:
        result = verify_bundle(args.directory, args.expected_source_sha256)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError, zipfile.BadZipFile) as error:
        print('Bundle verification failed: ' + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

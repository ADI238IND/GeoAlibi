"""Check an offline sequence of original + continuation evidence packets; no API calls."""
import argparse
import json
from pathlib import Path
from geoalibi.inspection_chain import verify_chain

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packets', type=Path, nargs='+', help='Unordered packets from one original-to-tip path; include every ancestor')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): parser.error('Output exists; use a new path to preserve prior evidence.')
    report = verify_chain(args.packets)
    serialized = json.dumps(report, indent=2, allow_nan=False) + '\n'
    with args.output.open('x') as stream: stream.write(serialized)
    state = 'complete' if report['inspection_complete'] else 'partial'
    print(f"Valid {state} inspection: {report['inspected_regions']}/{report['eligible_regions']} eligible regions. Real-world change remains unverified.")

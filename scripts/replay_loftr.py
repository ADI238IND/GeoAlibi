"""Check stored LoFTR correspondences without downloading or loading a model."""
import argparse
import hashlib
import json
from pathlib import Path

from geoalibi.matcher_audit import replay_matches


def replay_report(report):
    if report.get('schema') != 'geoalibi-loftr-audit-v1' or report.get('complete') is not True:
        raise ValueError('A complete v1 audit is required')
    digest = hashlib.sha256(Path('geoalibi/correspondence_checks.py').read_bytes()).hexdigest()
    if report['geometry_source_sha256'] != digest:
        raise ValueError('Geometry implementation differs from recorded version')
    cases = ('actual', 'mismatched', 'same', 'translated')
    expected = {(name[2:], case) for name in report['input_sha256'] if name.startswith('A/') for case in cases}
    seen = set()
    summary = {case: {'cases': 0, 'candidate_passes': 0} for case in cases}
    for row in report['results']:
        key = (row['file'], row['case'])
        if key not in expected or key in seen:
            raise ValueError('Unexpected or duplicate audit case')
        seen.add(key)
        geometry = replay_matches(row['audit'])
        summary[row['case']]['cases'] += 1
        summary[row['case']]['candidate_passes'] += int(geometry['candidate_pass'])
    if seen != expected or summary != report['summary']:
        raise ValueError('Missing cases or inconsistent summary')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    print(json.dumps(replay_report(json.loads(args.report.read_text())), indent=2))
    print('Internal replay only: this does not authenticate images, model output or alignment truth.')

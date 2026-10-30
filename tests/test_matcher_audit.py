import copy
import hashlib
from pathlib import Path

import numpy as np
import pytest

from geoalibi.matcher_audit import audit_matches, replay_matches
from scripts.replay_loftr import replay_report


def points():
    return np.array([(x, y) for y in (30, 90, 150, 210) for x in (30, 90, 150, 210)])


def test_raw_match_replay_and_holdout_mapping():
    source = points()
    record = audit_matches(source, source + [4, -3], np.ones(16))
    assert replay_matches(record)['candidate_pass']
    assert record['retained_indices'] == list(range(16))
    altered = copy.deepcopy(record)
    altered['geometry']['candidate_pass'] = False
    with pytest.raises(ValueError, match='differs'):
        replay_matches(altered)


def test_threshold_retains_raw_outputs_and_duplicate_abstention():
    source = points()
    confidence = np.ones(16)
    confidence[0] = .79
    record = audit_matches(source, source, confidence)
    assert len(record['confidence']) == 16
    assert record['retained_indices'] == list(range(1, 16))
    assert not replay_matches(record)['candidate_pass']
    source[1] = source[0]
    record = audit_matches(source, source, np.ones(16))
    assert not replay_matches(record)['candidate_pass']
    assert 'Repeated' in record['geometry']['reason']


@pytest.mark.parametrize('confidence', [[float('nan')]*16, [1.1]*16, [1]*15])
def test_invalid_predictions_rejected(confidence):
    with pytest.raises(ValueError):
        audit_matches(points(), points(), confidence)


def test_report_requires_complete_unique_cases_and_correct_summary():
    record = audit_matches(points(), points(), np.ones(16))
    cases = ('actual', 'mismatched', 'same', 'translated')
    report = {'schema': 'geoalibi-loftr-audit-v1', 'complete': True,
              'geometry_source_sha256': hashlib.sha256(Path('geoalibi/correspondence_checks.py').read_bytes()).hexdigest(),
              'input_sha256': {'A/example.png': 'fixture'},
              'results': [{'file': 'example.png', 'case': case, 'audit': record} for case in cases],
              'summary': {case: {'cases': 1, 'candidate_passes': 1} for case in cases}}
    assert replay_report(report) == report['summary']
    for mutate in (lambda r: r.update(complete=False),
                   lambda r: r['results'].pop(),
                   lambda r: r['results'].append(r['results'][0]),
                   lambda r: r['summary']['actual'].update(candidate_passes=0)):
        altered = copy.deepcopy(report)
        mutate(altered)
        with pytest.raises(ValueError):
            replay_report(altered)


def test_empty_output_abstains_and_flat_coordinates_fail():
    assert not replay_matches(audit_matches([], [], []))['candidate_pass']
    with pytest.raises(ValueError):
        audit_matches([1, 2], [1, 2], [1])

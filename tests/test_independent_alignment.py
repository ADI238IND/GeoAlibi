import copy

import numpy as np
import pytest

from geoalibi.independent_alignment import landmark_errors, evaluate_reviewed_alignment


def landmarks(offset=(4, -3)):
    source = np.array([(30, 30), (210, 30), (30, 210), (210, 210), (90, 90), (150, 150)])
    return np.concatenate([source, source + offset], axis=1).tolist()


def test_frozen_transform_is_scored_not_refitted():
    matrix = [[1, 0, 4], [0, 1, -3]]
    correct = landmark_errors(matrix, landmarks())
    assert correct['transform_rms_px'] == 0
    assert correct['identity_rms_px'] == 5
    wrong = landmark_errors(matrix, landmarks((12, -3)))
    assert wrong['transform_rms_px'] == 8
    assert wrong['fraction_within_2_5px'] == 0
    assert matrix == [[1, 0, 4], [0, 1, -3]]


def test_missing_transform_remains_abstained():
    result = landmark_errors(None, landmarks())
    assert result['transform_rms_px'] is None
    assert result['identity_rms_px'] == 5


@pytest.mark.parametrize('bad', [[], [[1, 2, 3, 4]] * 6,
    [[float('nan'), 1, 2, 3]] * 6, [[300, 1, 2, 3]] * 6,
    [[x, x, x, x] for x in range(10, 70, 10)]])
def test_invalid_or_clustered_landmarks_fail(bad):
    with pytest.raises(ValueError):
        landmark_errors(None, bad)


def fixture():
    name = 'example.png'
    hashes = {prefix + name: str(i) * 64 for i, prefix in enumerate(('A/', 'B/', 'label/'))}
    record = {'file': name, 'collection_basis': 'independent-original-image-review',
              'annotator': 'first', 'reviewer': 'second', 'landmarks': landmarks(),
              'before_sha256': hashes['A/' + name], 'after_sha256': hashes['B/' + name],
              'label_sha256': hashes['label/' + name]}
    audit = {'input_sha256': hashes, 'results': [{'file': name, 'case': 'actual',
             'audit': {'geometry': {'candidate_pass': False, 'matrix': [[1, 0, 4], [0, 1, -3]]}}}]}
    return audit, {name: record}


def test_review_does_not_promote_failed_candidate():
    audit, records = fixture()
    report = evaluate_reviewed_alignment(audit, records)
    assert report['pairs'][0]['transform_rms_px'] == 0
    assert report['candidate_pass_count'] == 0
    assert report['with_transform_count'] == 1
    assert 'reliable' not in report['pairs'][0]


def test_subset_wrong_image_and_model_derived_evidence_rejected():
    audit, records = fixture()
    with pytest.raises(ValueError, match='exactly'):
        evaluate_reviewed_alignment(audit, {})
    for field, value in [('before_sha256', 'f' * 64), ('collection_basis', 'model-matches')]:
        wrong = copy.deepcopy(records)
        wrong['example.png'][field] = value
        with pytest.raises(ValueError):
            evaluate_reviewed_alignment(audit, wrong)


def test_cli_checks_image_bytes_before_writing_report(tmp_path):
    import hashlib
    import json
    import subprocess
    import sys
    from pathlib import Path
    from PIL import Image
    from geoalibi.matcher_audit import audit_matches

    name = 'fixture.png'
    hashes = {}
    for folder in ('A', 'B', 'label'):
        directory = tmp_path / folder
        directory.mkdir()
        Image.new('L', (256, 256)).save(directory / name)
        hashes[folder + '/' + name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
    source = np.array([(x, y) for x in (30, 90, 150, 210) for y in (30, 90, 150, 210)])
    matches = audit_matches(source, source + [4, -3], np.ones(16))
    cases = ('actual', 'mismatched', 'same', 'translated')
    audit = {'schema': 'geoalibi-loftr-audit-v1', 'complete': True,
             'geometry_source_sha256': hashlib.sha256(Path('geoalibi/correspondence_checks.py').read_bytes()).hexdigest(),
             'input_sha256': hashes,
             'results': [{'file': name, 'case': case, 'audit': matches} for case in cases],
             'summary': {case: {'cases': 1, 'candidate_passes': 1} for case in cases}}
    annotation = {'file': name, 'coordinate_space': 'processed-original-images',
                  'collection_basis': 'independent-original-image-review',
                  'annotator': 'fixture-author', 'reviewer': 'fixture-reviewer',
                  'landmarks': landmarks(), 'before_sha256': hashes['A/' + name],
                  'after_sha256': hashes['B/' + name], 'label_sha256': hashes['label/' + name]}
    audit_path, annotation_path, output = (tmp_path / p for p in ('audit.json', 'review.json', 'output.json'))
    audit_path.write_text(json.dumps(audit))
    annotation_path.write_text(json.dumps({'schema': 'geoalibi-landmarks-v1', 'pairs': [annotation]}))
    command = [sys.executable, 'scripts/check_independent_alignment.py', str(audit_path),
               str(annotation_path), str(tmp_path), '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report['pairs'][0]['transform_rms_px'] == 0
    assert report['audit_sha256'] == hashlib.sha256(audit_path.read_bytes()).hexdigest()
    output.unlink()
    (tmp_path / 'A' / name).write_bytes(b'changed bytes')
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'mismatch' in result.stderr
    assert not output.exists()

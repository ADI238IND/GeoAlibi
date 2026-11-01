"""Check arithmetic and binding of saved diagnostics; do not rerun or infer accuracy."""
import json
from pathlib import Path

import pytest
from geoalibi.release_evidence import FILES, saved_evidence


def source_copy(tmp_path):
    for path in FILES.values():
        target = tmp_path / path; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(path).read_bytes())
    return tmp_path


def test_saved_results_are_derived_with_undefined_precision_and_visible_missed_changes():
    result = saved_evidence(Path('.'))
    arm = result['arms']['unet']
    assert result['pair_count'] == 8
    assert arm['metrics']['proposals']['tp'] == 272155
    assert arm['metrics']['supported']['precision'] is None
    assert arm['metrics']['supported']['recall'] == 0
    assert arm['verification_tradeoff']['removed_true_positive_pixels'] == 272155
    assert arm['verification_tradeoff']['removed_false_positive_pixels'] == 59847
    assert arm['registration_flagged_reliable_pairs'] == 0
    assert result['submission_readiness'] == 'not established'


@pytest.mark.parametrize('change', ['binding', 'subset', 'duplicate', 'metric', 'pooled-count', 'review-count', 'transition', 'scene-transition', 'source', 'alignment', 'negative-count', 'settings', 'model'])
def test_inconsistent_saved_evidence_cannot_enter_demo(tmp_path, change):
    root = source_copy(tmp_path)
    path = root / FILES['unet']; data = json.loads(path.read_text())
    row = data['pair_results'][0]
    if change == 'binding': data['dataset_manifest_sha256'] = '0' * 64
    elif change == 'subset': data['pair_results'].pop()
    elif change == 'duplicate': data['pair_results'][1] = row
    elif change == 'metric': data['metrics']['supported']['precision'] = 1
    elif change == 'pooled-count': data['metrics']['proposals']['tp'] += 1
    elif change == 'review-count': data['all_candidates_abstained_pairs'] -= 1
    elif change == 'transition': data['verification_tradeoff']['removed_true_positive_pixels'] -= 1
    elif change == 'scene-transition': row['verification_tradeoff']['removed_true_positive_pixels'] -= 1
    elif change == 'source': row['source_hashes']['A_sha256'] = '0' * 64
    elif change == 'alignment': row['alignment']['matrix'][0][2] += 1
    elif change == 'settings': data['threshold'] = .13
    elif change == 'model': row['model_provenance']['sha256'] = '0' * 64
    elif change == 'negative-count': row['metrics']['proposals']['fp'] = -1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError): saved_evidence(root)

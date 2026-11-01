"""Contract fixtures only; no satellite or independent-annotation accuracy claims."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from geoalibi.alignment_review import build_review, score_benchmark
from geoalibi.benchmark_manifest import freeze_dataset


def review_fixture(tmp_path, count=2, side=256):
    root = tmp_path / 'dataset'
    for folder in ('A', 'B', 'label'):
        (root / folder).mkdir(parents=True)
        for i in range(count):
            if folder == 'label':
                (root / folder / f'pair{i}.png').write_bytes(b'PRIVATE-LABEL-PIXELS-NOT-AN-IMAGE')
            else:
                Image.new('RGB', (side, side), (30 + i, 80, 120)).save(root / folder / f'pair{i}.png')
    manifest = tmp_path / 'inputs.json'
    data = freeze_dataset(root, 'Generated test fixture, not a real benchmark.')
    manifest.write_text(json.dumps(data))
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    source = [(x * side / 256, y * side / 256) for x, y in [(30, 30), (210, 30), (30, 210), (210, 210), (90, 90), (150, 150)]]
    annotations = {'schema': 'geoalibi-landmarks-v1', 'dataset_manifest_sha256': digest, 'pairs': []}
    benchmark = {'dataset_frozen': True, 'dataset_manifest_sha256': digest, 'subset_limit': 0,
                 'pairs': count, 'pair_results': []}
    for r in data['pairs']:
        annotations['pairs'].append({'file': r['file'], 'coordinate_space': 'processed-original-images',
            'annotator': 'fixture-author', 'reviewer': 'fixture-reviewer', 'reviewed': True,
            'collection_basis': 'independent-original-image-review',
            'before_sha256': r['A_sha256'], 'after_sha256': r['B_sha256'], 'label_sha256': r['label_sha256'],
            'landmarks': [[x, y, x + 4, y - 3] for x, y in source]})
        benchmark['pair_results'].append({'file': r['file'], 'source_hashes': r,
            'alignment': {'reliable': False, 'method': 'fixture', 'matrix': [[1, 0, 4], [0, 1, -3]]}})
    audit_path, annotation_path = tmp_path / 'benchmark.json', tmp_path / 'reviewed.json'
    audit_path.write_text(json.dumps(benchmark)); annotation_path.write_text(json.dumps(annotations))
    return root, manifest, audit_path, annotation_path


def test_blind_bundle_has_only_original_images_and_hash_metadata(tmp_path):
    root, manifest, _, _ = review_fixture(tmp_path)
    output = tmp_path / 'blind'
    summary = build_review(root, manifest, output)
    page = (output / 'review.html').read_text()
    assert 'PRIVATE-LABEL-PIXELS' not in page
    assert 'UFJJVkFURS1MQUJFTC1QSVhFTFM' not in page  # not embedded as base64 either
    assert page.count('data:image/png;base64,') == 4
    assert '/* REVIEW_TASK */' not in page
    assert summary['html_sha256'] == hashlib.sha256((output / 'review.html').read_bytes()).hexdigest()
    assert all('before' not in pair and 'after' not in pair for pair in summary['pairs'])
    with pytest.raises(ValueError, match='Output exists'):
        build_review(root, manifest, output)


def test_blind_bundle_rejects_changed_bytes_before_publish(tmp_path):
    root, manifest, _, _ = review_fixture(tmp_path)
    (root / 'B/pair1.png').write_bytes(b'changed')
    output = tmp_path / 'blind'
    with pytest.raises(ValueError, match='Frozen dataset differs'):
        build_review(root, manifest, output)
    assert not output.exists()


def test_production_transform_scored_at_actual_dimensions_without_refitting(tmp_path):
    root, manifest, benchmark, annotations = review_fixture(tmp_path)
    r = score_benchmark(benchmark, annotations, root, manifest)
    assert r['pair_count'] == 2 and r['production_reliable_count'] == 0
    assert all(p['identity_rms_px'] == 5 and p['transform_rms_px'] == 0 for p in r['pairs'])
    assert r['benchmark_sha256'] == hashlib.sha256(benchmark.read_bytes()).hexdigest()
    data = json.loads(annotations.read_text())
    for p in data['pairs']:
        for point in p['landmarks']: point[2] += 8
    annotations.write_text(json.dumps(data))
    wrong = score_benchmark(benchmark, annotations, root, manifest)
    assert all(p['transform_rms_px'] == 8 and p['production_reliable'] is False for p in wrong['pairs'])
    assert 'candidate_pass' not in wrong['pairs'][0]


@pytest.mark.parametrize('change', ['subset', 'duplicate', 'wrong-task', 'model-derived', 'unreviewed', 'same-person', 'out-of-bounds', 'wrong-image'])
def test_invalid_review_is_rejected(tmp_path, change):
    root, manifest, benchmark, annotations = review_fixture(tmp_path)
    a = json.loads(annotations.read_text())
    r = a['pairs'][0]
    if change == 'subset': a['pairs'].pop()
    elif change == 'duplicate': a['pairs'][1] = copy.deepcopy(r)
    elif change == 'wrong-task': a['dataset_manifest_sha256'] = '0' * 64
    elif change == 'model-derived': r['collection_basis'] = 'copied-model-matches'
    elif change == 'unreviewed': r['reviewed'] = False
    elif change == 'same-person': r['reviewer'] = ' FIXTURE-AUTHOR '
    elif change == 'out-of-bounds': r['landmarks'][0][0] = 300
    elif change == 'wrong-image': r['before_sha256'] = '0' * 64
    annotations.write_text(json.dumps(a))
    with pytest.raises(ValueError): score_benchmark(benchmark, annotations, root, manifest)


@pytest.mark.parametrize('change', ['hash', 'subset', 'source', 'unfrozen', 'matrix', 'decision'])
def test_invalid_benchmark_is_rejected(tmp_path, change):
    root, manifest, benchmark, annotations = review_fixture(tmp_path)
    b = json.loads(benchmark.read_text())
    if change == 'hash': b['dataset_manifest_sha256'] = '0' * 64
    elif change == 'subset': b['pair_results'].pop()
    elif change == 'source': b['pair_results'][0]['source_hashes']['A_sha256'] = '0' * 64
    elif change == 'unfrozen': b['dataset_frozen'] = False
    elif change == 'matrix': b['pair_results'][0]['alignment']['matrix'][0][0] = float('nan')
    elif change == 'decision': b['pair_results'][0]['alignment']['reliable'] = 'false'
    benchmark.write_text(json.dumps(b))
    with pytest.raises(ValueError): score_benchmark(benchmark, annotations, root, manifest)


def test_cli_refuses_overwrite_and_does_not_write_invalid_report(tmp_path):
    root, manifest, benchmark, annotations = review_fixture(tmp_path)
    output = tmp_path / 'result.json'
    command = [sys.executable, 'scripts/check_benchmark_alignment.py', str(benchmark), str(annotations), str(root),
               '--dataset-manifest', str(manifest), '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    prior = output.read_bytes()
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert output.read_bytes() == prior
    output.unlink(); (root / 'A/pair0.png').write_bytes(b'changed')
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert not output.exists()


def test_full_1024px_review_uses_original_processed_coordinates(tmp_path):
    root, manifest, benchmark, annotations = review_fixture(tmp_path, count=1, side=1024)
    report = score_benchmark(benchmark, annotations, root, manifest)
    assert report['pairs'][0]['landmarks'][1][0] == 840
    assert report['pairs'][0]['transform_rms_px'] == 0
    summary = build_review(root, manifest, tmp_path / 'full-scene')
    assert summary['pairs'][0]['width'] == summary['pairs'][0]['height'] == 1024

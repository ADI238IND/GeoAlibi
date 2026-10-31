import json
import subprocess
import sys

import pytest
from PIL import Image

from geoalibi.benchmark_manifest import dataset_records, freeze_dataset, validate_frozen_manifest


def dataset(tmp_path):
    for part in ('A', 'B', 'label'):
        (tmp_path / part).mkdir()
        for name in ('one.png', 'two.png'):
            Image.new('L', (64, 64), 0).save(tmp_path / part / name)
    return tmp_path


def test_frozen_bytes_include_labels_and_exact_subset(tmp_path):
    root = dataset(tmp_path)
    manifest = freeze_dataset(root, 'Synthetic test fixtures, not benchmark data', 1)
    path = root / 'manifest.json'
    path.write_text(json.dumps(manifest))
    assert len(validate_frozen_manifest(path, dataset_records(root, 1), 1)) == 64
    with pytest.raises(ValueError, match='Frozen dataset differs'):
        validate_frozen_manifest(path, dataset_records(root), 0)
    Image.new('L', (64, 64), 255).save(root / 'label/one.png')
    with pytest.raises(ValueError, match='Frozen dataset differs'):
        validate_frozen_manifest(path, dataset_records(root, 1), 1)


@pytest.mark.parametrize('folder', ['A', 'B', 'label'])
def test_unpaired_files_rejected_even_with_limit(tmp_path, folder):
    root = dataset(tmp_path)
    Image.new('L', (64, 64)).save(root / folder / 'extra.png')
    with pytest.raises(ValueError, match='exactly'):
        dataset_records(root, 1)


def test_negative_limit_rejected(tmp_path):
    with pytest.raises(ValueError, match='nonnegative'):
        dataset_records(dataset(tmp_path), -1)


def test_cli_frozen_evaluation_and_changed_label_failure(tmp_path):
    root = dataset(tmp_path)
    manifest, output = root / 'manifest.json', root / 'results.json'
    freeze = [sys.executable, 'scripts/freeze_benchmark.py', str(root), '--description',
              'Procedural integrity fixture only', '--output', str(manifest)]
    result = subprocess.run(freeze, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert subprocess.run(freeze, capture_output=True).returncode != 0
    command = [sys.executable, 'scripts/evaluate.py', str(root), '--dataset-manifest', str(manifest), '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report['dataset_frozen'] is True and report['pairs'] == 2
    assert report['pair_results'][0]['source_hashes']['label_sha256']
    output.unlink()
    Image.new('L', (64, 64), 255).save(root / 'label/two.png')
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and 'Frozen dataset differs' in result.stderr
    assert not output.exists() and 'Evaluated ' not in result.stdout

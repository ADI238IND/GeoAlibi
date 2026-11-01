"""Offline acquisition-contract tests; generated images are not benchmark data."""
import hashlib
import json
import sys
import types
import zipfile
from io import BytesIO

import pytest
from PIL import Image
from scripts.prepare_evaluation_subset import prepare
from geoalibi.benchmark_manifest import dataset_records, validate_frozen_manifest


def setup_archive(tmp_path, monkeypatch, bad=False):
    archive_path = tmp_path / 'fixture.zip'
    with zipfile.ZipFile(archive_path, 'w') as archive:
        for folder in ('A', 'B', 'label'):
            image = Image.new('L', (32, 32) if bad and folder == 'label' else (1024, 1024))
            content = BytesIO(); image.save(content, format='PNG')
            archive.writestr(f'{folder}/test_1.png', content.getvalue())
    monkeypatch.setitem(sys.modules, 'remotezip', types.SimpleNamespace(
        RemoteZip=lambda url, timeout: zipfile.ZipFile(archive_path)))
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({'count': 1, 'excluded_parent_scenes': [], 'rank_prefix': 'fixed:',
                               'archive_url': 'offline-test', 'purpose': 'Test fixture.', 'terms': 'Generated.'}))
    return plan


def test_acquisition_publishes_complete_bound_inputs_and_refuses_overwrite(tmp_path, monkeypatch):
    plan = setup_archive(tmp_path, monkeypatch)
    out = tmp_path / 'output'
    prepare(plan, out)
    selection = json.loads((out / 'selection.json').read_text())
    assert selection['selected'] == ['test_1.png']
    assert selection['plan_sha256'] == hashlib.sha256(plan.read_bytes()).hexdigest()
    assert len(selection['files']) == 3
    for name, record in selection['files'].items():
        assert record['sha256'] == hashlib.sha256((out / name).read_bytes()).hexdigest()
    assert validate_frozen_manifest(out / 'inputs.json', dataset_records(out))
    with pytest.raises(ValueError, match='Output exists'):
        prepare(plan, out)


def test_failed_member_does_not_publish_partial_dataset(tmp_path, monkeypatch):
    plan = setup_archive(tmp_path, monkeypatch, bad=True)
    out = tmp_path / 'output'
    with pytest.raises(ValueError, match='1024px'):
        prepare(plan, out)
    assert not out.exists()
    assert not list(tmp_path.glob('levir-subset-*'))

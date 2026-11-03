"""Procedural integrity contracts; none of these tests measure satellite accuracy."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from geoalibi.demo_verification import verify_bundle
from scripts.build_demo_bundle import build_bundle


@pytest.fixture(scope='module')
def original(tmp_path_factory):
    path = tmp_path_factory.mktemp('verified-demo') / 'bundle'
    # A minimal source root avoids coupling tests to manifest updates during development.
    from geoalibi.release_evidence import FILES
    root = path.parent / 'source'
    (root / 'docs').mkdir(parents=True)
    sources = {}
    for name in FILES.values():
        data = Path(name).read_bytes()
        (root / name).write_bytes(data)
        sources[name] = hashlib.sha256(data).hexdigest()
    (root / 'docs/SOURCE_MANIFEST.json').write_text(json.dumps(sources))
    build_bundle(path, root=root)
    return path


@pytest.fixture
def bundle(original, tmp_path):
    return Path(shutil.copytree(original, tmp_path / 'bundle'))


def rehash(bundle, name):
    path = bundle / 'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['files'][name] = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest))


def alter_json(bundle, name, update):
    path = bundle / name
    data = json.loads(path.read_text())
    update(data)
    path.write_text(json.dumps(data))
    rehash(bundle, name)


def test_valid_bundle_and_external_pin(original):
    pin = hashlib.sha256((original / 'SOURCE_MANIFEST.json').read_bytes()).hexdigest()
    result = verify_bundle(original, pin)
    assert result['files_verified'] == 21 and result['scenario_packets_verified'] == 4
    assert result['saved_research_pairs'] == 8 and result['external_source_pin_checked']
    with pytest.raises(ValueError, match='pin mismatch'):
        verify_bundle(original, '0' * 64)


@pytest.mark.parametrize('name', ['index.html', 'summary.json', 'research-unet.json'])
def test_corrupt_file_rejected(bundle, name):
    with (bundle / name).open('ab') as stream:
        stream.write(b'changed')
    with pytest.raises(ValueError, match='checksum'):
        verify_bundle(bundle)


@pytest.mark.parametrize('mode', ['missing', 'extra', 'symlink', 'directory', 'unsafe_manifest', 'oversize'])
def test_unsafe_or_incomplete_directory_rejected(bundle, mode):
    target = bundle / 'README.md'
    if mode == 'missing':
        target.unlink()
    elif mode == 'extra':
        (bundle / 'unexpected.env').write_text('procedural-fixture-only')
    elif mode == 'symlink':
        target.unlink(); target.symlink_to(bundle / 'summary.json')
    elif mode == 'directory':
        target.unlink(); target.mkdir()
    elif mode == 'oversize':
        with target.open('wb') as stream:
            stream.truncate(40 * 1024 * 1024 + 1)
    else:
        path = bundle / 'manifest.json'
        data = json.loads(path.read_text()); data['files']['../outside'] = '0' * 64
        path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        verify_bundle(bundle)


@pytest.mark.parametrize('mode', ['counts', 'duplicate_case', 'paid', 'seed', 'source', 'evidence',
                                 'research', 'gallery', 'packet', 'player', 'guide', 'duplicate_json'])
def test_rehashed_but_inconsistent_evidence_rejected(bundle, mode):
    summary = json.loads((bundle / 'summary.json').read_text())
    case = summary['scenarios'][0]['case']
    if mode == 'counts':
        alter_json(bundle, 'summary.json', lambda d: d['scenarios'][0]['counts'].update(review=999))
    elif mode == 'duplicate_case':
        alter_json(bundle, 'summary.json', lambda d: d['scenarios'].append(d['scenarios'][0]))
    elif mode in ('paid', 'seed', 'source'):
        key, value = {'paid': ('api_calls', 1), 'seed': ('seed', 19),
                      'source': ('source_manifest_sha256', '0' * 64)}[mode]
        alter_json(bundle, 'summary.json', lambda d: d.update({key: value}))
    elif mode == 'evidence':
        alter_json(bundle, 'recorded-research-evidence.json', lambda d: d.update(pair_count=999))
    elif mode == 'research':
        alter_json(bundle, 'research-unet.json', lambda d: d.update(pairs=999))
        # Updating both unsigned manifests cannot bypass the arithmetic/coverage validator.
        sha = hashlib.sha256((bundle / 'research-unet.json').read_bytes()).hexdigest()
        alter_json(bundle, 'SOURCE_MANIFEST.json', lambda d: d.update({'docs/EXPANDED_UNET_EVALUATION.json': sha}))
    elif mode == 'gallery':
        (bundle / (case + '-before.png')).write_bytes((bundle / (case + '-overlay.png')).read_bytes())
        rehash(bundle, case + '-before.png')
    elif mode == 'packet':
        (bundle / (case + '.zip')).write_bytes((bundle / (summary['scenarios'][1]['case'] + '.zip')).read_bytes())
        rehash(bundle, case + '.zip')
    elif mode in ('player', 'guide'):
        name = 'index.html' if mode == 'player' else 'RECORDING_SCRIPT.md'
        (bundle / name).write_text('Invented accuracy claim')
        rehash(bundle, name)
    else:
        name = 'summary.json'
        text = (bundle / name).read_text()
        (bundle / name).write_text(text.replace('"api_calls": 0', '"api_calls": 1, "api_calls": 0'))
        rehash(bundle, name)
    with pytest.raises(ValueError):
        verify_bundle(bundle)


def test_cli_failure_is_nonzero_and_does_not_modify_bundle(bundle):
    (bundle / 'index.html').write_text('corrupt')
    before = {p.name: p.read_bytes() for p in bundle.iterdir()}
    result = subprocess.run([sys.executable, 'scripts/verify_demo_bundle.py', str(bundle)], capture_output=True, text=True)
    assert result.returncode == 1 and 'verification failed' in result.stderr
    assert before == {p.name: p.read_bytes() for p in bundle.iterdir()}

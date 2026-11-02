import hashlib
import json
from pathlib import Path

import pytest
from geoalibi.dossier import verify_packet
from scripts.build_demo_bundle import build_bundle
from geoalibi.release_evidence import FILES


def test_rehearsal_is_labelled_verified_and_does_not_copy_private_files(tmp_path):
    root = tmp_path / 'source'
    (root / 'docs').mkdir(parents=True)
    sources = {}
    for path in FILES.values():
        data = Path(path).read_bytes()
        (root / path).write_bytes(data)
        sources[path] = hashlib.sha256(data).hexdigest()
    (root / 'docs/SOURCE_MANIFEST.json').write_text(json.dumps(sources))
    (root / '.env').write_text('FIXTURE_PRIVATE_VALUE=never-copy-this')
    out = tmp_path / 'bundle'
    summary = build_bundle(out, root=root)
    assert summary['synthetic'] and summary['api_calls'] == 0
    assert len(summary['scenarios']) == 4
    real = json.loads((out / summary['recorded_real_evidence']).read_text())
    assert real['pair_count'] == 8
    assert real['arms']['unet']['metrics']['supported']['precision'] is None
    assert '78.66%' in (out / 'README.md').read_text()
    assert '91.44%' not in (out / 'README.md').read_text()
    player=(out/'index.html').read_text()
    assert '78.66%' in player and 'undefined' in player and 'accepted zero pixels' in player
    assert '<!--SCENARIOS-->' not in player and 'Every image in this gallery is generated' in player
    assert (out/'RECORDING_SCRIPT.md').is_file()
    assert 'Supported recall was 0.00%' in (out/'RECORDING_SCRIPT.md').read_text()
    assert not any(p.suffix in ('.ckpt', '.env') for p in out.iterdir())
    manifest = json.loads((out / 'manifest.json').read_text())
    assert set(p.name for p in out.iterdir()) == set(manifest['files']) | {'manifest.json'}
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
        assert b'never-copy-this' not in (out / name).read_bytes()
    for case in summary['scenarios']:
        assert case['meta_status'] == 'not_requested'
        assert case['sam_status'] == 'not_requested'
        packet = (out / (case['case'] + '.zip')).read_bytes()
        assert verify_packet(packet)['run_id'].startswith('procedural-')
    with pytest.raises(ValueError, match='already exists'):
        build_bundle(out, root=root)


def test_source_mismatch_stops_before_creating_deliverable(tmp_path):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'code.py').write_text('changed')
    (tmp_path / 'docs/SOURCE_MANIFEST.json').write_text(json.dumps({'code.py': '0' * 64}))
    with pytest.raises(ValueError, match='mismatch'):
        build_bundle(tmp_path / 'bundle', root=tmp_path)
    assert not (tmp_path / 'bundle').exists()

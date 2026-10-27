import hashlib
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image
import pytest

from geoalibi.evaluation import checked_landmarks, load_landmark_manifest


def annotation():
    return {'file': 'pair.png', 'annotator': 'A', 'reviewer': 'B',
            'coordinate_space': 'processed-original-images',
            **{k: hashlib.sha256(b'image').hexdigest() for k in ('before_sha256', 'after_sha256', 'label_sha256')},
            'landmarks': [[20,20,20,20],[230,20,230,20],[20,230,20,230],[230,230,230,230],[60,80,60,80],[190,180,190,180]]}


def test_hash_binding_and_independent_review(tmp_path):
    record = annotation()
    path = tmp_path / 'annotations.json'
    path.write_text(json.dumps({'schema':'geoalibi-landmarks-v1','pairs':[record]}))
    records, digest = load_landmark_manifest(path)
    assert len(digest) == 64
    assert checked_landmarks(records['pair.png'], b'image', b'image', b'image') == record['landmarks']
    with pytest.raises(ValueError, match='mismatch'):
        checked_landmarks(record, b'changed', b'image', b'image')
    record['reviewer'] = ' a '
    path.write_text(json.dumps({'schema':'geoalibi-landmarks-v1','pairs':[record]}))
    with pytest.raises(ValueError, match='independent reviewer'):
        load_landmark_manifest(path)


def test_paired_evaluation_cli_and_wrong_image_rejection(tmp_path):
    rng = np.random.default_rng(42)
    image = rng.integers(0, 256, (256,256,3), dtype=np.uint8)
    record = annotation()
    for folder, field in [('A','before_sha256'),('B','after_sha256'),('label','label_sha256')]:
        (tmp_path / folder).mkdir()
        p = tmp_path / folder / 'pair.png'
        Image.fromarray(np.zeros((256,256),np.uint8) if folder=='label' else image).save(p)
        record[field] = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = tmp_path / 'annotations.json'
    manifest.write_text(json.dumps({'schema':'geoalibi-landmarks-v1','pairs':[record]}))
    output = tmp_path / 'results.json'
    command = [sys.executable, 'scripts/evaluate.py', str(tmp_path), '--landmarks', str(manifest), '--output', str(output)]
    env = {**os.environ, 'MODEL_API_KEY':''}
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report['pairs'] == 1 and len(report['assisted']['pair_results']) == 1
    assert report['assisted']['metrics']['supported']['fp'] == 0
    assert report['assisted']['metrics']['supported']['precision'] is None
    assert report['assisted']['pair_results'][0]['alignment']['held_out_points'] == 2
    output.unlink()
    (tmp_path/'B'/'pair.png').write_bytes(b'wrong image')
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    assert result.returncode != 0 and 'mismatch' in result.stderr
    assert not output.exists()

"""Freeze and validate exact source bytes before benchmark inference."""
import hashlib
import json
from pathlib import Path

SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}


def image_names(directory):
    return {p.name for p in directory.iterdir() if p.is_file() and p.suffix.lower() in SUFFIXES}


def dataset_records(root, limit=0):
    if limit < 0:
        raise ValueError('Subset limit must be nonnegative.')
    names = image_names(root / 'A')
    if not names or names != image_names(root / 'B') or names != image_names(root / 'label'):
        raise ValueError('A, B and label must contain exactly the same nonempty image filename set.')
    selected = sorted(names)[:limit] if limit else sorted(names)
    return [{'file': name, **{part + '_sha256': hashlib.sha256((root / part / name).read_bytes()).hexdigest()
                              for part in ('A', 'B', 'label')}} for name in selected]


def freeze_dataset(root, description, limit=0):
    if not isinstance(description, str) or not description.strip():
        raise ValueError('Describe source, split selection and applicable image terms.')
    return {'schema': 'geoalibi-benchmark-inputs-v1', 'description': description.strip(),
            'subset_limit': limit, 'pairs': dataset_records(root, limit),
            'warning': 'Hashes freeze bytes, not independence, licensing or annotation truth. Freeze before inspecting results; never tune on the evaluation split.'}


def validate_frozen_manifest(path, records, limit=0):
    raw = Path(path).read_bytes()
    manifest = json.loads(raw)
    if (not isinstance(manifest, dict) or manifest.get('schema') != 'geoalibi-benchmark-inputs-v1'
            or not isinstance(manifest.get('description'), str) or not manifest['description'].strip()
            or type(manifest.get('subset_limit')) is not int or manifest['subset_limit'] != limit
            or manifest.get('pairs') != records):
        raise ValueError('Frozen dataset differs: verify exact filenames, original image/label hashes and subset limit.')
    return hashlib.sha256(raw).hexdigest()

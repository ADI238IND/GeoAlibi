"""Strict, image-bound annotation loading for assisted benchmark evaluation."""
import hashlib
import json


def load_landmark_manifest(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Landmark manifest must be an object.')
    if data.get('schema') != 'geoalibi-landmarks-v1':
        raise ValueError('Unsupported landmark manifest schema.')
    records = data.get('pairs')
    if not isinstance(records, list) or not records:
        raise ValueError('Landmark manifest must contain a nonempty pairs list.')
    indexed = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Each annotation must be an object.')
        name = record.get('file', '')
        if not isinstance(name, str) or not name or '/' in name or '\\' in name or name in indexed:
            raise ValueError('Landmark filenames must be unique plain filenames.')
        for field in ('annotator', 'reviewer', 'coordinate_space'):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f'{name}: missing {field}.')
        if record['annotator'].strip().casefold() == record['reviewer'].strip().casefold():
            raise ValueError(f'{name}: independent reviewer must differ from annotator.')
        if record['coordinate_space'] != 'processed-original-images':
            raise ValueError(f'{name}: landmarks must use processed original image coordinates.')
        if not isinstance(record.get('landmarks'), list):
            raise ValueError(f'{name}: missing landmark rows.')
        for field in ('before_sha256', 'after_sha256', 'label_sha256'):
            value = record.get(field, '')
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError(f'{name}: invalid {field}.')
        indexed[name] = record
    return indexed, hashlib.sha256(raw).hexdigest()


def checked_landmarks(record, before, after, label):
    for field, content in [('before_sha256', before), ('after_sha256', after), ('label_sha256', label)]:
        if hashlib.sha256(content).hexdigest() != record[field]:
            raise ValueError(f"{record['file']}: {field} mismatch; annotation belongs to different bytes.")
    return record['landmarks']



def decode_binary_label(content, before_content, processed_shape):
    """Reject incompatible labels before nearest-neighbor reduction to image size."""
    from io import BytesIO
    import cv2
    import numpy as np
    from PIL import Image, ImageOps

    with Image.open(BytesIO(before_content)) as before:
        expected = ImageOps.exif_transpose(before).size
    with Image.open(BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source)
        if image.size != expected:
            raise ValueError('Label dimensions must match the oriented original BEFORE image; automatic stretching is disabled.')
        # Preserve categorical indices, including palette labels. Converting to L can
        # collapse distinct class values or turn colored background into change.
        values = np.asarray(image)
        if values.ndim != 2:
            raise ValueError('Label must be a single-channel binary class map, not RGB/RGBA.')
        unique = np.unique(values)
        if not np.isin(unique, [0, 1, 255]).all() or (1 in unique and 255 in unique):
            raise ValueError('Label must use 0/1 or 0/255 binary classes; remap other class values explicitly.')
        return cv2.resize((values > 0).astype(np.uint8), (processed_shape[1], processed_shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)

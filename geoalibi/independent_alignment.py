"""Score frozen matcher transforms on separately collected points; never refit."""
import cv2
import numpy as np


def landmark_errors(matrix, landmarks, width=256, height=256):
    points = np.asarray(landmarks, dtype=float)
    if points.ndim != 2 or points.shape[1:] != (4,) or not 6 <= len(points) <= 20 or not np.isfinite(points).all():
        raise ValueError('Require 6–20 finite independently collected landmark rows.')
    source, target = points[:, :2], points[:, 2:]
    for xy in (source, target):
        if (xy < 0).any() or (xy[:, 0] >= width).any() or (xy[:, 1] >= height).any():
            raise ValueError('Landmarks outside processed original-image bounds.')
        distances = np.linalg.norm(xy[:, None] - xy[None, :], axis=2)
        np.fill_diagonal(distances, np.inf)
        if distances.min() < 2:
            raise ValueError('Landmarks must be distinct in both images.')
        if cv2.contourArea(cv2.convexHull(xy.astype(np.float32))) < .1 * width * height:
            raise ValueError('Landmarks must span at least 10% of both image areas.')
    identity = np.linalg.norm(source - target, axis=1)
    result = {'points': len(points), 'landmarks': points.tolist(),
              'identity_errors_px': identity.tolist(),
              'identity_rms_px': float(np.sqrt(np.mean(identity ** 2))),
              'transform_errors_px': None, 'transform_rms_px': None}
    if matrix is None:
        return result
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape != (2, 3) or not np.isfinite(matrix).all():
        raise ValueError('Frozen transform must be a finite 2 by 3 matrix.')
    errors = np.linalg.norm(source @ matrix[:, :2].T + matrix[:, 2] - target, axis=1)
    return {**result, 'transform_errors_px': errors.tolist(),
            'transform_rms_px': float(np.sqrt(np.mean(errors ** 2))),
            'transform_max_error_px': float(errors.max()),
            'fraction_within_2_5px': float(np.mean(errors <= 2.5))}


def evaluate_reviewed_alignment(audit, annotations):
    actual = {row['file']: row for row in audit['results'] if row['case'] == 'actual'}
    if not actual or set(actual) != set(annotations):
        raise ValueError('Reviewed filenames must exactly match all actual audit pairs.')
    results = []
    for name, row in sorted(actual.items()):
        annotation = annotations[name]
        if annotation.get('collection_basis') != 'independent-original-image-review':
            raise ValueError('Declare independently collected original-image landmarks, not model matches.')
        for field, prefix in [('before_sha256', 'A/'), ('after_sha256', 'B/'), ('label_sha256', 'label/')]:
            if annotation[field] != audit['input_sha256'][prefix + name]:
                raise ValueError(f'{name}: reviewed image hashes differ from audit inputs.')
        geometry = row['audit']['geometry']
        measurements = landmark_errors(geometry.get('matrix'), annotation['landmarks'])
        results.append({'file': name, 'model_candidate_pass': geometry['candidate_pass'],
                        'annotator': annotation['annotator'], 'reviewer': annotation['reviewer'],
                        **measurements})
    return {'schema': 'geoalibi-independent-alignment-v1', 'pairs': results,
            'pair_count': len(results),
            'candidate_pass_count': sum(r['model_candidate_pass'] for r in results),
            'with_transform_count': sum(r['transform_rms_px'] is not None for r in results),
            'limitations': 'All review points score frozen transforms; no refitting or production acceptance. '
                          'Reviewer identities and independence are assertions, not authenticated. '
                          'Pixel residuals do not establish change accuracy or acquisition provenance.'}

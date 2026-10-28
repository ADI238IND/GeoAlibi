"""Audit registration on hash-verified real pairs and declared negative controls."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from geoalibi.vision import VERSION, align, decode_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--manifest', type=Path, default=Path('docs/REAL_SAMPLE_MANIFEST.json'))
    parser.add_argument('--output', type=Path, default=Path('registration-audit.json'))
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    images = {}
    for name, expected in manifest['files'].items():
        data = (args.dataset / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Hash mismatch: {name}')
        if name.startswith(('A/', 'B/')):
            images[name] = decode_image(data)
    names = sorted(name[2:] for name in images if name.startswith('A/'))
    if len(names) < 2:
        raise ValueError('At least two image pairs are required for mismatched-pair controls.')
    rows = []
    for index, name in enumerate(names):
        a = images['A/' + name]
        h, w = a.shape[:2]
        cases = [('actual_pair', images['B/' + name], None),
                 ('same_image', a.copy(), (0, 0)),
                 ('translated_source', cv2.warpAffine(a, np.float32([[1,0,4],[0,1,-3]]), (w,h), borderMode=cv2.BORDER_REFLECT), (-4,3)),
                 ('mismatched_pair', images['B/' + names[(index+1) % len(names)]], None)]
        for case, b, expected in cases:
            _, _, evidence = align(a, b)
            row = {'file': name, 'case': case, 'alignment': evidence}
            if case == 'mismatched_pair':
                row['after_file'] = names[(index+1) % len(names)]
            if expected is not None:
                matrix = np.asarray(evidence['matrix'])
                corners = np.float32([[0,0],[w-1,0],[0,h-1],[w-1,h-1]])
                errors = np.linalg.norm(corners @ matrix[:,:2].T + matrix[:,2] - (corners + expected), axis=1)
                row['known_transform_max_corner_error_px'] = float(errors.max())
            rows.append(row)
    summary = {case: {'cases': sum(r['case']==case for r in rows),
                      'reliable': sum(r['case']==case and r['alignment']['reliable'] for r in rows)}
               for case in ['actual_pair','same_image','translated_source','mismatched_pair']}
    result = {'engine': VERSION, 'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
              'opencv_version': cv2.__version__, 'summary': summary, 'results': rows,
              'limitations': 'Selected development samples, not an independent benchmark. Actual-pair transform truth is unknown. Mismatched filenames are negative-control candidates, not independently verified different footprints. Same-image/translation cases are derived controls, not separate acquisitions. No model calls or gate tuning.'}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

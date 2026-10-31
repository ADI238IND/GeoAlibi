"""Offline matcher diagnostic; candidate fits never override production abstention."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from geoalibi.vision import decode_image, gray


def measure(a, b, method):
    detector = cv2.SIFT_create() if method == 'SIFT' else cv2.AKAZE_create()
    norm = cv2.NORM_L2 if method == 'SIFT' else cv2.NORM_HAMMING
    ka, da = detector.detectAndCompute(gray(a), None)
    kb, db = detector.detectAndCompute(gray(b), None)
    matches = [] if da is None or db is None else [p[0] for p in cv2.BFMatcher(norm).knnMatch(db, da, k=2)
                if len(p) == 2 and p[0].distance < .72 * p[1].distance]
    row = {'matches': len(matches), 'candidate_pass': False, 'reason': 'fewer than 8 ratio-filtered matches'}
    if len(matches) < 8:
        return row
    src = np.float32([kb[m.queryIdx].pt for m in matches])
    dst = np.float32([ka[m.trainIdx].pt for m in matches])
    cv2.setRNGSeed(0)
    matrix, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.5)
    if matrix is None or mask is None:
        row['reason'] = 'fit failed'
        return row
    inliers = int(mask.sum())
    scale = float(np.linalg.norm(matrix[0,:2]))
    angle = float(abs(np.degrees(np.arctan2(matrix[1,0],matrix[0,0]))))
    coverage = min(cv2.contourArea(cv2.convexHull(points[mask.ravel()>0])) for points in [src,dst]) / (a.shape[0]*a.shape[1])
    passed = inliers >= 8 and inliers/len(matches)>=.4 and .95<scale<1.05 and angle<=5 and np.linalg.norm(matrix[:,2])<min(a.shape[:2])*.12 and coverage>=.1
    row.update(inliers=inliers, scale=scale, rotation_degrees=angle, coverage_fraction=coverage, matrix=matrix.tolist(),
               candidate_pass=bool(passed), reason='candidate geometry only; no independent held-out truth' if passed else 'insufficient consensus, coverage or bounded transform')
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset',type=Path)
    parser.add_argument('--output',type=Path,default=Path('matcher-comparison.json'))
    args=parser.parse_args()
    manifest_bytes=Path('docs/REAL_SAMPLE_MANIFEST.json').read_bytes()
    manifest=json.loads(manifest_bytes)
    images={}
    for name,digest in manifest['files'].items():
        data=(args.dataset/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Hash mismatch: '+name)
        if name.startswith(('A/','B/')):images[name]=decode_image(data)
    names=sorted(n[2:] for n in images if n.startswith('A/'))
    rows=[]
    for i,name in enumerate(names):
        a=images['A/'+name]
        shifted=cv2.warpAffine(a,np.float32([[1,0,4],[0,1,-3]]),(a.shape[1],a.shape[0]),borderMode=cv2.BORDER_REFLECT)
        for case,b in [('actual',images['B/'+name]),('mismatched',images['B/'+names[(i+1)%len(names)]]),('same',a),('translated',shifted)]:
            for method in ['SIFT','AKAZE']:
                rows.append({'file':name,'case':case,'method':method,**measure(a,b,method)})
    summary={method:{case:sum(r['candidate_pass'] for r in rows if r['method']==method and r['case']==case) for case in ['actual','mismatched','same','translated']} for method in ['SIFT','AKAZE']}
    output={'opencv_version':cv2.__version__,'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'ratio_threshold':.72,'summary':summary,'results':rows,
            'note':'Exploratory development samples. Candidate geometry is not validated registration. Controls are derived or mismatched filenames, not independently adjudicated acquisitions. No production behavior changed or threshold sweep performed.',
            'reference':'https://docs.opencv.org/4.13.0/db/d70/tutorial_akaze_matching.html'}
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()

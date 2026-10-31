"""Experimental CPU LoFTR audit; never changes production registration."""
import hashlib
import json
import time
from pathlib import Path

import cv2
import numpy as np
import argparse
import platform
from importlib.metadata import version
from geoalibi.matcher_audit import audit_matches
from geoalibi.vision import decode_image, gray

CHECKPOINT_SHA='21f5bec5968178e8bc8b7633441836fe5de4f47d861dd2cd7dc38e271b0479ec'
REVISION='0fb3b456cf176746709c38fa9cf80695a1c82dac'



def write_output(path, output):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Optional heavy dependencies are only imported for explicit inference.
    import torch
    from kornia.feature import LoFTR
    path = args.checkpoint
    if path.stat().st_size != 46341978:
        raise ValueError('Checkpoint size mismatch')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=CHECKPOINT_SHA:raise ValueError('Checkpoint SHA mismatch')
    torch.set_num_threads(4)
    model=LoFTR(pretrained=None).eval()
    model.load_state_dict(torch.load(path,map_location='cpu',weights_only=True)['state_dict'],strict=True)
    manifest_bytes=Path('docs/REAL_SAMPLE_MANIFEST.json').read_bytes();manifest=json.loads(manifest_bytes)
    root=args.dataset;images={}
    for name,expected in manifest['files'].items():
        data=(root/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Image SHA mismatch')
        if name.startswith(('A/','B/')):
            image=decode_image(data)
            if image.shape[:2]!=(256,256):raise ValueError('This protocol requires 256px inputs')
            images[name]=image
    names=sorted(n[2:] for n in images if n.startswith('A/'));rows=[]
    output={'schema':'geoalibi-loftr-audit-v1','complete':False,'python_version':platform.python_version(),'numpy_version':np.__version__,'kornia_version':version('kornia'),'input_sha256':manifest['files'],'geometry_source_sha256':hashlib.sha256(Path('geoalibi/correspondence_checks.py').read_bytes()).hexdigest(),'model':'LoFTR outdoor','revision':REVISION,'checkpoint_sha256':CHECKPOINT_SHA,'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
            'torch_version':torch.__version__,'opencv_version':cv2.__version__,'confidence_threshold':.8,'split_seed':42,'results':rows,
            'limitations':'Exploratory selected development crops. Held-out correspondences share the same matcher and may share errors; not independent ground truth. No production integration, training, threshold sweep or paid calls. Derived controls are not real acquisitions.'}
    for i,name in enumerate(names):
        a=images['A/'+name]
        shifted=cv2.warpAffine(a,np.float32([[1,0,4],[0,1,-3]]),(256,256),borderMode=cv2.BORDER_REFLECT)
        for case,b in [('actual',images['B/'+name]),('mismatched',images['B/'+names[(i+1)%len(names)]]),('same',a),('translated',shifted)]:
            start=time.perf_counter()
            with torch.inference_mode():
                prediction=model({'image0':torch.from_numpy(gray(b).copy()).float()[None,None]/255,'image1':torch.from_numpy(gray(a).copy()).float()[None,None]/255})
            audit = audit_matches(prediction['keypoints0'].numpy(),
                                  prediction['keypoints1'].numpy(),
                                  prediction['confidence'].numpy())
            target_name = names[(i+1)%len(names)] if case == 'mismatched' else name
            row={'file':name,'case':case,'before_file':'A/'+name,
                 'after_file':('B/'+target_name if case in ('actual','mismatched') else 'A/'+name),
                 'derived_transform':({'translation_xy':[4,-3],'border':'reflect'} if case == 'translated' else None),
                 'audit':audit,'seconds':round(time.perf_counter()-start,3)}
            rows.append(row)
            write_output(args.output, output)
            print(name,case,audit['geometry']['matches'],audit['geometry']['candidate_pass'],flush=True)
    output['complete'] = True
    output['summary']={case:{'cases':sum(r['case']==case for r in rows),'candidate_passes':sum(r['case']==case and r['audit']['geometry']['candidate_pass'] for r in rows)} for case in ['actual','mismatched','same','translated']}
    write_output(args.output, output)


if __name__=='__main__':main()

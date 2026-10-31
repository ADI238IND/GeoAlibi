"""Explore larger context for development crops. Install remotezip separately; no model calls."""
import hashlib
import json
from pathlib import Path

import numpy as np
from remotezip import RemoteZip

from geoalibi.vision import VERSION, align, decode_image

REVISION='6a6bb0a5b389403d81c05e33bf08bc0b9e5f13a6'
URL=f'https://huggingface.co/datasets/satellite-image-deep-learning/LEVIR-CD/resolve/{REVISION}/test.zip'


def main():
    manifest=json.loads(Path('docs/REAL_SAMPLE_MANIFEST.json').read_text())
    names=sorted(n[2:] for n in manifest['files'] if n.startswith('A/'))
    root=Path('datasets/levir-context');root.mkdir(parents=True,exist_ok=True)
    rows=[];hashes={}
    # Academic-use-only data; no image bytes belong in source control.
    with RemoteZip(URL, timeout=60) as archive:
        for name in names:
            parts=Path(name).stem.split('_');scene='_'.join(parts[:2])+'.png'
            arrays=[]
            for folder in ['A','B']:
                member=folder+'/'+scene
                if member not in hashes:
                    info=archive.getinfo(member)
                    if info.file_size>12*1024*1024:raise ValueError('Oversized archive member')
                    data=archive.read(member)  # ZIP reader verifies member CRC.
                    path=root/member;path.parent.mkdir(exist_ok=True);path.write_bytes(data)
                    hashes[member]=hashlib.sha256(data).hexdigest()
                arrays.append(decode_image((root/member).read_bytes()))
            # Establish exact pixel correspondence to the original-author demo.
            offsets=[]
            for folder,full in zip(['A','B'],arrays):
                raw=(Path('datasets/levir-author-demo')/folder/name).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=manifest['files'][folder+'/'+name]:raise ValueError('Original crop hash mismatch')
                crop=decode_image(raw);u,v=map(int,parts[2:])
                matches=[(y,x) for y,x in {(u,v),(v,u)} if np.array_equal(full[y:y+crop.shape[0],x:x+crop.shape[1]],crop)]
                if len(matches)!=1:raise ValueError('Full-image crop correspondence not uniquely established: '+name)
                offsets.append(matches[0])
            if offsets[0]!=offsets[1]:raise ValueError('Before/After crop offsets disagree')
            _,_,evidence=align(*arrays)
            rows.append({'crop':name,'scene':scene,'crop_yx':list(offsets[0]),'alignment':evidence})
            print(name,evidence['reliable'],flush=True)
    Path('docs/CONTEXT_REGISTRATION.json').write_text(json.dumps({'engine':VERSION,'mirror_revision':REVISION,'url':URL,'image_hashes':hashes,'results':rows,
        'limitations':'Exploratory context comparison, selected development scenes. Exact crop pixels checked against original-author samples, ZIP member CRC checked; full archive SHA not verified. No independent transform truth or change accuracy measured. Data remain academic-only; no imagery redistributed.'},indent=2)+'\n')


if __name__=='__main__':main()

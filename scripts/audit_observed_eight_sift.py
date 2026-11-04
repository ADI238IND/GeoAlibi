import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from geoalibi.stable_registration import stable_registration
root=Path(sys.argv[1]); output=Path(sys.argv[2])
if output.exists(): raise ValueError('Output exists')
manifest=Path('docs/EXPANDED_EVAL_INPUTS.json')
results=[]
for pair in json.loads(manifest.read_text())['pairs']:
    arrays=[]; hashes={}
    for side in ('A','B'):
        raw=(root/side/pair['file']).read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        assert digest==pair[side+'_sha256'], 'Original image hash mismatch'
        hashes[side]=digest
        with Image.open(root/side/pair['file']) as image: arrays.append(np.asarray(image.convert('RGB')))
    zero=np.zeros(arrays[0].shape[:2],np.uint8)
    actual=stable_registration(*arrays,zero,zero)
    same=stable_registration(arrays[0],arrays[0],zero,zero)
    results.append({'file':pair['file'],'original_sha256':hashes,'actual':actual,'same_image_control':same})
    print(pair['file'], 'actual:',actual['geometry']['candidate_pass'],'same:',same['geometry']['candidate_pass'],flush=True)
report={'schema':'geoalibi-unmasked-sift-observed-eight-v1','source_commit':'c0d963057caa60dd9d941f1940ad25bc0a02cc13','input_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'protocol':'Fixed candidate; all eight previously observed full scenes; zero exclusion masks; no labels read by this audit; no resizing or threshold changes. Same-image controls are not independent truth.','limitations':'Observed development scenes, not untouched holdout. Matcher holdout is not human alignment truth. No production gate, satellite change score, or Meta validation is changed.','results':results,'summary':{'scenes':len(results),'actual_candidate_passes':sum(r['actual']['geometry']['candidate_pass'] for r in results),'same_image_passes':sum(r['same_image_control']['geometry']['candidate_pass'] for r in results)}}
with output.open('x') as f: json.dump(report,f,indent=2,allow_nan=False)
print(report['summary'])

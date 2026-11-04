"""Research-only alignment diagnostic; exclusions must not come from evaluation labels."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from geoalibi.stable_registration import stable_registration


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','before_excluded','after_excluded','output'):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; preserve prior evidence and choose another path.')
    arrays=[]
    for path,mode in ((args.before,'RGB'),(args.after,'RGB'),(args.before_excluded,'L'),(args.after_excluded,'L')):
        with Image.open(path) as image:
            if min(image.size)<64 or max(image.size)>2048:
                parser.error('Input dimensions must be 64 through 2048; no resizing is performed.')
            arrays.append(np.asarray(image.convert(mode)))
    result=stable_registration(*arrays)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(result['geometry'],indent=2))


if __name__=='__main__':
    main()

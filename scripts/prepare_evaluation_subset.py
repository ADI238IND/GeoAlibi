"""Download only a preregistered academic test subset; never inspect model outputs."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from geoalibi.evaluation_selection import select_scenes
from geoalibi.benchmark_manifest import freeze_dataset


def prepare(plan_path, output):
    from remotezip import RemoteZip
    from PIL import Image
    from io import BytesIO
    raw = plan_path.read_bytes()
    plan = json.loads(raw)
    if output.exists():
        raise ValueError('Output exists; refusing to replace frozen inputs.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='levir-subset-') as tmp:
        stage = Path(tmp) / 'dataset'
        stage.mkdir()
        with RemoteZip(plan['archive_url'], timeout=60) as archive:
            names = select_scenes(archive.namelist(), plan)
            selection = {'plan_sha256': hashlib.sha256(raw).hexdigest(), 'selected': names,
                         'archive_url': plan['archive_url'], 'member_crc_verified': True,
                         'whole_archive_sha256_verified': False, 'files': {}}
            print('Frozen filename selection:', ', '.join(names), flush=True)
            for folder in ('A', 'B', 'label'):
                (stage / folder).mkdir()
                for name in names:
                    member = folder + '/' + name
                    info = archive.getinfo(member)
                    if info.file_size > 12 * 1024 * 1024:
                        raise ValueError('Oversized archive member')
                    data = archive.read(member)  # zipfile verifies each member CRC.
                    if len(data) != info.file_size:
                        raise ValueError('Truncated archive member')
                    with Image.open(BytesIO(data)) as image:
                        if image.size != (1024, 1024):
                            raise ValueError('Expected full 1024px parent images')
                        image.verify()
                    (stage / member).write_bytes(data)
                    selection['files'][member] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'crc32': info.CRC}
                    print('Verified', member, flush=True)
        (stage / 'selection.json').write_text(json.dumps(selection, indent=2) + '\n')
        manifest = freeze_dataset(stage, plan['purpose'] + ' ' + plan['terms'])
        (stage / 'inputs.json').write_text(json.dumps(manifest, indent=2) + '\n')
        if output.exists():
            raise ValueError('Output appeared during preparation')
        shutil.move(str(stage), output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=Path('docs/EXPANDED_EVAL_PLAN.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.plan, args.output)

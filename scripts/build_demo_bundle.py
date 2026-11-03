"""Build a local, credential-free procedural rehearsal bundle; never call models."""
import argparse
import hashlib
import json
import platform
import shutil
import tempfile
from importlib.metadata import version
from pathlib import Path

from geoalibi.demo import CASES, pair
from geoalibi.dossier import build_packet, verify_packet
from geoalibi.vision import investigate, png
from geoalibi.release_evidence import FILES, saved_evidence
from geoalibi.demo_player import render_player, recording_script


def build_bundle(output, root=None):
    root = root or Path(__file__).resolve().parents[1]
    output = Path(output)
    if output.exists():
        raise ValueError('Output already exists; choose a new directory to preserve prior evidence.')
    source_bytes = (root / 'docs/SOURCE_MANIFEST.json').read_bytes()
    sources = json.loads(source_bytes)
    for name, expected in sources.items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Source manifest mismatch: ' + name)
    evidence = saved_evidence(root)
    for key, path in FILES.items():
        if sources.get(path) != evidence['source_sha256'][key]:
            raise ValueError('Research evidence is not bound to the source manifest: ' + path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='geoalibi-rehearsal-', dir=output.parent) as temporary:
        stage = Path(temporary) / 'bundle'
        stage.mkdir()
        (stage / 'recorded-research-evidence.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
        for key, path in FILES.items():
            data = (root / path).read_bytes()
            if hashlib.sha256(data).hexdigest() != evidence['source_sha256'][key]:
                raise ValueError('Research source changed during bundle generation: ' + path)
            (stage / ('research-' + key + '.json')).write_bytes(data)
        results = []
        for case, title in CASES.items():
            before, after, _ = pair(case, seed=18)
            analysis = investigate(before, after)
            report = {**analysis.report, 'id': 'procedural-' + case, 'synthetic': True,
                      'title': 'PROCEDURAL ILLUSTRATION: ' + title,
                      'audit': [], 'evidence_responses': [],
                      'evidence_scope': 'Generated scenario; not a satellite benchmark or real acquisition.'}
            assets = {name: png(image) for name, image in analysis.images.items()}
            packet = build_packet(report, assets)
            verified = verify_packet(packet)
            (stage / (case + '.zip')).write_bytes(packet)
            for name in ('before', 'overlay'):
                (stage / (case + '-' + name + '.png')).write_bytes(assets[name])
            results.append({'case': case, 'title': title, 'counts': report['counts'],
                            'engine': report['engine'], 'packet_files_verified': len(verified['files']),
                            'meta_status': report['meta']['status'], 'sam_status': report['sam']['status']})
        summary = {'schema': 'geoalibi-offline-demo-v1', 'synthetic': True, 'seed': 18,
                   'source_manifest_sha256': hashlib.sha256(source_bytes).hexdigest(),
                   'environment': {'python': platform.python_version(), **{p: version(p) for p in ('numpy', 'opencv-python-headless', 'Pillow')}},
                   'api_calls': 0, 'new_api_reservations_usd': 0, 'scenarios': results,
                   'recorded_real_evidence': 'recorded-research-evidence.json',
                   'evidence_scope': 'Scenario images are procedural. Separate saved real-data reports are included but not rerun.',
                   'limitations': 'Procedural rehearsal only; no accuracy estimate, trained detector or live Meta inference. '
                                  'Historical $0.54 reservation is unreconciled; this bundle does not reset the ledger.'}
        (stage / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        (stage / 'SOURCE_MANIFEST.json').write_bytes(source_bytes)
        lines = ['# GeoAlibi offline rehearsal', '',
                 '**All images below are procedural illustrations, not satellite benchmark evidence.**', '',
                 'No credentials, API calls, model downloads or live ledger access are used.',
                 'Open index.html locally for the interactive gallery; RECORDING_SCRIPT.md provides a three-minute rehearsal draft. Confirm actual organizer requirements before recording/submitting.',
                 'Open each PNG locally. Each ZIP contains a report, source/derived images and an unsigned checksum manifest.',
                 'Verify a ZIP with `python scripts/verify_packet.py PATH_TO_ZIP` from the source repository.', '',
                 'Before recording, use the matching source checkout: `python scripts/verify_demo_bundle.py PATH_TO_THIS_DIRECTORY`.',
                 'Optionally supply `--expected-source-sha256 SHA256` obtained independently from the matching checkout/CI. Unsigned checksums do not authenticate a bundle.', '',
                 '## Evidence limits', '',
                 f"Saved eight-scene diagnostic: U-Net proposal F1 {100*evidence['arms']['unet']['metrics']['proposals']['f1']:.2f}%; RGB proposal F1 {100*evidence['arms']['baseline']['metrics']['proposals']['f1']:.2f}%.",
                 f"U-Net supported recall {100*evidence['arms']['unet']['metrics']['supported']['recall']:.2f}%; supported precision is undefined when no pixels are accepted. Registration flagged reliable in {evidence['arms']['unet']['registration_flagged_reliable_pairs']}/{evidence['pair_count']} scenes.",
                 'This is a saved small test-subset diagnostic, not full-benchmark accuracy or a new inference run. Original imagery, labels and model weights are excluded.',
                 '[Arithmetic-checked evidence summary](recorded-research-evidence.json) · [Frozen input hashes](research-inputs.json) · [Saved baseline report](research-baseline.json) · [Saved U-Net report](research-unet.json)',
                 'The separate LoFTR research audit found 1/7 actual candidate-consistent alignments, not independently verified truth.',
                 'The corrected SAM adapter is protocol-tested; real satellite segmentation quality and independent landmark review remain outstanding.', '',
                 '## Scenarios', '']
        for item in results:
            case = item['case']
            lines.extend([f"### {item['title']}", '', f"Counts: {json.dumps(item['counts'])}", '',
                          f'![Procedural before image]({case}-before.png)',
                          f'![Procedural candidate overlay]({case}-overlay.png)', '', f'[Evidence packet]({case}.zip)', ''])
        (stage / 'README.md').write_text('\n'.join(lines) + '\n')
        (stage / 'index.html').write_text(render_player(results, evidence, summary['source_manifest_sha256']))
        (stage / 'RECORDING_SCRIPT.md').write_text(recording_script(evidence))
        manifest = {'schema': 'geoalibi-demo-bundle-v1',
                    'warning': 'Unsigned checksums establish content consistency only, not authenticity or accuracy.',
                    'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.iterdir())}}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # Same-filesystem directory move: incomplete build output is never published.
        if output.exists():
            raise ValueError('Output appeared during generation; refusing to overwrite.')
        shutil.move(str(stage), output)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build_bundle(args.output)
    print(f"Built {len(report['scenarios'])} procedural scenarios; all packet checksums verified; zero model calls.")

"""Check an extracted rehearsal bundle without executing its HTML or contacting providers."""
import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import Path

from geoalibi.demo import CASES
from geoalibi.demo_player import render_player, recording_script
from geoalibi.dossier import verify_packet
from geoalibi.release_evidence import FILES, evidence_from_bytes

MAX_FILE = 40 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))


def verify_bundle(directory, expected_source_sha256=None):
    """Unsigned consistency only. An external source pin additionally binds the source manifest."""
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Require an extracted regular bundle directory.')
    expected = {'manifest.json', 'summary.json', 'SOURCE_MANIFEST.json', 'README.md',
                'index.html', 'RECORDING_SCRIPT.md', 'recorded-research-evidence.json'}
    expected.update('research-' + key + '.json' for key in FILES)
    expected.update(case + suffix for case in CASES for suffix in ('.zip', '-before.png', '-overlay.png'))
    entries = list(directory.iterdir())
    if {p.name for p in entries} != expected:
        raise ValueError('Bundle has missing or unexpected files.')
    total = 0
    for path in entries:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
            raise ValueError('Bundle entries must be bounded regular files: ' + path.name)
        total += info.st_size
    if total > MAX_TOTAL:
        raise ValueError('Bundle exceeds total size limit.')
    content = {p.name: p.read_bytes() for p in entries}
    if any(len(data) > MAX_FILE for data in content.values()) or sum(map(len, content.values())) > MAX_TOTAL:
        raise ValueError('Bundle changed size during reading.')
    manifest = read_json(content['manifest.json'])
    if manifest.get('schema') != 'geoalibi-demo-bundle-v1' or set(manifest['files']) != expected - {'manifest.json'}:
        raise ValueError('Unsupported or incomplete bundle manifest.')
    for name, sha in manifest['files'].items():
        if sha != digest(content[name]):
            raise ValueError('Bundle checksum mismatch: ' + name)
    source_sha = digest(content['SOURCE_MANIFEST.json'])
    if expected_source_sha256 is not None:
        if not re.fullmatch('[0-9a-f]{64}', expected_source_sha256) or source_sha != expected_source_sha256:
            raise ValueError('External source-manifest pin mismatch.')
    sources = read_json(content['SOURCE_MANIFEST.json'])
    raw = {key: content['research-' + key + '.json'] for key in FILES}
    for key, path in FILES.items():
        read_json(raw[key])  # Reject ambiguous JSON before arithmetic validation.
        if sources.get(path) != digest(raw[key]):
            raise ValueError('Research report differs from source manifest: ' + key)
    evidence = evidence_from_bytes(raw)
    if read_json(content['recorded-research-evidence.json']) != evidence:
        raise ValueError('Saved evidence summary disagrees with rechecked research reports.')
    summary = read_json(content['summary.json'])
    if (summary.get('schema') != 'geoalibi-offline-demo-v1' or summary.get('synthetic') is not True
            or type(summary.get('seed')) is not int or summary['seed'] != 18
            or summary.get('source_manifest_sha256') != source_sha
            or type(summary.get('api_calls')) is not int or summary['api_calls'] != 0
            or type(summary.get('new_api_reservations_usd')) not in (int, float)
            or summary['new_api_reservations_usd'] != 0
            or summary.get('recorded_real_evidence') != 'recorded-research-evidence.json'):
        raise ValueError('Invalid procedural bundle summary or source binding.')
    scenarios = summary['scenarios']
    if [s['case'] for s in scenarios] != list(CASES):
        raise ValueError('Require each procedural scenario exactly once in canonical order.')
    for item in scenarios:
        case = item['case']
        packet = content[case + '.zip']
        checked = verify_packet(packet)
        with zipfile.ZipFile(io.BytesIO(packet)) as archive:
            report = read_json(archive.read('report.json'))
            if (report.get('id') != 'procedural-' + case or checked['run_id'] != report['id']
                    or report.get('synthetic') is not True or item['title'] != CASES[case]
                    or report.get('title') != 'PROCEDURAL ILLUSTRATION: ' + item['title']
                    or item['counts'] != report['counts'] or item['engine'] != report['engine']
                    or item['packet_files_verified'] != len(checked['files'])
                    or any(item[key + '_status'] != 'not_requested' or
                           report[key]['status'] != 'not_requested' for key in ('meta', 'sam'))):
                raise ValueError('Scenario and evidence packet disagree: ' + case)
            for image in ('before', 'overlay'):
                if archive.read('images/' + image + '.png') != content[case + '-' + image + '.png']:
                    raise ValueError('Gallery image differs from evidence packet: ' + case)
    if content['index.html'].decode() != render_player(scenarios, evidence, source_sha):
        raise ValueError('Player differs from checked scenario/research evidence or verifier template.')
    if content['RECORDING_SCRIPT.md'].decode() != recording_script(evidence):
        raise ValueError('Recording guide differs from checked research evidence.')
    return {'schema': 'geoalibi-demo-verification-v1', 'files_verified': len(expected) - 1,
            'scenario_packets_verified': len(scenarios), 'saved_research_pairs': evidence['pair_count'],
            'source_manifest_sha256': source_sha, 'external_source_pin_checked': expected_source_sha256 is not None,
            'scope': 'Unsigned content consistency and saved-report arithmetic only; not authenticity, '
                     'execution proof, new inference, satellite accuracy or submission readiness.'}

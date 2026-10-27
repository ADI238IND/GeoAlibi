"""Auditable challenge log and evidence requests; no untested hypothesis is certified."""
import hashlib
import io
import json
import zipfile


def challenge_log(checks, alignment, perturbations):
    return [
        {"id": "registration", "hypothesis": "The apparent change is caused by image misalignment", "result": "unresolved" if not alignment['reliable'] else "explained" if checks['alignment_reduction']>.65 else "persists",
         "measurement": checks['alignment_reduction'], "scope": "Global affine/translation hypotheses only; parallax remains possible."},
        {"id": "illumination", "hypothesis": "A global lighting change explains the pixels", "result": "explained" if checks['lighting_reduction']>.65 else "persists",
         "measurement": checks['lighting_reduction'], "scope": "A fitted global channel-wise correction; local shadows are not ruled out."},
        {"id": "local_appearance", "hypothesis": "A local shadow or appearance change preserves the underlying structure", "result": "plausible" if checks['local_luminance_correlation']>=.9 else "unresolved",
         "measurement": checks['local_luminance_correlation'], "scope": "Correlation is diagnostic, not causal evidence."},
        {"id": "registration_stress", "hypothesis": "The finding depends on a one-pixel registration choice", "result": "sensitive" if checks.get('worst_perturbation_survival', min(p['survival'] for p in perturbations))<.55 else "persists",
         "experiments": perturbations, "scope": "Four bounded perturbations only; not every possible registration error."},
        {"id": "season_cloud_sensor", "hypothesis": "Season, cloud, parallax or sensor differences explain the finding", "result": "untested", "scope": "No acquisition metadata, multispectral cloud mask, elevation model or independent observation was supplied."},
    ]


def evidence_requests(checks, alignment):
    requests = []
    if not alignment['reliable']:
        requests.append({"priority": 1, "reason": "Registration could not be established", "request": "Provide larger surrounding image crops with stable landmarks, plus co-registration metadata or independently checked tie points.", "resolves": ["registration"]})
    if checks['local_luminance_correlation']>=.9:
        requests.append({"priority": 2, "reason": "A local appearance explanation remains plausible", "request": "Obtain a third acquisition with a different sun angle and inspect whether the same structure persists.", "resolves": ["local_appearance"]})
    requests.append({"priority": 3, "reason": "Important alternatives have not been tested", "request": "Compare acquisition dates, sensor/view angles and cloud quality flags; use an independent acquisition or ground observation before acting.", "resolves": ["season_cloud_sensor"]})
    return requests


def build_packet(report, assets):
    """Checksums detect modified contents; they are not a signature or authenticity proof."""
    files = {"report.json": json.dumps(report, sort_keys=True, indent=2, allow_nan=False).encode()}
    files.update({"images/"+name+".png": data for name,data in assets.items()})
    manifest = {"format": "geoalibi-evidence-1", "hash_algorithm": "sha256", "run_id": report['id'],
                "warning": "Unsigned content-integrity manifest. Not proof of acquisition provenance, correctness, or real-world change.",
                "files": {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name,data in files.items()}}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
        z.writestr('manifest.json', json.dumps(manifest, sort_keys=True, indent=2))
    return buffer.getvalue()


def verify_packet(data):
    if len(data)>40*1024*1024:raise ValueError('Packet is too large.')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        if len(names)!=len(set(names)) or len(names)>40:raise ValueError('Duplicate or excessive packet entries.')
        if sum(i.file_size for i in z.infolist())>80*1024*1024:raise ValueError('Expanded packet exceeds limits.')
        manifest = json.loads(z.read('manifest.json'))
        if manifest.get('format')!='geoalibi-evidence-1' or set(names)!=set(manifest['files'])|{'manifest.json'}:
            raise ValueError('Packet contents do not match the manifest.')
        for name,entry in manifest['files'].items():
            if name.startswith('/') or '..' in name.split('/') or '\\' in name:raise ValueError('Unsafe packet path.')
            content=z.read(name)
            if len(content)!=entry['bytes'] or hashlib.sha256(content).hexdigest()!=entry['sha256']:
                raise ValueError('Content integrity check failed: '+name)
        return manifest

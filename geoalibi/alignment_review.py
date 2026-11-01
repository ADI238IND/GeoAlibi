"""Blind original-image collection and no-refit scoring of frozen production transforms."""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from geoalibi.benchmark_manifest import dataset_records, validate_frozen_manifest
from geoalibi.evaluation import checked_landmarks, load_landmark_manifest
from geoalibi.independent_alignment import landmark_errors
from geoalibi.vision import decode_image, data_url


def frozen_inputs(dataset, manifest_path):
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    limit = manifest.get('subset_limit', 0)
    if type(limit) is not int or limit < 0:
        raise ValueError('Frozen subset limit must be a nonnegative integer.')
    records = dataset_records(dataset, limit)
    digest = validate_frozen_manifest(manifest_path, records, limit)
    return records, digest, limit


def checked_images(dataset, record):
    contents = {}
    for folder in ('A', 'B', 'label'):
        data = (dataset / folder / record['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != record[folder + '_sha256']:
            raise ValueError('Source bytes changed after preflight: ' + record['file'])
        contents[folder] = data
    before, after = (decode_image(contents[key]) for key in ('A', 'B'))
    if before.shape != after.shape:
        raise ValueError('Processed original image dimensions differ.')
    return contents, before, after


def build_review(dataset, manifest_path, output):
    """Embed only processed A/B originals; never load predictions or label pixels."""
    if output.exists():
        raise ValueError('Output exists; choose a new directory.')
    records, digest, _ = frozen_inputs(dataset, manifest_path)
    if len(records) > 16:
        raise ValueError('Blind review packs are limited to 16 frozen pairs.')
    items = []
    for record in records:
        _, before, after = checked_images(dataset, record)
        items.append({'file': record['file'], 'before_sha256': record['A_sha256'],
                      'after_sha256': record['B_sha256'], 'label_sha256': record['label_sha256'],
                      'width': before.shape[1], 'height': before.shape[0],
                      'before': data_url(before), 'after': data_url(after)})
    task = {'schema': 'geoalibi-blind-alignment-task-v1', 'dataset_manifest_sha256': digest, 'pairs': items}
    # Escaping '<' prevents filenames from closing the inline JSON script element.
    payload = json.dumps(task, ensure_ascii=True).replace('<', '\\u003c')
    template = (Path(__file__).parent / 'static/alignment-review.html').read_text()
    page = template.replace('/* REVIEW_TASK */', payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='alignment-review-', dir=output.parent) as temporary:
        stage = Path(temporary) / 'bundle'; stage.mkdir()
        (stage / 'review.html').write_text(page)
        summary = {'schema': task['schema'], 'dataset_manifest_sha256': digest,
                   'pairs': [{k: v for k, v in item.items() if k not in ('before', 'after')} for item in items],
                   'html_sha256': hashlib.sha256(page.encode()).hexdigest(),
                   'scope': 'Original A/B images only. No label pixels, predictions, model matches or fitted transforms. '
                            'Collection/review declarations are assertions, not authenticated independence. '
                            'Image source terms still apply; do not publish this bundle.'}
        (stage / 'task.json').write_text(json.dumps(summary, indent=2) + '\n')
        if output.exists():
            raise ValueError('Output appeared during generation.')
        shutil.move(str(stage), output)
    return summary


def score_benchmark(benchmark_path, annotation_path, dataset, manifest_path):
    records, digest, limit = frozen_inputs(dataset, manifest_path)
    raw = benchmark_path.read_bytes(); benchmark = json.loads(raw)
    if (benchmark.get('dataset_frozen') is not True or benchmark.get('dataset_manifest_sha256') != digest
            or type(benchmark.get('subset_limit')) is not int or benchmark['subset_limit'] != limit):
        raise ValueError('Benchmark does not bind the exact frozen input manifest and limit.')
    annotations, annotation_hash = load_landmark_manifest(annotation_path)
    annotation_raw = annotation_path.read_bytes()
    if hashlib.sha256(annotation_raw).hexdigest() != annotation_hash:
        raise ValueError('Annotations changed during validation.')
    annotation_data = json.loads(annotation_raw)
    if annotation_data.get('dataset_manifest_sha256') != digest:
        raise ValueError('Reviewed manifest belongs to a different frozen collection task.')
    rows = benchmark.get('pair_results', [])
    if (not isinstance(rows, list) or len(rows) != len(records) or benchmark.get('pairs') != len(records)
            or {r['file'] for r in rows} != {r['file'] for r in records}
            or set(annotations) != {r['file'] for r in records}):
        raise ValueError('Benchmark and reviewed filenames must exactly cover every frozen pair.')
    indexed = {row['file']: row for row in rows}
    results = []
    for record in records:
        name = record['file']; row = indexed[name]; annotation = annotations[name]
        if row.get('source_hashes') != record:
            raise ValueError('Benchmark source hashes differ: ' + name)
        if (annotation.get('collection_basis') != 'independent-original-image-review'
                or annotation.get('reviewed') is not True):
            raise ValueError('Require explicit independent original-image collection and completed review.')
        contents, before, _ = checked_images(dataset, record)
        checked_landmarks(annotation, contents['A'], contents['B'], contents['label'])
        alignment = row['alignment']
        if type(alignment.get('reliable')) is not bool or alignment.get('matrix') is None:
            raise ValueError('Require the saved production transform and boolean reliability decision.')
        measurements = landmark_errors(alignment['matrix'], annotation['landmarks'], before.shape[1], before.shape[0])
        results.append({'file': name, 'production_reliable': alignment['reliable'],
                        'production_method': alignment['method'], 'frozen_matrix': alignment['matrix'],
                        'annotator': annotation['annotator'], 'reviewer': annotation['reviewer'], **measurements})
    return {'schema': 'geoalibi-benchmark-alignment-review-v1', 'pair_count': len(results), 'pairs': results,
            'benchmark_sha256': hashlib.sha256(raw).hexdigest(), 'dataset_manifest_sha256': digest,
            'annotation_manifest_sha256': annotation_hash,
            'production_reliable_count': sum(row['production_reliable'] for row in results),
            'limitations': 'Every point scores the saved transform without refitting or production promotion. '
                           'Identities, completed review and independence are declarations, not authentication. '
                           'The benchmark hash binds a supplied unsigned report, not its authenticity. '
                           'Pixel residuals do not establish physical change or geographic accuracy.'}

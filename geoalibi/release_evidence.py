"""Derive demo evidence from frozen saved reports; never infer readiness from test success."""
import hashlib
import json
import math
from pathlib import Path

from geoalibi.verification_metrics import summarize_transitions
from geoalibi.pretrained import SHA256, REVISION

FILES = {'inputs': 'docs/EXPANDED_EVAL_INPUTS.json',
         'baseline': 'docs/EXPANDED_BASELINE_EVALUATION.json',
         'unet': 'docs/EXPANDED_UNET_EVALUATION.json'}
STAGES = ('raw_rgb', 'proposals', 'supported')
COUNTS = ('tp', 'fp', 'fn', 'tn')
TRANSITIONS = ('pixels', 'truth_change_pixels', 'proposal_pixels', 'supported_pixels',
               'proposal_true_positive_pixels', 'proposal_false_positive_pixels',
               'removed_true_positive_pixels', 'removed_false_positive_pixels',
               'added_true_positive_pixels', 'added_false_positive_pixels', 'retained_proposal_pixels')


def integers(record, keys):
    if any(type(record.get(key)) is not int or record[key] < 0 for key in keys):
        raise ValueError('Evidence counts must be nonnegative integers.')
    return {key: record[key] for key in keys}


def checked_metrics(saved):
    c = integers(saved, COUNTS); tp, fp, fn = (c[key] for key in ('tp', 'fp', 'fn'))
    ratios = {'precision': tp / (tp + fp) if tp + fp else None,
              'recall': tp / (tp + fn) if tp + fn else None,
              'f1': 2 * tp / max(1, 2 * tp + fp + fn), 'iou': tp / max(1, tp + fp + fn)}
    for key, expected in ratios.items():
        value = saved.get(key)
        if ((expected is None and value is not None) or (expected is not None and
                (type(value) not in (float, int) or not math.isfinite(value) or abs(value - expected) > 1e-12))):
            raise ValueError('Saved metric disagrees with its confusion counts: ' + key)
    return {**c, **ratios}


def saved_evidence(root):
    raw = {key: (Path(root) / path).read_bytes() for key, path in FILES.items()}
    return evidence_from_bytes(raw)


def evidence_from_bytes(raw):
    """Validate saved reports supplied by a bundle without writing temporary source files."""
    documents = {key: json.loads(data) for key, data in raw.items()}
    hashes = {key: hashlib.sha256(data).hexdigest() for key, data in raw.items()}
    inputs = documents['inputs']
    records = inputs['pairs']; indexed = {r['file']: r for r in records}
    if inputs.get('schema') != 'geoalibi-benchmark-inputs-v1' or not records or len(indexed) != len(records):
        raise ValueError('Require a nonempty unique frozen input manifest.')
    arms = {}; footprint = None; alignments = None; settings = None
    for arm in ('baseline', 'unet'):
        report = documents[arm]; rows = report['pair_results']
        if (report.get('detector') != arm or report.get('dataset_frozen') is not True
                or report.get('dataset_manifest_sha256') != hashes['inputs']
                or report.get('subset_limit') != inputs['subset_limit']
                or report.get('pairs') != len(records) or len(rows) != len(records)
                or {r['file'] for r in rows} != set(indexed)):
            raise ValueError('Saved arm does not exactly cover the frozen inputs: ' + arm)
        current_settings = {key: report[key] for key in ('threshold', 'min_area', 'subset_limit')}
        if (type(current_settings['threshold']) not in (float, int) or not math.isfinite(current_settings['threshold'])
                or not 0 < current_settings['threshold'] < 1 or type(current_settings['min_area']) is not int
                or current_settings['min_area'] <= 0 or settings is not None and settings != current_settings):
            raise ValueError('Compared arms require the same valid evaluation settings.')
        settings = current_settings
        model = None
        totals = {stage: dict.fromkeys(COUNTS, 0) for stage in STAGES}
        transitions = dict.fromkeys(TRANSITIONS, 0); scenes = []; geometry = {}; dimensions = {}
        for row in rows:
            if row['source_hashes'] != indexed[row['file']]:
                raise ValueError('Saved source hashes differ: ' + row['file'])
            if arm == 'unet':
                provenance = row.get('model_provenance') or {}
                if (provenance.get('sha256') != SHA256 or provenance.get('revision') != REVISION
                        or provenance.get('weights_license') != 'CC-BY-4.0' or model is not None and model != provenance):
                    raise ValueError('Pinned pretrained provenance is missing or inconsistent.')
                model = provenance
            metrics = {stage: checked_metrics(row['metrics'][stage]) for stage in STAGES}
            sizes = {(sum(m[k] for k in COUNTS), m['tp'] + m['fn']) for m in metrics.values()}
            if len(sizes) != 1 or next(iter(sizes))[0] <= 0:
                raise ValueError('Pixel footprint or truth count differs between stages.')
            dimensions[row['file']] = next(iter(sizes))
            decision = row['alignment']['reliable']; review = row['all_candidates_abstained']
            if type(decision) is not bool or type(review) is not bool:
                raise ValueError('Saved reliability/review decisions must be boolean.')
            geometry[row['file']] = row['alignment']
            t = integers(row['verification_tradeoff'], TRANSITIONS)
            p, s = metrics['proposals'], metrics['supported']
            if (t['pixels'] != dimensions[row['file']][0] or t['truth_change_pixels'] != p['tp'] + p['fn']
                    or t['proposal_pixels'] != p['tp'] + p['fp'] or t['supported_pixels'] != s['tp'] + s['fp']
                    or t['proposal_true_positive_pixels'] != p['tp'] or t['proposal_false_positive_pixels'] != p['fp']
                    or t['removed_true_positive_pixels'] > p['tp'] or t['removed_false_positive_pixels'] > p['fp']
                    or s['tp'] != p['tp'] - t['removed_true_positive_pixels'] + t['added_true_positive_pixels']
                    or s['fp'] != p['fp'] - t['removed_false_positive_pixels'] + t['added_false_positive_pixels']
                    or t['retained_proposal_pixels'] != t['proposal_pixels'] - t['removed_true_positive_pixels'] - t['removed_false_positive_pixels']):
                raise ValueError('Saved verification transitions do not conserve proposal/support counts.')
            for key in TRANSITIONS: transitions[key] += t[key]
            for stage in STAGES:
                for key in COUNTS: totals[stage][key] += metrics[stage][key]
            scenes.append({'file': row['file'], 'registration_flagged_reliable': decision,
                           'all_inspected_candidates_in_review': review, 'metrics': metrics})
        pooled = {stage: checked_metrics(report['metrics'][stage]) for stage in STAGES}
        if any(any(pooled[s][k] != totals[s][k] for k in COUNTS) for s in STAGES):
            raise ValueError('Pooled confusion counts differ from all scene counts.')
        if integers(report['verification_tradeoff'], TRANSITIONS) != transitions:
            raise ValueError('Pooled transitions differ from all scene transitions.')
        if footprint is not None and (footprint != dimensions or alignments != geometry):
            raise ValueError('Compared arms use different footprints, truth or alignment.')
        footprint, alignments = dimensions, geometry
        review_count = sum(r['all_inspected_candidates_in_review'] for r in scenes)
        if report['all_candidates_abstained_pairs'] != review_count:
            raise ValueError('Saved all-review count disagrees with scene records.')
        arms[arm] = {'metrics': pooled, 'recorded_model_provenance': model, 'verification_tradeoff': summarize_transitions(transitions),
                     'registration_flagged_reliable_pairs': sum(r['registration_flagged_reliable'] for r in scenes),
                     'zero_supported_pixel_pairs': sum(r['metrics']['supported']['tp'] + r['metrics']['supported']['fp'] == 0 for r in scenes),
                     'all_inspected_candidates_in_review_pairs': review_count, 'scenes': scenes}
    return {'schema': 'geoalibi-release-evidence-v1', 'pair_count': len(records),
            'settings': settings, 'source_files': FILES, 'source_sha256': hashes, 'arms': arms,
            'scope': 'Saved small prospective test-subset diagnostic; source hashes and arithmetic checked, '
                     'original imagery and model inference not replayed by this builder. '
                     'No full-benchmark, independently audited geographic/training split or calibrated-risk claim.',
            'submission_readiness': 'not established',
            'remaining_evidence': ['Independent human landmark collection and separate review',
                                   'Corrected real-image Meta validation with secure credentials, reconciled ledger and billing',
                                   'Authenticated participant submission requirements and final rehearsal'],
            'cost_scope': 'This summary makes no API calls or reservations and is not an account billing statement. '
                          'Historical $0.54 reservation remains unreconciled; do not reset the ledger.'}

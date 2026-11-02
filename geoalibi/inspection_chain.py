"""Validate one offline inspection path. Integrity/completeness is not change truth."""
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .dossier import verify_packet

MAX_PACKETS = 16
MAX_TOTAL_BYTES = 256 * 1024 * 1024
SOURCES = ('before', 'after', 'proposal_mask')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def nonnegative(value):
    if type(value) is not int or value < 0:
        raise ValueError('Inspection counts must be nonnegative integers.')
    return value


def sha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Missing or invalid frozen-context hash.')
    return value


def raster(data, size, mask=False):
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'PNG' or image.size != size or image.mode != ('L' if mask else 'RGB'):
            raise ValueError('Packet raster dimensions, PNG format or mode differ from the report.')
        pixels = np.asarray(image).copy()
    if mask:
        if not np.isin(pixels, [0, 255]).all():
            raise ValueError('Inspection masks must be binary 0/255 rasters.')
        return pixels > 0
    return pixels


def component_stats(mask):
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    return sorted(tuple(int(x) for x in row) for row in stats[1:count])


def eligible_geometry(proposal, min_area):
    if type(min_area) is not int or min_area <= 0:
        raise ValueError('Invalid saved minimum area.')
    clean = cv2.morphologyEx(proposal.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(clean, connectivity=8)
    selected = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= min_area]
    return np.isin(labels, selected), len(selected)


def load_packet(path):
    data = path.read_bytes()
    manifest = verify_packet(data)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        report = json.loads(archive.read('report.json'))
        run_id = report['id']
        if not re.fullmatch('[0-9a-f]{32}', run_id) or manifest['run_id'] != run_id:
            raise ValueError('Packet and report investigation identifiers differ.')
        if report.get('engine') != 'counterfactual-0.4.2':
            raise ValueError('This checker requires the v0.4.2 saved proposal-geometry protocol.')
        width, height = report['width'], report['height']
        if any(type(n) is not int or not 64 <= n <= 1024 for n in (width, height)):
            raise ValueError('Invalid processed image dimensions.')
        raw = {name: archive.read('images/' + name + '.png') for name in SOURCES}
        before, after = (raster(raw[key], (width, height)) for key in ('before', 'after'))
        proposal = raster(raw['proposal_mask'], (width, height), mask=True)
        supported = raster(archive.read('images/supported_mask.png'), (width, height), mask=True)
        omitted = raster(archive.read('images/omitted_mask.png'), (width, height), mask=True)
    if report['input_hash'] != digest(before.tobytes() + after.tobytes()):
        raise ValueError('Saved original-image pixels disagree with the input hash.')
    inspection = report['inspection']; rows = report['regions']
    offset = nonnegative(inspection['offset']); total = nonnegative(report['candidate_count'])
    if (total == 0 and offset != 0) or (total > 0 and offset >= total) or offset % 24:
        raise ValueError('Invalid inspection offset.')
    count = min(24, total - offset)
    after_count = total - offset - count
    expected = {'batch_size': 24, 'eligible_regions': total, 'inspected_regions': count,
                'regions_before_batch': offset, 'regions_after_batch': after_count,
                'omitted_regions': total - count, 'next_offset': offset + count if after_count else None,
                'start_rank': offset + 1 if count else None, 'end_rank': offset + count if count else None}
    if len(rows) != count or any(type(inspection.get(k)) is not type(v) or inspection[k] != v for k, v in expected.items()):
        raise ValueError('Batch rank bounds, counts or next offset are inconsistent.')
    if [r['id'] for r in rows] != [f'R{i:02}' for i in range(offset + 1, offset + count + 1)]:
        raise ValueError('Region IDs do not cover the exact batch ranks.')
    for key in ('eligible_region_pixels', 'inspected_region_pixels', 'omitted_region_pixels', 'supported_pixels', 'proposal_pixels'):
        nonnegative(inspection[key])
    if int(proposal.sum()) != inspection['proposal_pixels']:
        raise ValueError('Proposal raster and recorded pixel count differ.')
    eligible = nonnegative(inspection['eligible_region_pixels'])
    inspected = sum(nonnegative(row['pixels']) for row in rows)
    if (inspected != inspection['inspected_region_pixels'] or inspected > eligible
            or eligible - inspected != inspection['omitted_region_pixels']
            or int(omitted.sum()) != inspection['omitted_region_pixels']):
        raise ValueError('Eligible, inspected and omitted pixel counts disagree.')
    eligible_mask, component_count = eligible_geometry(proposal, report['min_area'])
    inspected_mask = eligible_mask & ~omitted
    expected_stats = []
    for row in rows:
        if len(row['bbox']) != 4 or any(type(x) is not int for x in row['bbox']):
            raise ValueError('Invalid recorded component bounds.')
        expected_stats.append(tuple(row['bbox']) + (row['pixels'],))
    if (component_count != total or int(eligible_mask.sum()) != eligible or (omitted & ~eligible_mask).any()
            or component_stats(inspected_mask) != sorted(expected_stats)
            or (supported & ~inspected_mask).any()):
        raise ValueError('Saved region bounds or omission/support masks disagree with proposal geometry.')
    component_count_current, component_labels, stats, _ = cv2.connectedComponentsWithStats(inspected_mask.astype(np.uint8), connectivity=8)
    declared = {}
    for row in rows:
        key = tuple(row['bbox']) + (row['pixels'],)
        if key in declared and declared[key] != row['verdict']:
            raise ValueError('Ambiguous component verdict mapping.')
        declared[key] = row['verdict']
    for i in range(1, component_count_current):
        verdict = declared[tuple(int(x) for x in stats[i])]
        has_supported_pixels = bool((supported & (component_labels == i)).any())
        if has_supported_pixels != (verdict == 'supported'):
            raise ValueError('Supported mask disagrees with the component verdicts.')
    if (int(supported.sum()) != nonnegative(report['supported_changed_pixels'])
            or inspection['supported_pixels'] != report['supported_changed_pixels']
            or (supported & omitted).any()):
        raise ValueError('Supported pixels are inconsistent or overlap omitted candidates.')
    if type(report['alignment']['reliable']) is not bool:
        raise ValueError('Reliability must be a saved boolean decision.')
    if not report['alignment']['reliable'] and supported.any():
        raise ValueError('Unreliable registration cannot claim supported pixels.')
    for verdict in ('supported', 'artifact', 'review'):
        if nonnegative(report['counts'][verdict]) != sum(row['verdict'] == verdict for row in rows):
            raise ValueError('Verdict totals differ from the recorded regions.')
    if any(row['verdict'] not in ('supported', 'artifact', 'review') for row in rows):
        raise ValueError('Unknown automated region verdict.')
    sha(report['analysis_context_sha256']); sha(report['analysis_source_sha256'])
    environment = report['analysis_environment']
    if not isinstance(environment, dict) or any(not isinstance(environment.get(k), str) or not environment[k] for k in ('numpy', 'opencv')):
        raise ValueError('Missing recorded numerical environment.')
    return {'report': report, 'packet_sha256': digest(data), 'source_asset_sha256': {k: digest(v) for k, v in raw.items()},
            'raster_sha256': {'input': report['input_hash'], 'proposal': digest(proposal.tobytes())},
            'supported': supported, 'omitted': omitted, 'size': (width, height), 'inspected_pixels': inspected}


def verify_chain(paths):
    paths = [Path(p) for p in paths]
    if not 1 <= len(paths) <= MAX_PACKETS:
        raise ValueError(f'Provide 1–{MAX_PACKETS} packets from one unbranched inspection path.')
    if any(p.stat().st_size > 40 * 1024 * 1024 for p in paths) or sum(p.stat().st_size for p in paths) > MAX_TOTAL_BYTES:
        raise ValueError('Combined packet input exceeds the offline verifier limits.')
    try:
        packets = [load_packet(path) for path in paths]
        indexed = {p['report']['id']: p for p in packets}
        if len(indexed) != len(packets):
            raise ValueError('Duplicate investigation packets would double-count coverage.')
        roots = [p for p in packets if not p['report'].get('lineage')]
        if len(roots) != 1 or roots[0]['report']['inspection']['offset'] != 0:
            raise ValueError('Include exactly one original offset-zero investigation.')
        root = roots[0]; root_report = root['report']; root_id = root_report['id']; children = {}
        stable = ('analysis_context_sha256', 'analysis_source_sha256', 'analysis_environment', 'engine',
                  'threshold', 'min_area', 'candidate_count', 'alignment', 'detector', 'model_provenance')
        for packet in packets:
            report = packet['report']
            if (any(report.get(key) != root_report.get(key) for key in stable)
                    or packet['raster_sha256'] != root['raster_sha256'] or packet['size'] != root['size']
                    or report['inspection']['eligible_region_pixels'] != root_report['inspection']['eligible_region_pixels']):
                raise ValueError('Packets disagree on frozen context, settings, geometry, model or source pixels.')
            if packet is root:
                continue
            lineage = report['lineage']; parent_id = lineage['source_run_id']
            if parent_id not in indexed or lineage['root_run_id'] != root_id:
                raise ValueError('Missing ancestor or wrong original investigation.')
            if parent_id in children:
                raise ValueError('Forked inspection paths cannot be combined or double-counted.')
            parent = indexed[parent_id]
            if (lineage['analysis_context_sha256'] != report['analysis_context_sha256']
                    or lineage['source_asset_sha256'] != parent['source_asset_sha256']
                    or report['inspection']['offset'] != parent['report']['inspection']['next_offset']):
                raise ValueError('Parent linkage, source asset hashes or rank continuity disagree.')
            if report['meta']['status'] != 'not_requested' or report['sam']['status'] != 'not_requested':
                raise ValueError('Follow-ups must preserve the no-provider-rerun contract.')
            children[parent_id] = packet
        ordered = []; current = root; seen = set()
        while current is not None:
            if current['report']['id'] in seen:
                raise ValueError('Cyclic inspection lineage.')
            seen.add(current['report']['id'])
            ordered.append(current); current = children.get(current['report']['id'])
        if len(ordered) != len(packets):
            raise ValueError('Disconnected or cyclic inspection lineage.')
        supported_union = np.zeros_like(root['supported']); omission_hits = np.zeros_like(root['omitted'], dtype=np.uint8)
        inspected_pixels = 0; batches = []; region_ids = []
        for packet in ordered:
            report = packet['report']; c = report['inspection']
            if (supported_union & packet['supported']).any():
                raise ValueError('Supported masks overlap across supposedly disjoint batches.')
            supported_union |= packet['supported']; omission_hits += packet['omitted']; inspected_pixels += packet['inspected_pixels']
            region_ids.extend(row['id'] for row in report['regions'])
            batches.append({'run_id': report['id'], 'packet_sha256': packet['packet_sha256'],
                            'offset': c['offset'], 'inspected_regions': c['inspected_regions'],
                            'supported_pixels': report['supported_changed_pixels']})
        if len(region_ids) != len(set(region_ids)):
            raise ValueError('Duplicate globally ranked regions.')
        spatial_checked = len(ordered) > 1
        if spatial_checked:
            eligible_mask = omission_hits > 0
            if (int(eligible_mask.sum()) != root_report['inspection']['eligible_region_pixels']
                    or not np.isin(omission_hits[eligible_mask], [len(ordered) - 1, len(ordered)]).all()
                    or int(((omission_hits == len(ordered) - 1) & eligible_mask).sum()) != inspected_pixels
                    or (supported_union & ~eligible_mask).any()):
                raise ValueError('Omission masks do not partition the same eligible pixel footprint.')
        remaining = root_report['candidate_count'] - len(region_ids)
        complete = remaining == 0 and ordered[-1]['report']['inspection']['next_offset'] is None
        return {'schema': 'geoalibi-inspection-chain-v1', 'root_run_id': root_id, 'batch_count': len(ordered),
                'analysis_context_sha256': root_report['analysis_context_sha256'], 'batches': batches,
                'eligible_regions': root_report['candidate_count'], 'inspected_regions': len(region_ids),
                'remaining_regions': remaining, 'inspection_complete': complete,
                'inspected_eligible_pixels': inspected_pixels, 'supported_pixel_union': int(supported_union.sum()),
                'cross_batch_spatial_partition_checked': spatial_checked, 'proposal_geometry_checked': True,
                'registration_flagged_reliable': root_report['alignment']['reliable'],
                'real_world_change_verification': 'not established by this check',
                'scope': 'One supplied unsigned packet path; checks content integrity, linkage and internal consistency, '
                         'not acquisition authenticity, actual execution, independent review, satellite accuracy or physical change. '
                         'Completeness covers eligible candidates at recorded settings, excluding small filtered components. '
                         'Pixel counts are image coordinates, not physical area. Saved binary proposal geometry is replayed; '
                         'no alignment fitting, model inference or paid API calls.'}
    except (KeyError, TypeError, zipfile.BadZipFile) as exc:
        raise ValueError('Malformed or unsupported inspection packet chain.') from exc

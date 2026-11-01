"""Deterministic RGB baseline. Scores are diagnostic measurements, not probabilities."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

VERSION = "counterfactual-0.4.2"
MAX_SIDE = 1024
SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def decode_image(data: bytes) -> np.ndarray:
    if len(data) > 12 * 1024 * 1024:
        raise ValueError("Each image must be 12 MB or smaller.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as im:
                if im.width * im.height > 24_000_000:
                    raise ValueError("Image exceeds 24 megapixels.")
                im = ImageOps.exif_transpose(im)
                if min(im.size) < 64:
                    raise ValueError("Images must be at least 64 × 64 pixels.")
                im.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
                return np.asarray(im.convert("RGB")).copy()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("Image exceeds safe decoding limits.") from exc
    except (OSError, SyntaxError) as exc:
        raise ValueError("Could not decode image. Use PNG, JPEG, or WebP.") from exc


def png(image: np.ndarray) -> bytes:
    out = io.BytesIO()
    Image.fromarray(image.astype(np.uint8)).save(out, "PNG")
    return out.getvalue()


def data_url(image: np.ndarray) -> str:
    return "data:image/png;base64," + base64.b64encode(png(image)).decode()


def gray(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def difference(a, b):
    af = cv2.GaussianBlur(a.astype(np.float32), (3, 3), 0)
    bf = cv2.GaussianBlur(b.astype(np.float32), (3, 3), 0)
    return np.sqrt(np.mean((af - bf) ** 2, axis=2)) / 255


def normalize(a, b, valid):
    """Robust per-channel affine illumination fit over the overlapping footprint."""
    out = b.astype(np.float32).copy()
    fits = []
    for channel in range(3):
        x = b[:, :, channel][valid].astype(np.float32)[::4]
        y = a[:, :, channel][valid].astype(np.float32)[::4]
        if len(x) < 100 or np.std(x) < 4:
            fits.append([1., 0.])
            continue
        keep = np.ones(len(x), bool)
        gain, bias = 1., 0.
        for _ in range(4):
            mat = np.stack([x[keep], np.ones(keep.sum())], axis=1)
            gain, bias = np.linalg.lstsq(mat, y[keep], rcond=None)[0]
            gain = float(np.clip(gain, .5, 2.))
            bias = float(np.clip(bias, -65, 65))
            residual = np.abs(gain * x + bias - y)
            keep = residual <= max(3., np.percentile(residual, 75))
        out[:, :, channel] = gain * out[:, :, channel] + bias
        fits.append([round(gain, 4), round(bias, 3)])
    return np.clip(out, 0, 255).astype(np.uint8), fits


def alignment_evidence(matrix, source, target, phase_shift, response, texture):
    """Evidence must support the selected transform, not another candidate."""
    residuals = np.linalg.norm(source @ matrix[:, :2].T + matrix[:, 2] - target, axis=1)
    consistent = int((residuals <= 2.5).sum())
    feature_support = len(source) >= 8 and consistent >= 8 and consistent / len(source) >= .4
    translation = np.array([-phase_shift[0], -phase_shift[1]])
    phase_support = (np.isfinite(response) and response > .4
                     and np.linalg.norm(matrix[:, :2] - np.eye(2)) < .01
                     and np.linalg.norm(matrix[:, 2] - translation) <= 2.5)
    return {"selected_transform_matches": consistent,
            "feature_support": bool(feature_support), "phase_support": bool(phase_support),
            "reliable": bool(texture > 25 and (feature_support or phase_support))}


def align(a, b):
    h, w = a.shape[:2]
    ag, bg = gray(a), gray(b)
    identity = np.array([[1., 0., 0.], [0., 1., 0.]], np.float32)
    best, method, matches, inliers = identity, "identity", 0, 0
    src = dst = np.empty((0, 2), dtype=np.float32)
    orb = cv2.ORB_create(nfeatures=2500, fastThreshold=12)
    ka, da = orb.detectAndCompute(ag, None)
    kb, db = orb.detectAndCompute(bg, None)
    if da is not None and db is not None:
        pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(db, da, k=2)
        good = [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < .72 * pair[1].distance]
        matches = len(good)
        if matches >= 8:
            src = np.float32([kb[m.queryIdx].pt for m in good])
            dst = np.float32([ka[m.trainIdx].pt for m in good])
            mat, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.5)
            if mat is not None and mask is not None:
                inliers = int(mask.sum())
                scale = float(np.linalg.norm(mat[0, :2]))
                if inliers >= 8 and inliers / matches >= .4 and .95 < scale < 1.05 and np.linalg.norm(mat[:, 2]) < min(w, h) * .12:
                    best, method = mat.astype(np.float32), "ORB + RANSAC"
    # Independently compare a translation-only hypothesis with the feature fit.
    (dx, dy), response = cv2.phaseCorrelate(ag.astype(np.float32), bg.astype(np.float32))
    transforms = [(identity, "identity"), (best, method)]
    if response > .12 and abs(dx) < w * .12 and abs(dy) < h * .12:
        transforms.append((np.array([[1, 0, -dx], [0, 1, -dy]], np.float32), "phase correlation"))
    scored = []
    for mat, name in transforms:
        warped = cv2.warpAffine(b, mat, (w, h), flags=cv2.INTER_LINEAR)
        valid = cv2.warpAffine(np.ones((h, w), np.uint8), mat, (w, h), flags=cv2.INTER_NEAREST).astype(bool)
        valid = cv2.erode(valid.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        if valid.mean() < .75:
            continue
        norm, _ = normalize(a, warped, valid)
        d = difference(a, norm)[valid]
        score = float(np.mean(np.sort(d)[:max(1, int(len(d) * .8))]))
        scored.append((score, mat, name, warped, valid))
    _, best, method, warped, valid = min(scored, key=lambda item: item[0])
    texture = float(cv2.Laplacian(ag, cv2.CV_32F).var())
    evidence = alignment_evidence(best, src, dst, (dx, dy), response, texture)
    return warped, valid, {"method": method, "matrix": best.tolist(), "matches": matches, "inliers": inliers,
                            "phase_response": round(float(response), 4), **evidence,
                            "overlap": round(float(valid.mean()), 4), "texture_variance": round(texture, 2)}


@dataclass
class Analysis:
    report: dict
    images: dict[str, np.ndarray]


def investigate(a, b, *, threshold=.12, min_area=70, proposal=None, detector_fn=None, landmarks=None, region_offset=0, expected_context=None) -> Analysis:
    started = time.perf_counter()
    if a.shape != b.shape:
        raise ValueError("Use images of the same dimensions and footprint. Automatic stretching is disabled.")
    if type(region_offset) is not int or region_offset < 0:
        raise ValueError('Region offset must be a nonnegative integer.')
    h, w = a.shape[:2]
    if landmarks is not None:
        from .landmarks import register
        aligned,valid,alignment=register(a,b,landmarks)
    else:
        aligned, valid, alignment = align(a, b)
    model_scores = None
    if detector_fn is not None:
        proposal, model_scores = detector_fn(a, aligned)
    normalized, fits = normalize(a, aligned, valid)
    raw_d = difference(a, b)
    align_d = difference(a, aligned)
    norm_d = difference(a, normalized)
    raw_mask = raw_d > threshold
    raw_mask &= valid
    verified_mask = (norm_d > threshold) & valid
    candidates = raw_mask | verified_mask
    if proposal is not None:
        if proposal.shape != (h, w):
            raise ValueError("Proposal mask must match the processed image dimensions.")
        candidates = proposal.astype(bool) & valid
    # Filter noise but preserve separately inspectable local candidate regions.
    clean = cv2.morphologyEx(candidates.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(clean)
    selected = sorted([i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= min_area], key=lambda i: -stats[i, cv2.CC_STAT_AREA])
    if region_offset and region_offset >= len(selected):
        raise ValueError('Region offset exceeds the eligible candidate set.')
    analysis_source_hash = SOURCE_SHA256
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != analysis_source_hash:
        raise ValueError('Analysis context changed: implementation changed on disk; restart before analysing.')
    analysis_environment = {'numpy': np.__version__, 'opencv': cv2.__version__}
    context = hashlib.sha256()
    context.update(json.dumps({'engine': VERSION, 'shape': list(a.shape), 'threshold': threshold,
                               'min_area': min_area, 'alignment': alignment, 'analysis_source_sha256': analysis_source_hash, 'environment': analysis_environment}, sort_keys=True, allow_nan=False).encode())
    for pixels in (a, b, aligned, normalized, valid, candidates, clean):
        context.update(np.ascontiguousarray(pixels).tobytes())
    context_hash = context.hexdigest()
    if expected_context is not None and expected_context != context_hash:
        raise ValueError('Analysis context changed; continuation refused. Re-run the original pair instead.')
    batch = selected[region_offset:region_offset + 24]
    edge_a = cv2.Canny(gray(a), 55, 135)
    edge_b = cv2.Canny(gray(normalized), 55, 135)
    near_a = cv2.dilate(edge_a, np.ones((3, 3), np.uint8)) > 0
    near_b = cv2.dilate(edge_b, np.ones((3, 3), np.uint8)) > 0
    edge_change = ((edge_a > 0) & ~near_b) | ((edge_b > 0) & ~near_a)
    perturbations = []
    for tx, ty in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        shifted = cv2.warpAffine(normalized, np.float32([[1, 0, tx], [0, 1, ty]]), (w, h), borderMode=cv2.BORDER_REFLECT)
        perturbations.append(difference(a, shifted) > threshold)
    regions, accepted = [], np.zeros((h, w), np.uint8)
    for number, label in enumerate(batch, region_offset + 1):
        component = labels == label
        x, y, rw, rh, area = [int(v) for v in stats[label]]
        raw = float(np.mean(raw_d[component]))
        geometric = float(np.mean(align_d[component]))
        normalized_value = float(np.mean(norm_d[component]))
        retained = float(np.mean(verified_mask[component]))
        stability = float(np.mean([np.mean(pm[component]) for pm in perturbations]))
        experiments = [{"dx": dx, "dy": dy, "survival": round(float(np.mean(pm[component])),3)} for (dx,dy),pm in zip([(1,0),(-1,0),(0,1),(0,-1)],perturbations)]
        worst_survival = float(min(np.mean(pm[component]) for pm in perturbations))
        # Measure edge disagreement in the region and a narrow surrounding ring.
        boundary = cv2.dilate(component.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & valid
        edge_total = int(((edge_a > 0) | (edge_b > 0))[boundary].sum())
        structural = float(edge_change[boundary].sum() / max(1, edge_total))
        pad = 5
        aa = gray(a)[max(0,y-pad):min(h,y+rh+pad), max(0,x-pad):min(w,x+rw+pad)].astype(float).ravel()
        bb = gray(normalized)[max(0,y-pad):min(h,y+rh+pad), max(0,x-pad):min(w,x+rw+pad)].astype(float).ravel()
        correlation = float(np.corrcoef(aa, bb)[0, 1]) if min(np.std(aa), np.std(bb)) > 2 else 0.
        # Canny edges can disappear solely because a shadow reduces contrast.
        # High local affine correlation is contradictory evidence, not a proof of artifact.
        appearance_only = correlation >= .90
        alignment_reduction = max(0., 1 - geometric / max(raw, 1e-6))
        lighting_reduction = max(0., 1 - normalized_value / max(geometric, 1e-6))
        reasons, contradictions = [], []
        if alignment_reduction > .65:
            contradictions.append("Most of this difference disappears after registration.")
        if lighting_reduction > .65:
            contradictions.append("Most of this difference disappears after global illumination correction.")
        if structural < .16:
            contradictions.append("Edges largely agree; lighting or surface appearance remains a plausible explanation.")
        if worst_survival < .55:
            contradictions.append("The candidate is sensitive to a one-pixel alignment perturbation.")
        if not alignment["reliable"]:
            contradictions.append("Image texture or registration evidence is insufficient for a supported verdict.")
        if appearance_only:
            contradictions.append("Local luminance structure remains highly correlated; a local shadow or appearance shift could explain this candidate.")
        if retained > .5:
            reasons.append("A majority of candidate pixels remain different after alignment and illumination correction.")
        if structural >= .16:
            reasons.append("Local edge disagreement provides independent structural evidence.")
        if worst_survival >= .55:
            reasons.append("The difference persists in every tested one-pixel registration perturbation.")
        if alignment["reliable"] and not appearance_only and retained >= .5 and worst_survival >= .55 and structural >= .16 and area < h * w * .4:
            verdict, title = "supported", "Persistent structural change"
            accepted[component & verified_mask] = 255
        elif retained < .18 and (alignment_reduction > .65 or lighting_reduction > .65):
            verdict, title = "artifact", "Change explained by a nuisance factor"
        else:
            verdict, title = "review", "Evidence is inconclusive"
        if area >= h * w * .4 and verdict != "artifact":
            verdict, title = "review", "Widespread appearance change"
            contradictions.append("This covers too much of the scene for a localized structural conclusion.")
        regions.append({"id": f"R{number:02}", "bbox": [x, y, rw, rh], "pixels": area, "verdict": verdict,
                        "title": title, "support": reasons, "contradictions": contradictions,
                        "checks": {"alignment_reduction": round(alignment_reduction, 3), "lighting_reduction": round(lighting_reduction, 3),
                                   "retained_fraction": round(retained, 3), "structural_disagreement": round(structural, 3), "perturbation_survival": round(stability, 3),
                                   "local_luminance_correlation": round(correlation, 3)},
                        "review": "unreviewed"})
        from .dossier import challenge_log, evidence_requests
        regions[-1]['checks']['worst_perturbation_survival'] = worst_survival
        regions[-1]['challenge_log'] = challenge_log(regions[-1]['checks'], alignment, experiments)
        regions[-1]['evidence_requests'] = evidence_requests(regions[-1]['checks'], alignment)
    counts = {k: sum(r["verdict"] == k for r in regions) for k in ["supported", "artifact", "review"]}
    flags = []
    if landmarks is not None:
        flags.append('Alignment uses user-supplied landmarks with a held-out geometric check. Correspondence truth and acquisition provenance were not independently verified.')
    if not alignment["reliable"]:
        flags.append("Low registration evidence: inspect alignment before interpreting change.")
    if len(selected) > 24:
        flags.append(f"Inspecting ranks {region_offset + 1}–{region_offset + len(batch)} of {len(selected)} eligible candidates. Verdicts cover this batch only.")
    if not regions:
        flags.append("No candidates above this threshold. This is not proof that the scene is unchanged.")
    blurred = cv2.Laplacian(gray(a), cv2.CV_32F).var() < 30 or cv2.Laplacian(gray(b), cv2.CV_32F).var() < 30
    if blurred:
        flags.append("One or both images have weak high-frequency detail; small changes can be missed.")
    overlay = aligned.copy()
    color = cv2.applyColorMap(np.uint8(np.clip(norm_d * 650, 0, 255)), cv2.COLORMAP_TURBO)[:, :, ::-1]
    heat = np.uint8(aligned * .45 + color * .55)
    for r in regions:
        x, y, rw, rh = r["bbox"]
        c = {"supported": (67, 225, 168), "artifact": (119, 147, 179), "review": (255, 193, 92)}[r["verdict"]]
        cv2.rectangle(overlay, (x, y), (x + rw, y + rh), c, 2)
        cv2.putText(overlay, r["id"], (x + 3, max(14, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, .45, c, 1)
    report = {"engine": VERSION, "detector": "RGB difference baseline (not a trained change model)", "width": w, "height": h,
              "input_hash": hashlib.sha256(a.tobytes() + b.tobytes()).hexdigest(), "alignment": alignment, "illumination_fit": fits,
              "threshold": threshold, "min_area": min_area, "counts": counts, "candidate_count": len(selected), "regions": regions, "warnings": flags,
              "raw_changed_pixels": int(raw_mask.sum()), "corrected_changed_pixels": int(verified_mask.sum()),
              "supported_changed_pixels": int((accepted > 0).sum()), "elapsed_ms": round((time.perf_counter() - started) * 1000),
              "limitations": ["Diagnostic scores are not calibrated probabilities.", "RGB-only: no geospatial coordinates, spectral bands, or physical area estimates.",
                              "No causal disaster/damage conclusion can be drawn from these checks alone.", "Global normalization does not resolve local shadows, clouds, parallax, or seasonal changes reliably.",
                              "Two images alone cannot prove that a candidate is a real-world change."],
              "meta": {"status": "not_requested", "reason": "Local evidence only; no Meta API call was made."}, "sam": {"status": "not_requested"}}
    eligible_pixels = int(sum(stats[i, cv2.CC_STAT_AREA] for i in selected))
    inspected_pixels = int(sum(r['pixels'] for r in regions))
    report['analysis_environment'] = analysis_environment
    report['analysis_source_sha256'] = analysis_source_hash
    report['analysis_context_sha256'] = context_hash
    report['inspection'] = {'offset': region_offset, 'batch_size': 24,
                            'start_rank': region_offset + 1 if batch else None,
                            'end_rank': region_offset + len(batch) if batch else None,
                            'regions_before_batch': region_offset,
                            'regions_after_batch': max(0, len(selected) - region_offset - len(batch)),
                            'next_offset': region_offset + len(batch) if region_offset + len(batch) < len(selected) else None,
                            'schema': 'geoalibi-inspection-v1',
                            'processed_pixels': h * w, 'valid_pixels': int(valid.sum()),
                            'proposal_pixels': int(candidates.sum()), 'morphology_pixels': int((clean > 0).sum()),
                            'eligible_regions': len(selected), 'inspected_regions': len(regions),
                            'omitted_regions': len(selected) - len(regions),
                            'eligible_region_pixels': eligible_pixels, 'inspected_region_pixels': inspected_pixels,
                            'omitted_region_pixels': eligible_pixels - inspected_pixels,
                            'below_min_area_pixels': int((clean > 0).sum()) - eligible_pixels,
                            'supported_pixels': report['supported_changed_pixels'],
                            'scope': 'This batch only; other batches may have inspected some omitted regions. Connected-component footprints after morphology; not accuracy, confidence, physical area or abstention-only pixels.'}
    from .assessment import assess
    report['assessment'] = assess(report)
    report['all_candidates_abstained'] = bool(regions) and counts['review'] == len(regions)
    if report['all_candidates_abstained']:
        report['warnings'].append('All inspected candidates require human review. Use the proposal view; no automated supported-change mask is claimed.')
    omitted = np.isin(labels, selected[:region_offset] + selected[region_offset + 24:]) if len(selected) > len(batch) else np.zeros((h, w), dtype=bool)
    omitted_overlay = aligned.copy()
    omitted_overlay[omitted] = np.uint8(.45 * aligned[omitted] + .55 * np.array([171, 112, 242]))
    images = {"omitted_mask": omitted.astype(np.uint8) * 255, "omitted_overlay": omitted_overlay, "before": a, "after": b, "aligned": aligned, "normalized": normalized, "overlay": overlay,
              "heatmap": heat, "raw_mask": raw_mask.astype(np.uint8) * 255, "proposal_mask": candidates.astype(np.uint8) * 255, "supported_mask": accepted}
    if model_scores is not None:
        from .pretrained import PROVENANCE, NAME
        report["detector"] = NAME
        report["model_provenance"] = PROVENANCE
        images["model_scores"] = np.uint8(np.clip(model_scores * 255, 0, 255))
    if landmarks is not None:
        for name,image,columns in [('landmarks_before',a,(2,3)),('landmarks_after',b,(0,1))]:
            overlay_points=image.copy()
            for i,row in enumerate(alignment['landmarks']):
                point=tuple(int(round(row[k])) for k in columns)
                color=(255,193,92) if i>=len(landmarks)-2 else (67,225,168)
                cv2.circle(overlay_points,point,5,color,2)
                cv2.putText(overlay_points,str(i+1),point,cv2.FONT_HERSHEY_SIMPLEX,.5,color,1)
            images[name]=overlay_points
    return Analysis(report, images)


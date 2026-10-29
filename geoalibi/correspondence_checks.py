"""Experimental correspondence checks; does not alter production registration."""
import cv2
import numpy as np


def check_correspondences(source, target, width=256, height=256):
    source, target = np.asarray(source, dtype=float), np.asarray(target, dtype=float)
    if source.ndim != 2 or source.shape[1:] != (2,) or source.shape != target.shape:
        raise ValueError("Correspondences must have matching N by 2 shapes.")
    if width <= 0 or height <= 0 or not np.isfinite(source).all() or not np.isfinite(target).all():
        raise ValueError("Finite coordinates and positive image dimensions required.")
    for points in (source, target):
        if (points < 0).any() or (points[:, 0] >= width).any() or (points[:, 1] >= height).any():
            raise ValueError("Correspondences lie outside image bounds.")
        if len(np.unique(points, axis=0)) != len(points):
            raise ValueError("Repeated correspondence locations are not independent evidence.")
    count = len(source)
    result = {"matches": count, "candidate_pass": False}
    if count < 16:
        return {**result, "reason": "Fewer than 16 matches"}
    order = np.random.default_rng(42).permutation(count)
    held, fit = order[:max(4, count // 4)], order[max(4, count // 4):]
    cv2.setRNGSeed(0)
    matrix, mask = cv2.estimateAffinePartial2D(
        source[fit], target[fit], method=cv2.RANSAC, ransacReprojThreshold=2.5)
    if matrix is None or mask is None or not np.isfinite(matrix).all():
        return {**result, "reason": "No finite transform"}
    keep = mask.ravel().astype(bool)
    inliers = int(keep.sum())
    coverage = min(cv2.contourArea(cv2.convexHull(p[fit][keep].astype(np.float32)))
                   for p in (source, target)) / (width * height)
    errors = np.linalg.norm(source[held] @ matrix[:, :2].T + matrix[:, 2] - target[held], axis=1)
    scale = float(np.linalg.norm(matrix[0, :2]))
    rotation = float(abs(np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0]))))
    passed = (inliers >= 8 and inliers / len(fit) >= .4 and .95 < scale < 1.05
              and rotation <= 5 and np.linalg.norm(matrix[:, 2]) < .12 * min(width, height)
              and coverage >= .1 and np.mean(errors <= 2.5) >= .8)
    return {**result, "candidate_pass": bool(passed), "matrix": matrix.tolist(),
            "fit_indices": fit.tolist(), "held_out_indices": held.tolist(),
            "inliers": inliers, "coverage": float(coverage),
            "held_out_errors_px": errors.tolist(),
            "held_out_rms_px": float(np.sqrt(np.mean(errors ** 2))),
            "reason": "Model correspondence consistency only; not independent alignment truth"}

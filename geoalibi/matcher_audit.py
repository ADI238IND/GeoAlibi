"""Replayable experimental model evidence, never a production verdict."""
import numpy as np

from .correspondence_checks import check_correspondences


def audit_matches(source, target, confidence):
    """Retain every model output; geometry indices address retained_indices."""
    source = np.asarray(source, dtype=float)
    target = np.asarray(target, dtype=float)
    if source.size == 0 and source.shape == (0,):
        source = source.reshape(0, 2)
    if target.size == 0 and target.shape == (0,):
        target = target.reshape(0, 2)
    confidence = np.asarray(confidence, dtype=float)
    if (source.ndim != 2 or source.shape[1:] != (2,)
            or source.shape != target.shape or confidence.shape != (len(source),)
            or not np.isfinite(source).all() or not np.isfinite(target).all()
            or not np.isfinite(confidence).all()
            or (confidence < 0).any() or (confidence > 1).any()):
        raise ValueError("Invalid model correspondence output")
    retained = np.flatnonzero(confidence >= .8)
    try:
        geometry = check_correspondences(source[retained], target[retained])
    except ValueError as exc:
        geometry = {"candidate_pass": False, "matches": len(retained), "reason": str(exc)}
    return {"source_after_xy": source.tolist(), "target_before_xy": target.tolist(),
            "confidence": confidence.tolist(), "retained_indices": retained.tolist(),
            "geometry": geometry}


def replay_matches(record):
    """Recompute geometry without weights; reject altered saved conclusions."""
    replayed = audit_matches(record["source_after_xy"], record["target_before_xy"],
                             record["confidence"])
    if replayed != record:
        raise ValueError("Saved audit differs from recomputed correspondence checks")
    return replayed["geometry"]

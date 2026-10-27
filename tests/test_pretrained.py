from pathlib import Path

import numpy as np
import pytest

from geoalibi.pretrained import infer_tiles, verify
from geoalibi.vision import investigate
from geoalibi.demo import pair


def test_tiling_preserves_non_multiple_dimensions_and_channel_order():
    a = np.full((270, 319, 3), 255, np.uint8)
    b = np.zeros_like(a)
    seen = []
    def predict(x):
        seen.append(x)
        assert x.shape == (6, 256, 256)
        assert np.all(x[:3] == 1) and np.all(x[3:] == -1)
        return np.full((256, 256), .75, np.float32)
    result = infer_tiles(a, b, predict)
    assert result.shape == (270, 319) and np.all(result == .75)
    assert len(seen) == 4


def test_invalid_model_output_fails():
    a = np.zeros((64, 64, 3), np.uint8)
    with pytest.raises(ValueError, match="invalid"):
        infer_tiles(a, a, lambda x: np.full((256, 256), np.nan))


def test_unverified_checkpoint_fails(tmp_path):
    path = tmp_path / "bad.ckpt"
    path.write_bytes(b"invalid")
    with pytest.raises(ValueError, match="unexpected size"):
        verify(path)


def test_learned_proposals_replace_rgb_candidates_and_keep_evidence():
    a, b, _ = pair()
    mask = np.zeros(a.shape[:2], bool)
    mask[240:276, 240:292] = True
    r = investigate(a, b, detector_fn=lambda a,b: (mask, mask.astype(np.float32)))
    assert r.report["candidate_count"] == 1
    assert "model_provenance" in r.report
    assert r.report["model_provenance"]["weights_license"] == "CC-BY-4.0"
    assert r.images["raw_mask"].sum() > r.images["proposal_mask"].sum()


def test_no_silent_fallback_from_missing_detector(monkeypatch):
    from geoalibi.pretrained import propose
    monkeypatch.setenv("GEOALIBI_CHECKPOINT", "/nonexistent/checkpoint.ckpt")
    a, b, _ = pair()
    with pytest.raises(ValueError, match="not configured"):
        propose(a,b)

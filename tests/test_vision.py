import io

import cv2
import numpy as np
import pytest
from PIL import Image

from geoalibi.demo import pair, scene
from geoalibi.vision import decode_image, investigate, png


@pytest.mark.parametrize("case", ["unchanged", "shift", "light"])
def test_nuisance_does_not_become_supported_change(case):
    a, b, _ = pair(case)
    result = investigate(a, b)
    assert result.report["counts"]["supported"] == 0
    assert not result.images["supported_mask"].any()
    if case != "unchanged":
        assert result.report["counts"]["artifact"] > 0
        assert result.report["corrected_changed_pixels"] < result.report["raw_changed_pixels"] * .1


def test_structural_edits_survive_but_local_shadow_abstains():
    a, b, truth = pair("mixed")
    result = investigate(a, b)
    supported = result.images["supported_mask"] > 0
    assert (supported & (truth > 0)).sum() > 2000
    # The fixture's lower-left shadow preserves its objects; it must not be supported.
    assert not supported[440:590, :160].any()
    assert result.report["counts"]["review"] >= 1
    assert all("local_luminance_correlation" in r["checks"] for r in result.report["regions"])


@pytest.mark.parametrize("seed", [81, 142, 319])
def test_unseen_fixture_textures(seed):
    a = scene(seed)
    b = np.clip(a.astype(float) * .80 + 7, 0, 255).astype(np.uint8)
    b = cv2.warpAffine(b, np.float32([[1, 0, -3], [0, 1, 2]]), (640, 640), borderMode=cv2.BORDER_REFLECT)
    r = investigate(a, b)
    assert r.report["counts"]["supported"] == 0


def test_low_texture_abstains():
    a = np.full((128, 128, 3), 100, np.uint8)
    b = a.copy()
    b[35:80, 35:80] = 200
    r = investigate(a, b).report
    assert not r["alignment"]["reliable"]
    assert r["counts"]["supported"] == 0
    assert r["counts"]["review"] >= 1


def test_mismatched_footprints_fail_instead_of_stretching():
    a, b, _ = pair()
    with pytest.raises(ValueError, match="same dimensions"):
        investigate(a, b[:-10])


def test_decode_resizes_and_strips_metadata():
    im = Image.new("RGB", (1600, 800), "green")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    a = decode_image(buf.getvalue())
    assert a.shape == (512, 1024, 3)
    assert np.array_equal(decode_image(png(a)), a)


@pytest.mark.parametrize("payload", [b"not an image", b"x" * (12 * 1024 * 1024 + 1)])
def test_invalid_uploads_fail(payload):
    with pytest.raises(ValueError):
        decode_image(payload)



def test_registration_evidence_is_specific_to_selected_transform():
    from geoalibi.vision import alignment_evidence
    identity = np.float32([[1,0,0],[0,1,0]])
    shifted = np.float32([[1,0,-12],[0,1,0]])
    source = np.float32([[20,20],[60,20],[100,20],[20,60],[60,60],[100,60],[20,100],[100,100]])
    target = source - [12,0]
    # A rejected feature transform must not make identity reliable.
    assert not alignment_evidence(identity, source, target, (12,0), .2, 100)['reliable']
    assert alignment_evidence(shifted, source, target, (12,0), .2, 100)['feature_support']
    empty = np.empty((0,2))
    # Merely selecting a weak phase translation does not establish reliability.
    assert not alignment_evidence(shifted, empty, empty, (12,0), .2, 100)['reliable']
    assert alignment_evidence(shifted, empty, empty, (12,0), .8, 100)['phase_support']
    assert not alignment_evidence(identity, empty, empty, (12,0), .8, 100)['reliable']
    assert not alignment_evidence(shifted, source, target, (12,0), .8, 0)['reliable']

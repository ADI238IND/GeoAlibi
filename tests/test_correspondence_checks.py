import numpy as np
import pytest
from geoalibi.correspondence_checks import check_correspondences


def points():
    return np.array([(x, y) for x in [20, 70, 120, 170, 210]
                     for y in [20, 70, 120, 170, 210]], dtype=float)


def test_known_translation_and_held_out_corruption():
    source = points()
    target = source + [4, -3]
    good = check_correspondences(source, target)
    assert good["candidate_pass"]
    assert good["held_out_rms_px"] < .001
    target[good["held_out_indices"]] += [8, 0]
    bad = check_correspondences(source, target)
    assert not bad["candidate_pass"]
    assert np.allclose(good["matrix"], bad["matrix"])
    assert set(good["held_out_indices"]).isdisjoint(good["fit_indices"])


def test_large_shift_clustered_support_and_too_few_matches():
    source = points()
    assert not check_correspondences(source, source + [32, 0])["candidate_pass"]
    assert not check_correspondences(source / 5, source / 5)["candidate_pass"]
    assert not check_correspondences(source[:8], source[:8])["candidate_pass"]


@pytest.mark.parametrize("kind", ["duplicate", "nan", "outside", "shape"])
def test_invalid_correspondences_rejected(kind):
    source = points()
    target = source.copy()
    if kind == "duplicate":
        source[1] = source[0]
    elif kind == "nan":
        target[0, 0] = np.nan
    elif kind == "outside":
        target[0, 0] = 256
    else:
        target = target[:-1]
    with pytest.raises(ValueError):
        check_correspondences(source, target)

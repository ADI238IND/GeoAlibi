import cv2
import numpy as np
import pytest
from geoalibi.stable_registration import stable_registration


def scene():
    image=np.random.default_rng(52).integers(0,256,(384,384,3),dtype=np.uint8)
    return cv2.GaussianBlur(image,(3,3),0)


def test_known_translation_and_excluded_local_edit():
    a=scene(); matrix=np.float32([[1,0,4],[0,1,-3]])
    b=cv2.warpAffine(a,matrix,(384,384));b[140:210,140:210]=255
    ma=np.zeros((384,384),np.uint8);mb=ma.copy();ma[135:215,135:215]=255;mb[135:215,135:215]=255
    result=stable_registration(a,b,ma,mb)
    assert result['geometry']['candidate_pass']
    recovered=np.asarray(result['geometry']['matrix'])
    assert np.allclose(recovered[:,:2],np.eye(2),atol=.01)
    assert np.allclose(recovered[:,2],[-4,3],atol=.5)
    assert not set(result['geometry']['fit_indices']) & set(result['geometry']['held_out_indices'])
    for key in ('source_after_xy','target_before_xy'):
        assert all(not (103<=x<247 and 103<=y<247) for x,y in result[key])
    assert result==stable_registration(a,b,ma,mb)


@pytest.mark.parametrize('excluded', [False,True])
def test_no_texture_or_no_unexcluded_area_abstains(excluded):
    a=scene() if excluded else np.zeros((384,384,3),np.uint8)
    mask=np.full(a.shape[:2],255 if excluded else 0,np.uint8)
    assert not stable_registration(a,a,mask,mask)['geometry']['candidate_pass']


@pytest.mark.parametrize('bad', [np.zeros((384,384),bool),np.ones((384,384),np.uint8),np.zeros((32,32),np.uint8)])
def test_invalid_exclusions_rejected(bad):
    a=scene()
    with pytest.raises(ValueError,match='binary'):
        stable_registration(a,a,bad,bad)


def test_unrelated_procedural_textures_do_not_pass():
    a=scene()
    b=cv2.GaussianBlur(np.random.default_rng(99).integers(0,256,a.shape,dtype=np.uint8),(3,3),0)
    mask=np.zeros(a.shape[:2],np.uint8)
    assert not stable_registration(a,b,mask,mask)['geometry']['candidate_pass']

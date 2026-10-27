import cv2
import numpy as np
import pytest
from geoalibi.demo import pair
from geoalibi.landmarks import register
from geoalibi.vision import investigate


def fixture():
    a,_,_=pair()
    b=cv2.warpAffine(a,np.float32([[1,0,4],[0,1,-3]]),(640,640),borderMode=cv2.BORDER_REFLECT)
    before=np.array([[50,50],[580,50],[50,580],[580,580],[150,180],[480,440]],float)
    return a,b,np.concatenate([before+[4,-3],before],axis=1)


def test_held_out_landmarks_recover_known_translation():
    a,b,p=fixture();warped,valid,info=register(a,b,p)
    assert info['fit_points']==4 and info['held_out_points']==2
    assert info['held_out_rms_px']<.001
    assert np.mean(np.abs(a[valid].astype(float)-warped[valid]))<.01
    report=investigate(a,b,landmarks=p).report
    assert report['counts']['supported']==0
    assert report['alignment']['landmark_hash']
    assert 'user-supplied' in report['warnings'][0]


def test_held_out_disagreement_is_not_used_to_refit_or_silently_ignored():
    a,b,p=fixture();p[-1,2:]+=12
    with pytest.raises(ValueError,match='held-out residual'):register(a,b,p)


@pytest.mark.parametrize('change',['duplicate','clustered','nonfinite','outside','few'])
def test_invalid_landmark_evidence_rejected(change):
    a,b,p=fixture()
    if change=='duplicate':p[1]=p[0]
    if change=='clustered':p[:4,:]*=.01
    if change=='nonfinite':p[0,0]=np.nan
    if change=='outside':p[0,0]=10000
    if change=='few':p=p[:5]
    with pytest.raises(ValueError):register(a,b,p)

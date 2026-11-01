import io
import zipfile
import copy

import numpy as np
import pytest

from geoalibi.assessment import assess, assessment_markdown
from geoalibi.demo import scene
from geoalibi.vision import investigate
from geoalibi.dossier import build_packet, verify_packet


def report(**changes):
    r={'regions':[{'pixels':20}], 'candidate_count':1, 'supported_changed_pixels':0,
       'alignment':{'reliable':True}, 'counts':{'supported':0,'artifact':0,'review':1}}
    return {**r,**changes}


@pytest.mark.parametrize('changes,code', [
    ({'alignment':{'reliable':False},'regions':[],'candidate_count':0},'alignment_unresolved'),
    ({'candidate_count':3,'supported_changed_pixels':10},'partial_inspection'),
    ({'supported_changed_pixels':10},'review_required'),
    ({'counts':{'review':0},'supported_changed_pixels':10},'supported_candidates'),
    ({'regions':[],'candidate_count':0,'counts':{'review':0}},'no_candidates'),
    ({'counts':{'review':0}},'no_supported_candidates')])
def test_scope_states_do_not_equate_empty_mask_with_no_change(changes,code):
    source=report(**changes); original=copy.deepcopy(source)
    result=assess(source)
    assert result['code']==code and result['next_step']
    assert source==original
    assert result['coverage'] is None
    assert result['omitted_regions']==max(0,source['candidate_count']-len(source['regions']))


def test_coverage_conserves_eligible_pixels_and_exposes_capped_regions():
    a=scene(); proposal=np.zeros(a.shape[:2],np.uint8)
    for y in range(20,620,70):
        for x in range(20,620,70):proposal[y:y+18,x:x+18]=1
    proposal[5:8,5:8]=1
    result=investigate(a,a.copy(),proposal=proposal,min_area=16)
    c=result.report['inspection']
    assert c['eligible_regions']==81 and c['inspected_regions']==24 and c['omitted_regions']==57
    assert c['eligible_region_pixels']==81*18*18
    assert c['inspected_region_pixels']==24*18*18
    assert c['omitted_region_pixels']==57*18*18
    assert c['below_min_area_pixels']==9
    assert c['morphology_pixels']==c['eligible_region_pixels']+c['below_min_area_pixels']
    assert c['supported_pixels']==int((result.images['supported_mask']>0).sum())==0
    assert result.report['assessment']['code']=='partial_inspection'
    omitted=result.images['omitted_mask']>0
    assert int(omitted.sum())==c['omitted_region_pixels']
    assert not omitted[5:8,5:8].any()  # below-minimum component is not an omitted eligible region
    for region in result.report['regions']:
        x,y,w,h=region['bbox']; assert not omitted[y:y+h,x:x+w].any()
    assert np.array_equal(result.images['omitted_overlay'][~omitted],result.images['aligned'][~omitted])
    assert not np.array_equal(result.images['omitted_overlay'][omitted],result.images['aligned'][omitted])
    source={**result.report,'id':'fixture','audit':[]}
    from geoalibi.vision import png
    packet=build_packet(source,{name:png(result.images[name]) for name in ['omitted_mask','omitted_overlay']})
    verified=verify_packet(packet)
    assert all(name in verified['files'] for name in ['SUMMARY.md','images/omitted_mask.png','images/omitted_overlay.png'])
    with zipfile.ZipFile(io.BytesIO(packet)) as archive:
        text=archive.read('SUMMARY.md').decode()
        assert 'omitted: 57' in text and str(57*18*18) in text
        assert 'physical area' in text


def test_legacy_summary_does_not_invent_pixel_coverage_or_promote_human_review():
    old=report(); old['regions'][0]['review']='confirmed'
    assert assess(old)['code']=='review_required'
    text=assessment_markdown(old)
    assert 'not recorded' in text and 'not been reconstructed' in text


def test_all_inspected_candidates_have_an_empty_omission_mask():
    a=scene(); mask=np.zeros(a.shape[:2],np.uint8);mask[30:60,30:60]=1
    result=investigate(a,a.copy(),proposal=mask,min_area=16)
    assert result.report['inspection']['eligible_regions']==1
    assert result.report['inspection']['omitted_regions']==0
    assert not result.images['omitted_mask'].any()
    assert np.array_equal(result.images['omitted_overlay'],result.images['aligned'])

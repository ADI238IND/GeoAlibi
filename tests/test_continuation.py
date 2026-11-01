"""Procedural inspection-pagination contracts, not benchmark accuracy evidence."""
import copy
import importlib

import numpy as np
import pytest
from fastapi.testclient import TestClient

from geoalibi.demo import scene
from geoalibi.vision import investigate, png
from geoalibi.store import Store


def source_pair():
    a=scene(); mask=np.zeros(a.shape[:2],np.uint8)
    for y in range(20,620,70):
        for x in range(20,620,70):mask[y:y+18,x:x+18]=1
    return a,mask


def test_batches_cover_each_eligible_component_once_with_one_frozen_context():
    a,mask=source_pair(); first=investigate(a,a.copy(),proposal=mask)
    context=first.report['analysis_context_sha256']; rows=[]; supported=[]
    for offset in (0,24,48,72):
        result=investigate(a,a.copy(),proposal=mask,region_offset=offset,expected_context=context)
        c=result.report['inspection']
        assert c['offset']==offset and c['regions_before_batch']==offset
        assert c['regions_after_batch']==max(0,81-offset-24)
        assert c['omitted_regions']==81-len(result.report['regions'])
        assert int((result.images['omitted_mask']>0).sum())==c['omitted_region_pixels']
        rows.extend(r['id'] for r in result.report['regions']);supported.append(result.report['supported_changed_pixels'])
    assert len(rows)==len(set(rows))==81
    assert rows==[f'R{n:02}' for n in range(1,82)]
    assert sum(supported)==0
    assert result.report['inspection']['next_offset'] is None


@pytest.mark.parametrize('change',['image','proposal','threshold','area','context'])
def test_changed_context_is_rejected(change):
    a,mask=source_pair(); original=investigate(a,a.copy(),proposal=mask)
    before=a.copy(); after=a.copy(); proposal=mask.copy()
    args={'threshold':.12,'min_area':70,'expected_context':original.report['analysis_context_sha256']}
    if change=='image': after[100:120,100:120]=0
    elif change=='proposal':proposal[20:38,20:38]=0
    elif change=='threshold':args['threshold']=.13
    elif change=='area':args['min_area']=71
    else:args['expected_context']='0'*64
    with pytest.raises(ValueError,match='context changed'):
        investigate(before,after,proposal=proposal,region_offset=24,**args)


@pytest.mark.parametrize('offset',[-1,True,1.5,81])
def test_invalid_offsets_fail(offset):
    a,mask=source_pair()
    with pytest.raises(ValueError): investigate(a,a.copy(),proposal=mask,region_offset=offset)


def test_api_continuation_preserves_parent_and_never_calls_a_provider(tmp_path,monkeypatch):
    appmod=importlib.import_module('geoalibi.app'); store=Store(tmp_path/'data');monkeypatch.setattr(appmod,'store',store)
    def forbidden(*args,**kwargs):raise AssertionError('Detector/provider rerun forbidden')
    monkeypatch.setattr(appmod.pretrained,'propose',forbidden);monkeypatch.setattr(appmod.meta,'enrich',forbidden);monkeypatch.setattr(store,'reserve',forbidden)
    a,mask=source_pair(); result=investigate(a,a.copy(),proposal=mask)
    result.report['detector']='fixture saved detector';result.report['model_provenance']={'fixture':True}
    parent=appmod.save_analysis(result,'Pagination fixture',True)
    store.review(parent['id'],'R01','confirmed','Fixture reviewer note stays with parent.')
    original=copy.deepcopy(store.get(parent['id']))
    client=TestClient(appmod.app)
    response=client.post(f"/api/runs/{parent['id']}/continue",json={'use_meta':True,'use_sam':True,'threshold':.35})
    assert response.status_code==200,response.text
    child=response.json()
    assert child['regions'][0]['id']=='R25' and child['regions'][-1]['id']=='R48'
    assert child['lineage']['source_run_id']==parent['id']==child['lineage']['root_run_id']
    assert child['analysis_context_sha256']==parent['analysis_context_sha256']
    assert child['threshold']==parent['threshold'] and all(r['review']=='unreviewed' for r in child['regions'])
    assert child['meta']['status']=='not_requested' and child['sam']['status']=='not_requested'
    assert child['detector']==parent['detector'] and child['model_provenance']=={'fixture':True}
    assert store.get(parent['id'])==original
    grandchild=client.post(f"/api/runs/{child['id']}/continue").json()
    assert grandchild['lineage']['source_run_id']==child['id'] and grandchild['lineage']['root_run_id']==parent['id']
    last=client.post(f"/api/runs/{grandchild['id']}/continue").json()
    assert len(last['regions'])==9 and last['inspection']['next_offset'] is None
    assert client.post(f"/api/runs/{last['id']}/continue").status_code==409
    # Changed parent bytes produce no child report.
    before_count=len(store.recent()); (store.root/parent['id']/'proposal_mask.png').write_bytes(png(np.zeros_like(a)))
    assert client.post(f"/api/runs/{parent['id']}/continue").status_code==422
    assert len(store.recent())==before_count
    assert client.post('/api/runs/not-a-run/continue').status_code==404


def test_old_context_is_not_invented(tmp_path,monkeypatch):
    appmod=importlib.import_module('geoalibi.app');store=Store(tmp_path/'data');monkeypatch.setattr(appmod,'store',store)
    a,mask=source_pair(); result=investigate(a,a.copy(),proposal=mask);result.report.pop('analysis_context_sha256')
    parent=appmod.save_analysis(result,'Legacy fixture',True)
    response=TestClient(appmod.app).post(f"/api/runs/{parent['id']}/continue")
    assert response.status_code==409 and 'no frozen analysis context' in response.json()['detail']


def test_paging_cannot_bypass_the_parent_registration_gate():
    a,mask=source_pair();a=np.full_like(a,110)
    parent=investigate(a,a.copy(),proposal=mask)
    child=investigate(a,a.copy(),proposal=mask,region_offset=24,
                      expected_context=parent.report['analysis_context_sha256'])
    assert parent.report['alignment']['reliable'] is False
    assert child.report['alignment']['reliable'] is False
    assert child.report['supported_changed_pixels']==0
    assert child.report['assessment']['code']=='alignment_unresolved'


def test_changed_analysis_source_refuses_continuation(monkeypatch):
    from pathlib import Path
    a,mask=source_pair();parent=investigate(a,a.copy(),proposal=mask)
    original=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda path:b'changed implementation' if path.name=='vision.py' else original(path))
    with pytest.raises(ValueError,match='context changed'):
        investigate(a,a.copy(),proposal=mask,region_offset=24,
                    expected_context=parent.report['analysis_context_sha256'])


def test_changed_numeric_environment_refuses_continuation(monkeypatch):
    import cv2
    a,mask=source_pair();parent=investigate(a,a.copy(),proposal=mask)
    monkeypatch.setattr(cv2,'__version__','changed-test-version')
    with pytest.raises(ValueError,match='context changed'):
        investigate(a,a.copy(),proposal=mask,region_offset=24,
                    expected_context=parent.report['analysis_context_sha256'])


def test_edited_frame_continues_from_serialized_saved_rgb_proposals(tmp_path,monkeypatch):
    appmod=importlib.import_module('geoalibi.app');store=Store(tmp_path/'data');monkeypatch.setattr(appmod,'store',store)
    a,_=source_pair(); b=a.copy()
    for y in range(20,620,70):
        for x in range(20,620,70):b[y:y+18,x:x+18]=[240,30,40]
    original=investigate(a,b)
    parent=appmod.save_analysis(original,'Edited-frame fixture',True)
    response=TestClient(appmod.app).post(f"/api/runs/{parent['id']}/continue")
    assert response.status_code==200,response.text
    child=response.json()
    assert child['inspection']['offset']==24
    assert child['analysis_context_sha256']==parent['analysis_context_sha256']
    assert child['alignment']==parent['alignment'] and child['input_hash']==parent['input_hash']

"""Generated contract packets only. These are not independent satellite evidence."""
import copy
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from geoalibi.demo import scene
from geoalibi.vision import investigate, png
from geoalibi.dossier import build_packet
from geoalibi.inspection_chain import verify_chain


def packets(tmp_path):
    a=scene(); proposal=np.zeros(a.shape[:2],np.uint8)
    for y in range(20,620,70):
        for x in range(20,620,70):proposal[y:y+18,x:x+18]=1
    result=[]; parent=None; parent_assets=None; context=None
    for i,offset in enumerate((0,24,48,72),1):
        analysis=investigate(a,a.copy(),proposal=proposal,region_offset=offset,expected_context=context)
        report={**analysis.report,'id':f'{i:032x}','synthetic':True}
        assets={k:png(analysis.images[k]) for k in ('before','after','proposal_mask','supported_mask','omitted_mask')}
        if parent:
            report['lineage']={'source_run_id':parent['id'],'root_run_id':f'{1:032x}',
                'analysis_context_sha256':context,'proposal_basis':'Generated parent proposal fixture.',
                'source_asset_sha256':{k:hashlib.sha256(parent_assets[k]).hexdigest() for k in ('before','after','proposal_mask')}}
        path=tmp_path/f'batch{i}.zip';path.write_bytes(build_packet(report,assets));result.append(path)
        parent,parent_assets,context=report,assets,report['analysis_context_sha256']
    return result


@pytest.fixture(scope='module')
def frozen_packets(tmp_path_factory):
    return packets(tmp_path_factory.mktemp('inspection-chain'))


def mutate(path,tmp_path,change):
    with zipfile.ZipFile(path) as z:
        report=json.loads(z.read('report.json'))
        assets={name[7:-4]:z.read(name) for name in z.namelist() if name.startswith('images/')}
    change(report,assets)
    target=tmp_path/(path.stem+'-changed.zip');target.write_bytes(build_packet(report,assets));return target


def test_unordered_complete_and_partial_chains_do_not_certify_change(frozen_packets):
    complete=verify_chain(list(reversed(frozen_packets)))
    assert complete['inspection_complete'] is True
    assert complete['batch_count']==4 and complete['inspected_regions']==81 and complete['remaining_regions']==0
    assert complete['cross_batch_spatial_partition_checked'] is True and complete['proposal_geometry_checked'] is True
    assert complete['inspected_eligible_pixels']==81*18*18
    assert complete['supported_pixel_union']==0
    assert complete['real_world_change_verification']=='not established by this check'
    partial=verify_chain(frozen_packets[:2])
    assert partial['inspection_complete'] is False and partial['remaining_regions']==33
    assert partial['inspected_regions']==48 and partial['inspected_eligible_pixels']==48*18*18
    single=verify_chain(frozen_packets[:1])
    assert single['cross_batch_spatial_partition_checked'] is False and single['remaining_regions']==57


@pytest.mark.parametrize('selection',[(1,), (0,2), (0,1,1), ()])
def test_missing_ancestors_duplicate_packets_and_empty_input_fail(frozen_packets,selection):
    with pytest.raises(ValueError):verify_chain([frozen_packets[i] for i in selection])


@pytest.mark.parametrize('change',['context','source','environment','model','input','parent','root','asset','ranks','ids','provider','verdict','omission','proposal','spatial','bounds','support-verdict','support-missing'])
def test_repacked_but_inconsistent_packets_are_rejected(frozen_packets,tmp_path,change):
    def modify(r,a):
        if change=='context':r['analysis_context_sha256']='f'*64
        elif change=='source':r['analysis_source_sha256']='f'*64
        elif change=='environment':r['analysis_environment']['opencv']='changed'
        elif change=='model':r['detector']='different detector'
        elif change=='input':r['input_hash']='f'*64
        elif change=='parent':r['lineage']['source_run_id']='f'*32
        elif change=='root':r['lineage']['root_run_id']='f'*32
        elif change=='asset':r['lineage']['source_asset_sha256']['before']='f'*64
        elif change=='ranks':r['inspection']['offset']=48
        elif change=='ids':r['regions'][0]['id']='R01'
        elif change=='provider':r['meta']['status']='completed'
        elif change=='verdict':r['counts']['supported']+=1
        elif change=='omission':a['omitted_mask']=png(np.zeros((640,640),np.uint8))
        elif change=='support-verdict':
            pixels=np.zeros((640,640),np.uint8);x,y,_,_=r['regions'][0]['bbox'];pixels[y+1,x+1]=255
            a['supported_mask']=png(pixels);r['supported_changed_pixels']=1;r['inspection']['supported_pixels']=1
        elif change=='support-missing':
            r['regions'][0]['verdict']='supported';r['counts']['supported']+=1;r['counts']['artifact']-=1
        elif change=='bounds':r['regions'][0]['bbox'][0]+=1
        elif change=='spatial':
            pixels=np.asarray(Image.open(io.BytesIO(a['omitted_mask']))).copy()
            pixels[25,25]=0;pixels[0,0]=255
            a['omitted_mask']=png(pixels)
        elif change=='proposal':a['proposal_mask']=png(np.zeros((640,640),np.uint8))
    bad=mutate(frozen_packets[1],tmp_path,modify)
    with pytest.raises(ValueError):verify_chain([frozen_packets[0],bad])


def test_fork_is_rejected_even_when_each_child_has_valid_source_binding(frozen_packets,tmp_path):
    fork=mutate(frozen_packets[1],tmp_path,lambda r,a:r.update(id='f'*32))
    with pytest.raises(ValueError,match='Forked'):verify_chain([*frozen_packets[:2],fork])


def test_checksum_tampering_fails_before_chain_validation(frozen_packets,tmp_path):
    target=tmp_path/'tampered.zip'
    with zipfile.ZipFile(frozen_packets[0]) as original,zipfile.ZipFile(target,'w') as out:
        for name in original.namelist():out.writestr(name,b'changed' if name=='report.json' else original.read(name))
    with pytest.raises(ValueError,match='integrity'):verify_chain([target])


def test_cli_preserves_existing_output_and_writes_nothing_on_invalid_chain(frozen_packets,tmp_path):
    out=tmp_path/'inspection.json'
    command=[sys.executable,'scripts/verify_inspection_chain.py',*(str(p) for p in frozen_packets),'--output',str(out)]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'Real-world change remains unverified' in result.stdout
    before=out.read_bytes()
    assert subprocess.run(command,capture_output=True).returncode!=0 and out.read_bytes()==before
    out.unlink()
    bad=[sys.executable,'scripts/verify_inspection_chain.py',str(frozen_packets[1]),'--output',str(out)]
    assert subprocess.run(bad,capture_output=True).returncode!=0 and not out.exists()


def test_zero_eligible_candidates_do_not_establish_absence_of_change(tmp_path):
    a=scene();analysis=investigate(a,a.copy(),proposal=np.zeros(a.shape[:2],np.uint8))
    report={**analysis.report,'id':'f'*32,'synthetic':True}
    assets={k:png(analysis.images[k]) for k in ('before','after','proposal_mask','supported_mask','omitted_mask')}
    path=tmp_path/'empty-candidate-set.zip';path.write_bytes(build_packet(report,assets))
    result=verify_chain([path])
    assert result['inspection_complete'] is True and result['eligible_regions']==0
    assert result['supported_pixel_union']==0
    assert result['real_world_change_verification']=='not established by this check'

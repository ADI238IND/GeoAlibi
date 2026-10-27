import io
import json
import zipfile

import pytest
from geoalibi.dossier import build_packet,verify_packet,challenge_log
from geoalibi.demo import pair
from geoalibi.vision import investigate


def test_packet_roundtrip_and_tamper_rejection():
    packet=build_packet({'id':'fixture','audit':[]},{'before':b'png-fixture'})
    assert len(verify_packet(packet)['files'])==2
    out=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(packet)) as original,zipfile.ZipFile(out,'w') as changed:
        for name in original.namelist():changed.writestr(name,b'changed' if name=='images/before.png' else original.read(name))
    with pytest.raises(ValueError,match='integrity'):verify_packet(out.getvalue())


def test_unresolved_alignment_is_never_labelled_refuted():
    a,b,_=pair();report=investigate(a,b).report
    region=report['regions'][0]
    entries=challenge_log({**region['checks'],'worst_perturbation_survival':.1},{'reliable':False},[{'survival':.8},{'survival':.8},{'survival':.8},{'survival':.1}])
    assert entries[0]['result']=='unresolved'
    assert entries[3]['result']=='sensitive'
    assert entries[4]['result']=='untested'


def test_supported_regions_survive_each_perturbation():
    a,b,_=pair();report=investigate(a,b).report
    assert report['counts']['supported']>0
    for r in report['regions']:
        assert len(r['challenge_log'])==5 and r['evidence_requests']
        if r['verdict']=='supported':assert all(e['survival']>=.55 for e in r['challenge_log'][3]['experiments'])

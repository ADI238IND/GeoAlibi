import importlib

import pytest
from fastapi.testclient import TestClient

from geoalibi.demo import pair
from geoalibi.vision import png


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GEOALIBI_DATA_DIR", str(tmp_path))
    # An explicit empty value prevents dotenv from loading a developer's real key.
    monkeypatch.setenv("MODEL_API_KEY", "")
    import geoalibi.app
    importlib.reload(geoalibi.app)
    with TestClient(geoalibi.app.app) as c:
        yield c


def test_full_investigation_review_export_and_persistence(client):
    response = client.post("/api/demo", json={"case": "mixed"})
    assert response.status_code == 200
    r = response.json()
    assert r["synthetic"] is True
    assert r["meta"]["status"] == "not_requested"
    assert r["counts"]["supported"] > 0
    assert client.get(r["assets"]["overlay"]).headers["content-type"] == "image/png"
    region = r["regions"][0]["id"]
    review = client.post(f'/api/runs/{r["id"]}/reviews/{region}', json={"decision": "needs_field_check", "note": "Need a third acquisition."})
    assert review.status_code == 200
    assert len(review.json()["audit"]) == 1
    stored = client.get(f'/api/runs/{r["id"]}').json()
    assert stored["regions"][0]["review"] == "needs_field_check"
    assert stored["regions"][0]["verdict"] == r["regions"][0]["verdict"]
    exported = client.get(f'/api/runs/{r["id"]}/report')
    assert "attachment" in exported.headers["content-disposition"]
    assert exported.json()["audit"][0]["note"] == "Need a third acquisition."
    assert client.get("/api/runs").json()[0]["id"] == r["id"]
    from geoalibi.dossier import verify_packet
    packet=client.get(f'/api/runs/{r["id"]}/packet')
    assert packet.status_code==200
    manifest=verify_packet(packet.content)
    assert manifest['run_id']==r['id'] and 'report.json' in manifest['files']


def test_missing_key_is_explicit_and_does_not_reserve_budget(client):
    before = client.get("/api/status").json()["budget"]["reserved_usd"]
    r = client.post("/api/demo", json={"case": "mixed", "use_meta": True}).json()
    assert r["meta"]["status"] == "unavailable"
    assert client.get("/api/status").json()["budget"]["reserved_usd"] == before


def test_upload_real_input_flow(client):
    a, b, _ = pair()
    r = client.post("/api/analyze", files={"before": ("a.png", png(a), "image/png"), "after": ("b.png", png(b), "image/png")}, data={"title": "Own images"})
    assert r.status_code == 200
    assert r.json()["synthetic"] is False
    assert r.json()["title"] == "Own images"


def test_bad_inputs_and_cross_origin_writes(client):
    assert client.post("/api/demo", json={"case": "bad"}).status_code == 422
    assert client.post("/api/demo", json={"threshold": .99}).status_code == 422
    assert client.post("/api/demo", json={}, headers={"Origin": "https://attacker.example"}).status_code == 403
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 403
    assert client.post("/api/analyze", files={"before": ("a.png", b"invalid"), "after": ("b.png", b"invalid")}).status_code == 422
    assert client.get("/api/runs/does-not-exist").status_code == 404


def test_security_headers_and_no_secret_exposure(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert "MODEL_API_KEY" not in client.get("/api/status").text


def test_landmark_upload_requires_valid_evidence(client):
    import json
    a,_,_=pair()
    points=[[50,50,50,50],[580,50,580,50],[50,580,50,580],[580,580,580,580],[150,180,150,180],[480,440,480,440]]
    files={"before":("a.png",png(a),"image/png"),"after":("b.png",png(a),"image/png")}
    good=client.post('/api/analyze',files=files,data={'landmarks':json.dumps(points)})
    assert good.status_code==200
    assert good.json()['alignment']['held_out_points']==2
    assert client.get(good.json()['assets']['landmarks_before']).status_code==200
    points[-1][2]+=20
    assert client.post('/api/analyze',files=files,data={'landmarks':json.dumps(points)}).status_code==422
    assert client.post('/api/analyze',files=files,data={'landmarks':'null'}).status_code==422

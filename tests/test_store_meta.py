import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from geoalibi import meta
from geoalibi.demo import pair
from geoalibi.store import Store
from geoalibi.vision import investigate


def test_budget_reservations_are_atomic_and_persist(tmp_path):
    store = Store(tmp_path)
    def reserve(_):
        try:
            store.reserve(.5, 1.)
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        result = list(pool.map(reserve, range(8)))
    assert sum(result) == 2
    assert Store(tmp_path).budget(1)["reserved_usd"] == 1


def test_meta_payload_validation_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key-not-real")
    a, b, _ = pair()
    analysis = investigate(a, b)
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        ids = payload["response_format"]["json_schema"]["schema"]["properties"]["regions"]["items"]["properties"]["id"]["enum"]
        interpretation = {"summary": "Mocked provider response for protocol testing.", "regions": [{"id": ids[0], "hypothesis": "Possible appearance difference", "alternate_explanations": ["shadow"], "needed_evidence": ["third image"]}]}
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(interpretation)}}], "usage": {"prompt_tokens": 100, "completion_tokens": 50}})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(meta.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    store = Store(tmp_path)
    asyncio.run(meta.enrich(analysis, store, 1))
    assert analysis.report["meta"]["status"] == "completed"
    assert len(calls) == 1
    assert calls[0]["model"] == "muse-spark-1.3"
    assert len(calls[0]["messages"][0]["content"]) == 4
    fresh = investigate(a, b)
    asyncio.run(meta.enrich(fresh, store, 1))
    assert fresh.report["meta"]["cache_hit"]
    assert len(calls) == 1
    assert store.budget(1)["reserved_usd"] == .5


def test_provider_failure_preserves_local_evidence_and_reservation(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key-not-real")
    a, b, _ = pair()
    analysis = investigate(a, b)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(meta.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(lambda _: httpx.Response(401, json={"error": "unauthorized"})), **kw))
    store = Store(tmp_path)
    asyncio.run(meta.enrich(analysis, store, 1))
    assert analysis.report["meta"]["status"] == "failed"
    assert "401" in analysis.report["meta"]["reason"]
    assert analysis.report["regions"]
    assert store.budget(1)["reserved_usd"] == .5


def test_unknown_model_region_rejected(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key-not-real")
    a, b, _ = pair()
    analysis = investigate(a, b)
    payload = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"summary": "x", "regions": [{"id": "R999", "hypothesis": "x"}]})}}]}
    real_client = httpx.AsyncClient
    monkeypatch.setattr(meta.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)), **kw))
    with pytest.raises(ValueError, match="invalid"):
        asyncio.run(meta.reason(analysis))


def test_adapter_version_invalidates_cached_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'test-key-not-real')
    calls = []
    async def reason(analysis):
        calls.append(True)
        return {'status': 'completed', 'interpretation': {'summary': 'fixture'}}
    monkeypatch.setattr(meta, 'reason', reason)
    a, b, _ = pair()
    store = Store(tmp_path)
    asyncio.run(meta.enrich(investigate(a, b), store, 1))
    monkeypatch.setattr(meta, 'ADAPTER_VERSION', 'future-geometry-fixture')
    fresh = investigate(a, b)
    asyncio.run(meta.enrich(fresh, store, 1))
    assert len(calls) == 2
    assert not fresh.report['meta'].get('cache_hit', False)
    assert store.budget(1)['reserved_usd'] == 1


def test_bad_sam_geometry_preserves_verdicts_and_is_not_cached(tmp_path, monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'test-key-not-real')
    monkeypatch.setattr(meta, 'sam_available', lambda: True)
    async def segment(image):
        raise ValueError('invalid geometry fixture')
    async def reason(analysis):
        assert analysis.report['sam']['status'] == 'failed'
        return {'status': 'completed'}
    monkeypatch.setattr(meta, 'segment', segment)
    monkeypatch.setattr(meta, 'reason', reason)
    a, b, _ = pair()
    store = Store(tmp_path)
    for _ in range(2):
        analysis = investigate(a, b)
        original = json.dumps(analysis.report['regions'], sort_keys=True)
        asyncio.run(meta.enrich(analysis, store, 1, with_sam=True))
        assert json.dumps(analysis.report['regions'], sort_keys=True) == original
        assert analysis.report['sam']['status'] == 'failed'
        assert 'sam_before_mask' not in analysis.images
        assert not analysis.report['meta'].get('cache_hit', False)
    assert store.budget(1)['reserved_usd'] == 1

import asyncio
from types import SimpleNamespace as NS

import numpy as np

from geoalibi.meta import segment


def test_sam_adapter_finalizes_lane_and_places_decoded_bytes(monkeypatch):
    import openai
    import meta_sam_parser
    monkeypatch.setenv("MODEL_API_KEY", "not-a-real-key")
    seen = []
    class Stream:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        def __aiter__(self):
            async def generate():
                for value in [{"type": "response.content_part.done", "item_id": "one", "output_index": 0, "content_index": 0,
                               "part": {"type": "output_text", "text": "parser-fixture"}}, {"type": "response.completed"}]:
                    yield NS(model_dump=lambda value=value: value)
            return generate()
    class API:
        def __init__(self, **kwargs): self.responses = self
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def create(self, **kwargs):
            assert kwargs["model"] == "sam-3.1"
            assert kwargs["input"][0]["content"][0]["text"] == "building"
            return Stream()
    def parse(source, format):
        async def final():
            async for event in source: seen.append(event)
            mask = NS(width=2, height=2)
            return NS(outcome=NS(status="completed"), diagnostics=[], records=[
                NS(kind="box", object_id=7, left=1, top=2, right=3, bottom=4), NS(kind="mask", object_id=7, mask=mask, bounds=NS(left=1, top=2, right=3, bottom=4))])
        return NS(final_result=final)
    monkeypatch.setattr(openai, "AsyncOpenAI", API)
    monkeypatch.setattr(meta_sam_parser, "parse_responses_stream", parse)
    monkeypatch.setattr(meta_sam_parser, "decode_mask_to_raster", lambda mask: bytes([1, 0, 1, 0]))
    summary, mask = asyncio.run(segment(np.zeros((8, 8, 3), np.uint8)))
    assert summary["objects"][0]["pixels"] == 2
    assert (mask > 0).sum() == 2
    assert mask[2, 1] == 255 and mask[3, 1] == 255
    assert any(e["type"] == "response.output_text.done" for e in seen)

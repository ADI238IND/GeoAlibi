import asyncio
from types import SimpleNamespace as NS

import numpy as np
import pytest

from geoalibi.sam_geometry import rasterize_records


def records(bounds=(1, 2, 3, 4), data=b'\x01\x00\x01\x00'):
    box = NS(kind='box', object_id='7', **dict(zip(('left', 'top', 'right', 'bottom'), bounds)))
    mask = NS(kind='mask', object_id='7', bounds=box, mask=NS(width=2, height=2, data=data))
    return [box, mask]


def decode(mask):
    return mask.data


def test_half_open_edges_do_not_add_or_stretch_pixels():
    objects, mask = rasterize_records(records((6, 6, 8, 8)), (8, 8), decode)
    assert objects == [{'id': '7', 'bbox': [6, 6, 2, 2], 'pixels': 2}]
    assert np.argwhere(mask).tolist() == [[6, 6], [7, 6]]
    # Interior placement must have exactly the same footprint as edge placement.
    _, interior = rasterize_records(records(), (8, 8), decode)
    assert np.argwhere(interior).tolist() == [[2, 1], [3, 1]]


@pytest.mark.parametrize('bounds', [(-1, 2, 3, 4), (6, 6, 9, 8), (1, 2, 1, 4),
                                    (1.5, 2, 3, 4), (float('nan'), 2, 3, 4)])
def test_invalid_bounds_fail_instead_of_clipping(bounds):
    with pytest.raises(ValueError):
        rasterize_records(records(bounds), (8, 8), decode)


def test_unpaired_repeated_or_mismatched_geometry_fails():
    pair = records()
    for malformed in (pair[:1], pair[1:], pair + pair):
        with pytest.raises(ValueError):
            rasterize_records(malformed, (8, 8), decode)
    pair[1].bounds = NS(left=2, top=2, right=4, bottom=4)
    with pytest.raises(ValueError):
        rasterize_records(pair, (8, 8), decode)


@pytest.mark.parametrize('data', [b'\x01', b'\x01\x02\x00\x00'])
def test_invalid_raster_fails(data):
    with pytest.raises(ValueError):
        rasterize_records(records(data=data), (8, 8), decode)


def test_empty_completed_segmentation_is_valid():
    objects, union = rasterize_records([], (8, 8), decode)
    assert objects == [] and not union.any()


def test_official_wire_example_through_real_parser_and_decoder():
    # Published Meta example: https://dev.meta.ai/docs/sam/reading-segmentation
    # Real codec/protocol regression, not a model inference or accuracy fixture.
    from meta_sam_parser import parse_responses_stream, image_segmentation_format, decode_mask_to_raster
    wire = "<0f>0<|box;x1=211;y1=228;x2=270;y2=254;w=320;h=334|><|mask;x=0;y=0;data=27,60,~!!!!M!0c[0o91w?q1!pIH4pPRVp2B3'7`e.ioeAf6-k/#Xd8%dX9x(|>"
    async def run():
        async def events():
            yield {'type': 'response.output_text.done', 'item_id': 'one', 'output_index': 0,
                   'content_index': 0, 'text': wire}
            yield {'type': 'response.completed', 'response': {'status': 'completed'}}
        return await parse_responses_stream(events(), image_segmentation_format()).final_result()
    result = asyncio.run(run())
    assert result.outcome.status == 'completed'
    assert not any(d.severity == 'error' for d in result.diagnostics)
    objects, union = rasterize_records(result.records, (334, 320), decode_mask_to_raster)
    parsed_mask = next(r for r in result.records if r.kind == 'mask')
    expected = np.frombuffer(decode_mask_to_raster(parsed_mask.mask), dtype=np.uint8).reshape(27, 60) * 255
    assert objects[0]['bbox'] == [211, 228, 60, 27]
    assert np.array_equal(union[228:255, 211:271], expected)
    assert int((union > 0).sum()) == int((expected > 0).sum())
    assert not union[255:, :].any() and not union[:, 271:].any()

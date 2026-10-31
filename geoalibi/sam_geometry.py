"""Place official parser masks using half-open source-image bounds."""
import cv2
import numpy as np

ADAPTER_VERSION = 'sam-half-open-2'


def rasterize_records(records, shape, decode):
    height, width = shape[:2]
    boxes, masks = {}, {}
    for record in records:
        if record.kind not in ('box', 'mask'):
            continue
        if getattr(record, 'frame', None) is not None:
            raise ValueError('Video-frame records are not valid image evidence.')
        destination = boxes if record.kind == 'box' else masks
        if record.object_id in destination:
            raise ValueError('Repeated SAM object geometry is ambiguous.')
        destination[record.object_id] = record
    if boxes.keys() != masks.keys():
        raise ValueError('SAM boxes and masks must pair exactly.')
    union = np.zeros((height, width), np.uint8)
    objects = []
    for identity, record in masks.items():
        box, bounds = boxes[identity], record.bounds
        coordinates = np.asarray([bounds.left, bounds.top, bounds.right, bounds.bottom], dtype=float)
        box_coordinates = np.asarray([box.left, box.top, box.right, box.bottom], dtype=float)
        if (not np.isfinite(coordinates).all() or not np.array_equal(coordinates, box_coordinates)
                or not np.array_equal(coordinates, np.floor(coordinates))):
            raise ValueError('SAM bounds must be matching finite integer coordinates.')
        x1, y1, x2, y2 = coordinates.astype(int)
        # Official parser has already converted inclusive wire endpoints to half-open.
        # Never clip then stretch: reject unsupported geometry instead of moving pixels.
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise ValueError('SAM bounds lie outside the source image.')
        mw, mh = record.mask.width, record.mask.height
        if not isinstance(mw, int) or not isinstance(mh, int) or mw <= 0 or mh <= 0 or mw * mh > 24_000_000:
            raise ValueError('Invalid or oversized SAM mask dimensions.')
        raster = np.frombuffer(bytes(decode(record.mask)), dtype=np.uint8)
        if raster.size != mw * mh or not np.isin(raster, [0, 1]).all():
            raise ValueError('SAM raster must contain exactly width times height binary values.')
        mask = cv2.resize(raster.reshape(mh, mw), (x2-x1, y2-y1), interpolation=cv2.INTER_NEAREST)
        union[y1:y2, x1:x2] |= mask * 255
        objects.append({'id': str(identity), 'bbox': [int(x1), int(y1), int(x2-x1), int(y2-y1)],
                        'pixels': int(mask.sum())})
    return objects, union

# SAM placement correction and validation

## Defect

The installed official `meta-sam-parser` 0.1.0 converts inclusive wire `x2/y2` to half-open `right/bottom` bounds. The old adapter added one again, enlarging interior boxes by one row and column before resizing their masks. Clamping at the image edge also made placement depend on whether an object touched the edge. Separately, orphan masks were silently ignored and duplicate boxes overwritten.

The corrected adapter uses each mask record's half-open bounds, checks agreement with its box, and resizes once to that exact extent using nearest-neighbour sampling. It rejects duplicate/unpaired records, video records, fractional/nonfinite/out-of-image bounds, and malformed or nonbinary rasters. Empty completed output remains a valid empty segmentation. Unsupported geometry becomes an explicit SAM failure while local deterministic verdicts remain available.

Evidence reports carry adapter version `sam-half-open-2` and the source coordinate convention. The version also namespaces the interpretation cache, preventing reuse of masks or Muse interpretations produced by the old geometry. This does not clear reservations or alter budget limits. A subsequent user-enabled uncached call still requires a new reservation.

## Validation

`tests/test_sam_geometry.py` feeds the published first button-mask payload from Meta's reading-segmentation guide through the real installed parser and codec, then asserts exact raster equality at `[228:255, 211:271]` and a 60×27 bounding box. It is a protocol regression using a published example, not fresh inference or satellite benchmark accuracy. Additional fixtures check image-edge placement, invalid bounds, missing/duplicate records, binary decoding and valid empty output. Integration tests cover cache invalidation and preservation of local verdicts on SAM failure.

Primary references:
- https://dev.meta.ai/docs/sam/reading-segmentation
- `meta-sam-parser` 0.1.0: `SegmentationMaskBounds` describes half-open source-media bounds; `_segmentation.py` converts wire endpoints once. The package metadata's Parsing behavior section documents the same conversion.

## Historical results and next step

Earlier live calls established connectivity and nonempty decoding, but their foreground counts and spatial masks were produced by the old placement code. Keep their logs as historical evidence; do not reuse those measurements as corrected spatial validation. No new paid API calls were made for this fix.

Next: once secure credentials and the existing budget ledger are available and billing is reconciled, run one licensed real satellite pair through the corrected adapter, inspect mask coordinates against original imagery, and retain adapter version, input hashes and request usage. The real-satellite quality claim remains unestablished.

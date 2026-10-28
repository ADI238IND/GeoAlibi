# Reviewed-landmark evaluation protocol

The automatic path still abstains on all seven selected real-image test demos. The assisted path has only been validated on controlled fixtures. No independently reviewed real-image annotations have been collected yet.

Use `python scripts/evaluate.py DATASET --detector unet --landmarks annotations.json --output results.json` to evaluate the same exact pairs twice: automatic registration and supplied-landmark registration. No Meta calls, training or downloads occur. The original top-level metrics remain automatic; conditional assisted metrics are under `assisted`. Do not pool them or present assisted results as automatic performance.

## Annotation collection

1. Freeze the evaluation filenames before viewing results. Use matching `A/`, `B/`, and binary `label/` files. Labels must describe change in BEFORE-image coordinates. The scorer does not warp labels or infer their coordinate convention.
2. One annotator picks 6–20 stable correspondences using the visual picker. Coordinates refer to the exact processed originals (EXIF orientation applied, maximum side 1024), not display canvas coordinates. Rows are `[after_x, after_y, before_x, before_y]`.
3. A different reviewer checks the correspondences against both original images, without using model masks or ground-truth changes to choose landmarks. Final two points are held out of transform fitting. Neither person should move points to improve benchmark scores.
4. Record the reviewer and annotator identifiers and SHA-256 of each original A, B and label file. Keep personal identifiers private as appropriate. Recorded identifiers are assertions; this tool cannot authenticate independence or correspondence truth.
5. The manifest's filename set must exactly match the evaluation set, including `--limit`. Missing, extra, duplicate, invalid or wrong-image records fail the run; there is no silent subset or fallback. Geometry must also pass the existing fit and held-out checks.

Manifest structure (replace placeholders; this is not real annotation data):

```json
{
  "schema": "geoalibi-landmarks-v1",
  "pairs": [{
    "file": "test_pair.png",
    "annotator": "annotator-id",
    "reviewer": "different-reviewer-id",
    "coordinate_space": "processed-original-images",
    "before_sha256": "<64 lowercase hex digits>",
    "after_sha256": "<64 lowercase hex digits>",
    "label_sha256": "<64 lowercase hex digits>",
    "landmarks": [[0, 0, 0, 0]]
  }]
}
```

The example landmark row is intentionally incomplete; supply 6–20 distinct, spatially distributed actual correspondences. File hashes can be obtained with `sha256sum` or Python `hashlib.sha256(Path(...).read_bytes()).hexdigest()`.

## Reporting

Report automatic and assisted precision, recall, F1 and IoU separately, with the number of evaluated pairs, frozen manifest hash, alignment diagnostics and elapsed times. No-positive precision is null. Rejected, abstained and invalid-border pixels count as negatives over the complete processed footprint, so ignored overlap does not silently increase recall. Metrics remain uncalibrated and conditional on dataset/annotation quality. Full-footprint scoring is deliberately conservative; it is not selective-risk calibration. The raw-RGB mask also uses each arm's valid overlap, so it is diagnostic rather than a common registration-independent baseline.

Do not tune gates on the test set. Publish failed geometry and annotation exclusions before revising a frozen collection. Keep imagery licensing and acquisition provenance separate from geometric agreement.


### Label integrity

The evaluator requires label dimensions to match the EXIF-oriented original BEFORE image. Only subsequent downsampling to the processing resolution is allowed. Use single-channel or palette-index labels with background 0 and change 1 or 255. Palette colors do not determine classes. RGB/RGBA masks, mixed positive encodings and other class IDs must be explicitly remapped before evaluation. This prevents silently inflated or corrupted scores from incompatible annotations.

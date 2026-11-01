# Collect and score independent alignment evidence

The eight-scene experiment has useful U-Net proposals (78.66% pixel F1) but zero supported pixels. Every saved production transform failed its reliability gate. Those internal decisions do **not** establish true geometric error. Independent stationary-point review is needed before revising registration or acceptance policy.

This workflow produces an offline original-image review page and separately scores the **saved** production transforms. It does not run a detector, refit a transform, expose change labels/predictions to the collector, or promote failed production decisions.

## Build the private collection pack

Restore the frozen inputs using [the existing acquisition commands](EXPANDED_EVALUATION.md), then:

```bash
python scripts/build_alignment_review.py datasets/levir-frozen-eight \
  --dataset-manifest docs/EXPANDED_EVAL_INPUTS.json \
  --output dist/blind-alignment-review
```

Use a new output directory; existing packs cannot be replaced. Open `dist/blind-alignment-review/review.html` locally in Chrome. It is self-contained, makes no network requests and needs no server, model weights, credentials or API calls. `task.json` records the exact dataset-manifest hash, original A/B/label hashes, processed image sizes and HTML checksum. The label bytes are read only for hash validation; their pixels are never decoded or embedded. The page embeds processed A/B originals and no benchmark report, transform, matches or model-derived layer.

**Keep this pack private.** It contains LEVIR/Google Earth source imagery, subject to the dataset's academic-only and underlying image terms. The generated pack is ignored by git and must not be published or included in public demo artifacts. The repository and CI artifacts contain only code, hashes, measured JSON and generated contract-test imagery.

## Collect before scoring

1. A collector who has not viewed predictions, model matches, transforms or change labels selects 6–20 stationary features in every pair. Use spatially distributed corners/road features that remain identifiable at both times. Avoid changed structures and shadows. Click After first, then the corresponding Before point. Use image/browser zoom for precision.
2. Check the independent-collection declaration after completing all pairs, enter an annotator identifier, and **Save unreviewed draft**. Drafts may be incomplete and are never accepted as reviewed evidence. Save before closing: there is no autosave or upload.
3. A different reviewer opens the same private pack, selects review mode and imports the draft. Source hashes, processed dimensions, task identity and the complete pair set must match. The reviewer checks all points against the original images and attests that they have not viewed model evidence/change labels. Each pair needs explicit approval. The two identifiers must differ. Review mode disables editing; corrections go back to collection, clear approvals and require a fresh review.
4. **Export all reviewed landmarks** becomes available only after every pair is approved with 6–20 valid, distinct, in-bounds, spatially spread points. Importing a draft or changing the reviewer/declaration clears all approvals. The Python scorer independently validates the geometry and complete image binding.
5. Freeze the exported JSON before scoring. Do not modify points in response to residuals. The output uses `geoalibi-landmarks-v1`, records `reviewed: true`, the independent-collection declaration and the exact frozen dataset-manifest hash. Names and declarations are assertions; the software cannot authenticate people or guarantee blindness, stationary-point truth or independent review.

## Score frozen production transforms

Use the saved eight-scene **baseline** report; its registration diagnostics are identical to the saved U-Net arm. All points are evaluation points, including those that would otherwise fit a landmark-assisted transform.

```bash
python scripts/check_benchmark_alignment.py \
  docs/EXPANDED_BASELINE_EVALUATION.json \
  alignment-reviewed-landmarks.json datasets/levir-frozen-eight \
  --dataset-manifest docs/EXPANDED_EVAL_INPUTS.json \
  --output independent-production-alignment.json
```

The command refuses existing output, mismatched or changed input bytes, incomplete/duplicate filenames, wrong task binding, missing review declarations, same-person IDs, invalid geometry, nonfinite matrices and invalid saved decisions. It scores the entire processed footprint's coordinate system, up to 1024px, with no refitting. Per-pair outputs preserve every point, the saved matrix and production reliability flag, identity and frozen-transform errors, RMS/max residuals and fraction within the existing 2.5px diagnostic tolerance. Hashes bind the supplied unsigned benchmark, annotation file and frozen input manifest; they do not authenticate those artifacts. No pooled accuracy or acceptance-policy threshold is inferred.

The older [LoFTR independent scorer](INDEPENDENT_ALIGNMENT.md) remains available for its seven-crop research audit. Use the new scorer for saved production benchmark reports.

## Evidence status — 1 November 2026

The eight-scene blind pack has been generated locally from all 24 verified source files. **No human-collected, separately reviewed real-image annotation manifest exists yet, so no independent alignment score is reported.** Browser/CLI roundtrip tests use generated images and invented point geometry solely to test contracts. They are not satellite accuracy or independently reviewed evidence.

Next: complete actual blind collection and separate review, freeze the result, then inspect residuals. Any resulting policy change requires a separate frozen evaluation. New paid API spend and reservations are $0; the historical $0.54 reservation remains unreconciled. Corrected live Meta validation still requires secure credentials, ledger reconciliation and billing access.

# Review a frozen learned alignment independently

LoFTR's own random held-out matches are not independent truth. The research audit now supports measuring a **frozen** model transform against separately collected stationary landmarks. No point from this review fits or refines the transform; all review points are evaluation points. A low residual never promotes a model candidate or changes production registration.

## Collection protocol

1. Freeze the seven actual filenames in `docs/LOFTR_AUDIT.json`. Include every actual pair, including failures; do not annotate only the passing pair.
2. An annotator selects 6–20 stationary, spatially distributed points in the original Before/After images using the existing visual picker. A different reviewer checks them. Collect without viewing model matches, transforms, predictions or ground-truth change masks. Do not copy matches from the LoFTR audit.
3. Use the `geoalibi-landmarks-v1` manifest described in [ASSISTED_EVALUATION.md](ASSISTED_EVALUATION.md), with original-image hashes and distinct annotator/reviewer identifiers. Add `"collection_basis": "independent-original-image-review"` to every pair. This is an explicit assertion, not authenticated proof of independence. Portable picker drafts are unreviewed and cannot be supplied directly.
4. Preserve the frozen annotations before scoring. All points must be distinct in both images, inside 256px processed originals, and cover at least 10% of each image's area. Bad geometry fails explicitly; points are not silently discarded. Do not edit annotations to improve residuals.

Run from the repository root:

```bash
python scripts/check_independent_alignment.py docs/LOFTR_AUDIT.json reviewed-landmarks.json datasets/levir-author-demo --output independent-alignment.json
```

This makes no API calls and needs no model weights. It first replays the stored audit, requires complete filename coverage, checks annotation hashes against audit hashes and exact local A/B/label bytes, and verifies processed dimensions. The output binds both input JSON files by SHA-256 and preserves every reviewed point, identity residual, frozen-transform residual, RMS, maximum error and fraction within the pre-existing 2.5px diagnostic tolerance.

Candidates with no transform keep `null` transform metrics. Failed model gates remain failed even if independent residuals are small. Results distinguish the number of actual pairs, model candidate passes and available transforms. No pooled accuracy or production pass threshold is inferred. Residuals measure correspondence agreement, not physical change, acquisition provenance or geographic accuracy.

## Current evidence status

No independently reviewed real-image landmark manifest has been collected. Consequently **no independent alignment result is claimed**. Automated regression fixtures test translation direction, no-refit behaviour, abstention, invalid/spatially concentrated points, wrong-image binding and exact set coverage; they are not satellite benchmark accuracy. Once actual annotations exist, run this check before proposing any production integration, then evaluate a separately frozen broader split.

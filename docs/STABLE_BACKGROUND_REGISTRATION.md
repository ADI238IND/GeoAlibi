# Stable-background registration research candidate

This candidate is isolated from the application and production verification gate. It is intended to reduce the influence of excluded changed objects on registration. It has not been evaluated on new satellite scenes or independently reviewed landmarks. Existing reported results remain unchanged.

Run from the matching source checkout:

```bash
python scripts/check_stable_registration.py before.png after.png before-excluded.png after-excluded.png research-result.json
```

Images must be equal-size RGB inputs with each dimension between 64 and 2048. Exclusions must be binary grayscale PNGs, 255 for excluded objects and 0 for permitted background, separately expressed in each original image's frame. Inputs are never resized. Use independently supplied exclusions or a detector fixed before evaluation; never use test-label change masks, tune exclusions to the desired transform, or assume an unexcluded pixel is actually stable. All-zero masks are allowed as an unmasked research control.

The candidate dilates exclusions by 32 pixels, detects SIFT features in the remainder, applies a conservative descriptor-clearance check, and retains only bidirectional ratio-filtered one-to-one locations. Duplicate keypoint orientations at the same location do not count as independent evidence. The existing fixed correspondence audit fits on one subset and checks residuals on a deterministic disjoint holdout. It also checks bounded scale/rotation/translation, consensus and spatial coverage. The holdout is from the same feature matcher; it is not independent acquisition or human alignment truth. Clearance is a conservative heuristic, not proof that no descriptor depends on changed pixels.

Output retains input-array hashes, original coordinate correspondences, fitting/holdout indices, residuals and the candidate matrix when available. No previous report is overwritten. No weights, provider calls, credentials or budget ledger are used. Masks that exclude all usable content and textureless images fail to produce a passing candidate.

Procedural regression controls cover a known shift plus an excluded local edit, unrelated textures, low texture, complete exclusion, invalid masks and repeatability. They are not satellite benchmark accuracy. Before any production promotion: freeze this protocol, collect independently reviewed stationary landmarks, evaluate new untouched scenes with failure/coverage reporting, compare against the existing method and preserve missed-change costs. Do not tune on the eight already observed LEVIR scenes and call the result untouched evaluation.

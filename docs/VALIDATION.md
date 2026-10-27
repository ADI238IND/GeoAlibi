# Validation — 27 October 2026

## Completed checks

- `python -m pytest -q`: **22 passed** in 9.57 seconds (Python 3.12).
- `node --check geoalibi/static/app.js`: passed.
- `python -m compileall -q geoalibi scripts`: passed.
- Real Chromium 153 browser run through the local HTTP server: passed fixture execution, PNG asset loading, region filtering and selection, saved review and audit persistence, image-view switching, comparison slider, JSON file download with review data, three nuisance scenarios, multipart image upload, reload/history recovery, and a 390-pixel mobile overflow check.
- Desktop and mobile renderings were visually inspected. Browser page-error collection was empty.
- The benchmark CLI was exercised on one generated A/B/label fixture and returned a valid result file. **This was a runner smoke test, not a real satellite benchmark.**
- One dependency deprecation warning came from FastAPI's TestClient using httpx; it did not affect the passing tests. Exact top-level tested versions are listed in TESTED_DEPENDENCIES.txt.

## Illustrative scenario behavior

These are procedural fixtures, not held-out satellite measurements.

| Scenario | Candidate behavior | Supported | Review | Nuisance explained |
| --- | --- | ---: | ---: | ---: |
| Two structural edits plus a local shadow | 6 candidate regions | 2 | 4 | 0 |
| Five-pixel/four-pixel translation | 39 candidates, largest 24 inspected | 0 | 0 | 24 |
| Global lighting change | 36 candidates, largest 24 inspected | 0 | 0 | 24 |
| Identical pair | No candidates above threshold | 0 | 0 | 0 |

The shadow fixture initially exposed a failure in edge-only evidence: reduced contrast can remove Canny edges without changing objects. Local luminance correlation was added as contradictory evidence. Three additional fixed, unseen fixture texture seeds with combined shift and brightness changes also yielded no supported verdict. This remains synthetic test evidence; it does not establish generalization to satellite imagery.

## Provider integration checks

- Mocked Muse protocol request, structured field validation, cache reuse, unknown region rejection, and 401 failure handling: passed.
- Mocked SAM streaming lane finalization and bytes-to-raster placement: passed.
- Atomic reservation test: eight concurrent requests against a $1 local ceiling accepted exactly two $0.50 reservations; total persisted across Store instances.
- Missing key made no provider calls or reservations, and was explicitly reported in the UI/API.
- **Live Muse Spark and SAM calls were not executed. No API key is available in this workspace.**

## Remaining validation

Verify the actual Meta API key, balance and allowed models. Run live request/response checks, including SAM mask placement on real imagery. Integrate a licensed trained proposal detector, lock a real held-out benchmark split, and report full precision/recall/F1/IoU alongside false alarms, abstention coverage and latency. Confirm full official participant rules and deliverables before any submission. No real-data accuracy, production readiness, or hackathon-winning claim is made.


## Live continuation update

Muse Spark authenticated and returned a completed structured interpretation of six fixture candidates. Its recorded usage was 2,932 input tokens and 1,340 output tokens. SAM completed both fixture requests with zero building detections; this establishes valid empty-response handling, not nonempty mask correctness. The main three-call experiment is estimated at $0.01436 using published standard rates, excluding separate smoke calls. A later smoke returned `ready` with 157 total tokens. See LIVE_VALIDATION.json for sanitized metadata; no key is included. The earlier no-key limitation above describes the initial build, not the current continuation.

A separate live SAM nonempty-output check on Meta's official duck photo returned **5 objects and 50,090 foreground mask pixels** at processed dimensions 1024 × 767. The official parser, lane finalization, byte decoding, and box placement completed. This is a parser smoke test on an ordinary photo, not validation on remote-sensing imagery. See SAM_DECODER_VALIDATION.json. All 22 behavioral tests passed again after configuring the real key; tests explicitly suppress dotenv key loading.


## Trained proposal milestone

27 tests pass, including tile boundary/channel normalization, malformed model output, checkpoint refusal, semantic proposal replacement and no silent fallback. CPU inference loaded the exact pinned author checkpoint and ran successfully. The upload API accepted a real pair in trained mode and exported its proposal mask. The browser workflow passed again at desktop and 390px mobile widths. See TRAINED_DETECTOR.md for real-sample diagnostic results, limitations and dataset terms. Local learned inference incurred no Meta API charges.

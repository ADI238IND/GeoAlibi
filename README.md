# GeoAlibi

**A change needs an alibi.** An evidence-first workstation for investigating whether an apparent satellite-image change survives alternative explanations.

Built for Aditya Singhal's Meta Global AI Developer Hackathon idea, Indie Dev Track. This is a working local research prototype. Live Muse Spark interpretation and SAM response decoding have been exercised; real satellite accuracy and deployment readiness remain to be established. It is not a completed hackathon submission.

## Integrated release — 1 November

The main-targeted [release PR #20](https://github.com/ADI238IND/GeoAlibi/pull/20) brings together the classical/larger-context experiments, replayable learned-match audit, corrected SAM geometry, frozen eight-scene evaluation, blind independent-review workflow and current offline deliverables. Research matchers remain separate from production registration. See [release status](docs/RELEASE_STATUS.md) for established evidence and remaining blockers.

Generate a credential-free offline rehearsal with four clearly labelled procedural scenarios and verified evidence packets:

```bash
python scripts/build_demo_bundle.py --output dist/offline-demo
```

The bundle also includes a separate summary of the saved eight-scene results and source reports, checked for complete frozen coverage, consistent counts and explicit missed changes. It runs no new model inference.

Use a new output directory for each run. CI builds this bundle and retains it with desktop/mobile screenshots as a downloadable workflow artifact for seven days. This is a local demo deliverable, not a hosted deployment or competition submission.

## Frozen eight-scene diagnostic — 1 November

A preregistered subset of eight new full LEVIR test scenes gives U-Net proposals 78.66% pixel F1 (baseline 8.08%). Both verified arms accept zero pixels: registration is flagged unreliable by the current gate in all eight scenes. This is a small research diagnostic, not full-benchmark accuracy or end-to-end readiness. See [protocol, all-scene results and reproduction](docs/EXPANDED_EVALUATION.md).

Collect independent geometry evidence with the [offline blind landmark-review workflow](docs/BLIND_ALIGNMENT_REVIEW.md). It shows original pairs only, requires a separate reviewer and scores saved production transforms without refitting. Real reviewed annotations are still needed.

Each investigation now shows its diagnostic state and inspection coverage, including eligible regions/pixels omitted by the 24-region cap. The purple Outside batch view locates eligible regions omitted by the cap, with an exportable binary omission mask; small filtered components are excluded. Evidence ZIPs include these spatial assets and a readable `SUMMARY.md`; an empty supported mask is never presented as proof of no change. Use **Inspect ranks …** to create the next linked 24-region investigation in the same full-scene context. Original reports stay intact; continuation reuses the saved proposal mask and makes no detector or paid-provider call. Results, supported masks and omission maps describe each batch separately. A changed analysis context is rejected; older runs without a context must be rerun first. Historical runs retain unknown pixel coverage rather than inventing it.

## Start on Windows PowerShell

Install Python 3.10 or newer. Extract this project, open its folder in PowerShell, then:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[meta,test]"
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn geoalibi.app:app --host 127.0.0.1 --port 8080
```

Open **http://127.0.0.1:8080**. No Node build step or API key is needed for the local image analysis and illustrative scenarios.

On macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[meta,test]'
cp .env.example .env
.venv/bin/python -m uvicorn geoalibi.app:app --host 127.0.0.1 --port 8080
```

## Connect the Meta API

Edit `.env` locally and set `MODEL_API_KEY` to the key from your Meta Model API dashboard. Restart the server. Never paste a key into the frontend or commit `.env`.

The user's stated $150 credits have not been independently verified by this code. A credit balance is not an API credential. Check the active balance, expiry, payment requirements and account controls in Meta Billing before enabling calls.

1. Optional low-token connectivity check: `python scripts/smoke_meta.py` (makes one paid request and reserves $0.01 in the local ledger).
2. Enable **Muse Spark interpretation** before running a scenario or uploading images.
3. Optionally enable **SAM 3.1 building evidence**. This calls SAM once for each image using the official parser, then sends the measured evidence with the imagery to Muse Spark.
4. Inspect interpretation separately from the deterministic verdict. Provider failures preserve the local results and visibly report their status.

`GEOALIBI_API_BUDGET_USD=10` sets a conservative **local reservation ceiling**. Every uncached model investigation reserves $0.50 before any outbound call; reservations persist across restarts and failures. No automatic retry is made. Identical successful interpretations are cached. This does not measure actual charges, verify remaining credit, control other applications using the key, or enforce a Meta billing cap.

Uses standard model mode. It does not select contributor/training mode.

## What works

- Before/after swipe comparison, residual and candidate overlays.
- PNG/JPEG/WebP uploads, content decoding and image size limits, EXIF stripping in stored assets.
- ORB/RANSAC and phase-correlation registration hypotheses, scored against identity.
- Robust per-channel global lighting correction.
- Candidate-level registration reduction, illumination reduction, local edge disagreement, local luminance correlation, and one-pixel perturbation checks.
- Supported / nuisance explained / human review verdicts with supporting and contradictory evidence.
- Explicit abstention on low-texture input and inconclusive local appearance changes.
- Optional live Muse Spark structured multimodal interpretation and SAM building evidence.
- SQLite investigation history, append-only human reviews, downloadable JSON evidence reports and image masks.
- Persistent budget reservations, cache, local host/origin guard and restrictive browser security headers.
- Held-out benchmark runner and behavioral tests, including mocked provider protocol/error tests.

## What is not established

- The default detector remains the RGB baseline. An optional author-released trained U-Net is now integrated; see [trained detector setup and evaluation](docs/TRAINED_DETECTOR.md). GeoAlibi did not train these weights.
- Current real-data evidence uses eight newly selected full test scenes: pinned U-Net proposal F1 78.66%, baseline 8.08%, supported recall 0 in both arms. The older seven selected demo crops remain historical development evidence. See docs/EXPANDED_EVALUATION.md for all cases and limitations. Built-in scenario images are procedural illustrations.
- **Live Muse Spark and SAM calls passed on an illustrative image pair on 27 October.** This validates the API integration, not accuracy on satellite imagery. Real-image SAM mask geometry and interpretation quality still need evaluation.
- Verdicts and diagnostic scores are not calibrated probabilities, ground truth or emergency guidance. SAM does not automatically prove an object changed.
- Input images must depict the same footprint and have the same processed dimensions. The app does not validate provenance or georeferencing. It handles rendered RGB imagery, not full multispectral GeoTIFF workflows.
- Global corrections do not reliably resolve cloud, seasonal vegetation, local shadows, parallax, sensor differences, or major perspective changes. Unknowns need more evidence.
- Maximum processing side is 1024 px; uploads over 24 megapixels or 12 MB fail clearly. Images are not automatically stretched to match.
- At most 24 largest regions are inspected and at most 8 passed to Muse per run. Omitted candidates are reported. No physical area is inferred from pixel counts.
- This is a localhost-only, single-user workstation. Before hosting publicly, add authentication, access control, deployment-aware proxy handling, rate limits, a persistent job queue, global concurrency and budget controls, retention/deletion controls, and an abuse review. Local image uploads and reports persist under `.geoalibi/`; it is excluded from version control.

## Tests

```bash
python -m pytest -q
```

Tests cover nuisance suppression, structural-change preservation, shadow abstention, unseen fixture seeds, texture failure, invalid imagery, full upload/review/export workflows, missing keys, provider failure, response reference validation, cache reuse, and concurrent spending reservations. See `docs/VALIDATION.md` for this run's results.

## Real-data evaluation

Obtain a licensed held-out binary change dataset such as LEVIR-CD from its original authors. Do not train or tune on the evaluation split. Preserve its license and citation. Use this layout:

```text
dataset/test/
  A/scene001.png
  B/scene001.png
  label/scene001.png
```

```bash
python scripts/evaluate.py dataset/test --output benchmark-results.json
```

The runner reports raw-baseline versus supported-mask pixel precision, recall, F1, IoU, counts, input hashes, settings and timings. Rejected/abstained pixels count as negative; selective review can reduce false alarms while losing recall. Do not report precision alone. Labels must be binary and use matching filenames. Labels are resized by nearest-neighbor to processed coordinates; report that when comparing with published results. This runner makes no model API calls.

## Architecture

`geoalibi/vision.py` owns local measurements and verdicts. `meta.py` owns explicit optional provider calls. `store.py` owns reports, review history, cache and atomic budget reservations. `app.py` serves the API and dependency-free HTML/CSS/JS client. No secrets are sent to the browser.

The model can suggest explanations and further evidence; it cannot change the deterministic verdict. Human reviews are separate append-only events. Exported reports retain both.

## Official integration references

- https://dev.meta.ai/docs/cookbook/quickstart-chat-completions
- https://dev.meta.ai/docs/image-understanding
- https://dev.meta.ai/docs/structured-output
- https://dev.meta.ai/docs/media-segmentation
- https://dev.meta.ai/docs/cookbook/sam-api-basics
- https://dev.meta.ai/docs/sam/reading-segmentation
- https://dev.meta.ai/docs/pricing-rate-limits

SAM uses the `meta-sam-parser` package; the event-lane finalization pattern follows Meta's official cookbook. Third-party dependencies retain their own licenses. This project contains no downloaded pretrained weights, third-party datasets, or original Meta source files.

## Next milestones

1. Extend the completed live Muse/SAM smoke validation to appropriately licensed satellite imagery.
2. Resolve the real-sample registration/abstention failure using larger context and independent registration evidence. Keep verification independent of the proposal model.
3. Evaluate a fixed held-out real satellite split plus preregistered nuisance stress transforms; report both false-positive reduction and missed-change cost.
4. Audit registration on repeated structures and difficult geographic/sensor conditions; add explicit cloud masks and acquisition metadata.
5. Test with independent reviewers, prepare the required demo and confirm the full participant rules before submission.



## Trained detector milestone

See [TRAINED_DETECTOR.md](docs/TRAINED_DETECTOR.md) (model setup, licenses, reproducibility and the all-abstention failure report). Optional weights and images are not bundled. The trained path was exercised through the real upload API; 27 automated tests and the desktop/mobile browser workflow pass.


## Challenge log and portable evidence (v0.3)

Every new region records five alternative-explanation challenges, with explicit unresolved/untested outcomes and prioritized evidence requests. Supported findings must survive each of four registration perturbations, not just the average. The Evidence packet button downloads source/derived images, current report and review history, plus an unsigned SHA-256 manifest. Verify downloaded content with `python scripts/verify_packet.py evidence.zip`. Checksums detect changes relative to the manifest; they are not signatures, acquisition provenance, or proof of correctness. Packets contain imagery: share only where the imagery terms and your privacy requirements allow. The registration bottleneck on the seven real demo pairs remains unresolved.


## Landmark-assisted registration (v0.4)

Advanced uploads accept 6–20 matched landmarks as `[after_x, after_y, before_x, before_y]` rows in processed original-image pixel coordinates. Supply stationary, independently checked correspondences. The first N−2 rows fit a bounded similarity transform; the final two rows are held out and are never used to refit. Fit points must span 10% of scene area; held-out points must be separated. Fit RMS must be ≤1.5px, held-out RMS ≤2px, and each held-out error ≤3px. The transform is limited to small shifts, ≤5° rotation and scale 0.95–1.05. Invalid evidence fails explicitly.

Reports include all supplied points, their hash, fit/held-out residuals and source disclosure. Evidence packets include numbered landmark overlays: green fitting points and amber held-out points. This checks geometric consistency of user-supplied correspondences, not their real-world truth, acquisition provenance or independent authenticity. Do not generate guessed identity correspondences to bypass an unresolved automatic registration gate. No real independently reviewed landmark manifest has yet been collected; the latest eight-scene zero-supported-pixel result remains unresolved.


## Visual landmark picker (v0.5)

Under Upload your imagery, choose both files and open **Pick matched landmarks visually**. Click a stationary landmark in Before, then its match in After. Add at least six well-spread pairs; the final two are held out. Undo/Clear are available. Explicitly enable **Use picked landmarks** before submitting. Selecting another image clears picks. Keyboard users can focus either canvas, move with arrows (Shift for 10px), and select with Enter.

The local preview endpoint uses the same EXIF orientation and resize pipeline as analysis, returns a processed PNG with no-store headers, and does not save an investigation or call a model. Coordinates are image pixels, not latitude/longitude. Geometric checks and user-supplied evidence limitations from v0.4 still apply. The advanced JSON path remains available and is disabled while picked landmarks are opted in.

## Experimental learned-match audit

[LoFTR audit instructions](docs/LOFTR_AUDIT.md) provide a fixed CPU protocol and model-free replay of saved raw correspondences. This research tool does not change production registration. Candidate consistency is not independently verified alignment or change accuracy; the selected demo pairs are not a full benchmark.

The [independent alignment check](docs/INDEPENDENT_ALIGNMENT.md) scores frozen learned transforms against separately collected, image-bound reviewed points without refitting. Real independent annotations are still required; model consistency alone is not validation.


## SAM geometry correction

The SAM adapter now respects the official parser's half-open bounds, avoiding an extra row/column during mask placement. It rejects unpaired, duplicate, out-of-bounds or malformed geometry rather than silently dropping or stretching evidence. A published Meta payload is tested through the real parser and decoder offline. This validates protocol placement, not satellite segmentation accuracy. Older cached interpretations are invalidated by the adapter version; historical live mask-area measurements require rerunning before reuse. See [SAM_GEOMETRY.md](docs/SAM_GEOMETRY.md).

For new real-data evaluation, [freeze the exact input split](docs/FROZEN_BENCHMARK.md) before inspecting results. The evaluator can verify original A/B/label bytes against that manifest and discloses whether a run used frozen inputs.

Benchmark output now reports [verification benefit and missed-change cost](docs/VERIFICATION_TRADEOFF.md) together, including per-pair metrics and separate automatic/assisted pixel transitions. Both the historical seven-pair RGB rerun and the latest eight-scene experiment produced zero supported pixels; removing false alarms also removed every correctly proposed change pixel.

# GeoAlibi

**A change needs an alibi.** An evidence-first workstation for investigating whether an apparent satellite-image change survives alternative explanations.

Built for Aditya Singhal's Meta Global AI Developer Hackathon idea, Indie Dev Track. This is a working local research prototype. Live Muse Spark interpretation and SAM response decoding have been exercised; real satellite accuracy and deployment readiness remain to be established. It is not a completed hackathon submission.

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

- **The detector is an RGB difference baseline, not a trained deep change-detection model.** The engine accepts an optional proposal mask in Python, but the UI uses the baseline.
- **No real satellite benchmark accuracy has been measured in this build.** The built-in scenes and stress fixtures are procedural illustrations, prominently labelled. Passing fixture tests is not evidence of real-world accuracy.
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

1. Run actual Muse/SAM calls with the user's key; verify schema, segmentation coordinate placement, usage and cache behavior.
2. Integrate and compare a licensed pretrained change detector against the existing RGB baseline. Keep verification independent of the proposal model.
3. Evaluate a fixed held-out real satellite split plus preregistered nuisance stress transforms; report both false-positive reduction and missed-change cost.
4. Audit registration on repeated structures and difficult geographic/sensor conditions; add explicit cloud masks and acquisition metadata.
5. Test with independent reviewers, prepare the required demo and confirm the full participant rules before submission.


# Judge quickstart — submitted release

GeoAlibi is a local research workstation. The submitted video is an offline visual walkthrough with procedural imagery and synthetic narration. It is not a live app recording or live Meta inference.

## Run the actual app (no credential or paid calls)

From the repository root, use Python 3.10+ in a fresh virtual environment:

```bash
python -m pip install -e ".[meta,test]"
python -m uvicorn geoalibi.app:app --host 127.0.0.1 --port 8080
```

Open http://127.0.0.1:8080. Keep Muse/SAM disabled for this local rehearsal. The default detector is RGB; the optional pretrained U-Net requires separately licensed downloaded weights.

1. Run **Structural edits + shadow**, a labelled procedural fixture. Inspect the supported and human-review candidates separately. These outcomes demonstrate software behavior, not satellite accuracy.
2. Compare Before/After using the swipe control. Open candidate evidence and alternative-explanation challenges.
3. Run registration-shift, illumination and unchanged fixtures. Compare nuisance outcomes against the mixed case.
4. Add a human review note. It is retained as a human statement, not converted into machine-verified truth.
5. Download an evidence packet and check it with `python scripts/verify_packet.py evidence.zip`. Unsigned checksums check consistency, not authenticity or correctness.
6. For batches with omitted candidates, inspect Outside batch and continue inspection. Each linked batch retains full-scene context; its supported mask is not a cumulative full-scene verdict.

## Review the research evidence

[Full eight-scene diagnostic](EXPANDED_EVALUATION.md): U-Net proposal pixel F1 78.66%, RGB baseline proposal F1 8.08%. Both supported arms accepted zero pixels; supported recall zero and precision undefined. The gate flagged all eight alignments unreliable, without independently proving their actual geometric error.

The optional Muse Spark/SAM integration has historical connectivity and decoding evidence and corrected geometry protocol tests. Corrected real-satellite Meta quality and end-to-end performance are unvalidated. No independent human landmark review has been completed. Do not interpret procedural supported candidates as resolving those gaps.

[Research PR #29](https://github.com/ADI238IND/GeoAlibi/pull/29) isolates a stable-background SIFT candidate. Its [CI passed](https://github.com/ADI238IND/GeoAlibi/actions/runs/41878567410), but it is outside submitted main behavior. Its 227 local tests are not the submitted release's 220-test count. No improved satellite change score is established.

## Reproduce the portable rehearsal

```bash
python scripts/build_demo_bundle.py --output dist/judge-rehearsal
python scripts/verify_demo_bundle.py dist/judge-rehearsal
```

Choose a new output directory if it already exists. Open its index.html locally. This replays procedural scenarios and saved satellite evidence; it does not rerun satellite models or call Meta.

The [MIT license](../LICENSE) covers original code/docs only; [third-party terms](../THIRD_PARTY_NOTICES.md) still govern imagery, weights and services. Do not redistribute source satellite imagery through evidence exports without the necessary rights.


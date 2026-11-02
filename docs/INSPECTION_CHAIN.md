# Verify linked inspections offline

A collection of individually valid evidence ZIPs is not automatically a valid inspection chain. Missing ancestors, forked retries or duplicate packets can produce misleading coverage totals. The offline checker validates one original-to-tip path, including every intermediate investigation, without contacting a server, loading a model, fitting alignment or reading credentials/ledger/billing.

## Collect the packets

1. Use a new v0.4.2 investigation, download its evidence packet, then use **Inspect ranks …** for subsequent batches.
2. Download each continuation's evidence packet. Retain every ancestor from the original to the chosen tip. Original reports/reviews stay intact; child packets do not replace them.
3. Supply these files in any order. Include one path only: two retries from the same parent are a fork and cannot be summed. Missing intermediate packets are rejected, rather than labelled partial success.

```bash
python scripts/verify_inspection_chain.py original.zip ranks25-48.zip ranks49-72.zip --output inspection-chain.json
```

The command requires the normal project dependencies, refuses an existing output, and validates/serializes before opening the new report. An invalid chain creates no report. Inputs are limited to 16 packets, 40 MiB per packet and 256 MiB combined; there is no silent truncation. Keep longer histories intact if these limits prevent a complete check.

## What is checked

- Existing unsigned packet manifests, all entry checksums, exact packet/report IDs, processed PNG dimensions/modes and binary masks.
- Original image-pixel hashes and identical saved proposal rasters, engine/source/context/environment, settings, model provenance and alignment across the path.
- Immediate-parent/root IDs, parent asset-byte hashes, exact rank continuity, stable global region IDs and no duplicated, forked, cyclic or disconnected coverage.
- Saved proposal **binary geometry** replay using the v0.4.2 3×3 opening/5×5 closing/minimum-area protocol. Component footprints must match recorded bounding boxes/pixel counts. Omitted/support masks cannot include regions outside their batch scope.
- Mask/count consistency, no overlapping supported pixels between batches and a consistent cross-batch spatial partition. Unreliable registration cannot claim supported pixels. Continuations must retain their no-provider-rerun status.

This replays only geometry of the supplied binary proposals. It does not rerun the proposal detector, registration, counterfactual classifier or model providers, and does not authenticate the recorded execution.

## Read the result correctly

`inspection_complete: false` means the supplied original-to-tip path is internally valid but leaves eligible ranks uninspected. The report gives remaining regions and preserves every packet's SHA-256. A valid original plus the next batch in the 81-region procedural contract example covers 48 ranks with 33 remaining.

`inspection_complete: true` means every eligible candidate at the **recorded filtering settings** is covered exactly once in that supplied path. Small filtered components remain excluded. It does not mean that all true changes were found, that alignment is independently verified, or that a supported candidate is real-world damage. The checker always records `real_world_change_verification: "not established by this check"`. Pixel unions are image coordinates, not physical area, calibrated confidence or benchmark accuracy.

Checksums and internal agreement do not establish acquisition authenticity, actual execution, stationary-point truth or independent review. Keep original imagery permissions and human-review provenance with the packets. Provider/billing claims require separate account evidence.

## Reproducible example and current evidence

CI retains two **generated browser-contract** packets, their `inspection-chain.json`, instructions and desktop/mobile screenshots. Download them from a successful workflow run and rerun the command above with the included filenames. These are procedural fixtures, not satellite accuracy or independently reviewed alignment evidence.

The saved eight-scene satellite results remain unchanged: U-Net proposal F1 78.66%, supported recall 0. Actual independent landmark collection/separate review and corrected live Meta validation remain outstanding. The checker makes $0 new API calls/reservations and does not reset or reconcile the historical $0.54 reservation.

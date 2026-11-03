# Verify the offline rehearsal before recording

Use the source checkout associated with the downloaded CI artifact, install the normal project dependencies, and locate the extracted `dist/offline-demo` directory. Do not execute untrusted HTML to verify it.

```bash
python scripts/verify_demo_bundle.py PATH_TO_EXTRACTED_OFFLINE_DEMO
```

Exit status zero prints a JSON verification report; invalid inputs return nonzero. No files are written or extracted, and no model, API, credential or ledger is accessed. CI retains its report as `test-results/offline-bundle-verification.json` alongside the player and screenshots.

For an external source pin, get the SHA-256 of `docs/SOURCE_MANIFEST.json` from the independently selected matching source checkout (not from the downloaded bundle itself):

```bash
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('docs/SOURCE_MANIFEST.json').read_bytes()).hexdigest())"
python scripts/verify_demo_bundle.py PATH_TO_EXTRACTED_OFFLINE_DEMO --expected-source-sha256 SHA256_FROM_ABOVE
```

The checker requires the exact flat file inventory, regular bounded files, manifest checksums and source binding. It rejects extra files, missing files, symlinks, directories, duplicate JSON keys, altered gallery images, mismatched scenario counts/provider statuses and inconsistent evidence packets. It recomputes the saved research summary from frozen input/report bytes, validates their source-manifest hashes, and checks the player and recording guide against the matching source templates. It does not run inference or regenerate procedural imagery.

Unsigned checksums are not signatures: an attacker who replaces a bundle and its unsigned manifests can produce internally consistent content. An independent source-manifest pin binds that manifest and its research report hashes; it does not attest actual execution, validate arbitrary README prose, authenticate acquisitions or certify change. The template check requires the same source version and can reject bundles from other versions. These are integrity checks, not a sandbox for adversarial code or a proof that declared zero API calls actually occurred.

All gallery images are procedural. The separate saved eight-scene diagnostic remains U-Net proposal F1 78.66%, baseline 8.08%, supported recall zero and supported precision undefined. Independent human alignment review, corrected real-image Meta validation and participant submission requirements remain outstanding. No public deployment or entry submission is performed by these commands.

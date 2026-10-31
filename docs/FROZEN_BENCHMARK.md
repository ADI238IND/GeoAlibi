# Freeze the benchmark before evaluation

The evaluator now preflights the exact A/B/label filename sets and hashes all selected original bytes, including labels. It rejects unmatched files even when limiting the evaluated subset. Negative limits and invalid scoring settings fail explicitly.

Before inspecting predictions, select an appropriately licensed independent split and freeze it:

```bash
python scripts/freeze_benchmark.py dataset/test --description "Record dataset source, split selection, prior use and applicable image terms" --output frozen-test.json
python scripts/evaluate.py dataset/test --dataset-manifest frozen-test.json --output benchmark-results.json
```

The freeze command refuses to overwrite a manifest. Archive or commit the manifest before running evaluation; a file generated after viewing results is not evidence of preregistration. Neither a description nor matching hashes proves licensing, independence or label correctness.

If using `--limit`, pass the same nonnegative value to both commands. Zero selects all; positive values select the first sorted filenames. Frozen records and limit must match exactly. Any changed image, label or selected filename stops evaluation before model inference. Original bytes are checked again as each pair is read to detect changes after preflight. All evaluated pairs retain their original A/B/label SHA-256s in the output, whether or not a frozen manifest was supplied. Outputs explicitly record `dataset_frozen` and the supplied manifest digest; an unfrozen run must not be described as a frozen benchmark.

This works with the baseline and optional pretrained detector, plus the existing separately reported assisted arm. It does not change registration thresholds or scoring conventions. Labels are still checked against original BEFORE dimensions and resized only to processed coordinates; rejected pixels count as negative.

No broader real benchmark was run as part of this change. Integrity regression fixtures are synthetic and are not accuracy evidence. The seven historical author-demo pairs remain development data, even if their bytes are now frozen.

---
status: active
owner: workflow
---

# Dioscorides Vocab Extraction Runbook (2026-03-02)

## Scope
- Isolate likely Dioscorides row-alignment errors (RV markers + duplicate keys/text) into an editable review file.
- Apply reviewed row fixes back to a patched Dioscorides CSV.
- Build a Dioscorides `entries`-shaped CSV from `data-workbench/diosc.build.csv` (preferred).
- Validate the CSV before extraction.
- Run vocab extraction with the Dioscorides prompt variant.
- QC completeness and output profile.

## Source-specific rule
- Keep the same `terms[]` + `qualities[]` schema.
- Do **not** assume Galenic 4-degree parallel methodology.
- Degrees/intensity are extracted only when explicit in the text.

## Inputs and outputs
- Source CSV: `data-workbench/diosc.csv`
- After missing-text patch: `data-workbench/diosc.patched.csv`
- After text-fixes patch (build-ready): `data-workbench/diosc.build.csv`
- Missing-text patch payloads: `data-workbench/diosc_missing_text_patch.csv`
- Missing-text apply report: `archive/docs/legacy_qc/diosc_missing_text_apply_report.md`
- Text-fixes patch payloads: `data-workbench/diosc_text_fixes_patch.csv`
- Text-fixes apply report: `archive/docs/legacy_qc/diosc_text_fixes_apply_report.md`
- Build audit summary: `data-workbench/diosc_build_audit.md`
- Build review sheet: `data-workbench/diosc_build_review.csv`
- Alignment review CSV: `data-workbench/diosc_alignment_review.csv`
- Alignment context report: `data-workbench/diosc_alignment_context.md`
- Alignment apply report: `archive/docs/legacy_qc/diosc_alignment_apply_report.md`
- Built entries CSV: `data-workbench/entries_diosc.csv`
- Build QC: `data-workbench/entries_diosc_qc.md`
- Prompt variant: `docs/prompts/vocab_term_extractor_with_degrees_diosc.md`
- Smoke run dir: `outputs/vocab_entries_v3/diosc_smoke_v3`
- Full run dir: `outputs/vocab_entries_v3/diosc_full_v3`
- Run QC summary: `<run_dir>/qc_summary.md` + `<run_dir>/qc_summary.json`

## Procedure
0. Apply recovered missing-text patch bundle (compact, text-first):
```bash
npm run diosc:text:apply
```

Outputs:
- `archive/docs/legacy_qc/diosc_missing_text_apply_report.md`
- `data-workbench/diosc.patched.csv`

This step supersedes direct editing of the verbose `diosc_alignment_review.csv` when the objective is to restore missing Greek/English text and known RV-cascade errors.

0.5 Apply targeted text-fixes (OCR cleanup, lemma heading fixes, translation de-dupes):
```bash
npm run diosc:textfix:apply
```

Outputs:
- `archive/docs/legacy_qc/diosc_text_fixes_apply_report.md`
- `data-workbench/diosc.build.csv`

0.75 Audit the build-ready CSV before extraction:
```bash
npm run diosc:build:audit
```

Outputs:
- `data-workbench/diosc_build_audit.md`
- `data-workbench/diosc_build_review.csv`

Use this step to review `lemma_gr`, `entry_gr`, `lemma_en`, `entry_en`, book/chapter consistency, and split integrity before rebuilding extraction inputs.

1. Extract alignment-suspect rows for review:
```bash
npm run diosc:align:extract
```

2. Edit `data-workbench/diosc_alignment_review.csv`:
- use `action` values `KEEP|REPLACE|DELETE|INSERT_AFTER`
- use `revised_*` columns for replacements/inserts
- keep `source_line_no` and `original_row_hash` unchanged for existing rows

3. Apply reviewed patch (non-destructive output):
```bash
npm run diosc:align:apply
```

4. Optional: if alignment review produced improvements you want to bake into the source CSV, apply them and promote as needed (keep a clean source-of-truth in `data-workbench/diosc.csv`).

5. Build Dioscorides entries CSV:
```bash
npm run diosc:entries:build
```

6. Validate Dioscorides entries CSV:
```bash
npm run diosc:entries:validate
```

7. Connectivity gate (1-entry probe):
```bash
npm run diosc:vocab:probe
```

8. Smoke run (25 entries):
```bash
npm run diosc:vocab:smoke
```

9. Smoke QC:
```bash
python scripts/qc_diosc_vocab_run.py --run-dir outputs/vocab_entries_v3/diosc_smoke_v3
```

If smoke is incomplete, resume:
```bash
npm run diosc:vocab:smoke:resume
```

10. Full run (resumable):
```bash
npm run diosc:vocab:run
```

11. Full-run QC:
```bash
npm run diosc:vocab:qc
```

## Resume/failure procedure
- If the 1-entry probe fails (model refresh errors or `codex exec` timeout), do not launch smoke/full runs; treat as infrastructure/runtime block and retry probe later.
- Re-run `npm run diosc:vocab:run` unchanged; it uses `--resume`.
- If rate-limit pressure is high, rerun with lower parallelism:
```bash
python scripts/vocab_multi_agent_pilot.py \
  --csv data-workbench/entries_diosc.csv \
  --id-col entry_id \
  --text-col greek \
  --prompt docs/prompts/vocab_term_extractor_with_degrees_diosc.md \
  --n 100000 \
  --outdir outputs/vocab_entries_v3 \
  --run-id diosc_full_v3 \
  --model gpt-5.2 \
  -c model_reasoning_effort=\"high\" \
  --parallel 6 \
  --timeout 900 \
  --retries 2 \
  --resume
```

## Acceptance checks
- `diosc_alignment_review.csv` is generated and editable with anchor/context flags.
- `diosc:align:apply` succeeds and writes `diosc_alignment_apply_report.md`.
- `entries_diosc.csv` validates cleanly.
- Run manifest job count equals valid result count (completeness).
- JSON outputs are parseable and `source_id`-consistent.
- QC does not require high degree frequency; low/nonexistent quantitative qualities are acceptable for Dioscorides.

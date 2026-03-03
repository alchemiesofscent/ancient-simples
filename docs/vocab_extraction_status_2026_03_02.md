# Vocab Extraction: Status + Accuracy Evaluation (2026-03-02)

This note documents:
- where the repo is with vocab extraction today,
- what was run and what exists on disk,
- the model-accuracy evaluation that was executed,
- what remains to do for the remaining corpus and for Dioscorides,
- where the relevant files live.

## 1) Where We Are (High-Level)

### Legacy (CSV-first) vs TEI-first
This repo currently contains both:
- the **legacy CSV-first MVP pipeline** (Next.js reads from `entries` and related tables), and
- the **TEI-first platform work** (migrations `005`/`006`, TEI indexer scripts, TEI doc configs).

For **vocab extraction**, we are operating in the **legacy CSV-first phase** for now: extraction runs against `data-workbench/entries.csv` and produces JSON results under `outputs/vocab_entries_v3/...`.

### What vocab extraction produces
The extraction prompt/schema yields JSON per entry with:
- `terms[]`: labeled candidate terms (SUBSTANCE, PART, PROCESS, etc.) with lemmata + normalized forms
- `qualities[]`: Galenic HOT/COLD/DRY/WET with degree/intensity/hedge + evidence

These are stored as:
- per-entry JSON results: `.../results/<SOURCE_ID>.json`
- consolidated JSONL: `.../results.jsonl`

Downstream import into the TEI-first schema is planned via `scripts/import_vocab_v3.py`, but full import requires a populated `config/entry_id_bridge.csv` (TEI doc+segment mappings), so import is deferred until TEI IDs are available.

## 2) The Current Vocab Extraction Run (v3)

### Core scripts
- Runner for a single entry:
  - `scripts/vocab_agent_runner.py`
  - Uses `codex exec --output-schema ... --output-last-message ...` to produce strict JSON.
- Orchestrator for many entries:
  - `scripts/vocab_multi_agent_pilot.py`
  - Reads a CSV (default: `data-workbench/entries.csv`) and writes prompts/results/errors into an output run directory.

### Primary outputs (already present)
- Main v3 run directory:
  - `outputs/vocab_entries_v3/entries_full_v3/`

Key contents:
- `outputs/vocab_entries_v3/entries_full_v3/manifest.json`
  - defines 2,135 jobs (one per entry), including output paths for results/errors.
- `outputs/vocab_entries_v3/entries_full_v3/results/`
  - per-entry results that exist so far.
- `outputs/vocab_entries_v3/entries_full_v3/errors/`
  - per-entry failure logs for attempts that did not produce a valid result.

### Completion status snapshot (current)
- As of **2026-03-03 18:25 UTC**:
- Total jobs in manifest: 2,135
- Completed results: 2,135
- Missing results: 0

Continuation verification/log:
- `outputs/vocab_entries_v3/entries_full_v3/continue_parallel10_20260302.log`
- `outputs/vocab_entries_v3/entries_full_v3/continue_parallel10_step2_escalated_20260303.log`
- `outputs/vocab_entries_v3/entries_full_v3/continue_residual_20260303_1722_utc.log`
- `outputs/vocab_entries_v3/entries_full_v3/continue_residual_20260303_1730_utc_escalated.log`
- `outputs/vocab_entries_v3/entries_full_v3/continue_residual_20260303_1758_utc_escalated.log`
- Run config used for residual completion: `gpt-5.2` + `model_reasoning_effort="high"` with `--parallel 10`, `--timeout 900`, `--retries 4`, `--usage-limit-max-waits 20`.
- Residual status:
  - first non-escalated residual pass failed due transport disconnects to Codex backend (`stream disconnected before completion ... /codex/responses`).
  - escalated residual pass recovered 16/17 missing IDs.
  - final remaining ID (`AET_LM-2.135`) repeatedly failed runner post-validation with:
    - `expected 'προςαγομενον', got 'προσαγομενον'`.
  - the final `AET_LM-2.135.json` was completed via deterministic normalization of the last `.json.tmp` payload using the repo normalizer, then validated with the same runner checks.

## 3) Model Accuracy Evaluation (Executed)

### Why this was needed
Runtime differences were not the priority; the goal was **accuracy** (precision/recall/labeling/linking/qualities).

### Candidate configurations tested
- `gpt-5.2` with `model_reasoning_effort="high"`
- `gpt-5.2` with `model_reasoning_effort="xhigh"`
- `gpt-5.3-codex` with `model_reasoning_effort="high"`

### Evaluation design
We implemented a blinded review process:
1) Freeze an eval set.
2) Generate model outputs for that set.
3) Build *blinded packets* per entry where model outputs are randomly permuted into Candidate A/B/C.
4) Score each packet with a rubric.
5) Aggregate scores and decide.

### Evaluation artifacts (files)
Root directory:
- `outputs/vocab_entries_v3/accuracy_eval/`

Key files:
- Log (all decisions + progress notes):
  - `outputs/vocab_entries_v3/accuracy_eval/LOG.md`
- Rubric (v1):
  - `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`
- Frozen eval set (30 entries, feature-first selection):
  - `outputs/vocab_entries_v3/accuracy_eval/eval_ids_30.txt`

### Practical constraint encountered
`xhigh` was too costly to complete on the full 30-entry set in a reasonable time window.

We therefore ran a focused 10-entry subset for 3-way comparison:
- `outputs/vocab_entries_v3/accuracy_eval/eval_ids_xhigh_10.txt`

### Model outputs produced
- Full 30-entry runs:
  - `outputs/vocab_entries_v3/accuracy_eval/models/gpt_5_2_high/`
  - `outputs/vocab_entries_v3/accuracy_eval/models/codex_5_3_high/`
- Focused 10-entry run:
  - `outputs/vocab_entries_v3/accuracy_eval/models/gpt_5_2_xhigh_subset10/`

### Blinded packet set used for scoring
- `outputs/vocab_entries_v3/accuracy_eval/subset10/packets/`
- Blinding key:
  - `outputs/vocab_entries_v3/accuracy_eval/subset10/blinding_key.json`

### Reviews + aggregation outputs
- Normalized reviews (JSONL):
  - `outputs/vocab_entries_v3/accuracy_eval/subset10/reviews_norm/reviews.jsonl`
- Summary:
  - `outputs/vocab_entries_v3/accuracy_eval/subset10/summary.md`
  - `outputs/vocab_entries_v3/accuracy_eval/subset10/summary.json`
- Decision memo:
  - `outputs/vocab_entries_v3/accuracy_eval/subset10/decision.md`

### Results (subset10)
See `outputs/vocab_entries_v3/accuracy_eval/subset10/summary.md`.

Averages (0–5) on the rubric dimensions:
- `gpt_5_2_high`
  - overall 4.69
  - linking 4.80
- `gpt_5_2_xhigh`
  - overall 4.67
  - qualities 5.00
- `codex_5_3_high`
  - overall 4.60
  - wins 13 (but also more rank-3 outcomes; higher variance)

### Recommendation
Default config for continuing extraction:
- **`gpt-5.2` + `model_reasoning_effort="high"`**

Reason:
- Best overall average in the subset10 blinded scoring.
- Strongest linking score.
- `xhigh` did not improve enough dimensions to justify the cost.

### Common error patterns observed (from reviewer notes)
- Over-extraction of generic `δύναμις` / `οὐσία` as `QUALITY_PROPERTY`.
- SUBSTANCE_PART inconsistencies:
  - Some outputs leave `lemma_gr` / `lemma_normalized` blank but set high `lemma_confidence`.
- Occasional normalization artifacts:
  - a few cases where “normalized” fields appear to retain diacritics.

These suggest prompt tightening and/or a post-validation pass may be worthwhile.

## 4) Code Changes Made During This Work

### Bug fix: codex_home path selection
`vocab_agent_runner.py` previously assumed `--out` was always under `outputs/*/<run_id>/results/`.
When `--out` was elsewhere (e.g. `/tmp/...`), it could attempt to write Codex HOME under `/_codex_home/...`.

Fix:
- `scripts/vocab_agent_runner.py`
  - now falls back to `outputs/_codex_home/<stem>/` when the expected layout does not apply.

### New evaluation tooling scripts
Added:
- `scripts/build_vocab_accuracy_eval_set.py`
  - builds deterministic eval sets using baseline v3 outputs to ensure feature coverage.
- `scripts/make_vocab_accuracy_packets.py`
  - builds blinded markdown packets + blinding key; supports restricting to an ids file.
- `scripts/assign_vocab_accuracy_reviews.py`
  - assigns packets to reviewers.
- `scripts/aggregate_vocab_accuracy_reviews.py`
  - aggregates reviewer JSONL into summary JSON + Markdown.

These scripts are pure local tooling and do not affect the runtime app.

## 5) What Still Needs To Be Done

### A) Finish extraction for the remaining legacy entries
Status: **completed** for the current legacy corpus in `data-workbench/entries.csv`.
- Manifest completeness is now 2,135/2,135 under:
  - `outputs/vocab_entries_v3/entries_full_v3/manifest.json`
- Recommended default for reruns/new legacy entries remains:
  - `gpt-5.2` + `model_reasoning_effort="high"`.

### B) Dioscorides extraction (before TEI)
Current extractor inputs:
- `scripts/vocab_multi_agent_pilot.py` defaults to `data-workbench/entries.csv`.

Dioscorides is not present in `data-workbench/entries.csv`.
To extract Dioscorides now (pre-TEI), we need to generate a Dioscorides “entries-like” CSV from:
- `data-workbench/diosc.csv`

Proposed approach:
- Create `data-workbench/entries_diosc.csv` with columns at least:
  - `entry_id` (e.g. `DIOSC_DMM-1.1` from book/chapter)
  - `source` = `DIOSC_DMM`
  - `ref` = `1.1`
  - `greek` from `entry_gr`
  - `translation` from `entry_en` (if desired)
  - page metadata fields where useful
- Then run `scripts/vocab_multi_agent_pilot.py --csv data-workbench/entries_diosc.csv --id-col entry_id --text-col greek ...`

Note:
- Import into TEI-first schema is still deferred until TEI segment IDs exist.

### C) Prompt tightening / post-validation
Status: **implemented**.
- Prompt updated to treat `δύναμις`/`οὐσία` as `QUALITY_PROPERTY` only when clearly pharmacodynamic in context.
- Runner post-validation added to:
  - enforce canonical normalization/diacritics-free `normalized` fields,
  - enforce `SUBSTANCE_PART` lemma-field consistency rules.

## 6) Relevant Paths (Quick Index)

Inputs
- `data-workbench/entries.csv`
- `data-workbench/diosc.csv`

Extraction tooling
- `scripts/vocab_agent_runner.py`
- `scripts/vocab_multi_agent_pilot.py`

Primary extraction outputs
- `outputs/vocab_entries_v3/entries_full_v3/`

Accuracy eval tooling
- `scripts/build_vocab_accuracy_eval_set.py`
- `scripts/make_vocab_accuracy_packets.py`
- `scripts/assign_vocab_accuracy_reviews.py`
- `scripts/aggregate_vocab_accuracy_reviews.py`

Accuracy eval outputs
- `outputs/vocab_entries_v3/accuracy_eval/LOG.md`
- `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`
- `outputs/vocab_entries_v3/accuracy_eval/eval_ids_30.txt`
- `outputs/vocab_entries_v3/accuracy_eval/eval_ids_xhigh_10.txt`
- `outputs/vocab_entries_v3/accuracy_eval/subset10/summary.md`
- `outputs/vocab_entries_v3/accuracy_eval/subset10/decision.md`

## 7) Dioscorides Execution Toolkit (added 2026-03-02)

To operationalize the Dioscorides pre-TEI extraction path, the repo now includes:

### Build/validation scripts
- `scripts/make_entries_diosc.py`
  - builds `data-workbench/entries_diosc.csv` from `data-workbench/diosc.csv`
  - writes `data-workbench/entries_diosc_qc.md`
- `scripts/validate_diosc_entries.py`
  - validates schema/normalization/invariants for `entries_diosc.csv`
- `scripts/extract_diosc_alignment_rows.py`
  - isolates RV/duplicate/cascade suspect rows from `diosc.csv`
  - writes editable `data-workbench/diosc_alignment_review.csv`
  - writes context report `data-workbench/diosc_alignment_context.md`
- `scripts/apply_diosc_alignment_patch.py`
  - applies edited review actions (`KEEP|REPLACE|DELETE|INSERT_AFTER`)
  - writes `data-workbench/diosc.patched.csv` and apply report

### Run-level QC
- `scripts/qc_diosc_vocab_run.py`
  - checks manifest completeness, parseability, source_id consistency, and anomaly metrics
  - writes `<run_dir>/qc_summary.md` and `<run_dir>/qc_summary.json`

### Prompt variant (Dioscorides-specific)
- `docs/prompts/vocab_term_extractor_with_degrees_diosc.md`
  - same output schema as v3 extractor
  - explicitly does **not** assume Galenic parallel degree methodology
  - degrees/intensity extracted only when explicit in text

### Runbook + QC notes
- `docs/dioscorides_vocab_plan_2026_03_02.md`
- `docs/dioscorides_vocab_qc_2026_03_02.md`

### NPM command wrappers
- `npm run diosc:entries:build`
- `npm run diosc:entries:validate`
- `npm run diosc:align:extract`
- `npm run diosc:align:apply`
- `npm run diosc:vocab:probe`
- `npm run diosc:vocab:smoke`
- `npm run diosc:vocab:smoke:resume`
- `npm run diosc:vocab:run`
- `npm run diosc:vocab:qc`

### Execution status (2026-03-02 update)
- `entries_diosc.csv` built and validated successfully (829 rows).
- Smoke run `diosc_smoke_v3` was attempted but failed 25/25 due Codex model-endpoint connectivity (`failed to refresh available models` / stream disconnected).
- Smoke QC artifacts were still generated in:
  - `outputs/vocab_entries_v3/diosc_smoke_v3/qc_summary.md`
  - `outputs/vocab_entries_v3/diosc_smoke_v3/qc_summary.json`
- Next step: re-run smoke after connectivity restoration, then run full resumable `diosc_full_v3`.

### Execution status (2026-03-03 update)
- Added one-entry connectivity probes before smoke/full runs:
  - `outputs/vocab_entries_v3/diosc_smoke_probe_20260302/`
  - `outputs/vocab_entries_v3/diosc_smoke_probe_20260302_escalated/`
- Added long-timeout probe:
  - `outputs/vocab_entries_v3/diosc_smoke_probe_900_escalated/` (1/1 succeeded)
- Initial probe results: 0/1 success in both short-timeout runs.
  - Sandbox probe failed with the same `codex/models` refresh stream-disconnect error.
  - Escalated-network probe reached runner execution but timed out after 180s waiting for `codex exec`.
- Conclusion: block is runtime model access/latency, not CSV/prompt/schema plumbing.
- Smoke rerun status (`diosc_smoke_v3` latest manifest `manifest_20260303_012830_utc.json`):
  - valid results: 2
  - missing: 23
  - QC: `outputs/vocab_entries_v3/diosc_smoke_v3/qc_summary.json`

## 8) Dioscorides Alignment Repair Workflow (added 2026-03-03)

Implemented a reviewer-driven correction flow before continuing extraction:
- extract suspect rows:
  - `npm run diosc:align:extract`
  - outputs:
    - `data-workbench/diosc_alignment_review.csv`
    - `data-workbench/diosc_alignment_context.md`
- edit review CSV:
  - set `action` column to `KEEP`, `REPLACE`, `DELETE`, or `INSERT_AFTER`
  - place corrected values in `revised_*` columns
- apply patch safely:
  - `npm run diosc:align:apply`
  - verifies row identity using `original_row_hash`
  - writes:
    - `data-workbench/diosc.patched.csv`
    - `data-workbench/diosc_alignment_apply_report.md`

Current extraction snapshot from latest generated review:
- extracted rows: 44
- anchor rows: 12
- high-signal groups include duplicate `2.178` rows and `190_RV`/`190` duplicate Greek pair.

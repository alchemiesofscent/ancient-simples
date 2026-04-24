---
status: active
owner: workflow
---

# Ancient Simples Live Workflow Board

This file is the canonical live tracker for the repo.

- Reference plan: `docs/new_simples/wbs_v1.md`
- Architecture reference: `docs/new_simples/tech_spec_v1.md`
- Session handoff log: `docs/new_simples/session_log.md`

## Operating Rules

- Start every session here, then read the latest entry in `docs/new_simples/session_log.md`.
- Keep exactly one leaf task in `Now`.
- `Resume Here` must match the `Now` task verbatim.
- Use these stream tags on every task: `[OPS]`, `[TEI]`, `[UI]`, `[LEGACY]`.
- Use these statuses only: `implemented`, `partial`, `blocked`, `not_started`.
- Done entries must include key before→after paths (e.g. `X` → `Y`), not just summaries. Record full details in `CHANGELOG.md`.
- When `Now`, `Next`, or `Done` changes, append a matching note to `docs/new_simples/session_log.md` in the same commit.

## Program Snapshot

- The repo currently contains two active streams:
  - TEI-first rewrite infrastructure: contracts, migrations, validation/indexing/import scaffolding.
  - Legacy CSV-first app and data pipeline: still the live UI path, with active Dioscorides patch/build/extraction work.
- The main implementation gap is not missing specs. It is drift between the TEI-first schema and the Python/Next.js code that is supposed to use it.
- The main operational risk is losing context between sessions. This board and the session log are the source of truth for resuming work.

## Milestone Status

| Milestone | Status | Evidence |
| --- | --- | --- |
| `M0` Contracts and textutils determinism | `partial` | Contracts exist (top-level `contracts/`); Python normalization/tokenizer tests pass (40 tests); Python parity fixture generated (`tests/fixtures/normalization_parity.json`); TS/SQL parity test runners still missing. |
| `M1` TEI-first schema deployed | `partial` | `005`/`006`/`007` migrations exist, but no fresh-project validation evidence is tracked here. |
| `M2` Indexer validated on test subset | `blocked` | TEI configs exist, but `tei/cmg` is absent and `scripts/index_tei.py` is out of sync with `005`. |
| `M3` Imports validated on test subset | `blocked` | `scripts/import_vocab_v3.py` still targets legacy tables and the bridge file is a stub. |
| `M4` Phase 2 gate passes | `blocked` | Test subset IDs and alignment seed data are placeholders/stubs; no facet-gate harness exists. |
| `M5` Core UI delivered | `partial` | Legacy `/entries` list/detail/editing exists; TEI-first citations and tables are not wired into the app. |
| `M6` Facet query UI delivered | `not_started` | No `/assertions/*` UI routes yet. |
| `M7` Lemma UI delivered | `not_started` | No `/lemmata` UI routes yet. |

## Current Blockers

- `BLK-TEI-01` `[TEI]` `blocked`: `tei/cmg` is not present in this checkout, so TEI validation and indexing cannot run end-to-end.
- `BLK-TEI-02` `[TEI]` `blocked`: `scripts/index_tei.py` writes fields and keys that do not match `supabase/migrations/005_tei_first_schema.sql`.
- `BLK-TEI-03` `[TEI]` `blocked`: `scripts/import_vocab_v3.py` still writes to legacy `lemma_forms`, `entry_lemma_forms`, and `assertions` instead of `tei_*`.
- `BLK-TEI-04` `[TEI]` `blocked`: `config/entry_id_bridge.csv` and `config/test_subset.txt` are scaffolding, not validated runtime inputs.
- `BLK-TEI-05` `[TEI]` `partial`: Python parity test and fixture generator exist (`tests/test_parity.py`); TS and SQL runners not yet wired.
- `BLK-UI-01` `[UI]` `blocked`: the Next.js app still reads legacy MVP tables instead of TEI-first tables.

## Now

- `TEI-INDEX-01` `[TEI]` Reconcile `scripts/index_tei.py` with the TEI-first schema in `005_tei_first_schema.sql`, including table names, payload shapes, key strategy, import-run fields, and stale/deactivation behavior. Status: `not_started`

## Next

- `TEI-IMPORT-01` `[TEI]` Reconcile `scripts/import_vocab_v3.py` with `tei_lemma_forms`, `tei_entry_lemma_forms`, and `tei_assertions`, then document any remaining bridge prerequisites. Status: `not_started`
- `TEI-SOURCE-01` `[TEI]` Restore or link the CMG TEI checkout at `tei/cmg`, then verify all three TEI doc config paths against real files. Status: `blocked`
- `TEI-TEST-01` `[TEI]` Add automated Python/TS/SQL normalization parity coverage and executable tests for the TEI rule fixtures under `tests/fixtures/tei_rules/`. Status: `partial` (Python parity corpus + fixture generator implemented in `tests/test_parity.py`; TS and SQL test runners still needed)
- `TEI-PHASE2-01` `[TEI]` Replace placeholder subset IDs, expand the bridge file from real indexed TEI entries, and turn the alignment seed into a real Phase 2 dataset. Status: `blocked`
- `UI-TEI-01` `[UI]` Port `/entries` list and detail from legacy `entries` to TEI-first tables and shared citation formatting. Status: `not_started`
- `LEGACY-DIOSC-01` `[LEGACY]` Keep the Dioscorides patch/build/extraction workflow current until it is either completed or folded into TEI-first ingest. Status: `partial`
- `TEI-SOURCE-ALIM-01` `[TEI]` Full GAL_ALIM ingestion deferred to TEI-first pipeline. Current CSV has 35 sparse entries (books 1-3). Requires: YAML config, CMG submodule, TEI XML. Status: `not_started`
- `TEI-SOURCE-PAUL-01` `[TEI]` PAUL_RM ingestion deferred to TEI-first pipeline. No entries in CSV; DB status `pending`. Requires: YAML config, CMG submodule, TEI XML. Status: `not_started`

## Done

- `OPS-TRACK-01` `[OPS]` Installed the canonical live board and append-only session log, and rebased the workflow on repo-truth rather than the original draft WBS. Status: `implemented`
- `OPS-CLARITY-01` `[OPS]` Refactored the repo surface so active docs, current workflow notes, and archived materials are structurally separated and indexed. Status: `implemented`
- `LEGACY-DIOSC-AUDIT-01` `[LEGACY]` Installed a deterministic `diosc.build.csv` audit workflow and review sheet so Dioscorides row correctness, numbering, and split integrity can be tracked explicitly before extraction. Status: `implemented`
- `OPS-RESTRUCTURE-01` `[OPS]` Greenfield-inspired repo restructure: `pyproject.toml` (proper Python packaging, editable install), consolidated normalization (all consumers delegate to `textutils.normalize`), re-normalized `entries.csv` v1.1, parity test suite (`tests/test_parity.py`), contracts elevated to top-level `contracts/`, structured `pipelines/` modules, sys.path hacking removed from 8+ files. Status: `implemented`
- `LEGACY-DATA-AUDIT-01` `[LEGACY]` Ref-sequence audit of `entries.csv`: fixed GAL_SMT-10.1.0→10.1, documented confirmed structural patterns (ORIB_CM depth variation, GAL_SMT book 6-8 continuous numbering, AET_LM ~N duplicates), deferred GAL_ALIM/PAUL_RM to TEI pipeline. Status: `implemented`
- `OPS-CLEANUP-01` `[OPS]` Repo cleanup for TEI-first focus: moved 13 legacy QC/analysis docs to `archive/`, wrote `PRODUCT_PLAN.md` (5-phase roadmap: org → extraction → import → search → NER), added 3-role autonomous architecture to `AGENTS.md`, updated all READMEs and doc maps. Status: `implemented`

## Resume Here

- `TEI-INDEX-01` `[TEI]` Reconcile `scripts/index_tei.py` with the TEI-first schema in `005_tei_first_schema.sql`, including table names, payload shapes, key strategy, import-run fields, and stale/deactivation behavior. Status: `not_started`

## Notes

- Keep `docs/new_simples/wbs_v1.md` unchanged as the plan-of-record reference. Do not use it as the live checklist.
- Keep legacy and TEI-first work on this single board so active work does not disappear during the rewrite.
- When a blocker is removed, move the task into `Next` or `Now` and record the change in `docs/new_simples/session_log.md`.

---
status: active
owner: workflow
---

# Ancient Simples Session Log

This file is the append-only handoff log for the repo.

## Entry Template

Use this template for every session entry:

### YYYY-MM-DD - actor

- Starting context:
- Tasks moved:
- Decisions:
- Transformations: (before → after for each structural change; also record in `CHANGELOG.md`)
- Evidence checked:
- Blockers:
- Exact next task:
- Resume note:

---

### 2026-03-12 - Codex

- Starting context: Rebased the repo against the TEI-first plan to determine actual implementation status and to install a durable resume workflow.
- Tasks moved: Added `OPS-TRACK-01` to `Done`. Set `TEI-INDEX-01` as the sole `Now` and `Resume Here` task in `docs/new_simples/new_wbs.md`.
- Decisions: Use one unified board for TEI-first and active legacy/Dioscorides work. Use a board plus append-only session log, not a generated dashboard, as the canonical workflow source of truth.
- Evidence checked: `docs/new_simples/wbs_v1.md`, `docs/new_simples/tech_spec_v1.md`, `docs/contracts/*`, `supabase/migrations/005_tei_first_schema.sql`, `supabase/migrations/006_tei_rls.sql`, `scripts/index_tei.py`, `scripts/import_vocab_v3.py`, `scripts/import_alignments.py`, `config/entry_id_bridge.csv`, `config/test_subset.txt`, `config/alignments/seed.jsonl`, `app/src/app/entries/page.tsx`, `app/src/app/entries/[entry_id]/page.tsx`, `docs/workflows/vocab_extraction/vocab_extraction_status_2026_03_02.md`, `docs/workflows/vocab_extraction/dioscorides_vocab_plan_2026_03_02.md`.
- Blockers: `tei/cmg` is absent in this checkout; `scripts/index_tei.py` and `scripts/import_vocab_v3.py` are out of sync with the TEI-first schema; parity and TEI-rule fixture tests are not enforced automatically.
- Exact next task: `TEI-INDEX-01` `[TEI]` Reconcile `scripts/index_tei.py` with the TEI-first schema in `005_tei_first_schema.sql`, including table names, payload shapes, key strategy, import-run fields, and stale/deactivation behavior.
- Resume note: Start by diffing `scripts/index_tei.py` against `005_tei_first_schema.sql` and `docs/contracts/tei_indexing_contract.md`, then patch the script before attempting any runtime validation.

### 2026-03-12 - Codex

- Starting context: Repo-clarity refactor to separate active docs and current workflow files from historical material and superseded output families.
- Tasks moved: Added `OPS-CLARITY-01` to `Done`. Kept `TEI-INDEX-01` as the active next implementation task.
- Decisions: Use process-named workflow folders, keep `WORKTREE_STATE.md` at repo root as an always-active fast resume file, keep `outputs/vocab_entries_v3/` as the only active output family, and archive older run families under `archive/outputs/`.
- Evidence checked: `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/new_simples/new_wbs.md`, `docs/workflows/vocab_extraction/*`, `data-workbench/simples_data_restructure_spec.md`, `scripts/vocab_multi_agent_pilot.py`, `package.json`, `supabase/migrations/001_init.sql`, and repo-wide path searches for moved docs and output roots.
- Blockers: Current data-workbench operational files remain intentionally mixed at top level because they are still in active use and already have local modifications in the worktree.
- Exact next task: `TEI-INDEX-01` `[TEI]` Reconcile `scripts/index_tei.py` with the TEI-first schema in `005_tei_first_schema.sql`, including table names, payload shapes, key strategy, import-run fields, and stale/deactivation behavior.
- Resume note: Use `WORKTREE_STATE.md` for the quick local snapshot, then return to the live board and continue `TEI-INDEX-01`.

### 2026-03-12 - Codex

- Starting context: Added the Dioscorides build-audit workflow after confirming `diosc.build.csv` is the current generated working file but still contains unresolved review-risk rows.
- Tasks moved: Added `LEGACY-DIOSC-AUDIT-01` to `Done`. Kept `TEI-INDEX-01` as the main repo-level `Now` task.
- Decisions: Treat `diosc.build.csv` as the canonical review surface, generate a full-row review sheet instead of a short anomaly list, and route all fixes back through the existing patch CSVs instead of editing generated CSVs directly.
- Evidence checked: `data-workbench/diosc.build.csv`, `data-workbench/diosc_missing_text_apply_report.md`, `data-workbench/diosc_text_fixes_apply_report.md`, `data-workbench/entries_diosc_qc.md`, `scripts/make_entries_diosc.py`, `scripts/validate_diosc_entries.py`, `docs/workflows/vocab_extraction/dioscorides_vocab_plan_2026_03_02.md`.
- Blockers: The build file still needs manual review of flagged rows before it should be treated as fully trusted for extraction-quality decisions.
- Exact next task: `TEI-INDEX-01` `[TEI]` Reconcile `scripts/index_tei.py` with the TEI-first schema in `005_tei_first_schema.sql`, including table names, payload shapes, key strategy, import-run fields, and stale/deactivation behavior.
- Resume note: For Dioscorides-specific continuation, start with `npm run diosc:build:audit`, review the high-priority rows in `data-workbench/diosc_build_review.csv`, and push fixes back into the patch CSVs before rebuilding `entries_diosc.csv`.

### 2026-04-06 - Claude

- Starting context: Picked up `LEGACY-DIOSC-01` vocab extraction closure. Smoke run (`diosc_smoke_v3`) at 2/25 valid results from March Codex-backend disconnects. Two high-priority build-audit rows outstanding (1.36, 4.151).
- Tasks moved: None (`LEGACY-DIOSC-01` stays `partial`).
- Decisions: All CSV fixes routed through `diosc_text_fixes_patch.csv`, never editing generated files directly. Confirmed `--parallel 3` is stable for Codex backend. Full run to use `--parallel 10` with fallback to 6.
- Transformations: Row 4.151 Greek `[151 ` prefix → cleaned; row 4.151 English `]49 %%...` footnote → removed. Both via new patches in `diosc_text_fixes_patch.csv`. Smoke run 2/25 → 17/25.
- Evidence checked: `entries_diosc.csv` row 1.36 corruption diagnosed as stale `diosc.build.csv` on disk (not a script bug) — regenerated clean. 15-check QA sweep over `entries_diosc.csv`: all passed (835 rows, 0 missing translations, normalization in sync, no stray non-Greek text). Row 4.151: `[151 ` Greek presentation prefix and `]49 %%...` English footnote fixed via two new patches in `diosc_text_fixes_patch.csv`. Smoke run resumed to 17/25 before context crash; runner stopped, no data lost.
- Blockers: Smoke run needs one more `--resume` pass (17/25 complete, 8 remaining). Full run blocked on smoke QC gate (`completeness_ok=true`, 25/25).
- Exact next task: Clear stale `.json.tmp` files, resume smoke with `--parallel 3 --timeout 900 --retries 2 --resume`, run QC, then launch full 835-entry extraction via `python3 scripts/vocab_multi_agent_pilot.py ... --run-id diosc_full_v3 --parallel 10`.
- Resume note: See plan file at `.claude/plans/cached-finding-flamingo.md` for the full checklist including smoke resume steps (S.1–S.5) and the exact full-run launch command.

### 2026-04-06 - Claude

- Starting context: Ref-sequence audit of `entries.csv`, then greenfield redesign thought exercise, then implementation of restructure changes.
- Tasks moved: Added `OPS-RESTRUCTURE-01` and `LEGACY-DATA-AUDIT-01` to `Done`. Updated `TEI-TEST-01` from `not_started` to `partial`. Updated `BLK-TEI-05` from `blocked` to `partial`. Updated `M0` milestone evidence.
- Decisions:
  - **Normalization single source of truth**: All Python consumers now delegate to `packages/textutils/normalize.py`. No local re-implementations. This fixed the iota subscript parity bug (v1.0 vs v1.1 drift between `make_entries.py` and `validate_data.py`).
  - **Proper Python packaging**: Created `pyproject.toml` with editable install (`pip install -e ".[dev]"`), replacing sys.path hacking in 8+ files.
  - **Contracts elevated**: Moved `docs/contracts/` → top-level `contracts/`. Updated all references in CLAUDE.md, AGENTS.md, migration 005.
  - **Structured pipelines**: Created `pipelines/` module with `validate/__main__.py` (wraps existing scripts). `tei_index/`, `vocab_extract/`, `alignment/` are placeholder packages for future migration.
  - **GAL_ALIM and PAUL_RM**: Deferred to TEI-first pipeline. Not worth CSV extraction effort.
  - **entries.csv fixes**: GAL_SMT-10.1.0 → GAL_SMT-10.1 (entry_id + ref). Re-normalized `greek_normalized` column (1,143 of 2,135 rows updated to v1.1). Confirmed structural patterns (ORIB_CM mixed depth, GAL_SMT continuous book 6-8 numbering, AET_LM ~N duplicates) are correct per source texts.
  - **Greenfield plan**: Wrote a full architectural redesign document (`.claude/plans/validated-leaping-kite.md`) as a north-star reference. The five practical gaps identified: kill CSV pipeline, fix normalization parity, package Python, move outputs out of git, add frontend tests.
- Transformations: See `CHANGELOG.md` entries for 2026-04-06. Key: `make_entries.py` local normalize (v1.0) → delegates to textutils (v1.1); `validate_data.py` local normalize → import from textutils; 8 scripts sys.path hacking → removed (pyproject.toml editable install); no pyproject.toml → created; `entries.csv` GAL_SMT-10.1.0 → GAL_SMT-10.1; `entries.csv` greek_normalized column v1.0 → v1.1 (1,143 rows); `docs/contracts/` → top-level `contracts/`; no pipelines/ → `pipelines/{validate,tei_index,vocab_extract,alignment}/`; no parity tests → `tests/test_parity.py` (30+ corpus, 5 tests); test count 35 → 40.
- Evidence checked: `entries.csv` (all 2,135 rows), `entries_qc.md`, `make_entries.py`, `workbook_utils.py`, `validate_data.py`, `index_tei.py`, `import_vocab_v3.py`, all scripts for sys.path usage, `pyproject.toml`, `tests/test_parity.py` (30+ parity corpus entries, all passing), `npm run textutils:test` (40 tests pass), `data-workbench/entries_refs_audit.md` (generated by new `scripts/audit_entries_refs.py`).
- Blockers: Pre-existing GAL_SMT-6.prooimion normalization mismatch in `validate_data.py` (not caused by this session's changes). TS and SQL parity test runners not yet implemented.
- Exact next task: `TEI-INDEX-01` `[TEI]` Reconcile `scripts/index_tei.py` with the TEI-first schema in `005_tei_first_schema.sql`.
- Resume note: All restructure work is unstaged. Run `git status` to see the full changeset. The greenfield plan at `.claude/plans/validated-leaping-kite.md` serves as the architectural north star — the five practical gaps listed at its end are the roadmap.

### 2026-04-06 - Claude

- Starting context: User requested repo cleanup for TEI-first focus, then pivoted to a broader product plan centered on the extraction → search → NER pipeline.
- Tasks moved: Added `OPS-CLEANUP-01` to `Done`.
- Decisions:
  - **No deletions**: "Clean" means organize and catalog, not delete. Legacy docs move to `archive/`, nothing is removed from git.
  - **Extraction data is critical**: `outputs/vocab_entries_v3/` (3.2GB, 27,707 terms, 2,894 qualities) is the foundation for search, computation, and NER training. Must not be deleted or treated as disposable.
  - **5-phase product plan**: Wrote `PRODUCT_PLAN.md` documenting the full pipeline: (1) repo org, (2) complete Dioscorides extraction, (3) import results → DB with legacy IDs, (4) build search/computation UI, (5) TEI transition + NER.
  - **3-role autonomous architecture**: Added Planner/Implementer/QC roles to `AGENTS.md` for structured autonomous work.
  - **Import strategy**: Import extraction results linked to legacy `entries` table first (no bridge CSV needed), then remap to TEI IDs when TEI indexing is ready. Unblocks search immediately.
- Transformations: See `CHANGELOG.md` entries for 2026-04-06 "Repo cleanup" and "Product plan". Key: 10 QC .md files `data-workbench/` → `archive/docs/legacy_qc/`; 2 analysis .md files `docs/` → `archive/docs/analysis/`; `WORKTREE_STATE.md` → `archive/docs/misc/`; no PRODUCT_PLAN.md → created (5-phase roadmap); AGENTS.md no work roles → 3-role autonomous architecture; `outputs/README.md` minimal → rewritten with data-flow diagram; `README.md` start-here WORKTREE_STATE → PRODUCT_PLAN; `docs/README.md` "Historical" section → "See also" with contracts + plan links.
- Evidence checked: `outputs/vocab_entries_v3/entries_full_v3/` (2,135 result JSONs, 100% complete), `data-workbench/entries.csv` (2,135 entries), `data-workbench/entries_diosc.csv` (835 entries), `scripts/import_vocab_v3.py` (bridge CSV is a stub with 3/2,135 mappings), app routes (minimal MVP, legacy tables only), all moved files verified in archive locations.
- Blockers: Dioscorides extraction at 8.5% (71/835). Bridge CSV is a stub. App has no faceted search, no assertion UI, no lemma browser.
- Exact next task: Phase 2 — complete Dioscorides extraction (resume smoke run, then full 835-entry run).
- Resume note: `PRODUCT_PLAN.md` is the roadmap. All Phase 1 changes are unstaged. Phase 2 requires Codex model access for `vocab_multi_agent_pilot.py`.

### 2026-04-25 - Codex

- Starting context: User chose the outputs-to-search path over resuming TEI indexer first. Live inspection found legacy extraction complete by JSON count, legacy `results.jsonl` empty, Dioscorides full extraction absent, and direct script commands failing on `textutils` imports outside pytest.
- Tasks moved: Added `LEGACY-VOCAB-AUTO-01` to `Done`. Set `LEGACY-DIOSC-FULL-01` as the sole `Now` and `Resume Here` task. Moved `TEI-INDEX-01` back to `Next`.
- Decisions: Keep TEI import bridge-gated, but unblock search through legacy-ID extraction tables keyed to `entries.entry_id`. Use an explicit alias CSV for v3 extraction IDs that predate ref cleanup rather than burying remaps in code.
- Transformations: `outputs/vocab_entries_v3/entries_full_v3/results/*.json` → fresh `outputs/vocab_entries_v3/entries_full_v3/results.jsonl`; no repo vocab controller → `python -m pipelines.vocab_extract {status,consolidate,complete}`; no legacy extraction tables → `supabase/migrations/008_legacy_vocab_import.sql`; TEI-only importer → `scripts/import_vocab_v3.py --target legacy|tei`; implicit stale result IDs → `config/vocab_entry_id_aliases.csv`; `scripts/import_supabase.py` entries-only import → appends `entries_diosc.csv` by default; `/entries` prefix-only UI → source/quality/degree/substance filters plus extraction detail panels.
- Evidence checked: `git status`, `PRODUCT_PLAN.md`, `docs/new_simples/new_wbs.md`, `outputs/vocab_entries_v3/*`, `scripts/vocab_multi_agent_pilot.py`, `scripts/qc_diosc_vocab_run.py`, `scripts/import_vocab_v3.py`, `package.json`, `app/src/app/entries/*`, `supabase/migrations/`.
- Blockers: `outputs/vocab_entries_v3/diosc_full_v3/` is still absent; full Dioscorides extraction requires Codex model access and was not launched in this implementation pass.
- Exact next task: `LEGACY-DIOSC-FULL-01` `[LEGACY]` Run/resume the full Dioscorides vocab extraction with `npm run diosc:vocab:run`, then run `npm run diosc:vocab:qc`, `npm run vocab:consolidate`, and legacy import dry-runs.
- Resume note: Start with `npm run vocab:status`; legacy output is consolidated and imports cleanly in dry-run with 2,135 entries. Then run the full Dioscorides extraction command and re-run `npm run vocab:complete` if interrupted.

### 2026-04-27 - Codex

- Starting context: User requested implementation of the Paul `vocab_entries_v3` plan for `data-workbench/paul.csv`; live inspection had already shown Paul CSV is structurally prepared enough for Greek-only extraction (680 rows, stable row IDs, no TEI/OCR corruption, blank translations expected).
- Tasks moved: Added `LEGACY-PAUL-PIPELINE-01` to `Done`. Set `LEGACY-PAUL-FULL-01` as the sole `Now` and `Resume Here` task. Replaced the old Dioscorides full blocker with a Paul full-extraction blocker because Dioscorides full output is now present and complete by controller status.
- Decisions: Treat Paul as source code `PAUL_AEG` in the legacy-ID vocab path. Keep blank `entry_en` translations as warnings, not errors. Use a Paul-specific prompt that expects explicit `τάξις`/`ἀπόστασις` degree language. Keep generic QC source-aware rather than preserving Dioscorides-only degree assumptions.
- Transformations: `data-workbench/paul.csv` → `data-workbench/entries_paul.csv` via `scripts/make_entries_paul.py`; no Paul validator → `scripts/validate_paul_entries.py`; Dioscorides-only QC → `scripts/qc_vocab_run.py` with `generic|dioscorides|paul` profiles; `package.json` Dioscorides-only scripts → added `paul:*` scripts; `pipelines/vocab_extract/__main__.py` legacy+Dioscorides status → legacy+Dioscorides+Paul status/consolidation/complete; `scripts/import_supabase.py` entries+entries_diosc → entries+entries_diosc+entries_paul; `scripts/import_vocab_v3.py` dry-run legacy ID check → includes `entries_paul.csv`; DB source seed without Paul → `supabase/migrations/009_paul_source.sql`; `/entries` source filter without Paul → includes `PAUL_AEG`; no Paul prompt → `docs/prompts/vocab_term_extractor_with_degrees_paul.md`; `outputs/README.md` legacy+Dioscorides flow → includes Paul flow.
- Evidence checked: `npm run paul:entries:build` wrote 680 rows; `npm run paul:entries:validate` passed with 680 expected blank-translation warnings; `/usr/local/bin/python -m pytest tests/test_vocab_pipeline.py -q` passed (5 tests); `npm run vocab:status` reports legacy complete, Dioscorides complete, Paul full partial (564/680), Paul smoke complete. Paul smoke QC: 5/5 valid, 25 qualities, 4 explicit-degree qualities, 0 alerts.
- Blockers: Full Paul extraction is incomplete at 564/680 result JSONs by status. The latest approved resume stopped at the external Codex usage limit; remaining failed entries are usage-limit failures starting with `PAUL_AEG-7.3.565`, not schema/data failures. The reported reset was 4:29 AM. The repo `.venv` lacks `pytest`; use `/usr/local/bin/python -m pytest ...` or install dev deps.
- Exact next task: `LEGACY-PAUL-FULL-01` `[LEGACY]` Resume the full Paul vocab extraction with `npm run paul:vocab:run`, then run `npm run paul:vocab:qc`, `npm run vocab:consolidate`, `npm run vocab:status`, and legacy import dry-runs.
- Resume note: Current resume point is `outputs/vocab_entries_v3/paul_full_v3/` with 564 result JSON files by status, 0 invalid JSON files, and 0 tmp files. The resume command is `npm run paul:vocab:run -- --parallel 5`; it will skip existing JSON results. After completion run `npm run paul:vocab:qc`, `npm run vocab:consolidate`, `npm run vocab:status`, and `npm run vocab:import -- --target legacy --results outputs/vocab_entries_v3/paul_full_v3/results.jsonl --dry-run`.

### 2026-04-27 - Codex

- Starting context: User asked for a frontend over `vocab_entries_v3` that can search by every extracted category while keeping simples as the primary comparison target.
- Tasks moved: Added `UI-SIMPLES-STATIC-01` to `Done`. Updated `M6` and `M7` to `partial` because the new route is static-output-backed, not DB/TEI-backed.
- Decisions: Build v1 as static JSON instead of waiting for Supabase import. Treat `SUBSTANCE` and `SUBSTANCE_PART` as result simples; treat condition, administration, preparation, process, place, quality property, tool/container, part, application site, and quality assertions as searchable facets. Include complete full-output run directories present in the checkout: legacy, Dioscorides, and Paul.
- Transformations: no static vocab viewer -> `scripts/build_vocab_frontend_index.py`, `app/public/vocab/vocab-index.json`, `app/src/app/simples/`, and `app/src/lib/vocab/`; app header entries-only nav -> includes `/simples`; no rebuild command -> `npm run vocab:frontend-index`.
- Evidence checked: `npm run vocab:frontend-index` wrote 4,559 simples from 3,243 result entries after the Paul checkpoint refresh; `python3 -m py_compile scripts/build_vocab_frontend_index.py tests/test_vocab_pipeline.py` passed; `/usr/local/bin/python -m pytest tests/test_vocab_pipeline.py -q` passed (5 tests); `npm run app:lint` passed; `npm run app:build` passed.
- Blockers: The `/simples` viewer loads a large static JSON index (~63 MB uncompressed); this is acceptable for local/research use but should become paged/server-backed before public deployment.
- Exact next task: Keep `LEGACY-PAUL-FULL-01` as the active pipeline resume task unless the next session is explicitly UI-focused.
- Resume note: To refresh the static viewer after more extraction output lands, run `npm run vocab:frontend-index`, then `npm run app:build`.

### 2026-04-28 - Codex

- Starting context: User asked to continue the Paul pipeline until complete from the 564/680 checkpoint left by the usage-limit pause.
- Tasks moved: Added `LEGACY-PAUL-FULL-01` to `Done`. Set `LEGACY-VOCAB-IMPORT-01` as the sole `Now` and `Resume Here` task. Removed the legacy blocker for Paul extraction.
- Decisions: Preserve the same `outputs/vocab_entries_v3/paul_full_v3/` run directory and resume instead of starting a new run. Delete stale usage-limit error logs only after every affected entry had a valid result JSON. Rerun QC against the original 680-job manifest rather than the final 116-job resume manifest.
- Transformations: `outputs/vocab_entries_v3/paul_full_v3/results/*.json` 564/680 -> 680/680; stale usage-limit `errors/*.txt` -> removed after successful extraction; partial resume `results.jsonl` (116 lines) -> consolidated full `results.jsonl` (680 lines); final-resume QC -> full-manifest QC.
- Evidence checked: `npm run paul:vocab:run -- --parallel 5` completed final 116/116 entries; `npm run vocab:consolidate` produced 680 valid Paul results and 0 invalid; Paul QC with `manifest_20260427_200412_utc.json` passed completeness (680 expected, 680 valid, 0 missing, 0 invalid, 0 source mismatches, 0 error files); `npm run vocab:status` reported no blockers; `npm run vocab:import -- --target legacy --results outputs/vocab_entries_v3/paul_full_v3/results.jsonl --dry-run` processed 680 entries and would upsert 1,126 lemma forms, 1,658 entry-form links, and 742 quality assertions.
- Blockers: Live DB import not run. Paul QC still raises a content-review alert for 13 generic `δύναμις`/`οὐσία` QUALITY_PROPERTY terms.
- Exact next task: `LEGACY-VOCAB-IMPORT-01` `[LEGACY]` Apply migrations `008`/`009`, run `npm run vocab:import -- --target legacy` for legacy, Dioscorides, and Paul JSONL outputs, then confirm app filters read imported rows.
- Resume note: Pipeline outputs are complete and consolidated. Before live import, ensure migrations `008_legacy_vocab_import.sql` and `009_paul_source.sql` are applied, then import `entries_full_v3`, `diosc_full_v3`, and `paul_full_v3` JSONL outputs.

### 2026-05-04 - Codex

- Starting context: User clarified the long-term goal for a complete cross-corpus simples register using the standard identity chain `ancient term -> scholarly identification(s) -> physical substance -> botanical/material source`, then asked to implement the durable workflow while keeping future Oribasius 1-14 and Aetius 3-4 additions open.
- Tasks moved: Added `LEGACY-SIMPLES-REGISTRY-01` to `Done`. Added `LEGACY-SIMPLES-REVIEW-01` to `Next`. Left board `Now`/`Resume Here` on `LEGACY-VOCAB-IMPORT-01`.
- Decisions: Keep v0 at the ancient-term layer; do not auto-merge normalized terms into final substances. Use a manifest-driven run list so future Oribasius 1-14 and Aetius 3-4 result runs can be added without schema changes. Treat deterministic name extraction as candidate generation only; LLM/human review remains required before synonym claims are accepted. Keep preparations out of this first implementation except as a later lightweight relation layer.
- Transformations: no simples registry manifest -> `config/simples_registry_runs.json`; no durable workflow note -> `docs/new_simples/simples_registry_workflow.md`; no registry workbench -> `data-workbench/simples/README.md` plus generated registry/candidate artifacts; no registry generator -> `scripts/build_simples_registry.py`; no name-relation candidate generator -> `scripts/build_simple_name_relation_candidates.py`; no npm commands -> `simples:registry` and `simples:name-candidates`; test coverage expanded in `tests/test_vocab_pipeline.py`.
- Evidence checked: `npm run simples:registry` wrote 4,861 draft term keys, 18,807 occurrences, and 6,057 forms from `entries_full_v3`, `diosc_full_v3`, and `paul_full_v3`; `npm run simples:name-candidates` wrote 681 pending candidate rows and 100 review packets (20 sampled entries per author group, 80 trigger samples, 20 controls); `/usr/local/bin/python -m pytest tests/test_vocab_pipeline.py -q` passed 7 tests; `python -m py_compile scripts/build_simples_registry.py scripts/build_simple_name_relation_candidates.py tests/test_vocab_pipeline.py` passed.
- Blockers: `simple_name_relations_pilot.csv` is intentionally pending LLM/human review; no synonym relation is accepted yet. Candidate generation is high-recall and will include false positives by design.
- Exact next task for this stream: `LEGACY-SIMPLES-REVIEW-01` `[LEGACY]` Review `data-workbench/simples/simple_name_relation_review_packets.jsonl` against `simple_name_relation_candidates.csv`, classify/reject/add name relations, and write accepted rows to `simple_name_relations_pilot.csv`.
- Resume note: Start with `data-workbench/simples/simple_name_relations_pilot_report.md`, then review packets in `simple_name_relation_review_packets.jsonl`. Board-wide `Resume Here` remains the live DB import task unless the next session is explicitly simples-focused.

### 2026-05-04 - Codex

- Starting context: User asked for a way to visualize the registry and list all named simples/substances with user-friendly data. Current `/simples` route loaded the full evidence index and did not expose the new v0 registry artifacts directly.
- Tasks moved: Added `UI-SIMPLES-REGISTRY-01` to `Done`. Left `LEGACY-SIMPLES-REVIEW-01` in `Next` and left board `Now`/`Resume Here` on `LEGACY-VOCAB-IMPORT-01`.
- Decisions: Keep `/simples` as the main app surface. Make `Registry` the default tab for research review and lazy-load the heavier `Evidence` view only when opened. Keep labels clear that rows are draft ancient terms, not final physical substances.
- Transformations: no compact public registry index -> `app/public/simples/registry-index.json`; no public-index generator -> `scripts/build_simples_public_index.py`; no command -> `npm run simples:public-index`; `/simples` evidence-only client -> Registry/Evidence tabbed client with named-simple filters, detail panel, quality summary, review status, source/author coverage, and filtered CSV/JSON export.
- Evidence checked: `npm run simples:public-index` wrote 4,861 registry terms into a 5.2 MB browser index; `/usr/local/bin/python -m pytest tests/test_vocab_pipeline.py -q` passed 8 tests; `npm run app:lint` passed; `npm run app:build` passed.
- Blockers: The registry view still reflects pending name-relation review state; accepted synonym/variant decisions require `LEGACY-SIMPLES-REVIEW-01`.
- Exact next task for this stream: `LEGACY-SIMPLES-REVIEW-01` `[LEGACY]` review the candidate packets and update `simple_name_relations_pilot.csv`.
- Resume note: Rebuild sequence after review edits is `npm run simples:name-candidates` only if candidate generation changes, otherwise update pilot rows and run `npm run simples:public-index`.

### 2026-05-04 - Codex

- Starting context: User asked whether the simples app could be usable without login/magic link and asked for the color scheme to be more visible.
- Tasks moved: Added `UI-SIMPLES-PUBLIC-01` to `Done`. Left `Now`/`Resume Here` on `LEGACY-VOCAB-IMPORT-01` because DB import remains the board-wide operational task.
- Decisions: Treat `/simples` as a public, read-only research browser because it is backed by generated static JSON. Keep login for editor/database-backed workflows such as `/entries`. Make auth optional in the global layout so public pages do not depend on configured Supabase credentials.
- Transformations: `/simples` protected by middleware -> public `/simples`; generated `/simples` and `/vocab` JSON asset paths protected by middleware -> public static assets; `/` redirect to `/entries` -> `/` redirect to `/simples`; header `Sign in` -> `Editor sign in`; low-contrast zinc shell and controls -> slate/indigo shell, stronger borders, selected row color, source chips, and active tab states.
- Evidence checked: `npm run app:lint`; `npm run app:build`; HTTP checks for `/`, `/simples`, `/entries`, `/simples/registry-index.json`, and `/vocab/vocab-index.json` against a local built Next server.
- Blockers: `/entries` remains intentionally login-gated until/unless the editor workflow is split from public read-only entry browsing.
- Exact next task for this stream: `LEGACY-SIMPLES-REVIEW-01` `[LEGACY]` review candidate name-relation packets and update `simple_name_relations_pilot.csv`.
- Resume note: Public browsing should start at `/simples`; editor/database pages still use magic-link auth.

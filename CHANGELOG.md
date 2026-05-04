# Changelog

### 2026-05-04 — Simples registry browser view

**Why**: The project needed a user-friendly way to inspect named simples and their source coverage without loading the full evidence explorer by default.

| Before | After | Why |
|--------|-------|-----|
| `/simples` loaded only the 66 MB evidence index | `/simples` defaults to a compact Registry view backed by `app/public/simples/registry-index.json` | Make named-simple review faster and clearer |
| No compact public registry index | `scripts/build_simples_public_index.py` and `npm run simples:public-index` | Merge term, form, occurrence, quality-summary, and review-status data for the browser |
| Registry and evidence were not separated | `/simples` has `Registry` and `Evidence` tabs; Evidence lazy-loads the larger vocab index | Keep detailed evidence available without slowing first load |
| No export from the named-simple list | Registry view exports the filtered rows as CSV or JSON | Support research review and ad hoc analysis |

### 2026-05-04 — Simples registry workflow

**Why**: The project needs a durable, reviewable path from `vocab_entries_v3` extraction output to a complete cross-corpus simples registry, while staying open to future Oribasius 1-14 and Aetius 3-4 additions.

| Before | After | Why |
|--------|-------|-----|
| No manifest for complete runs feeding a simples registry | `config/simples_registry_runs.json` declares included runs, entry CSVs, author groups, and future corpus slots | Add future result runs without changing schemas |
| No durable simples workflow note | `docs/new_simples/simples_registry_workflow.md` | Record long-term identity model, artifacts, review stages, and commit discipline |
| No registry workbench | `data-workbench/simples/README.md` plus generated CSV/JSON/MD artifacts | Keep outputs reviewable and reproducible |
| No v0 ancient-term registry generator | `scripts/build_simples_registry.py` and `npm run simples:registry` | Build draft term, occurrence, and form tables from complete `vocab_entries_v3` runs |
| No name-relation pilot packet generator | `scripts/build_simple_name_relation_candidates.py` and `npm run simples:name-candidates` | Generate high-recall synonym/name candidates plus controls for LLM/human review |
| No tests for registry/candidate workflow | `tests/test_vocab_pipeline.py` covers run/source metadata and trigger/control sampling | Prevent schema drift and preserve future-corpus extensibility |

Curated record of structural transformations. Not a git log — tracks *what became what* and *why*.

---

### 2026-04-27 — Static simples vocab viewer

**Why**: The vocab v3 outputs now contain enough cross-corpus extraction data to support local search and comparison before Supabase/TEI import is complete.

| Before | After | Why |
|--------|-------|-----|
| No generated browser index for `outputs/vocab_entries_v3` | `scripts/build_vocab_frontend_index.py` emits `app/public/vocab/vocab-index.json` | Make completed extraction output browsable without DB import |
| No route for lemma-centered simple comparison | `app/src/app/simples/` static viewer route | Search, display, and compare normalized simples |
| Search UI did not expose every extracted label | `/simples` filters condition, administration, preparation, process, place, quality property, tool/container, part, application site, source, quality axis/degree, confidence, and cross-corpus coverage | Let all gathered extraction categories drive research queries |
| No shared frontend vocab types/helpers | `app/src/lib/vocab/types.ts` and `app/src/lib/vocab/filter.ts` | Keep the generated index contract and client filtering explicit |
| App header only linked the entries workflow | Header includes `/simples` | Surface the new research view |
| No rebuild command for the static viewer index | `npm run vocab:frontend-index` | Repeatable local refresh after extraction runs |

---

### 2026-04-06 — Normalization consolidation + Python packaging

**Why**: Three independent implementations of Greek normalization had drifted (v1.0 vs v1.1 iota subscript handling). Scripts used `sys.path` hacking instead of proper packaging.

| Before | After | Why |
|--------|-------|-----|
| `data-workbench/make_entries.py` had local `normalize_greek()` preserving iota subscript (v1.0) | Delegates to `from textutils.normalize import normalize` (v1.1, strips iota subscript) | Single source of truth for normalization |
| `data-workbench/workbook_utils.py` had local `normalize_greek_for_match()` (v1.0) | Delegates to `from textutils.normalize import normalize` (v1.1) | Same |
| `scripts/validate_data.py` had local `normalize_greek_for_match()` (v1.1 but separate copy) | `from textutils.normalize import normalize as normalize_greek_for_match` | Eliminate duplicate implementation |
| 8 scripts had `sys.path.insert(0, str(REPO_ROOT / "packages"))` | Lines removed; package available via `pip install -e ".[dev]"` | Proper Python packaging |
| No `pyproject.toml` existed | Created with `[project]` (name, version, deps), `[project.optional-dependencies]` (dev, workbench), `[tool.setuptools.packages.find]`, `[tool.pytest.ini_options]` | Enable editable install, declare lxml/pytest/pandas as real deps |
| `tests/test_normalize.py` imported `from packages.textutils.normalize` | `from textutils.normalize import normalize` | Package installed via pip now |
| `tests/test_tokenize.py` imported via `packages.textutils` path | `from textutils.tokenize import tokenize` | Same |
| `tests/test_determinism.py` imported via `packages.textutils` path | `from textutils.normalize import normalize` | Same |
| `scripts/index_tei.py` had `sys.path.insert` for packages dir | Removed packages path (kept scripts path for `supabase_rest`) | textutils available via pip |
| `scripts/import_vocab_v3.py` had `sys.path.insert` for packages dir | Same cleanup as index_tei.py | Same |
| `scripts/make_entries_diosc.py`, `scripts/qc_diosc_vocab_run.py`, `scripts/validate_diosc_entries.py`, `scripts/vocab_agent_runner.py` each had `_PACKAGES_PATH` sys.path blocks | Blocks removed from all 4 | Same |
| `package.json` `textutils:test` was `cd packages/textutils && python -m pytest tests/ -v` | Changed to `python -m pytest tests/ -v` | Tests run from repo root with proper packaging |

---

### 2026-04-06 — entries.csv data fixes

**Why**: Ref-sequence audit found one incorrect entry ID and 1,143 rows with stale v1.0 normalized values.

| Before | After | Why |
|--------|-------|-----|
| `entries.csv` row with `entry_id=GAL_SMT-10.1.0`, `ref=10.1.0` | `entry_id=GAL_SMT-10.1`, `ref=10.1` | Chapter 10.1 has no third-level sections; `.0` was incorrect |
| `entries.csv` `greek_normalized` column had v1.0 values (iota subscript preserved) in 1,143 of 2,135 rows | Re-normalized all rows with v1.1 (iota subscript stripped) | Parity with canonical `textutils.normalize` |

---

### 2026-04-06 — Parity tests + pipelines structure

**Why**: No automated check existed to catch normalization drift across Python/TS/SQL. Scripts lived in a flat `scripts/` directory with no module structure.

| Before | After | Why |
|--------|-------|-----|
| No cross-language normalization test existed | `tests/test_parity.py` (30+ corpus entries, 5 tests) + `tests/fixtures/normalization_parity.json` | Catch drift between Python, TS, and SQL normalization |
| No `pipelines/` directory | `pipelines/__init__.py`, `pipelines/validate/__main__.py` (wraps existing scripts), `pipelines/tei_index/__init__.py`, `pipelines/vocab_extract/__init__.py`, `pipelines/alignment/__init__.py` | Structured module pattern; run via `python -m pipelines.validate` |
| Test count was 35 | Now 40 (5 new parity tests) | — |

---

### 2026-04-06 — Contracts elevated to top-level

**Why**: Contracts are the project's most important architectural asset; burying them under `docs/` undersold their role.

| Before | After | Why |
|--------|-------|-----|
| `docs/contracts/alignment_interchange_spec.md` | `contracts/alignment_interchange_spec.md` | Top-level visibility |
| `docs/contracts/anchoring_contract.md` | `contracts/anchoring_contract.md` | Same |
| `docs/contracts/citation_contract.md` | `contracts/citation_contract.md` | Same |
| `docs/contracts/export_contract.md` | `contracts/export_contract.md` | Same |
| `docs/contracts/normalization_contract.md` | `contracts/normalization_contract.md` | Same |
| `docs/contracts/tei_indexing_contract.md` | `contracts/tei_indexing_contract.md` | Same |
| `supabase/migrations/005` binding comment referenced `docs/contracts/` | Updated to `contracts/` | Reflect new path |
| `CLAUDE.md` referenced `docs/contracts/normalization_contract.md` | Updated to `contracts/normalization_contract.md` | Same |
| `AGENTS.md` referenced `docs/contracts/` | Updated to `contracts/` | Same |

---

### 2026-04-27 — Paul vocab pipeline

**Why**: `data-workbench/paul.csv` is prepared enough for the `vocab_entries_v3` workflow, but it needed a first-class bridge into the same autonomous build, QC, consolidation, and import path as legacy and Dioscorides.

| Before | After | Why |
|--------|-------|-----|
| `data-workbench/paul.csv` had no generated legacy entry surface | `scripts/make_entries_paul.py` emits `data-workbench/entries_paul.csv` plus QC | Give the LLM runner stable `PAUL_AEG-*` entry IDs and normalized Greek text |
| No Paul entry validator | `scripts/validate_paul_entries.py` | Catch numbering, normalization, page, and source drift before extraction |
| Dioscorides-only vocab QC command | `scripts/qc_vocab_run.py` with source-specific degree profiles | Reuse completeness and schema checks for Paul without Dioscorides degree heuristics |
| `vocab_extract` controller knew only legacy + Dioscorides | Controller now tracks Paul full/smoke runs and consolidates Paul JSONL | Let autonomous status/complete cover all active corpora |
| Imports appended only `entries_diosc.csv` | `scripts/import_supabase.py` appends `entries_paul.csv`; `scripts/import_vocab_v3.py` dry-run checks Paul IDs | Ensure Paul entries exist before legacy vocab assertions attach |
| DB/app source lists lacked Paul | `supabase/migrations/009_paul_source.sql`; `/entries` source filter includes `PAUL_AEG` | Make Paul selectable and FK-valid |
| No Paul-specific extraction prompt/scripts | `docs/prompts/vocab_term_extractor_with_degrees_paul.md` and `npm run paul:*` scripts | Capture Paul’s explicit degree language and provide repeatable commands |

---

### 2026-04-06 — Documentation updates

**Why**: CLAUDE.md and AGENTS.md were out of date after the restructure changes.

| Before | After | Why |
|--------|-------|-----|
| `CLAUDE.md` normalization section listed `validate_data.py` as a separate implementation | Rewritten: single-source-of-truth description, all consumers delegate to `textutils.normalize` | Reflect actual code state |
| `CLAUDE.md` environment section said "Python scripts use stdlib only (no pip dependencies)" | Describes `pyproject.toml` + `pip install -e ".[dev]"` with dependency groups | Reflect new packaging |
| `CLAUDE.md` workspace layout was missing `pipelines/`, had old test count | Updated with pipelines directory, test count 40, migration range 001-007 | Accuracy |
| `AGENTS.md` test count said 35 | Updated to 40 | Accuracy |
| `AGENTS.md` missing `pipelines/` in project structure | Added with description | Accuracy |
| `AGENTS.md` missing `pip install` in install deps | Added `pip install -e ".[dev]"` | Completeness |

---

### 2026-04-06 — Repo cleanup: legacy docs to archive

**Why**: Active working surface should only show TEI-first and current extraction docs. Legacy QC reports and analysis artifacts moved to archive for traceability.

| Before | After | Why |
|--------|-------|-----|
| `data-workbench/simples_data_restructure_spec.md` | `archive/docs/legacy_qc/simples_data_restructure_spec.md` | CSV-first spec superseded by TEI-first tech_spec |
| `data-workbench/columnO_category_audit.md` | `archive/docs/legacy_qc/columnO_category_audit.md` | One-time xlsx column audit |
| `data-workbench/preparations_diff_report.md` | `archive/docs/legacy_qc/preparations_diff_report.md` | One-time diff report |
| `data-workbench/lemmata_qc.md` | `archive/docs/legacy_qc/lemmata_qc.md` | Legacy lemmata QC |
| `data-workbench/lemmata_canonical_qc.md` | `archive/docs/legacy_qc/lemmata_canonical_qc.md` | Legacy canonical lemmata QC |
| `data-workbench/parts_qc.md` | `archive/docs/legacy_qc/parts_qc.md` | Legacy parts QC |
| `data-workbench/diosc_alignment_apply_report.md` | `archive/docs/legacy_qc/diosc_alignment_apply_report.md` | One-time apply report |
| `data-workbench/diosc_missing_text_apply_report.md` | `archive/docs/legacy_qc/diosc_missing_text_apply_report.md` | One-time apply report |
| `data-workbench/diosc_text_fixes_apply_report.md` | `archive/docs/legacy_qc/diosc_text_fixes_apply_report.md` | One-time apply report |
| `data-workbench/diosc_missing_text_qc.md` | `archive/docs/legacy_qc/diosc_missing_text_qc.md` | One-time QC check |
| `docs/vocab_v3_analysis_and_ner.md` | `archive/docs/analysis/vocab_v3_analysis_and_ner.md` | Analysis artifact, not a spec |
| `docs/vocab_v3_ner_handoff.md` | `archive/docs/analysis/vocab_v3_ner_handoff.md` | NER scoping notes, not a spec |
| `WORKTREE_STATE.md` (repo root) | `archive/docs/misc/WORKTREE_STATE.md` | Superseded by session_log + new_wbs |

---

### 2026-04-06 — Product plan + autonomous architecture

**Why**: Needed a central roadmap and a structured approach for autonomous work sessions.

| Before | After | Why |
|--------|-------|-----|
| No product roadmap existed | `PRODUCT_PLAN.md` — 5-phase plan: org → extraction → import → search → NER | Central planning document |
| `AGENTS.md` had no autonomous work roles | Added 3-role architecture: Planner (read-only), Implementer (executes plan), QC/Verifier (runs checks) | Structured autonomous work with handoff points |
| `outputs/README.md` was a 6-line minimal map | Rewritten with data-flow diagram, run inventory, and role as NER training corpus | Document extraction data as critical asset |
| `README.md` start-here pointed to `WORKTREE_STATE.md` | Points to `PRODUCT_PLAN.md` | Reflect current workflow |
| `docs/README.md` had "Historical" section pointing to archive | Replaced with "See also" section linking contracts, PRODUCT_PLAN, archive | Cleaner navigation |
| `data-workbench/README.md` listed all QC files inline | Simplified: canonical inputs, Dioscorides ops, active QC only; archived QC noted | Reflect moved files |
| Workflow docs referenced `data-workbench/diosc_*_apply_report.md` paths | Updated to `archive/docs/legacy_qc/diosc_*_apply_report.md` | Paths moved |

---

### 2026-04-25 — Autonomous vocab outputs-to-search path

**Why**: Legacy extraction output was complete but not ingestible, Dioscorides full extraction had not been launched, and direct repo commands failed without pytest's Python path.

| Before | After | Why |
|--------|-------|-----|
| `outputs/vocab_entries_v3/entries_full_v3/results.jsonl` was empty | Rebuilt from 2,135 per-entry JSON files | Import needs canonical JSONL input |
| No repo-local vocab controller | `pipelines/vocab_extract/__main__.py` with `status`, `consolidate`, and `complete` commands | Durable autonomous resume/status workflow |
| No explicit mapping for stale v3 extraction IDs | `config/vocab_entry_id_aliases.csv` | Auditable remap from old result IDs to current `entries.csv` IDs |
| `scripts/import_vocab_v3.py` was TEI/bridge-first | Importer supports `--target legacy` by default and keeps `--target tei` bridge-gated | Unblock search before TEI indexing is ready |
| No legacy-keyed extraction tables | `supabase/migrations/008_legacy_vocab_import.sql` | Store imported terms/assertions against current legacy entries |
| MVP `sources` seed lacked `DIOSC_DMM` for legacy tables | Migration `008` seeds `DIOSC_DMM` in `public.sources` | Let Dioscorides entries and vocab rows satisfy legacy FKs |
| `scripts/import_supabase.py` imported only `entries.csv` | Appends `entries_diosc.csv` by default, with `--skip-diosc` escape hatch | Ensure completed Dioscorides output can attach to `entries.entry_id` |
| `/entries` only supported Greek prefix search | Added source, quality, degree, and substance filters plus extraction panels on entry detail | First usable search surface over imported vocab output |
| Several direct scripts assumed installed `textutils` | Added repo-local `packages/` path bootstrap to direct script entrypoints | Make npm/Python commands work in this checkout |

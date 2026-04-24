# Product Plan: Ancient Simples

**Created**: 2026-04-06
**Status**: Active

## Vision

Build a scholarly search and computation platform for ancient Greek medical texts. The core data pipeline:

```
CSV entries (2,970 total)
    → LLM extraction (terms, qualities, lemmata)
        → Structured DB (assertions, lemma_forms, entry_lemma_forms)
            → Faceted search + cross-author computation
                → TEI-first transition (extraction results become NER training data)
```

Manually tagging several thousand entries is infeasible. The LLM extraction outputs are the foundation for both the search product and the future NER pipeline.

---

## Current State

### What we have

| Asset | Status | Location |
|-------|--------|----------|
| Legacy entries (GAL_SMT, AET_LM, ORIB_CM, GAL_ALIM) | 2,135 entries, complete | `data-workbench/entries.csv` |
| Dioscorides entries | 835 entries, built and validated | `data-workbench/entries_diosc.csv` |
| Legacy extraction results | 2,135/2,135 complete (100%) | `outputs/vocab_entries_v3/entries_full_v3/` |
| Dioscorides extraction results | 71/835 (8.5%) | `outputs/vocab_entries_v3/diosc_smoke_v3/` |
| Extracted terms | 27,707 total, 6,936 substances | Individual JSON files |
| Extracted qualities | 2,894 (HOT/COLD/DRY/WET with degrees) | Individual JSON files |
| Extraction tooling | Orchestrator + single-entry runner | `scripts/vocab_multi_agent_pilot.py`, `scripts/vocab_agent_runner.py` |
| Import script | Exists but blocked on bridge CSV | `scripts/import_vocab_v3.py` |
| TEI-first schema | Defined (migrations 005-007) | `supabase/migrations/` |
| App | Minimal MVP, prefix search only | `app/` |
| Contracts | 6 formal specs | `contracts/` |
| JSON schemas | Extraction output validation | `schemas/` |
| LLM prompts | 3 variants (legacy, Dioscorides) | `docs/prompts/` |
| Accuracy evaluation | Complete, model selected (gpt-5.2 + high) | `outputs/vocab_entries_v3/accuracy_eval/` |

### What's missing

| Gap | Blocks | Phase |
|-----|--------|-------|
| Dioscorides full extraction | Complete corpus coverage | 2 |
| Consolidated `results.jsonl` | Import pipeline | 3 |
| Import with legacy IDs | Getting data into DB | 3 |
| Faceted search UI | Product launch | 4 |
| Lemma browser | Product launch | 4 |
| Assertion detail views | Product launch | 4 |
| Cross-author alignment UI | Comparative scholarship | 4 |
| TEI indexer reconciliation | TEI transition | 5 |
| NER training pipeline | Automated annotation | 5 |
| Frontend tests | Code quality | 4 |
| TS/SQL parity tests | Normalization safety | 3 |

---

## Phase 1: Repo Organization

**Goal**: Clear the working surface so only TEI-first and active extraction files are visible. Move legacy artifacts to `archive/`. No deletions.

### Move to archive
- 10 legacy QC `.md` files from `data-workbench/` → `archive/docs/legacy_qc/`
- 2 analysis `.md` files from `docs/` → `archive/docs/analysis/`
- `WORKTREE_STATE.md` → `archive/docs/misc/`

### Update
- All README files and doc maps to reflect new locations
- `CLAUDE.md`, `AGENTS.md` to remove stale references
- WBS + session log

---

## Phase 2: Complete Dioscorides Extraction

**Goal**: Extract all 835 Dioscorides entries to match legacy corpus completion.

### Steps
1. Clear stale `.json.tmp` files from smoke runs
2. Resume smoke run (target: 25/25 complete)
3. QC smoke results
4. Launch full run: `diosc_full_v3` with `--parallel 10`
5. QC full run with `scripts/qc_diosc_vocab_run.py`

**Result**: 835 new extraction JSONs → total corpus = 2,970 entries

---

## Phase 3: Import Extraction Results

**Goal**: Get extraction data into the database so the app can query it.

### Approach: Import with legacy IDs first

The bridge CSV (legacy ID → TEI segment ID) requires TEI indexing which isn't ready. Instead of waiting, import directly linked to the legacy `entries` table.

### Steps
1. Write `scripts/consolidate_results.py` — convert individual JSONs → `results.jsonl`
2. Modify `import_vocab_v3.py` — add `--legacy` mode that writes assertions and lemma_forms linked to legacy entry IDs
3. Import legacy corpus (2,135 entries → ~6,936 lemma_forms, ~27,707 entry_lemma_forms, ~2,894 assertions)
4. Import Dioscorides corpus once Phase 2 completes
5. Add TS/SQL normalization parity tests

### Tables populated
| Table | Content | Estimated rows |
|-------|---------|---------------|
| `lemma_forms` | Unique extracted terms (deduplicated) | ~6,936 |
| `entry_lemma_forms` | Entry ↔ term links with role + confidence | ~27,707 |
| `assertions` | Quality statements (axis, degree, evidence) | ~2,894 |

---

## Phase 4: Build Search & Computation

**Goal**: Transform the app from a minimal translation editor into a scholarly search tool.

### 4a. Faceted search (`/entries` enhancement)
- Filter by: quality axis (HOT/COLD/DRY/WET), degree (1-4), source, assertion type
- Full-text search on English translation (trigram index exists, unused)
- Combined Greek prefix + facet filters
- Files: `app/src/app/entries/page.tsx`, new `app/src/lib/queries/` module

### 4b. Entry detail with assertions (`/entries/[entry_id]` enhancement)
- Show assertions (qualities with degree + evidence text)
- Show extracted terms with labels and confidence
- Show linked lemmata
- Files: `app/src/app/entries/[entry_id]/page.tsx`, new components

### 4c. Lemma browser (`/lemmata` — new route)
- Browse by category (vegetable/animal/mineral) or alphabetically
- Lemma → all entries containing it
- Cross-source comparison
- Files: new `app/src/app/lemmata/` routes

### 4d. Cross-author alignment (`/alignments` — new route)
- Parallel passages across Galen, Aetius, Dioscorides, Oribasius
- Built on `tei_entry_alignments` + alignment seed data
- Files: new `app/src/app/alignments/` route

### 4e. Export & computation
- Download filtered results as CSV/JSON
- Summary statistics (term frequency, quality distribution by source)
- Substance → quality relationship views

### 4f. Frontend tests
- Vitest for normalization, citation formatting, query builders
- Playwright for critical user flows (search, filter, entry detail)

---

## Phase 5: TEI Transition + NER

**Goal**: Move to TEI XML as canonical text source, using extraction results as NER training data.

### 5a. TEI indexing
- Reconcile `scripts/index_tei.py` with schema 005 (`TEI-INDEX-01`)
- Restore `tei/cmg` submodule
- Index TEI → `tei_entries`, `tei_tokens`, `tei_entry_refs`

### 5b. Bridge + FK remapping
- Build `config/entry_id_bridge.csv` from indexed TEI entries
- Remap assertions + lemma_forms from legacy → TEI entry IDs
- Switch app queries from legacy `entries` → `tei_entries`

### 5c. NER training corpus
- Convert extraction JSONs → token-level NER annotations (IOB/BIO tags)
- Align extracted terms to `tei_tokens` positions
- Reference: analysis in `archive/docs/analysis/vocab_v3_analysis_and_ner.md`

### 5d. NER pipeline
- Train NER model on the 2,970 labeled entries
- Apply to new TEI sources (PAUL_RM, full GAL_ALIM)
- Human-in-the-loop review for NER output
- Files: new `pipelines/ner/` module

---

## Files to Create

### Phase 1 (this session)
| Status | File | Purpose |
|--------|------|---------|
| CREATE | `PRODUCT_PLAN.md` | This document |
| UPDATE | `AGENTS.md` | Add 3-role architecture |
| MOVE | 13 files → `archive/` | Organize legacy docs |
| UPDATE | 6 README/doc files | Reflect new locations |

### Phase 3
| File | Purpose |
|------|---------|
| `scripts/consolidate_results.py` | JSONs → `results.jsonl` |
| `scripts/import_vocab_v3.py` (modify) | Add `--legacy` import mode |
| `tests/test_import.py` | Import pipeline tests |

### Phase 4
| File | Purpose |
|------|---------|
| `app/src/lib/queries/assertions.ts` | Assertion query builder |
| `app/src/lib/queries/lemmata.ts` | Lemma query builder |
| `app/src/app/lemmata/page.tsx` | Lemma browser |
| `app/src/app/lemmata/[lemma_id]/page.tsx` | Lemma detail |
| `app/src/app/alignments/page.tsx` | Alignment view |
| `app/src/components/FacetFilters.tsx` | Search filter components |
| `app/src/components/AssertionList.tsx` | Assertion display |
| `app/src/components/TermList.tsx` | Term display |
| `docs/new_simples/search_spec.md` | Search feature spec |
| `app/vitest.config.ts` | Frontend test config |

### Phase 5
| File | Purpose |
|------|---------|
| `pipelines/ner/__init__.py` | NER pipeline module |
| `pipelines/ner/__main__.py` | NER training entry point |
| `docs/new_simples/ner_plan.md` | NER pipeline spec |

---

## Extraction Pipeline Reference

```
data-workbench/entries.csv (2,135 rows)
data-workbench/entries_diosc.csv (835 rows)
    ↓
scripts/vocab_multi_agent_pilot.py (orchestrator, --parallel 10)
    ↓
scripts/vocab_agent_runner.py (per-entry, gpt-5.2 + high reasoning)
    ↓
schemas/vocab_term_extractor_with_degrees.schema.json (validation)
    ↓
outputs/vocab_entries_v3/{run_id}/results/*.json
    ↓
scripts/consolidate_results.py (TODO: JSONs → results.jsonl)
    ↓
scripts/import_vocab_v3.py (TODO: --legacy mode)
    ↓
DB: assertions + lemma_forms + entry_lemma_forms
    ↓
App: faceted search, lemma browser, alignment view
    ↓
NER training corpus (Phase 5)
    ↓
Automated annotation of new TEI sources
```

## Extraction Statistics

| Metric | Legacy corpus | Dioscorides | Total |
|--------|--------------|-------------|-------|
| Entries | 2,135 | 835 | 2,970 |
| Extraction complete | 100% | 8.5% | 72% |
| Terms extracted | 27,707 | ~71 entries done | — |
| Substances | 6,936 | — | — |
| Qualities | 2,894 | — | — |
| Model | gpt-5.2 + high | gpt-5.2 + high | — |

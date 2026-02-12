# Ancient Simples TEI-First Platform — Work Breakdown Structure (D-03)

Version: 1.0
Status: Draft

## 1. Milestones

M0: Contracts and textutils determinism complete
- all contracts C-01..C-05 written
- normalization parity test passes (Python/TS/SQL)

M1: TEI-first schema deployed
- migrations apply cleanly in a fresh Supabase project

M2: Indexer validated on test subset
- index_tei ingests 3 sources (Galen SMT, Aetius LM, Dioscorides DMM)
- re-index idempotency verified

M3: Imports validated on test subset
- v3 vocab importer creates lemma_forms + assertions
- alignment seed import creates entry_alignments

M4: Phase 2 gate passes
- all four facet query patterns return non-empty results
- multi-author lemma linking works (at least one shared lemma concept)

M5: Core UI delivered
- /entries, entry detail, translations, citations

M6: Facet query UI delivered
- /assertions/quality, /parts, /processes with CSV export

M7: Lemma UI delivered
- /lemmata and /lemmata/[lemma_id] comparison view

## 2. Phase 0 — Foundation (contracts + textutils)

D-01: Write tech spec (`docs/new_simples/tech_spec_v1.md`)
D-02: Write UX/UI spec (`docs/new_simples/ux_spec_v1.md`)
D-03: Write WBS (`docs/new_simples/wbs_v1.md`)

G-01: Add CMG corpus repo as git submodule (`tei/cmg/`)
G-02: Configure `.gitmodules` and `.gitignore`

C-01: TEI indexing contract
C-02: Normalization contract (NORMALIZATION_VERSION = 1.1; iota subscripts dropped)
C-03: Anchoring + tokenization contract
C-04: Citation contract
C-05: Export contract

F-02: TEI doc config schema + example YAML
F-03: Python normalization implementation + tests
F-04: Tokenizer implementation + tests
F-05: Hashing + citation helpers
F-06: Parity test across Python/TS/SQL
F-07: Packaging + shared fixtures

Phase 0 exit criteria (M0):
- `normalize("Ψυχρός") == "ψυχρος"` in Python/TS/SQL
- `normalize("τῇ") == "τη"` in Python/TS/SQL
- tokenizer offsets match fixtures

## 3. Phase 1 — Schema + Indexer + Importers

Track A: Database schema

S-01: Migration `005_tei_first_schema.sql`
- create TEI-first tables (tei_docs, tei_entries, tokens, entry_refs, import_runs, translations, assertions, lemma_forms, lemmata, entry_lemma_forms, lemma_aliases, entry_alignments)
- create CHECK constraints and indexes aligned to facet queries

S-02: Migration `006_tei_rls.sql`
- RLS policies per tech spec

S-03: Manual validation
- apply migrations to a fresh Supabase project

Track B: TEI indexer

I-01: `scripts/validate_tei.py`
- fatal errors on missing/duplicate xml:id
- smoke tests for reading stream rules

I-02: `scripts/index_tei.py`
- read doc config
- extract reading_text, refs, hashes
- tokenize
- upsert tei_entries, tokens, entry_refs

I-03: Staleness + deactivation semantics
- raw_hash change → mark assertions stale
- deactivate unseen segments

I-04: Import run reporting

I-05: `--dry-run` mode

Track C: Vocab importer

V-01: `config/entry_id_bridge.csv`

V-02: `scripts/import_vocab_v3.py`
- create lemma_forms (candidates)
- create entry_lemma_forms links
- create quality assertions (draft)

V-03: Conservative merge rules
- ambiguous groups → needs_review
- no cross-tradition auto-merges

V-04: Import validation report

Track D: Alignment

AL-01: Interchange format spec

AL-02: Seed alignment dataset (core 3 authors)

AL-03: `scripts/import_alignments.py`

AL-04: Schema for entry_alignments (in S-01 or follow-on)

AL-05: Alignment review UI (deferrable)

Phase 1 exit criteria (M1–M3):
- schema deployed and RLS behaves as specified
- indexer can index at least one doc end-to-end
- importer can create draft lemma_forms + assertions

## 4. Phase 2 — Test subset gate

T-01: Select test subset (`config/test_subset.txt`)
- ~18 entries across ≥3 sources

T-02: Ensure TEI files available via submodule

T-03: Create doc configs for test sources
- `config/tei_docs/gal_smt.yaml`
- `config/tei_docs/aet_lm.yaml`
- `config/tei_docs/diosc_dmm.yaml`

T-04: Run indexer on subset

T-05: Populate entry_id bridge rows for subset

T-06: Run vocab importer on subset

T-07: End-to-end validation
- re-index idempotency
- four facet query patterns return non-empty results

Phase 2 exit criteria (M4):
- ≥10 Galen/Aetius + ≥3 Dioscorides entries indexed with citations + tokens
- ≥3 quality assertions with degrees
- ≥2 lemma_forms in needs_review/confirmed
- ≥1 cross-author lemma concept in lemma UI (confirmed or provisional)

## 5. Phase 3 — Application UI

U-01: Navigation update

U-02: Entries list

U-03: Entry detail

U-04: Translation editor + version history

U-05: Lemmata list

U-06: Lemma detail + comparison view

U-07: Quality facet UI + CSV export

U-08: Parts facet UI

U-09: Processes facet UI

U-10: Assertions index

U-11: Shared citation formatter

U-12: Stale review UI

## 6. Critical path

Minimum critical path to first usable TEI-first UI:

C-01 → C-02 → F-03 → F-06 → S-01 → I-02 → T-04 → T-07 → U-03

## 7. Risks and mitigations

1) TEI structural inconsistencies
- mitigated by strict validation + small subset gate

2) Performance of token ingestion
- mitigated by REST for subset, COPY for full corpus, delayed index creation

3) Lemma merge errors
- mitigated by lemma_forms-first workflow and needs_review state

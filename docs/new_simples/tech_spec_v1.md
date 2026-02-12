# Ancient Simples TEI-First Platform — Technical Specification (D-01)

Version: 1.0
Status: Draft

## 1. Scope

This document specifies a TEI-first rewrite of the Ancient Simples platform.

Canonical source:
- TEI editions from the CMG pipeline (Git submodule)

SQL database stores:
- rebuildable caches derived from TEI (entries, tokens, citations)
- editorial layers (translations, lemma linking, assertions, alignments)

Out of scope for v1:
- full recipe modeling (ingredient graph, preparation workflows beyond facet-level assertions)

## 2. High-level architecture

Components:

1) TEI source (CMG submodule)
- Mounted at `tei/cmg/` and pinned to a commit for reproducibility.
- Indexer reads TEI from `tei/cmg/tei/output/`.

2) Indexer (Python + lxml)
- Validates TEI and config.
- Extracts `reading_text`, citations, dual hashes, and tokens.
- Writes to Postgres/Supabase.

3) textutils library
- Shared normalization + tokenization + hashing utilities.
- Guarantees determinism across Python/TypeScript/SQL.

4) Postgres (Supabase)
- Stores TEI-derived caches and editorial layers.
- RLS partitions indexer-write vs editor-write surfaces.

5) Next.js application
- Server component UI for browsing entries and editing editorial layers.

## 3. Core contracts

The platform depends on the following normative contracts:
- C-01 TEI Indexing Contract
- C-02 Normalization Contract (NORMALIZATION_VERSION = 1.1; iota subscripts dropped)
- C-03 Anchoring + Tokenization Contract
- C-04 Citation Contract
- C-05 Export Contract

Implementations MUST conform to these contracts; behavior changes require contract + version bumps.

## 4. Identity model

Canonical entry identity is the pair:
- `tei_doc_id`
- `tei_segment_id` (from TEI `@xml:id`)

Display entry id:
- `{tei_doc_id}~{tei_segment_id}`

Rationale:
- `#` is a browser fragment marker and cannot safely appear in routes.

Routes MUST use the display entry id.

## 5. Data model (Postgres)

This section describes the TEI-first tables. The actual DDL lives in migrations.

### 5.1 sources

Purpose: registry of texts and indexing readiness.

Key columns:
- `code` (PK) e.g., GAL_SMT, AET_LM, DIOSC_DMM
- `name`
- `edition`
- `status` enum-like text: active | registered | pending

### 5.2 tei_docs

Purpose: register TEI documents and bind them to sources.

Key columns:
- `tei_doc_id` (PK)
- `source_code` (FK sources.code)
- `tei_relpath` (relative path inside submodule)
- `label` (human-readable)
- `config_path` (YAML config location)
- `created_at`

### 5.3 import_runs

Purpose: provenance and audit for indexing/import pipelines.

Key columns:
- `id` UUID (PK)
- `started_at`, `finished_at`
- `cmg_submodule_commit`
- `indexer_version`
- `normalization_version` (expects “1.1”)
- `tokenizer_version` (expects “1.0”)
- `mode` (dry_run|live)
- `counts` JSONB (per-doc and totals)
- `warnings` JSONB

### 5.4 tei_entries

Purpose: TEI-derived entries (rebuildable cache) with stable identity.

Key columns:
- `id` BIGSERIAL (PK)
- `tei_doc_id` (FK tei_docs.tei_doc_id)
- `tei_segment_id` (text)
- `display_entry_id` (text; stored or generated)
- `reading_text` (text; NFC)
- `normalized_text` (text; normalize(reading_text) per C-02)
- `raw_hash` (hex sha256 of reading_text)
- `normalized_hash` (hex sha256 of normalized_text)
- `is_active` boolean default TRUE
- `last_import_run_id` (FK import_runs.id)
- timestamps

Constraints:
- UNIQUE(tei_doc_id, tei_segment_id)

Indexes (minimum):
- (tei_doc_id)
- (is_active)
- optionally trigram or tsvector indexes on normalized_text (post-v1 decision)

### 5.5 entry_refs

Purpose: citations per entry (rebuildable cache).

Key columns:
- `id` BIGSERIAL (PK)
- `tei_entry_id` (FK tei_entries.id)
- `ref_type` text: structure | edition
- `payload` JSONB (schemas defined by C-04)

Constraints:
- at most one structure row and one edition row per entry

### 5.6 tokens

Purpose: per-entry tokens for search and anchoring (rebuildable cache).

Key columns:
- `id` BIGSERIAL (PK)
- `tei_entry_id` (FK tei_entries.id)
- `token_index` int
- `start_offset` int (codepoints)
- `end_offset` int (codepoints)
- `token_text` text
- `token_normalized` text

Constraints:
- UNIQUE(tei_entry_id, token_index)

Indexes:
- (tei_entry_id)
- (token_normalized)

Scale note:
- tokens will be large at corpus scale; full-corpus ingestion should use COPY or large batched inserts.

### 5.7 translations

Purpose: editor-owned translations with versioning.

Key columns:
- `id` BIGSERIAL (PK)
- `tei_entry_id` (FK)
- `language` (e.g., 'en')
- `version` int (monotonic per entry+language)
- `status` text: draft | reviewed | published
- `text` (translation body)

Provenance columns (required when imported):
- `source_file`
- `source_row_id`
- `import_method`

### 5.8 assertions

Purpose: facet assertions (editor-owned) with extensible JSON payloads.

Key columns:
- `id` BIGSERIAL (PK)
- `tei_entry_id` (FK)
- `assertion_type` text: quality | part | process | other
- `payload` JSONB
- `status` text: draft | needs_review | confirmed
- `source` text (e.g., 'v3_import', 'diosc_vpp_import', 'manual')
- `is_stale` boolean default FALSE
- `anchor` JSONB (schema in C-03)

Constraints:
- CHECK constraints per type (minimum):
  - quality: payload has key 'axis'
  - part: payload has key 'part_name'
  - process: payload has key 'process_name'

Indexes:
- partial/expression indexes aligned to facet queries, e.g.:
  - (assertion_type, (payload->>'axis'))
  - (assertion_type, (payload->>'degree'))

### 5.9 controlled vocab tables

- `quality_vocab` (axis, gloss, ordering)
- `parts_vocab` (part_name, gloss)
- `process_vocab` (process_name, gloss)

These tables seed dropdowns and reduce spelling drift.

### 5.10 lemma layer

Goal: avoid irreversible automatic merges. Strings are captured first; concept-level lemmata are curated.

Tables:

1) `lemmata` (concepts)
- `lemma_id` text (PK, e.g. L000123)
- `headword_grc`
- `headword_normalized`
- `status` (draft|confirmed)

2) `lemma_forms` (strings)
- `id` UUID (PK)
- `form_grc`
- `form_normalized` (C-02)
- `status` (draft|needs_review|confirmed)
- `source` (v3_import|cmg_alignment|manual|csv_bridge)
- `confidence` numeric
- `lemma_id` nullable FK lemmata.lemma_id
- provenance columns (source_file, source_row_id, import_method) when imported

3) `entry_lemma_forms`
- `tei_entry_id` FK tei_entries.id
- `lemma_form_id` FK lemma_forms.id
- `role` text (headword|mentioned)
- `confidence` numeric

4) `lemma_aliases` (optional concept aliases)
- `lemma_id` FK
- `alias_grc`, `alias_normalized`
- `alias_type` (orthographic|cross_tradition|gloss)

Substance facet query is concept-driven:
- join entries → entry_lemma_forms → lemma_forms → lemmata

### 5.11 entry_alignments

Purpose: cross-author structural alignments.

Key columns:
- `id` BIGSERIAL (PK)
- `tei_entry_id_a` FK tei_entries.id
- `tei_entry_id_b` FK tei_entries.id
- `alignment_type` text (chapter_parallel|excerpt|rearrangement|independent)
- `confidence` numeric
- `source` text (cmg_alignment|manual)
- `evidence` JSONB
- `curator` text

## 6. Ingestion and pipelines

### 6.1 TEI indexing (C-01)

Steps:
1) validate TEI and config
2) for each segment: extract `reading_text` and refs
3) compute `raw_hash`, `normalized_text`, `normalized_hash`
4) tokenize reading_text (C-03)
5) upsert tei_entries, entry_refs, tokens
6) deactivate unseen segments for each tei_doc_id
7) write `import_runs`

Staleness semantics:
- If `raw_hash` changes, assertions anchored to that entry are stale.
- If `normalized_hash` changes, tokens MUST be recomputed.

### 6.2 Vocab v3 import

Input:
- `outputs/vocab_entries_v3/.../results.jsonl`
- `config/entry_id_bridge.csv` mapping old ids to new display ids

Output:
- lemma_forms (candidates)
- entry_lemma_forms links
- quality assertions (draft)

Importer MUST be conservative:
- do not auto-merge lemma concepts across sources
- ambiguous groups become status=needs_review

### 6.3 Dioscorides CSV supplements

Input:
- `diosc.csv` (translations and var_par_prod_gr)

Output:
- translations (version 1) with provenance columns set
- assertions (draft) with provenance columns set

### 6.4 Alignment import

Input:
- JSONL/CSV interchange format defined in AL-01

Output:
- entry_alignments rows

## 7. RLS model (Supabase)

Goals:
- indexer writes only TEI-derived caches
- editors write only editorial layers
- authenticated users can read everything

Proposed partition:

Indexer-owned (service-role write only):
- tei_entries
- tokens
- entry_refs
- import_runs

Editor-owned (authenticated write):
- translations
- assertions
- lemma_forms (status updates)
- lemmata (curated merges)
- lemma_aliases
- entry_alignments (manual curation)

All authenticated users: read access.

## 8. Performance and scaling

Test subset:
- Supabase REST writes are acceptable.

Full corpus:
- tokens ingestion should use Postgres COPY or large-batch inserts.
- create heavy indexes after the bulk load.

## 9. Facet query patterns (normative SQL)

The following four query patterns are the primary analytical interface. Expression indexes (§5.8) MUST align to these patterns.

### 9.1 Quality facet

```sql
-- "all drugs hot in the 3rd degree"
SELECT te.display_entry_id, a.payload->>'axis' AS axis,
       a.payload->>'degree' AS degree, a.status, a.source
FROM assertions a
JOIN tei_entries te ON te.id = a.tei_entry_id
WHERE a.assertion_type = 'quality'
  AND a.payload->>'axis' = 'HOT'
  AND a.payload->>'degree' = '3'
  AND te.is_active = TRUE;
```

### 9.2 Part facet

```sql
-- "all plant roots"
SELECT te.display_entry_id, a.payload->>'part_name' AS part_name, a.status
FROM assertions a
JOIN tei_entries te ON te.id = a.tei_entry_id
WHERE a.assertion_type = 'part'
  AND a.payload->>'part_name' = 'ῥίζα'
  AND te.is_active = TRUE;
```

### 9.3 Process facet

```sql
-- "all instances of boiling"
SELECT te.display_entry_id, a.payload->>'process_name' AS process_name, a.status
FROM assertions a
JOIN tei_entries te ON te.id = a.tei_entry_id
WHERE a.assertion_type = 'process'
  AND a.payload->>'process_name' = 'ἕψησις'
  AND te.is_active = TRUE;
```

### 9.4 Substance facet (lemma join)

```sql
-- "where does absinth appear"
SELECT te.display_entry_id, l.headword_grc, lf.form_grc
FROM tei_entries te
JOIN entry_lemma_forms elf ON elf.tei_entry_id = te.id
JOIN lemma_forms lf ON lf.id = elf.lemma_form_id
JOIN lemmata l ON l.lemma_id = lf.lemma_id
WHERE l.headword_normalized LIKE 'αψινθ%'
  AND te.is_active = TRUE;
```

## 10. Source-specific notes

### 10.1 Galen Alim. Fac. hybrid edition

GAL_ALIM TEI uses dual `<pb>` streams: Helmreich (primary, `@ed="Helmreich"`) and Kühn (secondary, `@edRef="Kühn"`). The indexer MUST:
- Use `@ed` (Helmreich) as the primary edition ref.
- Record Kühn refs as secondary entries in the `events` array with `ed: "Kühn"`.
- The citation formatter SHOULD display both when available (e.g., `Helmreich 1.7.3 [= Kühn VI.485]`).

This source is `status='registered'` (not indexed in Phase 1) but the indexer MUST handle dual editions when it is activated.

### 10.2 Dioscorides CSV supplement provenance

When importing translations and annotations from `diosc.csv`:

**Translations**: Import as `translations` version 1 rows with:
- `source_file = 'diosc.csv'`
- `source_row_id` = CSV row number (0-indexed)
- `import_method = 'csv_bridge'`

**var_par_prod_gr annotations**: Two-pass classification:
1. Automated lookup for top ~80 known terms against `parts_vocab` + `process_vocab` → assertions with `source='diosc_vpp_import'`, `status='draft'`
2. Remaining terms → queue for v3 pipeline extraction or manual review

All CSV-derived rows MUST carry provenance columns so they can be identified and replaced when TEI-derived or v3-extracted data supersedes them.

**Lemma headwords from CSV**: Use `diosc.csv` headword column as seed data for `match_diosc_lemmata.py`. Creates `lemma_forms` with `source='csv_bridge'`, `status='draft'`. Generates an audit CSV flagging category mismatches against existing lemmata for human review.

## 11. Verification checklist

A build is considered valid when:
- normalization parity passes (Python/TS/SQL)
- indexing the same inputs twice is idempotent (identical hashes and counts)
- a TEI change that alters reading text changes `raw_hash` and stales anchored assertions
- all four facet query patterns return results on the Phase 2 test subset:
  - quality
  - part
  - process
  - substance (lemma join)

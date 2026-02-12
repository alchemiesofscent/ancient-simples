# Export Contract (C-05)

Version: 1.0
Status: Draft (normative for TEI-first v1)

## 1. Purpose

This contract defines how the platform MUST export TEI-first data for:
- research use (CSV/JSON)
- auditing (round-trippable identifiers)
- downstream ingestion in other tools

Exports are not canonical (TEI is canonical), but exports MUST be deterministic and reproducible when pinned to an import run.

## 2. Export bundles

An export bundle is a directory (or archive) containing:
- a metadata file describing versions and provenance
- one or more tabular or JSONL datasets

Bundle id:
- `bundle_id` SHOULD be `<date>_<import_run_id>`.

## 3. Required metadata

Every bundle MUST include `meta.json` with at least:
- `export_version`: "1.0"
- `generated_at` (ISO timestamp)
- `import_run_id`
- `cmg_submodule_commit`
- `indexer_version`
- `normalization_version`
- `tokenizer_version`

## 4. Required datasets

### 4.1 Entries (TEI-derived)

File: `tei_entries.jsonl` (or CSV)

Each row MUST include:
- `tei_doc_id`
- `tei_segment_id`
- `display_entry_id` (`tei_doc_id~tei_segment_id`)
- `is_active`
- `raw_hash`
- `normalized_hash`
- `reading_text`
- `normalized_text`

Citations MAY be embedded (structure + edition) or exported separately via `entry_refs.jsonl`.

### 4.2 Entry refs (citations)

File: `entry_refs.jsonl`

Each row MUST include:
- `display_entry_id`
- `ref_type` (`structure` or `edition`)
- `payload` (per C-04)

### 4.3 Tokens (optional)

File: `tokens.jsonl`

Tokens are optional because they can be very large at corpus scale.

If exported, each row MUST include:
- `display_entry_id`
- `token_index`
- `start_offset`
- `end_offset`
- `token_text`
- `token_normalized`

### 4.4 Translations

File: `translations.jsonl`

Each row MUST include:
- `display_entry_id`
- `language`
- `version`
- `status`
- `text`
- provenance fields if imported (e.g., `source_file`, `source_row_id`, `import_method`)

### 4.5 Assertions

File: `assertions.jsonl`

Each row MUST include:
- `display_entry_id`
- `assertion_type`
- `payload`
- `status`
- `source`
- `is_stale`
- `anchor` (if present)

### 4.6 Lemma layer

Files:
- `lemma_forms.jsonl`
- `lemmata.jsonl`
- `entry_lemma_forms.jsonl`

Each MUST include enough information to reproduce the linking graph.

### 4.7 Alignments

File: `entry_alignments.jsonl`

Each row MUST include:
- `display_entry_id_a`
- `display_entry_id_b`
- `alignment_type`
- `confidence`
- `source`
- `evidence` (optional)

## 5. Determinism requirements

Given a fixed `import_run_id` and fixed database state:
- Export output MUST be deterministic.

Deterministic means:
- stable ordering of rows (defined below)
- stable serialization (UTF-8, normalized newlines)

Ordering rules:
- Default ordering is by `(tei_doc_id, tei_segment_id)` for entry-keyed tables.
- Within an entry, tokens ordered by `token_index`.

## 6. Encoding

- All text MUST be UTF-8.
- Newlines MUST be `\n`.
- JSON MUST be valid RFC 8259.

## 7. Optional TEI standoff export

The exporter MAY produce a TEI standoff representation for editorial layers.

If produced:
- it MUST reference canonical TEI segment ids (`@xml:id`) and `tei_doc_id`
- assertions MUST reference anchors in a machine-readable way (token spans or offsets)

## 8. Acceptance criteria

C-05 is satisfied when:
- exports contain required metadata and datasets
- a bundle exported twice from the same state is byte-identical (or differs only in `generated_at` if configured)
- identifiers are round-trippable back to canonical entry keys

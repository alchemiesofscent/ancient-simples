# Alignment Interchange Format Specification (AL-01)

Version: 1.0
Status: Draft

## 1. Purpose

This document defines the interchange format for cross-author entry alignments
("Aet. I.106 ≈ Gal. SMT 6.1.1 ≈ Diosc. 1.1"). These records feed the
platform's comparison views and lemma linking.

## 2. Format

JSONL (one JSON object per line). File extension: `.jsonl`.

## 3. Record schema

Each line MUST be a valid JSON object with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_a_entry_id` | string | yes | Display entry ID of first entry (e.g., `gal_smt~seg_6_1_1`) |
| `source_b_entry_id` | string | yes | Display entry ID of second entry (e.g., `aet_lm~ch106`) |
| `alignment_type` | string | yes | One of: `chapter_parallel`, `excerpt`, `rearrangement`, `independent` |
| `confidence` | number | no | 0.0–1.0; null if manually curated (implicitly 1.0) |
| `evidence` | object | no | Free-form evidence supporting the alignment |
| `curator` | string | no | Identifier of person or process that created the alignment |
| `source` | string | yes | Provenance: `cmg_alignment`, `manual`, or other identifier |

## 4. Alignment types

- `chapter_parallel`: Entries cover the same substance/topic in parallel traditions (most common).
- `excerpt`: One entry is an excerpt or abbreviation of the other.
- `rearrangement`: Same content but reorganized (e.g., Aetius rearranging Galen's order).
- `independent`: Entries cover the same substance but with independently authored content.

## 5. Ordering convention

`source_a_entry_id` SHOULD be lexicographically less than `source_b_entry_id`.
This ensures each pair has a canonical representation.

## 6. Example

```jsonl
{"source_a_entry_id": "aet_lm~ch106", "source_b_entry_id": "gal_smt~seg_6_1_1", "alignment_type": "chapter_parallel", "confidence": 0.95, "source": "cmg_alignment", "curator": "structural_analysis"}
{"source_a_entry_id": "diosc_dmm~seg_1_1", "source_b_entry_id": "gal_smt~seg_6_1_1", "alignment_type": "chapter_parallel", "confidence": 0.90, "source": "cmg_alignment"}
{"source_a_entry_id": "aet_lm~ch106", "source_b_entry_id": "diosc_dmm~seg_1_1", "alignment_type": "excerpt", "confidence": 0.80, "source": "cmg_alignment"}
```

## 7. Validation rules

- Both entry IDs MUST use the `~` delimiter (not `#`).
- `alignment_type` MUST be one of the four defined types.
- `confidence` MUST be between 0.0 and 1.0 if present.
- Self-alignments (source_a == source_b) are NOT allowed.
- Duplicate pairs (same a, b, type) SHOULD be deduplicated; last writer wins.

## 8. Import

`scripts/import_alignments.py` reads this format and creates `tei_entry_alignments` rows.
Entry IDs are resolved to `tei_entries.id` integers via display_entry_id lookup.

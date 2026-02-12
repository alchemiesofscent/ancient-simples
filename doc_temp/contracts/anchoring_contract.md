# Anchoring and Tokenization Contract (C-03)

Version: 1.0
Status: Draft (normative for TEI-first v1)

## 1. Purpose

This contract defines:
- tokenization of TEI-derived reading text
- offset units for tokens and spans
- how assertions anchor to text spans
- how staleness and drift are detected when TEI content changes

## 2. Tokens

Tokens are generated from each entry’s `reading_text` (C-01).

### 2.1 Offset units

All offsets are:
- 0-indexed
- measured in Unicode codepoints (not bytes, not UTF-16 code units)
- relative to the NFC-normalized `reading_text`

Span intervals are half-open: `[start, end)`.

### 2.2 Token definition (TOKENIZER_VERSION = "1.0")

A token is a maximal contiguous sequence of characters where each character is:
- a Unicode Letter (general category `L*`), OR
- a Unicode Number (general category `N*`)

All other characters are delimiters and are not emitted as tokens.

Special handling:
- If combining marks (`Mn`) appear despite NFC normalization, they MUST be attached to the preceding token if present; otherwise they are ignored.
- Apostrophes and elision marks (e.g., U+2019 RIGHT SINGLE QUOTATION MARK, Greek koronis) are treated as delimiters.

### 2.3 Token outputs

For each token, the tokenizer MUST emit:
- `token_index`: sequential integer starting at 0 within the entry
- `start_offset`: inclusive codepoint offset into `reading_text`
- `end_offset`: exclusive codepoint offset into `reading_text`
- `token_text`: exact substring `reading_text[start_offset:end_offset]`
- `token_normalized`: `normalize(token_text)` per C-02

### 2.4 Token fixture requirements

The repository MUST include fixtures asserting:
- token boundaries for punctuation, brackets, and the `[...]` gap placeholder
- exact start/end offsets and substrings

Recommended fixture layout:
- `tests/fixtures/tokenize/<case>.txt`
- `tests/fixtures/tokenize/<case>.expected.json`

## 3. Anchors

Assertions MAY be anchored to a span of the entry’s `reading_text`.

### 3.1 Anchor kinds

v1 supports one normative anchor kind:

`token_span`
: A span defined by token indices (primary) with redundant character offsets (secondary).

### 3.2 Anchor payload schema (normative)

For `token_span`, `assertions.anchor` JSON MUST include:
- `kind`: "token_span"
- `entry_id`: integer `tei_entries.id`
- `start_token`: integer (inclusive)
- `end_token`: integer (exclusive)
- `start_offset`: integer (inclusive)
- `end_offset`: integer (exclusive)
- `quote`: string (exact substring of `reading_text` at time of anchoring)
- `raw_hash_at_creation`: string (hex SHA-256)
- `normalized_hash_at_creation`: string (hex SHA-256)

It SHOULD include:
- `normalization_version_at_creation` (e.g., "1.1")
- `tokenizer_version_at_creation` (e.g., "1.0")

### 3.3 Internal consistency rules

Given current `reading_text`:
- `quote` SHOULD equal `reading_text[start_offset:end_offset]`.
- `start_token`/`end_token` SHOULD correspond to the token indices that cover the quote.

If token indices and character offsets disagree, token indices are authoritative.

## 4. Staleness and drift

### 4.1 Staleness (hash-based)

Rule:
- If `tei_entries.raw_hash != assertions.anchor.raw_hash_at_creation`, the assertion MUST be marked `is_stale = TRUE`.

Rationale:
- `raw_hash` changes on any change to displayed reading text (C-01).

### 4.2 Drift detection (quote-based)

Rule:
- If `quote` is present and `reading_text[start_offset:end_offset] != quote`, the assertion SHOULD be treated as drifted and surfaced for review.

### 4.3 Re-anchoring

When an editor re-anchors a stale assertion:
- hashes in the anchor MUST be updated to current values
- `is_stale` MUST be set to FALSE

## 5. Acceptance criteria

C-03 is satisfied when:
- tokenization fixtures pass with exact offsets
- changing reading text triggers `raw_hash` change and marks anchored assertions stale
- anchors validate cleanly against current text via offsets + quote

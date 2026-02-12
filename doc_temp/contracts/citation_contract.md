# Citation Contract (C-04)

Version: 1.0
Status: Draft (normative for TEI-first v1)

## 1. Purpose

This contract defines how the platform MUST extract and represent citations for each TEI-derived entry.

Two citation classes are supported:
- Structure refs: references derived from TEI structural hierarchy
- Edition refs: references derived from edition milestones (`<pb>`, `<lb>`)

The TEI indexer (C-01) is responsible for extraction. The app is responsible for rendering using stable formatting rules.

## 2. Definitions

Structure ref
: A hierarchical position within a work, derived from ancestor divisions (e.g., Book → Chapter → Section).

Edition milestone
: A TEI element marking a page or line boundary in a printed edition.

Edition ref
: A human-readable citation derived from a span of milestones within an entry (page range, optionally line range).

## 3. Inputs

Inputs are:
- TEI segment node selected for indexing (C-01)
- The extracted `reading_text`
- The TEI doc config (must specify how to map hierarchy to a “structure path”)

## 4. Extraction rules

### 4.1 Structure refs

The indexer MUST compute a structure path for each segment.

Default rule (unless overridden in config):
- Walk ancestor elements from the segment up to the TEI body.
- Collect TEI `<div>` elements in outer-to-inner order.
- For each collected `<div>`, capture:
  - `xml_id` (if present)
  - `n` (if present)
  - `type` (if present)
  - first `<head>` text (if present, normalized whitespace)

Config MAY restrict which `<div>` levels are included (e.g., only `@type in {book, chapter}`), but extraction MUST remain deterministic.

### 4.2 Edition refs (`<pb>`, `<lb>`)

The indexer MUST collect edition milestones encountered during the same traversal used for reading text extraction (C-01).

Rules:
- `<pb>` and `<lb>` MUST NOT contribute text to `reading_text`.
- Each milestone MUST be recorded with:
  - `kind`: "pb" or "lb"
  - `n`: the `@n` value (string)
  - `offset`: codepoint offset into `reading_text` at the milestone position

The milestone list MUST be in document order.

### 4.3 Deriving a summary edition ref

For each entry, the indexer MUST compute a summary ref from the milestone list:
- `start_pb`: first pb encountered (if any)
- `end_pb`: last pb encountered (if any)
- `start_lb`: first lb after start_pb within the segment (if any)
- `end_lb`: last lb before end_pb within the segment (if any)

If lb milestones are missing entirely:
- the edition ref is page-range-only (pb-only)

If pb milestones are missing entirely:
- the entry has no edition ref (this SHOULD be a validation warning for editions expected to have pb)

## 5. Database representation

Citations are stored in `entry_refs`.

### 5.1 Structure refs row

The indexer MUST write exactly one structure refs row per entry:
- `entry_refs.ref_type = 'structure'`
- `entry_refs.payload` JSON schema:

```json
{
  "path": [
    {"type": "book", "n": "1", "xml_id": "b1", "head": "..."},
    {"type": "chapter", "n": "106", "xml_id": "ch106", "head": "..."}
  ]
}
```

### 5.2 Edition refs row

The indexer MUST write at most one edition refs row per entry:
- `entry_refs.ref_type = 'edition'`
- `entry_refs.payload` JSON schema:

```json
{
  "edition": "Kühn XI–XII",
  "start": {"pb": "XI.123", "lb": "4"},
  "end":   {"pb": "XI.124", "lb": "2"},
  "events": [
    {"kind": "pb", "n": "XI.123", "offset": 0},
    {"kind": "lb", "n": "4", "offset": 0}
  ]
}
```

`events` MAY be omitted in production rows if storage size is a concern, but MUST be available in fixtures/tests.

## 6. Formatting rules (app)

The app MUST render citations deterministically.

### 6.1 Structure ref formatting

`formatStructureRef(path)` SHOULD:
- join the `n` values in order, prefixed by recognized types if required by style
- fall back to `head` text if numeric `n` is missing

### 6.2 Edition ref formatting

`formatEditionRef(edition_payload)` MUST support:

1) Page+line range
- Example output style: `Kühn XI.123.4–XI.124.2`

2) Page range only
- Example output style: `Wellmann 1.7–1.8`

If an edition uses “page-range-only” (no line breaks in TEI):
- the renderer MUST NOT invent line numbers

### 6.3 Combined citation

`formatCombined(structure, edition)` SHOULD render:
- structure ref first
- followed by edition ref in parentheses, or another consistent delimiter

Example: `6.1.1 (Kühn XI.123.4–XI.124.2)`

## 7. Test fixtures

Fixtures MUST cover:
- structure paths with multiple levels
- entries spanning multiple pb milestones
- entries with pb-only (no lb) for “page-range-only” editions

Recommended fixture layout:
- `tests/fixtures/citations/<case>.xml`
- `tests/fixtures/citations/<case>.expected.json`

## 8. Acceptance criteria

C-04 is satisfied when:
- citation fixtures pass
- edition milestones have correct offsets into `reading_text`
- formatting functions produce stable output across environments

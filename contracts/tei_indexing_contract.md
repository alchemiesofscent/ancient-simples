# TEI Indexing Contract (C-01)

Version: 1.0
Status: Draft (normative for TEI-first v1)

## 1. Purpose

This contract defines how the Ancient Simples TEI indexer MUST transform canonical TEI editions into deterministic, rebuildable database rows.

TEI editions are canonical for:
- segment boundaries (“entries”)
- Greek reading text shown in the app
- citations (structure hierarchy + edition page/line refs)

The database stores:
- extracted reading text (rebuildable cache)
- tokens and offsets (rebuildable cache)
- citation refs (rebuildable cache)
- editorial layers (translations, lemma linking, assertions) that can become stale when TEI changes

## 2. Normative language

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as described in RFC 2119.

## 3. Definitions

TEI document
: A single TEI XML file produced by the CMG pipeline.

TEI doc id (`tei_doc_id`)
: Stable identifier for a TEI document, defined by project configuration.

Segment
: A TEI node selected as one entry for indexing.

TEI segment id (`tei_segment_id`)
: The value of the segment node’s `@xml:id`.

Canonical entry key
: The pair `(tei_doc_id, tei_segment_id)`.

Display entry id
: URL-safe display id computed as `{tei_doc_id}~{tei_segment_id}`.

Reading text (`reading_text`)
: The human-readable Greek text for a segment after TEI construct resolution and NFC normalization, but before Ancient Simples normalization.

Deterministic
: Identical inputs produce identical outputs (content, hashes, ordering) independent of runtime.

## 4. Inputs and required provenance

A run is determined by:

1) TEI XML bytes (from the pinned CMG submodule checkout)
2) A validated TEI doc config YAML (schema: `config/tei_doc_config.schema.yaml`)
3) textutils versions:
   - `NORMALIZATION_VERSION` (C-02)
   - `TOKENIZER_VERSION` (C-03)
4) Indexer version identifier (git commit or semantic version)
5) CMG submodule commit hash

The indexer MUST write (3–5) into `import_runs`.

## 5. Segment selection and identity

### 5.1 Segment selection

Each TEI doc config MUST define a segment selector (XPath or equivalent).

Requirements:
- Selector MUST return at least 1 segment.
- Each selected segment MUST have an `@xml:id`.
- `@xml:id` values among selected segments MUST be unique.
- Segments MUST be processed in document order.

### 5.2 Entry identity

For each segment:
- `tei_segment_id = @xml:id`.
- `display_entry_id = tei_doc_id ~ tei_segment_id`.

The indexer MUST NOT use `#` in entry ids.

## 6. Reading stream extraction

### 6.1 General extraction steps

The indexer MUST produce `reading_text` by:

1) Traversing the segment subtree in document order.
2) Emitting text content subject to TEI construct rules (§6.2).
3) Normalizing whitespace:
   - collapse all whitespace runs to one U+0020 SPACE
   - trim leading/trailing spaces
4) Normalizing Unicode to NFC.

### 6.2 TEI construct resolution rules (normative)

The indexer MUST apply the following rules when emitting text:

| TEI construct | Required behavior in reading text |
|---|---|
| `<choice>` with `<reg>` and `<orig>` | emit `<reg>`; ignore `<orig>` |
| `<choice>` with `<expan>` and `<abbr>` | emit `<expan>`; ignore `<abbr>` |
| `<app>` with `<lem>` and `<rdg>` | emit `<lem>`; ignore `<rdg>` |
| `<pb>` and `<lb>` | emit nothing; record as edition refs only |
| `<note>`, `<add>`, `<del>` | omit from reading text |
| `<supplied>` | include its text content |
| `<gap>` | insert literal placeholder string `[...]` |

Fallback behavior:
- If preferred `<reg>`/`<expan>` is missing inside `<choice>`, the indexer MUST emit the first child element’s text and MUST emit a warning.
- If `<lem>` is missing inside `<app>`, the indexer MUST emit a warning and MAY fall back to the first `<rdg>`.

### 6.3 Gap placeholder spacing

If the placeholder `[...]` would abut letters/digits with no whitespace, the indexer MUST ensure spaces so tokens do not merge (e.g., `λέγει[...]ὅτι` becomes `λέγει [...] ὅτι`).

## 7. Citation extraction (normative link to C-04)

The indexer MUST extract per segment:

1) Structure refs derived from the segment’s structural ancestors (C-04).
2) Edition refs derived from `<pb>`/`<lb>` milestones encountered within the segment (C-04).

Edition refs MUST be recorded with offsets into `reading_text`.

## 8. Hashing and determinism

For each segment:

- `reading_text` MUST be NFC.
- `raw_hash = SHA-256(UTF-8(reading_text))`.
- `normalized_text = normalize(reading_text)` per C-02.
- `normalized_hash = SHA-256(UTF-8(normalized_text))`.

Determinism requirement:
- Given identical TEI bytes + identical configs + identical versions, the tuple
  `(reading_text, raw_hash, normalized_text, normalized_hash, refs, tokens)` MUST be identical for each canonical entry key.

## 9. Import semantics: upsert + deactivate unseen

Each indexer execution creates one `import_runs` row.

For each indexed TEI doc:

1) Upsert rows for all seen segments by `(tei_doc_id, tei_segment_id)`.
2) Set `tei_entries.last_import_run_id = this run` for seen segments.
3) For any previously-active segment of that `tei_doc_id` not seen in this run:
   - set `tei_entries.is_active = FALSE`
   - set `tei_entries.last_import_run_id = this run`

The indexer MUST NOT hard-delete segments.

## 10. Validation requirements

`validate_tei.py` MUST hard-fail on:
- invalid XML (parse errors)
- zero selected segments
- missing or duplicate `@xml:id` in selected segments
- empty `reading_text` after whitespace normalization (unless explicitly allowed in config)

It SHOULD warn on:
- missing preferred children in `<choice>`
- missing `<lem>` in `<app>`
- missing `<pb>`/`<lb>` where expected

## 11. Required test fixtures

Each TEI rule in §6.2 MUST have at least one fixture asserting:
- exact `reading_text`
- extracted edition refs (if applicable)

Recommended layout:
- `tests/fixtures/tei_rules/<rule_name>.xml`
- `tests/fixtures/tei_rules/<rule_name>.expected.json`

The expected JSON MUST minimally include:
- `reading_text`
- `edition_refs` (array, possibly empty)

### 11.1 Minimal illustrative fixtures

Choice reg/orig

```xml
<div xml:id="seg1">
  <p>λέγει <choice><orig>ψυχρὸς</orig><reg>ψυχρός</reg></choice>.</p>
</div>
```

Expected reading text:
- `λέγει ψυχρός.`

Gap placeholder

```xml
<div xml:id="seg2"><p>λέγει<gap reason="lost"/>ὅτι</p></div>
```

Expected reading text:
- `λέγει [...] ὅτι`

PB/LB refs only

```xml
<div xml:id="seg3"><p><pb n="XI.123"/><lb n="4"/>λέγει ψυχρός</p></div>
```

Expected:
- reading text: `λέγει ψυχρός`
- edition refs include pb XI.123 and lb 4 at offset 0 (exact encoding in C-04)

## 12. Acceptance criteria

C-01 is satisfied when:
- all TEI rule fixtures pass
- the same TEI doc indexed twice produces identical hashes and identical counts
- any change to displayed reading text changes `raw_hash`

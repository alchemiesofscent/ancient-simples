---
status: historical
owner: archive
---

# MVP_Description_TEI_First.md

---

product: Ancient Simples
document: MVP Description
version: 0.2
status: draft (pre-build)
date: 2026-02-02
----------------

## Purpose

Ancient Simples is an internal scholarly web application for creating, reviewing, and exporting structured knowledge about ancient simples across a TEI-based corpus.

The MVP is defined as the first buildable system that is stable under base-text revision and supports editorial work without duplicating or drifting from the edition text.

## Authority model

TEI is authoritative (read-only in the app) for:

* Greek base text content and ordering
* segment identifiers and segmentation boundaries
* citation structure and milestone placement (pb/lb/milestones where present)

SQL (Supabase/PostgreSQL) is authoritative (editable in the app) for:

* translations, versioning, review state
* lemma registry, lemma aliases, lemma relations
* entry↔lemma links
* annotations and structured assertions with evidence spans
* users/roles, audit logs, import run logs
* export artifacts and release metadata

SQL also stores derived projections (overwritten by the indexer) for:

* segment reading-text caches
* normalized Greek fields for search
* token streams and offsets for highlighting and anchoring
* derived citation ranges

## MVP capabilities

TEI indexing and projection

* ingest configured TEI documents into deterministic SQL projections for segments, citations, tokens, and search fields
* enforce validation gates and emit machine-readable run reports
* support re-indexing with idempotent upserts and predictable diffs

Segment workspace keyed by TEI identity

* stable segment pages keyed by TEI-derived identity
* recommended identifier strategy:

  * tei_doc_id identifies a TEI edition/document
  * tei_segment_id is the TEI @xml:id of a selected segment element
  * entry_id is a deterministic key derived from both (tei_doc_id#tei_segment_id)
* display read-only Greek from TEI-derived caches
* display citations as first-class UI elements:

  * structural refs (hierarchy-derived)
  * edition refs (pb/lb-derived where present)
* edit translations and editorial metadata stored in SQL

Token-span anchoring with drift safety

* create annotations anchored to token spans from the TEI-derived token stream
* anchors record the targeted segment hash and tokenization/normalization versions
* on TEI re-index, anchors become stale when the segment hash changes; content is retained and routed to review

Lemma registry and linking

* create and manage lemma identities with stable lemma_id values
* link segments to lemmata with relation types (main/variant/etc.)
* maintain lemma aliases for orthographic/inflectional/editorial variants

Comparative view (lemma-based)

* display segments linked to a lemma across works
* comparison unit is the segment; no word-level alignment or diff claims in MVP

Search and filtering

* fast search over normalized Greek caches and editorial fields
* enforce a single normalization policy shared by indexer and exports
* prefix search constraints are explicit and consistent (minimum query length, normalization behavior)

Exports

* structured exports (CSV/JSON) for translations, lemmata, lemma aliases, links, annotations, assertions
* TEI standoff export generated from SQL, referencing TEI segment/token anchors
* release artifacts include export version, content hash, and normalization/tokenizer version metadata

## Explicit non-goals

* TEI-native editing in the web app
* requirement to embed word tokens (<w>) inside TEI sources
* required token-level Greek↔English alignment
* morphology/lemmatization/BLAST-like alignment or true word-level diffs
* structural alignment claims across authors beyond lemma grouping

## Operational workflow

Base text workflow

* changes to Greek base text occur only by updating TEI via Git
* indexer refreshes SQL projections
* the app does not permit Greek edits

Editorial workflow

* translations, lemmata, links, annotations, assertions are edited in-app and stored in SQL
* review status and audit trail are enforced at the SQL layer
* exports package editorial work as structured files and TEI standoff artifacts

## Stability invariants

Segment identity is canonical and stable

* segment identifiers come from TEI and are used directly as SQL keys (no parallel segment identity scheme)

No base-text divergence

* Greek caches and token streams are derived and overwritten by the indexer only

Versioned anchoring

* anchored objects record segment hash and the normalization/tokenizer versions used to generate tokens/offsets
* stale review is mandatory when hashes diverge

## Definition of done for MVP

* deterministic indexing produces identical projections from identical TEI inputs
* segment workspace displays Greek, citations, and provenance; translation editing works with versioning and review states
* lemma linking supports cross-work comparison via lemma-based parallel view
* annotations/assertions persist through re-index; stale items are flagged and reviewable
* exports are schema-valid and include stable IDs and version metadata

---

# PRD_TEI_First_Ancient_Simples.md

---

product: Ancient Simples
document: Product Requirements Document (PRD)
version: 0.2
status: draft (pre-build)
date: 2026-02-02
----------------

## Product goal

Build an internal scholarly web application that enables editors to:

* browse TEI-derived Greek segments with reliable citations
* create and review translations
* link segments across works using a stable lemma registry
* add annotations and structured assertions anchored to evidence spans
* export datasets and TEI standoff packages for publication and interoperability

## Constraints

Runtime architecture

* single Next.js application
* Supabase/PostgreSQL for data and auth
* offline scripts allowed for indexing and exports
* no separate long-running backend service required for MVP

Governance

* TEI is authoritative for base text and citations
* SQL is authoritative for all editable and relational data
* derived projections are overwritten by the indexer and treated as rebuildable artifacts

## Users

Editors

* translate, link lemmata, create annotations/assertions, manage review states

Reviewers

* review and approve editorial work; manage stale review queues after re-index

Read-only internal users

* browse, search, export subsets for research

## Domain objects

TEI document

* a TEI file representing an edition/document addressed as tei_doc_id

Segment (entry)

* a selected TEI element representing a citable unit
* identified by tei_segment_id (TEI @xml:id)
* addressed in SQL by entry_id derived from tei_doc_id and tei_segment_id

Citation

* structure ref derived from TEI hierarchy
* edition ref derived from milestones where present
* edition refs must preserve raw milestone identifiers; parsed numeric fields are optional and best-effort

Token

* derived from the segment reading stream with offsets
* used for highlighting and anchoring evidence spans

Lemma

* cross-work identity with stable lemma_id
* includes aliases and optional relationships

Annotation

* note anchored to a token span plus context windows
* includes a staleness state tied to segment hash changes

Assertion

* typed structured claim (JSON payload) with optional lemma scope and evidence anchors
* includes staleness state tied to segment hash changes

## In-scope product behavior

TEI intake and indexing

* ingest TEI documents to SQL projections for segments, citations, tokens, and search fields
* enforce validation gates and record import run reports
* idempotent indexing; stable identifiers; deterministic outputs

Segment workspace

* browse documents and segments in canonical order
* segment detail view shows:

  * Greek (read-only derived cache)
  * citations (structure refs and edition refs)
  * provenance (doc id, segment id, document hash, segment hash)
  * lemma links and aliases
  * translation editor and workflow status
  * annotations/assertions with evidence highlighting and stale status

Translation workflow

* translation CRUD per segment
* version history, review status, reviewer notes, audit trail
* editing never touches Greek caches

Lemma registry, linking, and aliases

* lemma CRUD (restricted roles)
* entry↔lemma links with relation types
* lemma aliases (orthographic/inflectional/editorial/synonym categories)
* alias lookup supports downstream matching and internal search/filtering

Lemma-based comparative view

* list all segments linked to a lemma across works
* show Greek + translation + citations side-by-side
* sorting by work order and optionally by citation refs
* no word-level alignment claims in MVP

Annotation and assertion system

* token-span selection UI for evidence
* anchors stored as token indices plus context windows and quote caches
* anchored objects record:

  * entry_id
  * tei_segment_hash
  * token start/end indices
  * quote and prefix/suffix contexts
  * normalization/tokenizer version identifiers
* stale review queue surfaces items whose segment hash no longer matches current projections

Search and filtering

* normalized Greek search based on a documented, versioned normalization policy
* prefix matching constraints are explicit and enforced in UI (minimum query length)
* translation and note text search supported with basic filtering
* filtering by doc/work, lemma, translation status, annotation/assertion presence, stale state

Exports

* structured exports (CSV/JSON) from SQL-owned editorial tables and their links to segments
* TEI standoff export that references TEI anchors without mutating TEI sources
* export artifacts include:

  * export version
  * generated timestamp
  * normalization/tokenizer versions
  * content hash
* exports must be schema-validated in CI

## Out of scope

* TEI editing in the app
* requirement to add <w> tokens into TEI
* token-level Greek↔English alignment as a requirement
* morphology, automated lemmatization, transliteration, or fuzzy matching beyond the defined normalization policy
* public API or public site

## Functional requirements

Data governance and validation

* per-document configuration defines segmentation selector, ignore rules, milestone rules, and structure-ref extraction
* missing or duplicate segment IDs are hard errors
* milestone absence is a warning; citations may be partially populated
* import runs produce machine-readable reports suitable for CI and audit

Citations model requirements

* edition refs store raw milestone identifiers (page_raw/line_raw or equivalent)
* parsed numeric fields are optional and must not be required for correctness
* citation rows carry a ref_system or edition dimension to avoid hard-coding a single scheme

Anchoring model requirements

* token indices are required for anchoring and highlighting
* context windows are required for stable re-anchoring and review workflows
* character-offset-only anchors are not sufficient

Derived field ownership

* derived projections (Greek caches, tokens, entry_refs) are indexer-owned
* application roles must not modify derived fields directly

## Non-functional requirements

Determinism

* identical TEI input bytes and config yield identical projections (hashes, tokens, citations)

Performance

* segment browsing and lemma-parallel view must remain interactive on the MVP corpus

Reliability

* re-index never deletes editorial data; stale flags and review queues are the mechanism

Security

* role-based write controls
* indexer uses elevated credentials; editors write only to SQL-owned tables

Auditability

* import runs logged
* editorial edits carry user and timestamp metadata

## Delivery plan

Foundation phase

* contracts, config format, schema migrations, normalization/tokenizer implementation, CI gates

Indexing phase

* validator and deterministic indexer with dry-run reporting
* populate projections from TEI for the initial corpus

Editorial phase

* segment workspace UI, translation workflow, lemma registry/linking/aliases, lemma-parallel view

Anchoring phase

* token selection UI, annotation/assertion CRUD, stale review workflow

Export phase

* research exports, lemma package export, entry↔lemma link export, TEI standoff export

## Work packages (issue-ready)

WP-Contracts

* TEI indexing contract, citation interpretation rules, anchoring model contract, export contract

WP-Database

* TEI provenance tables, segments, citations, tokens, staleness fields, import runs, lemma aliases

WP-Textutils

* shared normalization/tokenization library with version identifiers and determinism tests

WP-Indexer

* TEI validator, deterministic indexer, deletion-to-deprecation handling, staleness marking

WP-App-Core

* segment browser/detail, translation workflow, lemma registry/linking/aliases, lemma-parallel view

WP-App-Anchoring

* token-span evidence selection, annotation/assertion UI, stale review queue

WP-Exports

* schema-valid exports, versioned artifacts, TEI standoff export

WP-Ops

* CI gates, runbooks, release procedures for exports

---

# Technical_Spec_TEI_First_Indexer_And_App.md

---

product: Ancient Simples
document: Technical Specification
version: 0.2
status: draft (pre-build)
date: 2026-02-02
----------------

## System shape

TEI corpus

* canonical base text, segmentation IDs, and milestones
* managed in Git; changes represent the only base-text edit pathway

Offline pipeline

* validator enforces TEI ingestion contract
* indexer projects TEI into SQL tables for segments, citations, tokens, and search fields
* export tooling produces versioned bundles and TEI standoff packages

Web application

* Next.js reads from projections and editorial tables in Supabase
* writes restricted to SQL-owned editorial tables
* derived projections are not editable via the app

## Identity and provenance

Document identity

* tei_doc_id identifies one TEI document/edition

Segment identity

* tei_segment_id is the TEI @xml:id of the selected segment element
* entry_id is deterministic and derived:

  * entry_id = tei_doc_id + "#" + tei_segment_id

Provenance hashes

* tei_version_hash is a hash of TEI file bytes
* tei_segment_hash is a hash of the segment reading stream bytes

Version identifiers

* normalization_version and tokenizer_version are explicit and included in:

  * import run reports
  * anchored records
  * export manifests

## Segmentation contract

Segment selection

* per-document config defines the selector that yields segments
* selector must yield at least one segment
* every selected segment must have @xml:id
* duplicate segment IDs within a document are hard errors

Ordering

* ordering_key is deterministic and derived from document order
* ordering_key must be sortable and stable across runs

Structure refs

* derived from ancestor hierarchy (book/chapter/section @n values where present)
* stored as structure_ref JSON for query ergonomics
* also stored as a stable string ref_value for display and exports

## Reading stream extraction contract

Reading stream is normative

* the reading stream is the single canonical extracted text used for:

  * segment Greek cache
  * tokenization and offsets
  * normalized Greek fields
  * search

Ignored content is explicit

* ignore_xpath rules in config exclude apparatus/footnotes from the reading stream
* ignored content is excluded consistently from cache text, tokens, and citation scanning

Whitespace and de-hyphenation

* whitespace normalization rules are deterministic and documented
* de-hyphenation is conservative and deterministic; rule changes require version bumps and re-index

Diplomatic stream is optional

* may be added later for display or QA
* is not used for anchors, tokens, or search in MVP

## Citation extraction contract

Milestones

* pb/lb/milestone elements are scanned within the same extraction frame as the reading stream (ignored nodes excluded)

Edition references store raw identifiers

* page_raw and line_raw store milestone values as text
* parsed numeric fields are optional and best-effort:

  * page_num, line_num may be populated only when safe

Reference system dimension

* citations include a ref_system or edition_id dimension to avoid hard-coding one interpretation
* tei_doc_id alone is not assumed sufficient to disambiguate citation schemes

## Database schema requirements

TEI provenance

* tei_docs table stores tei_doc_id, source_path, tei_version_hash, ingested timestamps, status

Segments

* entries table stores entry_id, tei_doc_id, tei_segment_id, tei_segment_hash, ordering_key, structure_ref
* entries stores derived caches:

  * entry_gr and entry_gr_normalized
* entries supports deprecation:

  * deprecated flag for segments removed from current TEI selection

Citations

* entry_refs table stores:

  * entry_id, ref_type, ref_value
  * ref_system or edition_id
  * page_raw/line_raw and optional page_num/line_num
* uniqueness constraints prevent duplicate refs per entry/ref_system/ref_type/ref_value

Tokens

* tokens table stores:

  * entry_id, tei_segment_hash, token_idx
  * form, form_normalized
  * char_start/char_end offsets into the reading stream
  * token_type
* primary key includes (entry_id, tei_segment_hash, token_idx)

Editorial tables

* translations are SQL-owned with versioning and workflow state
* lemmata are SQL-owned with stable lemma_id
* lemma_aliases are SQL-owned and indexed for lookup
* entry_lemmata is SQL-owned
* annotations/assertions are SQL-owned with:

  * entry_id
  * tei_segment_hash (target)
  * token start/end indices
  * quote cache and prefix/suffix contexts
  * normalization/tokenizer version identifiers
  * stale flag and stale_reason

Observability

* import_runs stores run status, counts, warnings/errors, and a JSON report blob

## Derived-field ownership and access control

Indexer-owned projections

* entries.entry_gr and entries.entry_gr_normalized
* tokens rows
* entry_refs rows

Access control requirement

* editors and app runtime must not be able to modify indexer-owned projections through normal credentials
* the indexer runs with elevated credentials and is the only writer for projections
* enforce via Supabase RLS and/or separate service-role usage patterns

## Shared normalization/tokenization library

Single source of truth

* normalization and tokenization functions must be implemented once and reused by:

  * indexer
  * exporter
  * optional app-side utilities (or app must match documented behavior exactly)

Normalization policy

* Greek-aware lowercase
* sigma normalization
* diacritic stripping policy is explicit and stable
* iota subscript handling is explicit and stable

Tokenization policy

* deterministic segmentation into tokens
* stable offsets relative to the reading stream
* token_type labels for words vs punctuation where useful for UI

Versioning

* normalization_version and tokenizer_version are constants in the shared library
* changing behavior requires version bump and a re-index

## Validator behavior

Hard errors

* TEI parse failure
* segment selector yields zero segments
* missing @xml:id on selected segments
* duplicate @xml:id among selected segments

Warnings

* missing milestones within a segment
* empty reading stream after ignoring configured nodes
* abnormal token count ranges (configurable thresholds)

Outputs

* machine-readable report suitable for CI consumption
* non-zero exit on hard errors

## Indexer behavior

Inputs

* per-document config specifying selector, ignore rules, milestone rules, and structure ref derivation
* database credentials
* optional dry-run mode and segment limit

Normative flow

* compute tei_version_hash and upsert tei_docs
* select segments and compute entry_id, ordering_key, structure_ref
* extract reading stream and compute tei_segment_hash
* overwrite derived caches and replace tokens and citation refs
* mark entries not present in a run as deprecated
* mark anchored editorial records stale when segment hash changes
* write import_runs report with counts, warnings, errors, and version metadata

Determinism

* identical TEI bytes and config must produce identical:

  * segment set and ordering_key
  * reading streams and tei_segment_hash values
  * token streams and offsets
  * derived citation refs

## Anchoring and staleness semantics

Anchor tuple

* entry_id
* tei_segment_hash
* start_token_idx and end_token_idx
* quote cache
* prefix_context and suffix_context (token windows)
* normalization_version and tokenizer_version

Staleness rule

* anchored objects become stale when stored tei_segment_hash differs from the current entry’s tei_segment_hash

Review workflow

* stale items remain visible and exportable
* stale review queue supports manual confirmation or re-anchoring

## Exports

Structured exports

* CSV/JSON exports for translations, lemma registry, lemma aliases, entry↔lemma links, annotations/assertions
* exports include stable IDs and anchor metadata

TEI standoff export

* generates TEI-compatible standoff referencing:

  * tei_doc_id
  * tei_segment_id
  * evidence spans (token indices and optional offsets)
* exports do not mutate TEI sources

Versioned release artifacts

* export bundles include:

  * export_version
  * generated_at
  * normalization_version and tokenizer_version
  * content hash
* schema validation is required in CI for each export format

## Test requirements

Determinism tests

* normalization and tokenization repeatability with fixed inputs
* indexer dry-run report stability on fixture TEI inputs

Drift tests

* controlled TEI change in one segment produces a segment hash change
* anchored records against the old hash are marked stale and retained

Schema validation tests

* exports validate against JSON schema definitions
* failures produce actionable error output

## Work packages (engineering plan)

WP-Contracts

* TEI ingestion contract, reading stream spec, citation extraction spec, anchor model spec, export schemas

WP-Database

* migrations implementing required tables, constraints, and access controls

WP-Textutils

* shared library for normalization/tokenization with versioning and tests

WP-Validator-Indexer

* validator, deterministic indexer, import run reporting, staleness marking

WP-App-Minimum

* segment browse/detail, translation workflow, lemma registry/linking/aliases, lemma-parallel view

WP-App-Anchors

* token-span selection UI, annotation/assertion workflows, stale review queue

WP-Exports

* structured exports, versioned artifacts, TEI standoff export tooling

WP-CI-Ops

* CI gates for tests, validator, dry-run index
* runbooks for re-indexing and release/export procedures

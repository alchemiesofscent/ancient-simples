# Work tree / WBS — Ancient Simples platform + Aëtius CMG corpus (TEI‑first linking build)

Plain-English summary of what we need to do and why:

We need to make TEI the reliable “citation spine” first, because every link, query result, annotation, and export must be able to point to stable identifiers and to both logical references (book/chapter/section) and physical references (volume/page/line). The Aëtius corpus is a good place to start because it already has a deterministic TEI pipeline and printed page/line anchors; it can serve as the first “compiler target” for the Simples indexer.

Once TEI is stable enough to index, we build a TEI indexer that projects TEI into SQL (Supabase) in a deterministic way: segments, citations, tokens, and normalized search fields. This makes the web app fast and gives us token-level anchors to attach evidence spans (without ever editing Greek in the app).

Then we build the editorial/linking layer: a lemma registry with stable lemma IDs, lemma aliases (for matching), entry↔lemma links, plus a minimal translation/commentary workflow. This is the minimum surface needed to “make linking happen” in a controlled and auditable way.

Finally, we add a semantic query layer that answers questions like: “all drugs that are 3rd degree hot,” “all plant roots,” “all instances of boiling,” and “all places where absinth shows up,” always returning full logical + physical references. This requires two things: curated structured assertions (for degrees of heat/cold and for part/process classifications) and derived mention indices (for fast “where does term X occur” across corpus), both tied back to TEI citations.

The query requirements you listed are part of the platform work (Ancient Simples), not just the Aëtius TEI production line. The Aëtius project produces better TEI and editorial inputs; the Simples platform provides the canonical queryability, evidence anchoring, and cross-author retrieval.

Notes on constraints and inherited decisions: the build remains a single Next.js app backed by Supabase/Postgres/Auth, with offline scripts allowed for indexing and exports; no separate backend service is required.  

---

## Where the “find all X … with full references” feature lives

The feature set (“3rd degree hot,” “plant roots,” “boiling,” “absinth occurrences,” always with logical + physical refs) belongs to Ancient Simples as a platform capability because it requires:

* a canonical relational store for assertions and query facets,
* joins across works/authors,
* consistent citation rendering and export behavior.

The Aëtius CMG corpus project contributes by producing high-fidelity TEI (pb/lb + CTS hierarchy) and by generating editorial signals (glossary and term instance logs) that can seed lemma aliases and suggestion queues.

This feature set is not “just search.” It is “facet query + evidence + citation,” so it must be backed by structured tables, not just free text.

Relevant upstream architectural patterns that support this include: references as first-class objects, normalized Greek search constraints, and annotation anchoring via token windows and context for standoff export compatibility. 

---

## Milestones (program-level)

M‑Foundation
Contracts, vocabularies, and schemas exist; TEI can be validated for the required invariants.

M‑Aetius‑Indexable
Aëtius TEI output is indexable into segments with stable xml:ids and usable pb/lb milestone metadata; at least one comparator slice is indexable too.

M‑Projection‑Layer
TEI indexer deterministically populates Supabase projections (segments, citations, tokens, normalized fields) and logs runs.

M‑Linking‑Minimum
Lemma registry + aliases + entry↔lemma links work end-to-end; “where does absinth show up” works at least via normalized token/alias matching.

M‑Facet‑Query
Curated assertions + derived mention indices support the four target query types, returning full logical + physical citations.

M‑Export‑Ready
Exports (CSV/JSON + TEI standoff) round-trip identifiers and evidence spans consistently.

M‑Ops‑Ready
CI gates and runbooks exist; re-index and stale review workflows are predictable.

---

# Detailed work tree / WBS

Conventions used below:

* Workstreams: TEI corpus production line (Aëtius), Simples platform, Linking & Query, Operations.
* Each leaf task is issueable and includes: deliverables, acceptance criteria, dependencies.
* IDs are stable.

Entities referenced once for clarity: Aëtius of Amida, Libri Medicinales, Galen, Oribasius, Dioscorides, Paul of Aegina, Text Encoding Initiative, Supabase, Vercel, Christine Salazar.

---

## Workstream A — Aëtius CMG corpus TEI production line (inputs to indexing)

Goal: produce deterministic, indexable TEI outputs with stable segment IDs and reliable pb/lb anchors, without relying on PDFs.

### WT‑A‑Contracts — TEI “indexability” contract for this corpus

Deliverables

* `docs/contracts/aetius_tei_indexability_contract.md` (corpus-specific addendum)
* Explicit definition of:

  * which TEI elements are “segments” for indexing,
  * required `xml:id` placement rules for those segments,
  * milestone expectations and how pb/lb identifiers should be interpreted.

Acceptance criteria

* Contract identifies exact segment selector(s) for Aëtius TEI output.
* Contract states which milestones must exist and what counts as “missing but tolerable.”

Dependencies

* none

### WT‑A‑Validator — Corpus validator that enforces indexability

Deliverables

* `scripts/validate_aetius_output_tei.py` (or equivalent in corpus repo)
* Reports hard errors vs warnings:

  * hard error if selected segment lacks `xml:id`,
  * hard error if duplicate ids within a document,
  * warnings for missing pb/lb coverage.

Acceptance criteria

* Validator fails on missing/duplicate segment ids.
* Validator produces machine-readable JSON report for CI consumption.

Dependencies

* WT‑A‑Contracts

### WT‑A‑SegmentIDs — Ensure selected segment elements have stable xml:ids

Deliverables

* Updated TEI transform step to ensure:

  * each indexable segment element carries stable `xml:id`,
  * ids remain stable across rebuilds.

Acceptance criteria

* Re-running the TEI build does not renumber segment ids.
* Segment IDs remain stable even when text corrections occur within a segment.

Dependencies

* WT‑A‑Contracts, WT‑A‑Validator

### WT‑A‑Milestones — Standardize pb/lb representation for physical references

Deliverables

* Confirm pb/lb in `tei/output/`:

  * `pb` carries `ed`, raw `n` (e.g., `vol.page`), and `xml:id`,
  * `lb` carries raw `n` and `xml:id`,
  * line numbers reset semantics are documented.

Acceptance criteria

* Physical citation extraction can always return “raw” (text) page/line identifiers; numeric parsing is best-effort only.

Dependencies

* WT‑A‑Contracts, WT‑A‑Validator

### WT‑A‑ComparatorSlice — Indexable comparator subset for cross-author linking tests

Deliverables

* Choose one “small but representative” slice from one comparator work (e.g., a subset of Galen SMT or Oribasius) and ensure:

  * segment ids exist at the chosen granularity,
  * pb/lb and structure are present enough to test citations.

Acceptance criteria

* At least two TEI docs (Aëtius + comparator) can be indexed end-to-end in the platform.

Dependencies

* WT‑A‑Validator, WT‑A‑SegmentIDs, WT‑A‑Milestones

---

## Workstream S — Ancient Simples platform: TEI‑first indexing + editorial layer

Goal: ingest TEI into SQL projections and provide an editing + linking surface without TEI editing in-app. The stack remains Next.js + Supabase with offline scripts; no separate backend service.  

### WT‑S‑Contracts — Platform contracts (shared across corpora)

Deliverables

* `docs/contracts/tei_indexing_contract.md` (platform-level)
* `docs/contracts/citation_contract.md` (raw + parsed, ref_system dimension)
* `docs/contracts/normalization_contract.md` (versioned behavior)
* `docs/contracts/anchoring_contract.md` (token indices + context windows)
* `docs/contracts/export_contract.md` (schema + versioning rules)

Acceptance criteria

* Contracts explicitly define:

  * segment identity model and stable key scheme,
  * “reading stream” extraction rules,
  * citation storage model (raw milestone ids + optional numeric),
  * tokenization and normalization versioning,
  * anchored evidence semantics and staleness behavior.

Dependencies

* none

### WT‑S‑Schema‑TEI — Supabase schema for TEI provenance and projections

Deliverables

* Supabase migrations to create/update:

  * `tei_docs` (doc id, source path, version hash)
  * `entries` (entry_id derived from TEI identity; structure_ref; derived Greek cache; deprecated flag)
  * `entry_refs` (structure + edition refs; raw and optional parsed fields; ref_system/edition dimension)
  * `tokens` (derived token stream with offsets; keyed by entry_id + segment hash)
  * `import_runs` (observability)

Acceptance criteria

* Migrations apply cleanly to a fresh DB.
* References are stored as first-class rows (not embedded as page_start/page_end on entry records).  

Dependencies

* WT‑S‑Contracts

### WT‑S‑Schema‑Editorial — Editorial schema (translations, lemmata, links, annotations, assertions)

Deliverables

* Migrations for:

  * `translations` (versioned + workflow)
  * `lemmata` (stable lemma_id)
  * `lemma_aliases` (alias surface forms for matching)
  * `entry_lemmata` (segment-level “aboutness” links)
  * `annotations` (token-span anchors + context + staleness)
  * `assertions` (typed payload + evidence spans + staleness)

Acceptance criteria

* Anchored tables store token indices and context windows (quote + prefix/suffix) per anchoring guidance. 
* Derived projections are indexer-owned; editorial tables are app-owned.

Dependencies

* WT‑S‑Schema‑TEI, WT‑S‑Contracts

### WT‑S‑Textutils — Shared normalization/tokenization library (single source of truth)

Deliverables

* `packages/textutils/` (Python) or equivalent shared module
* Version constants:

  * `NORMALIZATION_VERSION`
  * `TOKENIZER_VERSION`
* Deterministic:

  * normalization for search/match
  * tokenization returning offsets into the reading stream

Acceptance criteria

* Unit tests prove determinism.
* Indexer and exporter both import and use the same library.

Dependencies

* WT‑S‑Contracts

### WT‑S‑Indexer — Deterministic TEI indexer (offline)

Deliverables

* `scripts/index_tei.py` (or equivalent)
* `scripts/validate_tei.py` (platform validator)
* `scripts/validate_index_output.py` (post-run regression checks)

Acceptance criteria

* Indexing the same TEI twice yields identical:

  * entry ids, segment hashes, tokens (forms + offsets), and refs.
* Indexer stores both:

  * logical refs (structure) and physical refs (edition pb/lb) when available.
* Indexer ignores overlays not explicitly enabled.

Dependencies

* WT‑S‑Schema‑TEI, WT‑S‑Textutils, WT‑S‑Contracts, WT‑A‑Validator (for corpus-level readiness)

### WT‑S‑RLS — Access control and “derived field ownership”

Deliverables

* Supabase RLS policies that ensure:

  * editors cannot update derived projections (Greek caches, tokens, entry_refs),
  * indexer/service role can update projections,
  * editors can update translations, lemma links, annotations/assertions (SQL-owned).

Acceptance criteria

* Attempted writes to indexer-owned tables/columns from editor role fail.

Dependencies

* WT‑S‑Schema‑TEI, WT‑S‑Schema‑Editorial

### WT‑S‑App‑Core — Minimal UI for browsing and editing (linking-first)

Deliverables

* Next.js routes and components:

  * document/segment browsing
  * segment detail page showing Greek (read-only), citations, provenance
  * translation editor with versioning + status
  * lemma linking panel (entry↔lemma)
  * basic search (normalized prefix matching + filters)

Acceptance criteria

* Greek is always read-only in the UI (never edited in SQL).
* Search follows the normalization/prefix constraints (≥3 normalized chars) and clearly communicates the limitation. 

Dependencies

* WT‑S‑Indexer, WT‑S‑Schema‑Editorial, WT‑S‑RLS

### WT‑S‑App‑Annotations — Token-span annotation creation and stale review queue

Deliverables

* Token rendering/selection UI for Greek
* Annotation CRUD storing:

  * start/end token indices,
  * quote cache,
  * context windows,
  * anchored segment hash,
  * stale flag workflow
* Stale review queue page

Acceptance criteria

* An annotation survives re-index; if hash changes, it becomes stale and visible for review (not lost). 

Dependencies

* WT‑S‑App‑Core, WT‑S‑Indexer, WT‑S‑Schema‑Editorial

### WT‑S‑Exports‑Core — Basic export tooling (platform-native)

Deliverables

* Export scripts and/or Server Actions:

  * CSV/JSON exports for translations, lemmata, lemma_aliases, entry_lemmata, annotations, assertions
  * versioned export metadata: export_version, generated_at, normalization/tokenizer versions, content hash

Acceptance criteria

* Exports include entry_id + both logical and physical citations for each record that references a segment.

Dependencies

* WT‑S‑Schema‑Editorial, WT‑S‑Schema‑TEI, WT‑S‑Textutils

---

## Workstream L — Linking + semantic query layer (answers the “find all X…” requirement)

Goal: enable facet-style queries over lemma identity, properties, parts, processes, and term occurrences, returning full logical + physical references.

This workstream is the direct home of the four query examples.

### WT‑L‑FacetModel — Define the queryable “facet” model

Deliverables

* `docs/contracts/facet_query_contract.md` defining:

  * what counts as a “drug/substance” (lemma_id) vs “mention” vs “process”
  * required evidence fields (token spans + citations)
  * what is curated vs derived
  * the minimal vocabularies required:

    * qualities (hot/cold degrees),
    * parts (root, leaf, seed, etc.),
    * processes/actions (boil, roast, grind, mix, etc.)

Acceptance criteria

* Contract explicitly maps each target query to data sources and query patterns:

  * “3rd degree hot” → curated assertions
  * “plant roots” → curated part assertions and/or controlled part links
  * “boiling” → curated or lexicon-derived process mentions with evidence
  * “absinth shows up” → lemma mention index derived from aliases + tokens, plus optional curated confirmations

Dependencies

* WT‑S‑Contracts

### WT‑L‑Vocab‑Qualities — Controlled vocabulary for degrees (hot/cold)

Deliverables

* Tables:

  * `quality_vocab` (e.g., hot, cold, dry, wet; with degree scale rules)
  * optional `quality_degree_scale` (defines valid degrees and semantics)
* UI/editor support for selecting degree values

Acceptance criteria

* Degrees are constrained (e.g., 1–4); values validated server-side.

Dependencies

* WT‑L‑FacetModel, WT‑S‑Schema‑Editorial

### WT‑L‑Vocab‑Parts — Expand and stabilize parts vocabulary (root, etc.)

Deliverables

* `parts` table (if not already present) and stable identifiers
* mapping rules for “part of plant/mineral/animal” as needed

Acceptance criteria

* “root” is a first-class part value; parts can be attached with evidence to a segment or lemma occurrence.

Dependencies

* WT‑L‑FacetModel, WT‑S‑Schema‑Editorial
  Notes: prior CSV-first specs included parts vocab; this becomes SQL-first and TEI-independent. 

### WT‑L‑Vocab‑Processes — Controlled process/action registry

Deliverables

* `process_vocab` table:

  * canonical action keys (boil, decoct, roast, grind…)
  * optional Greek cue lexemes for suggestion generation
* Minimal UI to attach a process to an evidence span (assertion)

Acceptance criteria

* “boil” exists as a canonical process; attaching a process requires an evidence span.

Dependencies

* WT‑L‑FacetModel, WT‑S‑Schema‑Editorial

### WT‑L‑Assertions‑UI — Curated assertions entry with evidence and citations

Deliverables

* UI module to create assertions with:

  * assertion_type (quality / part / process / other)
  * payload (structured, validated)
  * linked lemma_id where applicable
  * evidence token span
  * anchored segment hash
  * workflow status (draft/reviewed)

Acceptance criteria

* An editor can record:

  * “absinth is hot degree 3” with evidence span and full citations,
  * “root” as a part with evidence span,
  * “boiling” as a process with evidence span.

Dependencies

* WT‑S‑App‑Core, WT‑S‑App‑Annotations, WT‑L‑Vocab‑Qualities, WT‑L‑Vocab‑Parts, WT‑L‑Vocab‑Processes

### WT‑L‑MentionIndex — Derived lemma mention index (answers “where does absinth show up”)

Deliverables

* `lemma_aliases` populated for key substances (starting with absinth)
* Derived table or materialized view:

  * `lemma_mentions` (entry_id, lemma_id, token_start/end, match_type, segment_hash)
* Offline rebuild script that:

  * matches aliases against token stream,
  * emits occurrences with evidence spans,
  * is rebuildable and versioned.

Acceptance criteria

* Query “absinth occurrences” returns all matched mentions with citations.
* Rebuild is deterministic given the same tokens and alias list.

Dependencies

* WT‑S‑Indexer, WT‑S‑Schema‑Editorial, WT‑S‑Textutils, WT‑L‑FacetModel

### WT‑L‑QueryUI — Faceted query page with full citations

Deliverables

* UI pages that support at minimum:

  * filter by quality degree (e.g., hot=3)
  * filter by part (root)
  * filter by process (boil)
  * filter by lemma (absinth) using both:

    * entry↔lemma “aboutness” links
    * lemma_mentions occurrence index
* Each result row displays:

  * lemma/term label
  * snippet with highlighted evidence
  * logical reference (book/chapter/section)
  * physical reference (edition system: volume/page/line)

Acceptance criteria

* Each of the four example queries returns:

  * a list of results,
  * citations in both logical and physical forms,
  * exportable results (CSV/JSON).

Dependencies

* WT‑L‑Assertions‑UI, WT‑L‑MentionIndex, WT‑S‑Schema‑TEI, WT‑S‑App‑Core

### WT‑L‑Citations‑Rendering — Canonical citation formatter

Deliverables

* A single citation formatting utility shared by:

  * UI,
  * exports,
  * API/server actions.
* Handles:

  * raw milestone ids (page_raw/line_raw)
  * optional parsed numeric fields
  * ref_system labels (e.g., “Olivieri CMG 8.1”)

Acceptance criteria

* No query result is emitted without both:

  * logical ref (structure), and
  * physical ref (edition pb/lb) when present in TEI.
* If physical is missing in TEI, UI labels it explicitly as “not available for this edition” rather than leaving it blank.

Dependencies

* WT‑S‑Schema‑TEI, WT‑S‑Indexer, WT‑S‑App‑Core

### WT‑L‑QA‑Queries — Query regression tests

Deliverables

* Integration tests that assert:

  * “hot degree 3” returns expected seeded fixtures
  * “root” returns expected fixtures
  * “boil” returns expected fixtures
  * “absinth” returns expected fixtures via mention index
* Test fixtures include both structure refs and pb/lb refs.

Acceptance criteria

* CI fails if any query path returns results missing required citations.

Dependencies

* WT‑L‑QueryUI, WT‑L‑MentionIndex, WT‑S‑Indexer

---

## Workstream O — Operations, CI, runbooks, and data governance

Goal: make this a repeatable, auditable system under re-indexing and ongoing TEI corrections.

### WT‑O‑CI — Minimal CI gates

Deliverables

* CI workflows that run:

  * unit tests (textutils determinism)
  * TEI validation on fixture subset
  * indexer dry-run determinism report check
  * export schema validation

Acceptance criteria

* PR cannot merge if validator or determinism tests fail.

Dependencies

* WT‑S‑Textutils, WT‑S‑Indexer, WT‑A‑Validator

### WT‑O‑Runbooks — Runbooks for re-indexing, stale review, and releases

Deliverables

* `docs/runbooks/indexing.md`
* `docs/runbooks/stale_review.md`
* `docs/runbooks/export_releases.md`

Acceptance criteria

* Runbooks define:

  * how to add a new TEI doc/config,
  * how to re-index safely,
  * how stale items are reviewed,
  * how exports are versioned and pinned.

Dependencies

* WT‑S‑Indexer, WT‑S‑Exports‑Core, WT‑L‑Citations‑Rendering

### WT‑O‑Telemetry — Import runs and quality dashboards

Deliverables

* Import run report storage and simple dashboards/queries for:

  * segment counts
  * missing milestone coverage warnings
  * stale item counts after re-index
  * mention index rebuild counts

Acceptance criteria

* After any index run, the team can see what changed and why.

Dependencies

* WT‑S‑Schema‑TEI, WT‑S‑Indexer, WT‑L‑MentionIndex

---

# Mapping the four target queries to implementation units

“All drugs that are 3rd degree hot”

* Data source: curated quality assertions (lemma-scoped or evidence-scoped).
* Work items: WT‑L‑Vocab‑Qualities, WT‑L‑Assertions‑UI, WT‑L‑QueryUI, WT‑L‑Citations‑Rendering.

“All plant roots”

* Data source: part assertions and/or part links with evidence spans.
* Work items: WT‑L‑Vocab‑Parts, WT‑L‑Assertions‑UI, WT‑L‑QueryUI, WT‑L‑Citations‑Rendering.

“All instances of boiling”

* Data source: process assertions (curated), optionally supplemented by lexicon-derived mention suggestions.
* Work items: WT‑L‑Vocab‑Processes, WT‑L‑Assertions‑UI, (optional suggestion builder as part of WT‑L‑MentionIndex pattern), WT‑L‑QueryUI.

“All places where absinth shows up”

* Data source: derived lemma mention index from aliases + token stream; optionally include entry↔lemma “aboutness.”
* Work items: WT‑L‑MentionIndex, WT‑L‑QueryUI, WT‑L‑Citations‑Rendering.

---

# Suggested critical path (linking-first)

Foundation contracts and schema must land before meaningful linking work, because IDs, citations, and token anchors govern everything downstream.

Critical path sequence

* WT‑A‑Contracts → WT‑A‑Validator → WT‑A‑SegmentIDs → WT‑A‑Milestones → WT‑A‑ComparatorSlice
* WT‑S‑Contracts → WT‑S‑Schema‑TEI → WT‑S‑Textutils → WT‑S‑Indexer → WT‑S‑RLS
* WT‑S‑Schema‑Editorial → WT‑S‑App‑Core
* WT‑L‑FacetModel → WT‑L‑Vocab‑Qualities/Parts/Processes → WT‑L‑Assertions‑UI
* WT‑L‑MentionIndex → WT‑L‑QueryUI → WT‑L‑Citations‑Rendering → WT‑L‑QA‑Queries
* WT‑S‑Exports‑Core → WT‑O‑CI → WT‑O‑Runbooks → WT‑O‑Telemetry

This ordering also respects the “no separate backend service” constraint and keeps ETL in offline scripts.  

---

# Implementation note: “complete” vs “initial linking build”

This WBS is complete in the sense that it spans: TEI production readiness → deterministic indexing → linking/editorial workflows → semantic query with full citations → exports → ops/CI.

If the immediate goal is “make linking happen quickly,” you can cut scope by delaying:

* full translation/commentary UX polish beyond basic versioned text,
* TEI standoff export beyond a minimal proof,
* automated suggestion pipelines for processes (boil) beyond curated assertions.

Do not cut:

* stable segment IDs,
* raw milestone capture for citations,
* token offsets + context anchoring,
* lemma aliases + mention index (for term occurrences like absinth),
  because those are prerequisites for reliable cross-author linking and for your four query types.

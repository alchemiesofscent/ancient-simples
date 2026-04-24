---
status: historical
owner: archive
---

# Overlap and sequencing assessment: Aëtius CMG Digital Corpus vs Ancient Simples (TEI‑first)

status: preliminary technical evaluation (pre-build)
date: 2026-02-02

## Overlap (shared primitives)

Shared canonical substrate: TEI + milestone citations

* Both efforts depend on TEI editions as the authoritative base text and as the citation spine. In the Simples stack, this replaces the earlier CSV-first intake posture and makes the TEI indexer the primary ingest path for Greek and references.  
* The Aëtius corpus already encodes page/line anchors (`pb`/`lb`) and a CTS-like structural hierarchy; these map directly onto the “references are first-class objects” model used by the Simples data design.  

Shared linking requirement: lemma identity as the pivot

* Both efforts require a stable lemma registry to enable cross-author linking and comparative views. The Simples comparative design aligns entries at lemma level (not word-diff) and expects many-to-many linking via a junction table.  

Shared anchoring requirement: tokens + context, not offsets alone

* The Aëtius workflow wants stable citations and deterministic text segmentation to support chapter-by-chapter editing and commentary. Simples’ annotation system is explicitly designed around token windows and captured context, not character-offset-only anchoring, because text will change and drift must be reviewable. 

Shared operational posture: “pipeline + UI”, no backend services

* The Simples architecture commits to Next.js + Supabase with offline scripts for ETL/tokenization/indexing, and no separate backend service. A TEI-first ingest for Simples fits naturally into that same constraint set.  

## Overlap (deliverables that can be reused)

TEI outputs in `tei/output/` can be direct indexer inputs

* Your Aëtius TEI “output” stage is exactly the kind of canonical input the Simples TEI indexer should consume: stable IDs, stable milestones, deterministic build scripts.

Aëtius linking artifacts can seed Simples lemma aliasing

* `data/glossary.tsv` and `data/term_instances.ndjson` are structurally similar to the “lemma aliases / surface-form evidence” problem Simples must solve for reliable linking. In Simples terms, these become candidates for `lemma_aliases` and for training/QA of matching heuristics.

Patch-based chapter workflow can become an external authoring tool

* The Aëtius “apply patch JSON” workflow is compatible with Simples if treated as an *offline authoring interface* that ultimately writes into SQL-owned translation/commentary tables (or produces importable deltas). It should not be allowed to mutate TEI base text (consistent with TEI-read-only boundary).

## Minimal mismatch / integration gaps to resolve early

Segment identifiers may be missing at the level Simples needs

* The Aëtius corpus description guarantees `pb`/`lb` have `xml:id`, and that CTS-compatible `div` hierarchy exists, but it does not explicitly guarantee that the *segment unit you want to index* (chapter/section/subsection) carries stable `xml:id`.
* A TEI-first Simples indexer typically needs stable `xml:id` on whichever elements are treated as “segments/entries” (e.g., `div[@type='textpart'][@subtype='section']` or comparable). Without those IDs, you either fail ingest (recommended) or you mint IDs (high risk of later drift).

Edition reference parsing should not assume integers

* Aëtius page markers use `n="vol.page"` and line markers reset per page; other corpora will have different `n` conventions. If Simples stores page/line as integers only, it will eventually break on non-numeric `n` values and multi-scheme citations. The citation layer should preserve raw milestone identifiers as text and parse numeric fields only when safely possible. This aligns with the prior “references as rows keyed by edition/ref_type” approach.  

Structural edge cases in other authors will still need to be confronted

* Your Aëtius notes already flag Oribasius and Paul structural issues. If the purpose of “Aëtius first” is to validate *linking across authors*, then Aëtius alone will not expose the hardest segmentation failures. It will validate the pipeline, but not the worst boundary cases.

Normalization must be identical across TEI pipeline, indexer, and linking logic

* Simples’ prior search/normalization constraints require strict, consistent Greek normalization rules across ETL, DB, and app. 
* The Aëtius corpus already normalizes glossary keys by stripping diacritics; that is directionally aligned, but it must be locked as a versioned normalization spec shared across all ingestion and linking steps (or you will get systematic false “unmatched terms”).

## Strategy evaluation: is “Aëtius first” a good move?

Aëtius-first is a good strategy if the objective is to validate the TEI spine and the linking workflow under realistic editorial pressure

* A corpus anchored by Aëtius of Amida is structurally suitable as an “integration anchor” because it is explicitly comparative (drawing from Galen, Oribasius, Dioscorides, Paul of Aegina), which forces you to exercise lemma identity and cross-document linking early rather than as a late-phase enhancement.
* The editorial workflow focus (revision of Christine Salazar’s translation, commentary discipline, text-critical notes) produces exactly the kind of SQL-owned editorial data (translation versions, annotation-like notes, assertions) that Simples is meant to host once the TEI projection exists.

Aëtius-first is a risky strategy if it is interpreted as “build an Aëtius-only system” before defining shared contracts

* If the Aëtius project invents identifiers, segmentation units, or linking file formats that do not align with the eventual Simples identity model (doc_id + segment xml:id + version/hash), integration will be an expensive translation step later.
* If “linking happens” using ad hoc surface-form matching without a stable lemma registry and alias policy, you will accumulate links that cannot be audited, merged, or exported consistently.

## Recommended approach (keeps Aëtius-first, reduces rework)

Treat the Aëtius project as the TEI production line; treat Simples as the linking and editorial platform

* Keep TEI build scripts, normalization, and anchor insertion in the Aëtius corpus repo (“TEI compiler”).
* Build Simples as the consumer that indexes TEI into SQL projections and provides UI for translation, lemma linking, and annotations. This aligns with the Simples architecture constraints and avoids introducing new runtime services.  

Start with a cross-author “minimal linking set,” not Aëtius alone

* Index Aëtius plus a small comparator slice (one book or a representative subset) from at least one of the primary sources used in comparisons (e.g., a subset of Galen SMT or Oribasius).
* This forces early resolution of: segmentation compatibility, citation representation, lemma ID policy, and alias matching across corpora.

Lock a shared contract before producing large volumes of links

* Segment identity contract: what TEI element is a segment, and what stable `xml:id` pattern is required.
* Citation contract: preserve raw pb/lb identifiers; store ref_system/edition dimension.
* Normalization/tokenization contract: versioned functions; changes require version bump and re-index.
* Link contract: link objects always reference lemma_id + entry_id, never “free-form strings.”

Use the Aëtius glossary and term-instance logs as *evidence*, not as canonical identities

* Convert high-confidence glossary keys into lemma aliases (candidates) and store provenance pointing back to evidence spans.
* Require that canonical lemma identities live in one place (SQL lemma registry), with controlled changes and versioned exports.

## Overlap summary (what you can count on)

High overlap

* TEI as canonical base text and citations
* deterministic pipeline concepts (validator + build scripts + reports)
* lemma linking as the cross-author backbone
* token/context anchoring model for durable notes under change

Moderate overlap

* chapter-by-chapter “patch” workflow (useful as external authoring tool; not necessarily the core app workflow)
* glossary + term-instance logs (useful as alias candidates and QA evidence)

Low overlap

* TEI normalization mechanics and edition-fidelity chores (these belong to the TEI production line, not the Simples app)
* author-specific structural edge cases (must be handled per doc, but should not be hard-coded in the app)

## Decision statement

Working Aëtius-first is a good strategy if it is treated as a pilot for the shared TEI spine and for cross-author lemma linking, and if it includes at least one comparator corpus early to validate linking and segmentation under real heterogeneity. It is not a good strategy if it becomes an Aëtius-only linking system that later must be reverse-fit into a different identity model.

If the near-term goal is “make linking happen,” the fastest safe path is: index Aëtius + one comparator slice into the same TEI-first projection layer, define lemma IDs and aliases once, then build links as SQL-owned objects keyed to stable TEI segment IDs.

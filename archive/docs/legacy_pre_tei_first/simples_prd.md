---
status: historical
owner: archive
---

# Ancient Simples Comparative Database
## Product Requirements & Delivery Plan

---

## 1. Executive Summary
Build an internal-facing scholarly web application that lets editors restructure, edit, annotate, and compare entries from Galen (*De simplicium medicamentorum* VI–XI), Oribasius (*Collectiones Medicae* 15), and Aetius (*Libri Medicinales* I–II). The MVP uses a single Next.js (App Router, TypeScript) deployment backed by Supabase (PostgreSQL + Auth). Next.js Server Actions provide all create/update flows; no separate Flask/FastAPI or generic backend service is part of scope. Data remains editable at all times, with annotation workflows and comparison views designed specifically for controlled, internal scholarly work.

---

## 2. Users & Pain Points
| Persona | Needs | Pain Points Today |
|---------|-------|-------------------|
| Lead editors (Sean + core researchers) | normalize legacy spreadsheets, edit translations & metadata, keep annotations stable as texts change | Spreadsheet macros are brittle, annotation offsets drift when text is revised |
| Collaborating scholars (invited domain experts) | suggest edits, add annotations with provenance, export slices for research | No shared environment with authentication; ad hoc files circulate |
| Future readers (phase 2+) | read-only browsing | No reliable comparative views yet |

---

## 3. Canonical Architecture (Authoritative)
- **Frontend + server logic:** Next.js 14+ App Router, TypeScript, Tailwind, shadcn/ui components.
- **Database & auth:** Supabase PostgreSQL with Row Level Security, Supabase Auth for email magic links.
- **Data access:** Supabase client for reads, Next.js Server Actions for writes/mutations to keep logic close to UI.
- **Batch tooling:** Offline Node/Python scripts allowed only for one-time ETL (e.g., CSV import from Excel) and bulk maintenance.
- **Deploy:** Vercel (Next.js) + Supabase project. CI deploy ensures migrations run in Supabase.

No Flask, FastAPI, generic REST API, or separate backend services ship in the MVP. All roadmap references inherit this constraint unless an explicit phase introduces a new service.

---

## 4. Scope Discipline
### MVP (Phase 1)
1. Import of curated CSVs (entries, lemmata, parts) into Supabase tables, with lemma relationships managed via junction tables.
2. Entry workspace (list + detail) with editable translation, metadata, and Supabase-backed history timestamps.
3. Annotation system anchored by token windows (selected quote + configurable prefix/suffix). Stored anchors survive text edits with automated re-anchoring attempts and a "needs review" flag when confidence drops.
4. Columnar comparative view that aligns entries by lemma_id; researchers pick base + comparison entries. No word-level diffing.
5. Search experience limited to prefix matching (≥3 normalized characters) over accent/breathing-stripped Greek plus direct text search over stored translation and lemma metadata. No morphology, lemmatization, or transliteration.
6. Authenticated access with edit roles only; no public API, no public site. Exports available as CSV/JSON downloads.

### Phase 2 (Not MVP, explicitly deferred)
- **Redactor View:** Heuristic, single-column overlay inspired by diffing but still driven by lemma alignment; explicitly *not* a definitive word-level diff.
- Real-time collaboration, public read-only portal, API endpoints, RDF/knowledge-graph layers.
- Automated BLAST-like alignment, TEI-native editing, or recipe/ingredient network visualizations.

### Explicitly Out of Scope (until after Phase 2)
- Real-time co-editing, shared cursors.
- Public API or webhook integrations.
- RDF triples/knowledge graphs.
- Automated lemmatization, morphology, transliteration, or fuzzy search beyond accent/breathing stripping.
- Word-level diff/BLAST comparisons in MVP.

---

## 5. Functional Requirements
### FR1. Data Intake & Governance
- **FR1.1** MVP ingests CSV exports (`entries.csv`, `lemmata.csv`, `parts.csv`) validated via diff-checks (row/word counts) and OpenRefine review before import.
- **FR1.2** `entries.csv` includes temporary `lemma_ids` column for import convenience, but canonical storage in Supabase uses `entry_lemmata` junction rows. Import scripts must split this column accordingly.
- **FR1.3** Supabase schema (entries, lemmata, parts, entry_lemmata, annotations, users) enforces referential integrity and stores timestamps for auditability.
- **FR1.4** Data remains editable; no "published and frozen" mode in MVP.
- **FR1.5** References are first-class objects: CTS URNs and edition-specific page/folio/column ranges live in `entry_references` rows (unique per entry + edition + ref_type). Entries themselves no longer carry page_start/page_end columns.

### FR2. Entry Workspace
- List view filters: source, lemma, book/chapter, translation status, presence of annotations, controlled categories.
- Detail view shows Greek text, translation editor, metadata panel, linked annotations, and Supabase-backed change timestamps.
- Editing uses Server Actions with optimistic UI and toast feedback.

### FR3. Translation Editing
- Rich text editor (TipTap or similar) scoped to standard formatting (italic, bold, footnote markers) and polytonic input helpers.
- Translation status workflow (`draft`, `in review`, `final`). Editors can re-open final translations; statuses log user + timestamp.

### FR4. Annotation System
- Anchoring combines selected quote plus ±N-token context (tokenization stored in Supabase). Tokenization runs server-side, regenerates on every Greek text save, and persists per entry for downstream anchoring.
- Re-anchoring logic retries after each edit; failed matches automatically mark annotation `needs_review` and surface in UI filters.
- Annotation record stores type/category, note body, references, and optional links to other entries.

### FR5. Comparative Features
- **MVP Comparative Table:** Column-based layout where users choose up to three entries sharing a lemma. Each column shows metadata summary, normalized word count, and text excerpt with manual notes. Emphasize entry-level comparison; no automated word-level diff or alignment claims.
- **Phase 2 Redactor View (Heuristic, Not MVP):** Concept retained for roadmap—single column highlighting retention/omission heuristics. All references must state it is heuristic, requires manual validation, and only arrives after MVP stability.

### FR6. Search & Filter
- Greek search uses normalization that strips accents and breathings only while avoiding morphology, lemmatization, or transliteration.
- Additional search facets over translation text, lemma metadata, annotation notes.
- Results highlight the limitation text ("normalized prefix matching only").

**Search contract:** Normalized Greek search relies on prefix matching only, requires at least three characters, and queries shorter than three characters intentionally return no results.

### FR7. Exports & TEI Transition
- CSV/JSON export endpoints for entries, lemmata, annotations.
- Provide a Next.js Server Action to generate TEI-ready packets: entries with token streams + annotation anchors to support future standoff TEI export (described in §9). MVP does **not** edit directly in TEI.

---

## 6. Non-Functional Requirements
- **Greek Text Support:** Full polytonic rendering, UTF-8 storage, normalization functions executed inside Supabase.
- **Performance:** Initial list load < 2s for 1.7k entries; search responses < 1s for indexed fields.
- **Reliability:** Nightly Supabase backups, manual export checkpoints prior to major schema changes.
- **Access Control:** Supabase Auth groups `editor`, `viewer`. No public anonymous access.
- **Auditability:** Supabase Row Level Security policies enforce per-user ownership; annotations and translations store `updated_by`.

---

## 7. Implementation Plan (12-Week Baseline)
| Phase | Weeks | Goals |
|-------|-------|-------|
| 0. Foundations | 1–2 | Supabase project, schema migrations, CSV diff-check + import scripts (Node/Claude CLI), baseline Next.js app shell. |
| 1. Entry Browser | 3–4 | Entry list/detail views, Supabase data fetching, filters, normalized Greek search. |
| 2. Editing Workbench | 5–6 | Translation editor with Server Actions, metadata forms, status workflow. |
| 3. Annotation Layer | 7–8 | Tokenization service, annotation CRUD, re-anchoring + `needs_review` state, annotation filters. |
| 4. Comparative Table | 9–10 | Columnar comparison UI, lemma-based entry selection, summary metrics. |
| 5. Polish & Export Prep | 11–12 | CSV/JSON export endpoints, TEI packet generator, access control hardening, deployment checklist. |

Offline Python/Node scripts are confined to Phase 0 import validation and future ETL batches.

---

## 8. Success Metrics
1. 100% of 1,699 entries imported with lemma links maintained via junction table.
2. ≥200 annotations anchored via token+context with zero unresolved drift after re-anchoring pass.
3. Comparative table used on all 284 overlapping lemmata without blocking UI errors.
4. Searches return in <1s under normalized prefix constraint; user education tooltip present in search UI.
5. TEI packet export tested on 10 sample entries for future pipeline.

---

## 9. TEI Transition Plan (Export-Only for MVP)
- **Data captured:** entries (Greek + translation), token sequences, annotations with quote+context, lemma linkages.
- **Export routine:** Server Action queries Supabase, assembles XML fragments per entry following TEI conventions for div/entry plus `<standOff>` annotations referencing tokens.
- **Workflow:** Editors continue working in Next.js UI; when TEI needed, run export, review in external TEI-aware tools.
- **Constraint:** No live TEI editing in MVP; TEI remains an interchange/export format. Redactor/annotation heuristics must produce metadata that can map cleanly to TEI standoff anchors later.

---

*Document version 3.0 – Authoritative scope & requirements for MVP delivery*

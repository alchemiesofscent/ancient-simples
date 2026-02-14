# Ancient Simples TEI-First Platform — UX/UI Specification (D-02)

Version: 1.0
Status: Draft

## 1. Goals

Primary goals:
- browse TEI-derived entries across multiple authors/works
- show canonical Greek reading text and stable citations
- allow editors to add and version translations
- allow editors to add/review assertions (quality/part/process)
- allow editors to review lemma forms and curate concept-level lemmata
- support cross-author comparison via alignments

Non-goals (v1):
- full recipe UI
- rich TEI rendering (app shows plain reading_text, not inline markup)

## 2. Navigation

Top-level navigation items:
- Entries
- Lemmata
- Assertions

Admin-only navigation (optional):
- Stale review

## 3. Routes

Public/authenticated routes (server components):
- `/entries`
- `/entries/[display_entry_id]`
- `/lemmata`
- `/lemmata/[lemma_id]`
- `/assertions`
- `/assertions/quality`
- `/assertions/parts`
- `/assertions/processes`

Admin/editor routes:
- `/admin/stale-review`

## 4. Entries list (`/entries`)

Purpose:
- browse entries across sources
- filter by source and indexing state
- see editorial completeness at a glance

UI elements:
- filters:
  - source (multi-select)
  - is_active (default TRUE)
  - has_translation (any language)
  - has_stale_assertions
- sorting:
  - default: source, structure ref, then segment id
- pagination

Row display:
- entry label: structure ref + short head (if available)
- citation: combined structure+edition ref
- badges:
  - translation count
  - assertion count
  - stale indicator

Click behavior:
- clicking a row opens the entry detail.

## 5. Entry detail (`/entries/[display_entry_id]`)

Layout sections:

A) Header
- structure citation
- edition citation
- source/work label
- is_active status (if inactive, show “inactive (not in current TEI run)”)
- hashes + import_run id (collapsed by default)

B) Greek reading text (read-only)
- show `reading_text` verbatim
- optional inline token highlighting on hover (future)

C) Lemma layer
- show linked lemma concepts (if any)
- show linked lemma forms (even if not assigned to a concept)
- affordance: “add lemma form” (creates draft lemma_form + entry_lemma_forms link)

D) Translations
- show latest translation per language
- show version history list (version, timestamp, status, author)
- editor action: “new version” opens an editor

Translation editor
- plain textarea
- save creates a new row with version+1
- status workflow:
  - draft → reviewed → published

E) Assertions
- grouped by `assertion_type`
- each assertion shows:
  - label (derived from payload)
  - citation (combined)
  - anchor quote snippet (if present)
  - status
  - source
  - stale marker if is_stale

Editor actions:
- add assertion (opens type-specific form)
- edit assertion status
- re-anchor (optional v1; at minimum provide “mark reviewed” with explanation)

## 6. Lemmata list (`/lemmata`)

Purpose:
- browse curated concepts
- search by normalized prefix

UI elements:
- search box (prefix match on headword_normalized)
- filters:
  - status (draft|confirmed)

Row display:
- lemma_id
- headword
- counts:
  - assigned forms
  - linked entries

## 7. Lemma detail (`/lemmata/[lemma_id]`)

Sections:

A) Lemma concept header
- lemma_id
- headword + normalized headword
- status toggle (editor-only)

B) Forms
- list lemma_forms assigned to this lemma
- show form_grc, source, confidence, status
- action: unassign form (sets lemma_id NULL)

C) Linked entries
- list entries linked via entry_lemma_forms where the form is assigned to this concept
- group by source
- each entry row includes:
  - structure+edition citation
  - link to entry detail

D) Comparison view (uses alignments)
- when an entry has alignments, show aligned entries side-by-side as a list
- minimal v1 UI: “Aligned entries” section with links and confidence

## 8. Assertions index (`/assertions`)

Purpose:
- landing page for facet query tools

Content:
- links to:
  - quality
  - parts
  - processes
- summary counts (total assertions per type; stale count)

## 9. Quality facet query (`/assertions/quality`)

Filters:
- axis (HOT|COLD|DRY|WET)
- degree (1–4)
- source
- status
- include stale (toggle)

Results:
- table with:
  - entry link
  - axis/degree
  - citation
  - quote snippet
  - source/status

Export:
- “Export CSV” button (server action)

## 10. Parts facet query (`/assertions/parts`)

Filters:
- part_name (dropdown from parts_vocab)
- source
- status

Same result format as quality.

## 11. Processes facet query (`/assertions/processes`)

Filters:
- process_name (dropdown from process_vocab)
- source
- status

Same result format as quality.

## 12. Stale review (`/admin/stale-review`)

Purpose:
- surface stale assertions for review after TEI changes

List view:
- filters:
  - source
  - assertion_type
- rows show:
  - entry link
  - assertion summary
  - stale reason (raw_hash mismatch)
  - last_import_run_id

Actions:
- mark as reviewed (keeps stale but records editorial acknowledgment)
- re-anchor (optional; if implemented, update anchor hashes and set is_stale FALSE)

## 13. Citation display rules

All pages MUST use the same formatter:
- structure path from entry_refs(ref_type='structure')
- edition ref from entry_refs(ref_type='edition')

Combined citation is rendered consistently across:
- entry header
- facet results
- lemma-linked entry lists

## 14. Accessibility and usability

Minimum requirements:
- keyboard navigation for lists
- filters use labeled inputs
- pagination controls are accessible
- stale indicators must not rely on color alone

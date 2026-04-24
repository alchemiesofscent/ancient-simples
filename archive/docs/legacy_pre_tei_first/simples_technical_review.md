---
status: historical
owner: archive
---

# Ancient Simples Database – Technical Architecture Review
*December 2025*  
*Canonical rationale aligned with the PRD*

---

## 1. Stack Confirmation & Rationale
| Layer | Choice | Notes |
|-------|--------|-------|
| UI + server logic | **Next.js 14+ (App Router, TypeScript)** | Single project handles routing, data fetching, and Server Actions for mutations; keeps edits close to UI. |
| Database + auth | **Supabase (PostgreSQL + Auth)** | Native Row Level Security, policy-based access, SQL migrations, nightly backups. |
| Styling | Tailwind CSS + shadcn/ui | Rapid prototyping with consistent design tokens. |
| Icons | Lucide React | Lightweight, tree-shakable. |
| Batch/ETL | Offline Node/Python scripts (Claude/Codex CLI) | Limited to CSV restructuring, diff-checking, tokenization precomputation. |

All MVP features run inside this stack—no Flask/FastAPI/Express services, no standalone API gateway. Next.js Server Actions talk directly to Supabase, benefiting from edge caching for reads and secure **secret (service role)** execution for writes.

---

## 2. Data Path & Validation Workflow
1. **Source spreadsheets → CSV drafts** using Claude/Codex CLI per the restructuring spec.
2. **Diff-check (MANDATORY):** compare row counts and word counts between original Excel sheets and generated CSVs. Flag deviations >5%.
3. **OpenRefine pass:** run text facets on categories, status, lemma_ids to catch silent autocorrections or malformed values.
4. **Supabase import:** load CSVs via `supabase db push` + `COPY`, splitting the temporary `lemma_ids` column into the canonical `entry_lemmata` junction table. The CSV column is import-only to ease Claude workflows; it is never used by the application at runtime.
5. **Next.js consumption:** Supabase client for queries, Server Actions for writes; React Query (or equivalent) caches results.

This pipeline preserves the CSV-first posture required for scholarly review and version control.

**Reference storage:** CTS URNs and edition-specific ranges are modeled as `entry_references` rows keyed by (`entry_id`, `edition_id`, `ref_type`), backed by an `editions` lookup so multiple editions per work coexist without embedding page numbers on the entry record.

---

## 3. Search & Normalization Constraints
- Implement a Supabase SQL function `normalize_greek(text)` that strips accents and breathings only (no transliteration, morphology, or lemmatization).
- Maintain `greek_normalized` columns for entries and lemmata; update via trigger on text change.
- Iota subscripts must remain preserved—normalization behavior must match the data spec and stay consistent across ETL scripts, database triggers, and application search.
- Next.js search UI enforces prefix queries of ≥3 normalized characters. Tooltips and docs must repeat this limitation so users understand why "αγ" returns nothing while "αγν" matches ἄγνος.
- Translation and annotation text use basic `ILIKE` filters; no full-text indexes beyond what Supabase provides out of the box.

---

## 4. Annotation Engineering Notes
- Store annotations with: `entry_id`, `token_start`, `token_end`, captured `quote`, `prefix_context`, `suffix_context`, author metadata, and status.
- When translations or Greek text change, run a re-anchoring routine (Server Action or background job) that attempts to match quote + context against the updated token array.
- Outcomes: `stable`, `reanchored`, or `needs_review`. UI filters surface items needing manual intervention.
- Character-offset–only anchors are rejected at validation time, guaranteeing future TEI standoff exports have sufficient context.

---

## 5. Comparative Features
### MVP – Columnar Comparison
- Users select up to three entries sharing lemma links. Each column renders metadata, normalized word counts, and edited text.
- Alignment is at the **entry level** only; we do not claim word-level correspondence.
- Notes panel encourages manual observations rather than automated diff output.

### Phase 2 – Redactor View (Heuristic)
- Single-column visualization overlays base text with heuristic signals (bold = preserved, gray = dropped, insertion cards = additions) derived from lemma-level heuristics and optional manual tagging.
- Must be labeled experimental; it is *not* a definitive diff or BLAST-style alignment.
- Requires manual validation and is deferred until MVP stability.

The comparative roadmap in the PRD must reference this same sequencing to avoid misinterpretation.

---

## 6. TEI Export Alignment (Export-Only)
- Token arrays, annotations, and entry metadata already stored in Supabase can be marshaled into TEI `<div>` elements with `<standOff>` references.
- Implement a Server Action producing TEI fragments per entry; batch zip downloads remain sufficient for Phase 1.
- No TEI-native editing is introduced—TEI serves solely as an interchange/export format for downstream pipelines and Phase 2 standoff experiments.

---

## 7. Operational Checklist (Always-On)
1. **Claude/Codex restructuring workflow** remains the authoritative method for generating CSVs.
2. **Diff-check script** stops imports when counts mismatch.
3. **OpenRefine review** before each import to Supabase.
4. **Supabase migrations** under version control; avoid ad hoc dashboard edits.
5. **Backups** verified weekly; retain local CSV exports prior to schema migrations.
6. **Security**: enforce Supabase Row Level Security for entries, annotations, and exports; Server Actions run with the Supabase **secret (service role)** key and authorize per-user capabilities.

---

## 8. Future Considerations (Beyond MVP)
- Recipe/ingredient modules, RDF triples, and Redactor View all stay on the roadmap but require no architectural change beyond additional tables and background jobs.
- If TEI editing ever becomes live, evaluate a minimal API layer, but current MVP documents must not presume it.

*This review supersedes earlier mixed-stack guidance and is the reference for implementation decisions.*

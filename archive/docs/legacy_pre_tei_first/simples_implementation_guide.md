---
status: historical
owner: archive
---

# Ancient Simples Database – Implementation Guide
*A practical walkthrough for the MVP stack: Next.js (App Router, TypeScript) + Supabase (PostgreSQL/Auth).*

This guide covers two coordinated workstreams:
1. **Data restructuring** with Claude/Codex CLI (CSV-first pipeline).
2. **Application implementation** using a single Next.js project with Supabase (no standalone backend service).

All steps assume Windows 11 or macOS with VS Code, Node.js ≥20, and Supabase CLI installed.

---

## 1. Prerequisites
- **Node.js:** Install LTS from https://nodejs.org and verify `node --version`.
- **pnpm or npm:** choose one (examples use `pnpm`).
- **Claude CLI:** `npm install -g @anthropic-ai/claude-code` then `claude login`.
- **Supabase CLI:** `npm install -g supabase` and authenticate via `supabase login`.
- **Project files:** `simples.xlsx`, `simples_data_restructure_spec.md`, and this guide.
- **VS Code extensions (optional):** Greek input helper, Supabase, ESLint.

---

## 2. Workspace Layout
```
ancient-simples/
 ├── data-workbench/
 │    ├── simples.xlsx
 │    ├── simples_data_restructure_spec.md
 │    ├── (CSV outputs…)
 └── app/
      ├── next.config.mjs
      ├── package.json
      └── (Next.js project files)
```
Work inside `data-workbench` for restructuring and `app` for the Next.js codebase. The Supabase project connects to both via environment variables.

---

## 3. Data Restructuring Workflow (Claude/Codex CLI)
### Step 3.1 – Launch Claude CLI
```bash
cd data-workbench
claude
```
Use the initial prompt:
```
Read simples_data_restructure_spec.md and help me restructure simples.xlsx into entries.csv, lemmata.csv, parts.csv, and supporting review files exactly as described. Confirm understanding before writing files.
```

### Step 3.2 – Generate `parts.csv`
Prompt Claude:
```
Execute Task A from the spec: create parts.csv with columns part_id,greek,english,category,notes using the starter vocabulary and any additional terms discovered in simples.xlsx.
```
Double-check in VS Code (UTF-8). If edits are needed, request them explicitly.

### Step 3.3 – Generate `lemmata.csv`
```
Execute Task B: parse the master lemma list, assign lemma_ids, fill category heuristics, populate parent_lemma + relationship, and create lemmata_review.csv for ambiguous rows.
```
Spot check parent/child rows; adjust by referencing the spec's guidance.

### Step 3.4 – Build `entries.csv`
```
Execute Task C: flatten all sheets into entries.csv with the required columns. Do not fill lemma_ids yet. Populate chapter_title_en literally.
```
Ensure word counts and references look correct.

### Step 3.5 – Link entries to lemmata & parts
```
Execute Task D: populate lemma_ids by matching normalized Greek forms to lemmata.csv, set part_id when titles mention parts, and emit unmatched_terms.csv for anything that fails to match.
```
Remember that `lemma_ids` is import-only; it will be exploded into `entry_lemmata` after loading into Supabase.

### Step 3.6 – Diff & OpenRefine Checks
```
Execute Task E: produce a summary comparing original sheet counts/word counts vs entries.csv and note any deviations. Prepare a markdown or CSV report.
```
Then run OpenRefine manually: import each CSV and facet key columns to catch typos before committing.

### Step 3.7 – Optional test subset
Follow Appendix C in the spec to run a small batch before scaling up.

### Step 3.8 – Commit artifacts
```
git add entries.csv lemmata.csv parts.csv modern_ids.csv lemmata_review.csv unmatched_terms.csv
```
Include the diff-check report in the commit for traceability.

---

## 4. Supabase Setup
### Step 4.1 – Initialize project
```bash
supabase projects create ancient-simples-mvp
supabase db remote set --project-ref <ref>
```
Store the `SUPABASE_URL` and `SUPABASE_SECRET_KEY` (service role) for local development.
Supabase now labels these keys as **publishable** (client) and **secret** (service role); prefer the new names in your `.env` files.

**IPv6-only note:** if your environment has no IPv4 egress, prefer Supabase Dashboard + Supabase CLI (HTTPS) workflows and avoid direct Postgres connections where possible.

### Step 4.2 – Define schema
Create `supabase/migrations/001_init.sql` with tables for sources, parts, lemmata, entries, entry_lemmata, annotations, and users (mirroring the PRD). Remember: application code never reads `entries.lemma_ids`; only the junction table is canonical.

### Step 4.3 – Import CSVs
1. Upload CSVs to Supabase storage or expose them locally.
2. Use `COPY` statements or Supabase dashboard import to load `sources`, `parts`, `lemmata`, `entries`.
3. Run a SQL script to explode `lemma_ids` into `entry_lemmata`:
   ```sql
   INSERT INTO entry_lemmata(entry_id, lemma_id, is_primary)
   SELECT entry_id, value AS lemma_id, value = split_part(lemma_ids, ',', 1)
   FROM entries
   CROSS JOIN LATERAL string_to_table(lemma_ids, ',') AS value
   WHERE lemma_ids <> '';
   UPDATE entries SET lemma_ids = NULL; -- optional cleanup
   ```
4. Validate counts using the checklist from the spec before moving on.

### Step 4.4 – Configure auth & policies
- Enable email magic-link auth.
- Create RLS policies: editors can select/update entries, annotations they own; viewers read-only.
- Store the secret (service role) key locally for privileged scripts (`.env.local`).

---

## 5. Next.js Application Implementation
### Step 5.1 – Scaffold project
```bash
cd ../app
pnpm create next-app@latest . --ts --app --src-dir --tailwind --eslint
pnpm install @supabase/auth-helpers-nextjs @supabase/supabase-js lucide-react @tanstack/react-query @radix-ui/react-popover tiptap-react tiptap-extension-mention
```

### Step 5.2 – Configure Supabase client
Create `/src/lib/supabase.ts` with browser and server clients. Reads use the publishable key; privileged scripts use the secret (service role) key (never expose it in client bundles).

### Step 5.3 – Data fetching patterns
- Use Server Components + Supabase queries for entry lists.
- Wrap client components with `React Query` for interactive search filters.
- Normalize Greek in SQL via stored function `normalize_greek(text)`; enforce prefix search (≥3 chars) in UI.

### Step 5.4 – Entry workspace
- Build sidebar filters (source, lemma, status, annotation flag).
- Detail route renders Greek text, translation editor (TipTap), metadata form, and annotation panel.
- Server Actions handle translation + metadata saves; optimistic UI updates show success toasts.

### Step 5.5 – Annotation module
- Tokenize Greek text via a Server Action immediately after each save so tokens stay in sync with the canonical entry text. Store the per-entry token arrays in Supabase and regenerate them whenever the Greek text changes.
- UI selection captures quote and ±N-token context; Server Action writes annotation with `status='stable'`.
- Provide re-anchoring action that attempts to match contexts after edits; unresolved matches set `status='needs_review'` and appear in a dedicated filter.

### Step 5.6 – Comparative table (MVP)
- Build `/compare` route where users select lemma, then choose up to three linked entries.
- Display entry metadata, translation excerpts, normalized word counts, and manual note field.
- Add helper text stating "Columnar comparison; no automated word-level diff in MVP."

### Step 5.7 – Exports & TEI packets
- Create a Server Action `exportEntries` that bundles selected entries, tokens, and annotations into CSV/JSON downloads.
- Provide a second action generating TEI-ready fragments (entries + `<standOff>` data). Emphasize that TEI is an export-only pathway, producing well-formed XML in MVP without enforcing schema validation.

### Step 5.8 – Authenticated experience
- Gate editing routes behind Supabase Auth middleware.
- Add role checks on Server Actions to block unauthorized writes.

---

## 6. Testing & Verification
1. **Unit tests:** use Vitest/Testing Library for utility functions (normalization, anchoring logic).
2. **Integration smoke tests:** Next.js Playwright tests for entry editing, annotation creation, and comparative selection.
3. **Manual TEI export test:** run export on 10 entries, validate XML against schema or well-formedness tools.
4. **Search QA:** ensure prefix requirement enforced; document limitation directly in UI copy.

---

## 7. Operational Runbook
- **Data updates:** rerun Claude CLI tasks for new batches, diff against previous CSVs, re-import via Supabase migrations.
- **Backups:** rely on Supabase nightly backups plus manual CSV exports stored in Git before schema changes.
- **Monitoring:** configure Supabase logs + Vercel analytics; track annotation re-anchoring failures to keep `needs_review` queue manageable.
- **Phase 2 planning:** Redactor View (heuristic overlay) stays deferred; do not allocate engineering effort until MVP metrics are met.

---

## 8. Quick Reference Commands
```bash
# Start Claude session
cd data-workbench && claude

# Run Supabase locally with remote project connection
supabase start

# Generate migrations
supabase db diff --linked --file 002_add_annotations.sql

# Next.js dev server
cd ../app && pnpm dev

# Deploy Next.js to Vercel (after linking project)
vercel --prod
```

---

## 9. Deliverable Checklist
- [ ] CSVs validated (diff-check + OpenRefine) and committed.
- [ ] Supabase schema deployed; junction table populated from `lemma_ids` import column.
- [ ] Next.js app implements entry workspace, annotation module, comparative table, and search constraints.
- [ ] Server Actions for translation edits, annotation CRUD, CSV/JSON/TEI exports.
- [ ] Documentation updated to explain prefix-based Greek search limitation and annotation re-anchoring states.

Once all boxes are checked, the team can onboard editors into the MVP environment and begin internal testing.

*Implementation guide v2.0 – Matches current PRD and technical review*

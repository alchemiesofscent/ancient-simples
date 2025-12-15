# ancient-simples

MVP constraints:
- Next.js + Supabase only (no separate backend service).
- CSV-first pipeline (data restructuring produces importable CSVs).
- `lemma_ids` is import-only (used to populate `entry_lemmata`, not read by the app).

Workspace layout:
- `data-workbench/` — source spreadsheet + restructuring spec + CSV outputs.
- `docs/` — project specs (unchanged copies).
- `app/` — reserved for the future Next.js project (no application code yet).

# Plan: Ancient Simples TEI-First Platform — Tech Spec, UX/UI, WBS + Seed Code

## Context

The existing Ancient Simples MVP is CSV-first: editors curated data in spreadsheets, imported to Supabase, and browse via a Next.js app. The `docs/new_simples/` specs define a **TEI-first** rewrite where TEI editions are the canonical source for Greek text and citations, with SQL storing only editorial metadata (translations, lemma links, assertions). 100 vocab extraction results exist in `outputs/vocab_entries_v3/` with rich term + quality data. TEI files exist from the Aetius CMG pipeline.

**Goal**: Produce three spec documents (tech spec, UX/UI spec, WBS) + scaffold seed code (textutils library, DB schema migration, TEI indexer, vocab importer, test fixtures) — all validated against a small curated subset of ~15 entries before scaling.

**User decisions**: Specs + seed code; small curated subset for testing; TEI exists already; recipes deferred (ingredients/facets only).

---

## Phase 0: Foundation (Contracts + Textutils Library)

### Spec documents (can start immediately, no code deps)

| Task | File | Notes |
|------|------|-------|
| D-01 Tech Spec | `docs/new_simples/tech_spec_v1.md` | Architecture, schema DDL, indexer contract, textutils spec, import pipeline, RLS model |
| D-02 UX/UI Spec | `docs/new_simples/ux_spec_v1.md` | Routes, screen designs, citation format, translation workflow, facet queries |
| D-03 WBS | `docs/new_simples/wbs_v1.md` | Phased tasks with dependencies, milestones, critical path |

### Platform contracts (formal docs)

| Task | File |
|------|------|
| F-01 | `docs/contracts/tei_indexing_contract.md` — segment identity, reading stream, determinism guarantee |
| F-01 | `docs/contracts/normalization_contract.md` — versioned rules (v1.0: lowercase, NFD strip 0300-036F except 0345, NFC) |
| F-01 | `docs/contracts/anchoring_contract.md` — token-span anchoring, staleness, drift safety |
| F-01 | `docs/contracts/citation_contract.md` — structure refs (hierarchy) + edition refs (pb/lb) |
| F-01 | `docs/contracts/export_contract.md` — CSV/JSON + optional TEI standoff |

### Shared textutils library

| Task | Files | Deps |
|------|-------|------|
| F-02 | `config/tei_doc_config.schema.yaml`, `config/tei_docs/example_config.yaml` | F-01 |
| F-03 | `packages/textutils/normalize.py` (NORMALIZATION_VERSION="1.0") + `tests/test_normalize.py` | F-01 |
| F-04 | `packages/textutils/tokenize.py` (TOKENIZER_VERSION="1.0") + `tests/test_tokenize.py` | F-01 |
| F-05 | `packages/textutils/hashing.py`, `citations.py` | F-01 |
| F-06 | `tests/test_determinism.py` — cross-validate Python/TS/SQL normalization parity (50 headwords from lemmata.csv) | F-03 |
| F-07 | `packages/textutils/__init__.py`, `tests/conftest.py` — packaging | F-03,F-04,F-05 |

**Reused code**: Normalization from `scripts/import_supabase.py:14-18` (Python), `app/src/lib/greek/normalize.ts` (TS), `supabase/migrations/001_init.sql:34-71` (SQL). The textutils module wraps the Python version with version constants.

**Phase 0 exit**: `normalize("Ψυχρός")` → `"ψυχρος"` identically in Python/TS/SQL. Tokenizer returns correct offsets. SHA-256 hashing is deterministic.

---

## Phase 1: Schema + Indexer + Vocab Importer (3 parallel tracks)

### Track A: Database schema

| Task | File | Notes |
|------|------|-------|
| S-01 | `supabase/migrations/005_tei_first_schema.sql` | New tables: `tei_docs`, `tei_entries`, `entry_refs`, `tokens`, `import_runs`, `translations`, `lemma_aliases`, `quality_vocab`, `parts_vocab`, `process_vocab`, `assertions`. Triggers for `entry_gr_normalized`. Seed controlled vocabs. |
| S-02 | `supabase/migrations/006_tei_rls.sql` | Indexer-owned tables (service-role write only): tei_entries, tokens, entry_refs, import_runs. Editor-owned: translations, assertions, lemma_aliases. All: authenticated read. |
| S-03 | Manual validation — apply to fresh Supabase project | S-01, S-02 |

**Key design**: New `tei_entries` table, not altering existing `entries`. Both coexist during transition. `assertions` uses JSONB `payload` + `assertion_type` discriminator (quality/part/process/other) — new facet types need no DDL change.

### Track B: TEI indexer

| Task | File | Deps |
|------|-------|------|
| I-01 | `scripts/validate_tei.py` — hard errors on missing/duplicate @xml:id, zero segments | F-01, F-02 |
| I-02 | `scripts/index_tei.py` — reads config YAML + TEI, produces tei_entries + entry_refs + tokens via `supabase_rest.py` | S-01, F-03-05, I-01 |
| I-03 | Staleness marking — when tei_segment_hash changes, flag assertions `is_stale=TRUE` | I-02 |
| I-04 | Import run reporting — write `import_runs` row with counts + version metadata | I-02 |
| I-05 | `--dry-run` mode — JSON report to stdout without DB writes | I-02 |

**Indexer processing per segment**: entry_id = `tei_doc_id#tei_segment_id` → extract reading stream → hash → normalize → tokenize → extract structure refs (ancestor hierarchy) + edition refs (pb/lb milestones) → upsert. Uses `lxml` (only non-stdlib dep).

### Track C: Vocab data importer

| Task | File | Deps |
|------|-------|------|
| V-01 | `config/entry_id_bridge.csv` — maps old source_id (GAL_SMT-8.15.9) → new entry_id (tei_doc_id#seg_id) | None |
| V-02 | `scripts/import_vocab_v3.py` — reads `results.jsonl` + bridge → creates lemmata candidates, lemma_aliases, entry_lemmata links, quality assertions | S-01, F-03 |
| V-03 | Lemma dedup logic within importer — dedup by (label, lemma_normalized), auto-assign L### IDs | V-02 |
| V-04 | Import validation report — stdout summary of created/skipped counts | V-02 |

**Mapping rules**: terms[SUBSTANCE] with confidence≥0.75 → lemmata + lemma_aliases. qualities[] with confidence≥0.70 → assertions(type=quality). All assertions get `source='v3_import'`, `status='draft'`.

---

## Phase 2: Test Data Subset (Critical Gate)

Nothing in Phase 3 starts until this passes.

| Task | File | Deps |
|------|-------|------|
| T-01 | `config/test_subset.txt` — ~15 entry IDs. Selection: 3+ with quality degrees, 2+ SUBSTANCE_PART, 2+ PREPARATION, 1+ APPLICATION_SITE, 1+ PLACE, entries from ≥2 sources. Adapt `scripts/select_deterministic_sample_ids.py`. | None |
| T-02 | `data/tei_fixtures/gal_smt_sample.xml`, `data/tei_fixtures/aet_lm_sample.xml` — minimal valid TEI with @xml:id segments, pb/lb milestones, Greek text from `entries.csv` | T-01 |
| T-03 | `config/tei_docs/gal_smt_sample.yaml`, `config/tei_docs/aet_lm_sample.yaml` — indexer configs for fixtures | T-02, F-02 |
| T-04 | Run `index_tei.py` on fixtures → verify tei_entries, entry_refs, tokens populated | I-02, T-03 |
| T-05 | Populate `entry_id_bridge.csv` for test subset mappings | T-04 |
| T-06 | Run `import_vocab_v3.py` for test subset → verify assertions + aliases created | V-02, T-05 |
| T-07 | End-to-end validation: all 4 facet queries return results, determinism verified (re-index produces identical hashes) | T-04, T-06 |

**Exit criteria**: ≥10 entries indexed with Greek/tokens/citations. ≥3 quality assertions with degrees. ≥2 lemma_aliases. All 4 query types return non-empty results. Re-index is idempotent.

---

## Phase 3: Next.js App UI (after T-07)

Server components throughout, following existing patterns in `app/src/`.

| Task | File | Notes |
|------|------|-------|
| U-01 | Modify `app/src/app/layout.tsx` | Add nav: Entries, Lemmata, Assertions |
| U-02 | Modify `app/src/app/entries/page.tsx` | Query `tei_entries`, add source/status filters, pagination, assertion count badge |
| U-03 | Modify `app/src/app/entries/[entry_id]/page.tsx` | TEI-first detail: provenance, citations (structure+edition), read-only Greek, lemma links, versioned translations, assertions grouped by type, stale highlighting |
| U-04 | Within `entries/[entry_id]/page.tsx` | Translation editor: server action creates new version row, version history, status workflow |
| U-05 | New `app/src/app/lemmata/page.tsx` | Prefix search, category filter, entry+alias counts, create form |
| U-06 | New `app/src/app/lemmata/[lemma_id]/page.tsx` | Lemma detail + aliases + linked entries grouped by source (comparison view) |
| U-07 | New `app/src/app/assertions/quality/page.tsx` | Facet query: axis/degree/intensity/source filters, results with citations, CSV export |
| U-08 | New `app/src/app/assertions/parts/page.tsx` | Part facet query with parts_vocab dropdown |
| U-09 | New `app/src/app/assertions/processes/page.tsx` | Process facet query with process_vocab dropdown |
| U-10 | New `app/src/app/assertions/page.tsx` | Index page linking to quality/parts/processes with summary counts |
| U-11 | New `app/src/lib/citations/format.ts` | `formatStructureRef()`, `formatEditionRef()`, `formatCombined()` — used by all detail/query pages |
| U-12 | New `app/src/app/admin/stale-review/page.tsx` | List stale assertions, confirm/flag actions |

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| New `tei_entries` table, don't alter `entries` | Identity model changes (SOURCE-ref → tei_doc_id#segment_id). Old app keeps working during transition. |
| JSONB payload for assertions | New assertion types (dosage, indication) need no DDL change. JSONB operators handle facet queries. |
| Python + lxml for indexer | lxml is standard for TEI/XML in digital humanities. Existing project is Python-heavy. |
| Explicit bridge CSV for v3→TEI IDs | Full control over mapping. Small file. Auditable. |
| No final sigma normalization in v1.0 | Current corpus handles it fine. Documented as explicit non-action. Version bump if needed later. |

---

## Database Schema Detail

### TEI Provenance Layer

```sql
tei_docs (
  tei_doc_id       TEXT PRIMARY KEY,
  source_code      TEXT NOT NULL REFERENCES sources(code),
  source_path      TEXT NOT NULL,
  tei_version_hash TEXT NOT NULL,
  title            TEXT NOT NULL DEFAULT '',
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  status           TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','deprecated'))
);

import_runs (
  run_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tei_doc_id            TEXT NOT NULL REFERENCES tei_docs(tei_doc_id),
  started_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at           TIMESTAMPTZ,
  status                TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','failed')),
  normalization_version TEXT NOT NULL,
  tokenizer_version     TEXT NOT NULL,
  segments_total        INTEGER,
  segments_new          INTEGER,
  segments_updated      INTEGER,
  segments_deprecated   INTEGER,
  warnings              JSONB NOT NULL DEFAULT '[]',
  errors                JSONB NOT NULL DEFAULT '[]',
  report                JSONB NOT NULL DEFAULT '{}'
);
```

### Projection Layer

```sql
tei_entries (
  entry_id            TEXT PRIMARY KEY,  -- tei_doc_id#tei_segment_id
  tei_doc_id          TEXT NOT NULL REFERENCES tei_docs(tei_doc_id),
  tei_segment_id      TEXT NOT NULL,
  tei_segment_hash    TEXT NOT NULL,
  ordering_key        TEXT NOT NULL,
  structure_ref       JSONB NOT NULL DEFAULT '{}',
  entry_gr            TEXT NOT NULL DEFAULT '',
  entry_gr_normalized TEXT NOT NULL DEFAULT '',
  deprecated          BOOLEAN NOT NULL DEFAULT FALSE,
  import_run_id       UUID REFERENCES import_runs(run_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tei_doc_id, tei_segment_id)
);

entry_refs (
  ref_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id   TEXT NOT NULL REFERENCES tei_entries(entry_id) ON DELETE CASCADE,
  ref_type   TEXT NOT NULL CHECK (ref_type IN ('structure','edition')),
  ref_system TEXT NOT NULL DEFAULT '',
  ref_value  TEXT NOT NULL,
  page_raw   TEXT,
  line_raw   TEXT,
  page_num   INTEGER,
  line_num   INTEGER,
  UNIQUE (entry_id, ref_system, ref_type, ref_value)
);

tokens (
  entry_id         TEXT NOT NULL REFERENCES tei_entries(entry_id) ON DELETE CASCADE,
  tei_segment_hash TEXT NOT NULL,
  token_idx        INTEGER NOT NULL,
  form             TEXT NOT NULL,
  form_normalized  TEXT NOT NULL,
  char_start       INTEGER NOT NULL,
  char_end         INTEGER NOT NULL,
  token_type       TEXT NOT NULL DEFAULT 'word' CHECK (token_type IN ('word','punctuation')),
  PRIMARY KEY (entry_id, tei_segment_hash, token_idx)
);
```

### Editorial Layer

```sql
translations (
  translation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id       TEXT NOT NULL REFERENCES tei_entries(entry_id) ON DELETE CASCADE,
  version        INTEGER NOT NULL DEFAULT 1,
  content        TEXT NOT NULL DEFAULT '',
  status         TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','review','final')),
  reviewer_notes TEXT NOT NULL DEFAULT '',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by     UUID REFERENCES auth.users(id),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by     UUID REFERENCES auth.users(id),
  UNIQUE (entry_id, version)
);

lemma_aliases (
  alias_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lemma_id           TEXT NOT NULL REFERENCES lemmata(lemma_id) ON DELETE CASCADE,
  surface_form       TEXT NOT NULL,
  surface_normalized TEXT NOT NULL,
  alias_type         TEXT NOT NULL DEFAULT 'orthographic'
                     CHECK (alias_type IN ('orthographic','inflectional','editorial','synonym')),
  source             TEXT NOT NULL DEFAULT 'manual',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Assertion Layer

```sql
assertions (
  assertion_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id              TEXT NOT NULL REFERENCES tei_entries(entry_id) ON DELETE CASCADE,
  assertion_type        TEXT NOT NULL CHECK (assertion_type IN ('quality','part','process','other')),
  payload               JSONB NOT NULL,
  lemma_id              TEXT REFERENCES lemmata(lemma_id),
  tei_segment_hash      TEXT NOT NULL,
  start_token_idx       INTEGER,
  end_token_idx         INTEGER,
  quote_cache           TEXT NOT NULL DEFAULT '',
  prefix_context        TEXT NOT NULL DEFAULT '',
  suffix_context        TEXT NOT NULL DEFAULT '',
  normalization_version TEXT NOT NULL,
  tokenizer_version     TEXT NOT NULL,
  is_stale              BOOLEAN NOT NULL DEFAULT FALSE,
  stale_reason          TEXT,
  status                TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','reviewed','published')),
  confidence            NUMERIC(3,2),
  source                TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual','v3_import','mention_index')),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by            UUID REFERENCES auth.users(id),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by            UUID REFERENCES auth.users(id)
);

-- Controlled vocabs
quality_vocab (quality_key TEXT PK, display_en TEXT, display_gr TEXT, max_degree INTEGER DEFAULT 4);
parts_vocab   (part_key TEXT PK, display_en TEXT, display_gr TEXT, notes TEXT DEFAULT '');
process_vocab (process_key TEXT PK, display_en TEXT, display_gr TEXT, greek_cues TEXT[] DEFAULT '{}', notes TEXT DEFAULT '');
```

### Assertion Payload Shapes (application-validated)

```json
// quality
{ "axis": "HOT|COLD|DRY|WET", "degree": 1-4|null, "intensity": "none|weak|moderate|balanced|strong|extreme",
  "hedge": "none|που|approx", "evidence_display": "...", "evidence_normalized": "..." }

// part
{ "part_key": "root", "substance_lemma_normalized": "...", "part_lemma_normalized": "..." }

// process
{ "process_key": "boil", "process_lemma_normalized": "...", "applies_to_lemma_normalized": "..." }
```

---

## UX/UI Route Map

| Route | Purpose |
|-------|---------|
| `/` | Redirect → `/entries` |
| `/entries` | Segment browser: search, filter by source/status, pagination, assertion count badges |
| `/entries/[entry_id]` | Detail: provenance, citations (structure+edition), read-only Greek, lemma links, versioned translations, assertions by type |
| `/lemmata` | Lemma registry: prefix search, category filter, create form |
| `/lemmata/[lemma_id]` | Lemma detail + aliases + linked entries by source (comparison view) |
| `/assertions` | Index page with links to facet query sub-pages + summary counts |
| `/assertions/quality` | Facet query: axis/degree/intensity/source filters, results with citations, CSV export |
| `/assertions/parts` | Part facet query with parts_vocab dropdown |
| `/assertions/processes` | Process facet query with process_vocab dropdown |
| `/compare/[lemma_id]` | Side-by-side comparison: entries grouped by source, Greek + translation + quality badges |
| `/admin/stale-review` | Stale assertion review queue |

### Citation Display Format

- Structure ref: `{ book: "8", chapter: "15", section: "6" }` → "Book 8, Ch. 15, Sec. 6" (short: "8.15.6")
- Edition ref: `{ ref_system: "Kuhn", page_raw: "XII.34", line_raw: "5" }` → "K. XII.34, l. 5"
- Combined: "Gal. SMT 8.15.6 (K. XII.34, l. 5)"
- Missing edition ref: "(edition ref not available)" in muted text

### Key UX Principles

- **Read-only Greek**: never editable in the app (TEI is authoritative)
- **Citations always visible**: every mention/assertion/query result shows structure + edition refs
- **Evidence-first**: every assertion links back to a quote and location
- **Stale items visible**: amber highlight, not hidden
- **Server components only**: form submissions, no client-side state management for MVP

---

## Execution Roadmap

| Week | Work |
|------|------|
| 1 | D-01/D-02/D-03 (specs), F-01→F-07 (foundation + textutils), T-01 (select subset), V-01 (bridge file) |
| 2 | S-01/S-02/S-03 (schema), I-01→I-05 (indexer), V-02→V-04 (vocab importer), T-02/T-03 (TEI fixtures) |
| 3 | T-04→T-07 (end-to-end validation gate), U-01/U-02/U-03/U-04/U-11 (entry browser + detail + citations) |
| 4 | U-05/U-06 (lemma registry), U-07/U-08/U-09/U-10 (facet queries), U-12 (stale review) |

**Critical path**: F-01 → F-03 → F-07 → S-01 → I-02 → T-04 → T-07 → U-03 (~9 days minimum)

**Milestones**:
- **M-0** Foundation complete: textutils tests pass, normalization parity verified
- **M-1** Schema deployed: migration applies to fresh DB
- **M-2** Indexer working: dry-run on fixture TEI succeeds
- **M-3** Pipeline end-to-end: test subset indexed + assertions imported, 4 facet queries return results
- **M-4** App browsable: all pages render with test subset data, facet queries exportable as CSV
- **M-5** Specs delivered: tech_spec_v1.md, ux_spec_v1.md, wbs_v1.md complete

---

## Verification

1. **Textutils**: `cd packages/textutils && python -m pytest tests/` — normalization determinism, tokenizer offsets, cross-language parity
2. **Schema**: `npm run db:push` — migration applies cleanly
3. **Indexer dry-run**: `python scripts/index_tei.py --config config/tei_docs/gal_smt_sample.yaml --dry-run` — JSON report with expected segment count
4. **Indexer live**: `python scripts/index_tei.py --config config/tei_docs/gal_smt_sample.yaml` — verify `tei_entries`, `tokens`, `entry_refs` in Supabase
5. **Vocab import**: `python scripts/import_vocab_v3.py --results outputs/vocab_entries_v3/entries_full_v3/results.jsonl --bridge config/entry_id_bridge.csv` — verify assertions + lemma_aliases
6. **Facet queries**: SQL queries against assertions table filtered by assertion_type + payload JSONB operators return results for all 4 types
7. **App**: `npm --prefix app run dev` → browse /entries, /lemmata, /assertions/quality with test subset data
8. **CI**: `npm run ci` passes (data validation + lint + build)

---

## Complete File Manifest

### New files to create

**Foundation (Phase 0)**:
- `docs/contracts/tei_indexing_contract.md`
- `docs/contracts/normalization_contract.md`
- `docs/contracts/anchoring_contract.md`
- `docs/contracts/citation_contract.md`
- `docs/contracts/export_contract.md`
- `config/tei_doc_config.schema.yaml`
- `config/tei_docs/example_config.yaml`
- `packages/textutils/__init__.py`
- `packages/textutils/normalize.py`
- `packages/textutils/tokenize.py`
- `packages/textutils/hashing.py`
- `packages/textutils/citations.py`
- `packages/textutils/tests/__init__.py`
- `packages/textutils/tests/conftest.py`
- `packages/textutils/tests/test_normalize.py`
- `packages/textutils/tests/test_tokenize.py`
- `packages/textutils/tests/test_determinism.py`

**Schema (Phase 1)**:
- `supabase/migrations/005_tei_first_schema.sql`
- `supabase/migrations/006_tei_rls.sql`

**Indexer + importer (Phase 1)**:
- `scripts/validate_tei.py`
- `scripts/index_tei.py`
- `config/entry_id_bridge.csv`
- `scripts/import_vocab_v3.py`

**Test data (Phase 2)**:
- `config/test_subset.txt`
- `data/tei_fixtures/gal_smt_sample.xml`
- `data/tei_fixtures/aet_lm_sample.xml`
- `config/tei_docs/gal_smt_sample.yaml`
- `config/tei_docs/aet_lm_sample.yaml`

**App UI (Phase 3)**:
- `app/src/lib/citations/format.ts`
- `app/src/app/lemmata/page.tsx`
- `app/src/app/lemmata/[lemma_id]/page.tsx`
- `app/src/app/assertions/page.tsx`
- `app/src/app/assertions/quality/page.tsx`
- `app/src/app/assertions/parts/page.tsx`
- `app/src/app/assertions/processes/page.tsx`
- `app/src/app/compare/[lemma_id]/page.tsx`
- `app/src/app/admin/stale-review/page.tsx`

**Spec documents (Phase 0/4)**:
- `docs/new_simples/tech_spec_v1.md`
- `docs/new_simples/ux_spec_v1.md`
- `docs/new_simples/wbs_v1.md`

### Existing files to modify

- `app/src/app/layout.tsx` — add nav links (Entries, Lemmata, Assertions)
- `app/src/app/entries/page.tsx` — query tei_entries, add filters + pagination
- `app/src/app/entries/[entry_id]/page.tsx` — TEI-first detail with citations + assertions

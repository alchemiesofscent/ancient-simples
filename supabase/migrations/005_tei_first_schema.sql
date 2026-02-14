-- 005_tei_first_schema.sql
-- TEI-first schema for Ancient Simples platform
-- Binding: docs/new_simples/tech_spec_v1.md, docs/contracts/
--
-- Creates all TEI-first tables. Existing MVP tables (entries, lemmata, etc.
-- from 001_init.sql) are NOT altered — both schemas coexist during transition.

begin;

-- ---------------------------------------------------------------------------
-- Source registry
-- ---------------------------------------------------------------------------
create table if not exists public.tei_sources (
  code text primary key,
  name text not null,
  edition text,
  status text not null default 'registered'
    check (status in ('active', 'registered', 'pending')),
  created_at timestamptz not null default now()
);

-- Seed sources: 3 active, 2 registered, 2 pending
INSERT INTO public.tei_sources (code, name, edition, status) VALUES
  ('GAL_SMT',   'Galen, De simplicium medicamentorum',    'Kühn XI–XII',        'active'),
  ('AET_LM',    'Aetius, Libri Medicinales I–II',          'Olivieri CMG 8.1',   'active'),
  ('DIOSC_DMM', 'Dioscorides, De Materia Medica',          'Wellmann',           'active'),
  ('GAL_ALIM',  'Galen, De alimentorum facultatibus',      'Helmreich + Kühn',   'registered'),
  ('AET_XVI',   'Aetius, Iatricorum liber XVI',            'Zervos',             'registered'),
  ('PAUL_RM',   'Paul of Aegina, De re medica I–VII',      'Heiberg CMG IX',     'pending'),
  ('ORIB_CM',   'Oribasius, Collectiones medicae I–XVI',   'Raeder CMG VI',      'pending')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- TEI document registry
-- ---------------------------------------------------------------------------
create table if not exists public.tei_docs (
  tei_doc_id text primary key,
  source_code text not null references public.tei_sources(code),
  tei_relpath text not null,
  label text,
  config_path text,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Import run provenance
-- ---------------------------------------------------------------------------
create table if not exists public.import_runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  cmg_submodule_commit text,
  indexer_version text,
  normalization_version text,
  tokenizer_version text,
  mode text not null default 'live'
    check (mode in ('dry_run', 'live')),
  counts jsonb default '{}'::jsonb,
  warnings jsonb default '[]'::jsonb
);

-- ---------------------------------------------------------------------------
-- TEI entries (rebuildable cache from TEI)
-- ---------------------------------------------------------------------------
-- Integer surrogate PK: tokens and other tables FK to bigint, not text.
-- Entry ID delimiter is ~ (not #).
-- Dual hashing: raw_hash + normalized_hash for change detection.
-- Soft delete via is_active + last_import_run_id.
create table if not exists public.tei_entries (
  id bigserial primary key,
  tei_doc_id text not null references public.tei_docs(tei_doc_id),
  tei_segment_id text not null,
  display_entry_id text generated always as (tei_doc_id || '~' || tei_segment_id) stored,
  reading_text text,
  normalized_text text,
  raw_hash text,
  normalized_hash text,
  is_active boolean not null default true,
  last_import_run_id uuid references public.import_runs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tei_entries_doc_seg_unique unique (tei_doc_id, tei_segment_id)
);

create index if not exists idx_tei_entries_doc_id on public.tei_entries (tei_doc_id);
create index if not exists idx_tei_entries_active on public.tei_entries (is_active) where is_active = true;
create index if not exists idx_tei_entries_display_id on public.tei_entries (display_entry_id);
create index if not exists idx_tei_entries_normalized_hash on public.tei_entries (normalized_hash);

-- Trigger: auto-update updated_at
create or replace function public.tei_entries_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger trg_tei_entries_updated_at
  before update on public.tei_entries
  for each row execute function public.tei_entries_set_updated_at();

-- ---------------------------------------------------------------------------
-- Entry refs (citations — rebuildable cache)
-- ---------------------------------------------------------------------------
create table if not exists public.tei_entry_refs (
  id bigserial primary key,
  tei_entry_id bigint not null references public.tei_entries(id) on delete cascade,
  ref_type text not null check (ref_type in ('structure', 'edition')),
  payload jsonb not null,
  constraint tei_entry_refs_unique unique (tei_entry_id, ref_type)
);

create index if not exists idx_tei_entry_refs_entry on public.tei_entry_refs (tei_entry_id);

-- ---------------------------------------------------------------------------
-- Tokens (rebuildable cache)
-- ---------------------------------------------------------------------------
create table if not exists public.tei_tokens (
  id bigserial primary key,
  tei_entry_id bigint not null references public.tei_entries(id) on delete cascade,
  token_index integer not null,
  start_offset integer not null,
  end_offset integer not null,
  token_text text not null,
  token_normalized text not null,
  constraint tei_tokens_entry_idx_unique unique (tei_entry_id, token_index)
);

create index if not exists idx_tei_tokens_entry on public.tei_tokens (tei_entry_id);
create index if not exists idx_tei_tokens_normalized on public.tei_tokens (token_normalized);

-- ---------------------------------------------------------------------------
-- Translations (editor-owned, versioned)
-- ---------------------------------------------------------------------------
create table if not exists public.tei_translations (
  id bigserial primary key,
  tei_entry_id bigint not null references public.tei_entries(id),
  language text not null default 'en',
  version integer not null default 1,
  status text not null default 'draft'
    check (status in ('draft', 'reviewed', 'published')),
  body text not null,
  author_id uuid references auth.users(id),
  source_file text,
  source_row_id text,
  import_method text,
  created_at timestamptz not null default now(),
  constraint tei_translations_version_unique unique (tei_entry_id, language, version)
);

create index if not exists idx_tei_translations_entry on public.tei_translations (tei_entry_id);

-- ---------------------------------------------------------------------------
-- Assertions (editor-owned, JSONB payload + CHECK constraints)
-- ---------------------------------------------------------------------------
create table if not exists public.tei_assertions (
  id bigserial primary key,
  tei_entry_id bigint not null references public.tei_entries(id),
  assertion_type text not null
    check (assertion_type in ('quality', 'part', 'process', 'other')),
  payload jsonb not null,
  status text not null default 'draft'
    check (status in ('draft', 'needs_review', 'confirmed')),
  source text,
  is_stale boolean not null default false,
  anchor jsonb,
  author_id uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- CHECK constraints per assertion_type
  constraint chk_quality_has_axis check (
    assertion_type != 'quality' OR payload ? 'axis'
  ),
  constraint chk_part_has_part_name check (
    assertion_type != 'part' OR payload ? 'part_name'
  ),
  constraint chk_process_has_process_name check (
    assertion_type != 'process' OR payload ? 'process_name'
  )
);

-- Expression indexes for facet queries
create index if not exists idx_assertions_quality_axis
  on public.tei_assertions (assertion_type, (payload->>'axis'))
  where assertion_type = 'quality';

create index if not exists idx_assertions_quality_degree
  on public.tei_assertions (assertion_type, (payload->>'degree'))
  where assertion_type = 'quality';

create index if not exists idx_assertions_part_name
  on public.tei_assertions (assertion_type, (payload->>'part_name'))
  where assertion_type = 'part';

create index if not exists idx_assertions_process_name
  on public.tei_assertions (assertion_type, (payload->>'process_name'))
  where assertion_type = 'process';

create index if not exists idx_assertions_entry on public.tei_assertions (tei_entry_id);
create index if not exists idx_assertions_stale on public.tei_assertions (is_stale) where is_stale = true;

-- Trigger: updated_at on assertions (reuses tei_entries_set_updated_at)
create trigger trg_assertions_updated_at
  before update on public.tei_assertions
  for each row execute function public.tei_entries_set_updated_at();

-- ---------------------------------------------------------------------------
-- Controlled vocab tables (seed dropdowns, reduce spelling drift)
-- ---------------------------------------------------------------------------
create table if not exists public.quality_vocab (
  axis text primary key,
  gloss text,
  ordering integer
);

INSERT INTO public.quality_vocab (axis, gloss, ordering) VALUES
  ('HOT',  U&'\03B8\03B5\03C1\03BC\03CC\03BD / hot',  1),
  ('COLD', U&'\03C8\03C5\03C7\03C1\03CC\03BD / cold', 2),
  ('DRY',  U&'\03BE\03B7\03C1\03CC\03BD / dry',       3),
  ('WET',  U&'\1F51\03B3\03C1\03CC\03BD / wet',       4)
ON CONFLICT (axis) DO NOTHING;

create table if not exists public.parts_vocab (
  part_name text primary key,
  gloss text
);

create table if not exists public.process_vocab (
  process_name text primary key,
  gloss text
);

-- ---------------------------------------------------------------------------
-- Lemma layer (conservative: forms -> review -> concepts)
-- ---------------------------------------------------------------------------

-- Concepts (curated)
create table if not exists public.tei_lemmata (
  lemma_id text primary key,
  headword_grc text not null,
  headword_normalized text not null,
  category text check (category in ('vegetable', 'animal', 'mineral')),
  status text not null default 'draft'
    check (status in ('draft', 'confirmed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_tei_lemmata_normalized
  on public.tei_lemmata (headword_normalized text_pattern_ops);

-- Forms (strings, linked to entries immediately)
create table if not exists public.tei_lemma_forms (
  id uuid primary key default gen_random_uuid(),
  form_grc text not null,
  form_normalized text not null,
  status text not null default 'draft'
    check (status in ('draft', 'needs_review', 'confirmed')),
  source text,
  confidence numeric,
  lemma_id text references public.tei_lemmata(lemma_id),
  source_file text,
  source_row_id text,
  import_method text,
  created_at timestamptz not null default now()
);

create index if not exists idx_lemma_forms_normalized
  on public.tei_lemma_forms (form_normalized text_pattern_ops);
create index if not exists idx_lemma_forms_lemma
  on public.tei_lemma_forms (lemma_id) where lemma_id is not null;

-- Entry <-> lemma form junction
create table if not exists public.tei_entry_lemma_forms (
  tei_entry_id bigint not null references public.tei_entries(id),
  lemma_form_id uuid not null references public.tei_lemma_forms(id),
  role text not null default 'headword'
    check (role in ('headword', 'mentioned')),
  confidence numeric,
  primary key (tei_entry_id, lemma_form_id)
);

-- Lemma aliases (concept-level)
create table if not exists public.tei_lemma_aliases (
  id bigserial primary key,
  lemma_id text not null references public.tei_lemmata(lemma_id),
  alias_grc text not null,
  alias_normalized text not null,
  alias_type text not null default 'orthographic'
    check (alias_type in ('orthographic', 'cross_tradition', 'gloss')),
  created_at timestamptz not null default now()
);

create index if not exists idx_lemma_aliases_lemma on public.tei_lemma_aliases (lemma_id);
create index if not exists idx_lemma_aliases_normalized
  on public.tei_lemma_aliases (alias_normalized text_pattern_ops);

-- ---------------------------------------------------------------------------
-- Entry alignments (cross-author structural mappings)
-- ---------------------------------------------------------------------------
create table if not exists public.tei_entry_alignments (
  id bigserial primary key,
  tei_entry_id_a bigint not null references public.tei_entries(id),
  tei_entry_id_b bigint not null references public.tei_entries(id),
  alignment_type text not null
    check (alignment_type in ('chapter_parallel', 'excerpt', 'rearrangement', 'independent')),
  confidence numeric,
  source text,
  evidence jsonb,
  curator text,
  created_at timestamptz not null default now(),
  constraint tei_alignments_pair_unique unique (tei_entry_id_a, tei_entry_id_b, alignment_type),
  constraint tei_alignments_no_self check (tei_entry_id_a != tei_entry_id_b)
);

create index if not exists idx_alignments_a on public.tei_entry_alignments (tei_entry_id_a);
create index if not exists idx_alignments_b on public.tei_entry_alignments (tei_entry_id_b);

-- ---------------------------------------------------------------------------
-- v1.1 normalization function (strips ALL combining marks including iota subscript)
-- ---------------------------------------------------------------------------
-- NOTE: The existing normalize_greek() in 001/003/004 preserves iota subscript (v1.0).
-- This new function implements v1.1 for TEI-first tables.
-- Key difference from v1.0:
--   1. Combining iota subscript U+0345 is STRIPPED (not preserved)
--   2. Precomposed iota subscript forms map to base letter WITHOUT iota subscript
--
-- Uses the same two-pass translate() pattern as 004_fix_normalize_greek_mapping.sql:
--   Pass 1: strip all combining marks U+0300..U+036F (including U+0345)
--   Pass 2: translate precomposed Greek Extended forms to base letters

create or replace function public.normalize_greek_v1_1(input_text text)
returns text
language plpgsql
immutable
as $$
declare
  marks_to_strip text := '';
  i int;
  -- Precomposed forms whose normalization differs from lowercase.
  -- Generated from the same codepoint ranges as v1.0 (004) but with
  -- iota-subscript forms mapping to base WITHOUT iota subscript.
  --
  -- Greek and Coptic: U+0370..U+03FF
  -- Greek Extended:   U+1F00..U+1FFF
  from_chars text :=
    -- Miscellaneous Greek punctuation / spacing marks that map to simpler forms
    U&'\0374\037E\0385\0387' ||
    -- Precomposed accent forms in base Greek block
    U&'\0390\03AC\03AD\03AE\03AF\03B0\03CA\03CB\03CC\03CD\03CE\03D3\03D4' ||
    -- Greek Extended: alpha with breathings/accents (U+1F00..1F07)
    U&'\1F00\1F01\1F02\1F03\1F04\1F05\1F06\1F07' ||
    -- Greek Extended: epsilon with breathings/accents (U+1F10..1F15)
    U&'\1F10\1F11\1F12\1F13\1F14\1F15' ||
    -- Greek Extended: eta with breathings/accents (U+1F20..1F27)
    U&'\1F20\1F21\1F22\1F23\1F24\1F25\1F26\1F27' ||
    -- Greek Extended: iota with breathings/accents (U+1F30..1F37)
    U&'\1F30\1F31\1F32\1F33\1F34\1F35\1F36\1F37' ||
    -- Greek Extended: omicron with breathings/accents (U+1F40..1F45)
    U&'\1F40\1F41\1F42\1F43\1F44\1F45' ||
    -- Greek Extended: upsilon with breathings/accents (U+1F50..1F57)
    U&'\1F50\1F51\1F52\1F53\1F54\1F55\1F56\1F57' ||
    -- Greek Extended: omega with breathings/accents (U+1F60..1F67)
    U&'\1F60\1F61\1F62\1F63\1F64\1F65\1F66\1F67' ||
    -- Greek Extended: vowels with varia/oxia only (U+1F70..1F7D)
    U&'\1F70\1F71\1F72\1F73\1F74\1F75\1F76\1F77\1F78\1F79\1F7A\1F7B\1F7C\1F7D' ||
    -- v1.1: alpha + iota subscript forms (U+1F80..1F87) -> alpha (NO iota subscript)
    U&'\1F80\1F81\1F82\1F83\1F84\1F85\1F86\1F87' ||
    -- v1.1: eta + iota subscript forms (U+1F90..1F97) -> eta (NO iota subscript)
    U&'\1F90\1F91\1F92\1F93\1F94\1F95\1F96\1F97' ||
    -- v1.1: omega + iota subscript forms (U+1FA0..1FA7) -> omega (NO iota subscript)
    U&'\1FA0\1FA1\1FA2\1FA3\1FA4\1FA5\1FA6\1FA7' ||
    -- v1.1: alpha short/long, alpha+varia+iota-sub, alpha+oxia+iota-sub, alpha-macron, etc.
    -- U+1FB0 alpha breve, U+1FB1 alpha macron, U+1FB2 alpha+varia+ypogegrammeni,
    -- U+1FB4 alpha+oxia+ypogegrammeni, U+1FB6 alpha+perispomeni,
    -- U+1FB7 alpha+perispomeni+ypogegrammeni, U+1FBE prosgegrammeni (-> iota)
    U&'\1FB0\1FB1\1FB2\1FB4\1FB6\1FB7\1FBE' ||
    -- U+1FC1 diaeresis+perispomeni, U+1FC2 eta+varia+ypogegrammeni,
    -- U+1FC4 eta+oxia+ypogegrammeni, U+1FC6 eta+perispomeni,
    -- U+1FC7 eta+perispomeni+ypogegrammeni
    U&'\1FC1\1FC2\1FC4\1FC6\1FC7' ||
    -- U+1FCD..1FCF koronis/psili variants
    U&'\1FCD\1FCE\1FCF' ||
    -- Iota short/long/accent forms
    U&'\1FD0\1FD1\1FD2\1FD3\1FD6\1FD7' ||
    -- U+1FDD..1FDF dasia variants
    U&'\1FDD\1FDE\1FDF' ||
    -- Upsilon short/long/accent forms + rho with breathings
    U&'\1FE0\1FE1\1FE2\1FE3\1FE4\1FE5\1FE6\1FE7' ||
    -- U+1FED..1FEF dialytika/varia/oxia
    U&'\1FED\1FEE\1FEF' ||
    -- v1.1: omega+varia+ypogegrammeni, omega+oxia+ypogegrammeni,
    -- omega+perispomeni, omega+perispomeni+ypogegrammeni
    U&'\1FF2\1FF4\1FF6\1FF7' ||
    -- U+1FFD oxia
    U&'\1FFD';
  to_chars text :=
    -- Miscellaneous Greek punctuation / spacing marks
    -- U+0374 -> U+02B9 (numeral sign -> modifier letter prime)
    -- U+037E -> U+003B (Greek question mark -> semicolon)
    -- U+0385 -> U+00A8 (dialytika tonos -> diaeresis)
    -- U+0387 -> U+00B7 (ano teleia -> middle dot)
    U&'\02B9\003B\00A8\00B7' ||
    -- Precomposed accent forms in base Greek block -> base letters
    -- U+0390 -> iota, U+03AC -> alpha, U+03AD -> epsilon, U+03AE -> eta,
    -- U+03AF -> iota, U+03B0 -> upsilon, U+03CA -> iota, U+03CB -> upsilon,
    -- U+03CC -> omicron, U+03CD -> upsilon, U+03CE -> omega,
    -- U+03D3 -> upsilon-with-hook, U+03D4 -> upsilon-with-hook
    U&'\03B9\03B1\03B5\03B7\03B9\03C5\03B9\03C5\03BF\03C5\03C9\03D2\03D2' ||
    -- Alpha with breathings: all -> alpha (U+03B1)
    U&'\03B1\03B1\03B1\03B1\03B1\03B1\03B1\03B1' ||
    -- Epsilon with breathings: all -> epsilon (U+03B5)
    U&'\03B5\03B5\03B5\03B5\03B5\03B5' ||
    -- Eta with breathings: all -> eta (U+03B7)
    U&'\03B7\03B7\03B7\03B7\03B7\03B7\03B7\03B7' ||
    -- Iota with breathings: all -> iota (U+03B9)
    U&'\03B9\03B9\03B9\03B9\03B9\03B9\03B9\03B9' ||
    -- Omicron with breathings: all -> omicron (U+03BF)
    U&'\03BF\03BF\03BF\03BF\03BF\03BF' ||
    -- Upsilon with breathings: all -> upsilon (U+03C5)
    U&'\03C5\03C5\03C5\03C5\03C5\03C5\03C5\03C5' ||
    -- Omega with breathings: all -> omega (U+03C9)
    U&'\03C9\03C9\03C9\03C9\03C9\03C9\03C9\03C9' ||
    -- Vowels with varia/oxia: alpha, alpha, epsilon, epsilon, eta, eta,
    -- iota, iota, omicron, omicron, upsilon, upsilon, omega, omega
    U&'\03B1\03B1\03B5\03B5\03B7\03B7\03B9\03B9\03BF\03BF\03C5\03C5\03C9\03C9' ||
    -- v1.1: alpha + iota subscript (1F80..1F87) -> alpha (NOT alpha-ypogegrammeni)
    U&'\03B1\03B1\03B1\03B1\03B1\03B1\03B1\03B1' ||
    -- v1.1: eta + iota subscript (1F90..1F97) -> eta (NOT eta-ypogegrammeni)
    U&'\03B7\03B7\03B7\03B7\03B7\03B7\03B7\03B7' ||
    -- v1.1: omega + iota subscript (1FA0..1FA7) -> omega (NOT omega-ypogegrammeni)
    U&'\03C9\03C9\03C9\03C9\03C9\03C9\03C9\03C9' ||
    -- 1FB0 -> alpha, 1FB1 -> alpha, 1FB2 -> alpha (v1.1: no iota sub),
    -- 1FB4 -> alpha (v1.1: no iota sub), 1FB6 -> alpha,
    -- 1FB7 -> alpha (v1.1: no iota sub), 1FBE -> iota
    U&'\03B1\03B1\03B1\03B1\03B1\03B1\03B9' ||
    -- 1FC1 -> diaeresis, 1FC2 -> eta (v1.1: no iota sub),
    -- 1FC4 -> eta (v1.1: no iota sub), 1FC6 -> eta,
    -- 1FC7 -> eta (v1.1: no iota sub)
    U&'\00A8\03B7\03B7\03B7\03B7' ||
    -- 1FCD -> psili (U+1FBF), 1FCE -> psili, 1FCF -> psili
    U&'\1FBF\1FBF\1FBF' ||
    -- Iota forms: 1FD0..1FD3 -> iota, 1FD6..1FD7 -> iota
    U&'\03B9\03B9\03B9\03B9\03B9\03B9' ||
    -- 1FDD -> dasia (U+1FFE), 1FDE -> dasia, 1FDF -> dasia
    U&'\1FFE\1FFE\1FFE' ||
    -- Upsilon forms + rho: 1FE0..1FE7
    -- upsilon, upsilon, upsilon, upsilon, rho, rho, upsilon, upsilon
    U&'\03C5\03C5\03C5\03C5\03C1\03C1\03C5\03C5' ||
    -- 1FED -> diaeresis, 1FEE -> diaeresis, 1FEF -> grave accent
    U&'\00A8\00A8\0060' ||
    -- v1.1: omega + iota subscript forms -> omega (no iota sub)
    -- 1FF2 -> omega, 1FF4 -> omega, 1FF6 -> omega, 1FF7 -> omega
    U&'\03C9\03C9\03C9\03C9' ||
    -- 1FFD -> acute accent (U+00B4)
    U&'\00B4';
begin
  -- Pass 1: Strip ALL combining marks U+0300..U+036F.
  -- v1.1 difference from v1.0: iota subscript U+0345 is also stripped.
  for i in 768..879 loop  -- 768 = 0x0300, 879 = 0x036F
    marks_to_strip := marks_to_strip || chr(i);
  end loop;

  -- Pass 2: Map precomposed Greek Extended forms to base letters, then lowercase.
  return translate(
    translate(lower(coalesce(input_text, '')), marks_to_strip, ''),
    from_chars,
    to_chars
  );
end;
$$;

commit;

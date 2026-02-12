-- 006_tei_rls.sql
-- Row-Level Security policies for TEI-first tables.
-- Follows the same pattern as 001_init.sql:
--   - public.is_authenticated() for read access
--   - public.is_editor(auth.uid()) for write access
--
-- Table ownership categories:
--   Indexer-owned (service-role write only, no INSERT/UPDATE/DELETE policies):
--     tei_entries, tei_tokens, tei_entry_refs, import_runs
--   Editor-owned (authenticated write via is_editor):
--     tei_translations, tei_assertions, tei_lemma_forms, tei_lemmata,
--     tei_lemma_aliases, tei_entry_alignments, tei_entry_lemma_forms
--   Read-only reference tables:
--     tei_sources, tei_docs, quality_vocab, parts_vocab, process_vocab

begin;

-- ---------------------------------------------------------------------------
-- Enable RLS on all TEI-first tables
-- ---------------------------------------------------------------------------

alter table public.tei_sources enable row level security;
alter table public.tei_docs enable row level security;
alter table public.import_runs enable row level security;
alter table public.tei_entries enable row level security;
alter table public.tei_entry_refs enable row level security;
alter table public.tei_tokens enable row level security;
alter table public.tei_translations enable row level security;
alter table public.tei_assertions enable row level security;
alter table public.quality_vocab enable row level security;
alter table public.parts_vocab enable row level security;
alter table public.process_vocab enable row level security;
alter table public.tei_lemmata enable row level security;
alter table public.tei_lemma_forms enable row level security;
alter table public.tei_entry_lemma_forms enable row level security;
alter table public.tei_lemma_aliases enable row level security;
alter table public.tei_entry_alignments enable row level security;

-- ---------------------------------------------------------------------------
-- Read-only reference tables: authenticated SELECT only
-- (tei_sources, tei_docs, quality_vocab, parts_vocab, process_vocab)
-- ---------------------------------------------------------------------------

-- tei_sources
drop policy if exists tei_sources_read on public.tei_sources;
create policy tei_sources_read
  on public.tei_sources
  for select
  using (public.is_authenticated());

-- tei_docs
drop policy if exists tei_docs_read on public.tei_docs;
create policy tei_docs_read
  on public.tei_docs
  for select
  using (public.is_authenticated());

-- quality_vocab
drop policy if exists quality_vocab_read on public.quality_vocab;
create policy quality_vocab_read
  on public.quality_vocab
  for select
  using (public.is_authenticated());

-- parts_vocab
drop policy if exists parts_vocab_read on public.parts_vocab;
create policy parts_vocab_read
  on public.parts_vocab
  for select
  using (public.is_authenticated());

-- process_vocab
drop policy if exists process_vocab_read on public.process_vocab;
create policy process_vocab_read
  on public.process_vocab
  for select
  using (public.is_authenticated());

-- ---------------------------------------------------------------------------
-- Indexer-owned tables: authenticated SELECT only
-- (No INSERT/UPDATE/DELETE policies — service role bypasses RLS)
-- ---------------------------------------------------------------------------

-- import_runs
drop policy if exists import_runs_read on public.import_runs;
create policy import_runs_read
  on public.import_runs
  for select
  using (public.is_authenticated());

-- tei_entries
drop policy if exists tei_entries_read on public.tei_entries;
create policy tei_entries_read
  on public.tei_entries
  for select
  using (public.is_authenticated());

-- tei_entry_refs
drop policy if exists tei_entry_refs_read on public.tei_entry_refs;
create policy tei_entry_refs_read
  on public.tei_entry_refs
  for select
  using (public.is_authenticated());

-- tei_tokens
drop policy if exists tei_tokens_read on public.tei_tokens;
create policy tei_tokens_read
  on public.tei_tokens
  for select
  using (public.is_authenticated());

-- ---------------------------------------------------------------------------
-- Editor-owned tables: authenticated SELECT + editor INSERT/UPDATE
-- ---------------------------------------------------------------------------

-- tei_translations
drop policy if exists tei_translations_read on public.tei_translations;
create policy tei_translations_read
  on public.tei_translations
  for select
  using (public.is_authenticated());

drop policy if exists tei_translations_insert on public.tei_translations;
create policy tei_translations_insert
  on public.tei_translations
  for insert
  with check (public.is_editor(auth.uid()));

drop policy if exists tei_translations_update on public.tei_translations;
create policy tei_translations_update
  on public.tei_translations
  for update
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- tei_assertions
drop policy if exists tei_assertions_read on public.tei_assertions;
create policy tei_assertions_read
  on public.tei_assertions
  for select
  using (public.is_authenticated());

drop policy if exists tei_assertions_insert on public.tei_assertions;
create policy tei_assertions_insert
  on public.tei_assertions
  for insert
  with check (public.is_editor(auth.uid()));

drop policy if exists tei_assertions_update on public.tei_assertions;
create policy tei_assertions_update
  on public.tei_assertions
  for update
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- tei_lemmata
drop policy if exists tei_lemmata_read on public.tei_lemmata;
create policy tei_lemmata_read
  on public.tei_lemmata
  for select
  using (public.is_authenticated());

drop policy if exists tei_lemmata_insert on public.tei_lemmata;
create policy tei_lemmata_insert
  on public.tei_lemmata
  for insert
  with check (public.is_editor(auth.uid()));

drop policy if exists tei_lemmata_update on public.tei_lemmata;
create policy tei_lemmata_update
  on public.tei_lemmata
  for update
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- tei_lemma_forms
drop policy if exists tei_lemma_forms_read on public.tei_lemma_forms;
create policy tei_lemma_forms_read
  on public.tei_lemma_forms
  for select
  using (public.is_authenticated());

drop policy if exists tei_lemma_forms_insert on public.tei_lemma_forms;
create policy tei_lemma_forms_insert
  on public.tei_lemma_forms
  for insert
  with check (public.is_editor(auth.uid()));

drop policy if exists tei_lemma_forms_update on public.tei_lemma_forms;
create policy tei_lemma_forms_update
  on public.tei_lemma_forms
  for update
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- tei_entry_lemma_forms
drop policy if exists tei_entry_lemma_forms_read on public.tei_entry_lemma_forms;
create policy tei_entry_lemma_forms_read
  on public.tei_entry_lemma_forms
  for select
  using (public.is_authenticated());

drop policy if exists tei_entry_lemma_forms_insert on public.tei_entry_lemma_forms;
create policy tei_entry_lemma_forms_insert
  on public.tei_entry_lemma_forms
  for insert
  with check (public.is_editor(auth.uid()));

drop policy if exists tei_entry_lemma_forms_update on public.tei_entry_lemma_forms;
create policy tei_entry_lemma_forms_update
  on public.tei_entry_lemma_forms
  for update
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- tei_lemma_aliases
drop policy if exists tei_lemma_aliases_read on public.tei_lemma_aliases;
create policy tei_lemma_aliases_read
  on public.tei_lemma_aliases
  for select
  using (public.is_authenticated());

drop policy if exists tei_lemma_aliases_insert on public.tei_lemma_aliases;
create policy tei_lemma_aliases_insert
  on public.tei_lemma_aliases
  for insert
  with check (public.is_editor(auth.uid()));

drop policy if exists tei_lemma_aliases_update on public.tei_lemma_aliases;
create policy tei_lemma_aliases_update
  on public.tei_lemma_aliases
  for update
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- tei_entry_alignments
drop policy if exists tei_entry_alignments_read on public.tei_entry_alignments;
create policy tei_entry_alignments_read
  on public.tei_entry_alignments
  for select
  using (public.is_authenticated());

drop policy if exists tei_entry_alignments_insert on public.tei_entry_alignments;
create policy tei_entry_alignments_insert
  on public.tei_entry_alignments
  for insert
  with check (public.is_editor(auth.uid()));

drop policy if exists tei_entry_alignments_update on public.tei_entry_alignments;
create policy tei_entry_alignments_update
  on public.tei_entry_alignments
  for update
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

commit;

begin;

-- Legacy-ID extraction tables for the outputs-to-search path.
-- These tables intentionally reference public.entries.entry_id, not TEI rows.
-- TEI remapping remains a later bridge/indexer step.

insert into public.sources (code, name, notes) values
  ('DIOSC_DMM', 'Dioscorides, De Materia Medica', 'Dioscorides CSV bridge / legacy vocab extraction')
on conflict (code) do nothing;

create table if not exists public.legacy_vocab_lemma_forms (
  id uuid primary key default gen_random_uuid(),
  source_code text not null references public.sources(code) on delete restrict,
  form_grc text not null,
  form_normalized text not null,
  status text not null default 'draft'
    check (status in ('draft', 'needs_review', 'confirmed')),
  source text,
  confidence numeric,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_code, form_normalized)
);

create index if not exists legacy_vocab_lemma_forms_normalized_idx
  on public.legacy_vocab_lemma_forms (form_normalized text_pattern_ops);

create index if not exists legacy_vocab_lemma_forms_source_idx
  on public.legacy_vocab_lemma_forms (source_code);

create table if not exists public.legacy_vocab_entry_lemma_forms (
  entry_id text not null references public.entries(entry_id) on delete cascade,
  lemma_form_id uuid not null references public.legacy_vocab_lemma_forms(id) on delete cascade,
  role text not null default 'headword'
    check (role in ('headword', 'mentioned')),
  confidence numeric,
  created_at timestamptz not null default now(),
  primary key (entry_id, lemma_form_id, role)
);

create index if not exists legacy_vocab_entry_lemma_forms_form_idx
  on public.legacy_vocab_entry_lemma_forms (lemma_form_id);

create table if not exists public.legacy_vocab_assertions (
  id uuid primary key default gen_random_uuid(),
  entry_id text not null references public.entries(entry_id) on delete cascade,
  assertion_type text not null
    check (assertion_type in ('quality', 'part', 'process', 'other')),
  payload jsonb not null,
  status text not null default 'draft'
    check (status in ('draft', 'needs_review', 'confirmed')),
  source text,
  is_stale boolean not null default false,
  confidence numeric,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint legacy_vocab_quality_has_axis check (
    assertion_type != 'quality' OR payload ? 'axis'
  )
);

create index if not exists legacy_vocab_assertions_entry_idx
  on public.legacy_vocab_assertions (entry_id);

create index if not exists legacy_vocab_assertions_quality_axis_idx
  on public.legacy_vocab_assertions (assertion_type, (payload->>'axis'))
  where assertion_type = 'quality';

create index if not exists legacy_vocab_assertions_quality_degree_idx
  on public.legacy_vocab_assertions (assertion_type, (payload->>'degree'))
  where assertion_type = 'quality';

drop trigger if exists trg_legacy_vocab_lemma_forms_updated on public.legacy_vocab_lemma_forms;
create trigger trg_legacy_vocab_lemma_forms_updated
  before update on public.legacy_vocab_lemma_forms
  for each row execute function public.tei_entries_set_updated_at();

drop trigger if exists trg_legacy_vocab_assertions_updated on public.legacy_vocab_assertions;
create trigger trg_legacy_vocab_assertions_updated
  before update on public.legacy_vocab_assertions
  for each row execute function public.tei_entries_set_updated_at();

alter table public.legacy_vocab_lemma_forms enable row level security;
alter table public.legacy_vocab_entry_lemma_forms enable row level security;
alter table public.legacy_vocab_assertions enable row level security;

drop policy if exists legacy_vocab_lemma_forms_read on public.legacy_vocab_lemma_forms;
create policy legacy_vocab_lemma_forms_read
  on public.legacy_vocab_lemma_forms
  for select
  using (true);

drop policy if exists legacy_vocab_entry_lemma_forms_read on public.legacy_vocab_entry_lemma_forms;
create policy legacy_vocab_entry_lemma_forms_read
  on public.legacy_vocab_entry_lemma_forms
  for select
  using (true);

drop policy if exists legacy_vocab_assertions_read on public.legacy_vocab_assertions;
create policy legacy_vocab_assertions_read
  on public.legacy_vocab_assertions
  for select
  using (true);

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    grant select on table
      public.legacy_vocab_lemma_forms,
      public.legacy_vocab_entry_lemma_forms,
      public.legacy_vocab_assertions
    to anon;
  end if;

  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    grant select on table
      public.legacy_vocab_lemma_forms,
      public.legacy_vocab_entry_lemma_forms,
      public.legacy_vocab_assertions
    to authenticated;
  end if;
end
$$;

commit;

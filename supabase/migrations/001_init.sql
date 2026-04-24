-- 001_init.sql
-- Ancient Simples MVP schema
-- Historical binding docs are archived under:
-- archive/docs/legacy_pre_tei_first/ and archive/docs/duplicates/

begin;

-- Extensions (Supabase convention: install into `extensions` schema).
create extension if not exists pgcrypto with schema extensions;
create extension if not exists pg_trgm with schema extensions;

-- ---------------------------------------------------------------------------
-- Core helpers
-- ---------------------------------------------------------------------------

create or replace function public.is_authenticated()
returns boolean
language sql
stable
as $$
  select auth.role() = 'authenticated';
$$;

-- Greek normalization (must preserve iota subscript U+0345, strip other accents/breathings).
--
-- Supabase-hosted Postgres does not expose a Unicode NFD/NFC function in all tiers/versions.
-- To keep one canonical normalization behavior inside Postgres, we use a deterministic
-- `translate()` map generated from the same rules used in the CSV pipeline:
-- - lowercase
-- - strip combining marks except U+0345 (iota subscript)
-- - leave output in NFC where possible (e.g., ᾴ → ᾳ)
--
-- NOTE: This covers all Greek / Greek Extended codepoints where the normalization changes the
-- character and results in a single codepoint output (true for our corpus).
create or replace function public.normalize_greek(input_text text)
returns text
language plpgsql
immutable
as $$
declare
  from_chars text :=
    U&'\\0300\\0301\\0302\\0303\\0304\\0305\\0306\\0307\\0308\\0309\\030A\\030B\\030C\\030D\\030E\\030F\\0310\\0311\\0312\\0313\\0314\\0315\\0316\\0317' ||
    U&'\\0318\\0319\\031A\\031B\\031C\\031D\\031E\\031F\\0320\\0321\\0322\\0323\\0324\\0325\\0326\\0327\\0328\\0329\\032A\\032B\\032C\\032D\\032E\\032F' ||
    U&'\\0330\\0331\\0332\\0333\\0334\\0335\\0336\\0337\\0338\\0339\\033A\\033B\\033C\\033D\\033E\\033F\\0340\\0341\\0342\\0343\\0344\\0346\\0347\\0348' ||
    U&'\\0349\\034A\\034B\\034C\\034D\\034E\\0350\\0351\\0352\\0353\\0354\\0355\\0356\\0357\\0358\\0359\\035A\\035B\\035C\\035D\\035E\\035F\\0360\\0361' ||
    U&'\\0362\\0363\\0364\\0365\\0366\\0367\\0368\\0369\\036A\\036B\\036C\\036D\\036E\\036F\\0374\\037E\\0385\\0386\\0387\\0388\\0389\\038A\\038C\\038E' ||
    U&'\\038F\\0390\\03AA\\03AB\\03AC\\03AD\\03AE\\03AF\\03B0\\03CA\\03CB\\03CC\\03CD\\03CE\\03D3\\03D4\\1F00\\1F01\\1F02\\1F03\\1F04\\1F05\\1F06\\1F07' ||
    U&'\\1F08\\1F09\\1F0A\\1F0B\\1F0C\\1F0D\\1F0E\\1F0F\\1F10\\1F11\\1F12\\1F13\\1F14\\1F15\\1F18\\1F19\\1F1A\\1F1B\\1F1C\\1F1D\\1F20\\1F21\\1F22\\1F23' ||
    U&'\\1F24\\1F25\\1F26\\1F27\\1F28\\1F29\\1F2A\\1F2B\\1F2C\\1F2D\\1F2E\\1F2F\\1F30\\1F31\\1F32\\1F33\\1F34\\1F35\\1F36\\1F37\\1F38\\1F39\\1F3A\\1F3B' ||
    U&'\\1F3C\\1F3D\\1F3E\\1F3F\\1F40\\1F41\\1F42\\1F43\\1F44\\1F45\\1F48\\1F49\\1F4A\\1F4B\\1F4C\\1F4D\\1F50\\1F51\\1F52\\1F53\\1F54\\1F55\\1F56\\1F57' ||
    U&'\\1F59\\1F5B\\1F5D\\1F5F\\1F60\\1F61\\1F62\\1F63\\1F64\\1F65\\1F66\\1F67\\1F68\\1F69\\1F6A\\1F6B\\1F6C\\1F6D\\1F6E\\1F6F\\1F70\\1F71\\1F72\\1F73' ||
    U&'\\1F74\\1F75\\1F76\\1F77\\1F78\\1F79\\1F7A\\1F7B\\1F7C\\1F7D\\1F80\\1F81\\1F82\\1F83\\1F84\\1F85\\1F86\\1F87\\1F88\\1F89\\1F8A\\1F8B\\1F8C\\1F8D' ||
    U&'\\1F8E\\1F8F\\1F90\\1F91\\1F92\\1F93\\1F94\\1F95\\1F96\\1F97\\1F98\\1F99\\1F9A\\1F9B\\1F9C\\1F9D\\1F9E\\1F9F\\1FA0\\1FA1\\1FA2\\1FA3\\1FA4\\1FA5' ||
    U&'\\1FA6\\1FA7\\1FA8\\1FA9\\1FAA\\1FAB\\1FAC\\1FAD\\1FAE\\1FAF\\1FB0\\1FB1\\1FB2\\1FB4\\1FB6\\1FB7\\1FB8\\1FB9\\1FBA\\1FBB\\1FBE\\1FC1\\1FC2\\1FC4' ||
    U&'\\1FC6\\1FC7\\1FC8\\1FC9\\1FCA\\1FCB\\1FCD\\1FCE\\1FCF\\1FD0\\1FD1\\1FD2\\1FD3\\1FD6\\1FD7\\1FD8\\1FD9\\1FDA\\1FDB\\1FDD\\1FDE\\1FDF\\1FE0\\1FE1' ||
    U&'\\1FE2\\1FE3\\1FE4\\1FE5\\1FE6\\1FE7\\1FE8\\1FE9\\1FEA\\1FEB\\1FEC\\1FED\\1FEE\\1FEF\\1FF2\\1FF4\\1FF6\\1FF7\\1FF8\\1FF9\\1FFA\\1FFB\\1FFD';
  to_chars text :=
    U&'\\02B9\\003B\\00A8\\03B1\\00B7\\03B5\\03B7\\03B9\\03BF\\03C5\\03C9\\03B9\\03B9\\03C5\\03B1\\03B5\\03B7\\03B9\\03C5\\03B9\\03C5\\03BF\\03C5\\03C9' ||
    U&'\\03D2\\03D2\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B1\\03B5\\03B5\\03B5\\03B5\\03B5\\03B5' ||
    U&'\\03B5\\03B5\\03B5\\03B5\\03B5\\03B5\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B7\\03B9\\03B9' ||
    U&'\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03B9\\03BF\\03BF\\03BF\\03BF\\03BF\\03BF\\03BF\\03BF\\03BF\\03BF' ||
    U&'\\03BF\\03BF\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C9\\03C9\\03C9\\03C9\\03C9\\03C9\\03C9\\03C9\\03C9\\03C9' ||
    U&'\\03C9\\03C9\\03C9\\03C9\\03C9\\03C9\\03B1\\03B1\\03B5\\03B5\\03B7\\03B7\\03B9\\03B9\\03BF\\03BF\\03C5\\03C5\\03C9\\03C9\\1FB3\\1FB3\\1FB3\\1FB3' ||
    U&'\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FB3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3\\1FC3' ||
    U&'\\1FC3\\1FC3\\1FC3\\1FC3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\1FF3\\03B1\\03B1\\1FB3\\1FB3' ||
    U&'\\03B1\\1FB3\\03B1\\03B1\\03B1\\03B1\\03B9\\00A8\\1FC3\\1FC3\\03B7\\1FC3\\03B5\\03B5\\03B7\\03B7\\1FBF\\1FBF\\1FBF\\03B9\\03B9\\03B9\\03B9\\03B9' ||
    U&'\\03B9\\03B9\\03B9\\03B9\\03B9\\1FFE\\1FFE\\1FFE\\03C5\\03C5\\03C5\\03C5\\03C1\\03C1\\03C5\\03C5\\03C5\\03C5\\03C5\\03C5\\03C1\\00A8\\00A8\\0060' ||
    U&'\\1FF3\\1FF3\\03C9\\1FF3\\03BF\\03BF\\03C9\\03C9\\00B4';
begin
  return translate(lower(coalesce(input_text, '')), from_chars, to_chars);
end;
$$;

create or replace function public.set_updated_fields()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  if new.updated_by is null then
    new.updated_by := auth.uid();
  end if;
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Auth profile / roles
-- ---------------------------------------------------------------------------

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  role text not null default 'viewer' check (role in ('viewer', 'editor')),
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.is_editor(user_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.profiles p
    where p.id = user_id
      and p.role = 'editor'
  );
$$;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, role, display_name)
  values (new.id, 'viewer', coalesce(new.raw_user_meta_data->>'display_name', null))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ---------------------------------------------------------------------------
-- Controlled vocab / lookup tables
-- ---------------------------------------------------------------------------

create table if not exists public.sources (
  code text primary key,
  name text not null,
  notes text
);

create table if not exists public.parts (
  part_id text primary key,
  greek text not null,
  english text not null default '',
  category text not null check (category in ('vegetable', 'animal', 'mineral', 'all')),
  notes text not null default ''
);

create table if not exists public.preparations (
  prep_id text primary key,
  greek text not null,
  english text not null default '',
  scope text not null check (scope in ('vegetable', 'animal', 'mineral', 'all')),
  notes text not null default ''
);

create table if not exists public.lemmata (
  lemma_id text primary key,
  headword_gr text not null,
  headword_normalized text not null,
  headword_en text not null default '',
  parent_lemma text references public.lemmata(lemma_id) on delete set null,
  relationship text not null default '' check (relationship in ('', 'subtype', 'synonym')),
  category text not null check (category in ('vegetable', 'animal', 'mineral')),
  notes text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id)
);

create table if not exists public.entries (
  entry_id text primary key,
  source text not null references public.sources(code) on delete restrict,
  ref text not null,
  chapter_title_gr text not null default '',
  chapter_title_en text not null default '',
  part_id text references public.parts(part_id) on delete set null,
  greek text not null,
  greek_normalized text not null,
  translation text not null default '',
  trans_status text not null default 'draft' check (trans_status in ('draft', 'review', 'final')),
  word_count integer,
  notes text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id)
);

create table if not exists public.entry_lemmata (
  entry_id text not null references public.entries(entry_id) on delete cascade,
  lemma_id text not null references public.lemmata(lemma_id) on delete restrict,
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),
  primary key (entry_id, lemma_id)
);

create table if not exists public.entry_preparations (
  entry_id text not null references public.entries(entry_id) on delete cascade,
  prep_id text not null references public.preparations(prep_id) on delete restrict,
  is_primary boolean not null default false,
  notes text not null default '',
  created_at timestamptz not null default now(),
  primary key (entry_id, prep_id)
);

create table if not exists public.editions (
  edition_id uuid primary key default extensions.gen_random_uuid(),
  code text not null unique,
  title text not null,
  notes text not null default ''
);

create table if not exists public.entry_references (
  entry_reference_id uuid primary key default extensions.gen_random_uuid(),
  entry_id text not null references public.entries(entry_id) on delete cascade,
  edition_id uuid not null references public.editions(edition_id) on delete restrict,
  ref_type text not null,
  volume text not null default '',
  page_start integer,
  page_end integer,
  notes text not null default '',
  created_at timestamptz not null default now(),
  unique (entry_id, edition_id, ref_type)
);

create table if not exists public.annotations (
  annotation_id uuid primary key default extensions.gen_random_uuid(),
  entry_id text not null references public.entries(entry_id) on delete cascade,
  token_start integer,
  token_end integer,
  quote text not null,
  prefix_context text not null default '',
  suffix_context text not null default '',
  body text not null,
  category text not null default '',
  status text not null default 'stable' check (status in ('stable', 'reanchored', 'needs_review')),
  created_at timestamptz not null default now(),
  created_by uuid references auth.users(id),
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id)
);

-- ---------------------------------------------------------------------------
-- Normalization + timestamp triggers
-- ---------------------------------------------------------------------------

create or replace function public.entries_set_normalized()
returns trigger
language plpgsql
as $$
begin
  new.greek_normalized := public.normalize_greek(new.greek);
  return new;
end;
$$;

create or replace function public.lemmata_set_normalized()
returns trigger
language plpgsql
as $$
begin
  new.headword_normalized := public.normalize_greek(new.headword_gr);
  return new;
end;
$$;

drop trigger if exists trg_entries_normalize on public.entries;
create trigger trg_entries_normalize
  before insert or update of greek
  on public.entries
  for each row execute procedure public.entries_set_normalized();

drop trigger if exists trg_lemmata_normalize on public.lemmata;
create trigger trg_lemmata_normalize
  before insert or update of headword_gr
  on public.lemmata
  for each row execute procedure public.lemmata_set_normalized();

drop trigger if exists trg_entries_updated on public.entries;
create trigger trg_entries_updated
  before update on public.entries
  for each row execute procedure public.set_updated_fields();

drop trigger if exists trg_lemmata_updated on public.lemmata;
create trigger trg_lemmata_updated
  before update on public.lemmata
  for each row execute procedure public.set_updated_fields();

drop trigger if exists trg_annotations_updated on public.annotations;
create trigger trg_annotations_updated
  before update on public.annotations
  for each row execute procedure public.set_updated_fields();

-- ---------------------------------------------------------------------------
-- Indices (Phase 1 search + basic performance)
-- ---------------------------------------------------------------------------

create index if not exists entries_source_idx on public.entries (source);
create index if not exists entries_ref_idx on public.entries (ref);
create index if not exists entries_greek_norm_prefix_idx
  on public.entries (greek_normalized text_pattern_ops);
create index if not exists entries_translation_trgm_idx
  on public.entries using gin (translation extensions.gin_trgm_ops);

create index if not exists lemmata_headword_norm_prefix_idx
  on public.lemmata (headword_normalized text_pattern_ops);

create index if not exists entry_lemmata_lemma_id_idx on public.entry_lemmata (lemma_id);
create index if not exists annotations_entry_id_idx on public.annotations (entry_id);
create index if not exists annotations_status_idx on public.annotations (status);

-- ---------------------------------------------------------------------------
-- RLS + policies
-- ---------------------------------------------------------------------------

alter table public.profiles enable row level security;
alter table public.sources enable row level security;
alter table public.parts enable row level security;
alter table public.preparations enable row level security;
alter table public.lemmata enable row level security;
alter table public.entries enable row level security;
alter table public.entry_lemmata enable row level security;
alter table public.entry_preparations enable row level security;
alter table public.editions enable row level security;
alter table public.entry_references enable row level security;
alter table public.annotations enable row level security;

-- profiles: user can read own; editors can read all.
drop policy if exists profiles_select_self on public.profiles;
create policy profiles_select_self
  on public.profiles
  for select
  using (id = auth.uid() or public.is_editor(auth.uid()));

-- profiles: only editors can update roles / profiles.
drop policy if exists profiles_editor_write on public.profiles;
create policy profiles_editor_write
  on public.profiles
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- sources: authenticated read; editor write.
drop policy if exists sources_read on public.sources;
create policy sources_read
  on public.sources
  for select
  using (public.is_authenticated());

drop policy if exists sources_write on public.sources;
create policy sources_write
  on public.sources
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- parts / preparations / lemmata: authenticated read; editor write.
drop policy if exists parts_read on public.parts;
create policy parts_read
  on public.parts
  for select
  using (public.is_authenticated());

drop policy if exists parts_write on public.parts;
create policy parts_write
  on public.parts
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

drop policy if exists preparations_read on public.preparations;
create policy preparations_read
  on public.preparations
  for select
  using (public.is_authenticated());

drop policy if exists preparations_write on public.preparations;
create policy preparations_write
  on public.preparations
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

drop policy if exists lemmata_read on public.lemmata;
create policy lemmata_read
  on public.lemmata
  for select
  using (public.is_authenticated());

drop policy if exists lemmata_write on public.lemmata;
create policy lemmata_write
  on public.lemmata
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- entries: authenticated read; editor write.
drop policy if exists entries_read on public.entries;
create policy entries_read
  on public.entries
  for select
  using (public.is_authenticated());

drop policy if exists entries_write on public.entries;
create policy entries_write
  on public.entries
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- junction tables: authenticated read; editor write.
drop policy if exists entry_lemmata_read on public.entry_lemmata;
create policy entry_lemmata_read
  on public.entry_lemmata
  for select
  using (public.is_authenticated());

drop policy if exists entry_lemmata_write on public.entry_lemmata;
create policy entry_lemmata_write
  on public.entry_lemmata
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

drop policy if exists entry_preparations_read on public.entry_preparations;
create policy entry_preparations_read
  on public.entry_preparations
  for select
  using (public.is_authenticated());

drop policy if exists entry_preparations_write on public.entry_preparations;
create policy entry_preparations_write
  on public.entry_preparations
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

drop policy if exists editions_read on public.editions;
create policy editions_read
  on public.editions
  for select
  using (public.is_authenticated());

drop policy if exists editions_write on public.editions;
create policy editions_write
  on public.editions
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

drop policy if exists entry_references_read on public.entry_references;
create policy entry_references_read
  on public.entry_references
  for select
  using (public.is_authenticated());

drop policy if exists entry_references_write on public.entry_references;
create policy entry_references_write
  on public.entry_references
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

drop policy if exists annotations_read on public.annotations;
create policy annotations_read
  on public.annotations
  for select
  using (public.is_authenticated());

drop policy if exists annotations_write on public.annotations;
create policy annotations_write
  on public.annotations
  for all
  using (public.is_editor(auth.uid()))
  with check (public.is_editor(auth.uid()));

-- ---------------------------------------------------------------------------
-- Seed minimal lookup rows needed for import workflows.
-- ---------------------------------------------------------------------------

insert into public.sources (code, name, notes) values
  ('GAL_SMT', 'Galen, De simplicium medicamentorum', ''),
  ('GAL_ALIM', 'Galen, De alimentorum facultatibus', ''),
  ('ORIB_CM', 'Oribasius, Collectiones Medicae 15', ''),
  ('AET_LM', 'Aetius, Libri Medicinales I–II', '')
on conflict (code) do nothing;

insert into public.editions (code, title, notes) values
  ('KUHN', 'Kühn edition (legacy volume/page ranges)', 'Imported from entries.csv e_vol/e_page_start/e_page_end')
on conflict (code) do nothing;

commit;

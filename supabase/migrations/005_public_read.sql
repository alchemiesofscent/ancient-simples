begin;

-- Public read-only MVP: allow anonymous visitors to read core content tables.
--
-- Writes remain restricted to authenticated editors via existing *_write policies.

drop policy if exists sources_read on public.sources;
create policy sources_read
  on public.sources
  for select
  using (true);

drop policy if exists parts_read on public.parts;
create policy parts_read
  on public.parts
  for select
  using (true);

drop policy if exists preparations_read on public.preparations;
create policy preparations_read
  on public.preparations
  for select
  using (true);

drop policy if exists lemmata_read on public.lemmata;
create policy lemmata_read
  on public.lemmata
  for select
  using (true);

drop policy if exists entries_read on public.entries;
create policy entries_read
  on public.entries
  for select
  using (true);

drop policy if exists entry_lemmata_read on public.entry_lemmata;
create policy entry_lemmata_read
  on public.entry_lemmata
  for select
  using (true);

drop policy if exists entry_preparations_read on public.entry_preparations;
create policy entry_preparations_read
  on public.entry_preparations
  for select
  using (true);

drop policy if exists editions_read on public.editions;
create policy editions_read
  on public.editions
  for select
  using (true);

drop policy if exists entry_references_read on public.entry_references;
create policy entry_references_read
  on public.entry_references
  for select
  using (true);

-- Ensure PostgREST roles can select (RLS still applies).
do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    grant select on table
      public.sources,
      public.parts,
      public.preparations,
      public.lemmata,
      public.entries,
      public.entry_lemmata,
      public.entry_preparations,
      public.editions,
      public.entry_references
    to anon;
  end if;

  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    grant select on table
      public.sources,
      public.parts,
      public.preparations,
      public.lemmata,
      public.entries,
      public.entry_lemmata,
      public.entry_preparations,
      public.editions,
      public.entry_references
    to authenticated;
  end if;
end
$$;

commit;


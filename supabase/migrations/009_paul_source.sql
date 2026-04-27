begin;

insert into public.sources (code, name, notes)
values
  (
    'PAUL_AEG',
    'Paul of Aegina, Epitome Book 7.3',
    'Paul CSV bridge / legacy vocab extraction'
  )
on conflict (code) do update
set
  name = excluded.name,
  notes = excluded.notes;

commit;

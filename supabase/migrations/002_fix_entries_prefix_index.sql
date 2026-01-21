begin;

-- Fix oversized btree index entries_greek_norm_prefix_idx by indexing a bounded prefix.
-- We keep the normalization stored in `entries.greek_normalized` (set by trigger).

drop index if exists public.entries_greek_norm_prefix_idx;

alter table public.entries
  add column if not exists greek_normalized_prefix text
    generated always as (left(greek_normalized, 512)) stored;

create index if not exists entries_greek_norm_prefix_idx
  on public.entries (greek_normalized_prefix text_pattern_ops);

commit;


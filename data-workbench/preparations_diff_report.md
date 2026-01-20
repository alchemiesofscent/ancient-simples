# Preparations split diff report

- Generated: `2026-01-20T21:38:06+00:00`
- Workbook: `simples.xlsx`

## (a) Removed from parts.csv
- _(none)_

## (b) Added to parts.csv
- _(none)_

## (c) Removed from preparations.csv
- `PR003` ἕψησις — boiling/cooking (scope: all)
- `PR004` πεπλυμένος — washed (scope: all)

## (d) Added to preparations.csv
- `PR001` κεκαυμένος — burnt/calcined (scope: all)
- `PR002` ἀφέψημα — decoction (scope: all)

## (e) Rule for preparations vs residue nouns
- Deterministic rule: preparations are adjectival or process terms that modify a base substance; residue/product nouns (e.g., σποδός, τέφρα) remain parts/materials even if produced by a process.

## (f) Downstream consistency changes
- `κεκαυμένος` and `ἀφέψημα` remain preparations (not parts).
- Linking for preparations will be emitted as `entry_preparations.csv` (import-only), analogous to `lemma_ids` → `entry_lemmata`.

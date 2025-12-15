# preparations.csv update report

- Generated: `2025-12-15T18:34:00+00:00`

## Current controlled vocabulary
- `PR001` κεκαυμένος — burnt/calcined (scope: all)
- `PR002` ἀφέψημα — decoction (scope: all)
- `PR003` ἕψησις — boiling/cooking (scope: all)
- `PR004` πεπλυμένος — washed (scope: all)

## Notes
- Includes PR003 (ἕψησις) and PR004 (πεπλυμένος) as promoted preparation/process terms.

## Matching policy
- `entry_preparations.csv` linking uses strict tokenization + normalization + exact token match against explicit controlled forms per preparation.

## Exclusions
- `ωμοτριβες`: lexicalized oil-type qualifier (not a preparation/state in this corpus).
- `ξηρα`: lexicalized subtype adjective in resin/oil naming (e.g., πιτυινη ἡ ξηρά), not a generic drying preparation/state.

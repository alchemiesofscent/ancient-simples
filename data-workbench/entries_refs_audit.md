# entries.csv ref-sequence audit

- Input: `data-workbench/entries.csv`
- Total rows: **2135**
- Sources: AET_LM, GAL_ALIM, GAL_SMT, ORIB_CM

This audit checks: ref uniqueness per source, sequential numbering
within each book/chapter group, book-level contiguity, ref-depth
consistency, and CSV-order drift. It cross-references
`entries_qc.md` to see whether any detected gaps are documented.

## Summary

| Source | Entries | `~N` dup refs | Bad dup refs | Off-modal depth | Gap groups | Non-1 starts | Book issues | Natural order |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| AET_LM | 624 | 6 | 0 | 0 | 0 | 0 | 0 | yes |
| GAL_ALIM | 35 | 0 | 0 | 0 | 3 | 3 | 3 | no |
| GAL_SMT | 639 | 0 | 0 | 6 | 0 | 0 | 2 | yes |
| ORIB_CM | 837 | 0 | 0 | 70 | 0 | 0 | 0 | yes |

- **`~N` dup refs** — structural refs shared by multiple sibling entries (all resolved via `~1/~2/…` entry_id suffixes; expected/benign).
- **Bad dup refs** — a ref appears on multiple rows but the entry_ids are not all `~N`-suffixed (indicates a real collision).
- **Off-modal depth** — rows whose ref component count differs from the source's majority depth (often `prooimion` or a structural quirk).
- **Gap groups** — prefix groups with missing last-component values between observed min and max.
- **Non-1 starts** — prefix groups whose smallest last-component is not 1 (possible leading gap or offset numbering convention).
- **Book issues** — book-level chapter-contiguity issues.
- **Natural order** — whether CSV row order matches natural ref order.

> Note: `entries_qc.md` (the output of `data-workbench/make_entries.py`) only records totals, skipped-row counts, and a random 10-row sample. It does not enumerate gaps — so any non-zero gap/book-issue count below is currently **undocumented** in that file unless otherwise noted.

## AET_LM

- Entries: **624**
- Duplicate refs resolved via `~N` entry_id suffix (expected): **6**
  - `1.209` ×2
  - `1.241` ×4
  - `1.318` ×3
  - `1.7` ×2
  - `1.77` ×2
  - `2.122` ×2
- Ref depth distribution: 2-tuple: 624
- Modal depth: **2**
- CSV rows in natural ref order: **yes**
- Groups with internal gaps: none
- Groups not starting at 1: none
- Book-level chapter contiguity issues: none

## GAL_ALIM

- Entries: **35**
- Duplicate refs: none
- Ref depth distribution: 2-tuple: 35
- Modal depth: **2**
- CSV rows in natural ref order: **no**
  - First divergences:
    - position 7 (csv row 647): csv has `1.28`, expected `1.27`
    - position 8 (csv row 648): csv has `1.27`, expected `1.28`
    - position 22 (csv row 662): csv has `2.35`, expected `2.34`
    - position 23 (csv row 663): csv has `2.34`, expected `2.35`
- Groups with internal gaps: **3**
  - prefix `1`: 9 values in 9..32, missing 10, 13–17, 19–24, 29–31
  - prefix `2`: 22 values in 3..69, missing 5, 7, 12–18, 21–23, 25, 28–33, 36–39, 41, 44–49, 51–59, 61–66
  - prefix `3`: 4 values in 15..39, missing 17–37
- Groups not starting at 1 (or 0 for prooimion): **3**
  - prefix `1`: starts at 9, ends at 32
  - prefix `2`: starts at 3, ends at 69
  - prefix `3`: starts at 15, ends at 39
- Book-level chapter contiguity issues: **3**
  - book 1: 9 chapters in 9..32; starts at chapter 9; missing chapters 10, 13–17, 19–24, 29–31
  - book 2: 22 chapters in 3..69; starts at chapter 3; missing chapters 5, 7, 12–18, 21–23, 25, 28–33, 36–39, 41, 44–49, 51–59, 61–66
  - book 3: 4 chapters in 15..39; starts at chapter 15; missing chapters 17–37
- Gap entry_ids explicitly mentioned in `entries_qc.md`: **0**

## GAL_SMT

- Entries: **639**
- Duplicate refs: none
- Ref depth distribution: 2-tuple: 6, 3-tuple: 633
- Modal depth: **3**
- Off-modal-depth rows: **6**
  - row 2 `GAL_SMT-6.prooimion` ref=`6.prooimion` (depth 2)
  - row 171 `GAL_SMT-7.prooimion` ref=`7.prooimion` (depth 2)
  - row 296 `GAL_SMT-8.prooimion` ref=`8.prooimion` (depth 2)
  - row 480 `GAL_SMT-9.prooimion` ref=`9.prooimion` (depth 2)
  - row 546 `GAL_SMT-10.1` ref=`10.1` (depth 2)
  - row 577 `GAL_SMT-11.prooimion` ref=`11.prooimion` (depth 2)
- CSV rows in natural ref order: **yes**
- Groups with internal gaps: none
- Groups not starting at 1: none
- Book-level chapter contiguity issues: **2**
  - book 7: 3 chapters in 10..12; starts at chapter 10
  - book 8: 12 chapters in 13..24; starts at chapter 13

## ORIB_CM

- Entries: **837**
- Duplicate refs: none
- Ref depth distribution: 3-tuple: 70, 4-tuple: 767
- Modal depth: **4**
- Off-modal-depth rows: **70**
  - row 1443 `ORIB_CM-15.2.1` ref=`15.2.1` (depth 3)
  - row 1444 `ORIB_CM-15.2.2` ref=`15.2.2` (depth 3)
  - row 1445 `ORIB_CM-15.2.3` ref=`15.2.3` (depth 3)
  - row 1446 `ORIB_CM-15.2.4` ref=`15.2.4` (depth 3)
  - row 1447 `ORIB_CM-15.2.5` ref=`15.2.5` (depth 3)
  - row 1448 `ORIB_CM-15.2.6` ref=`15.2.6` (depth 3)
  - row 1449 `ORIB_CM-15.2.7` ref=`15.2.7` (depth 3)
  - row 1450 `ORIB_CM-15.2.8` ref=`15.2.8` (depth 3)
  - row 1451 `ORIB_CM-15.2.9` ref=`15.2.9` (depth 3)
  - row 1452 `ORIB_CM-15.2.10` ref=`15.2.10` (depth 3)
  - row 1453 `ORIB_CM-15.2.11` ref=`15.2.11` (depth 3)
  - row 1454 `ORIB_CM-15.2.12` ref=`15.2.12` (depth 3)
  - row 1455 `ORIB_CM-15.2.13` ref=`15.2.13` (depth 3)
  - row 1456 `ORIB_CM-15.2.14` ref=`15.2.14` (depth 3)
  - row 1457 `ORIB_CM-15.2.15` ref=`15.2.15` (depth 3)
  - … and 55 more
- CSV rows in natural ref order: **yes**
- Groups with internal gaps: none
- Groups not starting at 1: none
- Book-level chapter contiguity issues: none


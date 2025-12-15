# Ancient Simples Database: Data Restructuring Specification

This document governs how the legacy Excel workbook (`Simples.xlsx`, ~1,699 entries) becomes normalized CSVs for import into Supabase/PostgreSQL. It aligns with the MVP architecture (Next.js + Supabase) and preserves a CSV-first workflow for scholarly review.

**Input:** `/mnt/user-data/uploads/Simples.xlsx`

**Required Outputs:**
- `entries.csv`
- `lemmata.csv`
- `parts.csv`
- `preparations.csv`
- `modern_ids.csv` (template)
- Review aides: `lemmata_review.csv`, `unmatched_terms.csv`
- Linking artefacts (import-only): `entry_preparations.csv`

> All CSVs must be UTF-8, comma-separated, quoted as needed, and checked into version control before database import.

---

## 1. Data Model Overview
Supabase/PostgreSQL hosts the canonical schema. CSVs are staging artifacts.

```
Sources ─┐
         ├─> Entries ─┐
         │            ├─> Entry_Lemmata (junction)
Lemmata ─┘            │
                      └─> Annotations (later)
Parts ─────────────────┘
```

- `entries.csv` supplies row-level text content.
- `lemmata.csv` defines normalized headwords with parent/child relations.
- `parts.csv` stores controlled vocabulary for plant/animal/mineral parts and material/residue nouns (e.g., τέφρα, σποδός).
- `preparations.csv` stores controlled vocabulary for adjectival/process preparation terms that modify a base substance (e.g., κεκαυμένος, ἀφέψημα).
- `entry_lemmata` is **not** represented as its own CSV; instead, `entries.csv` temporarily includes a `lemma_ids` column for import convenience. Import scripts must split the comma-separated values into rows within the canonical junction table because Supabase relies on proper many-to-many relationships.

### Supabase Compatibility Notes
- Text columns remain `TEXT`; enumerations use `VARCHAR` + application-level validation to keep migrations simple.
- Numeric fields (`e_page_start`, `word_count`) cast cleanly to `INTEGER`/`NUMERIC`.
- All identifiers (entry_id, lemma_id, part_id) remain under 30 characters for index efficiency.

---

## 2. Sheet Definitions
### Entries Sheet
| Column | Type | Notes |
|--------|------|-------|
| entry_id | string | `SOURCE-ref` (e.g., `GAL_SMT-6.1.1`). Compatible with future CTS URN conversion. |
| source | enum | `GAL_SMT`, `GAL_ALIM`, `ORIB_CM`, `AET_LM`. |
| ref | string | Hierarchical reference `Book.Chapter[.Section]`. |
| chapter_title_gr | string | Original heading. |
| chapter_title_en | string | Translate literally ("περὶ Χ" → "On X"). |
| lemma_ids | string | **Import-only.** Comma-separated lemma IDs to be exploded into `entry_lemmata`. Leave blank if unknown. |
| part_id | string | Optional reference to `parts.csv`. |
| greek | text | Canonical Greek text. |
| greek_normalized | text | Accent/breathing-stripped version for search (no transliteration). |
| translation | text | Editable English translation. |
| trans_status | enum | `draft`, `review`, `final`. |
| e_vol | string | Edition volume (e.g., Kühn). |
| e_page_start / e_page_end | number | Inclusive page range. |
| word_count | number | Auto-calculated from Greek text. |
| notes | text | Editorial comments. |

### Lemmata Sheet
| Column | Type | Notes |
|--------|------|-------|
| lemma_id | string | `L001`, `L002`, … |
| headword_gr | string | Nominative form. |
| headword_normalized | string | Accent/breathing-stripped form for matching. |
| headword_en | string | Optional gloss (can stay blank). |
| parent_lemma | string | Parent `lemma_id` when applicable. |
| relationship | enum | `subtype`, `synonym`, or blank. |
| category | enum | `vegetable`, `animal`, `mineral`. |
| notes | text | Context remarks. |

### Parts Sheet
| Column | Type | Notes |
|--------|------|-------|
| part_id | string | `P###`. |
| greek | string | Polytonic term (ῥίζα, σπέρμα, κέρας, etc.). |
| english | string | Plain-language equivalent. |
| category | enum | `vegetable`, `animal`, `mineral`, or `all`. |
| notes | text | Free-form context notes. |

### Preparations Sheet
| Column | Type | Notes |
|--------|------|-------|
| prep_id | string | `PR###`. |
| greek | string | Polytonic preparation/state term (e.g., κεκαυμένος, ἀφέψημα). |
| english | string | Plain-language equivalent. |
| scope | enum | `vegetable`, `animal`, `mineral`, or `all`. Use the most permissive logically admissible scope. |
| notes | text | Free-form remarks. |

### Modern IDs Template
Provides headers (`modern_id,lemma_id,binomial,common_en,authority,source_citation,confidence,notes`). Leave empty rows for now; future ETL can populate it.

---

## 3. Ontological Guidance
```
Category (animal / vegetable / mineral)
  └─ Lemma (substance)
       └─ Subtype/Synonym (optional)
            └─ Part/Preparation (if specified)
```
- Multi-word headings such as "ἀγαρικοῦ ῥίζα" link lemma=ἄγαρικον plus part=ῥίζα.
- Names containing preparation/state terms (κεκαυμένος, ἀφέψημα, etc.) map to `preparations.csv` for tracking; residue/product nouns such as τέφρα and σποδός remain `parts.csv`.

---

## 4. Automation Tasks
All tasks assume Claude/Codex CLI tooling in a local workspace. Keep intermediate scripts under version control when possible.

### Task A – Generate `parts.csv`
1. Seed with vocabulary from this spec (see Appendix A) covering plant, animal, and mineral parts (parts only).
2. Scan original lemma column + chapter titles for additional part terms (ῥίζα, φύλλα, κέρας, etc.) and append missing entries with proper categories.
3. Include brief notes where ambiguity exists (e.g., σπέρμα = seed; used across plant entries).

### Task A2 – Generate `preparations.csv`
1. Seed with preparation/state vocabulary (see Appendix A2) with stable IDs (`PR###`).
2. Scan original lemma column + chapter titles for additional preparation/state terms conservatively; if unsure, log candidates in `preparations_review.csv` rather than adding.

### Task B – Generate `lemmata.csv`
1. Parse the master lemma list (Appendix B) where parentheses indicate subtype/synonym candidates.
2. Assign incremental IDs (`L001…`). Items inside parentheses inherit `parent_lemma` of the preceding base term; mark `relationship=subtype` unless domain experts later mark as synonym.
3. Auto-assign `category` heuristically (terms with λίθος, γῆ → mineral; αἷμα, χολή → animal; default → vegetable). Flag uncertain cases in `lemmata_review.csv`.
4. Leave `headword_en` blank unless exact gloss exists.

### Task C – Restructure `entries.csv`
1. Flatten all sheets from `Simples.xlsx` into a single table with consistent columns.
2. Generate `entry_id` by combining source code + ref (pad sections as needed to maintain uniqueness).
3. Populate `chapter_title_en` via literal translation patterns; for multi-lemma headings, include both terms ("On southernwood and wormwood").
4. Leave `lemma_ids` blank initially; populate during Task D.
5. Compute `word_count` from Greek text tokens (simple whitespace split suffices for validation; precise counts optional later).

### Task D – Link Entries to Lemmata
1. Consume the legacy Lemma column; split on semicolons.
2. Normalize each token (strip accents/breathings, lowercase) and match against `lemmata.headword_normalized`.
3. Populate `lemma_ids` with comma-separated IDs per entry. Log unmatched tokens into `unmatched_terms.csv` for manual review.
4. Detect part references by scanning chapter titles and lemma strings; set `part_id` accordingly.
5. Detect preparation/state references by scanning chapter titles and lemma strings; emit `entry_preparations.csv` (import-only) with `entry_id,prep_id,is_primary,notes`.
6. After import, scripts must expand `lemma_ids` into `entry_lemmata` rows:
   ```
   INSERT INTO entry_lemmata(entry_id, lemma_id, is_primary)
   SELECT entry_id, UNNEST(string_to_array(lemma_ids, ',')), first = TRUE
   FROM staging_entries;
   ```
   Application code never reads `lemma_ids` once data sits in Supabase.

### Task E – Diff & Verification
1. Compare row counts per source between each original sheet and `entries.csv`.
2. Compare aggregate Greek word counts; alert if deviation >5%.
3. Sample 20 rows randomly; verify lemma links and part assignments match expectations.
4. Run OpenRefine facets on category/status columns to find typos.

### Task F – Optional Test Subset
Process 30 representative entries (list provided in Appendix C) through the entire pipeline before running bulk scripts.

---

## 5. Greek Text Handling Rules
- Preserve original polytonic text exactly; normalization is computed separately.
- Do not auto-capitalize or alter breathing marks.
- When matching, convert to lowercase, remove accents/breathings, but **never** strip iota subscripts or convert to Latin.
- Save CSVs as UTF-8; verify by re-opening in VS Code.
- The same normalization function must drive CSV generation, Supabase triggers, and application search—do not re-implement diverging logic in multiple layers.

---

## 6. Validation Checklist
- [ ] Entry counts by source: GAL_SMT=640, ORIB_CM=437, AET_LM=622, GAL_ALIM=TBD (fill actual count).
- [ ] 100% of entries populated in `entries.csv`.
- [ ] ≥95% entries have at least one `lemma_id`; remainder itemized in `unmatched_terms.csv`.
- [ ] `parts.csv` covers every explicit part/preparation mention.
- [ ] `parts.csv` covers every explicit part mention.
- [ ] `preparations.csv` covers every explicit preparation/state mention.
- [ ] `lemmata_review.csv` adjudicated by domain experts.
- [ ] Diff-check and OpenRefine logs archived alongside CSV commit.

---

## 7. File Locations & Naming
```
/project-root
 ├── Simples.xlsx                 # legacy input
 ├── simples_data_restructure_spec.md
 ├── entries.csv                  # authoritative staging file
 ├── lemmata.csv
 ├── parts.csv
 ├── modern_ids.csv
 ├── lemmata_review.csv
 ├── unmatched_terms.csv
 ├── entries_test.csv (optional)
 └── lemmata_test.csv (optional)
```

Supabase imports pull directly from these CSVs; keep them synchronized with Git commits for traceability.

---

## Appendix A – Starter Parts Vocabulary
*(expand as data demands)*

**Vegetable**: ῥίζα/root (P001), φύλλον/leaf (P002), σπέρμα/seed (P003), καρπός/fruit (P004), ἄνθος/flower (P005), φλοιός/bark (P006), χυλός/juice (P007), ὀπός/resin (P008), κλάδος/branch (P009), βλαστός/shoot (P010), τέφρα/ash (P102).

**Animal**: αἷμα/blood (P201), γάλα/milk (P202), χολή/bile (P203), πιμελή-fat (P204), μυελός/marrow (P205), ἧπαρ/liver (P206), κόπρος/dung (P207), οὖρον/urine (P208), ὀστοῦν/bone (P209), κέρας/horn (P210), δέρμα/skin (P211), ὄνυξ/claw (P212), ὠόν/egg (P213).

**Mineral**: λίθος/stone (P301), ἄνθος (efflorescence) (P302), σποδός/powder/ash residue (P303).

## Appendix A2 – Starter Preparations Vocabulary
*(expand as data demands)*

- κεκαυμένος / burnt/calcined (PR001)
- ἀφέψημα / decoction (PR002)

Add more as needed; keep IDs stable once published.

---

## Appendix B – Master Lemma List (Excerpt)
The full list (Greek headwords plus parenthetical variants) remains identical to the previous specification. Editors should reference the source text to resolve ambiguous relationships. Use the same ordering when assigning lemma IDs to preserve continuity with earlier drafts.

---

## Appendix C – Recommended Test Entries
Before bulk processing, run Tasks A–D on at least the following entries:
- **Galen SMT:** 6.1.1, 6.1.2, 6.1.4, 6.1.7, 6.2.30, 6.3.3, 6.4.7, 7.10.1, 8.18.1, 9.1.1
- **Oribasius CM 15:** 1, 10, 50, 75, 100, 150, 200, 300, 350, 400
- **Aetius LM I–II:** 1.1, 1.25, 1.50, 1.75, 2.1, 2.50, 2.100, 2.150, 2.200, 2.250

Document any mismatches uncovered during this subset run before applying scripts to the full corpus.

---

*Specification v1.1 – Supersedes prior drafts; conforms to the Next.js + Supabase MVP plan.*

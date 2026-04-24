# entries.csv QC report

- Generated: `2026-01-20T21:51:55+00:00`
- Workbook: `simples.xlsx`
- Total rows: **2135**

## Rows by source sheet
- `SMT`: 639
- `Alim.Fac`: 35
- `Oribasius CM 15`: 837
- `Aetius I-II`: 624

## Skipped rows
- _(none)_

## Sample (10 rows)
- `AET_LM-1.65`: βλίτον ἐδώδιμόν ἐστι λάχανον ὑγρὸν καὶ ψυχρὸν τῇ κράσει ἐν τῇ δευτέρᾳ μάλιστα ἀποστάσει τεταγμένον.
- `AET_LM-1.209~1`: κοκκυμηλέας ὁ καρπός. Ὑπάγει τὴν γαστέρα πρόσφατος μὲν ὑπάρχων μᾶλλον, ξηρανθεὶς δὲ ἧττον· ἐστὶ δ...
- `GAL_SMT-6.9.12`: ἱππομάραθρον. ἅμα τῷ μαράθρῳ περὶ τούτου ῥηθήσεται.
- `ORIB_CM-15.1.12.23`: καὶ δὴ καὶ κρατεῖ τὸ μὲν ὑδατῶδες ἐν τούτοις, ὡς εἶναι τὴν κρᾶσιν αὐτῶν ὑγροτέραν τε καὶ ψυχροτέρ...
- `AET_LM-2.155`: κεφαλὰς μαινίδων ταριχηρὰς καίων τις ἐχρῆτο πρὸς τὰς ἐν ἕδρᾳ ῥαγάδας καὶ τὰ σηπόμενα τῶν ὀδόντων ...
- `AET_LM-2.52`: διφρυγές. Μικτῆς ἐστι ποιότητος, στυφούσης μετὰ δριμύτητος, διὸ καὶ τῶν κακοήθων ἑλκῶν ἀγαθόν ἐστ...
- `AET_LM-1.145`: ἐρέβινθος ὄσπριόν ἐστι φυσῶδες τρόφιμον εὐκοίλιον οὐρητικόν, γάλακτος καὶ σπέρματος καὶ καταμηνίω...
- `ORIB_CM-15.1.18.51`: Στάχυς, ὁ παραπλήσιος τῷ πρασίῳ θάμνος, δριμύς τέ ἐστι καὶ πικρός, τῆς τρίτης τάξεως ὑπάρχων τῶν ...
- `AET_LM-2.14`: λίθος σχιστὸς γαλακτίτης μελιτίτης. Τῷ δὲ αἱματίτῃ λίθῳ παραπλησίαν μέν, ἀσθενεστέραν δὲ δύναμιν ...
- `ORIB_CM-15.2.26`: τινὲς μὲν οὖν πάνυ συνεχῆ τὴν χρῆσιν ἔχουσι, τινὲς δὲ σπανιωτέραν.

## Ref-sequence audit notes (2026-04-06)

Full report: `entries_refs_audit.md`. Audit script: `scripts/audit_entries_refs.py`.

### Fixes applied

- **GAL_SMT 6.9**: Renumbered sections from `6.9.8..15` to `6.9.1..8` (corrected xlsx numbering error).
- **GAL_SMT 10.1**: Changed `10.1.0` to `10.1` (2-level ref; chapter 1 has no subsections, unlike chapter 2+).

### Confirmed structural patterns (not errors)

- **GAL_SMT books 6-8**: Share continuous chapter numbering (6: ch. 1-9, 7: ch. 10-12, 8: ch. 13-24). Intentional per source text.
- **GAL_SMT prooimia**: Books 6, 7, 8, 9, 11 have `prooimion` entries; book 10 does not.
- **AET_LM `~N` duplicates**: 6 refs have sibling entries sharing a chapter number (e.g. `1.241` x4). These reflect unnumbered sub-entries in the edition.
- **ORIB_CM depth inconsistency**: Chapter 1 uses 4-tuple refs (`15.1.C.N`), chapter 2 uses 3-tuple refs (`15.2.N`). Reflects source text structure.

### Deferred sources

- **GAL_ALIM** (35 entries, sparse coverage across books 1-3): Current CSV retained as-is. Full ingestion deferred to TEI-first pipeline.
- **PAUL_RM** (no entries in CSV): Deferred to TEI-first pipeline. DB status remains `pending`.

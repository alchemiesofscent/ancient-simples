---
status: active
owner: archive
---

# Archive Map

This directory stores historical material that is kept for traceability but removed from the active working surface.

## Archive Rules

- Superseded docs move here in the same change that replaces them.
- Scratch parsing experiments and one-off import files belong here, not in active top-level folders.
- Historical output families move here once they are no longer referenced by active scripts or process docs.
- Archived files may retain historical path strings inside their own contents; active docs and scripts must not point here by default unless explicitly discussing history.

## Current Contents

- `docs/legacy_pre_tei_first/`
  - older planning and MVP design rounds superseded by the TEI-first documentation set
- `docs/legacy_qc/`
  - one-time QC reports, audit docs, and CSV-first specs moved from `data-workbench/` (2026-04-06)
- `docs/analysis/`
  - vocab v3 extraction analysis and NER scoping notes moved from `docs/` (2026-04-06)
- `docs/duplicates/`
  - duplicate specs retained only for provenance
- `docs/scaffold/`
  - default scaffold docs that are not part of the project’s active documentation
- `docs/misc/`
  - miscellaneous historical notes not on the active path (includes `WORKTREE_STATE.md`)
- `import_experiments/`
  - scratch import/parsing experiments
- `outputs/`
  - historical output families no longer on the active operational path

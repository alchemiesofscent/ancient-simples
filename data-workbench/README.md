---
status: active
owner: workflow
---

# Data Workbench Map

This directory contains the canonical CSV-first working surface.

## Canonical Inputs

- `entries.csv`, `lemmata.csv`, `parts.csv`, `preparations.csv`
  - legacy corpus inputs (2,135 entries across GAL_SMT, AET_LM, ORIB_CM, GAL_ALIM)
- `entry_preparations.csv`, `modern_ids.csv`
  - supporting CSV inputs

## Dioscorides Operational Files

- `diosc.csv`, `diosc.patched.csv`, `diosc.build.csv`
  - Dioscorides source, patched, and build-ready states
- `diosc_build_audit.md`, `diosc_build_review.csv`
  - audit summary and review sheet for validating `diosc.build.csv` before extraction
- `entries_diosc.csv`
  - generated entries-shaped CSV (835 entries) for the Dioscorides vocab extraction workflow
- `diosc_alignment_review.csv`, `diosc_alignment_context.md`
  - alignment review artifacts
- `diosc_missing_text_patch.csv`, `diosc_text_fixes_patch.csv`
  - patch payloads used by build scripts

## Active QC

- `entries_qc.md` — entries quality check (updated 2026-04-06 with ref-sequence audit notes)
- `entries_refs_audit.md` — ref-sequence audit findings (2026-04-06)
- `entries_diosc_qc.md` — Dioscorides entries QC

## Archived QC

Legacy one-time reports and CSV-first specs moved to `archive/docs/legacy_qc/` (2026-04-06)

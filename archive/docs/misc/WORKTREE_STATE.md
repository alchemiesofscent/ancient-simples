---
status: active
owner: workflow
---

# Worktree State

This file is the fast resume snapshot for the current worktree.

Use it for:
- the current local state that may not be obvious from `git status`
- the task being worked right now
- any local caveats before resuming the main workflow

Canonical planning and handoff still live in:
- `docs/new_simples/new_wbs.md`
- `docs/new_simples/session_log.md`

## Current Snapshot

- Repo clarity refactor completed: active docs and current workflow files have been separated from archived planning rounds and scratch material.
- Current output family kept active: `outputs/vocab_entries_v3/`
- Historical output families moved under `archive/outputs/`
- Dioscorides build-audit workflow installed: `npm run diosc:build:audit` now writes `data-workbench/diosc_build_audit.md` and `data-workbench/diosc_build_review.csv`
- Current main implementation task after this cleanup remains `TEI-INDEX-01`

## Resume Next

- Read `docs/new_simples/new_wbs.md`
- Read the latest entry in `docs/new_simples/session_log.md`
- Continue `TEI-INDEX-01`: reconcile `scripts/index_tei.py` with `supabase/migrations/005_tei_first_schema.sql`

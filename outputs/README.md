---
status: active
owner: workflow
---

# Outputs: Extraction Data

This directory contains the LLM extraction results that power search, computation, and future NER training. This data is critical and must not be deleted.

## Data Flow

```
data-workbench/entries.csv (2,135 entries)
data-workbench/entries_diosc.csv (835 entries)
    ↓
scripts/vocab_multi_agent_pilot.py (orchestrator)
    ↓
vocab_entries_v3/{run_id}/results/*.json
    ↓
scripts/import_vocab_v3.py → DB (assertions, lemma_forms)
    ↓
App: faceted search, lemma browser
    ↓
NER training corpus (future)
```

## Contents

- `vocab_entries_v3/`
  - `entries_full_v3/` — complete legacy corpus extraction (2,135/2,135 entries, 27,707 terms, 2,894 qualities)
  - `diosc_smoke_v3/` — Dioscorides smoke run (partial, ~51 results)
  - `diosc_smoke_v3_net/` — Dioscorides network smoke (partial, ~20 results)
  - `accuracy_eval/` — model accuracy evaluation (gpt-5.2 + high selected)
  - `model_eval/` — additional model evaluations
  - `diosc_smoke_probe*/` — probe runs for parameter tuning
- `_codex_home/`
  - runner fallback state used by local tooling

## Historical

Superseded output families (v2, pilot, experiments) are in `archive/outputs/`.

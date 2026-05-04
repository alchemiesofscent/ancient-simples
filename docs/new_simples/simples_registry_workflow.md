---
status: active
owner: workflow
---

# Simples Registry Workflow

## Long-Term Goal

Build a complete, evidence-backed registry of simples discussed across the active Greek medical corpora, then use that registry to study simples across authors and, later, inside preparations.

The identity chain is:

```text
ancient term -> scholarly identification(s) -> physical substance -> botanical/material source
```

The first workflow stage stays at the ancient-term layer. It does not collapse terms into final physical substances, and it does not force botanical identifications. Those layers come after name relations and identification evidence are reviewed.

## Current Scope

The v0 registry uses the complete `vocab_entries_v3` result runs declared in `config/simples_registry_runs.json`:

- `entries_full_v3`
- `diosc_full_v3`
- `paul_full_v3`

The workflow must remain open to later Oribasius 1-14 and Aetius 3-4 result runs. Every generated row therefore carries both `text_source` and `result_run`.

## Artifact Surface

Generated files live under `data-workbench/simples/`:

- `simple_terms_v0.csv`: one row per provisional ancient term key.
- `simple_term_occurrences_v0.csv`: one row per substance-like term occurrence.
- `simple_term_forms_v0.csv`: attested display forms per term key.
- `simple_registry_manifest.json`: run metadata, counts, inputs, and command.
- `simple_name_relation_candidates.csv`: deterministic name-relation candidates for review.
- `simple_name_relation_review_packets.jsonl`: full-context review packets for LLM or human reviewers.
- `simple_name_relations_pilot.csv`: reviewed relation surface; initially pending LLM review.
- `simple_name_relations_pilot_report.md`: pilot counts and next-step status.
- `app/public/simples/registry-index.json`: compact browser index for the `/simples` Registry view.

These are working artifacts, not final canonical data. They are checked in because review state and reproducibility matter more than hiding generated CSVs at this stage.

## Workflow

1. Build the v0 term registry from declared complete runs only.
2. Generate a 20-entry-per-author name-relation pilot sample.
3. Use deterministic rules only to find candidate evidence and controls.
4. Have LLM or human reviewers confirm, reject, classify, and add missed name relations.
5. Use the pilot to decide which normalized terms can become aliases, which are variants, and which must remain separate.
6. Only after this pilot, build identification candidates and physical-substance links.

## Browser Views

The `/simples` route has two research-review views:

- `Registry`: the default named-simple list. It loads `app/public/simples/registry-index.json`, supports source/author/review filters, and labels every row as a draft ancient term rather than a final physical substance.
- `Evidence`: the heavier extraction explorer. It loads `app/public/vocab/vocab-index.json` only when opened and preserves the detailed quality/facet/evidence comparison workflow.

Rebuild the compact browser index after regenerating registry artifacts:

```bash
npm run simples:public-index
```

## Open Problem: Candidate Simples View

Goal: produce a cleaner default list for users while preserving the raw extraction/audit view for transparent review.

The current registry exposes raw `SUBSTANCE` and `SUBSTANCE_PART` extraction terms too directly. Problem examples include `ῥίζα`, `φύλλα`, `σπέρμα`, inflected variants, article phrases, and generic plant parts that can appear as if they were independent simples.

Before adding more UI polish, decide whether candidate-simple status is UI-only, generated into `app/public/simples/registry-index.json`, or written back into `data-workbench/simples/` CSV artifacts.

## Review Relation Types

- `synonym`
- `variant`
- `regional_name`
- `foreign_name`
- `place_qualified_variant`
- `part_or_product`
- `mistaken_identification`
- `related_but_not_synonymous`
- `uncertain`
- `unreviewed`

## Save And Commit Discipline

Each milestone should be committed as one logical unit. At minimum:

1. Workflow docs and manifest.
2. Registry generator and v0 outputs.
3. Name-relation candidate generator and pilot packets.
4. Reviewed LLM pilot outputs.
5. QC/report updates and next-step planning.

Every run must write a manifest or report with input paths, source counts, output paths, command, timestamp, and git commit hash when available. Each committed milestone must update `docs/new_simples/new_wbs.md`, append to `docs/new_simples/session_log.md`, and update `CHANGELOG.md` when structural files are added or moved.

## Preparation Scope

Preparations stay lightweight until the simples/name-relation layer is stable. The next stage may record simple-to-preparation evidence as relation rows, but it should not attempt a full recipe model yet.

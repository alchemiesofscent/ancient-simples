---
status: active
owner: data-workbench
---

# Simples Registry Workbench

This directory is the artifact-first work surface for the simples registry.

The goal is to preserve an auditable path from extracted `vocab_entries_v3` terms to provisional ancient-term nodes, then to reviewed name relations, and only later to scholarly identifications and physical substances.

## Generated Artifacts

- `simple_terms_v0.csv`: provisional ancient-term registry from `SUBSTANCE` and `SUBSTANCE_PART`.
- `simple_term_occurrences_v0.csv`: entry-level evidence for each term.
- `simple_term_forms_v0.csv`: display-form counts by term key.
- `simple_registry_manifest.json`: inputs, counts, command, and git hash.
- `simple_name_relation_candidates.csv`: deterministic candidate relations and controls.
- `simple_name_relation_review_packets.jsonl`: full passage packets for LLM/human review.
- `simple_name_relations_pilot.csv`: reviewer output surface, initially pending review.
- `simple_name_relations_pilot_report.md`: candidate/sample summary.
- `app/public/simples/registry-index.json`: compact browser index for the `/simples` Registry view.

## Commands

```bash
npm run simples:registry
npm run simples:name-candidates
npm run simples:public-index
```

Both commands read `config/simples_registry_runs.json`. Add future Oribasius 1-14 and Aetius 3-4 result runs to that manifest rather than changing the CSV schema.

`simples:public-index` also reads the current evidence index at `app/public/vocab/vocab-index.json` so the Registry view can show compact quality badges without loading the full evidence payload first.

## Data Model Boundary

This directory works at the ancient-term layer:

```text
ancient term -> scholarly identification(s) -> physical substance -> botanical/material source
```

Only the first layer is generated here. Later identification and physical-substance layers must be evidence-backed and reviewable.

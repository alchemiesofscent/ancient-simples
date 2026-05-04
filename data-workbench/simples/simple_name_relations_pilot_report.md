# Simple Name Relations Pilot Report

- Generated: `2026-05-04T16:28:29.312852+00:00`
- Git commit: `eca4a6d4316256b51685e192e7683decefc636bd`
- Sample target: `20` entries per author group
- Candidate rows: `681`
- Review status: `pending_llm_review`

## Outputs

- `data-workbench/simples/simple_name_relation_candidates.csv`
- `data-workbench/simples/simple_name_relation_review_packets.jsonl`
- `data-workbench/simples/simple_name_relations_pilot.csv`

## Candidate Rows By Author

- Aetius: 168
- Dioscorides: 190
- Galen: 196
- Oribasius: 40
- Paul: 87

## Candidate Methods

- body_kaleitai: 48
- body_legetai: 1
- body_some_call: 37
- control_no_trigger: 20
- heading_eta: 418
- heading_hoi_de: 145
- heading_semicolon: 12

## Sample Counts

- sample_Aetius: 20
- sample_Dioscorides: 20
- sample_Galen: 20
- sample_Oribasius: 20
- sample_Paul: 20
- sample_type_control: 20
- sample_type_trigger: 80

## Next Step

Send `simple_name_relation_review_packets.jsonl` plus `simple_name_relation_candidates.csv` to LLM or human reviewers. Reviewers should confirm/reject candidates, classify relation types, and add missed relations visible in each passage.

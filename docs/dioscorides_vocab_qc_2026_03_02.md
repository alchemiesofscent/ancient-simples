# Dioscorides Vocab QC Notes (2026-03-02)

## Objective
Validate Dioscorides extraction in CSV-first mode while keeping schema compatibility with v3 and avoiding false Galenic quantification assumptions.

## Expectations
- `qualities[]` array is still present and schema-valid.
- Degree-bearing qualities may be sparse.
- QC focuses on completeness, parse validity, normalization, and over-quantification risk.

## Run log
- Entries build: completed
  - Command: `python scripts/make_entries_diosc.py`
  - Output: `data-workbench/entries_diosc.csv` (829 rows)
  - QC: `data-workbench/entries_diosc_qc.md`
- Entries validation: completed
  - Command: `python scripts/validate_diosc_entries.py`
  - Result: pass; 2 warnings (blank translations on `DIOSC_DMM-3.73_RV`, `DIOSC_DMM-4.58_RV`)
- Smoke extraction: attempted, blocked by model endpoint connectivity
  - Command: `npm run diosc:vocab:smoke`
  - Run dir: `outputs/vocab_entries_v3/diosc_smoke_v3`
  - Manifest: `outputs/vocab_entries_v3/diosc_smoke_v3/manifest_20260302_184125_utc.json`
  - Outcome: 0 succeeded, 25 failed
  - Error pattern: `codex exec failed` due `failed to refresh available models` / `stream disconnected before completion` when requesting `https://chatgpt.com/backend-api/codex/models`
- Connectivity probes on 2026-03-03 UTC:
  - Probe 1 (sandboxed): `outputs/vocab_entries_v3/diosc_smoke_probe_20260302`
    - Command: one-entry `vocab_multi_agent_pilot.py` run with same model/prompt stack
    - Outcome: 0/1 succeeded
    - Error pattern: same model-refresh stream disconnect on `codex/models`
  - Probe 2 (escalated network): `outputs/vocab_entries_v3/diosc_smoke_probe_20260302_escalated`
    - Command: same one-entry probe with unrestricted network
    - Outcome: 0/1 succeeded
    - Error pattern: `subprocess.TimeoutExpired` after 180s waiting on `codex exec`
  - Probe QC outputs:
    - `outputs/vocab_entries_v3/diosc_smoke_probe_20260302/qc_summary.md`
    - `outputs/vocab_entries_v3/diosc_smoke_probe_20260302_escalated/qc_summary.md`
- Connectivity probe with longer timeout on 2026-03-03 UTC:
  - Probe 3: `outputs/vocab_entries_v3/diosc_smoke_probe_900_escalated`
  - Command profile: same one-entry probe, timeout=900s
  - Outcome: 1/1 succeeded (completeness true)
  - QC: `outputs/vocab_entries_v3/diosc_smoke_probe_900_escalated/qc_summary.md`
- Smoke QC: completed (incomplete run allowed)
  - Command: `python scripts/qc_diosc_vocab_run.py --run-dir outputs/vocab_entries_v3/diosc_smoke_v3 --allow-incomplete`
  - Output: `outputs/vocab_entries_v3/diosc_smoke_v3/qc_summary.md`, `outputs/vocab_entries_v3/diosc_smoke_v3/qc_summary.json`
  - Current completeness snapshot: false (2/25 valid results; 23 missing)
- Full extraction: not run yet (depends on smoke pass and model connectivity)
- Full QC: not run yet

## Notes
- Runbook + scripts are in place and validated locally.
- Current blocker is runtime model access/latency, not CSV/schema/prompt wiring.
- Next execution step is re-running smoke once Codex model endpoint connectivity is restored and one-entry probe passes; then proceed to full resumable run.

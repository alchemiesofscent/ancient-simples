
# Vocab Model Eval Log

[2026-03-02T02:44:49Z] START

Decisions:
- Use ids_file=outputs/vocab_entries_v3/model_eval/ids_sample_small.txt
- Use baseline_results_dir=/home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/entries_full_v3/results
- Use schema=/home/seancoughlin/Projects/ancient-simples/schemas/vocab_term_extractor_with_degrees.schema.json
- Per-entry timeouts: high=600s, xhigh=900s
- Run sequential per entry (parallel=1) for easier logging

[2026-03-02T02:44:49Z] PREPARE_JOBS run_id=_prep_20260302_024449_utc

[2026-03-02T02:44:49Z] RUN: /home/seancoughlin/Projects/ancient-simples/.venv/bin/python /home/seancoughlin/Projects/ancient-simples/scripts/vocab_multi_agent_pilot.py --ids-file outputs/vocab_entries_v3/model_eval/ids_sample_small.txt --outdir /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval --run-id _prep_20260302_024449_utc --session-id _prep_20260302_024449_utc --prepare-only
STDOUT:
Wrote 6 jobs for review: /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/_prep_20260302_024449_utc/manifest__prep_20260302_024449_utc.json
[2026-03-02T02:44:49Z] EXIT: 0

[2026-03-02T02:44:49Z] MODEL_RUN_START gpt_5_2_high_20260302_024449_utc
- model: gpt-5.2
- model_reasoning_effort: high
- timeout_s: 600
- resume: True
[2026-03-02T02:44:49Z] START gpt_5_2_high_20260302_024449_utc GAL_SMT-10.1.0
[2026-03-02T02:53:58Z] OK gpt_5_2_high_20260302_024449_utc GAL_SMT-10.1.0 (548.2s)
[2026-03-02T02:53:58Z] START gpt_5_2_high_20260302_024449_utc GAL_SMT-10.2.10

[2026-03-02T02:54:30Z] DECISION
- Aborted first eval run mid-way because `GAL_SMT-10.1.0` took ~548s at `gpt-5.2` + `model_reasoning_effort="high"`.
- New decision: use a smaller, faster 6-entry sample with coverage (qualities + substance_part) to make 3-model comparison feasible.
- New ids file: `outputs/vocab_entries_v3/model_eval/ids_sample_fast.txt`.

# Vocab Model Eval Log

[2026-03-02T02:57:00Z] START

Decisions:
- Use ids_file=outputs/vocab_entries_v3/model_eval/ids_sample_fast.txt
- Use baseline_results_dir=/home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/entries_full_v3/results
- Use schema=/home/seancoughlin/Projects/ancient-simples/schemas/vocab_term_extractor_with_degrees.schema.json
- Per-entry timeouts: high=300s, xhigh=450s
- Run sequential per entry (parallel=1) for easier logging

[2026-03-02T02:57:00Z] PREPARE_JOBS run_id=_prep_20260302_025700_utc

[2026-03-02T02:57:00Z] RUN: /home/seancoughlin/Projects/ancient-simples/.venv/bin/python /home/seancoughlin/Projects/ancient-simples/scripts/vocab_multi_agent_pilot.py --ids-file outputs/vocab_entries_v3/model_eval/ids_sample_fast.txt --outdir /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval --run-id _prep_20260302_025700_utc --session-id _prep_20260302_025700_utc --prepare-only
STDOUT:
Wrote 6 jobs for review: /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/_prep_20260302_025700_utc/manifest__prep_20260302_025700_utc.json
[2026-03-02T02:57:00Z] EXIT: 0

[2026-03-02T02:57:00Z] MODEL_RUN_START gpt_5_2_high_20260302_025700_utc
- model: gpt-5.2
- model_reasoning_effort: high
- timeout_s: 300
- resume: False
[2026-03-02T02:57:00Z] START gpt_5_2_high_20260302_025700_utc GAL_SMT-7.10.44
[2026-03-02T02:58:02Z] OK gpt_5_2_high_20260302_025700_utc GAL_SMT-7.10.44 (61.8s)
[2026-03-02T02:58:02Z] START gpt_5_2_high_20260302_025700_utc GAL_SMT-8.18.34
[2026-03-02T02:58:28Z] OK gpt_5_2_high_20260302_025700_utc GAL_SMT-8.18.34 (25.5s)
[2026-03-02T02:58:28Z] START gpt_5_2_high_20260302_025700_utc GAL_ALIM-1.26
[2026-03-02T03:00:17Z] OK gpt_5_2_high_20260302_025700_utc GAL_ALIM-1.26 (109.3s)
[2026-03-02T03:00:17Z] START gpt_5_2_high_20260302_025700_utc GAL_ALIM-1.32
[2026-03-02T03:02:22Z] OK gpt_5_2_high_20260302_025700_utc GAL_ALIM-1.32 (124.9s)
[2026-03-02T03:02:22Z] START gpt_5_2_high_20260302_025700_utc ORIB_CM-15.1.10.28
[2026-03-02T03:02:42Z] OK gpt_5_2_high_20260302_025700_utc ORIB_CM-15.1.10.28 (20.3s)
[2026-03-02T03:02:42Z] START gpt_5_2_high_20260302_025700_utc ORIB_CM-15.1.11.5
[2026-03-02T03:03:26Z] OK gpt_5_2_high_20260302_025700_utc ORIB_CM-15.1.11.5 (44.1s)
[2026-03-02T03:03:26Z] MODEL_RUN_END gpt_5_2_high_20260302_025700_utc ok=6 failed=0 elapsed_s=386.0

[2026-03-02T03:03:26Z] RUN: /home/seancoughlin/Projects/ancient-simples/.venv/bin/python /home/seancoughlin/Projects/ancient-simples/scripts/compare_extraction_runs.py --run-a /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/entries_full_v3/results --run-b /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/gpt_5_2_high_20260302_025700_utc/results --ids-file outputs/vocab_entries_v3/model_eval/ids_sample_fast.txt --out-report /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/reports/gpt_5_2_high_20260302_025700_utc_vs_baseline.md --out-diffs-dir /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/diffs/gpt_5_2_high_20260302_025700_utc --label-a baseline --label-b gpt_5_2_high_20260302_025700_utc
STDOUT:
Wrote report: /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/reports/gpt_5_2_high_20260302_025700_utc_vs_baseline.md
Wrote diffs:  /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/diffs/gpt_5_2_high_20260302_025700_utc
[2026-03-02T03:03:26Z] EXIT: 0

[2026-03-02T03:03:26Z] MODEL_RUN_START gpt_5_2_xhigh_20260302_025700_utc
- model: gpt-5.2
- model_reasoning_effort: xhigh
- timeout_s: 450
- resume: False
[2026-03-02T03:03:26Z] START gpt_5_2_xhigh_20260302_025700_utc GAL_SMT-7.10.44
[2026-03-02T03:06:15Z] OK gpt_5_2_xhigh_20260302_025700_utc GAL_SMT-7.10.44 (169.1s)
[2026-03-02T03:06:15Z] START gpt_5_2_xhigh_20260302_025700_utc GAL_SMT-8.18.34
[2026-03-02T03:08:30Z] OK gpt_5_2_xhigh_20260302_025700_utc GAL_SMT-8.18.34 (134.7s)
[2026-03-02T03:08:30Z] START gpt_5_2_xhigh_20260302_025700_utc GAL_ALIM-1.26
[2026-03-02T03:14:04Z] OK gpt_5_2_xhigh_20260302_025700_utc GAL_ALIM-1.26 (333.4s)
[2026-03-02T03:14:04Z] START gpt_5_2_xhigh_20260302_025700_utc GAL_ALIM-1.32
[2026-03-02T03:18:50Z] OK gpt_5_2_xhigh_20260302_025700_utc GAL_ALIM-1.32 (286.7s)
[2026-03-02T03:18:50Z] START gpt_5_2_xhigh_20260302_025700_utc ORIB_CM-15.1.10.28
[2026-03-02T03:20:22Z] OK gpt_5_2_xhigh_20260302_025700_utc ORIB_CM-15.1.10.28 (92.1s)
[2026-03-02T03:20:22Z] START gpt_5_2_xhigh_20260302_025700_utc ORIB_CM-15.1.11.5
[2026-03-02T03:22:04Z] OK gpt_5_2_xhigh_20260302_025700_utc ORIB_CM-15.1.11.5 (101.2s)
[2026-03-02T03:22:04Z] MODEL_RUN_END gpt_5_2_xhigh_20260302_025700_utc ok=6 failed=0 elapsed_s=1117.2

[2026-03-02T03:22:04Z] RUN: /home/seancoughlin/Projects/ancient-simples/.venv/bin/python /home/seancoughlin/Projects/ancient-simples/scripts/compare_extraction_runs.py --run-a /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/entries_full_v3/results --run-b /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/gpt_5_2_xhigh_20260302_025700_utc/results --ids-file outputs/vocab_entries_v3/model_eval/ids_sample_fast.txt --out-report /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/reports/gpt_5_2_xhigh_20260302_025700_utc_vs_baseline.md --out-diffs-dir /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/diffs/gpt_5_2_xhigh_20260302_025700_utc --label-a baseline --label-b gpt_5_2_xhigh_20260302_025700_utc
STDOUT:
Wrote report: /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/reports/gpt_5_2_xhigh_20260302_025700_utc_vs_baseline.md
Wrote diffs:  /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/diffs/gpt_5_2_xhigh_20260302_025700_utc
[2026-03-02T03:22:04Z] EXIT: 0

[2026-03-02T03:22:04Z] MODEL_RUN_START codex_5_3_high_20260302_025700_utc
- model: gpt-5.3-codex
- model_reasoning_effort: high
- timeout_s: 300
- resume: False
[2026-03-02T03:22:04Z] START codex_5_3_high_20260302_025700_utc GAL_SMT-7.10.44
[2026-03-02T03:22:30Z] OK codex_5_3_high_20260302_025700_utc GAL_SMT-7.10.44 (26.6s)
[2026-03-02T03:22:30Z] START codex_5_3_high_20260302_025700_utc GAL_SMT-8.18.34
[2026-03-02T03:22:57Z] OK codex_5_3_high_20260302_025700_utc GAL_SMT-8.18.34 (26.4s)
[2026-03-02T03:22:57Z] START codex_5_3_high_20260302_025700_utc GAL_ALIM-1.26
[2026-03-02T03:24:44Z] OK codex_5_3_high_20260302_025700_utc GAL_ALIM-1.26 (107.5s)
[2026-03-02T03:24:44Z] START codex_5_3_high_20260302_025700_utc GAL_ALIM-1.32
[2026-03-02T03:26:39Z] OK codex_5_3_high_20260302_025700_utc GAL_ALIM-1.32 (114.7s)
[2026-03-02T03:26:39Z] START codex_5_3_high_20260302_025700_utc ORIB_CM-15.1.10.28
[2026-03-02T03:27:02Z] OK codex_5_3_high_20260302_025700_utc ORIB_CM-15.1.10.28 (23.2s)
[2026-03-02T03:27:02Z] START codex_5_3_high_20260302_025700_utc ORIB_CM-15.1.11.5
[2026-03-02T03:27:35Z] OK codex_5_3_high_20260302_025700_utc ORIB_CM-15.1.11.5 (32.5s)
[2026-03-02T03:27:35Z] MODEL_RUN_END codex_5_3_high_20260302_025700_utc ok=6 failed=0 elapsed_s=330.9

[2026-03-02T03:27:35Z] RUN: /home/seancoughlin/Projects/ancient-simples/.venv/bin/python /home/seancoughlin/Projects/ancient-simples/scripts/compare_extraction_runs.py --run-a /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/entries_full_v3/results --run-b /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/codex_5_3_high_20260302_025700_utc/results --ids-file outputs/vocab_entries_v3/model_eval/ids_sample_fast.txt --out-report /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/reports/codex_5_3_high_20260302_025700_utc_vs_baseline.md --out-diffs-dir /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/diffs/codex_5_3_high_20260302_025700_utc --label-a baseline --label-b codex_5_3_high_20260302_025700_utc
STDOUT:
Wrote report: /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/reports/codex_5_3_high_20260302_025700_utc_vs_baseline.md
Wrote diffs:  /home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/diffs/codex_5_3_high_20260302_025700_utc
[2026-03-02T03:27:35Z] EXIT: 0

[2026-03-02T03:27:35Z] WROTE summary=/home/seancoughlin/Projects/ancient-simples/outputs/vocab_entries_v3/model_eval/summary_20260302_032735_utc.json
[2026-03-02T03:27:35Z] END

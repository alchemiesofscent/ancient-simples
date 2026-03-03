# Vocab Extraction Accuracy Eval Log

- Started: 2026-03-02 (UTC)
- Goal: choose best model/config by measured correctness (precision/recall/labeling/linking/qualities), not speed.

## Candidate configs
- A: model=`gpt-5.2`, `model_reasoning_effort="high"`
- B: model=`gpt-5.2`, `model_reasoning_effort="xhigh"`
- C: model=`gpt-5.3-codex`, `model_reasoning_effort="high"`

## Key decisions
- Use a fixed eval set and blinded review packets.
- Review uses rubric in `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`.
- Up to 10 subagents act as independent reviewers; each scores a subset of packets.
Wrote 30 ids to outputs/vocab_entries_v3/accuracy_eval/eval_ids_30.txt

[2026-03-02T03:10:00Z] DECISION
- Eval set frozen at 30 entries (10 each: GAL_SMT, ORIB_CM, GAL_ALIM).
- Selection strategy: feature-first (qualities/substance_part/place_variant/linked_action) using existing baseline outputs, then fill by word-count diversity.
- Frozen ids: `outputs/vocab_entries_v3/accuracy_eval/eval_ids_30.txt`.

[2026-03-02T03:12:00Z] RUN
- Started multi-model extraction runs (30 entries each):
  - `outputs/vocab_entries_v3/accuracy_eval/models/gpt_5_2_high` (gpt-5.2, effort=high, timeout=900s)
  - `outputs/vocab_entries_v3/accuracy_eval/models/gpt_5_2_xhigh` (gpt-5.2, effort=xhigh, timeout=1200s)
  - `outputs/vocab_entries_v3/accuracy_eval/models/codex_5_3_high` (gpt-5.3-codex, effort=high, timeout=900s)
Wrote 30 jobs for review: outputs/vocab_entries_v3/accuracy_eval/prep/manifest_prep.json
[2026-03-02T03:09:22Z] PROGRESS gpt_5_2_high=4/30 gpt_5_2_xhigh=2/30 codex_5_3_high=6/30
[2026-03-02T03:10:22Z] PROGRESS gpt_5_2_high=5/30 gpt_5_2_xhigh=2/30 codex_5_3_high=7/30
[2026-03-02T03:11:22Z] PROGRESS gpt_5_2_high=6/30 gpt_5_2_xhigh=2/30 codex_5_3_high=8/30
[2026-03-02T03:12:22Z] PROGRESS gpt_5_2_high=7/30 gpt_5_2_xhigh=3/30 codex_5_3_high=10/30
[2026-03-02T03:13:22Z] PROGRESS gpt_5_2_high=8/30 gpt_5_2_xhigh=3/30 codex_5_3_high=10/30
[2026-03-02T03:14:22Z] PROGRESS gpt_5_2_high=9/30 gpt_5_2_xhigh=3/30 codex_5_3_high=10/30
[2026-03-02T03:15:22Z] PROGRESS gpt_5_2_high=10/30 gpt_5_2_xhigh=3/30 codex_5_3_high=11/30
[2026-03-02T03:16:22Z] PROGRESS gpt_5_2_high=10/30 gpt_5_2_xhigh=3/30 codex_5_3_high=12/30
[2026-03-02T03:17:22Z] PROGRESS gpt_5_2_high=10/30 gpt_5_2_xhigh=4/30 codex_5_3_high=12/30
[2026-03-02T03:18:22Z] PROGRESS gpt_5_2_high=10/30 gpt_5_2_xhigh=4/30 codex_5_3_high=13/30
[2026-03-02T03:19:22Z] PROGRESS gpt_5_2_high=10/30 gpt_5_2_xhigh=5/30 codex_5_3_high=14/30
[2026-03-02T03:20:22Z] PROGRESS gpt_5_2_high=11/30 gpt_5_2_xhigh=5/30 codex_5_3_high=14/30
[2026-03-02T03:21:22Z] PROGRESS gpt_5_2_high=11/30 gpt_5_2_xhigh=6/30 codex_5_3_high=14/30
[2026-03-02T03:22:22Z] PROGRESS gpt_5_2_high=12/30 gpt_5_2_xhigh=6/30 codex_5_3_high=15/30
[2026-03-02T03:23:22Z] PROGRESS gpt_5_2_high=12/30 gpt_5_2_xhigh=6/30 codex_5_3_high=15/30
[2026-03-02T03:24:22Z] PROGRESS gpt_5_2_high=12/30 gpt_5_2_xhigh=7/30 codex_5_3_high=15/30
[2026-03-02T03:25:22Z] PROGRESS gpt_5_2_high=12/30 gpt_5_2_xhigh=7/30 codex_5_3_high=15/30
[2026-03-02T03:26:22Z] PROGRESS gpt_5_2_high=13/30 gpt_5_2_xhigh=8/30 codex_5_3_high=15/30
[2026-03-02T03:27:22Z] PROGRESS gpt_5_2_high=13/30 gpt_5_2_xhigh=8/30 codex_5_3_high=16/30
[2026-03-02T03:28:22Z] PROGRESS gpt_5_2_high=14/30 gpt_5_2_xhigh=8/30 codex_5_3_high=16/30
[2026-03-02T03:29:22Z] PROGRESS gpt_5_2_high=14/30 gpt_5_2_xhigh=9/30 codex_5_3_high=17/30
[2026-03-02T03:30:22Z] PROGRESS gpt_5_2_high=14/30 gpt_5_2_xhigh=9/30 codex_5_3_high=18/30
[2026-03-02T03:31:22Z] PROGRESS gpt_5_2_high=14/30 gpt_5_2_xhigh=10/30 codex_5_3_high=18/30
[2026-03-02T03:32:22Z] PROGRESS gpt_5_2_high=14/30 gpt_5_2_xhigh=10/30 codex_5_3_high=18/30
[2026-03-02T03:33:22Z] PROGRESS gpt_5_2_high=14/30 gpt_5_2_xhigh=10/30 codex_5_3_high=19/30
[2026-03-02T03:34:22Z] PROGRESS gpt_5_2_high=15/30 gpt_5_2_xhigh=10/30 codex_5_3_high=19/30
[2026-03-02T03:35:23Z] PROGRESS gpt_5_2_high=15/30 gpt_5_2_xhigh=10/30 codex_5_3_high=19/30
[2026-03-02T03:36:23Z] PROGRESS gpt_5_2_high=15/30 gpt_5_2_xhigh=10/30 codex_5_3_high=20/30
[2026-03-02T03:37:23Z] PROGRESS gpt_5_2_high=15/30 gpt_5_2_xhigh=10/30 codex_5_3_high=22/30
[2026-03-02T03:38:23Z] PROGRESS gpt_5_2_high=15/30 gpt_5_2_xhigh=10/30 codex_5_3_high=24/30
[2026-03-02T03:39:23Z] PROGRESS gpt_5_2_high=15/30 gpt_5_2_xhigh=10/30 codex_5_3_high=26/30
[2026-03-02T03:40:23Z] PROGRESS gpt_5_2_high=16/30 gpt_5_2_xhigh=10/30 codex_5_3_high=27/30
[2026-03-02T03:41:23Z] PROGRESS gpt_5_2_high=16/30 gpt_5_2_xhigh=10/30 codex_5_3_high=29/30
[2026-03-02T03:42:23Z] PROGRESS gpt_5_2_high=17/30 gpt_5_2_xhigh=11/30 codex_5_3_high=30/30
[2026-03-02T03:43:23Z] PROGRESS gpt_5_2_high=17/30 gpt_5_2_xhigh=11/30 codex_5_3_high=30/30
[2026-03-02T03:44:23Z] PROGRESS gpt_5_2_high=17/30 gpt_5_2_xhigh=11/30 codex_5_3_high=30/30
[2026-03-02T03:45:23Z] PROGRESS gpt_5_2_high=18/30 gpt_5_2_xhigh=11/30 codex_5_3_high=30/30
[2026-03-02T03:46:23Z] PROGRESS gpt_5_2_high=18/30 gpt_5_2_xhigh=11/30 codex_5_3_high=30/30
[2026-03-02T03:47:23Z] PROGRESS gpt_5_2_high=18/30 gpt_5_2_xhigh=11/30 codex_5_3_high=30/30
[2026-03-02T03:48:23Z] PROGRESS gpt_5_2_high=18/30 gpt_5_2_xhigh=12/30 codex_5_3_high=30/30
[2026-03-02T03:49:23Z] PROGRESS gpt_5_2_high=19/30 gpt_5_2_xhigh=12/30 codex_5_3_high=30/30
[2026-03-02T03:50:23Z] PROGRESS gpt_5_2_high=19/30 gpt_5_2_xhigh=12/30 codex_5_3_high=30/30
[2026-03-02T03:51:23Z] PROGRESS gpt_5_2_high=19/30 gpt_5_2_xhigh=12/30 codex_5_3_high=30/30
[2026-03-02T03:52:23Z] PROGRESS gpt_5_2_high=19/30 gpt_5_2_xhigh=12/30 codex_5_3_high=30/30
[2026-03-02T03:53:23Z] PROGRESS gpt_5_2_high=20/30 gpt_5_2_xhigh=12/30 codex_5_3_high=30/30
[2026-03-02T03:54:23Z] PROGRESS gpt_5_2_high=22/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T03:55:23Z] PROGRESS gpt_5_2_high=23/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T03:56:23Z] PROGRESS gpt_5_2_high=25/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T03:57:23Z] PROGRESS gpt_5_2_high=26/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T03:58:23Z] PROGRESS gpt_5_2_high=27/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T03:59:23Z] PROGRESS gpt_5_2_high=28/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T04:00:23Z] PROGRESS gpt_5_2_high=29/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T04:01:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=13/30 codex_5_3_high=30/30
[2026-03-02T04:02:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:03:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:04:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:05:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:06:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:07:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:08:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:09:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:10:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:11:23Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:12:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:13:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:14:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:15:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:16:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=14/30 codex_5_3_high=30/30
[2026-03-02T04:17:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:18:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:19:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:20:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:21:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:22:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:23:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:24:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:25:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:26:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:27:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:28:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:29:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:30:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:31:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:32:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:33:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:34:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:35:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:36:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:37:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:38:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:39:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:40:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:41:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:42:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:43:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:44:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:45:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:46:24Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:47:25Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30
[2026-03-02T04:48:25Z] PROGRESS gpt_5_2_high=30/30 gpt_5_2_xhigh=15/30 codex_5_3_high=30/30

[2026-03-02T04:49:00Z] DECISION
- Stopped `gpt_5_2_xhigh` full-30 run at 15/30 due to extreme wall-clock time (included long idle/wait periods).
- New plan: run `gpt_5_2_xhigh` on a focused 10-entry subset for accuracy comparison, keeping 3-way comparison feasible.

[2026-03-02T04:50:00Z] RUN
- Started xhigh subset run: `outputs/vocab_entries_v3/accuracy_eval/models/gpt_5_2_xhigh_subset10` (10 entries)
- Frozen ids: `outputs/vocab_entries_v3/accuracy_eval/eval_ids_xhigh_10.txt`
[2026-03-02T04:49:15Z] PROGRESS xhigh_subset10=0/10
[2026-03-02T04:50:15Z] PROGRESS xhigh_subset10=0/10
[2026-03-02T04:51:15Z] PROGRESS xhigh_subset10=1/10
[2026-03-02T04:52:15Z] PROGRESS xhigh_subset10=1/10
[2026-03-02T04:53:15Z] PROGRESS xhigh_subset10=2/10
[2026-03-02T04:54:15Z] PROGRESS xhigh_subset10=2/10
[2026-03-02T04:55:15Z] PROGRESS xhigh_subset10=3/10
[2026-03-02T04:56:15Z] PROGRESS xhigh_subset10=3/10
[2026-03-02T04:57:15Z] PROGRESS xhigh_subset10=4/10
[2026-03-02T04:58:15Z] PROGRESS xhigh_subset10=4/10
[2026-03-02T04:59:15Z] PROGRESS xhigh_subset10=4/10
[2026-03-02T05:00:15Z] PROGRESS xhigh_subset10=4/10
[2026-03-02T05:01:15Z] PROGRESS xhigh_subset10=4/10
[2026-03-02T05:02:15Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:03:15Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:04:15Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:05:15Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:06:15Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:07:15Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:08:16Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:09:16Z] PROGRESS xhigh_subset10=5/10
[2026-03-02T05:10:16Z] PROGRESS xhigh_subset10=6/10
[2026-03-02T05:11:16Z] PROGRESS xhigh_subset10=7/10
[2026-03-02T05:12:16Z] PROGRESS xhigh_subset10=7/10
[2026-03-02T05:13:16Z] PROGRESS xhigh_subset10=8/10
[2026-03-02T05:14:16Z] PROGRESS xhigh_subset10=9/10
[2026-03-02T05:15:16Z] PROGRESS xhigh_subset10=9/10
[2026-03-02T05:16:16Z] PROGRESS xhigh_subset10=10/10
Wrote packets: outputs/vocab_entries_v3/accuracy_eval/subset10/packets
Wrote blinding key: outputs/vocab_entries_v3/accuracy_eval/subset10/blinding_key.json
Wrote assignments: outputs/vocab_entries_v3/accuracy_eval/subset10/assignments
Wrote assignments: outputs/vocab_entries_v3/accuracy_eval/subset10/assignments_6

[2026-03-02T05:25:00Z] DECISION
- Tried to spawn 10 reviewer subagents; environment limit is 6 concurrent agents.
- Adjusted reviewer pool to 6 and regenerated assignments in `outputs/vocab_entries_v3/accuracy_eval/subset10/assignments_6/`.
Wrote outputs/vocab_entries_v3/accuracy_eval/subset10/summary.json
Wrote outputs/vocab_entries_v3/accuracy_eval/subset10/summary.md

[2026-03-02T05:40:00Z] RESULT
- Aggregated blinded reviews: `outputs/vocab_entries_v3/accuracy_eval/subset10/summary.md`
- Decision memo: `outputs/vocab_entries_v3/accuracy_eval/subset10/decision.md`
- Recommendation: default to `gpt-5.2` + `model_reasoning_effort="high"`.

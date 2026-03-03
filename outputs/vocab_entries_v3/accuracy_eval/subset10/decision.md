# Decision: Vocab Extraction Model Config (Subset10 Accuracy Eval)

Date: 2026-03-02 (UTC)

## Test design
- 10-entry subset: `outputs/vocab_entries_v3/accuracy_eval/eval_ids_xhigh_10.txt`
- Models compared (blinded per packet):
  - `gpt_5_2_high`: model=`gpt-5.2`, `model_reasoning_effort="high"`
  - `gpt_5_2_xhigh`: model=`gpt-5.2`, `model_reasoning_effort="xhigh"` (subset-only run)
  - `codex_5_3_high`: model=`gpt-5.3-codex`, `model_reasoning_effort="high"`
- Review method:
  - Packets: `outputs/vocab_entries_v3/accuracy_eval/subset10/packets/`
  - Rubric: `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`
  - 20 total reviews (2 per packet) aggregated into `outputs/vocab_entries_v3/accuracy_eval/subset10/summary.md`.

## Results (averages 0–5)
From `outputs/vocab_entries_v3/accuracy_eval/subset10/summary.md`:
- `gpt_5_2_high` overall=4.69, linking=4.80
- `gpt_5_2_xhigh` overall=4.67, qualities=5.00
- `codex_5_3_high` overall=4.60, wins=13 but with a best/worst split (often ranked #1 or #3).

## Recommendation
- Default extraction config: **`gpt-5.2` with `model_reasoning_effort="high"`**.

Rationale:
- Highest overall average and strongest linking score in this eval.
- `xhigh` improves qualities slightly but does not improve labeling/lemma/linking enough to justify the large cost increase in routine runs.
- `gpt-5.3-codex` shows higher “win” counts but also more “worst” rankings, consistent with a higher-variance behavior.

## Follow-ups (prompt/schema improvements)
Common reviewer-noted issues:
- Over-extraction of generic `δύναμις` as `QUALITY_PROPERTY` (may be acceptable, but if not, tighten prompt).
- Inconsistent SUBSTANCE_PART metadata: some outputs leave `lemma_gr`/`lemma_normalized` blank while setting high `lemma_confidence`.
- Occasional normalization artifacts (diacritics retained in a "normalized" field).

Suggested next step: update the extraction prompt + schema checks to explicitly forbid diacritics in `normalized`/`lemma_normalized` fields and clarify expected SUBSTANCE_PART lemma fields.

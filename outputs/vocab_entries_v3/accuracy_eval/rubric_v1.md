# Accuracy Rubric v1 (Vocab Extraction)

Scope: score model outputs for a given `SOURCE_ID` + `TEXT` (and provided `CONTEXT`) under the extraction prompt + JSON schema.

## Scoring (0-5 each)

### 1) Precision (Hallucinations)
- 5: nearly all extracted terms/qualities are explicitly grounded in TEXT (or CONTEXT only when explicitly signaled by TEXT per prompt).
- 3: some questionable items; a few false positives.
- 1: many hallucinations or repeated grounding failures.

### 2) Coverage (Recall)
- 5: captures the obvious/key domain terms present (substances, parts, preparations, processes, sites, places, named conditions, salient quality-properties).
- 3: misses some important items.
- 1: misses many central items.

### 3) Labeling Correctness
- 5: labels match prompt definitions (SUBSTANCE vs PREPARATION, PART vs APPLICATION_SITE, etc.).
- 3: a few label mixups.
- 1: frequent mislabeling.

### 4) Lemma Quality
- 5: lemma_gr is plausible and lemma_normalized matches normalization rules.
- 3: mixed; some lemma guesses are off.
- 1: lemmata are often wrong/unhelpful.

### 5) Linking / Applies-To Correctness
- 5: `applies_to` is only set when warranted and is correct; SUBSTANCE_PART fields are correctly populated when used.
- 3: some over-linking/under-linking.
- 1: frequent incorrect linking or misuse of SUBSTANCE_PART structure.

### 6) Qualities Extraction Correctness
- 5: axes/degree/intensity/hedge are correct and grounded; applies_to is correct when specified.
- 3: some errors (wrong axis/degree, missing coordinated axes, misapplied subject).
- 1: qualities are mostly wrong or missing when clearly present.

## Review output format
For each packet, reviewer must return JSON with:
- `packet_id`
- `ranked`: ordered list like `["A","B","C"]`
- `scores`: per candidate letter with per-dimension scores 0-5
- `notes`: brief, concrete error notes per candidate (e.g., “missed degree 3 HOT”, “hallucinated PLACE”, “labeled PART as APPLICATION_SITE”).

## Tie-breaking guidance
When two candidates are close:
- Prefer higher Precision over higher Coverage.
- Prefer correctness on `Qualities` and `Linking` over extra miscellaneous term coverage.

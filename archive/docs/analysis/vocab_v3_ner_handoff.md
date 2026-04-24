# Vocab v3 → NER: Handoff and QA Notes

## Summary

This document records a research/scoping session that analyzed the
`outputs/vocab_entries_v3/` extraction results to determine their utility for
Named Entity Recognition (NER) on ancient Greek medical texts, and produced
two concrete implementation sketches.

No runtime code was committed; the deliverable is analysis + two reference
script sketches that can be promoted to `scripts/` after QA.

## What Was Delivered

### 1. Analysis document
**File:** `docs/vocab_v3_analysis_and_ner.md`

Contents:
- Inventory of runs under `outputs/vocab_entries_v3/` (entries_full_v3,
  diosc_smoke_v3_net, accuracy_eval, model_eval, etc.)
- Per-entry output schema with all 11 label categories and quality fields
- Aggregate statistics (26,708 term extractions, 2,885 quality assertions)
- How the outputs feed the TEI-first editorial pipeline
  (`tei_lemma_forms`, `tei_assertions`, controlled vocab tables)
- NER applicability assessment: strengths, gaps, and five use cases
- Two reference script sketches (Approach A: gazetteer, Approach B: span alignment)
- Comparison table and recommended path

### 2. Reference script: Gazetteer builder (Approach A)
**Location:** inline in §4 of the analysis document (not yet saved as runnable script)

Behavior:
- Reads `outputs/vocab_entries_v3/entries_full_v3/results/*.json`
- Aggregates unique `(lemma_normalized, label)` pairs
- Records entry_count, mean_confidence, is_multiword, display_forms
- Filters by `--min-confidence` (default 0.75) and `--min-entries`
- Outputs TSV sorted by entry count descending

### 3. Reference script: Span alignment / BIO tagger (Approach B)
**Location:** inline in §5 of the analysis document (not yet saved as runnable script)

Behavior:
- Loads Greek text from `data-workbench/entries.csv` (`greek` column)
- Tokenizes with `packages/textutils/tokenize.py` (gives codepoint offsets)
- Normalizes with `packages/textutils/normalize.py` (v1.1)
- Three-tier matching: exact normalized → lemma-stem prefix → MWE window
- Outputs BIO-tagged token sequences as TSV (entry_id, token_index,
  token_text, token_normalized, start_offset, end_offset, bio_tag)

### 4. Plan file
**File:** `~/.claude/plans/hashed-zooming-wirth.md`

Records scope, deliverables, file references, and verification steps.

## Key Technical Findings

1. **Tokenizer already exists and is suitable for NER.**
   `packages/textutils/tokenize.py` produces tokens with codepoint offsets
   (`start_offset`, `end_offset`). This is exactly the input format a
   sequence-labeling NER needs.

2. **Normalization is lossy but deterministic.**
   `packages/textutils/normalize.py` (v1.1) lowercases, NFD-decomposes, strips
   U+0300–U+036F, NFC-recomposes. Both original `token_text` and
   `token_normalized` are preserved per token, so NER can match on normalized
   forms while annotating the original surface.

3. **Primary gap: no character offsets in the vocab v3 output.**
   Each result JSON lists terms found in an entry but does not mark *where*
   in the entry they appear. The span-alignment sketch (Approach B) bridges
   this gap via normalized matching against the tokenized stream.

4. **Morphological mismatch is real.**
   The extraction's `display` field is a representative form (often nominative);
   the text contains inflected forms. The stem-prefix fallback in Approach B
   handles regular Greek nominal inflection (trim last 1–2 chars of lemma,
   match prefix). False positives possible for short stems — mitigable with
   `min_stem=4`.

5. **Within-entry deduplication means repeated mentions are collapsed.**
   The extraction lists each `(label, lemma_normalized)` once per entry.
   Approach B's stem matching naturally recovers all inflected occurrences,
   effectively un-deduplicating at alignment time.

## QA Steps (Before Promoting Sketches to scripts/)

### Gazetteer builder (Approach A)

- [ ] Save the sketch as `scripts/ner/build_gazetteer.py` (create directory)
- [ ] Run against `outputs/vocab_entries_v3/entries_full_v3/results/` with
      default `--min-confidence 0.75`
- [ ] Verify output row count is in expected range (estimate: 2,000–5,000
      unique `(lemma, label)` pairs after confidence filtering)
- [ ] Spot-check top 20 rows by `entry_count`: they should be common terms
      like θερμός (QUALITY_PROPERTY), ἔλαιον (SUBSTANCE), πυρετός (CONDITION),
      ὕδωρ (SUBSTANCE)
- [ ] Verify label distribution matches the known aggregate
      (QUALITY_PROPERTY should dominate)
- [ ] Spot-check low-count entries (entry_count=1): confirm they look like
      plausible hapax terms, not garbage
- [ ] Test with `--min-confidence 0.90` to see high-precision subset size
- [ ] Verify `display_forms` column contains inflected variants per lemma
- [ ] Check SUBSTANCE_PART handling: the compound key `substance+part`
      should appear for dual-lemma terms

### Span alignment / BIO tagger (Approach B)

- [ ] Save the sketch as `scripts/ner/align_spans.py`
- [ ] Run on a small sample first: `--limit 10`
- [ ] Manually review 3–5 entries' BIO output against the source Greek text:
      - [ ] Do `B-SUBSTANCE` tags land on actual substance mentions?
      - [ ] Do stem-matches produce false positives on common short words?
      - [ ] Are MWE spans correctly contiguous?
- [ ] Check tokens that should be tagged but aren't (false negatives):
      - [ ] Terms with irregular inflection
      - [ ] Terms whose lemma has shifted stress/accent beyond stripping
- [ ] Check tokens tagged with the wrong label:
      - [ ] When the same normalized form appears for multiple labels
      - [ ] Verify confidence-sort-priority is actually working
- [ ] Run on full `entries_full_v3/` corpus
- [ ] Verify tagged-token percentage is in expected range (rough estimate:
      15–30% of tokens given 26,708 extractions vs. ~1.5M tokens total)
- [ ] Count per-label tag distribution; should roughly mirror the gazetteer
      counts scaled by inflected occurrences
- [ ] Test with `--min-stem 4` and compare precision on a manual sample
- [ ] Check memory usage on full run (should be O(entries) since per-entry
      processing releases)

### Cross-script consistency

- [ ] Run both scripts with same `--min-confidence`
- [ ] Confirm gazetteer labels appear as B-tags in alignment output
- [ ] Confirm BIO output does not tag anything absent from the gazetteer
      (sanity check — would indicate a label-mapping bug)

### Integration with existing infrastructure

- [ ] Confirm scripts import cleanly from `packages/textutils/` when run
      from repo root
- [ ] Match the project's stdlib-only convention (no pip dependencies)
- [ ] Consider adding unit tests under `tests/` following the pattern of
      existing `packages/textutils/` tests
- [ ] Verify output TSVs work with standard NER tooling (spaCy, flair, HF)

### Follow-up work (not in scope for this session)

- [ ] Consider replacing stem heuristic with a proper ancient Greek
      morphological analyzer (e.g., Morpheus, CLTK) if precision is
      insufficient
- [ ] Produce a labeled gold-standard sample (~100 entries) for training
      a supervised NER model and measuring the sketches' precision/recall
- [ ] Extend Approach B to align `qualities[].evidence_display` spans,
      which would yield relation-level annotations (axis/degree anchored
      to text)
- [ ] Package gazetteer as a spaCy `PhraseMatcher` or JSONL for direct
      consumption by NER pipelines
- [ ] Extend to Dioscorides once `diosc_smoke_v3_net` results are merged
      with additional Dioscorides runs

## Files Touched This Session

- Created: `docs/vocab_v3_analysis_and_ner.md`
- Created: `docs/vocab_v3_ner_handoff.md` (this file)
- Created: `~/.claude/plans/hashed-zooming-wirth.md`

No code files modified or created outside `docs/`.

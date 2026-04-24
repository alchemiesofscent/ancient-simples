# Vocab v3 Extraction Outputs: Analysis and NER Potential

## 1. Overview

The `outputs/vocab_entries_v3/` directory contains the results of an LLM-driven
domain-specific term extraction pipeline that processes ancient Greek medical text
entries and produces structured JSON annotations per entry. Each result file
identifies pharmaceutical terms, classifies them into a closed label set, provides
normalized and lemmatized forms, and extracts Galenic quality assertions
(HOT/COLD/DRY/WET with degrees).

### 1.1 Extraction runs

| Run | Source corpus | Entries | Status |
|-----|--------------|---------|--------|
| `entries_full_v3/` | Galen *De simplicium* VI–XI + Aetius *Libri Med.* I–II | 2,135 | Complete |
| `diosc_smoke_v3_net/` | Dioscorides *De Materia Medica* I | 25 | Complete |
| `diosc_smoke_v3/` | Dioscorides (test) | 25 | Complete |
| `diosc_smoke_probe*` | Single-entry probes | 3–4 | Test only |
| `accuracy_eval/` | Blinded model comparison (3 models) | ~60 | Evaluation data |
| `model_eval/` | Extended model comparison | ~54 | Evaluation data |

### 1.2 Per-entry output schema

Each result JSON (`schemas/vocab_term_extractor_with_degrees.schema.json`) contains:

```json
{
  "source_id": "GAL_SMT-6.1.1",
  "terms": [
    {
      "label": "<one of 11 labels>",
      "display": "γαστέρα",
      "normalized": "γαστερα",
      "lemma_gr": "γαστήρ",
      "lemma_normalized": "γαστηρ",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE|PART|PREPARATION|SUBSTANCE_PART|UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.85,
      "lemma_confidence": 0.9
    }
  ],
  "qualities": [
    {
      "axis": "HOT|COLD|DRY|WET",
      "degree": 1,
      "intensity": "none|weak|moderate|balanced|strong|extreme",
      "hedge": "none|που|approx",
      "evidence_display": "θερμαίνει κατὰ τὴν πρώτην τάξιν",
      "evidence_normalized": "θερμαινει κατα την πρωτην ταξιν",
      "applies_to": { "..." : "..." },
      "confidence": 0.9
    }
  ]
}
```

### 1.3 Label set

The extraction uses 11 domain-specific entity categories (defined in
`docs/lemma_rules.md`):

| Label | Definition | Examples |
|-------|-----------|----------|
| SUBSTANCE | Base medicinal materials, ingredients, vehicles | μανδραγόρα, πέπερι, ὕδωρ, ὄξος |
| SUBSTANCE_PART | Specific part of a named substance (dual lemma) | *mandrake root* as a unit |
| PART | Physical parts of a substance | ῥίζα, φύλλον, σπέρμα, φλοιός |
| PREPARATION | Procedural outputs | ἀφέψημα, χυμός, κηρωτή, κατάπλασμα |
| PROCESS | Practitioner actions | μίγνυμι, τήκω, ἕψω, ἐπιτίθημι |
| TOOL_CONTAINER | Implements and vessels | ἀγγεῖον, σπόγγος, ἔριον |
| CONDITION | Diseases and clinical states | πυρετός, φλεγμονή, ἕλκος |
| QUALITY_PROPERTY | Pharmacodynamic properties | θερμός, ψυχρός, δύναμις, κρᾶσις |
| APPLICATION_SITE | Bodily target regions | δέρμα, γαστήρ, γλῶττα |
| ADMINISTRATION | Routes of use | ἐσθίειν, πίνειν, καταπίνειν |
| PLACE | Geographic qualifiers | Παρνασσός |

### 1.4 Aggregate statistics (entries_full_v3)

- **26,708 total term extractions** across 11 categories
- Top categories: QUALITY_PROPERTY (10,015), SUBSTANCE (6,936), CONDITION (2,771),
  PROCESS (2,588), APPLICATION_SITE (1,573)
- **2,885 quality assertions** (HOT/COLD/DRY/WET)
- 28.2% of qualities carry explicit Galenic degree values (1–4)

---

## 2. Designed Purpose

The outputs feed the **TEI-first editorial workflow** of the Ancient Simples
project. The pipeline is:

```
vocab v3 results
  → scripts/import_vocab_v3.py (confidence filtering, collision detection)
    → tei_lemma_forms     (draft term candidates, source='v3_import')
    → tei_entry_lemma_forms (entry ↔ form junction)
    → tei_assertions       (quality/part/process assertions, status='draft')
      → Editor review in Next.js UI
        → Confirmed lemmata + assertions
          → Faceted search + controlled vocabulary dropdowns
```

### 2.1 Seed the lemma layer

SUBSTANCE terms above confidence 0.75 become `tei_lemma_forms` rows with
`status='draft'`. Editors curate these into canonical `tei_lemmata` concepts.
Cross-source collisions (same normalized form in both Galen and Aetius) are
automatically flagged `status='needs_review'`.

### 2.2 Seed assertion tables

Quality extractions become `tei_assertions` rows (`assertion_type='quality'`)
with JSONB payloads containing axis, degree, and evidence snippets. Part and
process terms feed `part` and `process` assertions.

### 2.3 Populate controlled vocabulary

Confirmed terms fill the `quality_vocab`, `parts_vocab`, and `process_vocab`
tables, preventing spelling drift in editorial UI dropdowns.

### 2.4 Enable faceted search

Once imported, assertions power structured queries such as:
- "all drugs hot in the 3rd degree"
- "all substances applied to skin"
- "all entries mentioning mandrake"
- "all plant roots across Galen and Aetius"

### 2.5 Model evaluation

The `accuracy_eval/` and `model_eval/` subdirectories store blinded comparison
data used to select the extraction model. Three models were evaluated on a 6-dimension
rubric (precision, coverage, labeling, lemma, linking, qualities). All scored
4.6–4.69/5.0; GPT 5.2 (high reasoning) was selected for the production run.

---

## 3. NER Potential

### 3.1 What makes the outputs NER-relevant

The extraction outputs are entity-typed term inventories with lemmatization —
the same core information an NER system needs, organized at the entry level
rather than the token level.

| NER requirement | What vocab v3 provides |
|----------------|----------------------|
| Entity types | 11 domain categories (finer than standard PER/LOC/ORG) |
| Canonical forms | Normalized + lemmatized forms with confidence scores |
| Domain coverage | 26,708 extractions from 2,135 entries |
| MWE support | `is_multiword` flag + `head_lemma_normalized` |
| Compositional structure | SUBSTANCE_PART decomposition |
| Confidence scores | Both extraction and lemma confidence for filtering |

### 3.2 Concrete NER applications

1. **Gazetteer-based NER** — Aggregate unique `(lemma_normalized, label)` pairs
   into a lookup dictionary. At confidence >= 0.75, this yields thousands of
   high-quality entries for dictionary-lookup NER on unseen Greek medical text.

2. **Training data for sequence-labeling NER** — Re-project extracted terms onto
   the source token stream to produce BIO-tagged sequences. Requires span
   alignment (see Approach B below).

3. **Evaluation gazetteers** — Even without span alignment, the term lists serve
   as gold-standard entity inventories for evaluating NER recall: "did the system
   find all SUBSTANCEs in entry X?"

4. **Cross-corpus transfer** — The lemma inventory is not corpus-specific. A
   gazetteer built from Galen/Aetius generalizes to Dioscorides, Oribasius,
   Paul of Aegina, and other Greek medical authors who share pharmaceutical
   vocabulary.

5. **Relation extraction seed** — The `applies_to` and `evidence_display` fields
   provide proto-relation annotations (quality → substance, process → preparation)
   that could seed relation extraction models.

### 3.3 Gaps and limitations

| Gap | Impact | Mitigation |
|-----|--------|-----------|
| No span offsets | Cannot directly produce BIO/IOB tags | Span alignment (Approach B) |
| Entry-level, not token-level | Terms listed per entry, not anchored to positions | Re-project via tokenizer |
| Deduplication within entry | Repeated mentions collapsed to one record | String matching finds all occurrences |
| LLM extraction noise | Some terms may be hallucinated or misclassified | Filter by confidence >= 0.75–0.8 |
| Morphological mismatch | `display` is representative form, not every inflection | Normalized matching + stem fallback |
| Galenic corpus bias | 2,135 entries are Galen + Aetius; Dioscorides = 25 | Pipeline is ready to extend |
| No negative examples | Outputs list entities, not non-entities | BIO "O" tags assigned to unmatched tokens |

---

## 4. Approach A: Gazetteer Builder

### 4.1 Goal

Aggregate all extraction results into a deduplicated entity dictionary suitable
for dictionary-lookup NER, terminology databases, or as seed data for a
sequence-labeling model's feature set.

### 4.2 Design

Read every result JSON, collect all `(lemma_normalized, label)` pairs, aggregate
attestation counts and confidence statistics, and export a TSV.

### 4.3 Script sketch

```python
#!/usr/bin/env python3
"""Build a domain gazetteer from vocab v3 extraction results.

Usage:
    python build_gazetteer.py \
        --results-dir outputs/vocab_entries_v3/entries_full_v3/results \
        --min-confidence 0.75 \
        --min-entries 1 \
        --out gazetteer.tsv
"""
import argparse
import json
import csv
import sys
from collections import defaultdict
from pathlib import Path


def load_results(results_dir: Path):
    """Yield parsed result dicts from all .json files in directory."""
    for p in sorted(results_dir.glob("*.json")):
        if p.name.endswith(".tmp"):
            continue
        try:
            with open(p) as f:
                yield json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: skipping {p.name}: {e}", file=sys.stderr)


def build_gazetteer(results_dir: Path, min_confidence: float):
    """Aggregate terms into a gazetteer keyed by (lemma_normalized, label).

    Returns dict mapping (lemma_normalized, label) to stats dict.
    """
    gaz = defaultdict(lambda: {
        "lemma_gr": None,        # best polytonic display form
        "label": None,
        "entry_count": 0,        # number of distinct entries attesting this term
        "total_confidence": 0.0,
        "is_multiword": False,
        "display_forms": set(),  # unique surface forms seen
        "entries": set(),        # entry IDs that attest this term
    })

    for result in load_results(results_dir):
        source_id = result.get("source_id", "?")
        for term in result.get("terms", []):
            conf = term.get("confidence", 0.0)
            if conf < min_confidence:
                continue

            lemma_norm = term.get("lemma_normalized", "")
            label = term.get("label", "")
            if not lemma_norm or not label:
                continue

            # For SUBSTANCE_PART, key on the compound rather than empty lemma
            if label == "SUBSTANCE_PART" and not lemma_norm:
                sub = term.get("substance_lemma_normalized", "")
                part = term.get("part_lemma_normalized", "")
                lemma_norm = f"{sub}+{part}" if sub and part else ""
                if not lemma_norm:
                    continue

            key = (lemma_norm, label)
            rec = gaz[key]
            rec["label"] = label
            rec["entry_count"] = len(rec["entries"]) + (
                1 if source_id not in rec["entries"] else 0
            )
            rec["entries"].add(source_id)
            rec["total_confidence"] += conf
            rec["is_multiword"] = rec["is_multiword"] or term.get("is_multiword", False)
            rec["display_forms"].add(term.get("display", ""))

            # Keep the highest-confidence lemma_gr as representative
            if rec["lemma_gr"] is None or conf > (
                rec["total_confidence"] - conf
            ) / max(len(rec["entries"]) - 1, 1):
                rec["lemma_gr"] = term.get("lemma_gr", lemma_norm)

    return gaz


def write_tsv(gaz: dict, out_path: Path, min_entries: int):
    """Write gazetteer to TSV, sorted by entry count descending."""
    rows = []
    for (lemma_norm, label), rec in gaz.items():
        entry_count = len(rec["entries"])
        if entry_count < min_entries:
            continue
        rows.append({
            "lemma_normalized": lemma_norm,
            "lemma_gr": rec["lemma_gr"] or lemma_norm,
            "label": label,
            "entry_count": entry_count,
            "mean_confidence": round(
                rec["total_confidence"] / max(entry_count, 1), 3
            ),
            "is_multiword": rec["is_multiword"],
            "display_forms": "; ".join(sorted(rec["display_forms"] - {""})),
        })

    rows.sort(key=lambda r: (-r["entry_count"], r["label"], r["lemma_normalized"]))

    fieldnames = [
        "lemma_normalized", "lemma_gr", "label", "entry_count",
        "mean_confidence", "is_multiword", "display_forms",
    ]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} gazetteer entries to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Build NER gazetteer from vocab v3")
    parser.add_argument("--results-dir", type=Path, required=True,
                        help="Path to results/ directory")
    parser.add_argument("--min-confidence", type=float, default=0.75,
                        help="Minimum extraction confidence (default: 0.75)")
    parser.add_argument("--min-entries", type=int, default=1,
                        help="Minimum entry attestation count (default: 1)")
    parser.add_argument("--out", type=Path, default=Path("gazetteer.tsv"),
                        help="Output TSV path")
    args = parser.parse_args()

    gaz = build_gazetteer(args.results_dir, args.min_confidence)
    write_tsv(gaz, args.out, args.min_entries)


if __name__ == "__main__":
    main()
```

### 4.4 Output format

```
lemma_normalized  lemma_gr  label             entry_count  mean_confidence  is_multiword  display_forms
θερμος            θερμός    QUALITY_PROPERTY   847          0.912            False         θερμά; θερμή; θερμόν; θερμός
ελαιον            ἔλαιον    SUBSTANCE          412          0.884            False         ἐλαίου; ἐλαίῳ; ἔλαιον
πυρετος           πυρετός   CONDITION          298          0.871            False         πυρετοῖς; πυρετόν; πυρετός
```

### 4.5 Usage for NER

- **Exact-match NER**: For each token in unseen text, normalize it and look up
  `(token_normalized, *)` in the gazetteer. If found, assign the most frequent
  label. Fast and interpretable; no training required.
- **Feature input**: Feed gazetteer membership and label as features to a
  CRF or neural sequence labeler alongside character and contextual features.
- **Recall evaluation**: Compare NER system output against gazetteer inventory
  to estimate entity recall per category.

---

## 5. Approach B: Span Alignment (BIO Tagger)

### 5.1 Goal

Re-project entry-level term extractions onto the source token stream to produce
BIO-tagged token sequences suitable for training or evaluating a sequence-labeling
NER model.

### 5.2 Key infrastructure

The project already provides the two components needed:

- **`packages/textutils/tokenize.py`** — Tokenizes Greek text into spans defined
  by Unicode L*/N*/Mn character sequences. Each token carries `token_text`,
  `token_normalized`, `start_offset`, and `end_offset` (codepoint indices).

- **`packages/textutils/normalize.py`** — Greek normalization v1.1: lowercase,
  NFD, strip combining marks U+0300–U+036F, NFC. Used by the tokenizer to
  produce `token_normalized`.

### 5.3 Matching strategy

The extracted `display` form is a representative surface form — it may not match
every inflected occurrence in the text. Matching proceeds in three tiers:

1. **Exact normalized match**: `normalize(display) == token.token_normalized`.
   Handles accent/breathing variation.

2. **Lemma-stem prefix match**: If exact match fails, check whether
   `token.token_normalized` starts with a stem derived from `lemma_normalized`
   (e.g., `lemma_normalized="μανδραγορα"` matches tokens `μανδραγορας`,
   `μανδραγοραν`, `μανδραγορου`). The stem is the lemma minus its last 1–2
   characters (a rough but effective heuristic for Greek nominal inflection).

3. **MWE window match**: For multiword terms, match contiguous token windows
   where each token matches a word of the normalized display form.

### 5.4 Script sketch

```python
#!/usr/bin/env python3
"""Align vocab v3 extractions to source text tokens, producing BIO-tagged output.

Usage:
    python align_spans.py \
        --results-dir outputs/vocab_entries_v3/entries_full_v3/results \
        --entries-csv data-workbench/entries.csv \
        --min-confidence 0.70 \
        --out aligned_bio.tsv

Requires: packages/textutils on PYTHONPATH (or run from repo root).
"""
import argparse
import csv
import json
import sys
from pathlib import Path

# Add packages to path for textutils import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages"))
from textutils.tokenize import tokenize  # noqa: E402
from textutils.normalize import normalize  # noqa: E402


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------

def load_entries_csv(csv_path: Path) -> dict[str, str]:
    """Load entries CSV, return {entry_id: greek_text}."""
    entries = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = row.get("entry_id", "")
            greek = row.get("greek", "")
            if eid and greek:
                # CSV uses literal \n tokens for newlines within fields
                entries[eid] = greek.replace("\\n", "\n")
    return entries


def load_result(result_path: Path) -> dict | None:
    """Load a single extraction result JSON."""
    try:
        with open(result_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Matching engine
# ---------------------------------------------------------------------------

def make_stem(lemma_normalized: str, min_stem: int = 3) -> str:
    """Derive a rough stem by trimming the last 1-2 chars of the lemma.

    Greek nominal inflection typically modifies the final 1-2 characters.
    This is a heuristic; false positives are possible for short lemmata.
    """
    if len(lemma_normalized) <= min_stem:
        return lemma_normalized
    # Try trimming 2, then 1
    return lemma_normalized[:-2] if len(lemma_normalized) > min_stem + 1 \
        else lemma_normalized[:-1]


def find_single_token_matches(
    tokens: list[dict],
    term_normalized: str,
    lemma_normalized: str,
    min_stem: int = 3,
) -> list[int]:
    """Find token indices matching a single-token term.

    Tier 1: exact normalized match.
    Tier 2: lemma-stem prefix match.
    """
    matches = []
    stem = make_stem(lemma_normalized, min_stem)

    for tok in tokens:
        tn = tok["token_normalized"]
        # Tier 1: exact normalized match
        if tn == term_normalized:
            matches.append(tok["token_index"])
        # Tier 2: stem prefix match (only if exact didn't hit)
        elif len(stem) >= min_stem and tn.startswith(stem):
            matches.append(tok["token_index"])

    return matches


def find_mwe_matches(
    tokens: list[dict],
    mwe_normalized: str,
) -> list[tuple[int, int]]:
    """Find contiguous token windows matching a multiword expression.

    Returns list of (start_token_index, end_token_index) inclusive.
    """
    words = mwe_normalized.split()
    if len(words) < 2:
        return []

    matches = []
    for i in range(len(tokens) - len(words) + 1):
        window = tokens[i : i + len(words)]
        if all(w["token_normalized"] == word for w, word in zip(window, words)):
            matches.append((tokens[i]["token_index"], tokens[i + len(words) - 1]["token_index"]))

    return matches


# ---------------------------------------------------------------------------
# BIO tagger
# ---------------------------------------------------------------------------

def assign_bio_tags(
    tokens: list[dict],
    terms: list[dict],
    min_confidence: float,
) -> list[str]:
    """Assign BIO tags to each token based on extracted terms.

    Returns a list of tags parallel to tokens. Uses first-match priority
    (higher-confidence terms should be sorted first).
    """
    tags = ["O"] * len(tokens)

    # Sort terms by confidence descending so higher-confidence terms win ties
    sorted_terms = sorted(terms, key=lambda t: -t.get("confidence", 0.0))

    for term in sorted_terms:
        conf = term.get("confidence", 0.0)
        if conf < min_confidence:
            continue

        label = term.get("label", "")
        display = term.get("display", "")
        term_normalized = normalize(display)
        lemma_normalized = term.get("lemma_normalized", term_normalized)
        is_mwe = term.get("is_multiword", False)

        if is_mwe:
            # MWE: match contiguous token windows
            spans = find_mwe_matches(tokens, term_normalized)
            for (start_idx, end_idx) in spans:
                if tags[start_idx] == "O":  # don't overwrite existing
                    tags[start_idx] = f"B-{label}"
                    for j in range(start_idx + 1, end_idx + 1):
                        if tags[j] == "O":
                            tags[j] = f"I-{label}"
        else:
            # Single token: exact or stem match
            match_indices = find_single_token_matches(
                tokens, term_normalized, lemma_normalized
            )
            for idx in match_indices:
                if tags[idx] == "O":
                    tags[idx] = f"B-{label}"

    return tags


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def align_entry(
    entry_id: str,
    greek_text: str,
    result: dict,
    min_confidence: float,
) -> list[dict]:
    """Produce BIO-tagged token rows for one entry."""
    tokens = tokenize(greek_text)
    terms = result.get("terms", [])
    tags = assign_bio_tags(tokens, terms, min_confidence)

    rows = []
    for tok, tag in zip(tokens, tags):
        rows.append({
            "entry_id": entry_id,
            "token_index": tok["token_index"],
            "token_text": tok["token_text"],
            "token_normalized": tok["token_normalized"],
            "start_offset": tok["start_offset"],
            "end_offset": tok["end_offset"],
            "bio_tag": tag,
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Align vocab v3 → BIO tags")
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--entries-csv", type=Path, required=True)
    parser.add_argument("--min-confidence", type=float, default=0.70)
    parser.add_argument("--out", type=Path, default=Path("aligned_bio.tsv"))
    parser.add_argument("--limit", type=int, default=0,
                        help="Process only first N entries (0 = all)")
    args = parser.parse_args()

    entries = load_entries_csv(args.entries_csv)
    print(f"Loaded {len(entries)} entries from {args.entries_csv}", file=sys.stderr)

    fieldnames = [
        "entry_id", "token_index", "token_text", "token_normalized",
        "start_offset", "end_offset", "bio_tag",
    ]

    stats = {"entries": 0, "tokens": 0, "tagged": 0, "unmatched_results": 0}

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()

        result_files = sorted(args.results_dir.glob("*.json"))
        if args.limit > 0:
            result_files = result_files[: args.limit]

        for rpath in result_files:
            result = load_result(rpath)
            if result is None:
                continue

            source_id = result.get("source_id", rpath.stem)
            greek_text = entries.get(source_id)
            if greek_text is None:
                stats["unmatched_results"] += 1
                continue

            rows = align_entry(source_id, greek_text, result, args.min_confidence)
            w.writerows(rows)

            stats["entries"] += 1
            stats["tokens"] += len(rows)
            stats["tagged"] += sum(1 for r in rows if r["bio_tag"] != "O")

    tag_pct = (
        round(100 * stats["tagged"] / stats["tokens"], 1)
        if stats["tokens"] > 0 else 0
    )
    print(
        f"Done: {stats['entries']} entries, {stats['tokens']} tokens, "
        f"{stats['tagged']} tagged ({tag_pct}%), "
        f"{stats['unmatched_results']} unmatched results",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
```

### 5.5 Output format

```
entry_id         token_index  token_text     token_normalized  start_offset  end_offset  bio_tag
GAL_SMT-6.1.1   0            περὶ           περι              0             4           O
GAL_SMT-6.1.1   1            τῆς            της               5             8           O
GAL_SMT-6.1.1   2            μανδραγόρας    μανδραγορας       9             21          B-SUBSTANCE
GAL_SMT-6.1.1   3            ῥίζης          ριζης             22            27          B-PART
GAL_SMT-6.1.1   4            φλοιός         φλοιος            28            34          B-PART
GAL_SMT-6.1.1   5            θερμαίνει      θερμαινει         35            44          B-QUALITY_PROPERTY
...
```

### 5.6 Matching limitations and mitigations

**Morphological mismatch**: The extraction's `display` field is a representative
form (often nominative), but the text contains inflected forms (genitive, dative,
accusative). The stem-prefix fallback (tier 2) handles regular nominal inflection
by matching the first N-2 characters. This works well for longer words but may
produce false positives for short stems (3-4 chars). Set `min_stem=4` for
higher precision at the cost of recall.

**Overlapping entities**: When a token could match multiple labels (e.g., στόμα
as both APPLICATION_SITE and a generic noun), the higher-confidence term wins
(terms are sorted by confidence descending). The first-match-wins rule prevents
double-tagging.

**Missing mentions**: Deduplication in the extraction means each `(label,
lemma_normalized)` appears once per entry, but the stem-matching strategy
naturally finds all inflected occurrences in the text. This actually recovers
mentions that the extraction itself collapsed.

**Quality evidence spans**: The `qualities[].evidence_display` fields contain
short Greek snippets that could be aligned separately to produce relation-level
annotations (quality-assertion anchored to specific text), but this is not
implemented in the sketch above.

---

## 6. Comparison of Approaches

| Dimension | A: Gazetteer | B: Span Alignment |
|-----------|-------------|-------------------|
| Output | Entity dictionary (TSV) | BIO-tagged token sequences (TSV) |
| Effort | Minimal (aggregation only) | Moderate (tokenization + matching) |
| Use case | Lookup NER, feature engineering, evaluation | Training sequence-labeling models |
| Handles context | No (type-level only) | Yes (token-level in context) |
| False positives | Low (attested forms only) | Moderate (stem matching can over-match) |
| Covers all mentions | No (canonical forms only) | Yes (finds inflected occurrences) |
| Requires source text | No | Yes (`entries.csv` or `tei_entries`) |

### Recommended path

1. **Start with Approach A** — build the gazetteer to establish the entity
   inventory and get a quick sense of coverage and label distribution.
2. **Use Approach B on a sample** — align 50–100 entries, manually review the
   BIO output to estimate precision/recall of the matching, tune confidence
   thresholds and stem lengths.
3. **Iterate** — adjust matching tiers based on review; consider adding a
   morphological analyzer (if available for ancient Greek) to replace the
   stem heuristic with proper lemma-to-form expansion.

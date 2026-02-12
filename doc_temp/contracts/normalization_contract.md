# Normalization Contract (C-02)

Version: 1.1
Status: Draft (normative for TEI-first v1)

Change log:
- 1.1: Drop iota subscripts (U+0345) along with all other combining marks in U+0300..U+036F.

## 1. Purpose

This contract defines Ancient Simples normalization (`normalize()`) used for:
- lemma form normalization
- query matching across orthographic variants
- deterministic hashing of normalized text (C-01)

Normalization is a lossy transform intended for matching and indexing, not for display.

## 2. Inputs and outputs

Input:
- Any Unicode string. Callers SHOULD provide NFC-normalized reading text from C-01, but the function MUST be robust to non-NFC input.

Output:
- A Unicode string suitable for stable equality comparisons and prefix matching.

## 3. Versioning

- Implementations MUST expose `NORMALIZATION_VERSION = "1.1"`.
- Any behavior change MUST bump the version.
- `import_runs` MUST record `normalization_version`.

## 4. Algorithm (v1.1)

The v1.1 algorithm MUST perform the following steps, in order:

1) Unicode lowercase
   - Apply Unicode-aware lowercasing.

2) Decompose
   - Convert to Unicode NFD.

3) Strip combining marks
   - Remove all combining characters in the range U+0300..U+036F (inclusive).
   - This includes U+0345 COMBINING GREEK YPOGEGRAMMENI (iota subscript).

4) Recompose
   - Convert back to Unicode NFC.

Explicit non-actions in v1.1:
- Do NOT perform “final sigma” rewriting.
- Do NOT transliterate.

## 5. Invariants

- Determinism: identical input yields identical output.
- Idempotence: `normalize(normalize(x)) == normalize(x)`.
- NFC stability: `normalize(x) == normalize(NFC(x))`.

## 6. Cross-language parity

Normalization MUST be implemented in:
- Python (`packages/textutils/normalize.py`)
- TypeScript (`app/src/lib/greek/normalize.ts`)
- SQL (Postgres function in a migration)

All three implementations MUST produce byte-identical UTF-8 outputs for the same UTF-8 input.

Parity test requirement:
- `tests/test_determinism.py` MUST validate parity on a reference list of at least 50 headwords.

## 7. Reference test cases

The following MUST pass in Python/TS/SQL:

1) Accent stripping
- Input: `"Ψυχρός"`
- Output: `"ψυχρος"`

2) Iota subscript dropped
- Input: `"τῇ"`
- Output: `"τη"`

3) Mixed diacritics
- Input: `"ἄνθρωπος"`
- Output: `"ανθρωπος"`

4) Non-Greek content
- Input: `"Aëtius"`
- Output: `"aetius"`

## 8. Acceptance criteria

C-02 is satisfied when:
- Python/TS/SQL parity tests pass.
- `normalize("Ψυχρός") == "ψυχρος"`.
- `normalize("τῇ") == "τη"`.

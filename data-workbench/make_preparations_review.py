#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


GREEK_TOKEN_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]+", re.UNICODE)


def normalize_greek_for_match(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        ch for ch in text if not unicodedata.combining(ch) or ch == "\u0345"
    )
    return unicodedata.normalize("NFC", text)


def iter_greek_tokens(value: str) -> list[str]:
    return GREEK_TOKEN_RE.findall(value)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"

    xlsx_path = workbench / "Simples.xlsx"
    preparations_csv_path = workbench / "preparations.csv"
    out_csv_path = workbench / "preparations_review.csv"

    if not xlsx_path.exists():
        print(f"ERROR: missing input workbook: {xlsx_path}", file=sys.stderr)
        return 2
    if not preparations_csv_path.exists():
        print(f"ERROR: missing {preparations_csv_path}", file=sys.stderr)
        return 2

    preparations_df = pd.read_csv(preparations_csv_path, dtype=str).fillna("")

    # Tokens that should never be treated as preparations.
    prep_exclude_tokens = {
        # Lexicalized oil-type label ("cold-pressed oil"), not a preparation/state.
        "ωμοτριβες",
        # In this corpus, ξηρά is used as a lexicalized subtype label in resin/oil naming
        # (e.g., πιτυινη ἡ ξηρά), not as a generic drying preparation/state.
        "ξηρα",
    }

    xl = pd.ExcelFile(xlsx_path, engine="openpyxl")

    # Compute attested token norms across scanned fields for exact-form exclusion.
    attested: set[str] = set()
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, usecols=["Lemma", "Chapter_Title", "Section_Title"])
        for col in ["Lemma", "Chapter_Title", "Section_Title"]:
            for value in df[col].dropna().astype(str):
                for token in iter_greek_tokens(value):
                    attested.add(normalize_greek_for_match(token))

    # Explicit preparation forms to exclude from review (these should be linkable, not "review").
    known_prep_forms: set[str] = set()
    for _, r in preparations_df.iterrows():
        base = normalize_greek_for_match(str(r["greek"]))
        known_prep_forms.add(base)
        if base == "κεκαυμενος":
            known_prep_forms |= {t for t in attested if t.startswith("κεκαυμε")}
        elif base == "εψησις":
            known_prep_forms |= {t for t in attested if t.startswith("εψησ")}
        elif base == "πεπλυμενος":
            known_prep_forms |= {t for t in attested if t.startswith("πεπλυμε")}

    # Candidate families: genuinely preparation-like processes/adjectives.
    stem_reasons = {
        "εψη": "Looks like a boiling/cooking family (ἑψ-/ἐψ-).",
        "πεπλυ": "Looks like a washing family (πεπλυ-).",
        "εκπιεσ": "Looks like an expressing/pressing family (ἐκπιεσ-).",
        "τετριμ": "Looks like a grinding family (τετριμ-).",
        "κοπαν": "Looks like a pounding family (κοπαν-).",
        "ξηρ": "Looks like a drying state (ξηρ-).",
    }

    token_examples: dict[str, list[str]] = defaultdict(list)
    token_reason: dict[str, str] = {}
    token_count: dict[str, int] = defaultdict(int)

    for sheet in xl.sheet_names:
        df = xl.parse(sheet, usecols=["Lemma", "Chapter_Title", "Section_Title"])
        for col in ["Lemma", "Chapter_Title", "Section_Title"]:
            for value in df[col].dropna().astype(str):
                tokens = iter_greek_tokens(value)
                norms = [normalize_greek_for_match(t) for t in tokens]
                norms_set = set(norms)

                for token, token_norm in zip(tokens, norms):
                    if token_norm in prep_exclude_tokens:
                        continue
                    if token_norm in known_prep_forms:
                        continue
                    if token_norm.startswith("κεκαυμε"):
                        # Avoid listing inflected forms of κεκαυμένος in review output.
                        continue

                    reason = None
                    for stem, r in stem_reasons.items():
                        if token_norm.startswith(stem):
                            reason = r
                            break
                    if not reason:
                        continue

                    # Exclude the ωμοτριβές-with-ἔλαιον pattern explicitly, even if stems change later.
                    if token_norm == "ωμοτριβες" and "ελαιον" in norms_set:
                        continue

                    token_count[token_norm] += 1
                    token_reason[token_norm] = reason
                    if len(token_examples[token_norm]) < 3:
                        clipped = value.strip().replace("\n", " ")
                        if len(clipped) > 180:
                            clipped = clipped[:177] + "..."
                        token_examples[token_norm].append(clipped)

    rows: list[dict[str, str]] = []
    for token_norm, count in sorted(token_count.items(), key=lambda kv: (-kv[1], kv[0])):
        ex = token_examples.get(token_norm, [])
        rows.append(
            {
                "greek": token_norm,
                "context": ex[0] if ex else "",
                "reason": token_reason.get(token_norm, ""),
                "suggested_scope": "all",
            }
        )

    pd.DataFrame(rows, columns=["greek", "context", "reason", "suggested_scope"]).to_csv(
        out_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    print(f"Wrote {out_csv_path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

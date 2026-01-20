#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from workbook_utils import (
    EXPECTED_SHEETS,
    build_ref,
    dedupe_entry_ids,
    find_workbook_path,
    source_code_for_sheet,
)


GREEK_TOKEN_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]+", re.UNICODE)


@dataclass(frozen=True)
class PrepMatchRule:
    prep_id: str
    greek: str
    forms_norm: frozenset[str]


def normalize_greek_for_match(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        ch for ch in text if not unicodedata.combining(ch) or ch == "\u0345"
    )
    return unicodedata.normalize("NFC", text)


def iter_greek_tokens(value: str) -> Iterable[str]:
    return GREEK_TOKEN_RE.findall(value)


def to_intish_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    try:
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return str(value)
        if isinstance(value, int):
            return str(value)
    except Exception:
        return None
    v = str(value).strip()
    return v if v else None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"

    xlsx_path = find_workbook_path(workbench)
    preparations_csv_path = workbench / "preparations.csv"
    out_csv_path = workbench / "entry_preparations.csv"
    unmatched_csv_path = workbench / "unmatched_preparations.csv"

    if not xlsx_path.exists():
        print(f"ERROR: missing input workbook: {xlsx_path}", file=sys.stderr)
        return 2
    if not preparations_csv_path.exists():
        print(
            f"ERROR: missing preparations vocabulary: {preparations_csv_path}",
            file=sys.stderr,
        )
        return 2

    preparations_df = pd.read_csv(preparations_csv_path, dtype=str).fillna("")

    # Tokens that should never be treated as preparations.
    # Example: ωμοτριβές is a lexicalized oil-type label ("cold-pressed oil"), not a preparation/state.
    prep_exclude_tokens = {
        # Lexicalized oil-type label ("cold-pressed oil"), not a preparation/state.
        "ωμοτριβες",
        # In this corpus, ξηρά is used as a lexicalized subtype label in resin/oil naming
        # (e.g., πιτυινη ἡ ξηρά), not as a generic drying preparation/state.
        "ξηρα",
    }

    # Conservative preparation-like stems (used for unmatched logging only).
    prep_like_stems = {
        "εψη": "boiled/cooked family",
        "πεπλυ": "washed family",
        "εκπιεσ": "expressed/pressed family",
        "τετριμ": "ground family",
        "κοπαν": "pounded family",
        "ξηρ": "dried family",
    }

    xl = pd.ExcelFile(xlsx_path, engine="openpyxl")

    # Build a workbook token set for form-safe, exact matching of attested forms.
    attested_token_norms: set[str] = set()
    for sheet in EXPECTED_SHEETS:
        df = xl.parse(sheet)
        scan_cols = [
            c
            for c in [
                "lemma_gr",
                "var_par_prod_gr",
                "chapter_gr",
                "section_gr",
                "Lemma",
                "Chapter_Title",
                "Section_Title",
            ]
            if c in df.columns
        ]
        for col in scan_cols:
            for value in df[col].dropna().astype(str):
                for token in iter_greek_tokens(value):
                    attested_token_norms.add(normalize_greek_for_match(token))

    # Explicit controlled forms per preparation (exact-match only).
    # For plural/inflected forms: include only if attested in the workbook.
    forms_by_prepid: dict[str, set[str]] = {}
    for _, r in preparations_df.iterrows():
        prep_id = str(r["prep_id"]).strip()
        greek = str(r["greek"]).strip()
        base_norm = normalize_greek_for_match(greek)

        candidates: list[str]
        always_include: set[str] = set()
        if base_norm == "κεκαυμενος":
            # Include all attested κεκαυμ- token forms as full tokens.
            candidates = sorted(
                {t for t in attested_token_norms if t.startswith("κεκαυμε")}
            )
            always_include = {"κεκαυμενος", "κεκαυμενη", "κεκαυμενον"}
        elif base_norm == "εψησις":
            candidates = sorted({t for t in attested_token_norms if t.startswith("εψησ")})
            always_include = {"εψησις", "εψησεως"}
        elif base_norm == "πεπλυμενος":
            candidates = sorted(
                {t for t in attested_token_norms if t.startswith("πεπλυμε")}
            )
            always_include = {"πεπλυμενον"}
        elif base_norm == "αφεψημα":
            candidates = [
                "αφεψημα",
                "αφεψηματος",
                "αφεψηματι",
                "αφεψηματα",
                "αφεψηματων",
            ]
            always_include = {"αφεψημα"}
        else:
            # For any additional genuinely process/adjectival terms, only match the head form unless
            # more forms are explicitly added here later.
            candidates = [base_norm]
            always_include = {base_norm}

        forms = set(always_include)
        for c in candidates:
            if c in always_include:
                continue
            if c in attested_token_norms:
                forms.add(c)
        forms_by_prepid[prep_id] = forms

    rules: list[PrepMatchRule] = []
    for _, r in preparations_df.iterrows():
        prep_id = str(r["prep_id"]).strip()
        greek = str(r["greek"]).strip()
        rules.append(
            PrepMatchRule(
                prep_id=prep_id,
                greek=greek,
                forms_norm=frozenset(forms_by_prepid.get(prep_id, set())),
            )
        )

    out_rows: list[dict[str, str]] = []
    unmatched_rows: list[dict[str, str]] = []

    # Precompute entry_ids with the same deterministic duplicate suffixing as entries.csv.
    base_entry_ids: list[str] = []
    for sheet in EXPECTED_SHEETS:
        df = xl.parse(sheet)
        source_code = source_code_for_sheet(sheet)
        for idx, row in df.iterrows():
            ref = build_ref(row, row_index_1_based=idx + 1)
            base_entry_ids.append(f"{source_code}-{ref}")
    entry_ids = dedupe_entry_ids(base_entry_ids)

    global_row_idx = 0
    for sheet in EXPECTED_SHEETS:
        df = xl.parse(sheet)

        for idx, row in df.iterrows():
            entry_id = entry_ids[global_row_idx]
            global_row_idx += 1

            fields = [
                ("lemma_gr", row.get("lemma_gr") if "lemma_gr" in df.columns else row.get("Lemma")),
                ("var_par_prod_gr", row.get("var_par_prod_gr")),
                ("chapter_gr", row.get("chapter_gr") if "chapter_gr" in df.columns else row.get("Chapter_Title")),
                ("section_gr", row.get("section_gr") if "section_gr" in df.columns else row.get("Section_Title")),
            ]

            matches: list[tuple[str, str]] = []  # (prep_id, notes)
            seen_prep_ids: set[str] = set()

            for field_name, value in fields:
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    continue
                text = str(value)
                tokens = list(iter_greek_tokens(text))
                tokens_norm = [normalize_greek_for_match(t) for t in tokens]
                tokens_norm_set = set(tokens_norm)
                for token in tokens:
                    token_norm = normalize_greek_for_match(token)

                    if token_norm in prep_exclude_tokens:
                        # Exclude known lexicalized qualifiers (e.g., ωμοτριβές with ἔλαιον).
                        # Treat as lemma/product qualifier, not a preparation/state.
                        continue

                    matched = False
                    for rule in rules:
                        if token_norm in rule.forms_norm:
                            matched = True
                            if rule.prep_id not in seen_prep_ids:
                                seen_prep_ids.add(rule.prep_id)
                                matches.append(
                                    (
                                        rule.prep_id,
                                        f"matched_in={field_name}; token={token}",
                                    )
                                )
                            matched = True
                            break

                    if matched:
                        continue

                    stem_hit = None
                    for stem in prep_like_stems:
                        if token_norm.startswith(stem):
                            stem_hit = stem
                            break
                    if stem_hit:
                        clipped = text.strip().replace("\n", " ")
                        if len(clipped) > 180:
                            clipped = clipped[:177] + "..."
                        unmatched_rows.append(
                            {
                                "entry_id": entry_id,
                                "token": token,
                                "context": f"{field_name}: {clipped}",
                            }
                        )

            for i, (prep_id, notes) in enumerate(matches):
                out_rows.append(
                    {
                        "entry_id": entry_id,
                        "prep_id": prep_id,
                        "is_primary": "true" if i == 0 else "false",
                        "notes": notes,
                    }
                )

    out_df = pd.DataFrame(out_rows, columns=["entry_id", "prep_id", "is_primary", "notes"])
    out_df.to_csv(
        out_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    unmatched_df = pd.DataFrame(
        unmatched_rows, columns=["entry_id", "token", "context"]
    )
    unmatched_df.to_csv(
        unmatched_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    print(f"Wrote {out_csv_path} ({len(out_df)} rows)")
    print(f"Wrote {unmatched_csv_path} ({len(unmatched_df)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def source_code_for_sheet(sheet: str) -> str:
    return {
        "SMT": "GAL_SMT",
        "Alim.Fac": "GAL_ALIM",
        "Oribasius CM 15": "ORIB_CM",
        "Aetius I-II": "AET_LM",
    }.get(sheet, sheet.upper().replace(" ", "_"))


def build_entry_id(row: pd.Series, *, source_code: str, row_index_1_based: int) -> str:
    book = to_intish_string(row.get("Book_Arabic"))
    chapter = to_intish_string(row.get("Chapter_Arabic"))
    section = to_intish_string(row.get("Section_Arabic"))

    ref: str
    if book and chapter:
        ref = f"{book}.{chapter}"
        if section and section not in {"0", "0.0"}:
            ref = f"{ref}.{section}"
    elif section:
        ref = section
    else:
        ref = f"row{row_index_1_based}"

    return f"{source_code}-{ref}"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"

    xlsx_path = workbench / "Simples.xlsx"
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

    # Conservative preparation-like stems (used for unmatched logging only).
    prep_like_stems = {
        "εψη": "boiled/cooked family",
        "πεπλυ": "washed family",
        "εκπιεσ": "expressed/pressed family",
        "τετριμ": "ground family",
        "κοπαν": "pounded family",
        "ξηρ": "dried family",
        "ωμ": "raw family",
    }

    xl = pd.ExcelFile(xlsx_path, engine="openpyxl")

    # Build a workbook token set for form-safe, exact matching of attested forms.
    attested_token_norms: set[str] = set()
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, usecols=["Lemma", "Chapter_Title", "Section_Title"])
        for col in ["Lemma", "Chapter_Title", "Section_Title"]:
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
            candidates = [
                "κεκαυμενος",
                "κεκαυμενη",
                "κεκαυμενον",
                "κεκαυμενοι",
                "κεκαυμεναι",
                "κεκαυμενα",
                "κεκαυμενων",
                "κεκαυμενους",
                "κεκαυμεναις",
                "κεκαυμενοις",
                "κεκαυμενης",
                "κεκαυμενου",
                "κεκαυμενω",
            ]
            always_include = {"κεκαυμενος", "κεκαυμενη", "κεκαυμενον"}
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

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        source_code = source_code_for_sheet(sheet)

        for idx, row in df.iterrows():
            entry_id = build_entry_id(row, source_code=source_code, row_index_1_based=idx + 1)

            fields = [
                ("Lemma", row.get("Lemma")),
                ("Chapter_Title", row.get("Chapter_Title")),
                ("Section_Title", row.get("Section_Title")),
            ]

            matches: list[tuple[str, str]] = []  # (prep_id, notes)
            seen_prep_ids: set[str] = set()

            for field_name, value in fields:
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    continue
                text = str(value)
                tokens = list(iter_greek_tokens(text))
                for token in tokens:
                    token_norm = normalize_greek_for_match(token)

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

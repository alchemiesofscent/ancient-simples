#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

from workbook_utils import (
    EXPECTED_SHEETS,
    build_ref,
    dedupe_entry_ids,
    find_workbook_path,
    normalize_greek_for_match,
    source_code_for_sheet,
)


GREEK_TOKEN_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]+", re.UNICODE)


def is_nullish_cell(value: str) -> bool:
    v = value.strip().lower()
    return v in {"", "null", "(null)", "nan"}


def split_lemma_items(value: object) -> list[str]:
    original = str(value).strip()
    if is_nullish_cell(original):
        return []

    base_parts = [p.strip() for p in re.split(r"[;,]", original) if p.strip()]

    original_norm = normalize_greek_for_match(original)
    kai_count = original_norm.count(" και ")
    te_kai_count = original_norm.count(" τε και ")
    list_like = ("," in original or ";" in original) or (kai_count + te_kai_count >= 3)

    items: list[str] = []
    if list_like:
        conj_re = re.compile(r"\s+(?:τε\s+)?κα(?:ὶ|ι)\s+", re.UNICODE)
        for part in base_parts:
            subparts = [s.strip() for s in conj_re.split(part) if s.strip()]
            items.extend(subparts if subparts else [part])
    else:
        items = base_parts

    return [i for i in items if i.strip()]


def lemma_id_sort_key(lemma_id: str) -> int:
    s = str(lemma_id).strip()
    if len(s) >= 2 and s[0] in {"L", "l"}:
        digits = "".join(ch for ch in s[1:] if ch.isdigit())
        if digits:
            return int(digits)
    return 10**9


def load_parts_forms(parts_csv_path: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    """
    Return:
    - norm_form -> [part_id, ...] (to allow ambiguous tokens like ἄνθος)
    - part_id -> base_norm (for diagnostics)
    """
    if not parts_csv_path.exists():
        return {}, {}

    df = pd.read_csv(parts_csv_path, dtype=str).fillna("")
    if "part_id" not in df.columns or "greek" not in df.columns:
        return {}, {}

    base_norm_by_id: dict[str, str] = {}
    for _, r in df.iterrows():
        pid = str(r["part_id"]).strip()
        g = str(r["greek"]).strip()
        if not pid or not g:
            continue
        base_norm_by_id[pid] = normalize_greek_for_match(g)

    # Minimal inflection sets for common part nouns (covers the workbook’s plural usage).
    expansions: dict[str, set[str]] = {
        "ριζα": {"ριζα", "ριζης", "ριζαν", "ριζαι", "ριζων", "ριζας"},
        "φυλλον": {"φυλλον", "φυλλα", "φυλλων", "φυλλοις", "φυλλοι"},
        "σπερμα": {"σπερμα", "σπερματος", "σπερματι", "σπερματα", "σπερματων"},
        "καρπος": {"καρπος", "καρπου", "καρπον", "καρποι", "καρπων"},
        "ανθος": {"ανθος", "ανθους", "ανθει", "ανθη", "ανθων"},
        "φλοιος": {"φλοιος", "φλοιου", "φλοιον", "φλοιοι", "φλοιων"},
        "χυλος": {"χυλος", "χυλου", "χυλον", "χυλοι", "χυλων"},
        "οπος": {"οπος", "οπου", "οπον", "οποι", "οπων"},
        "κλαδος": {"κλαδος", "κλαδου", "κλαδον", "κλαδοι", "κλαδων"},
        "βλαστος": {"βλαστος", "βλαστου", "βλαστον", "βλαστοι", "βλαστων"},
        "τεφρα": {"τεφρα", "τεφρας"},
        "αιμα": {"αιμα", "αιματος"},
        "γαλα": {"γαλα", "γαλακτος", "γαλακτι"},
        "χολη": {"χολη", "χολης"},
        "πιμελη": {"πιμελη", "πιμελης"},
        "μυελος": {"μυελος", "μυελου"},
        "ηπαρ": {"ηπαρ", "ηπατος"},
        "κοπρος": {"κοπρος", "κοπρου"},
        "ουρον": {"ουρον", "ουρου"},
        "οστουν": {"οστουν", "οστα", "οστου", "οστων"},
        "κερας": {"κερας", "κερατος", "κερατα", "κερατων"},
        "δερμα": {"δερμα", "δερματος"},
        "ονυξ": {"ονυξ", "ονυχος", "ονυχες"},
        "ωον": {"ωον", "ωου", "ωα"},
        "λιθος": {"λιθος", "λιθου", "λιθον", "λιθοι", "λιθων"},
        "σποδος": {"σποδος", "σποδου", "σποδον", "σποδοι", "σποδων"},
    }

    norm_to_ids: dict[str, list[str]] = defaultdict(list)
    for pid, base_norm in base_norm_by_id.items():
        forms = expansions.get(base_norm, {base_norm})
        for f in forms:
            norm_to_ids[f].append(pid)
    for f in list(norm_to_ids.keys()):
        norm_to_ids[f] = sorted(norm_to_ids[f])

    return dict(norm_to_ids), base_norm_by_id


def normalize_category(value: object) -> str:
    v = str(value).strip().lower()
    return {"plant": "vegetable", "animal": "animal", "mineral": "mineral"}.get(v, "")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"

    xlsx_path = find_workbook_path(workbench)
    entries_csv_path = workbench / "entries.csv"
    lemmata_csv_path = workbench / "lemmata.csv"
    parts_csv_path = workbench / "parts.csv"
    unmatched_terms_csv_path = workbench / "unmatched_terms.csv"

    if not entries_csv_path.exists():
        print(f"ERROR: missing {entries_csv_path}; run make_entries.py first.", file=sys.stderr)
        return 2
    if not lemmata_csv_path.exists():
        print(f"ERROR: missing {lemmata_csv_path}; run make_lemmata.py first.", file=sys.stderr)
        return 2

    lemmata_df = pd.read_csv(lemmata_csv_path, dtype=str).fillna("")
    if "lemma_id" not in lemmata_df.columns or "headword_normalized" not in lemmata_df.columns:
        print("ERROR: lemmata.csv missing required columns.", file=sys.stderr)
        return 2

    # Map normalized headword -> canonical lemma_id (lowest numeric ID).
    norm_to_lemma_ids: dict[str, list[str]] = defaultdict(list)
    for _, r in lemmata_df.iterrows():
        norm = str(r["headword_normalized"]).strip()
        lid = str(r["lemma_id"]).strip()
        if norm and lid:
            norm_to_lemma_ids[norm].append(lid)
    norm_to_canonical: dict[str, str] = {}
    for norm, lids in norm_to_lemma_ids.items():
        norm_to_canonical[norm] = sorted(lids, key=lemma_id_sort_key)[0]

    # Tokens attested in the legacy "lemma" column that are actually preparation/process
    # words, not substances; keep them out of unmatched_terms.csv.
    ignore_unmatched_norms = {
        "βρεξαντα",
        "εψησις",
        "εψησεως",
    }

    parts_form_to_ids, _base_norm_by_id = load_parts_forms(parts_csv_path)

    xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
    missing_sheets = [s for s in EXPECTED_SHEETS if s not in xl.sheet_names]
    if missing_sheets:
        print(f"ERROR: missing expected sheets: {missing_sheets}", file=sys.stderr)
        return 2

    # Build entry_ids aligned to the workbook row order.
    base_entry_ids: list[str] = []
    row_payloads: list[dict[str, object]] = []
    for sheet in EXPECTED_SHEETS:
        df = xl.parse(sheet)
        source = source_code_for_sheet(sheet)
        for idx, row in df.iterrows():
            ref = build_ref(row, row_index_1_based=idx + 1)
            base_entry_ids.append(f"{source}-{ref}")
            row_payloads.append(
                {
                    "sheet": sheet,
                    "row_index_1": idx + 2,
                    "lemma_cell": row.get("lemma_gr") if "lemma_gr" in df.columns else row.get("Lemma"),
                    "var_par_prod_gr": row.get("var_par_prod_gr"),
                    "cat": row.get("cat") if "cat" in df.columns else row.get("Category"),
                }
            )
    entry_ids = dedupe_entry_ids(base_entry_ids)
    if len(entry_ids) != len(row_payloads):
        print("ERROR: internal row alignment mismatch.", file=sys.stderr)
        return 2

    entry_to_lemma_ids: dict[str, str] = {}
    entry_to_part_id: dict[str, str] = {}
    unmatched_rows: list[dict[str, str]] = []

    for entry_id, payload in zip(entry_ids, row_payloads):
        sheet = str(payload["sheet"])
        row_index_1 = int(payload["row_index_1"])
        lemma_cell = payload.get("lemma_cell")
        cat_norm = normalize_category(payload.get("cat"))

        items = split_lemma_items("" if lemma_cell is None else lemma_cell)
        matched_ids: list[str] = []
        for item in items:
            item_norm = normalize_greek_for_match(item)
            if item_norm in ignore_unmatched_norms:
                continue
            lemma_id = norm_to_canonical.get(item_norm, "")
            if lemma_id:
                if lemma_id not in matched_ids:
                    matched_ids.append(lemma_id)
                continue
            unmatched_rows.append(
                {
                    "entry_id": entry_id,
                    "unmatched_term": item,
                    "context": f"{sheet} row {row_index_1}: {str(lemma_cell).strip()}",
                }
            )
        entry_to_lemma_ids[entry_id] = ",".join(matched_ids)

        # part_id assignment (conservative): if exactly one controlled part token appears in var_par_prod_gr.
        var_text = "" if payload.get("var_par_prod_gr") is None else str(payload["var_par_prod_gr"])
        part_matches: set[str] = set()
        for tok in GREEK_TOKEN_RE.findall(var_text):
            tok_norm = normalize_greek_for_match(tok)
            candidate_ids = parts_form_to_ids.get(tok_norm, [])
            if not candidate_ids:
                continue
            if len(candidate_ids) == 1:
                part_matches.add(candidate_ids[0])
                continue
            # Disambiguate ἄνθος (flower vs mineral efflorescence) using workbook category.
            if cat_norm == "mineral" and "P302" in candidate_ids:
                part_matches.add("P302")
            elif cat_norm in {"vegetable", "animal"} and "P005" in candidate_ids:
                part_matches.add("P005")

        entry_to_part_id[entry_id] = part_matches.pop() if len(part_matches) == 1 else ""

    entries_df = pd.read_csv(entries_csv_path, dtype=str).fillna("")
    if "entry_id" not in entries_df.columns:
        print("ERROR: entries.csv missing entry_id column.", file=sys.stderr)
        return 2
    if "lemma_ids" not in entries_df.columns or "part_id" not in entries_df.columns:
        print("ERROR: entries.csv missing lemma_ids/part_id columns.", file=sys.stderr)
        return 2

    entries_df["lemma_ids"] = entries_df["entry_id"].map(entry_to_lemma_ids).fillna("")
    entries_df["part_id"] = entries_df["entry_id"].map(entry_to_part_id).fillna("")

    entries_df.to_csv(
        entries_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    pd.DataFrame(unmatched_rows, columns=["entry_id", "unmatched_term", "context"]).to_csv(
        unmatched_terms_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    print(f"Updated {entries_csv_path} (lemma_ids, part_id)")
    print(f"Wrote {unmatched_terms_csv_path} ({len(unmatched_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

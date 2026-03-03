#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
import sys


_THIS_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGES_PATH = _THIS_REPO_ROOT / "packages"
if str(_PACKAGES_PATH) not in sys.path:
    sys.path.insert(0, str(_PACKAGES_PATH))

from textutils.normalize import normalize as normalize_greek


EXPECTED_COLUMNS = [
    "entry_id",
    "source",
    "ref",
    "chapter_title_gr",
    "chapter_title_en",
    "lemma_ids",
    "part_id",
    "greek",
    "greek_normalized",
    "translation",
    "trans_status",
    "e_vol",
    "e_page_start",
    "e_page_end",
    "word_count",
    "notes",
]

_ENTRY_BASE_RE = re.compile(r"^(DIOSC_DMM-.+?)(?:~(\d+))?$")
_DIGITS_RE = re.compile(r"^\d+$")


def _word_count_simple(text: str) -> int:
    return len([t for t in (text or "").strip().split() if t])


def _is_numeric_or_empty(value: str) -> bool:
    return value == "" or bool(_DIGITS_RE.match(value))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate data-workbench/entries_diosc.csv.")
    ap.add_argument(
        "--csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "entries_diosc.csv"),
        help="Path to entries_diosc.csv",
    )
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    seen_entry_ids: set[str] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        if fieldnames != EXPECTED_COLUMNS:
            errors.append(
                "Header mismatch.\n"
                + f"Expected: {EXPECTED_COLUMNS}\n"
                + f"Actual:   {fieldnames}"
            )

        rows = list(reader)

    for idx, row in enumerate(rows, start=2):
        entry_id = (row.get("entry_id") or "").strip()
        source = (row.get("source") or "").strip()
        ref = (row.get("ref") or "").strip()
        greek = row.get("greek") or ""
        greek_normalized = row.get("greek_normalized") or ""
        trans_status = (row.get("trans_status") or "").strip()
        word_count_raw = (row.get("word_count") or "").strip()
        translation = row.get("translation") or ""

        if not entry_id:
            errors.append(f"line {idx}: empty entry_id")
        elif entry_id in seen_entry_ids:
            errors.append(f"line {idx}: duplicate entry_id {entry_id!r}")
        else:
            seen_entry_ids.add(entry_id)

        if source != "DIOSC_DMM":
            errors.append(f"line {idx}: source must be 'DIOSC_DMM' (got {source!r})")

        if not entry_id.startswith("DIOSC_DMM-"):
            errors.append(f"line {idx}: entry_id must start with 'DIOSC_DMM-' (got {entry_id!r})")

        if not ref:
            errors.append(f"line {idx}: ref must be non-empty")

        m = _ENTRY_BASE_RE.match(entry_id)
        if not m:
            errors.append(f"line {idx}: malformed entry_id {entry_id!r}")
        else:
            entry_base = m.group(1)
            expected_base = f"DIOSC_DMM-{ref}"
            if entry_base != expected_base:
                errors.append(
                    f"line {idx}: entry_id/ref mismatch; expected base {expected_base!r}, got {entry_base!r}"
                )

        if not greek.strip():
            errors.append(f"line {idx}: greek must be non-empty")

        expected_norm = normalize_greek(greek)
        if greek_normalized != expected_norm:
            errors.append(
                f"line {idx}: greek_normalized mismatch; expected {expected_norm!r}, got {greek_normalized!r}"
            )

        if trans_status != "draft":
            errors.append(f"line {idx}: trans_status must be 'draft' (got {trans_status!r})")

        if not word_count_raw or not _DIGITS_RE.match(word_count_raw):
            errors.append(f"line {idx}: word_count must be a positive integer (got {word_count_raw!r})")
        else:
            expected_wc = _word_count_simple(greek)
            actual_wc = int(word_count_raw)
            if actual_wc <= 0:
                errors.append(f"line {idx}: word_count must be > 0 (got {actual_wc})")
            if actual_wc != expected_wc:
                errors.append(
                    f"line {idx}: word_count mismatch; expected {expected_wc}, got {actual_wc}"
                )

        for col in ["e_vol", "e_page_start", "e_page_end"]:
            value = (row.get(col) or "").strip()
            if not _is_numeric_or_empty(value):
                errors.append(f"line {idx}: {col} must be numeric or empty (got {value!r})")

        if not translation.strip():
            warnings.append(f"line {idx}: blank translation for {entry_id}")

    if errors:
        print(f"Validation failed: {len(errors)} error(s)", file=sys.stderr)
        for msg in errors[:200]:
            print(f"- {msg}", file=sys.stderr)
        if len(errors) > 200:
            print(f"- ... and {len(errors) - 200} more", file=sys.stderr)
        return 2

    print(f"Validated {csv_path} ({len(rows)} rows)")
    print("OK")
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for msg in warnings[:50]:
            print(f"- {msg}")
        if len(warnings) > 50:
            print(f"- ... and {len(warnings) - 50} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

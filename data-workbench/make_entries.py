#!/usr/bin/env python3
from __future__ import annotations

import csv
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Ensure textutils is importable (installed via pyproject.toml editable install).
from textutils.normalize import normalize as _canonical_normalize

from workbook_utils import (
    EXPECTED_SHEETS,
    build_ref,
    dedupe_entry_ids,
    find_workbook_path,
    literal_chapter_title_en,
    single_line_text,
    source_code_for_sheet,
    to_intish_str,
    to_str,
)


@dataclass(frozen=True)
class EntryRow:
    entry_id: str
    source: str
    ref: str
    chapter_title_gr: str
    chapter_title_en: str
    lemma_ids: str
    part_id: str
    greek: str
    greek_normalized: str
    translation: str
    trans_status: str
    e_vol: str
    e_page_start: str
    e_page_end: str
    word_count: str
    notes: str


def normalize_greek(text: str) -> str:
    """Greek normalization v1.1 — delegates to canonical textutils.normalize."""
    return _canonical_normalize(text)


def word_count_simple(greek: str) -> int:
    # Spec permits simple whitespace split.
    return len([t for t in greek.strip().split() if t])


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"
    xlsx_path = find_workbook_path(workbench)
    out_csv_path = workbench / "entries.csv"
    qc_md_path = workbench / "entries_qc.md"

    if not xlsx_path.exists():
        print(f"ERROR: missing input workbook: {xlsx_path}", file=sys.stderr)
        return 2

    xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
    missing = [s for s in EXPECTED_SHEETS if s not in xl.sheet_names]
    if missing:
        print(f"ERROR: missing expected sheets: {missing}", file=sys.stderr)
        return 2

    entries: list[EntryRow] = []
    counts_by_sheet: Counter[str] = Counter()
    skipped: Counter[str] = Counter()
    skipped_examples: dict[str, list[str]] = defaultdict(list)

    for sheet in EXPECTED_SHEETS:
        df = xl.parse(sheet)
        source = source_code_for_sheet(sheet)

        for idx, row in df.iterrows():
            row_index_1 = idx + 2  # include header row offset for human-readable Excel row number

            contents = (
                row.get("entry_gr")
                if "entry_gr" in df.columns
                else row.get("Contents")
            )
            if contents is None or (isinstance(contents, float) and pd.isna(contents)):
                skipped["empty_contents"] += 1
                if len(skipped_examples["empty_contents"]) < 3:
                    skipped_examples["empty_contents"].append(f"{sheet} row {row_index_1}")
                continue

            greek = to_str(contents)
            if not greek.strip():
                skipped["blank_contents"] += 1
                if len(skipped_examples["blank_contents"]) < 3:
                    skipped_examples["blank_contents"].append(f"{sheet} row {row_index_1}")
                continue

            chapter_title_gr = (
                to_str(row.get("section_gr")).strip()
                if "section_gr" in df.columns
                else to_str(row.get("Section_Title")).strip()
            ) or (
                to_str(row.get("chapter_gr")).strip()
                if "chapter_gr" in df.columns
                else to_str(row.get("Chapter_Title")).strip()
            )
            chapter_title_en = literal_chapter_title_en(chapter_title_gr)

            ref = build_ref(row, row_index_1_based=idx + 1)
            entry_id = f"{source}-{ref}"

            translation_raw = (
                to_str(row.get("entry_en"))
                if "entry_en" in df.columns
                else to_str(row.get("Translation"))
            )
            translation = single_line_text(translation_raw)

            e_vol = (
                to_intish_str(row.get("e_vol"))
                if "e_vol" in df.columns
                else to_intish_str(row.get("E_Vol"))
            )
            e_page_start = (
                to_intish_str(row.get("e_p_start"))
                if "e_p_start" in df.columns
                else to_intish_str(row.get("E_P_Start"))
            )
            e_page_end = (
                to_intish_str(row.get("e_p_end"))
                if "e_p_end" in df.columns
                else to_intish_str(row.get("E_P_End"))
            )

            greek_norm = normalize_greek(greek)
            wc = word_count_simple(greek)

            entries.append(
                EntryRow(
                    entry_id=entry_id,
                    source=source,
                    ref=ref,
                    chapter_title_gr=chapter_title_gr,
                    chapter_title_en=chapter_title_en,
                    lemma_ids="",
                    part_id="",
                    greek=greek,
                    greek_normalized=greek_norm,
                    translation=translation,
                    trans_status="draft",
                    e_vol=e_vol,
                    e_page_start=e_page_start,
                    e_page_end=e_page_end,
                    word_count=str(wc),
                    notes="",
                )
            )
            counts_by_sheet[sheet] += 1

    out_df = pd.DataFrame([e.__dict__ for e in entries])[
        [
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
    ]

    # Ensure entry_id uniqueness deterministically by appending a stable suffix when needed.
    base_ids = out_df["entry_id"].astype(str).tolist()
    dup_counts = Counter(base_ids)
    dups = {k: v for k, v in dup_counts.items() if v > 1}
    out_df["entry_id"] = dedupe_entry_ids(base_ids)

    out_df.to_csv(
        out_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    # QC report
    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rnd = random.Random(0)
    sample_indices = (
        rnd.sample(range(len(out_df)), k=min(10, len(out_df))) if len(out_df) else []
    )
    sample_rows = out_df.iloc[sample_indices][["entry_id", "greek"]].to_dict("records")

    qc_lines: list[str] = []
    qc_lines.append("# entries.csv QC report")
    qc_lines.append("")
    qc_lines.append(f"- Generated: `{utc_now}`")
    qc_lines.append(f"- Workbook: `{xlsx_path.name}`")
    qc_lines.append(f"- Total rows: **{len(out_df)}**")
    qc_lines.append("")
    qc_lines.append("## Rows by source sheet")
    for sheet in EXPECTED_SHEETS:
        qc_lines.append(f"- `{sheet}`: {counts_by_sheet.get(sheet, 0)}")
    qc_lines.append("")
    qc_lines.append("## Skipped rows")
    if skipped:
        for reason, count in skipped.most_common():
            ex = ", ".join(skipped_examples.get(reason, []))
            qc_lines.append(f"- `{reason}`: {count}{f' (e.g., {ex})' if ex else ''}")
    else:
        qc_lines.append("- _(none)_")
    qc_lines.append("")
    qc_lines.append("## Sample (10 rows)")
    for r in sample_rows:
        snippet = " ".join(str(r["greek"]).split())
        if len(snippet) > 100:
            snippet = snippet[:97] + "..."
        qc_lines.append(f"- `{r['entry_id']}`: {snippet}")
    qc_lines.append("")

    qc_md_path.write_text("\n".join(qc_lines), encoding="utf-8", newline="\n")

    print(f"Wrote {out_csv_path} ({len(out_df)} rows)")
    print(f"Wrote {qc_md_path}")
    if dups:
        print(f"NOTE: resolved duplicate entry_ids for {len(dups)} refs via '~N' suffixes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

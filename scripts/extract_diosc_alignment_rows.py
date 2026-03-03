#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _row_hash(row: dict[str, str], source_columns: list[str]) -> str:
    payload = {column: row.get(column, "") for column in source_columns}
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _group_id_for_dup_key(key: tuple[str, str, str, str]) -> str:
    return f"DUP_KEY__{key[0]}__{key[1]}__{key[2]}__{key[3]}"


def _group_id_for_dup_entry(entry_text: str) -> str:
    digest = hashlib.sha1(entry_text.encode("utf-8")).hexdigest()[:12]
    return f"DUP_ENTRY_GR__{digest}"


def _preview(value: str, limit: int = 120) -> str:
    value = value.replace("\n", " ").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    ap = argparse.ArgumentParser(description="Extract RV/duplicate/cascade rows from data-workbench/diosc.csv")
    ap.add_argument(
        "--in-csv",
        default=str(repo_root / "data-workbench" / "diosc.csv"),
        help="Input diosc CSV path",
    )
    ap.add_argument(
        "--out-csv",
        default=str(repo_root / "data-workbench" / "diosc_alignment_review.csv"),
        help="Editable review CSV output path",
    )
    ap.add_argument(
        "--out-context-md",
        default=str(repo_root / "data-workbench" / "diosc_alignment_context.md"),
        help="Context markdown output path",
    )
    ap.add_argument(
        "--context-radius",
        type=int,
        default=2,
        help="Context window radius around anchors",
    )
    args = ap.parse_args()

    in_path = Path(args.in_csv)
    out_csv = Path(args.out_csv)
    out_context = Path(args.out_context_md)
    context_radius = max(0, int(args.context_radius))

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    rows: list[tuple[int, dict[str, str]]] = []
    with in_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        source_columns = list(reader.fieldnames or [])
        if not source_columns:
            raise SystemExit(f"Input CSV has no header columns: {in_path}")
        for line_no, row in enumerate(reader, start=2):
            rows.append((line_no, dict(row)))

    if not rows:
        raise SystemExit("Input CSV contains no data rows.")

    row_by_line = {line_no: row for line_no, row in rows}
    all_lines = [line_no for line_no, _ in rows]
    min_line = min(all_lines)
    max_line = max(all_lines)

    duplicate_key_counts: Counter[tuple[str, str, str, str]] = Counter(
        (
            _clean(row.get("book_no")),
            _clean(row.get("chapter_no")),
            _clean(row.get("section_no")),
            _clean(row.get("subsection_no")),
        )
        for _, row in rows
    )
    duplicate_entry_counts: Counter[str] = Counter(_clean(row.get("entry_gr")) for _, row in rows)

    dup_entry_meta: defaultdict[str, set[tuple[str, str]]] = defaultdict(set)
    for _, row in rows:
        entry_text = _clean(row.get("entry_gr"))
        if not entry_text:
            continue
        dup_entry_meta[entry_text].add((_clean(row.get("chapter_no")), _clean(row.get("lemma_en"))))

    anchor_flags_by_line: dict[int, list[str]] = defaultdict(list)
    group_ids_by_line: dict[int, list[str]] = defaultdict(list)

    for line_no, row in rows:
        chapter_no = _clean(row.get("chapter_no"))
        entry_gr = _clean(row.get("entry_gr"))
        key = (
            _clean(row.get("book_no")),
            chapter_no,
            _clean(row.get("section_no")),
            _clean(row.get("subsection_no")),
        )

        if "RV" in chapter_no:
            anchor_flags_by_line[line_no].append("RV_CHAPTER_NO")
            group_ids_by_line[line_no].append(f"RV_CHAPTER__{_clean(row.get('book_no'))}__{chapter_no}")

        if "RV:" in entry_gr:
            anchor_flags_by_line[line_no].append("RV_ENTRY_GR")
            group_ids_by_line[line_no].append(f"RV_ENTRY_GR__line_{line_no}")

        if duplicate_key_counts[key] > 1:
            anchor_flags_by_line[line_no].append("DUP_BOOK_CHAPTER_KEY")
            group_ids_by_line[line_no].append(_group_id_for_dup_key(key))

        if entry_gr and duplicate_entry_counts[entry_gr] > 1:
            anchor_flags_by_line[line_no].append("DUP_ENTRY_GR")
            group_ids_by_line[line_no].append(_group_id_for_dup_entry(entry_gr))
            if len(dup_entry_meta[entry_gr]) > 1:
                anchor_flags_by_line[line_no].append("DUP_ENTRY_GR_META_MISMATCH")

    anchor_lines = sorted(anchor_flags_by_line.keys())
    selected_lines: set[int] = set(anchor_lines)
    for anchor in anchor_lines:
        for line_no in range(anchor - context_radius, anchor + context_radius + 1):
            if min_line <= line_no <= max_line:
                selected_lines.add(line_no)

    ordered_selected = sorted(selected_lines)

    output_columns = [
        "source_line_no",
        "row_role",
        "anchor_flags",
        "anchor_group_id",
        "original_row_hash",
        "action",
        "insert_after_line_no",
        "review_notes",
    ]
    output_columns.extend(source_columns)
    output_columns.extend([f"revised_{column}" for column in source_columns])

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=output_columns, lineterminator="\n")
        writer.writeheader()

        for line_no in ordered_selected:
            row = row_by_line[line_no]
            flags = sorted(set(anchor_flags_by_line.get(line_no, [])))
            groups = sorted(set(group_ids_by_line.get(line_no, [])))
            row_role = "ANCHOR" if flags else "CONTEXT"

            out_row: dict[str, str] = {
                "source_line_no": str(line_no),
                "row_role": row_role,
                "anchor_flags": "|".join(flags),
                "anchor_group_id": "|".join(groups),
                "original_row_hash": _row_hash(row, source_columns),
                "action": "KEEP",
                "insert_after_line_no": "",
                "review_notes": "",
            }
            for column in source_columns:
                out_row[column] = row.get(column, "")
                out_row[f"revised_{column}"] = ""
            writer.writerow(out_row)

    context_lines: list[str] = []
    context_lines.append("# Dioscorides alignment context")
    context_lines.append("")
    context_lines.append(f"- Input: `{in_path}`")
    context_lines.append(f"- Extracted rows: **{len(ordered_selected)}**")
    context_lines.append(f"- Anchor rows: **{len(anchor_lines)}**")
    context_lines.append(f"- Context radius: **{context_radius}**")
    context_lines.append("")
    context_lines.append("## Anchor rows")
    for line_no in anchor_lines:
        row = row_by_line[line_no]
        flags = "|".join(sorted(set(anchor_flags_by_line.get(line_no, []))))
        context_lines.append(
            f"- line {line_no}: b{_clean(row.get('book_no'))}.{_clean(row.get('chapter_no'))} "
            f"`{_clean(row.get('lemma_en'))}` flags=`{flags}`"
        )
    context_lines.append("")
    context_lines.append("## Anchor windows")
    for anchor in anchor_lines:
        context_lines.append("")
        context_lines.append(f"### Anchor line {anchor}")
        for line_no in range(anchor - context_radius, anchor + context_radius + 1):
            if line_no not in row_by_line:
                continue
            row = row_by_line[line_no]
            marker = "*" if line_no == anchor else "-"
            context_lines.append(
                f"{marker} {line_no}: b{_clean(row.get('book_no'))}.{_clean(row.get('chapter_no'))} "
                f"lemma_en={_preview(_clean(row.get('lemma_en')), 36)!r} "
                f"entry_gr={_preview(_clean(row.get('entry_gr')), 70)!r}"
            )
    context_lines.append("")

    out_context.parent.mkdir(parents=True, exist_ok=True)
    out_context.write_text("\n".join(context_lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv} ({len(ordered_selected)} rows)")
    print(f"Wrote {out_context}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

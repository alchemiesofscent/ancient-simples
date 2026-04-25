#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _read_csv_rows(path: Path) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise SystemExit(f"CSV has no header: {path}")
        rows: list[tuple[int, dict[str, str]]] = []
        for line_no, row in enumerate(reader, start=2):
            rows.append((line_no, dict(row)))
    return fieldnames, rows


def _to_greek_numeral(n: int) -> str:
    ones = {1: "α", 2: "β", 3: "γ", 4: "δ", 5: "ε", 6: "ϛ", 7: "ζ", 8: "η", 9: "θ"}
    tens = {10: "ι", 20: "κ", 30: "λ", 40: "μ", 50: "ν", 60: "ξ", 70: "ο", 80: "π", 90: "ϟ"}
    hundreds = {
        100: "ρ",
        200: "σ",
        300: "τ",
        400: "υ",
        500: "φ",
        600: "χ",
        700: "ψ",
        800: "ω",
        900: "ϡ",
    }
    if n <= 0 or n >= 1000:
        return ""
    out: list[str] = []
    remaining = n
    for place, mapping in ((100, hundreds), (10, tens), (1, ones)):
        digit = remaining // place
        if digit:
            out.append(mapping[digit * place])
            remaining -= digit * place
    return "".join(out) + "´"


def _load_patch_map(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {
            "patch_id",
            "book_no",
            "chapter_no",
            "new_lemma_en",
            "new_chapter_gr",
            "new_lemma_gr",
            "new_entry_gr",
            "new_entry_en",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise SystemExit(f"Patch CSV missing columns: {missing}")

        patch_map: dict[tuple[str, str], dict[str, str]] = {}
        for row in reader:
            key = (_clean(row.get("book_no")), _clean(row.get("chapter_no")))
            patch_map[key] = {k: row.get(k, "") for k in (reader.fieldnames or [])}

    return patch_map


def _strip_rv_prefix(entry_gr: str, chapter_num: int) -> str:
    """
    Many recovered payloads (and some source rows) prefix the Greek entry with
    a bracketed marker like "[73] RV:" or "[190 RV]:".

    We keep RV-ness in chapter_no (e.g. 73_RV) and strip this presentation-only
    prefix from entry_gr to avoid polluting downstream tokenization/extraction.
    """
    s = entry_gr.strip()
    if not s:
        return s

    # Examples we handle:
    # - "[73] RV: ..."
    # - "[190 RV]: ..."
    # - "[137 RV: ..." (missing close bracket in some sources)
    # - "[17]8 RV: ..." (we still strip, but only if it starts the string)
    # Note: Some payloads include "[137 RV:" without a closing bracket.
    # Variant A: "[73] RV: ..." or "[73 RV: ..." (some sources omit the close bracket)
    pat_a = re.compile(rf"^\[\s*{chapter_num}\s*\]?\s*RV\s*:?\s*", flags=re.IGNORECASE)
    # Variant B: "[190 RV]: ..." (RV is inside the bracket)
    pat_b = re.compile(rf"^\[\s*{chapter_num}\s*RV\s*\]?\s*:?\s*", flags=re.IGNORECASE)

    s2 = pat_a.sub("", s, count=1)
    if s2 == s:
        s2 = pat_b.sub("", s, count=1)

    # Defensive cleanup for malformed prefixes that could leave a dangling bracket/colon.
    s2 = re.sub(r"^[\]\s:]+", "", s2).lstrip()
    return s2


def _make_row_from_template(
    template: dict[str, str],
    *,
    book_no: str,
    chapter_no: str,
) -> dict[str, str]:
    out = dict(template)
    out["book_no"] = book_no
    out["chapter_no"] = chapter_no
    out.setdefault("section_no", "")
    out.setdefault("subsection_no", "")
    out.setdefault("section_gr", "")
    out.setdefault("subsection_no_gr", "")
    return out


def _apply_patch_payload(
    row: dict[str, str],
    *,
    patch: dict[str, str],
    chapter_num_for_strip: int | None,
    mode: str,
) -> None:
    """
    mode:
      - "fill": only fill empty fields
      - "replace": overwrite fields regardless of existing content
    """
    if mode not in {"fill", "replace"}:
        raise ValueError(f"Invalid patch mode: {mode}")

    def set_field(field: str, value: str) -> None:
        if mode == "replace" or not _clean(row.get(field)):
            row[field] = value

    set_field("chapter_gr", patch.get("new_chapter_gr", ""))
    set_field("lemma_gr", patch.get("new_lemma_gr", ""))
    set_field("lemma_en", patch.get("new_lemma_en", ""))

    entry_gr = patch.get("new_entry_gr", "")
    if chapter_num_for_strip is not None and entry_gr:
        entry_gr = _strip_rv_prefix(entry_gr, chapter_num_for_strip)
        # Some sources embed the chapter number directly at the start (e.g. "191 ...").
        # Strip it if it looks like a presentation prefix.
        entry_gr = re.sub(
            rf"^{chapter_num_for_strip}\s+(?=[\u0370-\u03FF\u1F00-\u1FFF])",
            "",
            entry_gr,
            count=1,
        )
    set_field("entry_gr", entry_gr)
    set_field("entry_en", patch.get("new_entry_en", ""))


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    ap = argparse.ArgumentParser(description="Apply recovered Dioscorides missing-text patch")
    ap.add_argument("--in-csv", default=str(repo_root / "data-workbench" / "diosc.csv"))
    ap.add_argument(
        "--patch-csv",
        default=str(repo_root / "data-workbench" / "diosc_missing_text_patch.csv"),
    )
    ap.add_argument(
        "--out-csv",
        default=str(repo_root / "data-workbench" / "diosc.patched.csv"),
    )
    ap.add_argument(
        "--apply-report-md",
        default=str(repo_root / "data-workbench" / "diosc_missing_text_apply_report.md"),
    )
    args = ap.parse_args()

    in_path = Path(args.in_csv)
    patch_path = Path(args.patch_csv)
    out_path = Path(args.out_csv)
    apply_report_path = Path(args.apply_report_md)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")
    if not patch_path.exists():
        raise SystemExit(f"Patch CSV not found: {patch_path}")

    source_columns, source_rows = _read_csv_rows(in_path)
    rows_in_order: list[dict[str, str]] = [dict(row) for _line_no, row in source_rows]

    patch_map = _load_patch_map(patch_path)

    def patch_for(book_no: str, chapter_no: str) -> dict[str, str]:
        key = (_clean(book_no), _clean(chapter_no))
        if key not in patch_map:
            raise SystemExit(f"Missing patch payload for {key[0]}.{key[1]}")
        return patch_map[key]

    apply_log: list[str] = []

    # Build index helpers.
    index_by_key: dict[tuple[str, str], int] = {}
    def rebuild_index() -> None:
        index_by_key.clear()
        for i, r in enumerate(rows_in_order):
            key = (_clean(r.get("book_no")), _clean(r.get("chapter_no")))
            index_by_key[key] = i

    rebuild_index()

    def find_idx(book_no: str, chapter_no: str) -> int | None:
        return index_by_key.get((_clean(book_no), _clean(chapter_no)))

    # 1) Fix a known data wart: stray tab/quotes in 2.178_RV var_par_prod_gr.
    idx_178_rv = find_idx("2", "178_RV")
    if idx_178_rv is not None:
        row = rows_in_order[idx_178_rv]
        v = row.get("var_par_prod_gr", "")
        v2 = v.replace("\t", "").strip().strip('"')
        if v2 != v:
            row["var_par_prod_gr"] = v2
            apply_log.append("CLEAN 2.178_RV var_par_prod_gr (strip tab/quotes)")

        # Fill lemma_en from patch payload if missing.
        patch = patch_for("2", "178_RV")
        if not _clean(row.get("lemma_en")):
            row["lemma_en"] = patch.get("new_lemma_en", "")
            apply_log.append("FILL 2.178_RV lemma_en from patch")

    # 2) Fill/clean existing RV rows that are present but missing English.
    for book_no, chapter_no in [("3", "73_RV"), ("4", "58_RV")]:
        idx = find_idx(book_no, chapter_no)
        if idx is None:
            continue
        row = rows_in_order[idx]
        patch = patch_for(book_no, chapter_no)
        chapter_num = int(chapter_no.split("_", 1)[0])
        # Replace entry_gr only if it still contains an RV prefix marker.
        if re.search(r"\bRV\b\s*:", row.get("entry_gr", "")) or row.get("entry_gr", "").lstrip().startswith("["):
            row["entry_gr"] = _strip_rv_prefix(patch.get("new_entry_gr", ""), chapter_num)
            apply_log.append(f"REPLACE {book_no}.{chapter_no} entry_gr (strip RV prefix)")
        _apply_patch_payload(row, patch=patch, chapter_num_for_strip=chapter_num, mode="fill")
        apply_log.append(f"FILL {book_no}.{chapter_no} missing fields (lemma_en/entry_en)")

    # 3) Split embedded RV tails from host rows and insert standalone RV rows when absent.
    #    This makes RV-ness explicit in chapter_no instead of leaving markers in entry_gr.
    marker_re = re.compile(r"\[\s*(\d+)\s*\]?\s*RV\s*:", flags=re.IGNORECASE)
    insertions: list[tuple[int, dict[str, str]]] = []
    split_count = 0
    insert_count = 0

    for idx, row in enumerate(rows_in_order):
        entry_gr = row.get("entry_gr", "") or ""
        m = marker_re.search(entry_gr)
        if not m:
            continue
        chapter_num = int(m.group(1))
        book_no = _clean(row.get("book_no"))
        rv_chapter_no = f"{chapter_num}_RV"

        # Trim host row up to marker.
        trimmed = entry_gr[: m.start()].rstrip()
        if trimmed != entry_gr:
            row["entry_gr"] = trimmed
            split_count += 1
            apply_log.append(f"SPLIT_HOST {book_no}.{row.get('chapter_no')} -> removed [{chapter_num}] RV tail")

        # If an RV row already exists for this chapter_num, don't insert a duplicate.
        if find_idx(book_no, rv_chapter_no) is not None:
            continue

        # Insert an RV row immediately after the host row using patch payload.
        patch_key = (book_no, rv_chapter_no)
        if patch_key not in patch_map:
            apply_log.append(f"SKIP_INSERT missing patch payload for {book_no}.{rv_chapter_no}")
            continue
        patch = patch_map[patch_key]
        new_row = _make_row_from_template(row, book_no=book_no, chapter_no=rv_chapter_no)
        new_row["chapter_no_gr"] = _to_greek_numeral(chapter_num)
        _apply_patch_payload(new_row, patch=patch, chapter_num_for_strip=chapter_num, mode="replace")
        new_row["var_par_prod_gr"] = ""
        new_row["var_par_prod_en"] = ""
        new_row["cat"] = ""
        insertions.append((idx + 1, new_row))
        insert_count += 1
        apply_log.append(f"INSERT_AFTER {book_no}.{row.get('chapter_no')} -> {book_no}.{rv_chapter_no}")

    # Apply insertions from end to start so indices remain stable.
    for insert_at, new_row in sorted(insertions, key=lambda t: t[0], reverse=True):
        rows_in_order.insert(insert_at, new_row)

    if insertions:
        rebuild_index()

    # 4) Fix Book IV 190/191 misalignment:
    #    - 4.190_RV should be Kunea (patch)
    #    - 4.190 should be Large heliotrope (English currently stored in 4.190_RV in the source)
    #    - 4.191 should be Small heliotrope (insert if missing)
    idx_4_190_rv = find_idx("4", "190_RV")
    idx_4_190 = find_idx("4", "190")
    idx_4_191 = find_idx("4", "191")
    if idx_4_190_rv is not None and idx_4_190 is not None:
        row_190_rv = rows_in_order[idx_4_190_rv]
        row_190 = rows_in_order[idx_4_190]

        # Preserve Large heliotrope English before overwriting 190_RV.
        preserved_large_lemma_en = _clean(row_190_rv.get("lemma_en"))
        preserved_large_entry_en = _clean(row_190_rv.get("entry_en"))
        if preserved_large_entry_en:
            row_190["lemma_en"] = preserved_large_lemma_en or row_190.get("lemma_en", "")
            row_190["entry_en"] = preserved_large_entry_en
            apply_log.append("COPY 4.190_RV English -> 4.190 (restore Large heliotrope translation)")

        # Overwrite 4.190_RV with Kunea payload.
        patch_190_rv = patch_for("4", "190_RV")
        _apply_patch_payload(row_190_rv, patch=patch_190_rv, chapter_num_for_strip=190, mode="replace")
        row_190_rv["chapter_no_gr"] = _to_greek_numeral(190)
        apply_log.append("REPLACE 4.190_RV payload -> Kunea")

        # Ensure 4.190 is labeled Large heliotrope.
        if preserved_large_lemma_en:
            row_190["lemma_en"] = preserved_large_lemma_en

        # Insert 4.191 if missing.
        if idx_4_191 is None:
            patch_191 = patch_for("4", "191")
            new_191 = _make_row_from_template(row_190, book_no="4", chapter_no="191")
            new_191["chapter_no_gr"] = _to_greek_numeral(191)
            _apply_patch_payload(new_191, patch=patch_191, chapter_num_for_strip=191, mode="replace")
            new_191["var_par_prod_gr"] = ""
            new_191["var_par_prod_en"] = ""
            new_191["cat"] = ""
            # Insert after 4.190 row in the current list.
            rows_in_order.insert(idx_4_190 + 1, new_191)
            apply_log.append("INSERT_AFTER 4.190 -> 4.191 (Small heliotrope)")

    # Refresh index after mutations.
    rebuild_index()

    # Apply report + sanity checks.
    sanity_errors: list[str] = []

    required_chapters = [
        ("2", "178_RV"),
        ("3", "64_RV"),
        ("3", "73_RV"),
        ("4", "16_RV"),
        ("4", "58_RV"),
        ("4", "127_RV"),
        ("4", "137_RV"),
        ("4", "190_RV"),
        ("4", "190"),
        ("4", "191"),
    ]

    for book_no, chapter_no in required_chapters:
        idx = find_idx(book_no, chapter_no)
        if idx is None:
            sanity_errors.append(f"Missing required chapter row {book_no}.{chapter_no}")
            continue
        row = rows_in_order[idx]
        if not _clean(row.get("entry_gr")):
            sanity_errors.append(f"Chapter {book_no}.{chapter_no} has empty entry_gr")
        if not _clean(row.get("entry_en")):
            sanity_errors.append(f"Chapter {book_no}.{chapter_no} has empty entry_en")

    # No entry_gr should still contain an RV marker prefix/tail.
    rv_left = [
        (i, r.get("book_no", ""), r.get("chapter_no", ""))
        for i, r in enumerate(rows_in_order, start=2)
        if re.search(r"\bRV\b\s*:", r.get("entry_gr", "") or "")
    ]
    if rv_left:
        sanity_errors.append(f"Rows still contain 'RV:' marker text in entry_gr: {len(rv_left)}")

    missing_entry_en_count = sum(1 for row in rows_in_order if not _clean(row.get("entry_en")))

    apply_lines: list[str] = []
    apply_lines.append("# Dioscorides Missing-Text Apply Report")
    apply_lines.append("")
    apply_lines.append(f"- Input CSV: `{in_path}`")
    apply_lines.append(f"- Patch CSV: `{patch_path}`")
    apply_lines.append(f"- Output CSV: `{out_path}`")
    apply_lines.append(f"- Source rows: **{len(source_rows)}**")
    apply_lines.append(f"- Output rows: **{len(rows_in_order)}**")
    apply_lines.append(f"- Inserted rows: **{len(rows_in_order) - len(source_rows)}**")
    apply_lines.append(f"- Missing `entry_en` rows after patch: **{missing_entry_en_count}**")
    apply_lines.append(f"- Sanity errors: **{len(sanity_errors)}**")
    apply_lines.append("")
    apply_lines.append("## Operations")
    apply_lines.append(f"- Split embedded RV tails: **{split_count}**")
    apply_lines.append(f"- Inserted RV rows: **{insert_count}**")
    for line in apply_log:
        apply_lines.append(f"- {line}")

    if sanity_errors:
        apply_lines.append("")
        apply_lines.append("## Sanity Errors")
        for err in sanity_errors:
            apply_lines.append(f"- {err}")

    apply_report_path.parent.mkdir(parents=True, exist_ok=True)
    apply_report_path.write_text("\n".join(apply_lines) + "\n", encoding="utf-8")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=source_columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows_in_order)

    print(f"Wrote {out_path}")
    print(f"Wrote {apply_report_path}")
    if sanity_errors:
        print(f"Completed with {len(sanity_errors)} sanity error(s).")
    else:
        print("Completed with no sanity errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

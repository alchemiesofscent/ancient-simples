#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd


GREEK_TOKEN_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]+", re.UNICODE)


@dataclass(frozen=True)
class PartRow:
    part_id: str
    greek: str
    english: str
    category: str
    notes: str


@dataclass(frozen=True)
class PrepRow:
    prep_id: str
    greek: str
    english: str
    scope: str
    notes: str


def normalize_greek_for_match(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    # Remove accents/breathings, but preserve iota subscript (U+0345) per spec.
    text = "".join(
        ch for ch in text if not unicodedata.combining(ch) or ch == "\u0345"
    )
    return unicodedata.normalize("NFC", text)


def iter_greek_tokens(value: str) -> Iterable[str]:
    return GREEK_TOKEN_RE.findall(value)


def relevant_text_columns(columns: Iterable[object]) -> list[str]:
    out: list[str] = []
    for col in columns:
        name = str(col).strip()
        name_lower = name.lower()
        if "lemma" in name_lower:
            out.append(name)
        elif name_lower in {"chapter_title", "section_title"}:
            out.append(name)
    return out


def split_lemma_items(value: str) -> list[str]:
    # Legacy lemma column uses semicolons; be forgiving.
    return [chunk.strip() for chunk in re.split(r"[;]", value) if chunk.strip()]


def part_id_sort_key(part_id: str) -> tuple[int, str]:
    digits = "".join(ch for ch in part_id if ch.isdigit())
    return (int(digits) if digits else 0, part_id)


def prep_id_sort_key(prep_id: str) -> tuple[int, str]:
    digits = "".join(ch for ch in prep_id if ch.isdigit())
    return (int(digits) if digits else 0, prep_id)


def seed_parts() -> list[PartRow]:
    # Appendix A – Starter Parts Vocabulary (parts/materials/residue nouns only)
    rows: list[PartRow] = [
        # Vegetable
        PartRow("P001", "ῥίζα", "root", "vegetable", ""),
        PartRow("P002", "φύλλον", "leaf", "vegetable", ""),
        PartRow("P003", "σπέρμα", "seed", "vegetable", "Used across plant entries."),
        PartRow("P004", "καρπός", "fruit", "vegetable", ""),
        PartRow("P005", "ἄνθος", "flower", "vegetable", ""),
        PartRow("P006", "φλοιός", "bark", "vegetable", ""),
        PartRow("P007", "χυλός", "juice", "vegetable", ""),
        PartRow("P008", "ὀπός", "resin", "vegetable", ""),
        PartRow("P009", "κλάδος", "branch", "vegetable", ""),
        PartRow("P010", "βλαστός", "shoot", "vegetable", ""),
        # Animal
        PartRow("P201", "αἷμα", "blood", "animal", ""),
        PartRow("P202", "γάλα", "milk", "animal", ""),
        PartRow("P203", "χολή", "bile", "animal", ""),
        PartRow("P204", "πιμελή", "fat", "animal", ""),
        PartRow("P205", "μυελός", "marrow", "animal", ""),
        PartRow("P206", "ἧπαρ", "liver", "animal", ""),
        PartRow("P207", "κόπρος", "dung", "animal", ""),
        PartRow("P208", "οὖρον", "urine", "animal", ""),
        PartRow("P209", "ὀστοῦν", "bone", "animal", ""),
        PartRow("P210", "κέρας", "horn", "animal", ""),
        PartRow("P211", "δέρμα", "skin", "animal", ""),
        PartRow("P212", "ὄνυξ", "claw", "animal", ""),
        PartRow("P213", "ὠόν", "egg", "animal", ""),
        # Mineral
        PartRow("P301", "λίθος", "stone", "mineral", ""),
        PartRow(
            "P302",
            "ἄνθος",
            "efflorescence",
            "mineral",
            "Mineral ‘flower’/efflorescence; distinct from vegetable ἄνθος (flower).",
        ),
        PartRow("P303", "σποδός", "powder/ash residue", "mineral", ""),
    ]

    # Treat residue/product nouns as materials/parts (not preparations), regardless of origin.
    # This includes τέφρα and σποδός.
    rows.append(PartRow("P102", "τέφρα", "ash", "vegetable", ""))

    return rows


def seed_preparations() -> list[PrepRow]:
    # Explicit seeds (stable IDs, minimal set)
    return [
        PrepRow("PR001", "κεκαυμένος", "burnt/calcined", "all", ""),
        PrepRow(
            "PR002",
            "ἀφέψημα",
            "decoction",
            "all",
            "Defined by boiling in liquid; commonly applied to plants but attested for animal substances in medical texts.",
        ),
    ]


def detect_candidate_preparation_tokens(
    xl: pd.ExcelFile,
    *,
    stems: dict[str, str],
    max_examples_per_token: int = 3,
) -> dict[str, dict[str, object]]:
    """
    Return token_norm -> {count:int, examples:[str], reason:str, suggested_scope:str}.
    Conservative: only flags tokens whose normalized form starts with a known stem.
    """
    candidates: dict[str, dict[str, object]] = {}

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        cols = relevant_text_columns(df.columns)
        for col in cols:
            for value in df[col].dropna().astype(str):
                for token in iter_greek_tokens(value):
                    token_norm = normalize_greek_for_match(token)
                    stem_reason = None
                    for stem, reason in stems.items():
                        if token_norm.startswith(stem):
                            stem_reason = reason
                            break
                    if not stem_reason:
                        continue

                    rec = candidates.get(token_norm)
                    if not rec:
                        rec = {
                            "count": 0,
                            "examples": [],
                            "reason": stem_reason,
                            "suggested_scope": "all",
                        }
                        candidates[token_norm] = rec
                    rec["count"] = int(rec["count"]) + 1
                    if len(rec["examples"]) < max_examples_per_token:
                        clipped = value.strip().replace("\n", " ")
                        if len(clipped) > 180:
                            clipped = clipped[:177] + "..."
                        rec["examples"].append(clipped)

    return candidates


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"
    xlsx_path = workbench / "Simples.xlsx"

    parts_csv_path = workbench / "parts.csv"
    parts_qc_md_path = workbench / "parts_qc.md"
    preparations_csv_path = workbench / "preparations.csv"
    preparations_review_csv_path = workbench / "preparations_review.csv"
    diff_report_md_path = workbench / "preparations_diff_report.md"

    if not xlsx_path.exists():
        print(f"ERROR: missing input workbook: {xlsx_path}", file=sys.stderr)
        return 2

    old_parts: list[dict[str, str]] = []
    if parts_csv_path.exists():
        old_parts = pd.read_csv(parts_csv_path, dtype=str).fillna("").to_dict("records")

    old_preps: list[dict[str, str]] = []
    if preparations_csv_path.exists():
        old_preps = (
            pd.read_csv(preparations_csv_path, dtype=str).fillna("").to_dict("records")
        )

    xl = pd.ExcelFile(xlsx_path, engine="openpyxl")

    parts = seed_parts()
    preparations = seed_preparations()

    # Build parts.csv
    parts_df = pd.DataFrame([r.__dict__ for r in parts])[
        ["part_id", "greek", "english", "category", "notes"]
    ]
    parts_df = parts_df.sort_values(by="part_id", key=lambda s: s.map(part_id_sort_key))
    parts_df.to_csv(
        parts_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    # Build preparations.csv
    preparations_df = pd.DataFrame([r.__dict__ for r in preparations])[
        ["prep_id", "greek", "english", "scope", "notes"]
    ]
    preparations_df = preparations_df.sort_values(
        by="prep_id", key=lambda s: s.map(prep_id_sort_key)
    )
    preparations_df.to_csv(
        preparations_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    # Preparations review: conservative token detection (do not auto-add).
    # Stems correspond to common preparation/state families.
    stem_reasons = {
        "κεκαυμ": "Looks like a calcination/burning state (κεκαυμ-).",
        "αφεψημ": "Looks like a decoction noun family (ἀφέψημ-).",
        "εψη": "Looks like a boiling/cooking family (ἑψ-/ἐψ-).",
        "πεπλυ": "Looks like a washing family (πεπλυ-).",
        "εκπιεσ": "Looks like an expressing/pressing family (ἐκπιεσ-).",
        "τετριμ": "Looks like a grinding family (τετριμ-).",
        "κοπαν": "Looks like a pounding family (κοπαν-).",
        "ξηρ": "Looks like a drying state (ξηρ-).",
        "ωμ": "Looks like a raw/uncooked state (ὠμ-).",
    }
    candidate_tokens = detect_candidate_preparation_tokens(xl, stems=stem_reasons)

    existing_prep_norms = {
        normalize_greek_for_match(g): pid
        for pid, g in zip(preparations_df["prep_id"], preparations_df["greek"])
    }

    review_rows: list[dict[str, str]] = []
    for token_norm, rec in sorted(
        candidate_tokens.items(), key=lambda kv: (-int(kv[1]["count"]), kv[0])
    ):
        if token_norm in existing_prep_norms:
            continue
        examples = rec["examples"]
        context = examples[0] if examples else ""
        review_rows.append(
            {
                "greek": token_norm,
                "context": context,
                "reason": str(rec["reason"]),
                "suggested_scope": str(rec["suggested_scope"]),
            }
        )

    pd.DataFrame(review_rows, columns=["greek", "context", "reason", "suggested_scope"]).to_csv(
        preparations_review_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    # Diff report: compare old parts.csv vs new parts.csv; list additions to preparations.csv.
    old_part_ids = {r.get("part_id", "") for r in old_parts}
    new_part_ids = set(parts_df["part_id"].astype(str).tolist())
    removed_part_ids = sorted(old_part_ids - new_part_ids, key=part_id_sort_key)
    added_part_ids = sorted(new_part_ids - old_part_ids, key=part_id_sort_key)

    old_prep_ids = {r.get("prep_id", "") for r in old_preps}
    new_prep_ids = set(preparations_df["prep_id"].astype(str).tolist())
    removed_prep_ids = sorted(old_prep_ids - new_prep_ids, key=prep_id_sort_key)
    added_prep_ids = sorted(new_prep_ids - old_prep_ids, key=prep_id_sort_key)

    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines: list[str] = []
    lines.append("# Preparations split diff report")
    lines.append("")
    lines.append(f"- Generated: `{utc_now}`")
    lines.append(f"- Workbook: `{xlsx_path.name}`")
    lines.append("")
    lines.append("## (a) Removed from parts.csv")
    if removed_part_ids:
        old_by_id = {r["part_id"]: r for r in old_parts if "part_id" in r}
        for pid in removed_part_ids:
            row = old_by_id.get(pid, {})
            lines.append(
                f"- `{pid}` {row.get('greek','')} — {row.get('english','')} ({row.get('category','')})"
            )
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append("## (b) Added to parts.csv")
    if added_part_ids:
        new_by_id = {
            str(r["part_id"]): r
            for r in parts_df.to_dict("records")
            if "part_id" in r
        }
        for pid in added_part_ids:
            row = new_by_id.get(pid, {})
            lines.append(
                f"- `{pid}` {row.get('greek','')} — {row.get('english','')} ({row.get('category','')})"
            )
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append("## (c) Removed from preparations.csv")
    if removed_prep_ids:
        old_by_id = {r["prep_id"]: r for r in old_preps if "prep_id" in r}
        for pid in removed_prep_ids:
            row = old_by_id.get(pid, {})
            lines.append(
                f"- `{pid}` {row.get('greek','')} — {row.get('english','')} (scope: {row.get('scope','')})"
            )
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append("## (d) Added to preparations.csv")
    if added_prep_ids:
        new_by_id = {
            str(r["prep_id"]): r
            for r in preparations_df.to_dict("records")
            if "prep_id" in r
        }
        for pid in added_prep_ids:
            row = new_by_id.get(pid, {})
            lines.append(
                f"- `{pid}` {row.get('greek','')} — {row.get('english','')} (scope: {row.get('scope','')})"
            )
    else:
        for _, r in preparations_df.iterrows():
            lines.append(
                f"- `{r['prep_id']}` {r['greek']} — {r['english']} (scope: {r['scope']})"
            )
    lines.append("")

    lines.append("## (e) Rule for preparations vs residue nouns")
    lines.append(
        "- Deterministic rule: preparations are adjectival or process terms that modify a base substance; residue/product nouns (e.g., σποδός, τέφρα) remain parts/materials even if produced by a process."
    )
    lines.append("")
    lines.append("## (f) Downstream consistency changes")
    lines.append(
        "- `κεκαυμένος` and `ἀφέψημα` remain preparations (not parts)."
    )
    lines.append(
        "- Linking for preparations will be emitted as `entry_preparations.csv` (import-only), analogous to `lemma_ids` → `entry_lemmata`."
    )
    lines.append("")

    diff_report_md_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    # QC report for parts coverage only (exact normalized token matches).
    parts_norm_to_ids: dict[str, list[str]] = defaultdict(list)
    for _, r in parts_df.iterrows():
        parts_norm_to_ids[normalize_greek_for_match(str(r["greek"]))].append(str(r["part_id"]))

    token_counts: Counter[str] = Counter()
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        cols = relevant_text_columns(df.columns)
        for col in cols:
            for value in df[col].dropna().astype(str):
                for token in iter_greek_tokens(value):
                    token_norm = normalize_greek_for_match(token)
                    if token_norm in parts_norm_to_ids:
                        token_counts[token_norm] += 1

    qc_lines: list[str] = []
    qc_lines.append("# parts.csv QC report")
    qc_lines.append("")
    qc_lines.append(f"- Generated: `{utc_now}`")
    qc_lines.append(f"- Workbook: `{xlsx_path.name}`")
    qc_lines.append(f"- Wrote `parts.csv` rows: **{len(parts_df)}**")
    qc_lines.append("")
    qc_lines.append("## Starter parts coverage (observed token counts)")
    if token_counts:
        for token_norm, count in token_counts.most_common():
            ids = ", ".join(parts_norm_to_ids[token_norm])
            greek_display = parts_df.loc[
                parts_df["part_id"] == parts_norm_to_ids[token_norm][0], "greek"
            ].iloc[0]
            qc_lines.append(f"- `{greek_display}` ({ids}): {count}")
    else:
        qc_lines.append("- _(No part-token matches found in scanned columns.)_")
    qc_lines.append("")

    parts_qc_md_path.write_text("\n".join(qc_lines), encoding="utf-8", newline="\n")

    print(f"Wrote {parts_csv_path} ({len(parts_df)} rows)")
    print(f"Wrote {preparations_csv_path} ({len(preparations_df)} rows)")
    print(f"Wrote {preparations_review_csv_path} ({len(review_rows)} rows)")
    print(f"Wrote {diff_report_md_path}")
    print(f"Wrote {parts_qc_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


EXPECTED_SHEETS = ["SMT", "Alim.Fac", "Oribasius CM 15", "Aetius I-II"]


def source_code_for_sheet(sheet: str) -> str:
    return {
        "SMT": "GAL_SMT",
        "Alim.Fac": "GAL_ALIM",
        "Oribasius CM 15": "ORIB_CM",
        "Aetius I-II": "AET_LM",
    }[sheet]


def find_workbook_path(workbench: Path) -> Path:
    candidates = [
        workbench / "simples.xlsx",
        workbench / "Simples.xlsx",
        workbench / "simples.xlsm",
        workbench / "Simples.xlsm",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Missing input workbook; tried: " + ", ".join(str(p) for p in candidates)
    )


def to_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def to_intish_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, int):
        return str(value)
    s = str(value).strip()
    return s


def single_line_text(text: str, *, newline: str = "\\n") -> str:
    """
    Convert potentially multi-line cell text into a single physical line for CSV output.
    Keeps paragraph boundaries by replacing newlines with a literal `\\n` token.
    """
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\n" not in text:
        return text
    parts = [p.strip() for p in text.split("\n")]
    parts = [p for p in parts if p != ""]
    return newline.join(parts)


def normalize_greek_for_match(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    # Remove accents/breathings, but preserve iota subscript (U+0345) per spec.
    text = "".join(ch for ch in text if not unicodedata.combining(ch) or ch == "\u0345")
    return unicodedata.normalize("NFC", text)


_PROOIMION_NORM = normalize_greek_for_match("προοίμιον")


def build_ref(row: pd.Series, *, row_index_1_based: int) -> str:
    """
    Build the hierarchical `ref` field from either:
    - legacy column names (Book_Arabic/Chapter_Arabic/Section_Arabic), or
    - current `simples.xlsx` schema (book_no/chapter_no/section_no/subsection_no).
    """
    if "Book_Arabic" in row.index or "Chapter_Arabic" in row.index or "Section_Arabic" in row.index:
        book = to_intish_str(row.get("Book_Arabic"))
        chapter = to_intish_str(row.get("Chapter_Arabic"))
        section = to_intish_str(row.get("Section_Arabic"))
        parts = [p for p in [book, chapter, section] if p != ""]
        return ".".join(parts) if parts else f"row{row_index_1_based}"

    book = to_intish_str(row.get("book_no"))
    chapter = to_intish_str(row.get("chapter_no"))
    section = to_intish_str(row.get("section_no"))
    subsection = to_intish_str(row.get("subsection_no"))

    if chapter.lower() == "pr":
        return f"{book}.prooimion" if book else "prooimion"

    title_gr = to_str(row.get("section_gr")).strip() or to_str(row.get("chapter_gr")).strip()
    if (
        book
        and chapter in {"0", ""}
        and section in {"0", ""}
        and normalize_greek_for_match(title_gr) == _PROOIMION_NORM
    ):
        return f"{book}.prooimion"

    parts = [p for p in [book, chapter, section, subsection] if p != ""]
    return ".".join(parts) if parts else f"row{row_index_1_based}"


def dedupe_entry_ids(entry_ids: list[str]) -> list[str]:
    """
    Match `make_entries.py` behavior: if an entry_id appears N>1 times, suffix every
    occurrence with `~1..~N` in first-seen order.
    """
    counts = Counter(entry_ids)
    if not any(v > 1 for v in counts.values()):
        return entry_ids

    seen: dict[str, int] = defaultdict(int)
    out: list[str] = []
    for eid in entry_ids:
        seen[eid] += 1
        if counts[eid] > 1:
            out.append(f"{eid}~{seen[eid]}")
        else:
            out.append(eid)
    return out


_GREEK_PERI_RE = re.compile(r"^\\s*(?:Περὶ|περὶ|περι)\\s+(.*)\\s*$", re.UNICODE)


def literal_chapter_title_en(chapter_title_gr: str) -> str:
    if not chapter_title_gr.strip():
        return ""
    if normalize_greek_for_match(chapter_title_gr) == _PROOIMION_NORM:
        return "Prooimion"
    m = _GREEK_PERI_RE.match(chapter_title_gr)
    if not m:
        return ""
    remainder = m.group(1).strip()
    return f"On {remainder}" if remainder else ""

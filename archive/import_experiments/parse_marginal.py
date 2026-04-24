#!/usr/bin/env python3
import re, csv, argparse, sys

MARK_CHARS = set("0123456789.:,t")
EN_DASH_SPLIT_RE = re.compile(r"\s*–\s*")
TERMINAL_PUNCT = {"."}

CONTINUATION_STARTERS = {
    "καὶ",
    "κατὰ",
    "διὸ",
    "ταύτας",
}

def split_reference(ref: str) -> tuple[str, str, str, str, str]:
    ref = ref.strip()

    if ":" in ref:
        left, right = ref.split(":", 1)
        left_parts = left.split(".")
        book = left_parts[0] if len(left_parts) >= 1 else ""
        chapter = left_parts[1] if len(left_parts) >= 2 else ""

        right_parts = right.split(".")
        section = right_parts[0] if len(right_parts) >= 1 else ""
        if len(right_parts) >= 3:
            subsection = ".".join(right_parts[1:-1])
            line = right_parts[-1]
        elif len(right_parts) == 2:
            subsection = ""
            line = right_parts[1]
        else:
            subsection = ""
            line = ""
        return book, chapter, section, subsection, line

    parts = ref.split(".")
    book = parts[0] if len(parts) >= 1 else ""
    chapter = parts[1] if len(parts) >= 2 else ""
    if len(parts) >= 5:
        section = parts[2]
        subsection = ".".join(parts[3:-1])
        line = parts[-1]
    elif len(parts) == 4:
        section = parts[2]
        subsection = ""
        line = parts[3]
    elif len(parts) == 3:
        section = parts[2]
        subsection = ""
        line = ""
    else:
        section = ""
        subsection = ""
        line = ""
    return book, chapter, section, subsection, line

def is_marker_line(line: str) -> str | None:
    s = line.strip()
    if not s:
        return None
    if s[0] not in "0123456789" or s[-1] not in "0123456789":
        return None
    if "." not in s:
        return None
    if any(ch not in MARK_CHARS for ch in s):
        return None
    return s

def is_title_marker(ref: str) -> bool:
    return ".t." in ref

def normalise_ws(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def starts_with_letter(text: str) -> bool:
    saw_nonspace = False
    for ch in text:
        if ch.isspace():
            continue
        saw_nonspace = True
        if ch.isalpha():
            return True
        if ch == "<":
            return any(c.isalpha() for c in text)
        return False
    return False if saw_nonspace else False

def append_fragment(current: str, fragment: str) -> str:
    fragment = fragment.strip()
    if not fragment:
        return current
    if not current:
        return fragment
    stripped = current.rstrip()
    if stripped.endswith("-") and starts_with_letter(fragment):
        return stripped[:-1] + fragment.lstrip()
    return stripped + " " + fragment

def ends_with_terminal_punct(text: str) -> bool:
    s = text.rstrip()
    return bool(s) and s[-1] in TERMINAL_PUNCT

def split_at_preferred_boundary(text: str) -> tuple[str, str] | None:
    def first_word(s: str) -> str | None:
        s = s.lstrip()
        while s.startswith("<"):
            end = s.find(">")
            if end == -1:
                break
            s = s[end + 1 :].lstrip()
        m = re.search(r"[A-Za-zΑ-Ωα-ωἀ-῾]+", s)
        return m.group(0) if m else None

    candidates: list[tuple[str, bool, bool]] = [
        ("–", False, False),  # boundary, include boundary in prefix, require 2+ spaces after
        (".", True, False),
        ("·", True, True),    # only treat as entry boundary when written like "·  ..."
        (":", True, True),    # only treat as entry boundary when written like ":  ..."
    ]

    for boundary, include_in_prefix, require_double_space in candidates:
        if boundary == ".":
            for m in re.finditer(r"\.", text):
                if m.start() == 0:
                    continue
                if not text[m.start() - 1].isalpha():
                    continue
                if m.end() >= len(text) or text[m.end()] != " ":
                    continue
                prefix = text[: m.start() + (1 if include_in_prefix else 0)]
                remainder = text[m.end() :]
                if not starts_with_letter(remainder):
                    continue
                fw = first_word(remainder)
                if fw and fw in CONTINUATION_STARTERS:
                    continue
                return prefix, remainder
            continue

        if require_double_space:
            m = re.search(re.escape(boundary) + r"\s{2,}", text)
            if not m:
                continue
            cut = m.start() + (1 if include_in_prefix else 0)
            prefix = text[:cut]
            remainder = text[m.end() :]
        else:
            i = text.find(boundary)
            if i == -1:
                continue
            prefix = text[: i + (1 if include_in_prefix else 0)]
            remainder = text[i + 1 :]

        if starts_with_letter(remainder):
            fw = first_word(remainder)
            if fw and fw in CONTINUATION_STARTERS:
                continue
            return prefix, remainder
    return None

def parse(text: str):
    rows: list[tuple[str, str]] = []

    current_marker: str | None = None
    pending_split_ref: str | None = None
    pending_start = False

    current_entry_ref: str | None = None
    current_entry = ""

    def flush_entry():
        nonlocal current_entry_ref, current_entry
        if current_entry_ref is None:
            current_entry = ""
            return
        contents = normalise_ws(current_entry)
        if contents:
            rows.append((current_entry_ref, contents))
        current_entry_ref = None
        current_entry = ""

    def start_entry(ref: str | None):
        nonlocal current_entry_ref
        if ref is None:
            return
        current_entry_ref = ref

    def process_text(text_line: str):
        nonlocal current_entry, pending_start
        parts = EN_DASH_SPLIT_RE.split(text_line)
        for i, part in enumerate(parts):
            part = part.strip()
            if i == 0:
                if part:
                    current_entry = append_fragment(current_entry, part)
                continue

            flush_entry()
            if part:
                start_entry(current_marker)
                current_entry = append_fragment(current_entry, part)
            else:
                pending_start = True

    for raw_line in text.splitlines():
        if raw_line.startswith("Book "):
            continue

        marker = is_marker_line(raw_line)
        if marker is not None:
            if is_title_marker(marker):
                flush_entry()
                current_marker = None
                pending_split_ref = None
                pending_start = False
                continue

            current_marker = marker
            if current_entry_ref is not None:
                if ends_with_terminal_punct(current_entry):
                    flush_entry()
                    pending_split_ref = None
                    pending_start = True
                else:
                    pending_split_ref = marker
            else:
                pending_start = True
            continue

        line = raw_line.strip("\n")
        if not line.strip():
            continue

        if pending_split_ref is not None and current_entry_ref is not None:
            split = split_at_preferred_boundary(line)
            if split is None:
                if ends_with_terminal_punct(current_entry) and starts_with_letter(line):
                    flush_entry()
                    current_entry_ref = pending_split_ref
                    pending_split_ref = None
                    start_entry(current_entry_ref)
                    process_text(line)
                else:
                    current_entry = append_fragment(current_entry, line)
                continue

            prefix, remainder = split
            if prefix.strip():
                current_entry = append_fragment(current_entry, prefix)
            flush_entry()

            current_entry_ref = pending_split_ref
            pending_split_ref = None
            pending_start = True if remainder.strip() else pending_start

            if remainder.strip():
                start_entry(current_entry_ref)
                process_text(remainder)
            continue

        if pending_start and current_entry_ref is None:
            start_entry(current_marker)
            pending_start = False

        if current_entry_ref is None:
            continue

        process_text(line)

    flush_entry()
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile", nargs="?", help="Input text file (default stdin)")
    ap.add_argument("-o", "--outfile", help="Output CSV file (default stdout)")
    ap.add_argument("--split-reference", action="store_true", help="Write reference as book,chapter,section,subsection,line columns")
    args = ap.parse_args()

    raw = open(args.infile, "r", encoding="utf-8").read() if args.infile else sys.stdin.read()
    rows = parse(raw)

    out = open(args.outfile, "w", encoding="utf-8", newline="") if args.outfile else sys.stdout
    w = csv.writer(out)
    if args.split_reference:
        w.writerow(["book", "chapter", "section", "subsection", "line", "contents"])
        for ref, contents in rows:
            book, chapter, section, subsection, line = split_reference(ref)
            w.writerow([book, chapter, section, subsection, line, contents])
    else:
        w.writerow(["reference", "contents"])
        w.writerows(rows)
    if args.outfile:
        out.close()

if __name__ == "__main__":
    main()

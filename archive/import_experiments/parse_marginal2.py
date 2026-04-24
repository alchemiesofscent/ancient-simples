#!/usr/bin/env python3
import re, csv, argparse, sys

MARK_RE = re.compile(r"^[^\S\r\n]*(\d+\.\d+:\d+\.\d+\.\d+)[^\S\r\n]*$", re.MULTILINE)
INLINE_MARK_RE = re.compile(r"\b\d+\.\d+:\d+\.\d+\.\d+\b")

def entry_key(ref: str):
    head, tail = ref.rsplit(".", 1)
    return head, int(tail)

def squash_ws(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n+", " ", s)
    return s.strip()

def dehyphenate(s: str) -> str:
    # join linebreak hyphenation only when next char is a letter (not a digit marker)
    return re.sub(r"(\w)-\s*(?=\n\s*\w)", r"\1", s)

def start_after_punct(span: str) -> str:
    # your priority: full stop > colon > comma (include Greek ano teleia · as “full stop”)
    for p in [".", "·", ":", ","]:
        i = span.find(p)
        if i != -1:
            return span[i + 1 :].strip()
    return span.strip()

def build_entry_units(text: str):
    ms = list(MARK_RE.finditer(text))
    units = []
    cur_ref, cur_parts = None, []

    for i, m in enumerate(ms):
        ref = m.group(1)
        _, line_no = entry_key(ref)
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        span = text[start:end]

        if line_no == 1:
            if cur_ref is not None:
                units.append((cur_ref, "".join(cur_parts)))
            cur_ref, cur_parts = ref, [span]
        else:
            if cur_ref is None:
                cur_ref, cur_parts = ref, [span]
            else:
                cur_parts.append(span)

    if cur_ref is not None:
        units.append((cur_ref, "".join(cur_parts)))
    return units

def parse(text: str):
    text = dehyphenate(text)
    rows = []

    for ref, raw_span in build_entry_units(text):
        # safety: remove any marker strings that leaked into span
        raw_span = INLINE_MARK_RE.sub(" ", raw_span)
        span = squash_ws(raw_span)

        # split on em dash; each dash starts a new entry under same reference
        parts = [p.strip() for p in span.split("–")]

        # heuristic: if the first segment starts with lowercase (continuation), trim to after punct
        first = parts[0]
        if first and first[:1].islower():
            first = start_after_punct(first)

        if first:
            rows.append((ref, first))

        for seg in parts[1:]:
            seg = squash_ws(seg)
            if seg:
                rows.append((ref, seg))

    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile", nargs="?", help="Input text file (default: stdin)")
    ap.add_argument("-o", "--outfile", help="Output CSV file (default: stdout)")
    args = ap.parse_args()

    raw = open(args.infile, "r", encoding="utf-8").read() if args.infile else sys.stdin.read()
    rows = parse(raw)

    out = open(args.outfile, "w", encoding="utf-8", newline="") if args.outfile else sys.stdout
    w = csv.writer(out)
    w.writerow(["reference", "contents"])
    w.writerows(rows)
    if args.outfile:
        out.close()

if __name__ == "__main__":
    main()

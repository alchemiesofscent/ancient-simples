#!/usr/bin/env python3
"""
Audit ref-sequence integrity in data-workbench/entries.csv.

Read-only. Emits a markdown report to data-workbench/entries_refs_audit.md
summarizing per-source gaps, depth inconsistencies, CSV-order drift,
duplicates, and cross-references with entries_qc.md.

Always exits 0; findings live in the report.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


# "prooimion" (preamble) sits before chapter 1; encode as 0 for sort/gap math.
PROOIMION_TOKEN = "prooimion"
PROOIMION_SENTINEL = 0


def parse_ref(ref: str) -> tuple[int, ...] | None:
    """Parse a hierarchical ref like "6.1.5" or "6.prooimion" into a tuple of ints.

    Returns None if any component fails to parse.
    """
    if not ref:
        return None
    parts: list[int] = []
    for component in ref.split("."):
        c = component.strip()
        if c.lower() == PROOIMION_TOKEN:
            parts.append(PROOIMION_SENTINEL)
        else:
            try:
                parts.append(int(c))
            except ValueError:
                return None
    return tuple(parts)


def format_ref(tup: tuple[int, ...], is_prooimion_position: set[int] | None = None) -> str:
    """Format a numeric tuple back as a ref string (best-effort, numeric only)."""
    return ".".join(str(x) for x in tup)


def gaps_in_sequence(values: list[int]) -> list[tuple[int, int]]:
    """Given a sorted list of ints, return list of (gap_start, gap_end) inclusive.

    Only reports gaps *within* the observed range (does not flag missing values
    below the minimum or above the maximum).
    """
    if not values:
        return []
    result: list[tuple[int, int]] = []
    prev = values[0]
    for v in values[1:]:
        if v > prev + 1:
            result.append((prev + 1, v - 1))
        prev = v
    return result


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"
    entries_path = workbench / "entries.csv"
    qc_path = workbench / "entries_qc.md"
    report_path = workbench / "entries_refs_audit.md"

    if not entries_path.exists():
        print(f"ERROR: missing {entries_path}")
        return 2

    with entries_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Collect per-source refs in CSV order.
    #   source -> list of (csv_row_index, raw_ref_str, parsed_tuple | None, entry_id)
    per_source: dict[str, list[tuple[int, str, tuple[int, ...] | None, str]]] = defaultdict(list)
    for i, r in enumerate(rows):
        source = (r.get("source") or "").strip()
        ref = (r.get("ref") or "").strip()
        entry_id = (r.get("entry_id") or "").strip()
        parsed = parse_ref(ref)
        per_source[source].append((i, ref, parsed, entry_id))

    qc_text = qc_path.read_text(encoding="utf-8") if qc_path.exists() else ""

    # Build the report.
    lines: list[str] = []
    lines.append("# entries.csv ref-sequence audit")
    lines.append("")
    lines.append(f"- Input: `data-workbench/entries.csv`")
    lines.append(f"- Total rows: **{len(rows)}**")
    lines.append(f"- Sources: {', '.join(sorted(per_source.keys()))}")
    lines.append("")
    lines.append("This audit checks: ref uniqueness per source, sequential numbering")
    lines.append("within each book/chapter group, book-level contiguity, ref-depth")
    lines.append("consistency, and CSV-order drift. It cross-references")
    lines.append("`entries_qc.md` to see whether any detected gaps are documented.")
    lines.append("")

    # --- Executive summary (filled in after per-source analysis) ---
    summary_placeholder_index = len(lines)
    lines.append("## Summary")
    lines.append("")
    lines.append("_(populated below)_")
    lines.append("")

    summary_counts: dict[str, dict[str, int]] = {}

    for source in sorted(per_source.keys()):
        entries = per_source[source]
        lines.append(f"## {source}")
        lines.append("")
        lines.append(f"- Entries: **{len(entries)}**")

        # Unparseable refs
        unparseable = [(i, raw, eid) for (i, raw, parsed, eid) in entries if parsed is None]
        if unparseable:
            lines.append(f"- Unparseable refs: **{len(unparseable)}**")
            for i, raw, eid in unparseable[:10]:
                lines.append(f"  - row {i + 2} `{eid}` ref=`{raw}`")
            if len(unparseable) > 10:
                lines.append(f"  - … and {len(unparseable) - 10} more")
        parsed_entries = [(i, raw, parsed, eid) for (i, raw, parsed, eid) in entries if parsed is not None]

        # Duplicate refs within a source. These are EXPECTED when all sibling
        # entry_ids carry `~N` suffixes (the make_entries.py convention for
        # multiple xlsx rows sharing the same structural ref). Flag separately
        # any dupes where entry_ids lack the suffix — those are real errors.
        ref_to_entry_ids: dict[str, list[str]] = defaultdict(list)
        for (_, raw, _, eid) in parsed_entries:
            ref_to_entry_ids[raw].append(eid)
        dupes = {k: v for k, v in ref_to_entry_ids.items() if len(v) > 1}
        unresolved_dupes: dict[str, list[str]] = {}
        resolved_dupes: dict[str, list[str]] = {}
        for k, eids in dupes.items():
            if all("~" in e for e in eids):
                resolved_dupes[k] = eids
            else:
                unresolved_dupes[k] = eids
        if resolved_dupes:
            lines.append(
                f"- Duplicate refs resolved via `~N` entry_id suffix (expected): **{len(resolved_dupes)}**"
            )
            for k, eids in sorted(resolved_dupes.items())[:10]:
                lines.append(f"  - `{k}` ×{len(eids)}")
            if len(resolved_dupes) > 10:
                lines.append(f"  - … and {len(resolved_dupes) - 10} more")
        if unresolved_dupes:
            lines.append(
                f"- Duplicate refs WITHOUT `~N` suffix (error): **{len(unresolved_dupes)}**"
            )
            for k, eids in sorted(unresolved_dupes.items())[:20]:
                lines.append(f"  - `{k}` ×{len(eids)}: {eids}")
        if not dupes:
            lines.append("- Duplicate refs: none")

        # Depth distribution
        depth_counts = Counter(len(parsed) for (_, _, parsed, _) in parsed_entries)
        modal_depth = depth_counts.most_common(1)[0][0] if depth_counts else 0
        depth_str = ", ".join(f"{d}-tuple: {c}" for d, c in sorted(depth_counts.items()))
        lines.append(f"- Ref depth distribution: {depth_str}")
        lines.append(f"- Modal depth: **{modal_depth}**")

        # Flag rows whose depth != modal depth
        off_modal = [
            (i, raw, parsed, eid)
            for (i, raw, parsed, eid) in parsed_entries
            if len(parsed) != modal_depth
        ]
        if off_modal:
            lines.append(f"- Off-modal-depth rows: **{len(off_modal)}**")
            for i, raw, parsed, eid in off_modal[:15]:
                lines.append(f"  - row {i + 2} `{eid}` ref=`{raw}` (depth {len(parsed)})")
            if len(off_modal) > 15:
                lines.append(f"  - … and {len(off_modal) - 15} more")

        # CSV order vs natural (sorted) order
        csv_order_tuples = [parsed for (_, _, parsed, _) in parsed_entries]
        sorted_tuples = sorted(csv_order_tuples)
        in_natural_order = csv_order_tuples == sorted_tuples
        lines.append(
            f"- CSV rows in natural ref order: **{'yes' if in_natural_order else 'no'}**"
        )
        if not in_natural_order:
            # Report first few positions where CSV order diverges from sorted order.
            drift_examples: list[str] = []
            for idx, (csv_tup, sorted_tup) in enumerate(zip(csv_order_tuples, sorted_tuples)):
                if csv_tup != sorted_tup:
                    # Find the original row index for this csv_order position.
                    orig_row_index = parsed_entries[idx][0]
                    drift_examples.append(
                        f"position {idx + 1} (csv row {orig_row_index + 2}): "
                        f"csv has `{format_ref(csv_tup)}`, expected `{format_ref(sorted_tup)}`"
                    )
                    if len(drift_examples) >= 10:
                        break
            if drift_examples:
                lines.append("  - First divergences:")
                for d in drift_examples:
                    lines.append(f"    - {d}")

        # --- Gap analysis: group by (all components except last), analyze last component ---
        # group_key -> list of last-component values (ints)
        # Also track which 0-values came from "prooimion" so we can distinguish
        # book-level preambles from literal `.0` sections (e.g. GAL_SMT-10.1.0).
        group_values: dict[tuple[int, ...], list[int]] = defaultdict(list)
        prooimion_zeros: set[tuple[tuple[int, ...], int]] = set()  # (prefix, last) for prooimion entries
        for (_, raw, parsed, _) in parsed_entries:
            if not parsed:
                continue
            prefix = parsed[:-1]
            last = parsed[-1]
            group_values[prefix].append(last)
            if last == 0 and PROOIMION_TOKEN in raw.lower():
                prooimion_zeros.add((prefix, last))

        # Flag groups whose only value is a literal-0 (not prooimion) — e.g. 10.1.0.
        literal_zero_groups: list[tuple[tuple[int, ...], str]] = []
        for prefix, values in sorted(group_values.items()):
            if set(values) == {0} and (prefix, 0) not in prooimion_zeros:
                # Find the raw ref for reporting.
                prefix_str = ".".join(str(x) for x in prefix)
                literal_zero_groups.append((prefix, f"{prefix_str}.0"))
        if literal_zero_groups:
            lines.append(
                f"- Literal `.0` sections (not `prooimion`): **{len(literal_zero_groups)}**"
            )
            for prefix, ref_str in literal_zero_groups:
                lines.append(f"  - `{ref_str}` (only entry under prefix `{'.'.join(str(x) for x in prefix)}`)")

        gap_groups: list[tuple[tuple[int, ...], list[tuple[int, int]], int, int, int]] = []
        for prefix, values in sorted(group_values.items()):
            values_sorted = sorted(values)
            gaps = gaps_in_sequence(values_sorted)
            if gaps:
                gap_groups.append((prefix, gaps, values_sorted[0], values_sorted[-1], len(values_sorted)))

        if gap_groups:
            lines.append(f"- Groups with internal gaps: **{len(gap_groups)}**")
            for prefix, gaps, lo, hi, count in gap_groups:
                prefix_str = ".".join(str(x) for x in prefix) if prefix else "(root)"
                gap_strs = ", ".join(
                    f"{g[0]}" if g[0] == g[1] else f"{g[0]}–{g[1]}" for g in gaps
                )
                lines.append(
                    f"  - prefix `{prefix_str}`: {count} values in {lo}..{hi}, missing {gap_strs}"
                )
        else:
            lines.append("- Groups with internal gaps: none")

        # Also note groups that do not start at 1 (potential leading gap).
        # A minimum of 0 is benign when it corresponds to a `prooimion` entry;
        # otherwise it's worth flagging as a literal `.0` section (already
        # reported separately).
        non_one_start: list[tuple[tuple[int, ...], int, int]] = []
        for prefix, values in sorted(group_values.items()):
            lo = min(values)
            hi = max(values)
            if lo == 0 and (prefix, 0) in prooimion_zeros:
                # prooimion precedes chapter 1; the rest of the sequence is
                # what we actually want to audit.
                non_zero = [v for v in values if v != 0]
                if not non_zero:
                    continue  # only prooimion in this group — expected
                lo = min(non_zero)
                hi = max(non_zero)
            if lo != 1:
                non_one_start.append((prefix, lo, hi))
        if non_one_start:
            lines.append(f"- Groups not starting at 1 (or 0 for prooimion): **{len(non_one_start)}**")
            for prefix, lo, hi in non_one_start[:30]:
                prefix_str = ".".join(str(x) for x in prefix) if prefix else "(root)"
                lines.append(f"  - prefix `{prefix_str}`: starts at {lo}, ends at {hi}")
            if len(non_one_start) > 30:
                lines.append(f"  - … and {len(non_one_start) - 30} more")
        else:
            lines.append("- Groups not starting at 1: none")

        # Book-level contiguity: for each first-component (book), check that the
        # set of second-components (chapters) is contiguous starting at 1
        # (or 0 for prooimion).
        book_chapters: dict[int, set[int]] = defaultdict(set)
        for (_, _, parsed, _) in parsed_entries:
            if len(parsed) >= 2:
                book_chapters[parsed[0]].add(parsed[1])
        book_issues: list[str] = []
        for book in sorted(book_chapters.keys()):
            chapters = sorted(book_chapters[book])
            # Drop prooimion (0) from "expected 1..N" analysis, but note its presence.
            real_chapters = [c for c in chapters if c != 0]
            if not real_chapters:
                continue
            lo, hi = real_chapters[0], real_chapters[-1]
            chapter_gaps = gaps_in_sequence(real_chapters)
            notes_bits: list[str] = []
            if lo > 1:
                notes_bits.append(f"starts at chapter {lo}")
            if chapter_gaps:
                gs = ", ".join(
                    f"{g[0]}" if g[0] == g[1] else f"{g[0]}–{g[1]}" for g in chapter_gaps
                )
                notes_bits.append(f"missing chapters {gs}")
            if notes_bits:
                book_issues.append(
                    f"book {book}: {len(real_chapters)} chapters in {lo}..{hi}; " + "; ".join(notes_bits)
                )
        if book_issues:
            lines.append(f"- Book-level chapter contiguity issues: **{len(book_issues)}**")
            for b in book_issues:
                lines.append(f"  - {b}")
        else:
            lines.append("- Book-level chapter contiguity issues: none")

        # Cross-reference with entries_qc.md: look for the full entry_id
        # (including source prefix) so we don't get substring false positives
        # like `1.10` matching within `15.1.10...`.
        if gap_groups and qc_text:
            gap_entry_ids_mentioned = 0
            for prefix, gaps, _, _, _ in gap_groups:
                prefix_str = ".".join(str(x) for x in prefix)
                for g_lo, g_hi in gaps:
                    for n in range(g_lo, g_hi + 1):
                        ref_part = f"{prefix_str}.{n}" if prefix_str else str(n)
                        candidate = f"{source}-{ref_part}"
                        if candidate in qc_text:
                            gap_entry_ids_mentioned += 1
            lines.append(
                f"- Gap entry_ids explicitly mentioned in `entries_qc.md`: **{gap_entry_ids_mentioned}**"
            )

        lines.append("")

        summary_counts[source] = {
            "entries": len(entries),
            "resolved_dupes": len(resolved_dupes),
            "unresolved_dupes": len(unresolved_dupes),
            "off_modal_depth": len(off_modal),
            "gap_groups": len(gap_groups),
            "non_one_start_groups": len(non_one_start),
            "book_issues": len(book_issues),
            "natural_order": 1 if in_natural_order else 0,
        }

    # Populate executive summary
    summary_lines: list[str] = []
    summary_lines.append("## Summary")
    summary_lines.append("")
    summary_lines.append(
        "| Source | Entries | `~N` dup refs | Bad dup refs | Off-modal depth | Gap groups | Non-1 starts | Book issues | Natural order |"
    )
    summary_lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|"
    )
    for source in sorted(summary_counts.keys()):
        s = summary_counts[source]
        summary_lines.append(
            f"| {source} | {s['entries']} | {s['resolved_dupes']} | {s['unresolved_dupes']} | "
            f"{s['off_modal_depth']} | {s['gap_groups']} | {s['non_one_start_groups']} | "
            f"{s['book_issues']} | {'yes' if s['natural_order'] else 'no'} |"
        )
    summary_lines.append("")
    summary_lines.append(
        "- **`~N` dup refs** — structural refs shared by multiple sibling entries "
        "(all resolved via `~1/~2/…` entry_id suffixes; expected/benign)."
    )
    summary_lines.append(
        "- **Bad dup refs** — a ref appears on multiple rows but the entry_ids "
        "are not all `~N`-suffixed (indicates a real collision)."
    )
    summary_lines.append(
        "- **Off-modal depth** — rows whose ref component count differs from "
        "the source's majority depth (often `prooimion` or a structural quirk)."
    )
    summary_lines.append(
        "- **Gap groups** — prefix groups with missing last-component values "
        "between observed min and max."
    )
    summary_lines.append(
        "- **Non-1 starts** — prefix groups whose smallest last-component is "
        "not 1 (possible leading gap or offset numbering convention)."
    )
    summary_lines.append(
        "- **Book issues** — book-level chapter-contiguity issues."
    )
    summary_lines.append(
        "- **Natural order** — whether CSV row order matches natural ref order."
    )
    summary_lines.append("")
    summary_lines.append(
        "> Note: `entries_qc.md` (the output of `data-workbench/make_entries.py`) "
        "only records totals, skipped-row counts, and a random 10-row sample. It "
        "does not enumerate gaps — so any non-zero gap/book-issue count below is "
        "currently **undocumented** in that file unless otherwise noted."
    )
    summary_lines.append("")

    # Replace placeholder summary block
    lines[summary_placeholder_index : summary_placeholder_index + 4] = summary_lines

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

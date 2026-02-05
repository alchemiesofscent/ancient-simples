#!/usr/bin/env python3

import argparse
import difflib
import json
from dataclasses import dataclass
from pathlib import Path


def _load_ids(ids_file: Path) -> list[str]:
    ids = []
    for line in ids_file.read_text(encoding="utf-8", errors="replace").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        ids.append(value)
    return ids


def _load_obj(results_dir: Path, source_id: str) -> dict:
    fp = results_dir / f"{source_id}.json"
    if not fp.exists():
        raise FileNotFoundError(fp)
    return json.loads(fp.read_text(encoding="utf-8"))


def _norm_str(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _sig_applies_to(applies_to: dict) -> tuple:
    if not isinstance(applies_to, dict):
        return ("UNSPECIFIED", None, None, None)
    return (
        applies_to.get("kind"),
        _norm_str(applies_to.get("lemma_normalized")),
        _norm_str(applies_to.get("substance_lemma_normalized")),
        _norm_str(applies_to.get("part_lemma_normalized")),
    )


def _term_sig(t: dict) -> tuple:
    return (
        t.get("label"),
        _norm_str(t.get("lemma_normalized")),
        _norm_str(t.get("substance_lemma_normalized")),
        _norm_str(t.get("part_lemma_normalized")),
        _norm_str(t.get("head_lemma_normalized")),
        _norm_str(t.get("variant_place_lemma_normalized")),
        _sig_applies_to(t.get("applies_to") or {}),
    )


def _quality_sig(q: dict) -> tuple:
    return (
        q.get("axis"),
        q.get("degree"),
        q.get("intensity"),
        q.get("hedge"),
        _norm_str(q.get("variant_place_lemma_normalized")),
        _sig_applies_to(q.get("applies_to") or {}),
    )


def _cmp_key(value):
    # Total ordering for mixed JSON-ish types (keeps None distinct from "").
    if value is None:
        return (0, None)
    if isinstance(value, bool):
        return (1, value)
    if isinstance(value, int):
        return (2, value)
    if isinstance(value, float):
        return (3, value)
    if isinstance(value, str):
        return (4, value)
    if isinstance(value, tuple) or isinstance(value, list):
        return (5, tuple(_cmp_key(v) for v in value))
    if isinstance(value, dict):
        return (6, tuple((k, _cmp_key(v)) for k, v in sorted(value.items())))
    return (7, str(value))


def _canonical_semantic(obj: dict) -> dict:
    terms = list({_term_sig(t) for t in obj.get("terms", [])})
    qualities = list({_quality_sig(q) for q in obj.get("qualities", [])})
    terms.sort(key=_cmp_key)
    qualities.sort(key=_cmp_key)
    return {
        "source_id": obj.get("source_id"),
        "terms_semantic": terms,
        "qualities_semantic": qualities,
    }


@dataclass
class DiffSummary:
    added_terms: int = 0
    removed_terms: int = 0
    added_qualities: int = 0
    removed_qualities: int = 0


def _diff_sets(a: set, b: set) -> tuple[set, set]:
    return (b - a, a - b)


def _unified_diff(a_obj: dict, b_obj: dict, title_a: str, title_b: str) -> str:
    a_txt = json.dumps(a_obj, ensure_ascii=False, indent=2, sort_keys=True).splitlines(True)
    b_txt = json.dumps(b_obj, ensure_ascii=False, indent=2, sort_keys=True).splitlines(True)
    return "".join(
        difflib.unified_diff(
            a_txt,
            b_txt,
            fromfile=title_a,
            tofile=title_b,
            lineterm="",
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare two extraction runs semantically (ignoring confidence/evidence) and write a report."
    )
    ap.add_argument("--run-a", required=True, help="Results dir A (contains <source_id>.json).")
    ap.add_argument("--run-b", required=True, help="Results dir B (contains <source_id>.json).")
    ap.add_argument("--ids-file", required=True, help="List of SOURCE_IDs to compare.")
    ap.add_argument("--out-report", required=True, help="Write a Markdown report to this path.")
    ap.add_argument("--out-diffs-dir", required=True, help="Write per-entry unified diffs here.")
    ap.add_argument("--label-a", default="run_a", help="Label for run A.")
    ap.add_argument("--label-b", default="run_b", help="Label for run B.")
    args = ap.parse_args()

    run_a = Path(args.run_a)
    run_b = Path(args.run_b)
    ids_file = Path(args.ids_file)
    out_report = Path(args.out_report)
    out_diffs_dir = Path(args.out_diffs_dir)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_diffs_dir.mkdir(parents=True, exist_ok=True)

    ids = _load_ids(ids_file)
    if not ids:
        raise SystemExit(f"No ids found in {ids_file}")

    total = 0
    changed = 0
    summary = DiffSummary()
    per_entry = []

    for source_id in ids:
        total += 1
        a_raw = _load_obj(run_a, source_id)
        b_raw = _load_obj(run_b, source_id)

        a = _canonical_semantic(a_raw)
        b = _canonical_semantic(b_raw)

        a_terms = set(map(tuple, a["terms_semantic"]))
        b_terms = set(map(tuple, b["terms_semantic"]))
        a_quals = set(map(tuple, a["qualities_semantic"]))
        b_quals = set(map(tuple, b["qualities_semantic"]))

        added_terms, removed_terms = _diff_sets(a_terms, b_terms)
        added_quals, removed_quals = _diff_sets(a_quals, b_quals)

        if added_terms or removed_terms or added_quals or removed_quals:
            changed += 1
            summary.added_terms += len(added_terms)
            summary.removed_terms += len(removed_terms)
            summary.added_qualities += len(added_quals)
            summary.removed_qualities += len(removed_quals)

            # Per-entry diff of semantic canonical JSON only.
            diff_text = _unified_diff(a, b, args.label_a, args.label_b)
            (out_diffs_dir / f"{source_id}.diff").write_text(diff_text + "\n", encoding="utf-8")

        per_entry.append(
            {
                "source_id": source_id,
                "term_added": len(added_terms),
                "term_removed": len(removed_terms),
                "qual_added": len(added_quals),
                "qual_removed": len(removed_quals),
            }
        )

    lines = []
    lines.append(f"# Extraction run comparison: {args.label_a} vs {args.label_b}\n")
    lines.append(f"- Entries compared: {total}\n")
    lines.append(f"- Entries with semantic changes: {changed}\n")
    lines.append(
        f"- Term changes (added/removed): {summary.added_terms}/{summary.removed_terms}\n"
    )
    lines.append(
        f"- Quality changes (added/removed): {summary.added_qualities}/{summary.removed_qualities}\n"
    )
    lines.append("\n## Per-entry counts\n")
    lines.append("| source_id | +terms | -terms | +qualities | -qualities |\n")
    lines.append("|---|---:|---:|---:|---:|\n")
    for row in per_entry:
        lines.append(
            f"| {row['source_id']} | {row['term_added']} | {row['term_removed']} | {row['qual_added']} | {row['qual_removed']} |\n"
        )

    out_report.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote report: {out_report}")
    print(f"Wrote diffs:  {out_diffs_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

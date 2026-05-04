#!/usr/bin/env python3
"""Build deterministic name-relation pilot candidates for simples review."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_PATH = REPO_ROOT / "packages"
if str(PACKAGES_PATH) not in sys.path:
    sys.path.insert(0, str(PACKAGES_PATH))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_simples_registry import (
    DEFAULT_CONFIG,
    DEFAULT_OUTDIR,
    author_group_lookup,
    compact,
    load_config,
    load_entries,
    repo_path,
    source_code,
)


DEFAULT_REGISTRY_OCCURRENCES = DEFAULT_OUTDIR / "simple_term_occurrences_v0.csv"
RELATION_TYPES = [
    "synonym",
    "variant",
    "regional_name",
    "foreign_name",
    "place_qualified_variant",
    "part_or_product",
    "mistaken_identification",
    "related_but_not_synonymous",
    "uncertain",
    "unreviewed",
]

TRIGGER_PATTERNS = [
    ("heading_eta", re.compile(r"\s[ἤἢη]\s")),
    ("heading_semicolon", re.compile(r";")),
    ("heading_hoi_de", re.compile(r"ο[ἱι]\s+δ[ὲε]")),
    ("body_kaleitai", re.compile(r"καλε[ῖι]ται|καλο[ῦυ]σι|καλο[ύυ]μεν")),
    ("body_legetai", re.compile(r"λ[έέε]γεται|λεγ[όόο]μεν|λ[έέε]γουσι")),
    ("body_some_call", re.compile(r"τιν[ὲε]ς|ο[ἱι]\s+δ[ὲε]")),
    ("body_romans", re.compile(r"[Ῥρ]ωμα[ῖι]οι|λατ[ῖι]νοι")),
]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def load_occurrences(path: Path) -> dict[str, list[dict[str, str]]]:
    by_entry: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            by_entry[row["entry_id"]].append(row)
    return by_entry


def find_trigger(entry: dict[str, str]) -> tuple[str, str, str]:
    title = compact(entry.get("chapter_title_gr"))
    greek = compact(entry.get("greek"))
    for name, pattern in TRIGGER_PATTERNS:
        if title and pattern.search(title):
            return name, pattern.pattern, title
    for name, pattern in TRIGGER_PATTERNS:
        match = pattern.search(greek)
        if match:
            start = max(0, match.start() - 90)
            end = min(len(greek), match.end() + 160)
            return name, pattern.pattern, greek[start:end]
    return "", "", ""


def unique_terms(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    terms: list[dict[str, str]] = []
    for row in rows:
        key = compact(row.get("term_key"))
        if key and key not in seen:
            seen.add(key)
            terms.append(row)
    return terms


def choose_sample(entries: dict[str, dict[str, str]], by_entry: dict[str, list[dict[str, str]]], source_to_author: dict[str, str], per_author: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry_id, rows in by_entry.items():
        entry = entries.get(entry_id)
        if not entry:
            continue
        source = source_code(entry_id)
        author = source_to_author.get(source, source)
        trigger_name, trigger_pattern, evidence = find_trigger(entry)
        terms = unique_terms(rows)
        grouped[author].append(
            {
                "entry_id": entry_id,
                "entry": entry,
                "author_group": author,
                "text_source": source,
                "trigger_name": trigger_name,
                "trigger_pattern": trigger_pattern,
                "evidence": evidence,
                "terms": terms,
            }
        )

    sample: list[dict[str, Any]] = []
    for author in sorted(grouped):
        entries_for_author = grouped[author]
        triggered = [
            item for item in entries_for_author
            if item["trigger_name"] and len(item["terms"]) >= 2
        ]
        controls = [
            item for item in entries_for_author
            if not item["trigger_name"] and item["terms"]
        ]
        triggered.sort(key=lambda item: (item["text_source"], item["entry_id"]))
        controls.sort(key=lambda item: (item["text_source"], item["entry_id"]))
        control_count = min(4, max(0, per_author // 5))
        chosen = triggered[: max(0, per_author - control_count)] + controls[:control_count]
        if len(chosen) < per_author:
            chosen_ids = {item["entry_id"] for item in chosen}
            fillers = [
                item for item in entries_for_author
                if item["entry_id"] not in chosen_ids and item["terms"]
            ]
            fillers.sort(key=lambda item: (item["text_source"], item["entry_id"]))
            chosen.extend(fillers[: per_author - len(chosen)])
        sample.extend(chosen[:per_author])
    return sample


def relation_hint(left: dict[str, str], right: dict[str, str]) -> str:
    left_head = compact(left.get("head_lemma_normalized"))
    right_head = compact(right.get("head_lemma_normalized"))
    left_key = compact(left.get("term_key"))
    right_key = compact(right.get("term_key"))
    if left_head and left_head == right_key:
        return "variant"
    if right_head and right_head == left_key:
        return "variant"
    if compact(left.get("variant_place_lemma_normalized")) or compact(right.get("variant_place_lemma_normalized")):
        return "place_qualified_variant"
    return "unreviewed"


def candidate_rows(sample: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, Any]], Counter[str]]:
    rows: list[dict[str, str]] = []
    packets: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    candidate_no = 1
    for item in sample:
        entry = item["entry"]
        terms = item["terms"]
        sample_type = "trigger" if item["trigger_name"] else "control"
        counts[f"sample_{item['author_group']}"] += 1
        counts[f"sample_type_{sample_type}"] += 1
        packet_candidates: list[str] = []

        if sample_type == "control" or len(terms) < 2:
            candidate_id = f"SNRC-{candidate_no:05d}"
            candidate_no += 1
            packet_candidates.append(candidate_id)
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "author_group": item["author_group"],
                    "entry_id": item["entry_id"],
                    "text_source": item["text_source"],
                    "sample_type": sample_type,
                    "candidate_method": item["trigger_name"] or "control_no_trigger",
                    "trigger_pattern": item["trigger_pattern"],
                    "left_term_key": terms[0]["term_key"] if terms else "",
                    "left_display": terms[0]["display"] if terms else "",
                    "right_term_key": "",
                    "right_display": "",
                    "relation_hint": "unreviewed",
                    "evidence_display": item["evidence"] or compact(entry.get("chapter_title_gr")),
                    "review_status": "pending_llm_review",
                    "review_confidence": "",
                    "review_note": "Control entry: reviewer should add any missed name relations or confirm none.",
                }
            )
            counts["candidate_control_rows"] += 1
        else:
            max_pairs = 12
            emitted = 0
            for i, left in enumerate(terms):
                for right in terms[i + 1 :]:
                    if emitted >= max_pairs:
                        break
                    candidate_id = f"SNRC-{candidate_no:05d}"
                    candidate_no += 1
                    packet_candidates.append(candidate_id)
                    rows.append(
                        {
                            "candidate_id": candidate_id,
                            "author_group": item["author_group"],
                            "entry_id": item["entry_id"],
                            "text_source": item["text_source"],
                            "sample_type": sample_type,
                            "candidate_method": item["trigger_name"],
                            "trigger_pattern": item["trigger_pattern"],
                            "left_term_key": left["term_key"],
                            "left_display": left["display"],
                            "right_term_key": right["term_key"],
                            "right_display": right["display"],
                            "relation_hint": relation_hint(left, right),
                            "evidence_display": item["evidence"],
                            "review_status": "pending_llm_review",
                            "review_confidence": "",
                            "review_note": "",
                        }
                    )
                    emitted += 1
                    counts["candidate_relation_rows"] += 1
                if emitted >= max_pairs:
                    break

        packets.append(
            {
                "entry_id": item["entry_id"],
                "author_group": item["author_group"],
                "text_source": item["text_source"],
                "entry_ref": compact(entry.get("ref")),
                "chapter_title_gr": compact(entry.get("chapter_title_gr")),
                "greek": compact(entry.get("greek")),
                "greek_normalized": compact(entry.get("greek_normalized")),
                "candidate_ids": packet_candidates,
                "candidate_terms": [
                    {
                        "term_key": row["term_key"],
                        "display": row["display"],
                        "label": row["label"],
                        "head_lemma_normalized": row["head_lemma_normalized"],
                        "variant_place_lemma_normalized": row["variant_place_lemma_normalized"],
                    }
                    for row in terms
                ],
                "review_instruction": (
                    "Confirm, reject, classify, or add ancient-name relations. "
                    f"Allowed relation types: {', '.join(RELATION_TYPES[:-1])}."
                ),
            }
        )
    return rows, packets, counts


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_pending_pilot(path: Path, candidates: list[dict[str, str]]) -> None:
    rows = []
    for candidate in candidates:
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "entry_id": candidate["entry_id"],
                "text_source": candidate["text_source"],
                "author_group": candidate["author_group"],
                "left_term_key": candidate["left_term_key"],
                "right_term_key": candidate["right_term_key"],
                "relation_type": "unreviewed",
                "evidence_display": candidate["evidence_display"],
                "review_status": "pending_llm_review",
                "review_confidence": "",
                "reviewer": "",
                "review_note": "",
            }
        )
    write_csv(path, rows)


def write_report(path: Path, candidates: list[dict[str, str]], counts: Counter[str], outdir: Path, per_author: int) -> None:
    by_author = Counter(row["author_group"] for row in candidates)
    by_method = Counter(row["candidate_method"] for row in candidates)
    lines = [
        "# Simple Name Relations Pilot Report",
        "",
        f"- Generated: `{datetime.now(UTC).isoformat()}`",
        f"- Git commit: `{git_commit()}`",
        f"- Sample target: `{per_author}` entries per author group",
        f"- Candidate rows: `{len(candidates)}`",
        f"- Review status: `pending_llm_review`",
        "",
        "## Outputs",
        "",
        f"- `{(outdir / 'simple_name_relation_candidates.csv').relative_to(REPO_ROOT)}`",
        f"- `{(outdir / 'simple_name_relation_review_packets.jsonl').relative_to(REPO_ROOT)}`",
        f"- `{(outdir / 'simple_name_relations_pilot.csv').relative_to(REPO_ROOT)}`",
        "",
        "## Candidate Rows By Author",
        "",
    ]
    for author, count in sorted(by_author.items()):
        lines.append(f"- {author}: {count}")
    lines.extend(["", "## Candidate Methods", ""])
    for method, count in sorted(by_method.items()):
        lines.append(f"- {method}: {count}")
    lines.extend(
        [
            "",
            "## Sample Counts",
            "",
        ]
    )
    for key, count in sorted(counts.items()):
        if key.startswith("sample_"):
            lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "Send `simple_name_relation_review_packets.jsonl` plus `simple_name_relation_candidates.csv` to LLM or human reviewers. Reviewers should confirm/reject candidates, classify relation types, and add missed relations visible in each passage.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--occurrences", type=Path, default=DEFAULT_REGISTRY_OCCURRENCES)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--per-author", type=int, default=20)
    args = parser.parse_args()

    config = load_config(args.config)
    entries = load_entries(config.get("entry_csvs", []))
    by_entry = load_occurrences(args.occurrences)
    sample = choose_sample(entries, by_entry, author_group_lookup(config), args.per_author)
    candidates, packets, counts = candidate_rows(sample)

    args.outdir.mkdir(parents=True, exist_ok=True)
    write_csv(args.outdir / "simple_name_relation_candidates.csv", candidates)
    with (args.outdir / "simple_name_relation_review_packets.jsonl").open("w", encoding="utf-8") as handle:
        for packet in packets:
            handle.write(json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n")
    write_pending_pilot(args.outdir / "simple_name_relations_pilot.csv", candidates)
    write_report(args.outdir / "simple_name_relations_pilot_report.md", candidates, counts, args.outdir, args.per_author)
    print(
        f"Wrote {len(candidates)} candidate rows "
        f"for {len(packets)} sampled entries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a compact browser index for the user-facing simples registry view."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBENCH = REPO_ROOT / "data-workbench" / "simples"
DEFAULT_OUT = REPO_ROOT / "app" / "public" / "simples" / "registry-index.json"
DEFAULT_VOCAB_INDEX = REPO_ROOT / "app" / "public" / "vocab" / "vocab-index.json"
DEFAULT_CONFIG = REPO_ROOT / "config" / "simples_registry_runs.json"


def compact(value: object) -> str:
    return " ".join(str(value or "").split())


def split_list(value: str) -> list[str]:
    return [item for item in (compact(part) for part in value.split(";")) if item]


def to_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def to_float(value: object) -> float | None:
    value = compact(value)
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def label_counts(value: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in split_list(value):
        if ":" in item:
            label, count = item.split(":", 1)
            counts[label] = to_int(count)
        elif item:
            counts[item] = 1
    return counts


def load_quality_summaries(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    summaries: dict[str, list[dict[str, Any]]] = {}
    for simple in payload.get("simples", []):
        key = compact(simple.get("lemma_normalized"))
        if not key:
            continue
        summaries[key] = [
            {
                "axis": quality.get("axis"),
                "degree": quality.get("degree"),
                "entry_count": quality.get("entry_count", 0),
                "direct": bool(quality.get("direct")),
            }
            for quality in (simple.get("qualities") or [])[:8]
        ]
    return summaries


def relation_status(candidate_count: int, pending_count: int, reviewed_count: int) -> str:
    if candidate_count == 0:
        return "none"
    if reviewed_count and pending_count:
        return "mixed_review"
    if reviewed_count:
        return "reviewed"
    return "pending_candidates"


def build_index(
    *,
    workbench: Path = DEFAULT_WORKBENCH,
    vocab_index_path: Path = DEFAULT_VOCAB_INDEX,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    term_rows = read_csv(workbench / "simple_terms_v0.csv")
    form_rows = read_csv(workbench / "simple_term_forms_v0.csv")
    occurrence_rows = read_csv(workbench / "simple_term_occurrences_v0.csv")
    candidate_rows = read_csv(workbench / "simple_name_relation_candidates.csv")
    pilot_rows = read_csv(workbench / "simple_name_relations_pilot.csv")

    manifest_path = workbench / "simple_registry_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    quality_summaries = load_quality_summaries(vocab_index_path)

    forms_by_term: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in form_rows:
        key = compact(row.get("term_key"))
        if not key:
            continue
        forms_by_term[key].append(
            {
                "display": compact(row.get("form_display")),
                "normalized": compact(row.get("form_normalized")),
                "count": to_int(row.get("count")),
                "entry_count": to_int(row.get("entry_count")),
                "text_sources": split_list(row.get("text_sources", "")),
                "author_groups": split_list(row.get("author_groups", "")),
            }
        )
    for forms in forms_by_term.values():
        forms.sort(key=lambda item: (-item["count"], item["display"]))

    source_counts: dict[str, Counter[str]] = defaultdict(Counter)
    author_counts: dict[str, Counter[str]] = defaultdict(Counter)
    entry_samples: dict[str, list[str]] = defaultdict(list)
    for row in occurrence_rows:
        key = compact(row.get("term_key"))
        if not key:
            continue
        source = compact(row.get("text_source"))
        author = compact(row.get("author_group"))
        entry_id = compact(row.get("entry_id"))
        if source:
            source_counts[key][source] += 1
        if author:
            author_counts[key][author] += 1
        if entry_id and len(entry_samples[key]) < 20 and entry_id not in entry_samples[key]:
            entry_samples[key].append(entry_id)

    candidate_counts: Counter[str] = Counter()
    pending_counts: Counter[str] = Counter()
    for row in candidate_rows:
        for key in (compact(row.get("left_term_key")), compact(row.get("right_term_key"))):
            if key:
                candidate_counts[key] += 1
                if compact(row.get("review_status")) == "pending_llm_review":
                    pending_counts[key] += 1

    reviewed_counts: Counter[str] = Counter()
    for row in pilot_rows:
        relation_type = compact(row.get("relation_type"))
        review_status = compact(row.get("review_status"))
        is_reviewed = relation_type not in {"", "unreviewed"} or review_status not in {"", "pending_llm_review"}
        if not is_reviewed:
            continue
        for key in (compact(row.get("left_term_key")), compact(row.get("right_term_key"))):
            if key:
                reviewed_counts[key] += 1

    terms: list[dict[str, Any]] = []
    source_totals: Counter[str] = Counter()
    author_totals: Counter[str] = Counter()
    review_totals: Counter[str] = Counter()
    for row in term_rows:
        key = compact(row.get("term_key"))
        if not key:
            continue
        source_map = dict(sorted(source_counts[key].items()))
        author_map = dict(sorted(author_counts[key].items()))
        for source in source_map:
            source_totals[source] += 1
        for author in author_map:
            author_totals[author] += 1
        candidate_count = candidate_counts[key]
        pending_count = pending_counts[key]
        reviewed_count = reviewed_counts[key]
        status = relation_status(candidate_count, pending_count, reviewed_count)
        review_totals[status] += 1
        forms = forms_by_term.get(key, [])
        search_text = " ".join(
            [
                key,
                compact(row.get("preferred_display")),
                " ".join(form["display"] for form in forms[:16]),
                " ".join(source_map.keys()),
                " ".join(author_map.keys()),
                compact(row.get("head_lemma_normalized")),
                compact(row.get("variant_place_lemma_normalized")),
            ]
        ).lower()
        terms.append(
            {
                "term_key": key,
                "preferred_display": compact(row.get("preferred_display")),
                "lemma_normalized": compact(row.get("lemma_normalized")),
                "labels": label_counts(row.get("labels", "")),
                "is_multiword": compact(row.get("is_multiword")) == "true",
                "head_lemma_normalized": compact(row.get("head_lemma_normalized")),
                "variant_place_lemma_normalized": compact(row.get("variant_place_lemma_normalized")),
                "source_count": to_int(row.get("source_count")),
                "entry_count": to_int(row.get("entry_count")),
                "occurrence_count": to_int(row.get("occurrence_count")),
                "text_sources": split_list(row.get("text_sources", "")),
                "author_groups": split_list(row.get("author_groups", "")),
                "source_counts": source_map,
                "author_counts": author_map,
                "result_runs": split_list(row.get("result_runs", "")),
                "confidence_avg": to_float(row.get("confidence_avg")),
                "status": compact(row.get("status")),
                "forms": forms[:24],
                "quality_summary": quality_summaries.get(key, []),
                "entry_samples": entry_samples.get(key, []),
                "name_relation": {
                    "status": status,
                    "candidate_count": candidate_count,
                    "pending_count": pending_count,
                    "reviewed_count": reviewed_count,
                },
                "search_text": search_text,
            }
        )
    terms.sort(key=lambda item: (-item["entry_count"], item["preferred_display"]))

    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "source_files": {
            "manifest": relative(manifest_path),
            "terms": relative(workbench / "simple_terms_v0.csv"),
            "forms": relative(workbench / "simple_term_forms_v0.csv"),
            "occurrences": relative(workbench / "simple_term_occurrences_v0.csv"),
            "candidates": relative(workbench / "simple_name_relation_candidates.csv"),
            "pilot": relative(workbench / "simple_name_relations_pilot.csv"),
            "vocab_index": relative(vocab_index_path),
        },
        "future_corpora": config.get("future_corpora", []),
        "stats": {
            "terms": len(terms),
            "occurrences": len(occurrence_rows),
            "forms": len(form_rows),
            "sources": dict(sorted(source_totals.items())),
            "author_groups": dict(sorted(author_totals.items())),
            "review_statuses": dict(sorted(review_totals.items())),
            "registry_manifest_counts": manifest.get("counts", {}),
        },
        "terms": terms,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbench", type=Path, default=DEFAULT_WORKBENCH)
    parser.add_argument("--vocab-index", type=Path, default=DEFAULT_VOCAB_INDEX)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    index = build_index(workbench=args.workbench, vocab_index_path=args.vocab_index, config_path=args.config)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} ({index['stats']['terms']} registry terms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

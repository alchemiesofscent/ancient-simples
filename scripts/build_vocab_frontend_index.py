#!/usr/bin/env python3
"""Build a static browser index for the vocab v3 simples viewer."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
VOCAB_OUTPUT_ROOT = REPO_ROOT / "outputs" / "vocab_entries_v3"
DEFAULT_RUN_NAMES = ["entries_full_v3", "diosc_full_v3", "paul_full_v3"]
DEFAULT_RUN_DIRS = [
    VOCAB_OUTPUT_ROOT / run_name / "results"
    for run_name in DEFAULT_RUN_NAMES
    if (VOCAB_OUTPUT_ROOT / run_name / "results").exists()
]
DEFAULT_OUTPUT = REPO_ROOT / "app" / "public" / "vocab" / "vocab-index.json"

LABELS = [
    "SUBSTANCE",
    "SUBSTANCE_PART",
    "PART",
    "PREPARATION",
    "PROCESS",
    "TOOL_CONTAINER",
    "CONDITION",
    "QUALITY_PROPERTY",
    "APPLICATION_SITE",
    "ADMINISTRATION",
    "PLACE",
]
SIMPLE_LABELS = {"SUBSTANCE", "SUBSTANCE_PART"}
QUALITY_AXES = ["HOT", "COLD", "DRY", "WET"]
MAX_EXAMPLES = 8


def normalize_for_match(value: str) -> str:
    lowered = value.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(
        ch for ch in decomposed
        if not (0x0300 <= ord(ch) <= 0x036F)
    )
    return unicodedata.normalize("NFC", stripped)


def compact_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def source_code(source_id: str) -> str:
    if "-" in source_id:
        return source_id.rsplit("-", 1)[0]
    return source_id


def confidence_band(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value >= 0.9:
        return "0.90+"
    if value >= 0.75:
        return "0.75-0.89"
    if value >= 0.5:
        return "0.50-0.74"
    return "<0.50"


def term_key(term: dict[str, Any]) -> str:
    return compact_space(
        term.get("lemma_normalized")
        or term.get("normalized")
        or normalize_for_match(term.get("lemma_gr") or term.get("display") or "")
    )


def term_display(term: dict[str, Any], fallback: str) -> str:
    return compact_space(term.get("lemma_gr") or term.get("display") or fallback)


def applies_to_keys(payload: dict[str, Any] | None) -> set[str]:
    if not payload:
        return set()
    keys = {
        payload.get("lemma_normalized"),
        payload.get("substance_lemma_normalized"),
    }
    return {compact_space(key) for key in keys if compact_space(key or "")}


def add_limited(items: list[dict[str, Any]], item: dict[str, Any], limit: int = MAX_EXAMPLES) -> None:
    if item in items:
        return
    if len(items) < limit:
        items.append(item)


def new_simple(key: str, display: str) -> dict[str, Any]:
    return {
        "lemma_normalized": key,
        "display": display or key,
        "_display_counter": Counter(),
        "_labels": Counter(),
        "_sources": Counter(),
        "_entries": set(),
        "_confidences": [],
        "_forms": defaultdict(lambda: {"display": "", "count": 0, "sources": set()}),
        "_facets": {
            label: defaultdict(lambda: {
                "key": "",
                "display": "",
                "count": 0,
                "sources": set(),
                "entries": set(),
                "direct": False,
                "examples": [],
            })
            for label in LABELS
        },
        "_qualities": defaultdict(lambda: {
            "axis": "",
            "degree": None,
            "count": 0,
            "sources": set(),
            "entries": set(),
            "direct": False,
            "examples": [],
        }),
    }


def ingest_result(
    result: dict[str, Any],
    simples: dict[str, dict[str, Any]],
    entries: list[dict[str, Any]],
    global_labels: Counter[str],
    global_sources: Counter[str],
) -> None:
    source_id = compact_space(result.get("source_id") or result.get("entry_id") or "")
    if not source_id:
        return
    source = source_code(source_id)
    global_sources[source] += 1

    terms = [term for term in result.get("terms") or [] if isinstance(term, dict)]
    qualities = [quality for quality in result.get("qualities") or [] if isinstance(quality, dict)]
    entry_simple_keys: set[str] = set()
    compact_terms: list[dict[str, Any]] = []

    for term in terms:
        label = compact_space(term.get("label") or "").upper()
        if label not in LABELS:
            continue
        key = term_key(term)
        if not key:
            continue
        display = term_display(term, key)
        confidence = term.get("confidence")
        try:
            confidence_value = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence_value = None
        global_labels[label] += 1

        compact = {
            "label": label,
            "key": key,
            "display": display,
            "confidence": confidence_value,
            "applies_to": sorted(applies_to_keys(term.get("applies_to"))),
        }
        compact_terms.append(compact)

        if label in SIMPLE_LABELS:
            entry_simple_keys.add(key)
            simple = simples.setdefault(key, new_simple(key, display))
            simple["_display_counter"][display] += 1
            simple["_labels"][label] += 1
            simple["_sources"][source] += 1
            simple["_entries"].add(source_id)
            if confidence_value is not None:
                simple["_confidences"].append(confidence_value)
            form = simple["_forms"][display]
            form["display"] = display
            form["count"] += 1
            form["sources"].add(source)

    for term in compact_terms:
        if term["label"] in SIMPLE_LABELS:
            continue
        target_keys = set(term["applies_to"]) & entry_simple_keys
        linked_keys = target_keys or entry_simple_keys
        for simple_key in linked_keys:
            simple = simples.get(simple_key)
            if not simple:
                continue
            facet = simple["_facets"][term["label"]][term["key"]]
            facet["key"] = term["key"]
            facet["display"] = term["display"]
            facet["count"] += 1
            facet["sources"].add(source)
            facet["entries"].add(source_id)
            if simple_key in target_keys:
                facet["direct"] = True
            add_limited(
                facet["examples"],
                {
                    "entry_id": source_id,
                    "source": source,
                    "display": term["display"],
                    "confidence": term["confidence"],
                    "relation": "direct" if simple_key in target_keys else "cooccurs",
                },
            )

    compact_qualities: list[dict[str, Any]] = []
    for quality in qualities:
        axis = compact_space(quality.get("axis") or "").upper()
        if axis not in QUALITY_AXES:
            continue
        degree = quality.get("degree")
        if degree is not None:
            degree = str(degree)
        evidence = compact_space(quality.get("evidence_display") or quality.get("evidence_normalized") or "")
        try:
            confidence_value = float(quality.get("confidence")) if quality.get("confidence") is not None else None
        except (TypeError, ValueError):
            confidence_value = None
        target_keys = applies_to_keys(quality.get("applies_to"))
        linked_keys = (target_keys & entry_simple_keys) or entry_simple_keys
        compact_quality = {
            "axis": axis,
            "degree": degree,
            "confidence": confidence_value,
            "evidence": evidence,
            "applies_to": sorted(target_keys),
        }
        compact_qualities.append(compact_quality)

        for simple_key in linked_keys:
            simple = simples.get(simple_key)
            if not simple:
                continue
            qkey = f"{axis}:{degree or 'unspecified'}"
            item = simple["_qualities"][qkey]
            item["axis"] = axis
            item["degree"] = degree
            item["count"] += 1
            item["sources"].add(source)
            item["entries"].add(source_id)
            if simple_key in target_keys:
                item["direct"] = True
            add_limited(
                item["examples"],
                {
                    "entry_id": source_id,
                    "source": source,
                    "evidence": evidence,
                    "confidence": confidence_value,
                    "relation": "direct" if simple_key in target_keys else "cooccurs",
                },
            )

    entries.append(
        {
            "entry_id": source_id,
            "source": source,
            "simple_keys": sorted(entry_simple_keys),
            "terms": compact_terms,
            "qualities": compact_qualities,
        }
    )


def finalize_simple(simple: dict[str, Any]) -> dict[str, Any]:
    confidences = simple["_confidences"]
    confidence_avg = round(statistics.fmean(confidences), 3) if confidences else None
    display = simple["_display_counter"].most_common(1)[0][0] if simple["_display_counter"] else simple["display"]

    facets: dict[str, list[dict[str, Any]]] = {}
    for label, values in simple["_facets"].items():
        finalized = []
        for facet in values.values():
            finalized.append(
                {
                    "key": facet["key"],
                    "display": facet["display"],
                    "count": facet["count"],
                    "sources": sorted(facet["sources"]),
                    "entry_count": len(facet["entries"]),
                    "direct": facet["direct"],
                    "examples": facet["examples"],
                }
            )
        facets[label] = sorted(finalized, key=lambda item: (-item["count"], item["display"]))[:80]

    qualities = [
        {
            "axis": item["axis"],
            "degree": item["degree"],
            "count": item["count"],
            "sources": sorted(item["sources"]),
            "entry_count": len(item["entries"]),
            "direct": item["direct"],
            "examples": item["examples"],
        }
        for item in simple["_qualities"].values()
    ]

    forms = [
        {
            "display": item["display"],
            "count": item["count"],
            "sources": sorted(item["sources"]),
        }
        for item in simple["_forms"].values()
    ]

    return {
        "lemma_normalized": simple["lemma_normalized"],
        "display": display,
        "search_text": normalize_for_match(
            " ".join(
                [
                    simple["lemma_normalized"],
                    display,
                    " ".join(simple["_display_counter"].keys()),
                    " ".join(
                        facet["display"]
                        for label_values in facets.values()
                        for facet in label_values
                    ),
                    " ".join(
                        example.get("evidence", "")
                        for quality in qualities
                        for example in quality["examples"]
                    ),
                ]
            )
        ),
        "labels": dict(simple["_labels"]),
        "sources": dict(simple["_sources"]),
        "entry_ids": sorted(simple["_entries"]),
        "entry_count": len(simple["_entries"]),
        "source_count": len(simple["_sources"]),
        "confidence_avg": confidence_avg,
        "confidence_band": confidence_band(confidence_avg),
        "forms": sorted(forms, key=lambda item: (-item["count"], item["display"]))[:40],
        "facets": facets,
        "qualities": sorted(
            qualities,
            key=lambda item: (QUALITY_AXES.index(item["axis"]), item["degree"] or "z"),
        ),
    }


def build_index(run_dirs: list[Path]) -> dict[str, Any]:
    simples: dict[str, dict[str, Any]] = {}
    entries: list[dict[str, Any]] = []
    global_labels: Counter[str] = Counter()
    global_sources: Counter[str] = Counter()
    files: list[Path] = []
    for run_dir in run_dirs:
        files.extend(sorted(run_dir.glob("*.json")))

    for path in files:
        if path.name.endswith(".tmp"):
            continue
        with path.open("r", encoding="utf-8") as handle:
            ingest_result(json.load(handle), simples, entries, global_labels, global_sources)

    finalized_simples = sorted(
        (finalize_simple(simple) for simple in simples.values()),
        key=lambda item: (-item["entry_count"], item["display"]),
    )
    facet_counts = {label: Counter() for label in LABELS}
    quality_counts: Counter[str] = Counter()
    for simple in finalized_simples:
        for label, values in simple["facets"].items():
            for facet in values:
                facet_counts[label][facet["key"]] += facet["count"]
        for quality in simple["qualities"]:
            quality_counts[f"{quality['axis']}:{quality['degree'] or 'unspecified'}"] += quality["count"]

    generated_from = []
    for path in run_dirs:
        try:
            generated_from.append(str(path.relative_to(REPO_ROOT)))
        except ValueError:
            generated_from.append(str(path))

    return {
        "version": 1,
        "generated_from": generated_from,
        "labels": LABELS,
        "quality_axes": QUALITY_AXES,
        "stats": {
            "result_files": len(files),
            "entries": len(entries),
            "simples": len(finalized_simples),
            "term_labels": dict(global_labels),
            "sources": dict(global_sources),
        },
        "facet_options": {
            label: [
                {"key": key, "count": count}
                for key, count in counter.most_common(250)
            ]
            for label, counter in facet_counts.items()
        },
        "quality_options": [
            {"key": key, "count": count}
            for key, count in quality_counts.most_common()
        ],
        "simples": finalized_simples,
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        action="append",
        type=Path,
        dest="run_dirs",
        help="Result directory to include. Defaults to legacy full + Dioscorides full.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    run_dirs = args.run_dirs or DEFAULT_RUN_DIRS
    missing = [path for path in run_dirs if not path.exists()]
    if missing:
        raise SystemExit(f"Missing result directories: {', '.join(str(path) for path in missing)}")

    index = build_index(run_dirs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.out} "
        f"({index['stats']['simples']} simples, {index['stats']['entries']} entries)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

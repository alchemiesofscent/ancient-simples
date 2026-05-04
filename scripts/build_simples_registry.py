#!/usr/bin/env python3
"""Build the v0 simples term registry from vocab_entries_v3 outputs."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
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

from textutils.normalize import normalize

DEFAULT_CONFIG = REPO_ROOT / "config" / "simples_registry_runs.json"
DEFAULT_OUTDIR = REPO_ROOT / "data-workbench" / "simples"
SIMPLE_LABELS = {"SUBSTANCE", "SUBSTANCE_PART"}


def repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def compact(value: object) -> str:
    return " ".join(str(value or "").split())


def source_code(entry_id: str) -> str:
    if "-" in entry_id:
        return entry_id.rsplit("-", 1)[0]
    return entry_id


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_entries(paths: list[str]) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for path_text in paths:
        path = repo_path(path_text)
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                entry_id = compact(row.get("entry_id"))
                if entry_id:
                    entries[entry_id] = row
    return entries


def author_group_lookup(config: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for group in config.get("author_groups", []):
        author = compact(group.get("author_group"))
        for source in group.get("source_codes", []):
            lookup[compact(source)] = author
    return lookup


def term_key(term: dict[str, Any]) -> str:
    for field in ("lemma_normalized", "normalized", "substance_lemma_normalized"):
        value = compact(term.get(field))
        if value:
            return value
    value = compact(term.get("lemma_gr") or term.get("display"))
    return normalize(value) if value else ""


def term_display(term: dict[str, Any], key: str) -> str:
    return compact(term.get("lemma_gr") or term.get("display") or key)


def term_confidence(term: dict[str, Any], field: str) -> float | None:
    value = term.get(field)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def applies_to(term: dict[str, Any]) -> dict[str, str]:
    payload = term.get("applies_to")
    if not isinstance(payload, dict):
        payload = {}
    return {
        "applies_to_kind": compact(payload.get("kind")),
        "applies_to_lemma_normalized": compact(payload.get("lemma_normalized")),
        "applies_to_substance_lemma_normalized": compact(payload.get("substance_lemma_normalized")),
        "applies_to_part_lemma_normalized": compact(payload.get("part_lemma_normalized")),
    }


def read_result_files(config: dict[str, Any]) -> list[tuple[str, Path, dict[str, Any]]]:
    records: list[tuple[str, Path, dict[str, Any]]] = []
    for run in config.get("included_runs", []):
        if not run.get("complete", False):
            continue
        run_id = compact(run.get("run_id"))
        result_dir = repo_path(run.get("result_dir", ""))
        for path in sorted(result_dir.glob("*.json")):
            if path.name.endswith(".tmp"):
                continue
            with path.open("r", encoding="utf-8") as handle:
                records.append((run_id, path, json.load(handle)))
    return records


def build_registry(config: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    entries = load_entries(config.get("entry_csvs", []))
    source_to_author = author_group_lookup(config)
    term_rows: dict[str, dict[str, Any]] = {}
    occurrence_rows: list[dict[str, str]] = []
    form_counts: dict[tuple[str, str], dict[str, Any]] = {}
    source_counts: Counter[str] = Counter()
    author_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    run_counts: Counter[str] = Counter()

    for run_id, path, result in read_result_files(config):
        entry_id = compact(result.get("entry_id") or result.get("source_id"))
        if not entry_id:
            continue
        source = source_code(entry_id)
        author = source_to_author.get(source, source)
        entry_meta = entries.get(entry_id, {})
        run_counts[run_id] += 1
        source_counts[source] += 1
        author_counts[author] += 1

        for index, term in enumerate(result.get("terms") or []):
            if not isinstance(term, dict):
                continue
            label = compact(term.get("label")).upper()
            if label not in SIMPLE_LABELS:
                continue
            key = term_key(term)
            if not key:
                continue
            display = term_display(term, key)
            confidence = term_confidence(term, "confidence")
            lemma_confidence = term_confidence(term, "lemma_confidence")
            label_counts[label] += 1

            agg = term_rows.setdefault(
                key,
                {
                    "term_key": key,
                    "display_counter": Counter(),
                    "label_counter": Counter(),
                    "sources": Counter(),
                    "authors": Counter(),
                    "entries": set(),
                    "runs": Counter(),
                    "head_lemma_normalized": set(),
                    "variant_place_lemma_normalized": set(),
                    "is_multiword": False,
                    "confidences": [],
                },
            )
            agg["display_counter"][display] += 1
            agg["label_counter"][label] += 1
            agg["sources"][source] += 1
            agg["authors"][author] += 1
            agg["entries"].add(entry_id)
            agg["runs"][run_id] += 1
            agg["is_multiword"] = bool(agg["is_multiword"] or term.get("is_multiword"))
            if compact(term.get("head_lemma_normalized")):
                agg["head_lemma_normalized"].add(compact(term.get("head_lemma_normalized")))
            if compact(term.get("variant_place_lemma_normalized")):
                agg["variant_place_lemma_normalized"].add(compact(term.get("variant_place_lemma_normalized")))
            if confidence is not None:
                agg["confidences"].append(confidence)

            form_key = (key, display)
            form = form_counts.setdefault(
                form_key,
                {
                    "term_key": key,
                    "form_display": display,
                    "form_normalized": normalize(display),
                    "sources": Counter(),
                    "authors": Counter(),
                    "entries": set(),
                    "count": 0,
                },
            )
            form["count"] += 1
            form["sources"][source] += 1
            form["authors"][author] += 1
            form["entries"].add(entry_id)

            occurrence = {
                "occurrence_id": f"{run_id}:{entry_id}:{index}",
                "term_key": key,
                "entry_id": entry_id,
                "text_source": source,
                "author_group": author,
                "result_run": run_id,
                "entry_ref": compact(entry_meta.get("ref")),
                "chapter_title_gr": compact(entry_meta.get("chapter_title_gr")),
                "display": compact(term.get("display")),
                "lemma_gr": compact(term.get("lemma_gr")),
                "label": label,
                "normalized": compact(term.get("normalized")),
                "lemma_normalized": compact(term.get("lemma_normalized")),
                "is_multiword": str(bool(term.get("is_multiword"))).lower(),
                "head_lemma_normalized": compact(term.get("head_lemma_normalized")),
                "substance_lemma_normalized": compact(term.get("substance_lemma_normalized")),
                "part_lemma_normalized": compact(term.get("part_lemma_normalized")),
                "variant_place_lemma_normalized": compact(term.get("variant_place_lemma_normalized")),
                "confidence": "" if confidence is None else f"{confidence:.3f}",
                "lemma_confidence": "" if lemma_confidence is None else f"{lemma_confidence:.3f}",
                "result_file": display_path(path),
            }
            occurrence.update(applies_to(term))
            occurrence_rows.append(occurrence)

    term_output: list[dict[str, str]] = []
    for key, agg in sorted(term_rows.items()):
        confidences = agg["confidences"]
        confidence_avg = statistics.fmean(confidences) if confidences else None
        term_output.append(
            {
                "term_key": key,
                "preferred_display": agg["display_counter"].most_common(1)[0][0],
                "lemma_normalized": key,
                "labels": ";".join(f"{label}:{count}" for label, count in sorted(agg["label_counter"].items())),
                "is_multiword": str(bool(agg["is_multiword"])).lower(),
                "head_lemma_normalized": ";".join(sorted(agg["head_lemma_normalized"])),
                "variant_place_lemma_normalized": ";".join(sorted(agg["variant_place_lemma_normalized"])),
                "source_count": str(len(agg["sources"])),
                "entry_count": str(len(agg["entries"])),
                "occurrence_count": str(sum(agg["sources"].values())),
                "text_sources": ";".join(sorted(agg["sources"])),
                "author_groups": ";".join(sorted(agg["authors"])),
                "result_runs": ";".join(sorted(agg["runs"])),
                "confidence_avg": "" if confidence_avg is None else f"{confidence_avg:.3f}",
                "status": "draft",
            }
        )

    form_output: list[dict[str, str]] = []
    for (_key, _display), item in sorted(form_counts.items()):
        form_output.append(
            {
                "term_key": item["term_key"],
                "form_display": item["form_display"],
                "form_normalized": item["form_normalized"],
                "count": str(item["count"]),
                "entry_count": str(len(item["entries"])),
                "text_sources": ";".join(sorted(item["sources"])),
                "author_groups": ";".join(sorted(item["authors"])),
            }
        )

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "config_path": str(DEFAULT_CONFIG.relative_to(REPO_ROOT)),
        "included_runs": config.get("included_runs", []),
        "entry_csvs": config.get("entry_csvs", []),
        "future_corpora": config.get("future_corpora", []),
        "counts": {
            "terms": len(term_output),
            "occurrences": len(occurrence_rows),
            "forms": len(form_output),
            "sources": dict(sorted(source_counts.items())),
            "author_groups": dict(sorted(author_counts.items())),
            "labels": dict(sorted(label_counts.items())),
            "runs": dict(sorted(run_counts.items())),
        },
        "command": "python scripts/build_simples_registry.py",
    }
    return term_output, occurrence_rows, form_output, manifest


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    args = parser.parse_args()

    config = load_config(args.config)
    terms, occurrences, forms, manifest = build_registry(config)
    args.outdir.mkdir(parents=True, exist_ok=True)
    write_csv(args.outdir / "simple_terms_v0.csv", terms)
    write_csv(args.outdir / "simple_term_occurrences_v0.csv", occurrences)
    write_csv(args.outdir / "simple_term_forms_v0.csv", forms)
    manifest["outputs"] = {
        "simple_terms_v0": str((args.outdir / "simple_terms_v0.csv").relative_to(REPO_ROOT)),
        "simple_term_occurrences_v0": str((args.outdir / "simple_term_occurrences_v0.csv").relative_to(REPO_ROOT)),
        "simple_term_forms_v0": str((args.outdir / "simple_term_forms_v0.csv").relative_to(REPO_ROOT)),
        "simple_registry_manifest": str((args.outdir / "simple_registry_manifest.json").relative_to(REPO_ROOT)),
    }
    (args.outdir / "simple_registry_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "Wrote simples registry "
        f"({manifest['counts']['terms']} terms, "
        f"{manifest['counts']['occurrences']} occurrences, "
        f"{manifest['counts']['forms']} forms)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

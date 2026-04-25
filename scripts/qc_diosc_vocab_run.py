#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import sys


_THIS_REPO_ROOT = Path(__file__).resolve().parents[1]

from textutils.normalize import normalize as normalize_greek


def _load_manifest(run_dir: Path, manifest_arg: str | None) -> Path:
    if manifest_arg:
        p = Path(manifest_arg)
        if not p.exists():
            raise SystemExit(f"Manifest not found: {p}")
        return p

    explicit = run_dir / "manifest.json"
    if explicit.exists():
        return explicit

    manifests = sorted(run_dir.glob("manifest_*.json"), key=lambda p: p.stat().st_mtime)
    if manifests:
        return manifests[-1]

    raise SystemExit(f"No manifest found under {run_dir}")


def _validate_normalized_fields(obj: dict) -> list[str]:
    issues: list[str] = []

    for idx, term in enumerate(obj.get("terms") or []):
        path = f"terms[{idx}]"
        display = term.get("display", "")
        normalized = term.get("normalized", "")
        expected = normalize_greek(display)
        if normalized != expected:
            issues.append(f"{path}.normalized expected {expected!r}, got {normalized!r}")

        lemma_gr = term.get("lemma_gr", "")
        lemma_normalized = term.get("lemma_normalized", "")
        if lemma_gr and lemma_normalized != normalize_greek(lemma_gr):
            issues.append(
                f"{path}.lemma_normalized expected {normalize_greek(lemma_gr)!r}, got {lemma_normalized!r}"
            )
        if not lemma_gr and lemma_normalized != "":
            issues.append(f"{path}.lemma_normalized must be empty when lemma_gr empty")

        for key in [
            "head_lemma_normalized",
            "substance_lemma_normalized",
            "part_lemma_normalized",
            "variant_place_lemma_normalized",
        ]:
            value = term.get(key)
            if isinstance(value, str) and value != normalize_greek(value):
                issues.append(f"{path}.{key} is not normalized")

        applies_to = term.get("applies_to") or {}
        for key in ["lemma_normalized", "substance_lemma_normalized", "part_lemma_normalized"]:
            value = applies_to.get(key)
            if isinstance(value, str) and value != normalize_greek(value):
                issues.append(f"{path}.applies_to.{key} is not normalized")

        if term.get("label") == "SUBSTANCE_PART":
            if term.get("lemma_gr", "") != "":
                issues.append(f"{path}.lemma_gr must be empty for SUBSTANCE_PART")
            if term.get("lemma_normalized", "") != "":
                issues.append(f"{path}.lemma_normalized must be empty for SUBSTANCE_PART")
            if not (term.get("substance_lemma_normalized") or ""):
                issues.append(f"{path}.substance_lemma_normalized missing for SUBSTANCE_PART")
            if not (term.get("part_lemma_normalized") or ""):
                issues.append(f"{path}.part_lemma_normalized missing for SUBSTANCE_PART")

    for idx, quality in enumerate(obj.get("qualities") or []):
        path = f"qualities[{idx}]"
        display = quality.get("evidence_display", "")
        normalized = quality.get("evidence_normalized", "")
        expected = normalize_greek(display)
        if normalized != expected:
            issues.append(
                f"{path}.evidence_normalized expected {expected!r}, got {normalized!r}"
            )

        for key in ["variant_place_lemma_normalized"]:
            value = quality.get(key)
            if isinstance(value, str) and value != normalize_greek(value):
                issues.append(f"{path}.{key} is not normalized")

        applies_to = quality.get("applies_to") or {}
        for key in ["lemma_normalized", "substance_lemma_normalized", "part_lemma_normalized"]:
            value = applies_to.get(key)
            if isinstance(value, str) and value != normalize_greek(value):
                issues.append(f"{path}.applies_to.{key} is not normalized")

    return issues


def _write_md(path: Path, summary: dict) -> None:
    lines: list[str] = []
    lines.append("# Dioscorides vocab run QC summary")
    lines.append("")
    lines.append(f"- Run dir: `{summary['run_dir']}`")
    lines.append(f"- Manifest: `{summary['manifest_path']}`")
    lines.append(f"- Run id: `{summary['run_id']}`")
    lines.append("")
    lines.append("## Completeness")
    lines.append(f"- Expected jobs: {summary['expected_jobs']}")
    lines.append(f"- Result files present: {summary['result_files']}")
    lines.append(f"- Valid result JSONs: {summary['valid_results']}")
    lines.append(f"- Missing results: {summary['missing_results']}")
    lines.append(f"- Invalid JSON files: {summary['invalid_json']}")
    lines.append(f"- source_id mismatches: {summary['source_id_mismatches']}")
    lines.append(f"- Error logs present: {summary['error_files']}")
    lines.append(f"- Completeness OK: **{summary['completeness_ok']}**")
    lines.append("")
    lines.append("## Quality profile")
    lines.append(f"- Total qualities: {summary['qualities_total']}")
    lines.append(f"- Entries with >=1 quality: {summary['entries_with_quality']}")
    lines.append(f"- Entries with degree != null: {summary['entries_with_degree']}")
    lines.append(f"- Qualities with explicit degree: {summary['qualities_with_degree']}")
    lines.append(f"- Degree ratio: {summary['degree_ratio']:.3f}")
    lines.append("")
    lines.append("### Axis counts")
    for axis, count in summary["axis_counts"].items():
        lines.append(f"- {axis}: {count}")
    lines.append("")
    lines.append("### Intensity counts")
    for intensity, count in summary["intensity_counts"].items():
        lines.append(f"- {intensity}: {count}")
    lines.append("")
    lines.append("## Term profile")
    for label, count in summary["term_label_counts"].items():
        lines.append(f"- {label}: {count}")
    lines.append("")
    lines.append("## Anomalies")
    lines.append(
        f"- QUALITY_PROPERTY lemma_normalized in {{δυναμις, ουσια}}: {summary['generic_quality_property_count']}"
    )
    lines.append(f"- SUBSTANCE_PART consistency anomalies: {summary['substance_part_anomalies']}")
    lines.append(f"- Normalization anomalies: {summary['normalization_anomalies']}")
    if summary["alerts"]:
        lines.append("")
        lines.append("## Alerts")
        for alert in summary["alerts"]:
            lines.append(f"- {alert}")
    if summary["missing_result_ids"]:
        lines.append("")
        lines.append("## Missing result IDs (first 50)")
        for eid in summary["missing_result_ids"][:50]:
            lines.append(f"- `{eid}`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="QC summary for Dioscorides vocab extraction runs.")
    ap.add_argument(
        "--run-dir",
        default=str(_THIS_REPO_ROOT / "outputs" / "vocab_entries_v3" / "diosc_full_v3"),
        help="Run directory created by vocab_multi_agent_pilot.py",
    )
    ap.add_argument(
        "--manifest",
        default=None,
        help="Optional explicit manifest path; otherwise auto-detect in run-dir.",
    )
    ap.add_argument(
        "--out-md",
        default=None,
        help="Markdown summary path (default: <run-dir>/qc_summary.md)",
    )
    ap.add_argument(
        "--out-json",
        default=None,
        help="JSON summary path (default: <run-dir>/qc_summary.json)",
    )
    ap.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Exit 0 even if results are incomplete.",
    )
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"Run dir not found: {run_dir}")
    results_dir = run_dir / "results"
    errors_dir = run_dir / "errors"
    if not results_dir.exists():
        raise SystemExit(f"Missing results dir: {results_dir}")

    manifest_path = _load_manifest(run_dir, args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jobs = manifest.get("jobs") or []
    expected_ids = [j.get("source_id", "") for j in jobs if j.get("source_id")]

    term_label_counts: Counter[str] = Counter()
    axis_counts: Counter[str] = Counter()
    intensity_counts: Counter[str] = Counter()

    qualities_total = 0
    qualities_with_degree = 0
    entries_with_quality = 0
    entries_with_degree = 0
    valid_results = 0
    invalid_json = 0
    source_id_mismatches = 0
    normalization_anomalies = 0
    substance_part_anomalies = 0
    generic_quality_property_count = 0

    missing_result_ids: list[str] = []
    invalid_examples: list[str] = []

    for source_id in expected_ids:
        fp = results_dir / f"{source_id}.json"
        if not fp.exists():
            missing_result_ids.append(source_id)
            continue

        try:
            obj = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            invalid_json += 1
            invalid_examples.append(source_id)
            continue

        valid_results += 1
        if obj.get("source_id") != source_id:
            source_id_mismatches += 1

        terms = obj.get("terms") or []
        qualities = obj.get("qualities") or []
        if qualities:
            entries_with_quality += 1

        has_degree = False
        for quality in qualities:
            qualities_total += 1
            axis_counts[str(quality.get("axis") or "")] += 1
            intensity_counts[str(quality.get("intensity") or "")] += 1
            if quality.get("degree") is not None:
                has_degree = True
                qualities_with_degree += 1
        if has_degree:
            entries_with_degree += 1

        for term in terms:
            label = str(term.get("label") or "")
            term_label_counts[label] += 1

            if label == "QUALITY_PROPERTY":
                lemma_norm = (term.get("lemma_normalized") or "").strip()
                if lemma_norm in {"δυναμις", "ουσια"}:
                    generic_quality_property_count += 1

            if label == "SUBSTANCE_PART":
                if (
                    (term.get("lemma_gr") or "") != ""
                    or (term.get("lemma_normalized") or "") != ""
                    or not (term.get("substance_lemma_normalized") or "")
                    or not (term.get("part_lemma_normalized") or "")
                ):
                    substance_part_anomalies += 1

        normalization_anomalies += len(_validate_normalized_fields(obj))

    result_files = len(list(results_dir.glob("*.json")))
    error_files = len(list(errors_dir.glob("*.txt"))) if errors_dir.exists() else 0
    expected_jobs = len(expected_ids)
    missing_results = len(missing_result_ids)
    degree_ratio = (qualities_with_degree / qualities_total) if qualities_total else 0.0

    alerts: list[str] = []
    if degree_ratio > 0.25:
        alerts.append(
            "High explicit-degree ratio for Dioscorides (>25%); check for over-quantification."
        )
    if generic_quality_property_count > 0:
        alerts.append("Generic QUALITY_PROPERTY terms (δυναμις/ουσια) detected; spot-check context.")
    if normalization_anomalies > 0:
        alerts.append("Normalization anomalies detected; results may have bypassed runner post-validation.")
    if invalid_json > 0:
        alerts.append("Invalid JSON result files detected.")
    if source_id_mismatches > 0:
        alerts.append("source_id mismatches detected.")

    completeness_ok = (missing_results == 0 and invalid_json == 0 and source_id_mismatches == 0)

    summary = {
        "run_dir": str(run_dir),
        "manifest_path": str(manifest_path),
        "run_id": manifest.get("run_id"),
        "expected_jobs": expected_jobs,
        "result_files": result_files,
        "valid_results": valid_results,
        "missing_results": missing_results,
        "missing_result_ids": missing_result_ids,
        "invalid_json": invalid_json,
        "invalid_examples": invalid_examples,
        "source_id_mismatches": source_id_mismatches,
        "error_files": error_files,
        "completeness_ok": completeness_ok,
        "term_label_counts": dict(sorted(term_label_counts.items())),
        "axis_counts": dict(sorted(axis_counts.items())),
        "intensity_counts": dict(sorted(intensity_counts.items())),
        "qualities_total": qualities_total,
        "qualities_with_degree": qualities_with_degree,
        "entries_with_quality": entries_with_quality,
        "entries_with_degree": entries_with_degree,
        "degree_ratio": degree_ratio,
        "generic_quality_property_count": generic_quality_property_count,
        "substance_part_anomalies": substance_part_anomalies,
        "normalization_anomalies": normalization_anomalies,
        "alerts": alerts,
    }

    out_md = Path(args.out_md) if args.out_md else (run_dir / "qc_summary.md")
    out_json = Path(args.out_json) if args.out_json else (run_dir / "qc_summary.json")

    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_md(out_md, summary)

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    if alerts:
        print("Alerts:")
        for alert in alerts:
            print(f"- {alert}")

    if completeness_ok or args.allow_incomplete:
        return 0
    print("ERROR: run is incomplete or has invalid outputs.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

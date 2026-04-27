from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.consolidate_results import consolidate


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "outputs" / "vocab_entries_v3"
LEGACY_RUN = OUTPUT_ROOT / "entries_full_v3"
DIOSC_RUN = OUTPUT_ROOT / "diosc_full_v3"
DIOSC_SMOKE_RUN = OUTPUT_ROOT / "diosc_smoke_v3"
PAUL_RUN = OUTPUT_ROOT / "paul_full_v3"
PAUL_SMOKE_RUN = OUTPUT_ROOT / "paul_smoke_v3"
STATUS_JSON = OUTPUT_ROOT / "status.json"
STATUS_MD = OUTPUT_ROOT / "status.md"
ENTRY_ID_ALIASES = REPO_ROOT / "config" / "vocab_entry_id_aliases.csv"


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def _load_csv_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8", newline="") as f:
        return {(row.get("entry_id") or "").strip() for row in csv.DictReader(f) if row.get("entry_id")}


def _load_aliases(path: Path = ENTRY_ID_ALIASES) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(line for line in f if not line.startswith("#"))
        return {
            (row.get("old_entry_id") or "").strip(): (row.get("new_entry_id") or "").strip()
            for row in reader
            if (row.get("old_entry_id") or "").strip() and (row.get("new_entry_id") or "").strip()
        }


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _scan_run(
    run_dir: Path,
    *,
    expected_ids: set[str],
    entry_id_aliases: dict[str, str],
) -> dict[str, Any]:
    results_dir = run_dir / "results"
    json_files = list(results_dir.glob("*.json")) if results_dir.exists() else []
    tmp_files = list(results_dir.glob("*.json.tmp")) if results_dir.exists() else []
    invalid = 0
    terms = 0
    qualities = 0
    source_ids: set[str] = set()
    current_entry_ids: set[str] = set()

    for path in json_files:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            invalid += 1
            continue
        source_id = (obj.get("source_id") or obj.get("entry_id") or path.stem).strip()
        source_ids.add(source_id)
        current_entry_ids.add(entry_id_aliases.get(source_id, source_id))
        terms += len(obj.get("terms") or [])
        qualities += len(obj.get("qualities") or [])

    jsonl_path = run_dir / "results.jsonl"
    missing_entry_ids = sorted(expected_ids - current_entry_ids)
    extra_result_ids = sorted(current_entry_ids - expected_ids) if expected_ids else []
    return {
        "run_dir": str(run_dir),
        "exists": run_dir.exists(),
        "expected": len(expected_ids),
        "result_files": len(json_files),
        "unique_source_ids": len(source_ids),
        "unique_result_ids": len(current_entry_ids),
        "invalid_json": invalid,
        "tmp_files": len(tmp_files),
        "missing_entry_ids_count": len(missing_entry_ids),
        "missing_entry_ids_first_50": missing_entry_ids[:50],
        "extra_result_ids_count": len(extra_result_ids),
        "extra_result_ids_first_50": extra_result_ids[:50],
        "results_jsonl": str(jsonl_path),
        "results_jsonl_lines": _count_jsonl(jsonl_path),
        "terms": terms,
        "qualities": qualities,
        "complete": bool(expected_ids) and not missing_entry_ids and not extra_result_ids and invalid == 0,
    }


def _load_qc(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "qc_summary.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"error": f"invalid QC JSON: {path}"}


def build_status() -> dict[str, Any]:
    entry_id_aliases = _load_aliases()
    legacy_expected_ids = _load_csv_ids(REPO_ROOT / "data-workbench" / "entries.csv")
    diosc_expected_ids = _load_csv_ids(REPO_ROOT / "data-workbench" / "entries_diosc.csv")
    paul_expected_ids = _load_csv_ids(REPO_ROOT / "data-workbench" / "entries_paul.csv")
    legacy = _scan_run(
        LEGACY_RUN,
        expected_ids=legacy_expected_ids,
        entry_id_aliases=entry_id_aliases,
    )
    diosc = _scan_run(
        DIOSC_RUN,
        expected_ids=diosc_expected_ids,
        entry_id_aliases=entry_id_aliases,
    )
    smoke = _scan_run(
        DIOSC_SMOKE_RUN,
        expected_ids=set(),
        entry_id_aliases=entry_id_aliases,
    )
    paul = _scan_run(
        PAUL_RUN,
        expected_ids=paul_expected_ids,
        entry_id_aliases=entry_id_aliases,
    )
    paul_smoke = _scan_run(
        PAUL_SMOKE_RUN,
        expected_ids=set(),
        entry_id_aliases=entry_id_aliases,
    )
    diosc["qc"] = _load_qc(DIOSC_RUN)
    smoke["qc"] = _load_qc(DIOSC_SMOKE_RUN)
    paul["qc"] = _load_qc(PAUL_RUN)
    paul_smoke["qc"] = _load_qc(PAUL_SMOKE_RUN)

    blockers: list[str] = []
    if not legacy["complete"]:
        blockers.append("legacy extraction is incomplete")
    if legacy["results_jsonl_lines"] != legacy["unique_result_ids"]:
        blockers.append("legacy results.jsonl is stale or missing")
    if not diosc["complete"]:
        blockers.append("Dioscorides full extraction is incomplete")
    if diosc["complete"] and diosc["results_jsonl_lines"] != diosc["unique_result_ids"]:
        blockers.append("Dioscorides results.jsonl is stale or missing")
    if diosc.get("qc") and not diosc["qc"].get("completeness_ok", False):
        blockers.append("Dioscorides QC did not pass completeness")
    if paul_expected_ids:
        if not paul["complete"]:
            blockers.append("Paul full extraction is incomplete")
        if paul["complete"] and paul["results_jsonl_lines"] != paul["unique_result_ids"]:
            blockers.append("Paul results.jsonl is stale or missing")
        if paul.get("qc") and not paul["qc"].get("completeness_ok", False):
            blockers.append("Paul QC did not pass completeness")

    if not diosc["exists"]:
        next_action = "run npm run diosc:vocab:run"
    elif not diosc["complete"]:
        next_action = "resume npm run diosc:vocab:run"
    elif paul_expected_ids and not paul["exists"]:
        next_action = "run npm run paul:vocab:run"
    elif paul_expected_ids and not paul["complete"]:
        next_action = "resume npm run paul:vocab:run"
    elif blockers:
        next_action = "run npm run vocab:consolidate and corpus QC"
    else:
        next_action = "run npm run vocab:import -- --target legacy --dry-run"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "legacy": legacy,
        "dioscorides": diosc,
        "dioscorides_smoke": smoke,
        "paul": paul,
        "paul_smoke": paul_smoke,
        "entry_id_aliases": {
            "path": str(ENTRY_ID_ALIASES),
            "count": len(entry_id_aliases),
        },
        "blockers": blockers,
        "next_action": next_action,
    }


def write_status(status: dict[str, Any]) -> None:
    STATUS_JSON.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Vocab Extraction Status",
        "",
        f"- Generated: `{status['generated_at']}`",
        f"- Next action: `{status['next_action']}`",
        "",
        "## Coverage",
        "",
        "| Corpus | Expected | Results | JSONL lines | Terms | Qualities | Complete |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for label, key in [
        ("Legacy", "legacy"),
        ("Dioscorides", "dioscorides"),
        ("Dioscorides smoke", "dioscorides_smoke"),
        ("Paul", "paul"),
        ("Paul smoke", "paul_smoke"),
    ]:
        item = status[key]
        lines.append(
            f"| {label} | {item['expected']} | {item['unique_result_ids']} | "
            f"{item['results_jsonl_lines']} | {item['terms']} | {item['qualities']} | {item['complete']} |"
        )
    if status["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in status["blockers"])
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_status(_args: argparse.Namespace) -> int:
    status = build_status()
    write_status(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if not status["blockers"] else 1


def cmd_consolidate(_args: argparse.Namespace) -> int:
    summaries = []
    for run_dir in [LEGACY_RUN, DIOSC_RUN, PAUL_RUN]:
        if run_dir.exists() and (run_dir / "results").exists():
            summaries.append(consolidate(run_dir))
    status = build_status()
    write_status(status)
    print(json.dumps({"consolidated": summaries, "status": status}, ensure_ascii=False, indent=2))
    return 0


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def cmd_complete(_args: argparse.Namespace) -> int:
    _run(["python", "-m", "pytest", "tests/", "-q"])
    _run(["npm", "run", "data:validate"])
    _run(["npm", "run", "diosc:entries:validate"])
    _run(["npm", "run", "paul:entries:validate"])
    _run(["npm", "run", "diosc:vocab:run"])
    _run(["npm", "run", "diosc:vocab:qc"])
    _run(["npm", "run", "paul:vocab:run"])
    _run(["npm", "run", "paul:vocab:qc"])
    cmd_consolidate(_args)
    _run([
        "python",
        "scripts/import_vocab_v3.py",
        "--target",
        "legacy",
        "--results",
        str(LEGACY_RUN / "results.jsonl"),
        "--dry-run",
    ])
    if (DIOSC_RUN / "results.jsonl").exists():
        _run([
            "python",
            "scripts/import_vocab_v3.py",
            "--target",
            "legacy",
            "--results",
            str(DIOSC_RUN / "results.jsonl"),
            "--dry-run",
        ])
    if (PAUL_RUN / "results.jsonl").exists():
        _run([
            "python",
            "scripts/import_vocab_v3.py",
            "--target",
            "legacy",
            "--results",
            str(PAUL_RUN / "results.jsonl"),
            "--dry-run",
        ])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Vocab extraction controller.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("consolidate").set_defaults(func=cmd_consolidate)
    sub.add_parser("complete").set_defaults(func=cmd_complete)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_utc")


def _read_ids(ids_file: Path) -> list[str]:
    ids: list[str] = []
    for line in ids_file.read_text(encoding="utf-8", errors="replace").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        ids.append(value)
    if not ids:
        raise SystemExit(f"No ids found in {ids_file}")
    return ids


def _append_log(log_path: Path, text: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def _run(cmd: list[str], *, log_path: Path, cwd: Path | None = None) -> int:
    _append_log(log_path, f"\n[{_utc_stamp()}] RUN: {' '.join(cmd)}\n")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.stdout:
        _append_log(log_path, "STDOUT:\n" + proc.stdout.decode("utf-8", errors="replace"))
    if proc.stderr:
        _append_log(log_path, "STDERR:\n" + proc.stderr.decode("utf-8", errors="replace"))
    _append_log(log_path, f"[{_utc_stamp()}] EXIT: {proc.returncode}\n")
    return proc.returncode


@dataclass(frozen=True)
class ModelRun:
    run_id: str
    model: str
    reasoning_effort: str
    timeout_s: int


def _prepare_jobs(
    *,
    run_root: Path,
    ids_file: Path,
    session_id: str,
    log_path: Path,
) -> Path:
    runner = _repo_root() / "scripts" / "vocab_multi_agent_pilot.py"
    if not runner.exists():
        raise SystemExit(f"Missing pilot script: {runner}")

    cmd = [
        sys.executable,
        str(runner),
        "--ids-file",
        str(ids_file),
        "--outdir",
        str(run_root.parent),
        "--run-id",
        run_root.name,
        "--session-id",
        session_id,
        "--prepare-only",
    ]
    code = _run(cmd, log_path=log_path, cwd=_repo_root())
    if code != 0:
        raise SystemExit(f"Prepare-only failed (exit={code}); see log at {log_path}")

    manifest_path = run_root / f"manifest_{session_id}.json"
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found after prepare-only: {manifest_path}")
    return manifest_path


def _load_manifest(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _ensure_clean_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _run_one_model(
    *,
    model_run: ModelRun,
    manifest: dict,
    out_root: Path,
    schema_path: Path,
    log_path: Path,
    resume: bool,
) -> Path:
    run_root = out_root / model_run.run_id
    results_dir = run_root / "results"
    errors_dir = run_root / "errors"
    _ensure_clean_dir(results_dir)
    _ensure_clean_dir(errors_dir)

    agent_runner = _repo_root() / "scripts" / "vocab_agent_runner.py"
    if not agent_runner.exists():
        raise SystemExit(f"Missing agent runner: {agent_runner}")

    jobs = manifest.get("jobs") or []
    if not jobs:
        raise SystemExit("Manifest contained no jobs.")

    _append_log(
        log_path,
        (
            f"\n[{_utc_stamp()}] MODEL_RUN_START {model_run.run_id}\n"
            f"- model: {model_run.model}\n"
            f"- model_reasoning_effort: {model_run.reasoning_effort}\n"
            f"- timeout_s: {model_run.timeout_s}\n"
            f"- resume: {resume}\n"
        ),
    )

    ok = 0
    failed = 0
    started = time.time()

    for job in jobs:
        source_id = job["source_id"]
        job_prompt = Path(job["job_prompt"])
        out_path = results_dir / f"{source_id}.json"
        err_path = errors_dir / f"{source_id}.txt"

        if resume and out_path.exists() and out_path.stat().st_size > 0:
            _append_log(log_path, f"[{_utc_stamp()}] SKIP (resume) {model_run.run_id} {source_id}\n")
            continue

        cmd = [
            sys.executable,
            str(agent_runner),
            "--job",
            str(job_prompt),
            "--out",
            str(out_path),
            "--expected-source-id",
            source_id,
            "--schema",
            str(schema_path),
            "--timeout",
            str(model_run.timeout_s),
            "--model",
            model_run.model,
            "-c",
            f"model_reasoning_effort={json.dumps(model_run.reasoning_effort)}",
        ]

        t0 = time.time()
        _append_log(log_path, f"[{_utc_stamp()}] START {model_run.run_id} {source_id}\n")
        proc = subprocess.run(cmd, cwd=str(_repo_root()), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dt = time.time() - t0

        if proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
            ok += 1
            _append_log(log_path, f"[{_utc_stamp()}] OK {model_run.run_id} {source_id} ({dt:.1f}s)\n")
            continue

        failed += 1
        payload = []
        payload.append(f"Runner failed for source_id={source_id}")
        payload.append(f"model_run={model_run.run_id}")
        payload.append(f"elapsed_s={dt:.1f}")
        payload.append("\nSTDOUT:\n" + proc.stdout.decode("utf-8", errors="replace"))
        payload.append("\nSTDERR:\n" + proc.stderr.decode("utf-8", errors="replace"))
        err_path.write_text("\n".join(payload).strip() + "\n", encoding="utf-8")
        _append_log(log_path, f"[{_utc_stamp()}] FAIL {model_run.run_id} {source_id} ({dt:.1f}s)\n")

    total_dt = time.time() - started
    _append_log(
        log_path,
        f"[{_utc_stamp()}] MODEL_RUN_END {model_run.run_id} ok={ok} failed={failed} elapsed_s={total_dt:.1f}\n",
    )
    return results_dir


def _summarize_results(results_dir: Path, ids: list[str]) -> dict:
    terms_total = 0
    qualities_total = 0
    ok = 0
    missing = 0

    for sid in ids:
        fp = results_dir / f"{sid}.json"
        if not fp.exists() or fp.stat().st_size == 0:
            missing += 1
            continue
        try:
            obj = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            missing += 1
            continue
        ok += 1
        terms_total += len(obj.get("terms") or [])
        qualities_total += len(obj.get("qualities") or [])

    avg_terms = (terms_total / ok) if ok else 0.0
    avg_qualities = (qualities_total / ok) if ok else 0.0
    return {
        "ok": ok,
        "missing_or_invalid": missing,
        "avg_terms_per_entry": avg_terms,
        "avg_qualities_per_entry": avg_qualities,
    }


def _missing_ids(results_dir: Path, ids: list[str]) -> list[str]:
    missing: list[str] = []
    for sid in ids:
        fp = results_dir / f"{sid}.json"
        if not fp.exists() or fp.stat().st_size == 0:
            missing.append(sid)
            continue
        try:
            json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            missing.append(sid)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a small vocab extraction model eval with logging.")
    ap.add_argument("--ids-file", required=True, help="File with SOURCE_IDs (one per line).")
    ap.add_argument(
        "--baseline-results-dir",
        default=str(_repo_root() / "outputs/vocab_entries_v3/entries_full_v3/results"),
        help="Baseline per-entry JSON dir (contains <source_id>.json).",
    )
    ap.add_argument(
        "--out-root",
        default=str(_repo_root() / "outputs/vocab_entries_v3/model_eval"),
        help="Output root for model eval runs.",
    )
    ap.add_argument(
        "--schema",
        default=str(_repo_root() / "schemas/vocab_term_extractor_with_degrees.schema.json"),
        help="JSON schema file for codex exec validation.",
    )
    ap.add_argument(
        "--log",
        default=None,
        help="Append log to this path (default: <out_root>/log.md).",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Skip entries whose per-entry result JSON already exists and is non-empty.",
    )
    ap.add_argument(
        "--timeout-high",
        type=int,
        default=600,
        help="Timeout seconds per entry for high effort runs.",
    )
    ap.add_argument(
        "--timeout-xhigh",
        type=int,
        default=900,
        help="Timeout seconds per entry for xhigh effort runs.",
    )
    args = ap.parse_args()

    ids_file = Path(args.ids_file)
    baseline_results_dir = Path(args.baseline_results_dir)
    out_root = Path(args.out_root)
    schema_path = Path(args.schema)
    log_path = Path(args.log) if args.log else (out_root / "log.md")

    if not ids_file.exists():
        raise SystemExit(f"ids file not found: {ids_file}")
    if not baseline_results_dir.exists():
        raise SystemExit(f"baseline results dir not found: {baseline_results_dir}")
    if not schema_path.exists():
        raise SystemExit(f"schema not found: {schema_path}")

    ids = _read_ids(ids_file)

    _append_log(
        log_path,
        (
            f"\n# Vocab Model Eval Log\n\n"
            f"[{_utc_stamp()}] START\n\n"
            f"Decisions:\n"
            f"- Use ids_file={ids_file}\n"
            f"- Use baseline_results_dir={baseline_results_dir}\n"
            f"- Use schema={schema_path}\n"
            f"- Per-entry timeouts: high={args.timeout_high}s, xhigh={args.timeout_xhigh}s\n"
            f"- Run sequential per entry (parallel=1) for easier logging\n"
        ),
    )

    out_root.mkdir(parents=True, exist_ok=True)

    prep_run_id = f"_prep_{_utc_id()}"
    prep_session_id = prep_run_id
    prep_root = out_root / prep_run_id

    _append_log(log_path, f"\n[{_utc_stamp()}] PREPARE_JOBS run_id={prep_run_id}\n")
    manifest_path = _prepare_jobs(
        run_root=prep_root,
        ids_file=ids_file,
        session_id=prep_session_id,
        log_path=log_path,
    )
    manifest = _load_manifest(manifest_path)

    # Model runs (the ones you asked for).
    runs = [
        ModelRun(
            run_id=f"gpt_5_2_high_{_utc_id()}",
            model="gpt-5.2",
            reasoning_effort="high",
            timeout_s=int(args.timeout_high),
        ),
        ModelRun(
            run_id=f"gpt_5_2_xhigh_{_utc_id()}",
            model="gpt-5.2",
            reasoning_effort="xhigh",
            timeout_s=int(args.timeout_xhigh),
        ),
        ModelRun(
            run_id=f"codex_5_3_high_{_utc_id()}",
            model="gpt-5.3-codex",
            reasoning_effort="high",
            timeout_s=int(args.timeout_high),
        ),
    ]

    compare_script = _repo_root() / "scripts" / "compare_extraction_runs.py"
    if not compare_script.exists():
        raise SystemExit(f"Missing compare script: {compare_script}")

    reports_dir = out_root / "reports"
    diffs_dir = out_root / "diffs"
    reports_dir.mkdir(parents=True, exist_ok=True)
    diffs_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, dict] = {"ids_file": str(ids_file), "runs": {}}

    for r in runs:
        results_dir = _run_one_model(
            model_run=r,
            manifest=manifest,
            out_root=out_root,
            schema_path=schema_path,
            log_path=log_path,
            resume=bool(args.resume),
        )

        # Compare vs baseline.
        report_path = reports_dir / f"{r.run_id}_vs_baseline.md"
        out_diffs = diffs_dir / r.run_id
        out_diffs.mkdir(parents=True, exist_ok=True)

        missing = _missing_ids(results_dir, ids)
        if missing:
            _append_log(
                log_path,
                f"[{_utc_stamp()}] SKIP_COMPARE {r.run_id} missing_results={len(missing)} sample={missing[:5]}\n",
            )
        else:
            cmd = [
                sys.executable,
                str(compare_script),
                "--run-a",
                str(baseline_results_dir),
                "--run-b",
                str(results_dir),
                "--ids-file",
                str(ids_file),
                "--out-report",
                str(report_path),
                "--out-diffs-dir",
                str(out_diffs),
                "--label-a",
                "baseline",
                "--label-b",
                r.run_id,
            ]
            code = _run(cmd, log_path=log_path, cwd=_repo_root())
            if code != 0:
                _append_log(log_path, f"[{_utc_stamp()}] WARNING compare failed for {r.run_id}\n")

        summary["runs"][r.run_id] = {
            "model": r.model,
            "model_reasoning_effort": r.reasoning_effort,
            "timeout_s": r.timeout_s,
            "results_dir": str(results_dir),
            "report_path": str(report_path),
            "diffs_dir": str(out_diffs),
            "stats": _summarize_results(results_dir, ids),
        }

    summary_path = out_root / f"summary_{_utc_id()}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _append_log(log_path, f"\n[{_utc_stamp()}] WROTE summary={summary_path}\n")
    _append_log(log_path, f"[{_utc_stamp()}] END\n")

    print(f"Wrote log:     {log_path}")
    print(f"Wrote summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

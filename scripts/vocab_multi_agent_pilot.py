#!/usr/bin/env python3

import argparse
import csv
import json
import re
import subprocess
import sys
import time
import threading
from queue import Queue, Empty
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
_STREAM_DISCONNECT_RE = re.compile(r"stream disconnected before completion", re.IGNORECASE)


def _safe_filename(value: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("_", value.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "row"


def _utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_utc")


_USAGE_LIMIT_RE = re.compile(r"\"resets_in_seconds\"\\s*:\\s*(\\d+)")


def _utc_session_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_utc")


def _read_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue


def _extract_usage_from_codex_home(codex_home: Path) -> dict | None:
    sessions_dir = codex_home / ".codex" / "sessions"
    if not sessions_dir.exists():
        return None

    rollouts = sorted(sessions_dir.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not rollouts:
        return None

    rollout = rollouts[-1]
    start_secondary = None
    end_secondary = None
    last_usage = None
    total_usage = None

    for obj in _read_jsonl(rollout):
        if obj.get("type") != "event_msg":
            continue
        payload = obj.get("payload") or {}
        if payload.get("type") != "token_count":
            continue

        rate_limits = payload.get("rate_limits") or {}
        secondary = rate_limits.get("secondary") or {}
        used_percent = secondary.get("used_percent")
        if start_secondary is None and used_percent is not None:
            start_secondary = used_percent

        info = payload.get("info")
        if isinstance(info, dict):
            if used_percent is not None:
                end_secondary = used_percent
            last_usage = info.get("last_token_usage") or last_usage
            total_usage = info.get("total_token_usage") or total_usage

    return {
        "rollout": str(rollout),
        "start_secondary_used_percent": start_secondary,
        "end_secondary_used_percent": end_secondary,
        "last_token_usage": last_usage,
        "total_token_usage": total_usage,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Orchestrate a 5-row multi-agent pilot run for vocab extraction."
    )
    ap.add_argument(
        "--csv",
        default=str(_repo_root() / "data-workbench/entries.csv"),
        help="CSV file with entries.",
    )
    ap.add_argument(
        "--prompt",
        default=str(_repo_root() / "docs/prompts/vocab_term_extractor_with_degrees.md"),
        help="Base prompt markdown file.",
    )
    ap.add_argument("--n", type=int, default=5, help="Number of entries to run.")
    ap.add_argument(
        "--session-id",
        default=None,
        help="Session id for this invocation (used to name manifest + job folder).",
    )
    ap.add_argument(
        "--outdir",
        default=str(_repo_root() / "outputs/vocab_entries_v3/pilot_runs"),
        help="Output directory root.",
    )
    ap.add_argument("--run-id", default=None, help="Optional run id (folder name).")
    ap.add_argument(
        "--id-col",
        default="entry_id",
        help="CSV column name for SOURCE_ID.",
    )
    ap.add_argument(
        "--text-col",
        default="greek",
        help="CSV column name for Greek TEXT.",
    )
    ap.add_argument(
        "--id-prefix",
        default=None,
        help="If set, only process rows whose SOURCE_ID starts with this prefix (case-sensitive).",
    )
    ap.add_argument(
        "--id-regex",
        default=None,
        help="If set, only process rows whose SOURCE_ID matches this regex.",
    )
    ap.add_argument(
        "--ids-file",
        default=None,
        help="If set, only process SOURCE_IDs listed in this file (one per line).",
    )
    ap.add_argument(
        "--prepare-only",
        action="store_true",
        help="Only write job files + manifest, do not invoke the agent.",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Skip jobs that already have a result file.",
    )
    ap.add_argument(
        "--schema",
        default=str(_repo_root() / "schemas/vocab_term_extractor_with_degrees.schema.json"),
        help="JSON schema file passed through to the agent runner.",
    )
    ap.add_argument("--model", default=None, help="Optional model name for codex exec.")
    ap.add_argument(
        "--oss",
        action="store_true",
        help="Use Codex OSS provider (requires a local LM Studio/Ollama server).",
    )
    ap.add_argument(
        "--local-provider",
        default=None,
        help="Local OSS provider (lmstudio, ollama, or ollama-chat).",
    )
    ap.add_argument(
        "-c",
        "--config",
        action="append",
        default=[],
        help="Repeatable Codex `-c key=value` overrides (passed through to the runner).",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout (seconds) per entry.",
    )
    ap.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of concurrent agent runs.",
    )
    ap.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries per failed entry (non-schema failures).",
    )
    ap.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        help="Exponential backoff base (seconds) between retries.",
    )
    ap.add_argument(
        "--usage-limit-max-waits",
        type=int,
        default=10,
        help="Max times to wait for `usage_limit_reached` resets before failing an entry.",
    )
    ap.add_argument(
        "--usage-limit-policy",
        choices=["wait", "stop", "fail"],
        default="wait",
        help="What to do when `usage_limit_reached` occurs: wait, stop the whole session, or fail and continue.",
    )
    ap.add_argument(
        "--usage-limit-stop-threshold",
        type=int,
        default=600,
        help="If policy=stop, only stop when resets_in_seconds >= this threshold.",
    )

    args = ap.parse_args()

    csv_path = Path(args.csv)
    prompt_path = Path(args.prompt)
    schema_path = Path(args.schema)

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")
    if not prompt_path.exists():
        raise SystemExit(f"Prompt not found: {prompt_path}")
    if not schema_path.exists():
        raise SystemExit(f"Schema not found: {schema_path}")

    run_id = args.run_id or _utc_run_id()
    run_root = Path(args.outdir) / run_id
    jobs_dir = run_root / "jobs"
    results_dir = run_root / "results"
    errors_dir = run_root / "errors"
    usage_dir = run_root / "usage"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    errors_dir.mkdir(parents=True, exist_ok=True)
    usage_dir.mkdir(parents=True, exist_ok=True)

    prompt_base = prompt_path.read_text(encoding="utf-8")

    session_id = args.session_id or _utc_session_id()
    jobs_session_dir = jobs_dir / session_id
    jobs_session_dir.mkdir(parents=True, exist_ok=True)

    existing_results: set[str] = set()
    if args.resume and not args.ids_file:
        existing_results = {p.stem for p in results_dir.glob("*.json")}

    ids_set: set[str] | None = None
    if args.ids_file:
        ids_path = Path(args.ids_file)
        ids = []
        for line in ids_path.read_text(encoding="utf-8", errors="replace").splitlines():
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            ids.append(value)
        ids_set = set(ids)
        if not ids_set:
            raise SystemExit(f"--ids-file provided but contained no ids: {ids_path}")

    selected = []
    id_re = re.compile(args.id_regex) if args.id_regex else None
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if args.id_col not in reader.fieldnames:
            raise SystemExit(f"Missing id col {args.id_col!r} in CSV header.")
        if args.text_col not in reader.fieldnames:
            raise SystemExit(f"Missing text col {args.text_col!r} in CSV header.")

        prev_by_source: dict[str, tuple[str, str]] = {}
        for row_i, row in enumerate(reader, start=2):  # header is line 1
            source_id = (row.get(args.id_col) or "").strip()
            text = (row.get(args.text_col) or "").strip()
            source = (row.get("source") or "").strip()
            if not source_id or not text:
                continue

            prev = prev_by_source.get(source)
            prev_by_source[source] = (source_id, text)

            if ids_set is not None and source_id not in ids_set:
                continue
            if existing_results and source_id in existing_results:
                continue
            if args.id_prefix and not source_id.startswith(args.id_prefix):
                continue
            if id_re and not id_re.search(source_id):
                continue
            selected.append((row_i, source_id, text, prev))
            if ids_set is not None:
                if len(selected) >= len(ids_set):
                    break
            else:
                if len(selected) >= args.n:
                    break

    if not selected:
        raise SystemExit("No non-empty rows found to run.")

    if ids_set is not None:
        found = {sid for _, sid, _, _ in selected}
        missing = sorted(ids_set - found)
        if missing:
            raise SystemExit(f"--ids-file ids not found in CSV (with non-empty text): {missing[:20]}")

    manifest = {
        "run_id": run_id,
        "session_id": session_id,
        "csv": str(csv_path),
        "prompt": str(prompt_path),
        "schema": str(schema_path),
        "n_requested": args.n,
        "n_selected": len(selected),
        "jobs": [],
    }

    for row_i, source_id, text, prev in selected:
        safe_id = _safe_filename(source_id)
        job_path = jobs_session_dir / f"{safe_id}.prompt.md"
        result_path = results_dir / f"{safe_id}.json"
        error_path = errors_dir / f"{safe_id}.txt"

        if prev:
            prev_source_id, prev_text = prev
            context_block = (
                "\n\n---\n\n## CONTEXT (for anaphora; use only if explicitly signalled in TEXT)\n"
                + f"CONTEXT_PREV_SOURCE_ID: {prev_source_id}\n"
                + "CONTEXT_PREV_TEXT:\n"
                + prev_text
                + "\n"
            )
        else:
            context_block = "\n\n---\n\n## CONTEXT\n(none)\n"

        job_text = (
            prompt_base
            + context_block
            + "\n\n---\n\n## INPUT (authoritative)\n"
            + "Use the following SOURCE_ID and TEXT (ignore any placeholders above).\n\n"
            + f"SOURCE_ID: {source_id}\n"
            + "TEXT:\n"
            + text
            + "\n"
        )
        job_path.write_text(job_text, encoding="utf-8")

        manifest["jobs"].append(
            {
                "csv_line": row_i,
                "source_id": source_id,
                "job_prompt": str(job_path),
                "result_json": str(result_path),
                "error_txt": str(error_path),
            }
        )

    manifest_path = run_root / f"manifest_{session_id}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.prepare_only:
        print(f"Wrote {len(selected)} jobs for review: {manifest_path}")
        return 0

    runner_path = _repo_root() / "scripts/vocab_agent_runner.py"
    if not runner_path.exists():
        raise SystemExit(f"Runner script not found: {runner_path}")

    progress_lock = threading.Lock()
    block_lock = threading.Lock()
    block_cond = threading.Condition(block_lock)
    blocked_until = 0.0
    stop_event = threading.Event()
    stop_reason = {"message": None}

    completed = 0
    failed = 0
    skipped = 0

    def set_block(seconds: int) -> None:
        nonlocal blocked_until
        until = time.time() + seconds + 5
        with block_cond:
            if until > blocked_until:
                blocked_until = until
            block_cond.notify_all()

    def wait_if_blocked() -> None:
        nonlocal blocked_until
        with block_cond:
            while True:
                now = time.time()
                if now >= blocked_until:
                    return
                remaining = blocked_until - now
                block_cond.wait(timeout=remaining)

    def run_one(job: dict) -> tuple[str, int]:
        source_id = job["source_id"]
        result_path = Path(job["result_json"])
        error_path = Path(job["error_txt"])
        job_prompt = job["job_prompt"]

        if args.resume and result_path.exists():
            return (source_id, 0)

        cmd = [
            sys.executable,
            str(runner_path),
            "--job",
            job_prompt,
            "--out",
            str(result_path),
            "--expected-source-id",
            source_id,
            "--schema",
            str(schema_path),
            "--timeout",
            str(args.timeout),
        ]
        if args.model:
            cmd.extend(["--model", args.model])
        if args.oss:
            cmd.append("--oss")
        if args.local_provider:
            cmd.extend(["--local-provider", args.local_provider])
        for item in args.config:
            cmd.extend(["-c", item])

        attempts = max(1, int(args.retries) + 1)
        last_code = 1
        usage_waits = 0
        last_out = ""
        last_err = ""

        attempt = 1
        while attempt <= attempts:
            if stop_event.is_set():
                return (source_id, 2)
            wait_if_blocked()
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode == 0:
                return (source_id, 0)

            last_code = proc.returncode
            last_out = proc.stdout.decode("utf-8", errors="replace")
            last_err = proc.stderr.decode("utf-8", errors="replace")
            lower_err = last_err.lower()

            # Hard stop: schema / invalid request errors won't succeed on retry.
            if "invalid_json_schema" in lower_err or "invalid_request_error" in lower_err:
                break

            # If plan usage limit is reached, wait until reset and retry (does not count as an attempt).
            if "usage_limit_reached" in lower_err:
                m = _USAGE_LIMIT_RE.search(last_err)
                if m:
                    resets_in_seconds = int(m.group(1))
                    if args.usage_limit_policy == "stop" and resets_in_seconds >= int(
                        args.usage_limit_stop_threshold
                    ):
                        stop_reason["message"] = f"usage_limit_reached (resets_in_seconds={resets_in_seconds})"
                        stop_event.set()
                        break
                    if args.usage_limit_policy == "fail":
                        break
                    usage_waits += 1
                    if usage_waits > int(args.usage_limit_max_waits):
                        break
                    set_block(resets_in_seconds)
                    continue

            # Transient stream/network issues are common under load; retry with backoff.
            if _STREAM_DISCONNECT_RE.search(last_err):
                if attempt < attempts:
                    sleep_s = float(args.retry_backoff) * (2 ** (attempt - 1))
                    time.sleep(sleep_s)
                attempt += 1
                continue

            # Normal retry backoff.
            if attempt < attempts:
                sleep_s = float(args.retry_backoff) * (2 ** (attempt - 1))
                time.sleep(sleep_s)
            attempt += 1

        error_path.write_text(
            f"Runner failed for source_id={source_id}\n\nSTDOUT:\n{last_out}\n\nSTDERR:\n{last_err}\n",
            encoding="utf-8",
        )
        return (source_id, last_code)

    # Work queue so we can coordinate waits across workers.
    to_run = []
    for job in manifest["jobs"]:
        rp = Path(job["result_json"])
        if args.resume and rp.exists():
            continue
        to_run.append(job)

    total = len(to_run) + sum(
        1 for job in manifest["jobs"] if args.resume and Path(job["result_json"]).exists()
    )
    q: Queue[dict] = Queue()
    for job in to_run:
        q.put(job)

    def worker() -> None:
        nonlocal completed, failed, skipped
        while True:
            if stop_event.is_set():
                # Drain remaining tasks without writing errors/results so they can be picked up in a future session.
                while True:
                    try:
                        job = q.get_nowait()
                    except Empty:
                        return
                    with progress_lock:
                        skipped += 1
                        done = completed + failed + skipped
                        if done % 25 == 0 or done == total:
                            print(
                                f"Progress: {done}/{total} (ok={completed}, failed={failed}, skipped={skipped})"
                            )
                    q.task_done()
                return
            try:
                job = q.get_nowait()
            except Empty:
                return
            try:
                _, code = run_one(job)
                with progress_lock:
                    if code == 0:
                        completed += 1
                    else:
                        failed += 1
                    done = completed + failed + skipped
                    if done % 25 == 0 or done == total:
                        print(
                            f"Progress: {done}/{total} (ok={completed}, failed={failed}, skipped={skipped})"
                        )
            finally:
                q.task_done()

    parallelism = max(1, int(args.parallel))
    with ThreadPoolExecutor(max_workers=parallelism) as ex:
        for _ in range(parallelism):
            ex.submit(worker)
        q.join()

    # Consolidate succeeded results as JSONL for easy review.
    jsonl_path = run_root / "results.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as out:
        for job in manifest["jobs"]:
            result_path = Path(job["result_json"])
            if not result_path.exists():
                continue
            try:
                obj = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")

    # Usage summary for this session (best-effort).
    usage_summary = {
        "run_id": run_id,
        "session_id": session_id,
        "jobs": [],
        "totals": {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "total_tokens": 0,
        },
        "secondary_used_percent": {"start_min": None, "end_max": None},
    }
    for job in manifest["jobs"]:
        safe_id = Path(job["result_json"]).stem
        codex_home = run_root / "_codex_home" / safe_id
        info = _extract_usage_from_codex_home(codex_home)
        if not info:
            continue
        usage_summary["jobs"].append({"source_id": job["source_id"], "safe_id": safe_id, "usage": info})
        last = info.get("last_token_usage") or {}
        for k in usage_summary["totals"].keys():
            usage_summary["totals"][k] += int(last.get(k) or 0)

        start_pct = info.get("start_secondary_used_percent")
        end_pct = info.get("end_secondary_used_percent")
        s = usage_summary["secondary_used_percent"]["start_min"]
        e = usage_summary["secondary_used_percent"]["end_max"]
        if start_pct is not None:
            usage_summary["secondary_used_percent"]["start_min"] = start_pct if s is None else min(s, start_pct)
        if end_pct is not None:
            usage_summary["secondary_used_percent"]["end_max"] = end_pct if e is None else max(e, end_pct)

    usage_path = usage_dir / f"usage_{session_id}.json"
    usage_path.write_text(json.dumps(usage_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if stop_event.is_set():
        print(f"Stopped early: {stop_reason['message']}")
    print(f"Pilot complete: {completed} succeeded, {failed} failed, {skipped} skipped.")
    print(f"Review manifest: {manifest_path}")
    print(f"Review outputs:  {jsonl_path}")
    print(f"Usage summary:   {usage_path}")
    if failed:
        print(f"Review errors:   {errors_dir}")
    print("Waiting for human review (no further entries will be processed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

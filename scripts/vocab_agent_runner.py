#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _extract_json(text: str) -> dict:
    candidate = text.strip()
    if candidate.startswith("```"):
        left = candidate.find("{")
        right = candidate.rfind("}")
        if left != -1 and right != -1 and right > left:
            candidate = candidate[left : right + 1].strip()
    return json.loads(candidate)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run a single vocab extraction job via Codex and write strict JSON output."
    )
    ap.add_argument("--job", required=True, help="Path to job prompt markdown file.")
    ap.add_argument("--out", required=True, help="Path to write validated JSON output.")
    ap.add_argument(
        "--expected-source-id",
        default=None,
        help="If set, require output.source_id to match.",
    )
    ap.add_argument(
        "--schema",
        default=str(_repo_root() / "schemas/vocab_term_extractor_with_degrees.schema.json"),
        help="JSON schema file passed to `codex exec --output-schema`.",
    )
    ap.add_argument("--model", default=None, help="Optional model name for codex exec.")
    ap.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout (seconds) for the agent run.",
    )
    ap.add_argument("--codex-bin", default="codex", help="Codex CLI binary name/path.")
    ap.add_argument(
        "--sandbox",
        default="read-only",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Codex sandbox mode.",
    )
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
        help="Repeatable Codex `-c key=value` overrides.",
    )
    ap.add_argument(
        "--codex-home",
        default=None,
        help=(
            "Writable HOME directory for Codex to store sessions/cache. "
            "Defaults to <run_root>/_codex_home when --out is under outputs/*/<run_id>/results/."
        ),
    )

    args = ap.parse_args()

    job_path = Path(args.job)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = Path(args.schema)
    if not schema_path.exists():
        raise SystemExit(f"Schema file not found: {schema_path}")

    job_text = job_path.read_text(encoding="utf-8")
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")

    # In this environment, writes outside the workspace (e.g. ~/.codex) are blocked.
    # Point Codex at a writable HOME and (optionally) seed it from the user's real ~/.codex.
    if args.codex_home:
        codex_home = Path(args.codex_home)
    else:
        # Typical layout: outputs/<name>/<run_id>/results/<source_id>.json
        # Use a per-job HOME to avoid concurrent Codex state races (e.g. skills install).
        codex_home = (out_path.parent.parent / "_codex_home" / out_path.stem).resolve()

    codex_state_dir = codex_home / ".codex"
    codex_state_dir.mkdir(parents=True, exist_ok=True)

    real_state_dir = Path.home() / ".codex"
    for filename in ["config.toml", "auth.json"]:
        dst = codex_state_dir / filename
        src = real_state_dir / filename
        if not dst.exists() and src.exists():
            try:
                dst.symlink_to(src)
            except Exception:
                dst.write_bytes(src.read_bytes())

    env = os.environ.copy()
    env["HOME"] = str(codex_home)

    cmd = [
        args.codex_bin,
        "exec",
        "-C",
        str(_repo_root()),
        "--sandbox",
        args.sandbox,
        "--color",
        "never",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(tmp_path),
        "-",
    ]
    if args.model:
        cmd[2:2] = ["-m", args.model]
    if args.oss:
        cmd[2:2] = ["--oss"]
    if args.local_provider:
        cmd[2:2] = ["--local-provider", args.local_provider]
    if args.config:
        # Insert after `exec` so overrides apply to this invocation.
        insert_at = 2
        for item in args.config:
            cmd[insert_at:insert_at] = ["-c", item]
            insert_at += 2

    proc = subprocess.run(
        cmd,
        input=job_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=args.timeout,
        env=env,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        stdout = proc.stdout.decode("utf-8", errors="replace")
        msg = (
            f"codex exec failed (exit={proc.returncode}).\n\nSTDERR:\n{stderr}\n\nSTDOUT:\n{stdout}"
        )
        raise RuntimeError(msg)

    raw = tmp_path.read_text(encoding="utf-8", errors="replace")
    try:
        obj = _extract_json(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to parse strict JSON from {tmp_path}: {e}\n\nRaw:\n{raw}")

    if args.expected_source_id and obj.get("source_id") != args.expected_source_id:
        raise RuntimeError(
            f"source_id mismatch: expected {args.expected_source_id}, got {obj.get('source_id')}"
        )

    out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        tmp_path.unlink(missing_ok=True)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

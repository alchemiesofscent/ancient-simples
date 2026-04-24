#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Any


_THIS_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGES_PATH = _THIS_REPO_ROOT / "packages"
if str(_PACKAGES_PATH) not in sys.path:
    sys.path.insert(0, str(_PACKAGES_PATH))

from textutils import normalize as normalize_greek


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


def _fix_normalized_fields(obj: dict[str, Any]) -> None:
    """Re-normalize all normalized fields in-place so LLM output
    that is close-but-not-quite (e.g. retained iota subscripts) is
    corrected before validation instead of rejected."""

    _TERM_NORM_KEYS = [
        "normalized", "lemma_normalized", "head_lemma_normalized",
        "substance_lemma_normalized", "part_lemma_normalized",
        "variant_place_lemma_normalized",
    ]
    _APPLIES_TO_KEYS = [
        "lemma_normalized", "substance_lemma_normalized", "part_lemma_normalized",
    ]

    for term in obj.get("terms") or []:
        # Fix display→normalized
        display = term.get("display", "")
        if display:
            term["normalized"] = normalize_greek(display)
        # Fix lemma_gr→lemma_normalized
        lemma_gr = term.get("lemma_gr", "")
        if lemma_gr.strip():
            term["lemma_normalized"] = normalize_greek(lemma_gr)
        # Fix all other normalized keys
        for key in _TERM_NORM_KEYS:
            val = term.get(key)
            if isinstance(val, str) and val:
                term[key] = normalize_greek(val)
        # Fix applies_to
        applies_to = term.get("applies_to") or {}
        for key in _APPLIES_TO_KEYS:
            val = applies_to.get(key)
            if isinstance(val, str) and val:
                applies_to[key] = normalize_greek(val)

    for quality in obj.get("qualities") or []:
        # Fix evidence_display→evidence_normalized
        ev_display = quality.get("evidence_display", "")
        if ev_display:
            quality["evidence_normalized"] = normalize_greek(ev_display)
        # Fix other normalized keys
        for key in ["evidence_normalized", "variant_place_lemma_normalized"]:
            val = quality.get(key)
            if isinstance(val, str) and val:
                quality[key] = normalize_greek(val)
        # Fix applies_to
        applies_to = quality.get("applies_to") or {}
        for key in _APPLIES_TO_KEYS:
            val = applies_to.get(key)
            if isinstance(val, str) and val:
                applies_to[key] = normalize_greek(val)


def _validate_normalized_value(path: str, value: str, issues: list[str]) -> None:
    expected = normalize_greek(value)
    if value != expected:
        issues.append(f"{path}: expected normalized form {expected!r}, got {value!r}")


def _validate_extraction_obj(obj: dict[str, Any]) -> None:
    issues: list[str] = []

    terms = obj.get("terms") or []
    for idx, term in enumerate(terms):
        path = f"terms[{idx}]"
        label = term.get("label")

        display = term.get("display", "")
        normalized = term.get("normalized", "")
        if normalize_greek(display) != normalized:
            issues.append(
                f"{path}.normalized: must equal normalize(display); expected {normalize_greek(display)!r}, got {normalized!r}"
            )

        lemma_gr = term.get("lemma_gr", "")
        lemma_normalized = term.get("lemma_normalized", "")
        if lemma_gr.strip():
            expected_lemma_norm = normalize_greek(lemma_gr)
            if lemma_normalized != expected_lemma_norm:
                issues.append(
                    f"{path}.lemma_normalized: must equal normalize(lemma_gr); expected {expected_lemma_norm!r}, got {lemma_normalized!r}"
                )
        elif lemma_normalized != "":
            issues.append(
                f"{path}.lemma_normalized: must be empty string when lemma_gr is empty; got {lemma_normalized!r}"
            )

        for key in [
            "normalized",
            "lemma_normalized",
            "head_lemma_normalized",
            "substance_lemma_normalized",
            "part_lemma_normalized",
            "variant_place_lemma_normalized",
        ]:
            value = term.get(key)
            if isinstance(value, str):
                _validate_normalized_value(f"{path}.{key}", value, issues)

        applies_to = term.get("applies_to") or {}
        for key in ["lemma_normalized", "substance_lemma_normalized", "part_lemma_normalized"]:
            value = applies_to.get(key)
            if isinstance(value, str):
                _validate_normalized_value(f"{path}.applies_to.{key}", value, issues)

        if label == "SUBSTANCE_PART":
            if lemma_gr != "":
                issues.append(f"{path}.lemma_gr: must be empty string for SUBSTANCE_PART")
            if lemma_normalized != "":
                issues.append(f"{path}.lemma_normalized: must be empty string for SUBSTANCE_PART")

            sub_norm = term.get("substance_lemma_normalized")
            part_norm = term.get("part_lemma_normalized")
            if not isinstance(sub_norm, str) or not sub_norm:
                issues.append(
                    f"{path}.substance_lemma_normalized: must be non-empty string for SUBSTANCE_PART"
                )
            if not isinstance(part_norm, str) or not part_norm:
                issues.append(
                    f"{path}.part_lemma_normalized: must be non-empty string for SUBSTANCE_PART"
                )

            if applies_to.get("kind") != "UNSPECIFIED":
                issues.append(f"{path}.applies_to.kind: must be 'UNSPECIFIED' for SUBSTANCE_PART")
            for key in ["lemma_normalized", "substance_lemma_normalized", "part_lemma_normalized"]:
                if applies_to.get(key) is not None:
                    issues.append(
                        f"{path}.applies_to.{key}: must be null for SUBSTANCE_PART (got {applies_to.get(key)!r})"
                    )

    qualities = obj.get("qualities") or []
    for idx, quality in enumerate(qualities):
        path = f"qualities[{idx}]"

        evidence_display = quality.get("evidence_display", "")
        evidence_normalized = quality.get("evidence_normalized", "")
        expected_ev = normalize_greek(evidence_display)
        if evidence_normalized != expected_ev:
            issues.append(
                f"{path}.evidence_normalized: must equal normalize(evidence_display); expected {expected_ev!r}, got {evidence_normalized!r}"
            )

        for key in ["evidence_normalized", "variant_place_lemma_normalized"]:
            value = quality.get(key)
            if isinstance(value, str):
                _validate_normalized_value(f"{path}.{key}", value, issues)

        applies_to = quality.get("applies_to") or {}
        for key in ["lemma_normalized", "substance_lemma_normalized", "part_lemma_normalized"]:
            value = applies_to.get(key)
            if isinstance(value, str):
                _validate_normalized_value(f"{path}.applies_to.{key}", value, issues)

    if issues:
        preview = "\n".join(f"- {item}" for item in issues[:50])
        if len(issues) > 50:
            preview += f"\n- ... and {len(issues) - 50} more"
        raise RuntimeError(
            "Post-validation failed: normalized fields and/or SUBSTANCE_PART consistency checks failed.\n"
            + preview
        )


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

    repo_root = _repo_root()

    codex_bin = args.codex_bin
    if not Path(codex_bin).exists():
        resolved = shutil.which(codex_bin)
        if resolved:
            codex_bin = resolved
        else:
            raise SystemExit(f"Could not find codex binary on PATH: {args.codex_bin!r}")

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
        #
        # If --out is not under the expected outputs/*/<run_id>/results layout,
        # fall back to a repo-local outputs/_codex_home directory rather than
        # accidentally trying to write under filesystem root (e.g. /_codex_home).
        try:
            out_rel = out_path.resolve().relative_to((repo_root / "outputs").resolve())
            # out_rel like: vocab_entries_v3/.../<run_id>/results/<file>.json
            # Mirror the existing pattern by using grandparent of the out file
            # (i.e. <run_id>) as the anchor.
            codex_home = (out_path.parent.parent / "_codex_home" / out_path.stem).resolve()
        except Exception:
            codex_home = (repo_root / "outputs" / "_codex_home" / out_path.stem).resolve()

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
        codex_bin,
        "exec",
        "-C",
        str(repo_root),
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

    _fix_normalized_fields(obj)
    _validate_extraction_obj(obj)

    out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        tmp_path.unlink(missing_ok=True)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""TEI validation script for Ancient Simples TEI-first platform.

Validates TEI XML against a doc config YAML. Hard-fails on structural
errors (missing xml:id, zero segments, duplicate ids). Warns on content
issues (missing preferred children in <choice>, missing <lem> in <app>).

Usage:
    python scripts/validate_tei.py --config config/tei_docs/gal_smt.yaml
"""
from __future__ import annotations

import argparse
import re
import sys
import yaml
from pathlib import Path
from lxml import etree

# TEI namespace
TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}


def load_config(config_path: Path) -> dict:
    with config_path.open() as f:
        return yaml.safe_load(f)


def validate_tei(config: dict, repo_root: Path) -> tuple[list[str], list[str]]:
    """Validate TEI file per config. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    tei_path = repo_root / config["tei_relpath"]
    if not tei_path.exists():
        errors.append(f"TEI file not found: {tei_path}")
        return errors, warnings

    try:
        tree = etree.parse(str(tei_path))
    except etree.XMLSyntaxError as e:
        errors.append(f"XML parse error: {e}")
        return errors, warnings

    # Select segments using XPath from config
    segment_xpath = config["segment_xpath"]
    segments = tree.xpath(segment_xpath, namespaces=NSMAP)

    if not segments:
        errors.append(f"Zero segments selected by XPath: {segment_xpath}")
        return errors, warnings

    # Check xml:id uniqueness
    seen_ids: dict[str, etree._Element] = {}
    for seg in segments:
        xml_id = seg.get("{http://www.w3.org/XML/1998/namespace}id")
        if xml_id is None:
            errors.append(
                f"Segment missing @xml:id: "
                f"{etree.tostring(seg, encoding='unicode')[:200]}"
            )
            continue
        if xml_id in seen_ids:
            errors.append(f"Duplicate @xml:id: {xml_id}")
        seen_ids[xml_id] = seg

    # Smoke-test reading text extraction for each segment
    for xml_id, seg in seen_ids.items():
        reading_text = extract_reading_text(seg)
        if not reading_text.strip():
            if not config.get("allow_empty_segments", False):
                errors.append(f"Empty reading_text for segment {xml_id}")

        # Warn on content issues within <choice> elements
        for choice in seg.iter(f"{{{TEI_NS}}}choice"):
            has_reg = choice.find(f"{{{TEI_NS}}}reg") is not None
            has_expan = choice.find(f"{{{TEI_NS}}}expan") is not None
            has_orig = choice.find(f"{{{TEI_NS}}}orig") is not None
            has_abbr = choice.find(f"{{{TEI_NS}}}abbr") is not None
            if has_orig and not has_reg:
                warnings.append(
                    f"Segment {xml_id}: <choice> has <orig> but no <reg>"
                )
            if has_abbr and not has_expan:
                warnings.append(
                    f"Segment {xml_id}: <choice> has <abbr> but no <expan>"
                )

        # Warn on <app> without <lem>
        for app in seg.iter(f"{{{TEI_NS}}}app"):
            if app.find(f"{{{TEI_NS}}}lem") is None:
                warnings.append(f"Segment {xml_id}: <app> has no <lem>")

    return errors, warnings


# ---------------------------------------------------------------------------
# Reading text extraction (simplified, for validation smoke testing)
# The full implementation with edition ref tracking lives in index_tei.py.
# ---------------------------------------------------------------------------

# Tags to skip entirely (omit from reading text)
SKIP_TAGS = {
    f"{{{TEI_NS}}}note",
    f"{{{TEI_NS}}}add",
    f"{{{TEI_NS}}}del",
}

# Milestone tags (no text contribution)
MILESTONE_TAGS = {
    f"{{{TEI_NS}}}pb",
    f"{{{TEI_NS}}}lb",
}

GAP_PLACEHOLDER = "[...]"


def extract_reading_text(node: etree._Element) -> str:
    """Extract reading text from a TEI segment node per C-01 rules.

    This is a simplified version for validation smoke testing.
    The full implementation with edition ref tracking is in index_tei.py.
    """
    parts: list[str] = []
    _extract_text(node, parts)
    text = " ".join(parts)
    # Collapse whitespace runs to single space, trim
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_text(node: etree._Element, parts: list[str]) -> None:
    """Recursively extract text from a TEI node following C-01 rules."""
    tag = node.tag if isinstance(node.tag, str) else ""

    # Skip tags: omit entirely
    if tag in SKIP_TAGS:
        return

    # Milestone tags: no text
    if tag in MILESTONE_TAGS:
        return

    # <gap>: insert placeholder
    if tag == f"{{{TEI_NS}}}gap":
        parts.append(GAP_PLACEHOLDER)
        return

    # <choice>: prefer <reg> over <orig>, <expan> over <abbr>
    if tag == f"{{{TEI_NS}}}choice":
        reg = node.find(f"{{{TEI_NS}}}reg")
        if reg is not None:
            _extract_text(reg, parts)
            return
        expan = node.find(f"{{{TEI_NS}}}expan")
        if expan is not None:
            _extract_text(expan, parts)
            return
        # Fallback: first child element
        for child in node:
            _extract_text(child, parts)
            return
        return

    # <app>: prefer <lem>, ignore <rdg>
    if tag == f"{{{TEI_NS}}}app":
        lem = node.find(f"{{{TEI_NS}}}lem")
        if lem is not None:
            _extract_text(lem, parts)
            return
        # Fallback: first <rdg>
        rdg = node.find(f"{{{TEI_NS}}}rdg")
        if rdg is not None:
            _extract_text(rdg, parts)
        return

    # Default: recurse into children, collect text and tail
    if node.text:
        parts.append(node.text)
    for child in node:
        _extract_text(child, parts)
        if child.tail:
            parts.append(child.tail)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate TEI file for Ancient Simples indexing"
    )
    parser.add_argument(
        "--config", required=True, help="Path to TEI doc config YAML"
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    config = load_config(config_path)

    errors, warnings = validate_tei(config, repo_root)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(
            f"\nValidation FAILED: {len(errors)} error(s), "
            f"{len(warnings)} warning(s)",
            file=sys.stderr,
        )
        return 1

    print(f"Validation OK: {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

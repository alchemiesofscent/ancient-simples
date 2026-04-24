"""Cross-language normalization parity tests.

Verifies that the Python canonical normalize (textutils.normalize) and the
TypeScript normalizeGreekForMatch (app/src/lib/greek/normalize.ts) produce
identical output for a shared corpus of Greek strings.

The TS function is tested indirectly: this file defines the expected
input/output pairs derived from the Python implementation. A companion
test (or CI step) can run these same pairs through the TS function.

For now, this test:
1. Validates Python normalize against a curated corpus of edge cases.
2. Writes a JSON fixture file that can be consumed by a future TS test.
"""

import json
from pathlib import Path

from textutils.normalize import normalize, NORMALIZATION_VERSION

# Corpus of edge-case Greek strings that exercise normalization boundaries.
# Each pair is (input, expected_output) computed by the Python canonical implementation.
PARITY_CORPUS = [
    # Basic accents/breathings
    ("τῇ", "τη"),
    ("ἀβροτόνου", "αβροτονου"),
    ("Περὶ ἀβροτόνου", "περι αβροτονου"),
    # Iota subscript (the v1.0 → v1.1 change)
    ("τῷ", "τω"),
    ("ᾧ", "ω"),
    ("ᾳ", "α"),
    ("ᾴ", "α"),
    ("ᾶ", "α"),
    ("ᾷ", "α"),
    ("ῇ", "η"),
    ("ῃ", "η"),
    ("ῳ", "ω"),
    ("ᾠ", "ω"),
    # Rough/smooth breathings
    ("ἁ", "α"),
    ("ἀ", "α"),
    ("Ἁ", "α"),
    ("Ἀ", "α"),
    # Circumflex + diaeresis
    ("ϊ", "ι"),
    ("ϋ", "υ"),
    ("ΐ", "ι"),
    ("ΰ", "υ"),
    # Mixed Greek and Latin
    ("σίδηρος iron", "σιδηρος iron"),
    # Empty / whitespace
    ("", ""),
    ("   ", "   "),
    # Numbers and punctuation (pass-through)
    ("123·456", "123·456"),
    # Combined marks at extremes of range
    ("\u0300", ""),  # standalone combining grave accent → stripped
    ("\u036F", ""),  # standalone combining mark at end of range → stripped
    # Prooimion (the full word)
    ("προοίμιον", "προοιμιον"),
    # Double accents (editorial markup sometimes produces these)
    ("ὰά", "αα"),
    # NFC stability: already-NFC input should be unchanged after normalize
    ("αβγδ", "αβγδ"),
]


class TestNormalizationParity:
    """Verify Python normalize against the curated corpus."""

    def test_version(self):
        assert NORMALIZATION_VERSION == "1.1"

    def test_corpus(self):
        failures = []
        for input_str, expected in PARITY_CORPUS:
            actual = normalize(input_str)
            if actual != expected:
                failures.append(
                    f"  input={input_str!r}  expected={expected!r}  got={actual!r}"
                )
        assert not failures, "Parity corpus mismatches:\n" + "\n".join(failures)

    def test_write_fixture(self, tmp_path: Path):
        """Write the corpus as a JSON fixture for consumption by TS tests."""
        fixture = {
            "normalization_version": NORMALIZATION_VERSION,
            "description": "Normalization parity test corpus. Each pair is [input, expected_output].",
            "pairs": [[inp, normalize(inp)] for inp, _ in PARITY_CORPUS],
        }
        fixture_path = tmp_path / "normalization_parity.json"
        fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2))
        assert fixture_path.exists()

    def test_iota_subscript_stripped(self):
        """The v1.0 → v1.1 change: iota subscripts must be stripped."""
        # τῇ has iota subscript (U+0345 after NFD). v1.0 preserved it; v1.1 strips it.
        result = normalize("τῇ")
        assert result == "τη", f"Iota subscript not stripped: got {result!r}"
        # ᾧ = omega + iota subscript + rough breathing + circumflex
        result = normalize("ᾧ")
        assert result == "ω", f"Complex iota subscript not stripped: got {result!r}"


class TestParityFixtureOnDisk:
    """Write a persistent fixture to tests/fixtures/ for TS consumption."""

    def test_generate_fixture(self):
        fixture_dir = Path(__file__).parent / "fixtures"
        fixture_dir.mkdir(exist_ok=True)
        fixture_path = fixture_dir / "normalization_parity.json"
        fixture = {
            "normalization_version": NORMALIZATION_VERSION,
            "description": "Normalization parity corpus. Run these pairs through both Python and TS normalize to verify parity.",
            "pairs": [[inp, normalize(inp)] for inp, _ in PARITY_CORPUS],
        }
        fixture_path.write_text(
            json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        # Verify round-trip
        loaded = json.loads(fixture_path.read_text(encoding="utf-8"))
        assert len(loaded["pairs"]) == len(PARITY_CORPUS)

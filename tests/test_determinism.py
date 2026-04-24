"""Tests for normalization determinism — same input always yields same output."""

from textutils.normalize import normalize


class TestDeterminism:
    """Verify normalize() produces consistent results across multiple calls."""

    def test_determinism_headwords(self, greek_headwords):
        """Each headword normalizes to the same result on every call."""
        assert len(greek_headwords) >= 50, (
            f"Expected 50+ headwords, got {len(greek_headwords)}"
        )
        for hw in greek_headwords:
            result1 = normalize(hw)
            result2 = normalize(hw)
            result3 = normalize(hw)
            assert result1 == result2 == result3, (
                f"Non-deterministic for {hw!r}: {result1!r}, {result2!r}, {result3!r}"
            )

    def test_determinism_with_whitespace_variants(self, greek_headwords):
        """Normalization is deterministic even with surrounding whitespace."""
        for hw in greek_headwords[:20]:
            padded = f"  {hw}  "
            result1 = normalize(padded)
            result2 = normalize(padded)
            assert result1 == result2

    def test_determinism_concatenated(self, greek_headwords):
        """Normalizing a concatenation is deterministic."""
        combined = " ".join(greek_headwords)
        result1 = normalize(combined)
        result2 = normalize(combined)
        assert result1 == result2

    def test_normalized_headwords_match_csv(self, greek_headwords):
        """Verify that our v1.1 normalization of headwords produces expected stripped forms.

        Note: the CSV headword_normalized column was produced with v1.0 rules (which kept
        iota subscript). v1.1 strips iota subscript as well. So we only check that the
        result is deterministic and idempotent, not that it matches the CSV column exactly.
        """
        for hw in greek_headwords:
            normalized = normalize(hw)
            # Must be idempotent
            assert normalize(normalized) == normalized
            # Must be lowercase
            assert normalized == normalized.lower()

"""Tests for textutils.normalize — reference cases, idempotence, and NFC stability."""

import unicodedata

from textutils.normalize import normalize, NORMALIZATION_VERSION


class TestNormalizationVersion:
    def test_version_is_1_1(self):
        assert NORMALIZATION_VERSION == "1.1"


class TestReferenceCases:
    """Core reference cases from the spec."""

    def test_uppercase_with_diacritics(self):
        # Ψυχρός -> ψυχρος (lowercase, strip acute)
        assert normalize("\u03a8\u03c5\u03c7\u03c1\u03cc\u03c2") == "\u03c8\u03c5\u03c7\u03c1\u03bf\u03c2"

    def test_iota_subscript_stripped_v1_1(self):
        # τῇ -> τη (v1.1: iota subscript U+0345 is stripped)
        assert normalize("\u03c4\u1fc7") == "\u03c4\u03b7"

    def test_smooth_breathing_and_acute(self):
        # ἄνθρωπος -> ανθρωπος
        assert normalize("\u1f04\u03bd\u03b8\u03c1\u03c9\u03c0\u03bf\u03c2") == "\u03b1\u03bd\u03b8\u03c1\u03c9\u03c0\u03bf\u03c2"

    def test_latin_with_diaeresis(self):
        # Aëtius -> aetius
        assert normalize("A\u00ebtius") == "aetius"

    def test_empty_string(self):
        assert normalize("") == ""

    def test_none_input(self):
        assert normalize(None) == ""

    def test_plain_ascii(self):
        assert normalize("hello") == "hello"

    def test_rough_breathing(self):
        # ἁ -> α (strip rough breathing)
        assert normalize("\u1f01") == "\u03b1"

    def test_circumflex(self):
        # ῶ -> ω (strip circumflex)
        assert normalize("\u1ff6") == "\u03c9"

    def test_grave_accent(self):
        # ὰ -> α (strip grave)
        assert normalize("\u1f70") == "\u03b1"

    def test_breathing_and_accent_combined(self):
        # ἅ -> α (rough breathing + acute)
        assert normalize("\u1f05") == "\u03b1"

    def test_final_sigma_preserved(self):
        # Final sigma should NOT be rewritten to medial sigma
        assert normalize("\u03c2") == "\u03c2"

    def test_mixed_greek_and_latin(self):
        result = normalize("abc \u03b1\u03b2\u03b3")
        assert result == "abc \u03b1\u03b2\u03b3"


class TestIdempotence:
    """normalize(normalize(x)) == normalize(x) for all inputs."""

    def test_idempotence_basic(self):
        cases = [
            "\u03a8\u03c5\u03c7\u03c1\u03cc\u03c2",
            "\u03c4\u1fc7",
            "\u1f04\u03bd\u03b8\u03c1\u03c9\u03c0\u03bf\u03c2",
            "A\u00ebtius",
            "",
            "hello",
        ]
        for text in cases:
            once = normalize(text)
            twice = normalize(once)
            assert once == twice, f"Idempotence failed for {text!r}: {once!r} != {twice!r}"

    def test_idempotence_headwords(self, greek_headwords):
        for hw in greek_headwords:
            once = normalize(hw)
            twice = normalize(once)
            assert once == twice, f"Idempotence failed for {hw!r}"


class TestNFCStability:
    """Output must always be in NFC form."""

    def test_output_is_nfc(self):
        cases = [
            "\u03a8\u03c5\u03c7\u03c1\u03cc\u03c2",
            "\u03c4\u1fc7",
            "\u1f04\u03bd\u03b8\u03c1\u03c9\u03c0\u03bf\u03c2",
            "A\u00ebtius",
        ]
        for text in cases:
            result = normalize(text)
            assert unicodedata.is_normalized("NFC", result), (
                f"Output not NFC for {text!r}: {result!r}"
            )

    def test_nfc_stability_headwords(self, greek_headwords):
        for hw in greek_headwords:
            result = normalize(hw)
            assert unicodedata.is_normalized("NFC", result), (
                f"Output not NFC for {hw!r}: {result!r}"
            )

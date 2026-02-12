"""Tests for textutils.tokenize — basic Greek tokenization and gap placeholder handling."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from packages.textutils.tokenize import tokenize, TOKENIZER_VERSION
from packages.textutils.normalize import normalize


class TestTokenizerVersion:
    def test_version_is_1_0(self):
        assert TOKENIZER_VERSION == "1.0"


class TestBasicGreekTokenization:
    """Basic Greek text tokenization with exact offset verification."""

    def test_single_word(self):
        tokens = tokenize("\u03bb\u03cc\u03b3\u03bf\u03c2")  # λόγος
        assert len(tokens) == 1
        t = tokens[0]
        assert t["token_index"] == 0
        assert t["start_offset"] == 0
        assert t["end_offset"] == 5
        assert t["token_text"] == "\u03bb\u03cc\u03b3\u03bf\u03c2"
        assert t["token_normalized"] == normalize("\u03bb\u03cc\u03b3\u03bf\u03c2")

    def test_two_words(self):
        text = "\u03bb\u03cc\u03b3\u03bf\u03c2 \u03ba\u03b1\u03bb\u03cc\u03c2"  # λόγος καλός
        tokens = tokenize(text)
        assert len(tokens) == 2

        assert tokens[0]["token_index"] == 0
        assert tokens[0]["start_offset"] == 0
        assert tokens[0]["end_offset"] == 5
        assert tokens[0]["token_text"] == "\u03bb\u03cc\u03b3\u03bf\u03c2"

        assert tokens[1]["token_index"] == 1
        assert tokens[1]["start_offset"] == 6
        assert tokens[1]["end_offset"] == 11
        assert tokens[1]["token_text"] == "\u03ba\u03b1\u03bb\u03cc\u03c2"

    def test_punctuation_as_delimiter(self):
        text = "\u03bb\u03cc\u03b3\u03bf\u03c2, \u03ba\u03b1\u03bb\u03cc\u03c2."  # λόγος, καλός.
        tokens = tokenize(text)
        assert len(tokens) == 2
        assert tokens[0]["token_text"] == "\u03bb\u03cc\u03b3\u03bf\u03c2"
        assert tokens[1]["token_text"] == "\u03ba\u03b1\u03bb\u03cc\u03c2"

    def test_empty_string(self):
        tokens = tokenize("")
        assert tokens == []

    def test_only_delimiters(self):
        tokens = tokenize("   ,.;  ")
        assert tokens == []

    def test_mixed_greek_latin(self):
        text = "abc \u03b1\u03b2\u03b3"
        tokens = tokenize(text)
        assert len(tokens) == 2
        assert tokens[0]["token_text"] == "abc"
        assert tokens[1]["token_text"] == "\u03b1\u03b2\u03b3"

    def test_numbers_are_tokens(self):
        text = "word1 123 \u03b1\u03b2\u03b3"
        tokens = tokenize(text)
        # "word1" is one token (L and N mixed), "123" is a token, "αβγ" is a token
        assert len(tokens) == 3
        assert tokens[0]["token_text"] == "word1"
        assert tokens[1]["token_text"] == "123"
        assert tokens[2]["token_text"] == "\u03b1\u03b2\u03b3"

    def test_offsets_are_codepoints(self):
        # Verify offsets work with multi-codepoint characters
        text = "\u1f04\u03bd\u03b8\u03c1\u03c9\u03c0\u03bf\u03c2"  # ἄνθρωπος
        tokens = tokenize(text)
        assert len(tokens) == 1
        t = tokens[0]
        # ἄ is a single precomposed codepoint
        assert t["start_offset"] == 0
        assert text[t["start_offset"]:t["end_offset"]] == text


class TestGapPlaceholder:
    """[...] gap placeholders: brackets and dots are all delimiters, no tokens produced."""

    def test_gap_placeholder_no_tokens(self):
        text = "[...]"
        tokens = tokenize(text)
        # [ is Ps, ] is Pe, . is Po — none are L* or N*
        assert tokens == []

    def test_text_around_gap(self):
        text = "\u03bb\u03cc\u03b3\u03bf\u03c2 [...] \u03ba\u03b1\u03bb\u03cc\u03c2"
        tokens = tokenize(text)
        assert len(tokens) == 2
        assert tokens[0]["token_text"] == "\u03bb\u03cc\u03b3\u03bf\u03c2"
        assert tokens[0]["start_offset"] == 0
        assert tokens[1]["token_text"] == "\u03ba\u03b1\u03bb\u03cc\u03c2"
        # "λόγος [...] καλός" = 5 + 1 + 5 + 1 = offset 12 for καλός
        assert tokens[1]["start_offset"] == 12

    def test_multiple_gaps(self):
        text = "[...] \u03b1 [...] \u03b2 [...]"
        tokens = tokenize(text)
        assert len(tokens) == 2
        assert tokens[0]["token_text"] == "\u03b1"
        assert tokens[1]["token_text"] == "\u03b2"


class TestTokenNormalization:
    """Verify token_normalized matches normalize(token_text)."""

    def test_normalized_field_matches(self):
        text = "\u03a8\u03c5\u03c7\u03c1\u03cc\u03c2 \u03c4\u1fc7 \u1f04\u03bd\u03b8\u03c1\u03c9\u03c0\u03bf\u03c2"
        tokens = tokenize(text)
        for t in tokens:
            assert t["token_normalized"] == normalize(t["token_text"])

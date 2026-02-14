import unicodedata
from .normalize import normalize

TOKENIZER_VERSION = "1.0"


def tokenize(text: str) -> list[dict]:
    """Tokenize reading text into L*/N* token spans with codepoint offsets."""
    tokens = []
    codepoints = list(text)
    i = 0
    token_idx = 0
    while i < len(codepoints):
        ch = codepoints[i]
        cat = unicodedata.category(ch)
        if cat.startswith("L") or cat.startswith("N"):
            start = i
            while i < len(codepoints):
                c = codepoints[i]
                ct = unicodedata.category(c)
                if ct.startswith("L") or ct.startswith("N") or ct == "Mn":
                    i += 1
                else:
                    break
            token_text = "".join(codepoints[start:i])
            tokens.append({
                "token_index": token_idx,
                "start_offset": start,
                "end_offset": i,
                "token_text": token_text,
                "token_normalized": normalize(token_text),
            })
            token_idx += 1
        else:
            i += 1
    return tokens

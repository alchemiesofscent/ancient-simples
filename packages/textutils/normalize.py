import unicodedata

NORMALIZATION_VERSION = "1.1"


def normalize(text: str) -> str:
    """Ancient Simples Greek normalization v1.1.

    Lowercase, strip all combining marks U+0300-U+036F (including iota subscript), NFC.
    """
    lowered = (text or "").lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(
        ch for ch in decomposed
        if not (0x0300 <= ord(ch) <= 0x036F)
    )
    return unicodedata.normalize("NFC", stripped)

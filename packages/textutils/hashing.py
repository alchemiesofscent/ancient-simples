import hashlib
from .normalize import normalize


def raw_hash(reading_text: str) -> str:
    """SHA-256 hex digest of NFC reading_text UTF-8 bytes."""
    return hashlib.sha256(reading_text.encode("utf-8")).hexdigest()


def normalized_hash(reading_text: str) -> str:
    """SHA-256 hex digest of normalized reading_text UTF-8 bytes."""
    return hashlib.sha256(normalize(reading_text).encode("utf-8")).hexdigest()


def dual_hash(reading_text: str) -> tuple[str, str]:
    """Return (raw_hash, normalized_hash) for a reading_text string."""
    return raw_hash(reading_text), normalized_hash(reading_text)

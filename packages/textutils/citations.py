def format_structure_ref(path: list[dict]) -> str:
    """Format a structure ref path into a human-readable string."""
    parts = []
    for level in path:
        n = level.get("n", "")
        if n:
            parts.append(n)
        elif level.get("head"):
            parts.append(level["head"])
    return ".".join(parts)


def format_edition_ref(payload: dict) -> str:
    """Format an edition ref payload into a human-readable string."""
    edition = payload.get("edition", "")
    start = payload.get("start", {})
    end = payload.get("end", {})

    start_str = start.get("pb", "")
    if start.get("lb"):
        start_str += f".{start['lb']}"

    end_str = end.get("pb", "")
    if end.get("lb"):
        end_str += f".{end['lb']}"

    if start_str == end_str:
        return f"{edition} {start_str}" if edition else start_str
    return f"{edition} {start_str}\u2013{end_str}" if edition else f"{start_str}\u2013{end_str}"


def format_combined(structure_path: list[dict], edition_payload: dict | None) -> str:
    """Format combined citation: structure ref (edition ref)."""
    struct = format_structure_ref(structure_path)
    if edition_payload:
        ed = format_edition_ref(edition_payload)
        return f"{struct} ({ed})"
    return struct

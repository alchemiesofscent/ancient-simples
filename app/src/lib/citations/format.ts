/**
 * Citation formatting utilities for Ancient Simples TEI-first platform.
 * Implements C-04 §6 formatting rules.
 *
 * Used by all detail/query pages for consistent citation display.
 */

export type StructureLevel = {
  type?: string;
  n?: string;
  xml_id?: string;
  head?: string;
};

export type EditionRef = {
  edition?: string;
  start?: { pb?: string; lb?: string };
  end?: { pb?: string; lb?: string };
  events?: Array<{ kind: string; n: string; offset: number }>;
};

/**
 * Format a structure ref path into a human-readable string.
 * Joins `n` values in order; falls back to `head` text if `n` is missing.
 *
 * Example: [{n: "6"}, {n: "1"}, {n: "1"}] → "6.1.1"
 */
export function formatStructureRef(path: StructureLevel[]): string {
  const parts: string[] = [];
  for (const level of path) {
    if (level.n) {
      parts.push(level.n);
    } else if (level.head) {
      parts.push(level.head);
    }
  }
  return parts.join(".");
}

/**
 * Format an edition ref payload into a human-readable string.
 *
 * Supports:
 * 1. Page+line range: "Kühn XI.123.4–XI.124.2"
 * 2. Page range only: "Wellmann 1.7–1.8"
 * 3. Single page: "Kühn XI.123.4"
 *
 * If edition uses page-range-only (no line breaks), MUST NOT invent line numbers.
 */
export function formatEditionRef(payload: EditionRef): string {
  const edition = payload.edition ?? "";

  const startPb = payload.start?.pb ?? "";
  const startLb = payload.start?.lb;
  const endPb = payload.end?.pb ?? "";
  const endLb = payload.end?.lb;

  let startStr = startPb;
  if (startLb) startStr += `.${startLb}`;

  let endStr = endPb;
  if (endLb) endStr += `.${endLb}`;

  let ref: string;
  if (!startStr && !endStr) {
    return edition;
  } else if (startStr === endStr || !endStr) {
    ref = startStr;
  } else {
    ref = `${startStr}\u2013${endStr}`;
  }

  return edition ? `${edition} ${ref}` : ref;
}

/**
 * Format combined citation: structure ref (edition ref).
 *
 * Example: "6.1.1 (Kühn XI.123.4–XI.124.2)"
 */
export function formatCombined(
  structurePath: StructureLevel[],
  editionPayload: EditionRef | null | undefined,
): string {
  const struct = formatStructureRef(structurePath);
  if (editionPayload) {
    const ed = formatEditionRef(editionPayload);
    if (ed) {
      return `${struct} (${ed})`;
    }
  }
  return struct;
}

/**
 * Ancient Simples Greek normalization v1.1.
 *
 * Lowercase, NFD decompose, strip ALL combining marks U+0300–U+036F
 * (including U+0345 iota subscript), NFC recompose.
 *
 * v1.1 change: iota subscripts are now stripped (previously preserved in v1.0).
 */
export const NORMALIZATION_VERSION = "1.1";

export function normalizeGreekForMatch(input: string): string {
  const lowered = input.toLowerCase();
  const decomposed = lowered.normalize("NFD");
  let out = "";

  for (const ch of decomposed) {
    const codePoint = ch.codePointAt(0);
    if (codePoint === undefined) continue;

    // v1.1: strip ALL combining marks in U+0300..U+036F (including iota subscript U+0345)
    const isCombiningMark = codePoint >= 0x0300 && codePoint <= 0x036f;
    if (isCombiningMark) continue;

    out += ch;
  }

  return out.normalize("NFC");
}


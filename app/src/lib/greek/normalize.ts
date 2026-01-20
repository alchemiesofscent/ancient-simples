export function normalizeGreekForMatch(input: string): string {
  const lowered = input.toLowerCase();
  const decomposed = lowered.normalize("NFD");
  let out = "";

  for (const ch of decomposed) {
    const codePoint = ch.codePointAt(0);
    if (codePoint === undefined) continue;

    const isCombiningMark = codePoint >= 0x0300 && codePoint <= 0x036f;
    const isIotaSubscript = codePoint === 0x0345;
    if (isCombiningMark && !isIotaSubscript) continue;

    out += ch;
  }

  return out.normalize("NFC");
}


const ARTICLE_RE = /제\d+조(?:의\d+)?/g;

// 백엔드 app/external/law.py 의 basis_keys 와 같은 규칙
// '최저임금법 제5조②, 같은 법 시행령 제3조' → ['최저임금법 제5조', '최저임금법 시행령 제3조']
export function basisKeys(basis: string): string[] {
  const keys: string[] = [];
  let prevLaw = "";
  for (const part of basis.split(",").map((p) => p.trim()).filter(Boolean)) {
    const articles = part.match(ARTICLE_RE);
    if (!articles) continue;
    let law = part.slice(0, part.search(ARTICLE_RE)).trim();
    if (law.startsWith("같은 법")) law = (prevLaw + law.slice("같은 법".length)).trim();
    keys.push(...articles.map((a) => `${law} ${a}`));
    prevLaw = law;
  }
  return keys;
}

// '20260820' → '2026.08.20'
export function formatEffectiveDate(yyyymmdd: string): string {
  const m = /^(\d{4})(\d{2})(\d{2})$/.exec(yyyymmdd);
  return m ? `${m[1]}.${m[2]}.${m[3]}` : yyyymmdd;
}

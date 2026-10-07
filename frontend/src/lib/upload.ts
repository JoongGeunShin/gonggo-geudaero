// 백엔드 app/services/extraction.py 와 같은 기준
const ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const MAX_BYTES = 10 * 1024 * 1024;

// <input type="file" accept=...> 에 넣는 값
export const FILE_ACCEPT = ".jpg,.jpeg,.png,.pdf";
export const FILE_HINT = "jpg·png·pdf, 10MB 이하";

// 올리기 전에 브라우저에서 먼저 거른다 (서버도 같은 검사를 한 번 더 한다)
export function checkFile(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type)) return "jpg, png, pdf 파일만 올릴 수 있어요.";
  if (file.size > MAX_BYTES) return "파일은 10MB 이하만 올릴 수 있어요.";
  return null;
}

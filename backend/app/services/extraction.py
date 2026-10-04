"""업로드된 문서 한 장을 '저장해도 되는 추출 결과'로 만드는 공통 흐름: 검사 → 추출 → 인용검증 → 마스킹."""

from app.ai.base import DocKind, ExtractionResult, ExtractorProvider
from app.ai.mask import mask_result
from app.ai.verify import verify_quotes

MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10MB
ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "application/pdf"}


class UploadRejected(ValueError):
    """받을 수 없는 파일. 라우터가 status_code 그대로 HTTP 에러로 바꾼다."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def check_upload(data: bytes, media_type: str | None) -> None:
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise UploadRejected(415, f"jpg·png·pdf만 받을 수 있음 (받은 형식: {media_type})")
    if not data:
        raise UploadRejected(400, "빈 파일")
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadRejected(413, f"파일은 {MAX_UPLOAD_BYTES // (1024 * 1024)}MB 이하만 받을 수 있음")


def extract_document(extractor: ExtractorProvider, data: bytes, media_type: str,
                     doc_kind: DocKind) -> ExtractionResult:
    """검증을 마스킹보다 먼저 한다: 인용과 원문을 같은 상태로 비교해야 하므로."""
    check_upload(data, media_type)
    result = extractor.extract(data, media_type, doc_kind)
    return mask_result(verify_quotes(result))

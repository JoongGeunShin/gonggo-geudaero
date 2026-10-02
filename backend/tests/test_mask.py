import pytest

from app.ai.base import ExtractionResult
from app.ai.mask import mask_result, mask_text
from app.ai.verify import verify_quotes
from app.schemas import ConditionDoc, ExtractedField


@pytest.mark.parametrize("raw", ["900101-1234567", "900101 - 2234567", "9001013234567"])
def test_masks_resident_numbers(raw):
    assert mask_text(f"주민등록번호: {raw} 끝") == "주민등록번호: ******-******* 끝"


@pytest.mark.parametrize("raw", ["010-1234-5678", "01012345678", "011 123 4567", "010.1234.5678"])
def test_masks_mobile_numbers(raw):
    assert mask_text(f"연락처 {raw}") == "연락처 ***-****-****"


def test_masks_email():
    assert mask_text("메일 hong.gd+hr@ga-na.co.kr 로") == "메일 ***@*** 로"


@pytest.mark.parametrize("text", [
    "시급 10,320원",
    "2026-10-01부터 2027-09-30까지",
    "사업자등록번호 124-81-00998",
    "매월 10일 지급, 주 40시간",
    "",
])
def test_leaves_ordinary_numbers_alone(text):
    assert mask_text(text) == text


def test_none_passes_through():
    assert mask_text(None) is None


def test_mask_result_masks_full_text_and_every_quote():
    result = ExtractionResult(
        full_text="근로자 연락처 010-1234-5678\n임금 월 250만원",
        fields=ConditionDoc(
            company=ExtractedField(value="가나", quote="담당 hr@gana.kr"),
            wage=ExtractedField(value={"type": "월급"}, quote="임금 월 250만원"),
        ),
    )
    masked = mask_result(result)
    assert "010-1234-5678" not in masked.full_text
    assert masked.fields.company.quote == "담당 ***@***"
    assert masked.fields.wage.quote == "임금 월 250만원"
    assert result.full_text.endswith("250만원") and "010-1234-5678" in result.full_text   # 입력은 그대로


def test_masked_quote_still_verifies_against_masked_text():
    result = ExtractionResult(
        full_text="문의: 010-1234-5678 (인사팀)",
        fields=ConditionDoc(workplace=ExtractedField(value="인사팀", quote="문의: 010-1234-5678 (인사팀)")),
    )
    assert verify_quotes(mask_result(result)).fields.workplace.value == "인사팀"

from app.ai.base import ExtractionResult
from app.ai.verify import normalize, verify_quotes
from app.schemas import ConditionDoc, ExtractedField

SOURCE = "근로계약서\n임금: 시급 １０,３２０원\n근무시간  09:00 ~ 18:00\n“수습 3개월”"


def make(**fields) -> ExtractionResult:
    return ExtractionResult(full_text=SOURCE, fields=ConditionDoc(**fields))


def test_normalize_ignores_spaces_newlines_and_full_width():
    assert normalize("시급 １０,３２０원") == normalize("시급10,320원")
    assert normalize("09:00 ~ 18:00") == normalize("09:00\n～18:00")
    assert normalize("“수습”") == normalize('"수습"')


def test_quote_found_in_source_is_kept():
    result = verify_quotes(make(wage=ExtractedField(value={"type": "시급"}, quote="시급 10,320원")))
    assert result.fields.wage.value == {"type": "시급"}
    assert result.fields.wage.verification is None


def test_quote_matches_across_whitespace_differences():
    result = verify_quotes(make(start_time=ExtractedField(value="09:00", quote="근무시간 09:00~18:00")))
    assert result.fields.start_time.value == "09:00"


def test_unmatched_quote_drops_value():
    result = verify_quotes(make(wage=ExtractedField(value={"type": "월급"}, quote="월급 300만원")))
    assert result.fields.wage.value is None
    assert result.fields.wage.verification == "quote_not_found"
    assert result.fields.wage.quote == "월급 300만원"   # 무엇이 버려졌는지 보여주려고 인용은 남긴다


def test_value_without_quote_is_dropped():
    result = verify_quotes(make(company=ExtractedField(value="가나정밀", quote=None)))
    assert result.fields.company.value is None
    assert result.fields.company.verification == "quote_missing"


def test_empty_fields_and_doc_type_are_left_alone():
    result = verify_quotes(make(doc_type=ExtractedField(value="계약서", quote=None)))
    assert result.fields.doc_type.value == "계약서"
    assert result.fields.doc_type.verification is None
    assert result.fields.wage.verification is None


def test_masked_parts_are_ignored_when_comparing():
    source = "연락처 010-****-**** 로 문의"
    result = verify_quotes(ExtractionResult(full_text=source, fields=ConditionDoc(
        workplace=ExtractedField(value="x", quote="연락처 010-1234-5678 로 문의"))))
    assert result.fields.workplace.value is None   # 숫자가 다르면 여전히 불일치
    result = verify_quotes(ExtractionResult(full_text=source, fields=ConditionDoc(
        workplace=ExtractedField(value="x", quote="연락처 010-****-**** 로 문의"))))
    assert result.fields.workplace.value == "x"


def test_input_is_not_mutated():
    original = make(wage=ExtractedField(value={"type": "월급"}, quote="없는 문장"))
    verify_quotes(original)
    assert original.fields.wage.value == {"type": "월급"}


def test_mock_results_pass_verification_unchanged():
    from app.ai.mock import MockExtractor
    for kind in ("posting", "contract"):
        result = MockExtractor().extract(b"x", "image/png", kind)
        assert verify_quotes(result) == result

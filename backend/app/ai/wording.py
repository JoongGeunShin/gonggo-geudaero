"""설명 문구 검사: 법적 판단을 단정하는 말이 들어가면 쓰지 않는다.

판정은 규칙 엔진만 하고, 그 결과도 '확인이 필요합니다' 수준으로만 전한다 (법률 자문이 아님).
"""

from app.schemas import ExplanationItem

ASSERTIVE_WORDS = ("위반", "불법", "위법", "처벌", "범죄", "고소", "고발")


def assertive_words(text: str) -> list[str]:
    return [w for w in ASSERTIVE_WORDS if w in text]


def is_safe(item: ExplanationItem) -> bool:
    return not assertive_words(item.summary + item.question)

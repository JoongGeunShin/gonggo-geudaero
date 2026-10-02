from app.ai.base import ExtractorProvider
from app.config import settings


def get_extractor() -> ExtractorProvider:
    """.env의 AI_PROVIDER 값으로 추출 구현체를 고른다. 구현을 바꿔 끼우는 곳은 여기 한 곳뿐."""
    provider = settings.ai_provider
    if provider == "mock":
        from app.ai.mock import MockExtractor
        return MockExtractor()
    # gemini(Step 6-4)는 구현하면서 여기에 추가한다
    raise ValueError(f"지원하지 않는 AI_PROVIDER: {provider}")

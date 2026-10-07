from app.ai.base import ExplainerProvider, ExtractorProvider
from app.config import settings


def get_extractor() -> ExtractorProvider:
    """.env의 AI_PROVIDER 값으로 추출 구현체를 고른다. 구현을 바꿔 끼우는 곳은 여기 한 곳뿐."""
    provider = settings.ai_provider
    if provider == "mock":
        from app.ai.mock import MockExtractor
        return MockExtractor()
    if provider == "gemini":
        if not settings.gemini_api_key or not settings.gemini_model:
            raise ValueError("AI_PROVIDER=gemini에는 GEMINI_API_KEY와 GEMINI_MODEL이 필요합니다")
        from app.ai.gemini import GeminiExtractor
        return GeminiExtractor(api_key=settings.gemini_api_key, model=settings.gemini_model)
    raise ValueError(f"지원하지 않는 AI_PROVIDER: {provider}")


def get_explainer() -> ExplainerProvider:
    """설명 구현체 선택. 추출과 같은 AI_PROVIDER를 따른다."""
    provider = settings.ai_provider
    if provider == "mock":
        from app.ai.mock import MockExplainer
        return MockExplainer()
    raise ValueError(f"지원하지 않는 AI_PROVIDER: {provider}")

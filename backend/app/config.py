from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "sqlite:///./local.db"
    nts_service_key: str = ""      # 국세청 (Decoding 키)
    law_oc: str = ""               # 법제처 OC
    ai_provider: str = "mock"      # mock | gemini | ennoia
    gemini_api_key: str = ""
    gemini_model: str = ""         # 시작 시점 공식 문서의 무료 티어 모델명으로
    cors_origins: str = "http://localhost:3000"


settings = Settings()

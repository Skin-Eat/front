from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수 기반 설정. API 명세가 바뀌어도 이 파일은 거의 안 바뀜 —
    새 외부 연동이 생기면 여기 필드만 추가하면 됨."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # "local"일 때만 SUPABASE_JWT_SECRET 미설정 시 UUID 그대로 신뢰하는 개발용 폴백을 허용한다.
    # 배포 환경에서는 반드시 production으로 설정해서 그 폴백이 막히게 할 것 (app/core/security.py 참고).
    app_env: str = "local"

    # Supabase Postgres 기준. Vercel(프론트) -> 가비아(FastAPI 백엔드 호스팅) -> Supabase(DB) 구조.
    database_url: str = "postgresql://postgres:password@localhost:5432/postgres"

    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    # anon(공개) 키 — /auth/signup, /auth/login이 서버사이드에서 Supabase Auth API를 대신
    # 호출할 때 apikey 헤더로 씀. service_role 키가 아니라 anon 키(공개돼도 되는 키)로 충분함.
    supabase_anon_key: str = ""

    openai_api_key: str = ""

    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

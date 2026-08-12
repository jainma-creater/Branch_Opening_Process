from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Branch Opening Platform"
    app_env: str = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/branch_opening"
    secret_key: str = "change-me-in-production"
    token_expire_minutes: int = 480
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:3000,http://localhost:3100"

    # API hardening
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 300
    rate_limit_window_seconds: int = 60
    rate_limit_trusted_hosts: str = "127.0.0.1,::1,localhost,testclient"
    max_request_body_bytes: int = 1_048_576

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def rate_limit_trusted_host_list(self) -> list[str]:
        return [h.strip() for h in self.rate_limit_trusted_hosts.split(",") if h.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

from pydantic import (
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SearchIntel AI"
    app_env: str = "development"
    database_url: str
    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    )

    api_token: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace(
                "postgres://",
                "postgresql+psycopg://",
                1,
            )

        if value.startswith("postgresql://"):
            return value.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        return value

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.app_env.lower() != "production":
            return self

        if self.api_token is None:
            raise ValueError(
                "API_TOKEN is required in production."
            )

        if not self.allowed_cors_origins:
            raise ValueError(
                "CORS_ORIGINS is required in production."
            )

        if any(
            origin == "*"
            or not origin.startswith("https://")
            for origin in self.allowed_cors_origins
        ):
            raise ValueError(
                "CORS_ORIGINS must contain explicit "
                "HTTPS origins in production."
            )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

"""Application settings loaded from environment variables via Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration is read from environment variables (or a .env file).

    Why Pydantic settings?
    - Type-safe: a missing or malformed var raises a clear error at startup.
    - No manual os.getenv() boilerplate scattered across the codebase.
    - Works seamlessly with FastAPI's dependency injection.
    """

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Comma-separated origins, e.g. "http://localhost:5173,https://app.example.com"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Split the CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Single shared instance — import this everywhere
settings = Settings()

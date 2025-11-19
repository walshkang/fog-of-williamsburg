from functools import lru_cache
from pydantic import BaseSettings, AnyHttpUrl


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Fog of Williamsburg Backend"
    environment: str = "local"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fog_of_williamsburg"

    # Mapbox
    mapbox_public_token: str = ""
    mapbox_secret_token: str = ""
    mapbox_map_matching_base_url: AnyHttpUrl = (  # type: ignore[assignment]
        "https://api.mapbox.com/matching/v5/mapbox/cycling"  # default profile
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()



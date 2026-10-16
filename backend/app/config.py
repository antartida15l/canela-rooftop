from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # uvicorn y pytest se ejecutan desde backend/, el .env está en la raíz
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str
    condicion_key: str
    jwt_secret: str
    jwt_access_minutes: int = 15
    jwt_refresh_days: int = 30
    cookie_secure: bool = False  # True en producción (HTTPS)
    zona_padres_minutes: int = 5
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
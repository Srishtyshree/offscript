from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Read from env vars or api/.env. Secrets never leave the backend."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    offscript_env: Literal["development", "production"] = "development"
    offscript_mode: Literal["live", "mock"] = "live"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    tinker_api_key: str = ""
    tinker_model_path: str = ""
    serpapi_api_key: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def model_configured(self) -> bool:
        return bool(self.tinker_api_key and self.tinker_model_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()

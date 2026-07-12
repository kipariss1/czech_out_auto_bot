from typing import Literal, TypedDict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


AppEnv = Literal["production", "local", "test"]
LLMProvider = Literal["local", "api-key"]


class PostgresData(TypedDict):
    user: str
    password: str
    db: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: AppEnv = "local"
    LLM: LLMProvider = "local"
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    WEBAPP_BASE_URL: str | None = Field(default=None, validation_alias="RENDER_EXTERNAL_URL")
    OLLAMA_MODEL: str = "gemma4:12b"
    OLLAMA_BASE_URL: str | None = None
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3-flash"
    
    @property
    def base_url(self) -> str | None:
        return self.WEBAPP_BASE_URL
    
    @property
    def env(self) -> AppEnv:
        return self.ENV

    @property
    def is_postgres_env(self) -> bool:
        return self.env in ("production", "local")

    @property
    def llm(self) -> LLMProvider:
        return self.LLM

    @property
    def ollama_model(self) -> str:
        return self.OLLAMA_MODEL

    @property
    def ollama_base_url(self) -> str:
        if self.OLLAMA_BASE_URL:
            return self.OLLAMA_BASE_URL
        return "http://ollama:11434" if self.env == "production" else "http://localhost:11434"

    @property
    def gemini_api_key(self) -> str | None:
        return self.GEMINI_API_KEY or None

    @property
    def gemini_model(self) -> str:
        return self.GEMINI_MODEL
    
    @property
    def postgres_data(self) -> PostgresData:
        if not self.is_postgres_env:
            raise ValueError(f"ENV type is '{self.env}', but Postgres settings were requested")

        if not self.POSTGRES_USER or not self.POSTGRES_PASSWORD or not self.POSTGRES_DB:
            raise ValueError(
                f"ENV type is '{self.env}' but Postgres data is missing, check the data below"
                + f"\n\t - User is {self.POSTGRES_USER}"
                + f"\n\t - Password is {'xxxxxxx' if self.POSTGRES_PASSWORD is not None else None}"
                + f"\n\t - DB name is {self.POSTGRES_DB}"
            )

        return {
            'user': self.POSTGRES_USER,
            'password': self.POSTGRES_PASSWORD,
            'db': self.POSTGRES_DB,
        }


settings = Settings()

from typing import Literal, TypedDict

import os
from pydantic_settings import BaseSettings


class PostgresData(TypedDict):
    user: str | None
    password: str | None
    db: str | None


class Settings(BaseSettings):
    ENV: Literal['production', 'test'] = os.getenv("ENV", "production") # type: ignore
    LLM: Literal["local", "api-key"] = os.getenv("LLM", "local") # type: ignore
    POSTGRES_USER: str | None = os.getenv("POSTGRES_USER", None)
    POSTGRES_PASSWORD: str | None = os.getenv("POSTGRES_PASSWORD", None)
    POSTGRES_DB: str | None = os.getenv("POSTGRES_DB", None)
    WEBAPP_BASE_URL: str | None = os.getenv("RENDER_EXTERNAL_URL")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma4:12b")
    OLLAMA_BASE_URL: str | None = os.getenv("OLLAMA_BASE_URL")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash")
    
    @property
    def base_url(self):
        return self.WEBAPP_BASE_URL
    
    @property
    def env(self) -> Literal['production', 'test']:
        return self.ENV

    @property
    def llm(self) -> Literal["local", "api-key"]:
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
        if any(x is None for x in (self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB)) and self.ENV == 'production':
            raise ValueError("ENV type is 'production' but Postgres data is missing, check the data below" 
                             + f"\n\t - User is {self.POSTGRES_USER}" 
                             + f"\n\t - Password is {'xxxxxxx' if self.POSTGRES_PASSWORD is not None else None}" 
                             + f"\n\t - DB name is {self.POSTGRES_DB}")
        return {
            'user': self.POSTGRES_USER,
            'password': self.POSTGRES_PASSWORD,
            'db': self.POSTGRES_DB
        }


settings = Settings()

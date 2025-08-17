import os
from pydantic_settings import BaseSettings
from typing import Literal, TypedDict


class PostgresData(TypedDict):
    user: str
    password: str
    db: str


class Settings(BaseSettings):
    ENV: Literal['production', 'test'] = os.getenv("ENV", "production")
    if ENV == 'production':
        POSTGRES_USER = os.getenv("POSTGRES_USER", None)
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", None)
        POSTGRES_DB = os.getenv("POSTGRES_DB", None)
    WEBAPP_BASE_URL: str = os.getenv("RENDER_EXTERNAL_URL")
    
    @property
    def base_url(self):
        return self.WEBAPP_BASE_URL
    
    @property
    def env(self) -> Literal['production', 'test']:
        return self.ENV
    
    @property
    def postgres_data(self) -> PostgresData:
        if any(x is None for x in (self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB)):
            raise ValueError("ENV type is 'production' but Postgres data is missing, check the data below" 
                             + f"\n\t - User is {self.POSTGRES_USER}" 
                             + f"\n\t - Password is {'xxxxxxx' if self.POSTGRES_PASSWORD is not None else None}" 
                             + f"\n\t - DB name is {self.POSTGRES_DB}")
        return {
            'user': self.POSTGRES_DB,
            'password': self.POSTGRES_PASSWORD,
            'db': self.POSTGRES_DB
        }


settings = Settings()

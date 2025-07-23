import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "production")
    DATABASE_URL: str = "sqlite:///./local.db"
    TEST_DATABASE_URL: str = "sqlite:///./test_local.db"

    @property
    def db_url(self):
        if self.ENV == "test":
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL


settings = Settings()

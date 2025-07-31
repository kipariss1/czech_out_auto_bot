import os
from pydantic_settings import BaseSettings
from src import SRC_DIR


class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "production")
    DATABASE_URL: str = f"sqlite:///./src/db/local.db"
    TEST_DATABASE_URL: str = f"sqlite:///./src/db/test.db"
    WEBAPP_BASE_URL: str = os.getenv("RENDER_EXTERNAL_URL")

    @property
    def db_url(self):
        if self.ENV == "test":
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL
    
    @property
    def base_url(self):
        return self.WEBAPP_BASE_URL


settings = Settings()

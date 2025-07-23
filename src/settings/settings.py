import os
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "production")
    SETTINGS_DIR: Path = Path(__file__).parent
    DATABASE_URL: str = f"sqlite:////{SETTINGS_DIR.parent / 'db' / 'local.db'}"
    TEST_DATABASE_URL: str = f"sqlite:////{SETTINGS_DIR.parent / 'db' / 'test_local.db'}"
    WEBAPP_BASE_URL: str = "https://czech-out-auto-bot-webapp.onrender.com"    # TODO: change later to env

    @property
    def db_url(self):
        if self.ENV == "test":
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL
    
    @property
    def base_url(self):
        return self.WEBAPP_BASE_URL


settings = Settings()

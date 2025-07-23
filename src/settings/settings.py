import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "production")
    DATABASE_URL: str = "sqlite:///./src/db/local.db"
    TEST_DATABASE_URL: str = "sqlite:///./src/db/test_local.db"
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

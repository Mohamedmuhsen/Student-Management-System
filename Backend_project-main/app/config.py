import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./student_management.db")
    secret_key: str = "change-this-in-production-use-env-file"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # السطر ده بيخليه يقرا المتغيرات من ملف .env لو موجود
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
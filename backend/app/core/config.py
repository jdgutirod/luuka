from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/habi"
    port: int = 8000

settings = Settings()

DATABASE_URL = settings.database_url
PORT = settings.port

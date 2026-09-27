from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/luuka"
    port: int = 8000
    secret_key: str
    access_token_expire_minutes: int = 30
    # Amounts are whole Colombian pesos (COP)
    min_transaction_amount: int = 1_000
    max_transaction_amount: int = 10_000_000
    # Comma separated origins allowed to call the API from a browser (e.g. the frontend)
    cors_origins: str = "http://localhost:5173"

settings = Settings()

DATABASE_URL = settings.database_url
PORT = settings.port
SECRET_KEY = settings.secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
MIN_TRANSACTION_AMOUNT = settings.min_transaction_amount
MAX_TRANSACTION_AMOUNT = settings.max_transaction_amount
CORS_ORIGINS = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

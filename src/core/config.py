from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    # Используем SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///pecs.db"
    
    # Веса для алгоритма ранжирования
    WEIGHT_USAGE_FACTOR: float = 2.0  # Множитель частоты
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Settings()

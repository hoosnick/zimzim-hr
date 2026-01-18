import os
from pathlib import Path
from typing import Final, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class PostgresConfig(BaseModel):
    POSTGRES_DB: str = "zim_attendance_db"
    POSTGRES_USER: str = "zim_attendance_user"
    POSTGRES_PASSWORD: str = "zim_attendance_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432

    @computed_field  # type: ignore
    @property
    def DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


class LoggingConfig(BaseModel):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    LOG_DIR: str = os.path.join(BASE_DIR, "logs")

    LOG_STD_LEVEL: str = "INFO"

    LOG_ACCESS_FILENAME: str = "access.log"
    LOG_ERROR_FILENAME: str = "error.log"


class TelegramConfig(BaseModel):
    TELEGRAM_BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    TELEGRAM_CHAT_ID: str = "-1001234567890"


class HikvisionConfig(BaseModel):
    APP_KEY: str = "YOUR_APP_KEY"
    SECRET_KEY: str = "YOUR_SECRET_KEY"

    SERVERS: Final[dict[str, str]] = {
        "russia": "https://hikcentralconnectru.com",
        "singapore": "https://isgp.hikcentralconnect.com",
        "india": "https://isgp.hikcentralconnect.com",
        "europe": "https://ieu.hikcentralconnect.com",
        "south_america": "https://isa.hikcentralconnect.com",
        "north_america": "https://ius.hikcentralconnect.com",
        "singapore_team": "https://isgp-team.hikcentralconnect.com",
    }

    # Default timeouts (in seconds)
    DEFAULT_TIMEOUT: float = 30.0
    DEFAULT_CONNECT_TIMEOUT: float = 10.0

    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 0.5


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    # Admin Panel
    LOGIN: str = "admin"
    PASSWORD: str = "admin123"

    # Don't run with debug turned on in production!
    DEBUG: bool = False

    # Turn it on in https
    PRODUCTION: bool = True

    # Max page size for pagination
    MAX_PAGE_SIZE: int = 500

    # allowed hosts and origins
    ALLOWED_HOSTS: list[str] = ["*"]
    ALLOWED_ORIGINS: list[str] = ["*"]

    # get piccolo orm config module
    PICCOLO_CONF: str = "core.piccolo_conf"

    OPENAPI_TITLE: str = "ZIM-ZIM HR Management API"
    OPENAPI_CONTACT: dict = {
        "name": "hoosnick",
        "url": "https://t.me/hoosnick",
    }

    WEB_APP_URL: str = "https://hr.zim-zim.uz"

    API_V1_STR: str = "/v1"

    REDIS_URL: str = "redis://localhost:6379"

    HTTP_WEBHOOK_URL: str = "http://example.com/webhook"

    # Hikvision Configuration
    HIK: HikvisionConfig = HikvisionConfig()

    # Database configuration
    DATABASE: PostgresConfig = PostgresConfig()

    # Logging configuration
    LOGGING: LoggingConfig = LoggingConfig()

    # Telegram Configuration
    TELEGRAM: TelegramConfig = TelegramConfig()


settings = Settings()

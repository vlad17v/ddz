import os

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str

    ES_HOST: str = "elasticsearch"
    ES_PORT: int = 9200
    ES_SCHEME: str = "http"
    ES_INDEX: str = "todos"
    ES_TIMEOUT: float = 10.0

    DATA_DIR: str = "data"
    IMAGES_DIR: str = "images"
    FILES_DIR: str = "files"
    IMPORTS_DIR: str = "files/imports"
    ATTACHMENTS_DIR: str = "files/attachments"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
    )


settings = Settings()


def get_db_url() -> str:
    return (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )


def get_auth_data() -> dict[str, str]:
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}


def get_es_url() -> str:
    return f"{settings.ES_SCHEME}://{settings.ES_HOST}:{settings.ES_PORT}"


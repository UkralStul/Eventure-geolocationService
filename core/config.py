from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    db_url: str = "postgresql+asyncpg://postgres:7243@localhost:5432/geoService"
    echo: bool = True


settings = Settings()

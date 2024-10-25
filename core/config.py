from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str = "postgresql+asyncpg://postgres:7243@localhost:5432/userService"
    echo: bool = True


settings = Settings()

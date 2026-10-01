from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    MONGO_URL: str

    MONGO_DB_NAME: str

    SECRET_KEY: str

    SMTP_HOST: str

    SMTP_PORT: int = 587

    SMTP_USERNAME: str

    SMTP_PASSWORD: str

    SMTP_FROM: str

    INITIAL_ADMIN_USERNAME: str
    INITIAL_ADMIN_EMAIL: str
    INITIAL_ADMIN_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()
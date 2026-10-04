from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    MONGO_URL: str

    MONGO_DB_NAME: str

    SECRET_KEY: str

    MAILERSEND_API_KEY: str
    MAILERSEND_FROM_EMAIL: str

    INITIAL_ADMIN_USERNAME: str
    INITIAL_ADMIN_EMAIL: str
    INITIAL_ADMIN_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()
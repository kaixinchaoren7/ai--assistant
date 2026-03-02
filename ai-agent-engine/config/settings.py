from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
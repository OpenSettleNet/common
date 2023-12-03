import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    payment_wallet: str


settings = Settings(
    _env_prefix="OPENSETTLENET_",
    _env_file=os.getenv("OPENSETTLENET_ENV_FILE", "opensettlenet.env"),
)

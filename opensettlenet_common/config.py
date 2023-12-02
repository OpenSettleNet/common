import os

from pydantic import BaseConfig


class Settings(BaseConfig):
    PAYMENT_WALLET: str

    class Config:
        env_prefix = "OPENSETTLENET_"
        env_file = os.getenv("OPENSETTLENET_ENV_FILE", "opensettlenet.env")


settings = Settings()

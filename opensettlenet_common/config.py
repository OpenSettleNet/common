import os

from pydantic import BaseConfig


class Settings(BaseConfig):
    payment_wallet: str

    class Config:
        env_prefix = "OPENSETTLENET_"
        env_file = os.getenv("OPENSETTLENET_ENV_FILE", "opensettlenet.env")


settings = Settings()

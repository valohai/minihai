import os
from pathlib import Path

from pydantic import BaseSettings

BASE_PATH = Path(__file__).parent.parent


class Settings(BaseSettings):
    data_path: Path = BASE_PATH / "data"


settings = Settings()
os.makedirs(settings.data_path, exist_ok=True)

import os
import sqlite3
from pathlib import Path

import docker
from pydantic import BaseSettings

BASE_PATH = Path(__file__).parent.parent


class Settings(BaseSettings):
    data_path: Path = BASE_PATH / "data"


settings = Settings()
os.makedirs(settings.data_path, exist_ok=True)
docker_client = docker.from_env()
cache_db = sqlite3.connect(
    settings.data_path / "cache.sqlite3", check_same_thread=False
)

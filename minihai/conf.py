import json
import logging
import os
import secrets
import sqlite3
import sys
from pathlib import Path
from typing import Dict

import docker
import pydantic
import yaml

BASE_PATH = Path(__file__).parent.parent
log = logging.getLogger(__name__)


def settings_yaml_source(settings: pydantic.BaseSettings):
    config_file = os.environ.get("MINIHAI_CONFIG")
    if config_file:
        log.info(f"Loading Minihai configuration from {config_file}")
        with open(config_file) as f:
            return yaml.safe_load(f)
    return {}


class Settings(pydantic.BaseSettings):
    data_path: Path = BASE_PATH / "data"
    mounts: Dict[str, str] = {}
    read_only_mounts: Dict[str, str] = {}
    jwt_secret: str = None
    auth: Dict[str, str] = {}

    def initialize(self):
        os.makedirs(self.data_path, exist_ok=True)
        jwt_secret_path = self.data_path / "jwt_secret.json"
        if jwt_secret_path.exists() or not self.jwt_secret:
            if not jwt_secret_path.exists():
                jwt_secret_path.write_text(
                    json.dumps({"secret": secrets.token_hex(64)})
                )
            self.jwt_secret = json.loads(jwt_secret_path.read_text())["secret"]

    class Config:
        env_prefix = "MINIHAI"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                env_settings,
                settings_yaml_source,
                file_secret_settings,
            )


# TODO: this initialization should probably happen a little more deferredly...

try:
    settings = Settings()
    settings.initialize()
except pydantic.ValidationError as ve:
    print("=================================================", file=sys.stderr)
    print("Minihai: Failed to load settings!", file=sys.stderr)
    print(ve, file=sys.stderr)
    print("=================================================", file=sys.stderr)
    sys.exit(9)

docker_client = docker.from_env()
cache_db = sqlite3.connect(
    str(settings.data_path / "cache.sqlite3"), check_same_thread=False
)

import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, Union

import docker
import pydantic
import yaml
from pydantic.utils import deep_update

BASE_PATH = Path(__file__).parent.parent
log = logging.getLogger(__name__)


class Settings(pydantic.BaseSettings):
    data_path: Path = BASE_PATH / "data"

    def _build_values(
        self, init_kwargs: Dict[str, Any], _env_file: Union[Path, str, None] = None
    ) -> Dict[str, Any]:
        values = super()._build_values(init_kwargs, _env_file)
        config_file = os.environ.get("MINIHAI_CONFIG")
        if config_file:
            log.info(f"Loading Minihai configuration from {config_file}")
            with open(config_file) as f:
                values = deep_update(values, yaml.safe_load(f))
        return values

    class Config:
        env_prefix = "MINIHAI"


# TODO: this initialization should probably happen a little more deferredly...

try:
    settings = Settings()
except pydantic.ValidationError as ve:
    print("=================================================", file=sys.stderr)
    print("Minihai: Failed to load settings!", file=sys.stderr)
    print(ve, file=sys.stderr)
    print("=================================================", file=sys.stderr)
    sys.exit(9)

os.makedirs(settings.data_path, exist_ok=True)
docker_client = docker.from_env()
cache_db = sqlite3.connect(
    settings.data_path / "cache.sqlite3", check_same_thread=False
)

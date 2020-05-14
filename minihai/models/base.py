import datetime
import json
import os
import pathlib
from typing import Iterable, Any

from fastapi.encoders import jsonable_encoder

from minihai.conf import settings


class DoesNotExist(Exception):
    pass


def sanitize_id(id: Any) -> str:
    return os.path.basename(str(id)).lower()


class BaseModel:
    kind = None
    path_group_len = 4

    @classmethod
    def get_base_path(cls, id: str) -> pathlib.Path:
        assert cls.kind
        id = sanitize_id(id)
        return settings.data_path / cls.kind / id.strip("~")[: cls.path_group_len] / id

    def __init__(self, *, id: str):
        self.id = sanitize_id(id)
        self.path = self.get_base_path(id)
        self.metadata_path = self.path / "metadata.json"

    @property
    def exists(self) -> bool:
        return self.path.exists() and self.metadata_path.exists()

    @property
    def metadata(self) -> dict:
        with open(self.metadata_path) as fp:
            return json.load(fp)

    @classmethod
    def load(cls, id):
        obj = cls(id=sanitize_id(id))
        if not obj.exists:
            raise DoesNotExist(f"{cls.__name__} with id {id!r} does not exist")
        return obj

    @classmethod
    def iterate_ids(cls) -> Iterable[str]:
        for dirpath, dirnames, filenames in os.walk(settings.data_path / cls.kind):
            for filename in filenames:
                if filename == "metadata.json":
                    yield os.path.basename(dirpath)

    @classmethod
    def iterate_instances(cls) -> Iterable:
        for id in cls.iterate_ids():
            yield cls(id=id)

    @classmethod
    def create_with_metadata(cls, id: str, data: dict):
        obj = cls(id=id)
        assert not obj.exists
        obj.path.mkdir(parents=True)
        with open(obj.metadata_path, "w") as outf:
            json.dump(
                {"id": id, "ctime": datetime.datetime.now().isoformat(), **data,},
                outf,
                default=jsonable_encoder,
                indent=2,
                sort_keys=True,
            )
        return obj

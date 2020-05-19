import datetime
import hashlib
import os
import posixpath
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from uuid import UUID

from minihai import conf
from minihai.lib.cache import Cache


def get_output_cache():
    return Cache(db=conf.cache_db, name="outputs")


@dataclass
class Output:
    execution_id: str
    name: str
    path: str  # relative to data_path
    _stat: Optional[os.stat_result] = None

    @property
    def disk_path(self):
        return Path(conf.settings.data_path) / self.path

    @property
    def stat(self) -> os.stat_result:
        if self._stat is None:
            self._stat = os.stat(self.disk_path)
        return self._stat

    @property
    def size(self) -> int:
        return self.stat.st_size

    @property
    def ctime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.stat.st_ctime)

    @property
    def id(self) -> UUID:
        hash_bits = f"{self.execution_id}+{self.name}+{self.size}"
        return UUID(bytes=hashlib.md5(hash_bits.encode()).hexdigest().encode()[:16])

    @property
    def download_url(self):
        return posixpath.join("/data/", self.path)

    def as_api_response(self) -> dict:
        return {
            "id": self.id,
            "size": self.size,
            "ctime": self.ctime,
            "file_ctime": self.ctime,
            "file_mtime": self.ctime,
            "name": self.name,
            "purged": False,
            "output_execution": {"id": self.execution_id,},
        }

    @classmethod
    def from_cache(cls, id: str) -> Optional["Output"]:
        data = get_output_cache().get(id)
        if not data:
            return None
        return cls(**data)

    def cache(self, cache: Cache):
        data = asdict(self)
        data.pop("_self", None)
        cache.set(self.id, data)

import json
import sqlite3
import time
from typing import Any, Dict

from fastapi.encoders import jsonable_encoder


class Cache:
    def __init__(self, db: sqlite3.Connection, name: str):
        self.db = db
        self.name = name
        self.db.execute(
            f"CREATE TABLE IF NOT EXISTS {self.name} (key TEXT PRIMARY KEY, value TEXT, ts INTEGER)"
        )

    def encode(self, value: Any) -> str:
        return json.dumps(value, default=jsonable_encoder)

    def decode(self, value: str) -> Any:
        return json.loads(value)

    def set_many(self, key_to_value: Dict[str, Any]):
        query = (
            f"INSERT INTO {self.name} "
            f"(key, value, ts) "
            f"VALUES (?, ?, ?) "
            f"ON CONFLICT (key) "
            f"DO UPDATE SET value=excluded.value, ts=excluded.ts"
        )
        return self.db.executemany(
            query,
            [
                (str(key), self.encode(value), time.time(),)
                for (key, value) in key_to_value.items()
            ],
        )

    def set(self, key: str, value: Any):
        return self.set_many({key: value})

    def get(self, key: str, default=None):
        query = f"SELECT value FROM {self.name} WHERE key = ? LIMIT 1"
        params = (key,)
        res = self.db.execute(query, params,)
        row = res.fetchone()
        if not row:
            return default
        return self.decode(row[0])

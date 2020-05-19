import sqlite3

from minihai.lib.cache import Cache


def test_cache(tmpdir):
    conn = sqlite3.connect(str(tmpdir.join("cache.sqlite3")))
    c1 = Cache(db=conn, name="one")
    assert c1.get("yay") is None
    obj = {"foo": [1, 2, [4, 8]]}
    c1.set("yay", obj)
    assert c1.get("yay") == obj
    c1.set_many({"yay": 123, "foop": 456})
    assert c1.get("yay") == 123
    assert c1.get("foop") == 456

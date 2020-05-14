import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from minihai.app import app

    return TestClient(app)

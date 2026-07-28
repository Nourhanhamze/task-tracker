import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app


@pytest.fixture(autouse=True)
def reset_storage():
    storage._reset()
    yield
    storage._reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def created_task(client):
    r = client.post("/tasks", json={"title": "Sample task"})
    return r.json()

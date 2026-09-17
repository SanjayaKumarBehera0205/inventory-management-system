import os

os.environ["DATABASE_URL"] = "sqlite:///./test_inventory.db"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth(client):
    client.post("/api/v1/auth/register", json={"name": "Manager", "email": "manager@example.com", "password": "password123"})
    login = client.post("/api/v1/auth/login", data={"username": "manager@example.com", "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}

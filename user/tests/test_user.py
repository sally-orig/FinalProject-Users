import pytest
from httpx import AsyncClient, ASGITransport
from ..models import User
from ..db import get_db
from ..main import app
from .test_db import setup_test_db, teardown_test_db, TestingSessionLocal, override_get_db
from datetime import datetime, timezone
from unittest.mock import MagicMock

@pytest.fixture(scope="module", autouse=True)
def prepare_database():
    setup_test_db()

    db = TestingSessionLocal()
    db.add_all([
        User(email="call@gmil.com", mobile="09231111890", firstName="Call", middleName="Me", lastName="Maybe",
                role="HR", status="inactive", created_at=datetime.now(timezone.utc)),
        User(email="test@hotmail.com", mobile="09010101010", firstName="Test", middleName="Li", lastName="Down",
                role="App Dev 2", status="active", created_at=datetime.now(timezone.utc)),
        User(email="sample@hotmail.com", mobile="09222222222", firstName="Alice", middleName="In", lastName="Wonder",
                role="App Dev 1", status="active", created_at=datetime.now(timezone.utc)),
    ])
    db.commit()
    db.close()

    yield
    teardown_test_db()


# Test cases for get all users
@pytest.mark.asyncio
async def test_get_all_users():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3

@pytest.mark.asyncio
async def test_get_all_users_empty_db():
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.all.return_value = []
    mock_session.query.return_value = mock_query

    def override_empty_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_empty_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users")
    assert response.status_code == 200
    assert response.json() == {"detail": "No users found"}
    app.dependency_overrides[get_db] = override_get_db

# Test cases for get user by ID
@pytest.mark.asyncio
async def test_get_user_by_id():
    transport = ASGITransport(app=app)
    TEST_ID = 2
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/users/{TEST_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TEST_ID
    assert data["email"] == "test@hotmail.com"
    assert data["mobile"] == "09010101010"
    assert data["firstName"] == "Test"
    assert data["middleName"] == "Li"
    assert data["lastName"] == "Down"
    assert data["role"] == "App Dev 2"
    assert data["status"] == "active"

@pytest.mark.asyncio
async def test_get_user_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/users/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

@pytest.mark.asyncio
async def test_get_user_invalid_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users/invalid_id")
    assert response.status_code == 422
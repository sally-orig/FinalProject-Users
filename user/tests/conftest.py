import pytest
from httpx import AsyncClient, ASGITransport
from ..main import app
from .test_db import setup_test_db, teardown_test_db, TestingSessionLocal
from ..models import User, Credential, RefreshToken
from ..auth.auth import get_password_hash, save_refresh_token
from datetime import datetime, timezone
import uuid
from fastapi import Request

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    setup_test_db()
    yield
    teardown_test_db()

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def create_user_token(client: AsyncClient):
    db = TestingSessionLocal()

    user1 = User(email="call@gmil.com", mobile="09231111890", firstName="Call", middleName="Me", lastName="Maybe", completeName="Call Me Maybe",
                 role="HR", status="inactive", created_at=datetime.now(timezone.utc))
    user2 = User(email="test@hotmail.com", mobile="09010101010", firstName="Test", middleName="Li", lastName="Down", completeName="Test Li Down",
                 role="App Dev 2", status="active", created_at=datetime.now(timezone.utc))
    user3 = User(email="sample@hotmail.com", mobile="09222222222", firstName="Alice", middleName="In", lastName="Wonder", completeName="Alice In Wonder",
                 role="App Dev 1", status="active", created_at=datetime.now(timezone.utc))

    db.add_all([user1, user2, user3])
    db.commit()  
    
    db.refresh(user1)
    db.refresh(user2)
    db.refresh(user3)

    credentials = [
        Credential(user_id=user1.id, username="testuser", hashed_password=get_password_hash("testpass")),
        Credential(user_id=user2.id, username="test121_user", hashed_password="hashed_pw_2"),
        Credential(user_id=user3.id, username="alice_user", hashed_password="hashed_pw_3"),
    ]
    db.add_all(credentials)
    db.commit()
    db.close()

    response = await client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass"},
    )
    assert response.status_code == 200, f"Token generation failed: {response.text}"
    token = response.json()["access_token"]
    return f"Bearer {str(token)}"

@pytest.fixture
async def create_user_for_auth(client: AsyncClient):
    db = TestingSessionLocal()
    try:
        user = User(
            email=f"call+{uuid.uuid4()}@gmil.com",
            mobile="09231111890",
            firstName="Call",
            middleName="Me",
            lastName="Maybe",
            completeName="Call Me Maybe",
            role="HR",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        credential = Credential(
            user_id=user.id,
            username=f"testuser_{uuid.uuid4()}",
            hashed_password=get_password_hash("testpass"),
        )
        db.add(credential)

        db.commit()

        response = await client.post(
            "/auth/token",
            data={"username": credential.username, "password": "testpass"},
        )

        assert response.status_code == 200, f"Token generation failed: {response.text}"
        return response.json()
    finally:
        db.close()
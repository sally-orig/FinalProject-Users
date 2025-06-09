import pytest
from httpx import AsyncClient
from .test_db import TestingSessionLocal
from ..models import User, Credential
from ..auth import get_password_hash
from ..main import app
from httpx import ASGITransport

@pytest.mark.asyncio
async def test_token_endpoint():
    db = TestingSessionLocal()
    try:
        user = User(
            email="call@gmil.com",
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
            username="testuser",
            hashed_password=get_password_hash("testpass"),
        )
        db.add(credential)
        db.commit()
    finally:
        db.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpass"},
        )

    assert response.status_code == 200, f"Failed with response: {response.text}"
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_unauthorized(client):
    response = await client.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpass"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


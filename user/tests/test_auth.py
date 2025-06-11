import pytest
from httpx import AsyncClient
from .test_db import TestingSessionLocal
from ..models import User, Credential
from ..auth import get_password_hash
from ..main import app
from httpx import ASGITransport
from datetime import datetime, timedelta, UTC
from jose import jwt
from ..auth import SECRET_KEY, ALGORITHM

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
    assert "refresh_token" in json_data
    assert json_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_unauthorized(client):
    response = await client.post(
            "/auth/token",
            data={"username": "testuser", "password": "testpass"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

@pytest.mark.asyncio
async def test_access_token_undefined(client):
    invalid_token = "undefined"
    response = await client.get(
        "/users",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing access token"}

@pytest.mark.asyncio
async def test_access_token_user_not_found(client):
    to_encode = {"exp": datetime.now(UTC) + timedelta(minutes=30), "token_type": "access"}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    response = await client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "User ID not found in token"}

@pytest.mark.asyncio
async def test_access_token_invalid_type(client):
    to_encode = {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=30), "token_type": "refresh"}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    response = await client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token type"}

@pytest.mark.asyncio
async def test_access_token_expired(client):
    to_encode = {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=30), "token_type": "access"}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    response = await client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Token has expired"}

@pytest.mark.asyncio
async def test_refresh_token_success(client, create_user_for_auth):
    data = create_user_for_auth
    response = await client.post(
        "/auth/token/refresh",
        headers={"Authorization": f"Bearer {data["access_token"]}"},
        json={"refresh_token": data["refresh_token"]},
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert "refresh_token" in json_data
    assert json_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_refresh_token_expired(client, create_user_for_auth):
    user = create_user_for_auth
    to_encode = {"sub": "1", "exp": datetime.now(UTC) - timedelta(days=100), "token_type": "refresh"}
    expired_refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    response = await client.post(
        "/auth/token/refresh",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"refresh_token": expired_refresh_token},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh token has expired"}

@pytest.mark.asyncio
async def test_refresh_token_invalid(client, create_user_for_auth):
    user = create_user_for_auth
    to_encode = {"sub": "1", "exp": datetime.now(UTC) - timedelta(days=100), "token_type": "refresh"}
    expired_refresh_token = jwt.encode(to_encode, "invalidsecret", algorithm=ALGORITHM)
    response = await client.post(
        "/auth/token/refresh",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"refresh_token": expired_refresh_token},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid refresh token"}

async def test_refresh_token_invalid_token_type(client, create_user_for_auth):
    user = create_user_for_auth
    to_encode = {"sub": "1", "exp": datetime.now(UTC) + timedelta(days=7), "token_type": "access"}
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    response = await client.post(
        "/auth/token/refresh",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token type"}

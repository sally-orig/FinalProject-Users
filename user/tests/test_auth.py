import pytest
from httpx import AsyncClient
from .test_db import TestingSessionLocal
from ..models import User, Credential, RefreshToken
from ..auth.auth import get_password_hash
from ..main import app
from httpx import ASGITransport
from datetime import datetime, timedelta, UTC
from jose import jwt
from uuid import uuid4
from ..auth.auth import SECRET_KEY, ALGORITHM

@pytest.mark.asyncio
async def test_token_success():
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
@pytest.mark.parametrize(
    "token_payload, expected_detail",
    [
        # success case
        ({"exp": datetime.now(UTC) + timedelta(minutes=30), "token_type": "access"}, "User ID not found in token"),
        # invalid token type
        ({"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=30), "token_type": "refresh"}, "Invalid token type"),
        # expired token
        ({"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=30), "token_type": "access"}, "Token has expired"),
    ]
)
async def test_access_token_errors(client, token_payload, expected_detail):
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    response = await client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": expected_detail}

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "refresh_token_payload, secret, expected_status, expected_detail",
    [
        # success case
        ({"sub": "1", "exp": datetime.now(UTC) + timedelta(days=30), "token_type": "refresh", "jti": str(uuid4())}, SECRET_KEY, 200, None),
        # expired token
        ({"sub": "1", "exp": datetime.now(UTC) - timedelta(days=100), "token_type": "refresh", "jti": str(uuid4())}, SECRET_KEY, 401, "Token has expired"),
        # invalid signature
        ({"sub": "1", "exp": datetime.now(UTC) + timedelta(days=30), "token_type": "refresh", "jti": str(uuid4())}, "invalidsecret", 401, "Invalid token"),
        # invalid token type
        ({"sub": "1", "exp": datetime.now(UTC) + timedelta(days=7), "token_type": "access", "jti": str(uuid4())}, SECRET_KEY, 400, "Invalid token type"),
    ]
)
async def test_refresh_token_errors(client, create_user_token, refresh_token_payload, secret, expected_status, expected_detail):
    user = create_user_token
    access_token_payload = {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=30), "token_type": "access", "jti": str(uuid4())}
    access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_token_payload, secret, algorithm=ALGORITHM)
    jti = refresh_token_payload.get("jti")

    # Insert the refresh token in DB if this is the success case to simulate valid token
    if expected_status == 200:
        db = TestingSessionLocal()
        db_token = RefreshToken(
            jti=jti,
            user_id=1,
            expires_at=datetime.now(UTC) + timedelta(days=30)
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        db.close()

    response = await client.post(
        "/auth/token/refresh",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    print(response.json())  # For debugging purposes
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json() == {"detail": expected_detail}
    else:
        # success assertions
        json_data = response.json()
        assert "access_token" in json_data
        assert "refresh_token" in json_data
        assert json_data["token_type"] == "bearer"

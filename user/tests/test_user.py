import pytest
from ..db import get_db
from ..main import app
from ..models import User, Credential
from .test_db import TestingSessionLocal, override_get_db
from unittest.mock import MagicMock

# Test cases for get all users
@pytest.mark.asyncio
@pytest.mark.parametrize("offset, limit, status, expected_count", [
    (0, 10, None, 3),  # Default case
    (1, 2, None, 2),   # Offset by 1, limit to 2
    (0, 2, None, 2),   # Limit to 2
    (0, 5, None, 3),    # Limit greater than total count
    (0, 10, "active", 2),  # Filter by active status
])
async def test_get_all_users(client, create_user_token, offset, limit, status, expected_count):
    token = create_user_token
    params = {"offset": offset, "limit": limit}
    if status:
        params["status"] = status
    response = await client.get("/users", headers={"Authorization": token}, params=params)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert len(data["data"]) == expected_count

@pytest.mark.asyncio
async def test_get_all_users_empty_db(client, create_user_token):
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.all.return_value = []
    mock_session.query.return_value = mock_query

    def override_empty_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_empty_db

    token = create_user_token
    response = await client.get("/users", headers={"Authorization": token})
    assert response.status_code == 200
    assert response.json() == {"detail": "No users found"}
    app.dependency_overrides[get_db] = override_get_db

# Test cases for get user by ID
@pytest.mark.asyncio
async def test_get_user_by_id(client, create_user_token):
    TEST_ID = 2
    token = create_user_token
    response = await client.get(f"/users/{TEST_ID}", headers={"Authorization": token})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TEST_ID
    assert data["email"] == "test@hotmail.com"
    assert data["mobile"] == "09010101010"
    assert data["firstName"] == "Test"
    assert data["middleName"] == "Li"
    assert data["lastName"] == "Down"
    assert data["completeName"] == "Test Li Down"
    assert data["role"] == "App Dev 2"
    assert data["status"] == "active"

@pytest.mark.asyncio
async def test_get_user_not_found(client, create_user_token):
    token = create_user_token
    response = await client.get("/users/999", headers={"Authorization": token})

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

@pytest.mark.asyncio
async def test_get_user_invalid_id(client, create_user_token):
    token = create_user_token
    response = await client.get("/users/invalid_id", headers={"Authorization": token})
    
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_user_success(client):
    user_data = {
        "email": "newuser@example.com",
        "mobile": "09123456789",
        "firstName": "New",
        "middleName": "Test",
        "lastName": "User",
        "username": "newuser",
        "plain_password": "newuserpassword",
        "role": "User"
    }

    response = await client.post("/users/register", json=user_data)
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email1, email2, username1, username2, expected_status, expected_detail", 
    [
        ("exists@example.com", "another@example.com", "testuser", "testuser", 400, "Username already exists"),
        ("duplicate@example.com", "duplicate@example.com", "testuser", "testuser1", 400, "Email already exists")
    ])
async def test_register_user_fail_duplicate_email_username (client, email1, email2, username1, username2, expected_status, expected_detail):
    db = TestingSessionLocal()
    from ..auth.auth import get_password_hash
    from datetime import datetime, timezone

    user = User(
        email=email1,
        mobile="09999999999",
        firstName="Dup",
        middleName="Name",
        lastName="User",
        completeName="Dup Name User",
        role="User",
        status="active",
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    cred = Credential(user_id=user.id, username=username1, hashed_password=get_password_hash("testpass"))
    db.add(cred)
    db.commit()
    db.close()

    user_data = {
        "email": email2,
        "mobile": "09123456780",
        "firstName": "Another",
        "middleName": "Test",
        "lastName": "User",
        "username": username2,
        "plain_password": "testpass",
        "role": "User"
    }

    response = await client.post("/users/register", json=user_data)
    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}

@pytest.mark.asyncio
@pytest.mark.parametrize("method, endpoint, mobile, email,expected_status", [
    ("post", "register", "11", "duplicate@example.com", 422), # Too short mobile: /register
    ("post", "register", "091234567890", "duplicate@example.com", 422), # Too long mobile: /register
    ("post", "register", "string", "duplicate@example.com", 422), # Invalid mobile: /register
    ("post", "register", "09112222222", "invalid-email", 422), # Invalid email: /register
    ("put", "update/1", "11", "duplicate@example.com", 422), # Too short mobile: /update/1
    ("put", "update/1", "091234567890", "duplicate@example.com", 422), # Too long mobile: /update/1
    ("put", "update/1", "string", "duplicate@example.com", 422), # Invalid mobile: /update/1
    ("put", "update/1", "09112222222", "invalid-email", 422), # Invalid email: /update/1
])
async def test_user_invalid_mobile_email(client, create_user_token, method, endpoint, mobile, email, expected_status):
    token = create_user_token
    user_data = {
        "email": email,
        "mobile": mobile,
        "firstName": "Another",
        "middleName": "Test",
        "lastName": "User",
        "username": "testuser",
        "plain_password": "testpass",
        "role": "User"
    }
    request_method = getattr(client, method.lower())
    response = await request_method(f"/users/{endpoint}", headers={"Authorization": token}, json=user_data)
    assert response.status_code == expected_status

@pytest.mark.asyncio
async def test_update_user_success(client, create_user_token):
    token = create_user_token
    update_data = {
        "email": "updated@example.com",
        "mobile": "09112223333",
        "firstName": "Updated",
        "middleName": "User",
        "lastName": "Example",
        "role": "Admin"
    }

    TEST_ID = 1
    response = await client.put(f"/users/update/{TEST_ID}", headers={"Authorization": token}, json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TEST_ID
    assert data["email"] == "updated@example.com"
    assert data["mobile"] == "09112223333"
    assert data["firstName"] == "Updated"
    assert data["middleName"] == "User"
    assert data["lastName"] == "Example"
    assert data["completeName"] == "Updated User Example"
    assert data["role"] == "Admin"
    assert data["status"] == "inactive"

@pytest.mark.asyncio
async def test_update_user_not_found(client, create_user_token):
    token = create_user_token
    update_data = {
        "email": "updated@example.com",
        "mobile": "09112223333",
        "firstName": "Updated",
        "middleName": "User",
        "lastName": "Example",
        "role": "Admin"
    }

    TEST_ID = 999
    response = await client.put(f"/users/update/{TEST_ID}", headers={"Authorization": token}, json=update_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

@pytest.mark.asyncio
@pytest.mark.parametrize("test_id, expected_status, expected_response", [
    (1, 200, "Password changed successfully"),
    (999, 404, "User not found")
])
async def test_change_password_success_not_found(client, create_user_for_auth, test_id, expected_status, expected_response):
    token = create_user_for_auth
    refresh_token = token["refresh_token"]
    change_data = {
        "body": {
            "current_password": "testpass",
            "new_password": "newtestpass"
            },
        "refresh_token": refresh_token
    }
    
    response = await client.put(
        f"/users/change/password/{test_id}", 
        headers={"Authorization": f"Bearer {token["access_token"]}"}, 
        json=change_data)

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_response}

@pytest.mark.asyncio
async def test_change_user_password_wrong_password(client, create_user_for_auth):
    token = create_user_for_auth
    refresh_token = token["refresh_token"]
    change_data = {
        "body": {
            "current_password": "wrongpass",
            "new_password": "newtestpass"
            },
        "refresh_token": refresh_token
    }

    TEST_ID = 1
    response = await client.put(f"/users/change/password/{TEST_ID}", headers={"Authorization": f"Bearer {token["access_token"]}"}, json=change_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Credential not found"}

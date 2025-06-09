import pytest
from ..db import get_db
from ..main import app
from ..models import User, Credential
from .test_db import TestingSessionLocal, override_get_db
from unittest.mock import MagicMock

# Test cases for get all users
@pytest.mark.asyncio
async def test_get_all_users(client, create_user_token):
    token = create_user_token
    response = await client.get("/users", headers={"Authorization": token})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3

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
async def test_register_user_fail_duplicate_username(client):
    db = TestingSessionLocal()
    from ..auth import get_password_hash
    from datetime import datetime, timezone

    user = User(
        email="exists@example.com",
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

    cred = Credential(user_id=user.id, username="testuser", hashed_password=get_password_hash("testpass"))
    db.add(cred)
    db.commit()
    db.close()

    user_data = {
        "email": "another@example.com",
        "mobile": "09123456780",
        "firstName": "Another",
        "middleName": "Test",
        "lastName": "User",
        "username": "testuser",
        "plain_password": "testpass",
        "role": "User"
    }

    response = await client.post("/users/register", json=user_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already exists"}

@pytest.mark.asyncio
async def test_register_user_fail_duplicate_email(client):
    db = TestingSessionLocal()
    from ..auth import get_password_hash
    from datetime import datetime, timezone

    user = User(
        email="duplicate@example.com",
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

    cred = Credential(user_id=user.id, username="testuser1", hashed_password=get_password_hash("testpass"))
    db.add(cred)
    db.commit()
    db.close()

    user_data = {
        "email": "duplicate@example.com",
        "mobile": "09123456780",
        "firstName": "Another",
        "middleName": "Test",
        "lastName": "User",
        "username": "testuser",
        "plain_password": "testpass",
        "role": "User"
    }

    response = await client.post("/users/register", json=user_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already exists"}

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
    assert response.json() == {"message": "User updated successfully"}

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

    assert response.status_code == 400
    assert response.json() == {"detail": "User not found"}

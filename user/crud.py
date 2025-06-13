from sqlalchemy.orm import Session
from .models import User, Credential, RefreshToken
from .schemas import UserOut, PaginatedResponse, UserCreate, UserUpdate
from .auth.auth import get_password_hash, verify_password, verify_refresh_token
from typing import Optional
from datetime import datetime, timezone

def get_all_users(db: Session, offset: int = 0, limit: int = 20, status: Optional[str] = None) -> PaginatedResponse:
    """
    Retrieve a list of users from the database. Can be filtered by status and paginated.
    Args:
        db (Session): The database session.
        offset (int): The starting point for the query (for pagination).
        limit (int): The maximum number of records to return.
        status (Optional[str]): The status to filter users by (e.g., 'active', 'inactive'). Defaults to None.

    Returns:
        dict: A list of UserOut schemas representing the users and pagination in a dictionary.
    """
    if status:
        data = db.query(User).filter(User.status == status.value if hasattr(status, "value") else status).offset(offset).limit(limit).all()
    else:
        data = db.query(User).offset(offset).limit(limit).all()

    formatted_data = []
    for user in data:
        user_dict = UserOut.model_validate(user).model_dump()
        user_dict['completeName'] = f"{user.firstName} {user.middleName or ''} {user.lastName}".strip()
        formatted_data.append(user_dict)

    return PaginatedResponse(
        data=formatted_data if formatted_data else [],
        totalCount=db.query(User).count(),
        limit=limit,
        offset=offset
    )

def get_user_by_id(db: Session, user_id: int) -> UserOut | None:
    """
    Retrieve a user by their ID.
    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to retrieve.

    Returns:
        UserOut | None: A UserOut schema representing the user, or None if not found.
    """
    return db.query(User).filter(User.id == user_id).first()

def generate_complete_name(first_name: str, middle_name: Optional[str], last_name: str) -> str:
    """
    Generate a complete name from first, middle, and last names.
    Args:
        first_name (str): The first name of the user.
        middle_name (Optional[str]): The middle name of the user, can be None.
        last_name (str): The last name of the user.

    Returns:
        str: The complete name formatted as "First Middle Last".
    """
    return f"{first_name} {middle_name or ''} {last_name}".strip()

def create_user(db: Session, user_data: UserCreate) -> None:
    """
    Create a new user in the database.
    Args:
        db (Session): The database session.
        user_data (UserOut): The data for the user to be created.

    Returns:
        None: This function does not return anything. It commits the new user to the database.
    """
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    existing_username = db.query(Credential).filter(Credential.username == user_data.username).first()
    if existing_email:
        raise ValueError("Email already exists")
    if existing_username:
        raise ValueError("Username already exists")

    username = user_data.username
    plain_password = user_data.plain_password
    hashed_password = get_password_hash(plain_password)
    
    user_dict = user = user_data.model_dump(exclude={"username", "plain_password"})
    user_dict["completeName"] = generate_complete_name(
        first_name=user_data.firstName,
        middle_name=user_data.middleName or None,
        last_name=user_data.lastName
    )
    user = User(**user_dict)
    try:
        db.add(user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    
    credential = Credential(
        user_id=user.id,
        username=username,
        hashed_password=hashed_password
    )
    try:
        db.add(credential)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(credential)

def update_user(db: Session, user_id: int, user_data: UserUpdate) -> UserOut:
    """
    Update an existing user in the database.
    Args:
        db (Session): The database session.
        user_id (int): The ID of the user to update.
        user_data (UserUpdate): The new data for the user.

    Returns:
        UserOut: A UserOut schema representing the updated user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    for key, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    user.updated_at = datetime.now(timezone.utc)
    if user_data.firstName or user_data.middleName or user_data.lastName:
        user.completeName = generate_complete_name(
            first_name=user.firstName,
            middle_name=user.middleName or None,
            last_name=user.lastName
        )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)

    return UserOut.model_validate(user).model_dump()

def change_password(db: Session, user_id: int, current_password: str, new_password: str, refresh_token: str) -> None:
    """
    Change the password for a user.
    Args:
        db (Session): The database session.
        user_id (int): The ID of the user whose password is to be changed.
        current_password (str): The current password of the user to verify.
        new_password (str): The new password to set.
        refresh_token (str): The refresh token to invalidate after password change.

    Returns:
        None: This function does not return anything. It commits the new password to the database.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    print(get_password_hash(current_password))
    credential = db.query(Credential).filter(Credential.user_id == user_id).first()
    if not verify_password(current_password, credential.hashed_password):
        raise ValueError("Credential not found")

    credential.hashed_password = get_password_hash(new_password)
    credential.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(credential)

    user_id_from_token = verify_refresh_token(refresh_token, db)


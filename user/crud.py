from sqlalchemy.orm import Session
from .models import User, Credential
from .schemas import UserOut, PaginatedResponse, UserCreate
from .auth import get_password_hash
from typing import Optional

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

    user = User(**user_data.model_dump(exclude={"username", "plain_password"}))
    db.add(user)
    db.commit()
    db.refresh(user)
    
    credential = Credential(
        user_id=user.id,
        username=username,
        hashed_password=hashed_password
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)



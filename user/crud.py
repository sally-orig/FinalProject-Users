from sqlalchemy.orm import Session
from .models import User
from .schemas import UserOut, PaginatedResponse
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
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from .crud import get_all_users, get_user_by_id, create_user
from .db import get_db
from .schemas import PaginatedResponse, UserOut, StatusEnum, UserCreate
from typing import Optional

router = APIRouter()

@router.get("", response_model=PaginatedResponse, summary="Get all users", description="Retrieve a paginated list of all users.")
async def get_users(status: Optional[StatusEnum] = Query(None, description="Filter users by status (active/inactive)"), 
                    offset: int = Query(0, ge=0, description="Start index"), limit: int = Query(10, ge=1, description="Maximum number of users to return"), 
                    db: Session = Depends(get_db)):
    users = get_all_users(db, offset=offset, limit=limit, status=status)
    if not(users.data):
        raise HTTPException(status_code=200, detail="No users found")
    return users

@router.get("/{user_id}", response_model=UserOut, summary="Get user by ID", description="Retrieve a user by their unique ID.")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/register", response_model=None, status_code=status.HTTP_201_CREATED, summary="Register a new user", description="Create a new user with the provided details.")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User created successfully"}
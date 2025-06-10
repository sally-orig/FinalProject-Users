from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from .crud import get_all_users, get_user_by_id, create_user, update_user, change_password
from .db import get_db
from .schemas import PaginatedResponse, UserOut, StatusEnum, UserCreate, UserUpdate
from .logger import logger, log_action
from .schemas import ActionLogEnum, ActionLogActionsEnum, CredentialUpdate
from .auth import get_current_user
from typing import Optional

router = APIRouter()

@router.get("", response_model=PaginatedResponse, summary="Get all users", description="Retrieve a paginated list of all users.")
async def get_users(status: Optional[StatusEnum] = Query(None, description="Filter users by status (active/inactive)"), 
                    offset: int = Query(0, ge=0, description="Start index"), limit: int = Query(10, ge=1, description="Maximum number of users to return"), 
                    db: Session = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
    users = get_all_users(db, offset=offset, limit=limit, status=status)
    if not(users.data):
        logger.warning("GET /users - No users found")
        raise HTTPException(status_code=200, detail="No users found")
    logger.info("GET /users - retrieving all users successfully")
    return users

@router.get("/{user_id}", response_model=UserOut, summary="Get user by ID", description="Retrieve a user by their unique ID.")
async def get_user(user_id: int, db: Session = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
    user = get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"GET /users/{user_id} - user not found")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"GET /users/{user_id} - get user details successfully")
    return user

@router.post("/register", response_model=None, status_code=status.HTTP_201_CREATED, summary="Register a new user", description="Create a new user with the provided details.")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        create_user(db, user_data)
    except ValueError as e:
        logger.error(f"Register failed for username {user_data.username}: {str(e)}")
        log_action(db, username=user_data.username, action=ActionLogEnum.register_user, status=ActionLogActionsEnum.failed)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while registering user {user_data.username}: {str(e)}")
        log_action(db, username=user_data.username, action=ActionLogEnum.register_user, status=ActionLogActionsEnum.failed)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    logger.info(f"User created successfully: username={user_data.username}")
    log_action(db, username=user_data.username, action=ActionLogEnum.register_user, status=ActionLogActionsEnum.success)
    return {"message": "User created successfully"}

@router.put("/update/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK, summary="Update user details", description="Update the details of an existing user.")
async def update_user_by_id(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
    try:
        user = update_user(db, user_id, user_data)
    except ValueError as e:
        logger.error(f"Update failed for user ID {user_id}: {str(e)}")
        log_action(db, user_id=user_id, action=ActionLogEnum.update_user, status=ActionLogActionsEnum.failed)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while updating user ID {user_id}: {str(e)}")
        log_action(db, user_id=user_id, action=ActionLogEnum.update_user, status=ActionLogActionsEnum.failed)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    logger.info(f"User updated successfully: user_id={user_id}")
    log_action(db, user_id=user_id, action=ActionLogEnum.update_user, status=ActionLogActionsEnum.success)
    return user

@router.put("/change/password/{user_id}", status_code=status.HTTP_200_OK, summary="Change user password", description="Change the password of an existing user.")
async def change_user_password(user_id: int, body: CredentialUpdate, db: Session = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
    try:
        change_password(db, user_id, body.current_password, body.new_password)
        logger.info(f"Changed password successfully for user ID: {user_id}")
        log_action(db, user_id=user_id, action=ActionLogEnum.change_password, status=ActionLogActionsEnum.success)
    except ValueError as e:
        logger.error(f"Change password failed for user ID {user_id}: {str(e)}")
        log_action(db, user_id=user_id, action=ActionLogEnum.change_password, status=ActionLogActionsEnum.failed)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error while changing password for user ID {user_id}: {str(e)}")
        log_action(db, user_id=user_id, action=ActionLogEnum.change_password, status=ActionLogActionsEnum.failed)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    return {"message": "Password changed successfully"}
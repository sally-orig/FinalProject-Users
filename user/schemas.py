from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
from enum import Enum
from datetime import datetime
from typing import Optional, List, Any

class StatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"

class ActionLogActionsEnum(str, Enum):
    success = "success"
    failed = "failed"

class ActionLogEnum(str, Enum):
    register_user = "register_user"
    update_user = "update_user"
    login = "login"
    logout = "logout"
    generate_token = "generate_token"
    verify_token = "verify_token"
    change_password = "change_password"

class ActionLogBase(BaseModel):
    user_id: int
    user_name: str
    action: ActionLogEnum
    status: str
    timestamp: datetime

class ActionLogOut(ActionLogBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )

class PaginatedResponse(BaseModel):
    totalCount: int
    offset: int
    limit: int
    data: List[Any]

    model_config = ConfigDict(
        from_attributes=True
    )

class UserBase(BaseModel):
    email: EmailStr
    mobile: str = Field(..., min_length=10, max_length=11)
    firstName: str
    middleName: Optional[str] = None
    lastName: str
    role: str
class UserOut(UserBase):
    id: int
    completeName: str
    status: StatusEnum = StatusEnum.active
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )

class UserCreate(UserBase):
    username: str
    plain_password: str
    mobile: str = Field(..., min_length=10, max_length=11, pattern=r'^\d+$')

    model_config = ConfigDict(
        from_attributes=True
    )

class UserUpdate(UserBase):
    firstName: Optional[str] = None
    middleName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(default=None, min_length=10, max_length=11, pattern=r'^\d+$')
    role: Optional[str] = None

class CredentialUpdate(BaseModel):
    current_password: str
    new_password: str

    model_config = ConfigDict(
        from_attributes=True
    )
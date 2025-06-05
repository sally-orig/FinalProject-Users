from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum
from datetime import datetime
from typing import Optional, List, Any

class StatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"

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

    model_config = ConfigDict(
        from_attributes=True
    )

class UserCreate(UserBase):
    username: str
    plain_password: str

    model_config = ConfigDict(
        from_attributes=True
    )
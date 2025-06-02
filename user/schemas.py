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
    status: StatusEnum = StatusEnum.active
    created_at: datetime

class UserOut(UserBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )

class UserCreate(BaseModel):
    email: str
    mobile: str
    firstName: str
    middleName: str
    lastName: str
    role: str
    status: str
    created_at: datetime
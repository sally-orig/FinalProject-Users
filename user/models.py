from sqlalchemy import Column, Integer, String, DateTime
from .db import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile = Column(String(11), nullable=False)
    firstName = Column(String(255), nullable=False)
    middleName = Column(String(255), nullable=True)
    lastName = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, nullable=False)
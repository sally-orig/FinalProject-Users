from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile = Column(String(11), nullable=False)
    firstName = Column(String(255), nullable=False)
    middleName = Column(String(255), nullable=True)
    lastName = Column(String(255), nullable=False)
    completeName = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)

    credential = relationship("Credential", back_populates="user", uselist=False, cascade="all, delete")
class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="credential")
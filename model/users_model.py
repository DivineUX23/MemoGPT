from sqlalchemy import Text, Column, ForeignKey, Integer, String, LargeBinary, DateTime, JSON, Boolean
from database.db import Base
from sqlalchemy.orm import Relationship
from datetime import datetime


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    summaries = Relationship("Summary", cascade="all, delete-orphan")
    histories = Relationship("History", cascade="all, delete-orphan")
    audio = Relationship("Audio", cascade="all, delete-orphan")
    verification_token = Column(String(255))
    is_verified = Column(Boolean, default=False)
from sqlalchemy import Text, Column, ForeignKey, Enum, Integer, String, LargeBinary, DateTime, JSON, Boolean
from database.db import Base
from sqlalchemy.orm import Relationship
from datetime import datetime, timedelta


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

    paid_start = Column(DateTime)
    paid_duration = Column(Integer)

    def is_paid(self):
        if self.paid_start and self.paid_duration:
            return self.paid_start + timedelta(days=self.paid_duration) > datetime.utcnow()
        else:
            return False
from sqlalchemy import Text, Column, ForeignKey, Integer, String, LargeBinary, DateTime, JSON
from database.db import Base
from sqlalchemy.orm import Relationship
from datetime import datetime

class Audio(Base):
    __tablename__ = "audio"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transcript = Column(JSON)
    date_created = Column(DateTime, default=datetime.utcnow())
    data = Column(LargeBinary)
    summaries = Relationship("Summary", cascade="all, delete-orphan")
    histories = Relationship("History", cascade="all, delete-orphan")


class Summary(Base):
    __tablename__ = "summary"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Audio_id = Column(Integer, ForeignKey("audio.id"))
    title = Column(Text)
    summary = Column(Text)

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Audio_id = Column(Integer, ForeignKey("audio.id"))
    chat_response = Column(JSON)


from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Summary(BaseModel):
    id: Optional[int] 
    title: Optional[str]
    summary: Optional[str]

class History(BaseModel):
    id: Optional[int]
    chat_response: dict

class Audio(BaseModel):
    id: Optional[int] 
    transcript: Optional[str]
    date_created: Optional[datetime]
    data: bytes
    summaries: List[Summary] = []
    histories: List[History] = []
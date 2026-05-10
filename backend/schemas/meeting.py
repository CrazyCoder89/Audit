from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MeetingCreate(BaseModel):
    title: str

class MeetingResponse(BaseModel):
    id: int
    title: str
    room_code: str
    created_by: int
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class MinutesResponse(BaseModel):
    meeting_id: int
    title: str
    transcript: Optional[str]
    minutes: Optional[str]
    minutes_pdf_path: Optional[str]



    
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    room_code = Column(String, unique=True, nullable=False)  # unique 8-char code
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="waiting")  # waiting, active, ended
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    transcript = Column(Text, nullable=True)       # full whisper transcript
    minutes = Column(Text, nullable=True)           # AI generated minutes
    minutes_pdf_path = Column(String, nullable=True)  # path to saved PDF
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", foreign_keys=[created_by])


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)

    meeting = relationship("Meeting", backref="participants")
    user = relationship("User", backref="meeting_participations")
    
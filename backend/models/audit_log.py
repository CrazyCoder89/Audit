# Records every important action in the system.
# This is the compliance backbone — regulators can ask "who accessed what and when"
# We log: user, action type, resource, timestamp, and extra details.

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for system actions
    action = Column(String, nullable=False)        # e.g. "document.upload", "document.ask"
    resource_type = Column(String, nullable=True)  # e.g. "document", "user"
    resource_id = Column(Integer, nullable=True)   # ID of the affected resource
    details = Column(Text, nullable=True)          # Extra info stored as JSON string
    ip_address = Column(String, nullable=True)     # IP address of the request
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="audit_logs")
# Defines the Document table in PostgreSQL
# Stores metadata about uploaded files — not the file itself
# The actual file is saved to a local folder (uploads/)

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class DocumentCategory(str, enum.Enum):
    financial = "financial"
    legal = "legal"
    compliance = "compliance"
    hr = "hr"
    unknown = "unknown"

class DocumentStatus(str, enum.Enum):
    pending = "pending"       # Uploaded but not processed
    processed = "processed"   # Text extracted, ready for RAG
    failed = "failed"         # Processing failed

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)               # Original file name
    stored_filename = Column(String, nullable=False)        # UUID filename on disk
    file_path = Column(String, nullable=False)              # Full path to file
    file_size = Column(Integer)                             # Size in bytes
    category = Column(Enum(DocumentCategory), default=DocumentCategory.unknown)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.pending)
    uploaded_by = Column(Integer, ForeignKey("users.id"))   # Who uploaded it
    is_active = Column(Boolean, default=True)               # Soft delete
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship — lets us do document.uploader to get the User object
    uploader = relationship("User", backref="documents")

    
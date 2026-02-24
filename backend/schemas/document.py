# Schemas for document upload requests and responses
from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime

class DocumentCategory(str, Enum):
    financial = "financial"
    legal = "legal"
    compliance = "compliance"
    hr = "hr"
    unknown = "unknown"

class DocumentStatus(str, Enum):
    pending = "pending"
    processed = "processed"
    failed = "failed"

# Returned after upload or when listing documents
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    category: DocumentCategory
    status: DocumentStatus
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.document import Document, DocumentCategory, DocumentStatus
from schemas.document import DocumentResponse
from auth.dependencies import get_current_user, require_admin
from services.classifier import classify_document
from services.rag_services import process_document, ask_document
from services.audit_services import log_action
from pydantic import BaseModel
from fastapi.responses import FileResponse
router = APIRouter(prefix="/documents", tags=["Documents"])

def user_has_document_access(doc, current_user, db):
    from models.task import Task
    if current_user.role in ["admin", "auditor"]:
        return True
    if doc.uploaded_by == current_user.id:
        return True
    task = db.query(Task).filter(
        Task.document_id == doc.id,
        Task.assigned_to == current_user.id
    ).first()
    return task is not None


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QuestionRequest(BaseModel):
    question: str

def process_in_background(file_path: str, document_id: int, db: Session):
    result = process_document(file_path, document_id)
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        if result["status"] == "success":
            doc.status = DocumentStatus.processed
        else:
            doc.status = DocumentStatus.failed
        db.commit()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    file_size = len(content)

    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 10MB")

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    category = classify_document(file.filename)

    new_doc = Document(
        filename=file.filename,
        stored_filename=unique_filename,
        file_path=file_path,
        file_size=file_size,
        category=DocumentCategory(category),
        status=DocumentStatus.pending,
        uploaded_by=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Log the upload
    log_action(
        db=db,
        action="document.upload",
        user_id=current_user.id,
        resource_type="document",
        resource_id=new_doc.id,
        details={"filename": file.filename, "size": file_size, "category": category},
        ip_address=request.client.host
    )

    background_tasks.add_task(process_in_background, file_path, new_doc.id, db)
    return new_doc

@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log_action(
        db=db,
        action="document.list",
        user_id=current_user.id,
        resource_type="document",
        details={"role": current_user.role},
        ip_address=request.client.host
    )

    if current_user.role in ["admin", "auditor"]:
        return db.query(Document).filter(Document.is_active == True).all()

    # Viewers see own docs + docs linked to their assigned tasks
    from models.task import Task
    from sqlalchemy import or_
    assigned_doc_ids = db.query(Task.document_id).filter(
        Task.assigned_to == current_user.id,
        Task.document_id != None
    ).all()
    assigned_doc_ids = [d[0] for d in assigned_doc_ids]

    return db.query(Document).filter(
        Document.is_active == True,
        or_(
            Document.uploaded_by == current_user.id,
            Document.id.in_(assigned_doc_ids)
        )
    ).all()

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.is_active == True
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not user_has_document_access(doc, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Log the view
    log_action(
        db=db,
        action="document.view",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document_id,
        ip_address=request.client.host
    )

    return doc

@router.post("/{document_id}/ask")
def ask_about_document(
    document_id: int,
    request: Request,
    body: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.is_active == True
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not user_has_document_access(doc, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")

    if doc.status == DocumentStatus.pending:
        raise HTTPException(status_code=400, detail="Document is still being processed")

    if doc.status == DocumentStatus.failed:
        raise HTTPException(status_code=400, detail="Document processing failed, please re-upload")

    # Log the question
    log_action(
        db=db,
        action="document.ask",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document_id,
        details={"question": body.question, "filename": doc.filename},
        ip_address=request.client.host
    )

    result = ask_document(document_id, body.question)
    return result

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_active = False
    db.commit()

    # Log the deletion
    log_action(
        db=db,
        action="document.delete",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document_id,
        details={"filename": doc.filename},
        ip_address=request.client.host
    )

    return {"message": f"Document {document_id} deleted successfully"}

@router.get("/search/query", response_model=list[DocumentResponse])
def search_documents(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full-text search across document filenames and categories."""
    from sqlalchemy import or_
    query = db.query(Document).filter(Document.is_active == True)

    if current_user.role == "viewer":
        from models.task import Task
        from sqlalchemy import or_
        assigned_doc_ids = db.query(Task.document_id).filter(
            Task.assigned_to == current_user.id,
            Task.document_id != None
        ).all()
        assigned_doc_ids = [d[0] for d in assigned_doc_ids]
        query = query.filter(
            or_(
                Document.uploaded_by == current_user.id,
                Document.id.in_(assigned_doc_ids)
            )
        )

    results = query.filter(
        or_(
            Document.filename.ilike(f"%{q}%"),
            Document.category.ilike(f"%{q}%"),
            Document.status.ilike(f"%{q}%")
        )
    ).all()
    return results

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.is_active == True
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not user_has_document_access(doc, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    log_action(
        db=db,
        action="document.download",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document_id,
        details={"filename": doc.filename},
        ip_address=request.client.host
    )

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type="application/pdf"
    )


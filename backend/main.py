import os

from fastapi import FastAPI
from database import engine, Base
from routes.auth_routes import router as auth_router
from routes.document_routes import router as document_router
from routes.audit_routes import router as audit_router
from routes.task_routes import router as task_router
from routes.comment_routes import router as comment_router
from tasks.weekly_report import start_scheduler
from routes.report_routes import router as report_router
from routes.analytics_routes import router as analytics_router
from routes.meeting_routes import router as meeting_router
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import text
from database import get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Audit System", version="1.0.0")

from fastapi.middleware.cors import CORSMiddleware
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8501","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://auditsys-frontend.vercel.app",
        "https://auditsys-meeting.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(audit_router)
app.include_router(task_router)
app.include_router(comment_router)
app.include_router(report_router)
app.include_router(analytics_router)
app.include_router(meeting_router)

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    import os
    from database import SessionLocal
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("vector_indexes", exist_ok=True)
    os.makedirs("meeting_minutes", exist_ok=True)
    db = SessionLocal()
    try:
        from models.document import Document
        processed_docs = db.query(Document).filter(
            Document.status == "processed",
            Document.is_active == True
        ).all()
        reset_count = 0
        for doc in processed_docs:
            index_path = os.path.join("vector_indexes", str(doc.id), "faiss.index")
            if not os.path.exists(index_path):
                doc.status = "pending"
                reset_count += 1
        if reset_count > 0:
            db.commit()
            print(f"[STARTUP] Reset {reset_count} docs to pending — indexes lost on redeploy")
    except Exception as e:
        print(f"[STARTUP] Error: {e}")
    finally:
        db.close()

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "DB OK"}
    except Exception as e:
        return {"status": "DB FAIL", "error": str(e)}
    
@app.get("/")
def root():
    return {"message": "AuditSys API is running", "status": "ok", "version": "1.0.0"}

print(f"[STARTUP] uploads/ exists: {os.path.exists('uploads')}")
print(f"[STARTUP] vector_indexes/ exists: {os.path.exists('vector_indexes')}")



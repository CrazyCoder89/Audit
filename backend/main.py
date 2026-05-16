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


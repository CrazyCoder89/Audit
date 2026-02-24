from fastapi import FastAPI
from database import engine, Base
from routes.auth_routes import router as auth_router
from routes.document_routes import router as document_router
from routes.audit_routes import router as audit_router
from routes.task_routes import router as task_router

# Creates all tables including the new documents table
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Audit System", version="1.0.0")

app.include_router(auth_router)
app.include_router(document_router)
app.include_router(audit_router)
app.include_router(task_router)

@app.get("/")
def root():
    return {"message": "AI Audit System is running"}


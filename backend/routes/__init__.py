# Makes routes a proper Python package

from .auth_routes import router as auth_router
from .document_routes import router as document_router
from .audit_routes import router as audit_router
from .task_routes import router as task_router
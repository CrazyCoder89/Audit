# ⚡ AuditSys — AI-Powered Compliance & Audit Management System

> Enterprise-grade compliance intelligence platform with RAG-powered document Q&A, audit trail logging, and task management.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## ✨ Features

- 🔐 **Authentication** — JWT-based login, role-based access (Admin/Auditor/Viewer/Guest)
- 📄 **Document Management** — Upload PDFs, auto-classify, version tracking
- 🤖 **AI Document Q&A** — Ask questions about any document using RAG (FAISS + Mistral)
- 📋 **Task Management** — Create, assign, and track audit tasks with deadlines
- 🔍 **Audit Trail** — Every action logged with timestamp, user, and IP address
- 📊 **Analytics Dashboard** — Compliance score, charts, activity feed, deadline calendar
- 📤 **CSV Export** — Export full audit logs for regulatory reporting
- 🔒 **100% Local & Private** — No data leaves your machine

---

## 🏗️ Architecture
```
User → Streamlit Frontend (port 8501)
            ↓
      FastAPI Backend (port 8000)
            ↓
    ┌───────────────────┐
    │   PostgreSQL DB   │  ← Users, Documents, Tasks, Audit Logs
    └───────────────────┘
            ↓
    ┌───────────────────┐
    │   RAG Engine      │  ← PyMuPDF + FAISS + Mistral (Ollama)
    └───────────────────┘
```

---

## 📁 Project Structure
```
audit_system/
├── backend/                  # FastAPI backend
│   ├── main.py               # App entry point
│   ├── database.py           # PostgreSQL connection
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── task.py
│   │   └── audit_log.py
│   ├── schemas/              # Pydantic schemas
│   ├── routes/               # API endpoints
│   │   ├── auth_routes.py
│   │   ├── document_routes.py
│   │   ├── task_routes.py
│   │   └── audit_routes.py
│   ├── services/             # Business logic
│   │   ├── classifier.py     # Auto document classification
│   │   ├── rag_services.py   # RAG integration
│   │   └── audit_service.py  # Audit logging
│   └── auth/                 # JWT auth handlers
│
├── ai_engine/                # RAG system
│   ├── config.py
│   ├── ingestion/            # PDF processing
│   ├── embeddings/           # sentence-transformers
│   ├── retrieval/            # FAISS vector store
│   └── rag/                  # Pipeline + Ollama
│
└── frontend/                 # Streamlit UI
    ├── app.py                # Entry point
    ├── utils.py              # Shared utilities
    └── pages/
        ├── 0_login.py        # Authentication
        ├── 1_dashboard.py    # Analytics dashboard
        ├── 2_documents.py    # Document management
        ├── 3_ask_ai.py       # AI Q&A interface
        ├── 4_tasks.py        # Task management
        ├── 5_audit_logs.py   # Compliance logs
        └── 6_admin.py        # Admin panel
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL
- [Ollama](https://ollama.com/download) with Mistral model

### 1. Clone the repository
```bash
git clone https://github.com/CrazyCoder89/Audit.git
cd Audit
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/audit_db
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
```bash
uvicorn main:app --reload
```

### 3. AI Engine Setup
```bash
ollama pull mistral
ollama serve
```

### 4. Frontend Setup
```bash
cd frontend
pip install streamlit requests plotly
streamlit run app.py
```

### 5. Open your browser

- Frontend: `http://localhost:8501`
- API Docs: `http://localhost:8000/docs`

---

## 👥 Default Roles

| Role | Permissions |
|------|------------|
| Admin | Full access — manage users, view all logs, export CSV |
| Auditor | Create tasks, view all documents and logs |
| Viewer | View own documents, update assigned task status |
| Guest | Limited read-only access |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| Auth | JWT, bcrypt, passlib |
| AI/RAG | PyMuPDF, sentence-transformers, FAISS, Mistral (Ollama) |
| Frontend | Streamlit, Plotly |
| Task Queue | Background tasks (FastAPI) |

---

## 📧 Contact

**Developer:** CrazyCoder89  
**GitHub:** [@CrazyCoder89](https://github.com/CrazyCoder89)

---

## 🌟 Star this repo if you find it useful!

Made with ❤️ using Python, FastAPI, and open-source AI tools
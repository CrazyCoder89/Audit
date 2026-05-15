from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # 👈 checks dead connections
    pool_recycle=300,        # 👈 refresh connection every 5 min
    pool_size=5,
    max_overflow=10,
    connect_args={
        "sslmode": "require"  # 👈 VERY IMPORTANT for Neon
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
print("DATABASE_URL =", DATABASE_URL)
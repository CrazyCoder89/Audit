#sets up the database connection and session management using SQLAlchemy. 
#creates engine and session factory
#Every route that needs DB access will use get_db() to get a session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
#engine connection
engine = create_engine(DATABASE_URL)
#creates factory that created new db sessions for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#prent class for all models to inherit from
Base = declarative_base()
#fastapi routes call this to get a db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/database")
# For now, use SQLite for simplicity during initial development
DATABASE_URL = "sqlite:///./program_pal.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# REMOVED User model definition from here - it belongs in models.py

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables if using SQLite (Alembic is better for production/Postgres)
# This needs to happen *after* models are defined and imported.
# We will call this from main.py or use Alembic later.
# if "sqlite" in DATABASE_URL:
#     # Import models here before creating tables
#     from . import models # Assuming models.py is in the same directory
#     Base.metadata.create_all(bind=engine)


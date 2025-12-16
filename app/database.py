from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/bolt")

# Create SQLAlchemy engine to talk to database
engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# URL mapping table
class URLMapping(Base):
    __tablename__ = "url_mappings"
    
    short_code = Column(String, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
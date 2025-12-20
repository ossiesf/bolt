from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
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

# Table for metrics and traffic tracking
# Use the shortener to link things on resume such as github and collect analytics
# Example link: bolt-testing.dev/short_code?resume=v2&job_url=https://greenhouse.io
class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, ForeignKey("url_mappings.short_code"))
    clicked_at = Column(DateTime, default=datetime.utcnow)

    # Essential metrics to track to see who clicked, which job posting, and referrer
    job_posting_url = Column(String, nullable=True)
    resume_version = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
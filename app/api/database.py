from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/shopflow_db")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models
Base = declarative_base()

# Dependency to get the database session in our routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

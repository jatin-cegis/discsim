import time
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/discsim")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    content = Column(LargeBinary)

Base.metadata.create_all(bind=engine)

def get_engine(retries=5, delay=2):
    for attempt in range(retries):
        try:
            engine = create_engine(DATABASE_URL)
            engine.connect()
            return engine
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
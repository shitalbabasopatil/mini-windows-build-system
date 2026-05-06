# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = "sqlite:///./database/builds.db"

Base = declarative_base()

class BuildRecord(Base):
    __tablename__ = "builds"

    build_id = Column(String, primary_key=True, index=True)
    repo_url = Column(String)
    branch = Column(String)
    project_path = Column(String)
    build_command = Column(String)
    status = Column(String)  # QUEUED, CLONING, RUNNING, SUCCESS, FAILED, CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    artifact_path = Column(String, nullable=True)

class LogRecord(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    build_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    log_line = Column(Text)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

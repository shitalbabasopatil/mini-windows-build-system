# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
import datetime
import os

from database.models import init_db, get_db, BuildRecord, LogRecord
from pydantic import BaseModel
from worker.lifecycle.manager import WorkerManager, BuildQueue

# Models
class BuildRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    project_path: str = "./"
    build_command: str = "dotnet build"

class BuildStatus(BaseModel):
    build_id: str
    status: str
    created_at: datetime.datetime
    completed_at: datetime.datetime = None

# Initialize App
app = FastAPI(title="WinBuild Cloud API", description="Local Windows Container Build System")

# Initialize Queue and Worker
build_queue = BuildQueue()
worker_manager = WorkerManager(build_queue)

@app.on_event("startup")
def startup_event():
    init_db()
    worker_manager.start()

@app.get("/health")
def health_check():
    return {"status": "healthy", "worker_running": worker_manager.running}

@app.post("/build", response_model=BuildStatus)
def create_build(request: BuildRequest, db: Session = Depends(get_db)):
    build_id = str(uuid.uuid4())
    
    new_build = BuildRecord(
        build_id=build_id,
        repo_url=request.repo_url,
        branch=request.branch,
        project_path=request.project_path,
        build_command=request.build_command,
        status="QUEUED"
    )
    
    db.add(new_build)
    db.commit()
    db.refresh(new_build)
    
    # Add to in-memory queue
    build_queue.push(build_id)
    
    return new_build

@app.get("/build/{build_id}", response_model=BuildStatus)
def get_build_status(build_id: str, db: Session = Depends(get_db)):
    build = db.query(BuildRecord).filter(BuildRecord.build_id == build_id).first()
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return build

@app.get("/build/{build_id}/logs")
def get_build_logs(build_id: str, db: Session = Depends(get_db)):
    logs = db.query(LogRecord).filter(LogRecord.build_id == build_id).order_by(LogRecord.timestamp.asc()).all()
    return [{"timestamp": l.timestamp, "message": l.log_line} for l in logs]

@app.get("/builds", response_model=List[BuildStatus])
def list_builds(db: Session = Depends(get_db)):
    return db.query(BuildRecord).order_by(BuildRecord.created_at.desc()).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

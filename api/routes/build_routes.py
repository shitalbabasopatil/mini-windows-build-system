# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Author: Shital Babaso Patil
# Email: shitalbabasopatil@gmail.com

import os
import uuid
from flask import send_file
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.orm import Session

from database.models import SessionLocal, BuildRecord, LogRecord
from api.schemas import BuildRequestSchema, BuildStatusSchema, LogSchema

blp = Blueprint("builds", "builds", url_prefix="/", description="Operations on builds")

# We use global references that will be initialized in main.py
build_queue = None
worker_manager = None

def init_api(q, wm):
    global build_queue, worker_manager
    build_queue = q
    worker_manager = wm

@blp.route("/health")
class Health(MethodView):
    @blp.response(200, description="Health check")
    def get(self):
        """Check if API and Workers are running"""
        return {"status": "healthy", "worker_running": worker_manager.running if worker_manager else False}

@blp.route("/build")
class BuildList(MethodView):
    @blp.arguments(BuildRequestSchema)
    @blp.response(201, BuildStatusSchema)
    def post(self, new_data):
        """Submit a new build job"""
        db: Session = SessionLocal()
        try:
            build_id = str(uuid.uuid4())
            new_build = BuildRecord(
                build_id=build_id,
                repo_url=new_data["repo_url"],
                branch=new_data["branch"],
                project_path=new_data["project_path"],
                build_command=new_data["build_command"],
                status="QUEUED"
            )
            db.add(new_build)
            db.commit()
            db.refresh(new_build)
            
            if build_queue:
                build_queue.push(build_id)
            return new_build
        finally:
            db.close()

    @blp.response(200, BuildStatusSchema(many=True))
    def get(self):
        """List all builds"""
        db: Session = SessionLocal()
        try:
            return db.query(BuildRecord).order_by(BuildRecord.created_at.desc()).all()
        finally:
            db.close()

@blp.route("/build/<string:build_id>")
class BuildDetail(MethodView):
    @blp.response(200, BuildStatusSchema)
    def get(self, build_id):
        """Get build status and metadata"""
        db: Session = SessionLocal()
        try:
            build = db.query(BuildRecord).filter(BuildRecord.build_id == build_id).first()
            if not build:
                abort(404, message="Build not found")
            return build
        finally:
            db.close()

@blp.route("/build/<string:build_id>/logs")
class BuildLogs(MethodView):
    @blp.response(200, LogSchema(many=True))
    def get(self, build_id):
        """Get real-time build logs"""
        db: Session = SessionLocal()
        try:
            logs = db.query(LogRecord).filter(LogRecord.build_id == build_id).order_by(LogRecord.timestamp.asc()).all()
            return logs
        finally:
            db.close()

@blp.route("/build/<string:build_id>/artifact")
class BuildArtifact(MethodView):
    def get(self, build_id):
        """Download build artifacts (ZIP)"""
        db: Session = SessionLocal()
        try:
            build = db.query(BuildRecord).filter(BuildRecord.build_id == build_id).first()
            if not build or not build.artifact_path:
                abort(404, message="Artifact not found or build failed")
            
            if not os.path.exists(build.artifact_path):
                abort(404, message="Artifact file missing on server")
            
            return send_file(build.artifact_path, as_attachment=True, download_name=f"artifact_{build_id}.zip")
        finally:
            db.close()

# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

import asyncio
import threading
import queue
import logging
import datetime
from sqlalchemy.orm import Session
from database.models import SessionLocal, BuildRecord, LogRecord
from worker.executor.windows_executor import WindowsExecutor

class BuildQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def push(self, build_id: str):
        self._queue.put(build_id)

    def pop(self):
        try:
            return self._queue.get(block=True, timeout=1)
        except queue.Empty:
            return None

    def task_done(self):
        self._queue.task_done()

class WorkerManager:
    def __init__(self, build_queue: BuildQueue):
        self.queue = build_queue
        self.executor = WindowsExecutor(storage_root="./storage/builds")
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        logging.info("Worker thread started.")

    def _worker_loop(self):
        while self.running:
            build_id = self.queue.pop()
            if build_id:
                try:
                    self._process_build(build_id)
                except Exception as e:
                    logging.error(f"Error processing build {build_id}: {e}")
                finally:
                    self.queue.task_done()

    def _process_build(self, build_id: str):
        db: Session = SessionLocal()
        build = db.query(BuildRecord).filter(BuildRecord.build_id == build_id).first()
        
        if not build:
            db.close()
            return

        def log_to_db(line: str):
            # Print to console for real-time visibility in docker-compose logs
            print(f"[{build_id}] {line}")
            
            # Persist to database
            new_log = LogRecord(build_id=build_id, log_line=line)
            db.add(new_log)
            db.commit()

        try:
            build.status = "RUNNING"
            db.commit()

            success = self.executor.run_build(
                build_id=build.build_id,
                repo_url=build.repo_url,
                branch=build.branch,
                project_path=build.project_path,
                build_command=build.build_command,
                log_callback=log_to_db
            )

            build.status = "SUCCESS" if success else "FAILED"
            build.completed_at = datetime.datetime.utcnow()
            db.commit()

        except Exception as e:
            log_to_db(f"CRITICAL WORKER ERROR: {str(e)}")
            build.status = "FAILED"
            db.commit()
        finally:
            db.close()

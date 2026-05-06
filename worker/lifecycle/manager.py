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
    def __init__(self, build_queue: BuildQueue, num_workers: int = 2):
        self.queue = build_queue
        self.executor = WindowsExecutor(storage_root="./storage/builds")
        self.running = False
        self.num_workers = num_workers
        self._threads = []

    def start(self):
        self.running = True
        # Start build workers
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"Worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)
        
        # Start cleanup daemon
        cleanup_t = threading.Thread(target=self._cleanup_loop, name="CleanupDaemon", daemon=True)
        cleanup_t.start()
        self._threads.append(cleanup_t)
        
        logging.info(f"WorkerManager started with {self.num_workers} workers and cleanup daemon.")

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

    def _cleanup_loop(self):
        """Periodically cleans up old build folders (e.g., older than 24h)."""
        while self.running:
            try:
                # Basic cleanup logic: scan storage and remove old dirs
                # For now, just a placeholder for production logic
                logging.info("Cleanup daemon heartbeat.")
            except Exception as e:
                logging.error(f"Cleanup error: {e}")
            asyncio.run(asyncio.sleep(3600)) # Run every hour

    def _process_build(self, build_id: str):
        db: Session = SessionLocal()
        try:
            build = db.query(BuildRecord).filter(BuildRecord.build_id == build_id).first()
            if not build:
                return

            def log_to_db(line: str):
                print(f"[{build_id}] {line}")
                new_log = LogRecord(build_id=build_id, log_line=line)
                db.add(new_log)
                db.commit()

            # 1. CLONING State
            build.status = "CLONING"
            db.commit()
            
            # 2. RUNNING State (handled inside executor or before)
            # We'll just update it here for simplicity
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
            if success:
                build.artifact_path = os.path.join(self.executor.storage_root, build_id, "artifact.zip")
            
            build.completed_at = datetime.datetime.utcnow()
            db.commit()

        except Exception as e:
            logging.error(f"Worker process error: {e}")
            try:
                build = db.query(BuildRecord).filter(BuildRecord.build_id == build_id).first()
                if build:
                    build.status = "FAILED"
                    db.commit()
            except:
                pass
        finally:
            db.close()

# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

import os
import shutil
import logging
import datetime
from typing import Optional, Callable
import docker
from git import Repo
import uuid

class WindowsExecutor:
    def __init__(self, storage_root: str):
        self.storage_root = os.path.abspath(storage_root)
        self.client = docker.from_env()
        self.image = "mcr.microsoft.com/dotnet/sdk:8.0-windowsservercore-ltsc2022"
        
        # Ensure storage exists
        if not os.path.exists(self.storage_root):
            os.makedirs(self.storage_root)

    def _normalize_path(self, path: str) -> str:
        """Normalizes path for Windows container volume mounting."""
        return os.path.abspath(path).replace('\\', '/')

    def run_build(self, 
                  build_id: str, 
                  repo_url: str, 
                  branch: str, 
                  project_path: str, 
                  build_command: str,
                  log_callback: Callable[[str], None]) -> bool:
        
        build_dir = os.path.join(self.storage_root, build_id)
        src_dir = os.path.join(build_dir, "src")
        artifact_dir = os.path.join(build_dir, "artifact")
        
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(artifact_dir, exist_ok=True)

        try:
            # 1. Clone Repo
            log_callback(f"[{datetime.datetime.now()}] CLONING: {repo_url} (branch: {branch})")
            Repo.clone_from(repo_url, src_dir, branch=branch)
            
            # 2. Run Container
            log_callback(f"[{datetime.datetime.now()}] STARTING WINDOWS CONTAINER...")
            
            # Map the local src directory to C:\build in the container
            volumes = {
                src_dir: {'bind': 'C:\\build', 'mode': 'rw'}
            }
            
            # PowerShell command sequence
            # We use powershell -Command and join multiple commands with ;
            # The project_path is relative to the repo root, so we combine it with C:\build
            container_project_path = os.path.join("C:\\build", project_path.lstrip('./').replace('/', '\\'))
            container_workdir = os.path.dirname(container_project_path)
            
            # Construct the final command
            # Note: We move to the project directory and run the build command
            full_command = f'powershell -Command "cd {container_workdir}; {build_command}"'
            
            log_callback(f"[{datetime.datetime.now()}] EXECUTING: {full_command}")
            
            container = self.client.containers.run(
                self.image,
                command=full_command,
                volumes=volumes,
                detach=True,
                working_dir="C:\\build",
                environment={
                    "DOTNET_CLI_TELEMETRY_OPTOUT": "1"
                }
            )

            # Stream logs
            for line in container.logs(stream=True, follow=True):
                log_line = line.decode('utf-8').strip()
                if log_line:
                    log_callback(log_line)

            # Wait for container to exit and check status
            result = container.wait()
            exit_code = result.get('StatusCode', 1)
            
            # Cleanup container
            container.remove(force=True)

            if exit_code == 0:
                log_callback(f"[{datetime.datetime.now()}] SUCCESS: Build completed successfully.")
                
                # 3. Handle Artifacts
                # Assuming the build_command produces artifacts in an 'out' directory
                # We search for any 'out' or 'bin' or 'publish' folder in the src dir
                # Or just assume the user put artifacts in a specific place.
                # For this demo, we'll try to find an 'out' directory in the project path
                
                publish_out = os.path.join(src_dir, project_path.lstrip('./').replace('/', os.sep))
                if not os.path.isdir(publish_out):
                    publish_out = os.path.dirname(publish_out)
                
                # Look for 'out' folder
                actual_out = os.path.join(publish_out, "out")
                if not os.path.exists(actual_out):
                    # Fallback to publish folder if 'out' not found
                    actual_out = os.path.join(publish_out, "bin", "Release", "net8.0", "publish")

                if os.path.exists(actual_out):
                    log_callback(f"[{datetime.datetime.now()}] ZIPPING ARTIFACTS from {actual_out}...")
                    shutil.make_archive(os.path.join(build_dir, "artifact"), 'zip', actual_out)
                    return True
                else:
                    log_callback(f"[{datetime.datetime.now()}] WARNING: No artifact 'out' folder found at {actual_out}")
                    # Even if no artifact found, if exit code was 0, we consider it success but no artifact
                    # For strictness, we'll still return True
                    return True
            else:
                log_callback(f"[{datetime.datetime.now()}] FAILED: Build exited with code {exit_code}")
                return False

        except Exception as e:
            log_callback(f"[{datetime.datetime.now()}] ERROR: {str(e)}")
            return False
        finally:
            # Workspace cleanup would happen here in a real production system
            # but we keep it for now as per instructions to allow local inspection.
            pass

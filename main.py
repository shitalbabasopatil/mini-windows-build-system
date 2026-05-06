# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

from flask import Flask
from flask_smorest import Api
from database.models import init_db
from worker.lifecycle.manager import WorkerManager, BuildQueue
from api.routes.build_routes import blp as build_blp, init_api

# 1. Configuration
class Config:
    API_TITLE = "WinBuild Cloud API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize components
    init_db()
    build_queue = BuildQueue()
    worker_manager = WorkerManager(build_queue)
    worker_manager.start()

    # Initialize API
    api = Api(app)
    init_api(build_queue, worker_manager)
    api.register_blueprint(build_blp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

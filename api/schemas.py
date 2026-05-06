# Copyright 2026 Shital Babaso Patil <shitalbabasopatil@gmail.com>
# Author: Shital Babaso Patil
# Email: shitalbabasopatil@gmail.com

from marshmallow import Schema, fields

class BuildRequestSchema(Schema):
    repo_url = fields.Str(required=True, metadata={"example": "https://github.com/dotnet/dotnet-docker"})
    branch = fields.Str(load_default="main")
    project_path = fields.Str(load_default="./")
    build_command = fields.Str(load_default="dotnet build")

class BuildStatusSchema(Schema):
    build_id = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    repo_url = fields.Str(dump_only=True)
    branch = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(dump_only=True)
    artifact_path = fields.Str(dump_only=True)

class LogSchema(Schema):
    timestamp = fields.DateTime(dump_only=True)
    message = fields.Str(attribute="log_line", dump_only=True)

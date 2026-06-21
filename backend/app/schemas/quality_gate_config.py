from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QualityGateConfigUpdate(BaseModel):
    min_total_coverage: float | None = Field(default=None, ge=0, le=100)
    max_coverage_drop: float | None = Field(default=None, ge=0, le=100)
    min_changed_files_coverage: float | None = Field(default=None, ge=0, le=100)
    security_fail_on: list[str] | dict | None = None
    max_function_lines: int | None = Field(default=None, ge=1)
    max_complexity: int | None = Field(default=None, ge=1)
    fail_on_new_todo: bool | None = None
    comment_on_github: bool | None = None
    publish_github_status: bool | None = None


class QualityGateConfigRead(BaseModel):
    id: UUID
    repository_id: UUID
    min_total_coverage: float
    max_coverage_drop: float
    min_changed_files_coverage: float
    security_fail_on: list[str] | dict
    max_function_lines: int
    max_complexity: int
    fail_on_new_todo: bool
    comment_on_github: bool
    publish_github_status: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

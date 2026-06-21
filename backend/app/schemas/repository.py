from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RepositoryCreate(BaseModel):
    owner: str = Field(min_length=1)
    name: str = Field(min_length=1)
    full_name: str | None = None
    default_branch: str = "main"
    github_repo_id: int | None = None

    @model_validator(mode="after")
    def default_full_name(self) -> "RepositoryCreate":
        if self.full_name is None:
            self.full_name = f"{self.owner}/{self.name}"
        return self


class RepositoryRead(BaseModel):
    id: UUID
    github_repo_id: int | None
    owner: str
    name: str
    full_name: str
    default_branch: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

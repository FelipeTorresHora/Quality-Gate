from uuid import UUID

from pydantic import BaseModel


class CurrentUserRead(BaseModel):
    id: UUID
    github_user_id: int
    github_login: str
    name: str | None = None
    avatar_url: str | None = None
    has_github_connection: bool

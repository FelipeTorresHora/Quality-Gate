from pydantic import BaseModel


class GitHubInstallationRead(BaseModel):
    installation_id: int
    account_login: str
    account_type: str
    active: bool


class GitHubInstallUrlRead(BaseModel):
    url: str

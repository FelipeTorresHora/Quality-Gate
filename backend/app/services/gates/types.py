from dataclasses import dataclass, field

from app.models.enums import FindingCategory, FindingSeverity


@dataclass
class GateFinding:
    category: FindingCategory
    severity: FindingSeverity
    file_path: str | None
    line_number: int | None
    title: str
    description: str
    blocking: bool


@dataclass
class GateResult:
    snapshot: dict
    findings: list[GateFinding] = field(default_factory=list)
    error_message: str | None = None

    @property
    def status(self) -> str:
        return str(self.snapshot.get("status", "error"))

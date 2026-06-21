from enum import Enum


class AnalysisRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class GateDecision(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class AnalysisTriggerSource(str, Enum):
    MOCK = "mock"
    MANUAL = "manual"
    GITHUB_WEBHOOK = "github_webhook"


class FindingCategory(str, Enum):
    COVERAGE = "coverage"
    SECURITY = "security"
    TECHNICAL_DEBT = "technical_debt"


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

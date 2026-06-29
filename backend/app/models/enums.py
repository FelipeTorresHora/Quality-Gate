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


class CoverageLanguage(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"


class CoverageReportFormat(str, Enum):
    COBERTURA_XML = "cobertura_xml"
    LCOV = "lcov"
    GO_COVERPROFILE = "go_coverprofile"

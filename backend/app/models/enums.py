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
    CODE_REVIEW = "code_review"


class FindingSource(str, Enum):
    """Origin of an Analysis Finding.

    Deterministic gates own Gate Decision. Findings with source ``ai`` are
    explanatory and are stored with blocking false (ADR 0032).
    """

    DETERMINISTIC = "deterministic"
    AI = "ai"


class GateEvaluationMode(str, Enum):
    """How a pillar may attach AI evidence.

    ``hybrid`` is the default: the deterministic gate still owns Gate Decision
    and AI may add non-blocking Analysis Findings. ``deterministic`` records
    scanner evidence only. ``ai_only`` still does not let the model set Gate
    Decision or blocking; publication stays a separate action (ADR 0032, ADR 0034).
    """

    HYBRID = "hybrid"
    DETERMINISTIC = "deterministic"
    AI_ONLY = "ai_only"


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

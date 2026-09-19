from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.coverage_execution_config import CoverageExecutionConfig
from app.models.enums import CoverageLanguage, CoverageReportFormat
from app.schemas.coverage_execution_config import CoverageExecutionConfigUpdate
from app.services.repository_service import get_repository


DEFAULTS_BY_LANGUAGE = {
    CoverageLanguage.PYTHON: {
        "install_command": "pip install -r requirements.txt",
        "test_command": "pytest --cov=. --cov-report=xml:coverage.xml",
        "report_path": "coverage.xml",
        "report_format": CoverageReportFormat.COBERTURA_XML,
    },
    CoverageLanguage.TYPESCRIPT: {
        "install_command": "npm ci",
        "test_command": "npm test -- --coverage",
        "report_path": "coverage/lcov.info",
        "report_format": CoverageReportFormat.LCOV,
    },
    CoverageLanguage.JAVASCRIPT: {
        "install_command": "npm ci",
        "test_command": "npm test -- --coverage",
        "report_path": "coverage/lcov.info",
        "report_format": CoverageReportFormat.LCOV,
    },
    CoverageLanguage.GO: {
        "install_command": "go mod download",
        "test_command": "go test ./... -coverprofile=coverage.out",
        "report_path": "coverage.out",
        "report_format": CoverageReportFormat.GO_COVERPROFILE,
    },
}

_GITHUB_LANGUAGE_ALIASES = {
    "python": CoverageLanguage.PYTHON,
    "javascript": CoverageLanguage.JAVASCRIPT,
    "js": CoverageLanguage.JAVASCRIPT,
    "node": CoverageLanguage.JAVASCRIPT,
    "nodejs": CoverageLanguage.JAVASCRIPT,
    "typescript": CoverageLanguage.TYPESCRIPT,
    "ts": CoverageLanguage.TYPESCRIPT,
    "go": CoverageLanguage.GO,
    "golang": CoverageLanguage.GO,
}


def map_github_language(
    github_language: str | None,
) -> tuple[CoverageLanguage, bool]:
    if not github_language or not str(github_language).strip():
        return CoverageLanguage.PYTHON, False
    key = str(github_language).strip().lower()
    language = _GITHUB_LANGUAGE_ALIASES.get(key)
    if language is None:
        return CoverageLanguage.PYTHON, False
    return language, True


def build_coverage_execution_config(
    *,
    github_language: str | None = None,
) -> CoverageExecutionConfig:
    language, matched = map_github_language(github_language)
    defaults = DEFAULTS_BY_LANGUAGE[language]
    return CoverageExecutionConfig(
        language=language,
        language_preset_confirmed=matched,
        install_command=defaults["install_command"],
        test_command=defaults["test_command"],
        report_path=defaults["report_path"],
        report_format=defaults["report_format"],
    )


def get_coverage_execution_config(
    db: Session, repository_id: UUID
) -> CoverageExecutionConfig:
    repository = get_repository(db, repository_id)
    if repository.coverage_execution_config is None:
        raise AppError(
            404,
            "coverage_execution_config_not_found",
            "Coverage execution config was not found for this repository.",
        )
    return repository.coverage_execution_config


def update_coverage_execution_config(
    db: Session, repository_id: UUID, payload: CoverageExecutionConfigUpdate
) -> CoverageExecutionConfig:
    config = get_coverage_execution_config(db, repository_id)
    values = payload.model_dump(exclude_unset=True)

    if "language" in values:
        language = CoverageLanguage(values["language"])
        defaults = DEFAULTS_BY_LANGUAGE[language]
        config.language = language
        for field, value in defaults.items():
            if field not in values:
                setattr(config, field, value)

    for field, value in values.items():
        if field == "language":
            continue
        if field == "report_format" and value is not None:
            value = CoverageReportFormat(value)
        setattr(config, field, value)

    config.language_preset_confirmed = True

    expected_format = DEFAULTS_BY_LANGUAGE[config.language]["report_format"]
    if config.report_format != expected_format:
        raise AppError(
            422,
            "coverage_report_format_invalid",
            f"{config.language.value} coverage requires {expected_format.value} report format.",
        )

    db.commit()
    db.refresh(config)
    return config

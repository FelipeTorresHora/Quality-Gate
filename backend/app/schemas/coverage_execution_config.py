from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

CoverageLanguageValue = Literal["python", "typescript", "javascript", "go"]
CoverageReportFormatValue = Literal["cobertura_xml", "lcov", "go_coverprofile"]

EXPECTED_FORMAT_BY_LANGUAGE = {
    "python": "cobertura_xml",
    "typescript": "lcov",
    "javascript": "lcov",
    "go": "go_coverprofile",
}


class CoverageExecutionConfigUpdate(BaseModel):
    language: CoverageLanguageValue | None = None
    install_command: str | None = None
    test_command: str | None = Field(default=None, min_length=1)
    report_path: str | None = Field(default=None, min_length=1)
    report_format: CoverageReportFormatValue | None = None

    @model_validator(mode="after")
    def validate_language_report_format(self) -> "CoverageExecutionConfigUpdate":
        if self.test_command is not None and not self.test_command.strip():
            raise ValueError("test_command must not be blank")
        if self.report_path is not None and not self.report_path.strip():
            raise ValueError("report_path must not be blank")
        if self.language is not None and self.report_format is not None:
            expected = EXPECTED_FORMAT_BY_LANGUAGE[self.language]
            if self.report_format != expected:
                raise ValueError(
                    f"{self.language} coverage requires {expected} report format"
                )
        return self


class CoverageExecutionConfigRead(BaseModel):
    id: UUID
    repository_id: UUID
    language: CoverageLanguageValue
    install_command: str
    test_command: str
    report_path: str
    report_format: CoverageReportFormatValue
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

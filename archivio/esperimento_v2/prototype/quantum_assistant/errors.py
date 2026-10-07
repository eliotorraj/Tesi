'Structured errors produced during request preparation.'

from __future__ import annotations

from .models import ValidationReport


class RequestValidationError(ValueError):
    'Report an invalid request before data retrieval.'

    retryable = False

    def __init__(self, report: ValidationReport) -> None:
        'Retain the report and prepare a readable message.'
        self.report = report
        self.code = (
            report.issues[0].code if report.issues else "REQUEST_VALIDATION_FAILED"
        )
        message = "; ".join(
            f"{issue.path}: {issue.message}" for issue in report.issues
        )
        super().__init__(message or 'Invalid request.')

    def to_dict(self) -> dict[str, object]:
        'Return the error in a UI-ready format.'
        return {
            "code": self.code,
            "retryable": self.retryable,
            "validation": self.report.to_dict(),
        }

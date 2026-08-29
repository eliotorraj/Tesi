"""Typed request-preparation errors."""

from __future__ import annotations

from .models import ValidationReport


class RequestValidationError(ValueError):
    """Raised before retrieval when request validation fails."""

    retryable = False

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        self.code = (
            report.issues[0].code if report.issues else "REQUEST_VALIDATION_FAILED"
        )
        message = "; ".join(
            f"{issue.path}: {issue.message}" for issue in report.issues
        )
        super().__init__(message or "Richiesta non valida.")

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "retryable": self.retryable,
            "validation": self.report.to_dict(),
        }

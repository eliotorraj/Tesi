"""Errori strutturati prodotti durante la preparazione della richiesta."""

from __future__ import annotations

from .models import ValidationReport


class RequestValidationError(ValueError):
    """Segnala una richiesta non valida prima del recupero dei dati."""

    retryable = False

    def __init__(self, report: ValidationReport) -> None:
        """Conserva il rapporto e prepara un messaggio leggibile."""
        self.report = report
        self.code = (
            report.issues[0].code if report.issues else "REQUEST_VALIDATION_FAILED"
        )
        message = "; ".join(
            f"{issue.path}: {issue.message}" for issue in report.issues
        )
        super().__init__(message or "Richiesta non valida.")

    def to_dict(self) -> dict[str, object]:
        """Restituisce l'errore in un formato adatto alla UI."""
        return {
            "code": self.code,
            "retryable": self.retryable,
            "validation": self.report.to_dict(),
        }

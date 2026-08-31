"""Controllore per la UI con raccomandazioni conservate lato servizio."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import ApprovedCompilation, RecommendationResult
from .ports import RequestInput
from .services import PrototypeService


class PrototypeController:
    """Espone il prototipo a una futura UI REST, desktop o da terminale.

    Le raccomandazioni validate restano sul lato servizio. In questo modo la
    compilazione non accetta dati modificati dal client. In produzione questa
    memoria temporanea potrà essere sostituita da una memoria persistente.
    """

    def __init__(self, service: PrototypeService) -> None:
        """Collega il controllore al servizio applicativo."""
        self._service = service
        self._recommendations: dict[str, RecommendationResult] = {}

    def get_hardware_catalog(self) -> dict[str, Any]:
        """Restituisce il catalogo usato sia dalla UI sia dal servizio."""
        return self._service.hardware_catalog.snapshot().to_dict()

    def prepare_request(self, submission: RequestInput) -> dict[str, Any]:
        """Prepara la richiesta senza interrogare Dataset o LLM."""
        return self._service.prepare_request(submission).to_dict()

    def request_recommendation(self, submission: RequestInput) -> dict[str, Any]:
        """Genera e conserva una raccomandazione già validata."""
        result = self._service.recommend(submission)
        self._recommendations[result.request.request_id] = result
        return {
            "request_id": result.request.request_id,
            "recommendation": asdict(result.recommendation),
            "attempts": result.attempts,
            "hardware_mask": result.compatibility.to_dict(),
            "compatible_hardware": list(
                result.compatibility.available_device_ids
            ),
            "unavailable_hardware": {
                device: list(reasons)
                for device, reasons in result.compatibility.unavailable.items()
            },
            "retrieved_record_ids": [
                example.record_id for example in result.retrieved_examples
            ],
            "requires_user_confirmation_for_compilation": True,
        }

    def compile_recommendation(
        self,
        request_id: str,
        *,
        user_confirmed: bool,
    ) -> dict[str, Any]:
        """Compila una raccomandazione conservata dopo la conferma."""
        try:
            result = self._recommendations[request_id]
        except KeyError as exc:
            raise KeyError(
                f"Nessuna recommendation validata per request_id={request_id!r}."
            ) from exc
        artifact = self._service.compile_approved(
            ApprovedCompilation(
                recommendation_result=result,
                user_confirmed=user_confirmed,
            )
        )
        return asdict(artifact)

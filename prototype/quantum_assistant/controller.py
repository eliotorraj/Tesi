"""Thin UI-facing controller with server-side recommendation state."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import ApprovedCompilation, RecommendationResult
from .ports import RequestInput
from .services import PrototypeService


class PrototypeController:
    """Adapter usable by a future REST, desktop, or command-line UI.

    Validated recommendations are retained server-side so the compilation
    endpoint does not trust an edited recommendation sent back by the client.
    Replace this in-memory store with persistent session storage for deployment.
    """

    def __init__(self, service: PrototypeService) -> None:
        self._service = service
        self._recommendations: dict[str, RecommendationResult] = {}

    def get_hardware_catalog(self) -> dict[str, Any]:
        """Return the canonical options used by both UI and backend."""
        return self._service.hardware_catalog.snapshot().to_dict()

    def prepare_request(self, submission: RequestInput) -> dict[str, Any]:
        """Expose the terminal pre-RAG boundary to a future UI/API."""
        return self._service.prepare_request(submission).to_dict()

    def request_recommendation(self, submission: RequestInput) -> dict[str, Any]:
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

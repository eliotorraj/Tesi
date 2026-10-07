'UI controller with recommendations retained on the service side.'

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import ApprovedCompilation, RecommendationResult
from .ports import RequestInput
from .services import PrototypeService


class PrototypeController:
    """Expose the prototype to a future REST, desktop or terminal UI.

Validated recommendations remain on the service side, so compilation does not accept client-modified data. Production deployment can replace this temporary storage with persistent storage."""

    def __init__(self, service: PrototypeService) -> None:
        'Connect the controller to the application service.'
        self._service = service
        self._recommendations: dict[str, RecommendationResult] = {}

    def get_hardware_catalog(self) -> dict[str, Any]:
        'Return the catalog shared by the UI and service.'
        return self._service.hardware_catalog.snapshot().to_dict()

    def prepare_request(self, submission: RequestInput) -> dict[str, Any]:
        'Prepare the request without querying the Dataset or LLM.'
        return self._service.prepare_request(submission).to_dict()

    def request_recommendation(self, submission: RequestInput) -> dict[str, Any]:
        'Generate and retain an already validated recommendation.'
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
        'Compile a retained recommendation after confirmation.'
        try:
            result = self._recommendations[request_id]
        except KeyError as exc:
            raise KeyError(
                f'No validated recommendation for request_id={request_id!r}.'
            ) from exc
        artifact = self._service.compile_approved(
            ApprovedCompilation(
                recommendation_result=result,
                user_confirmed=user_confirmed,
            )
        )
        return asdict(artifact)

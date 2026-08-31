"""Costruzione del prototipo locale con gli adattatori predefiniti."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from qiskit_dataset.catalog import load_catalog

from .adapters.compilation import QiskitDeterministicCompiler
from .adapters.context import (
    JsonDatasetContextRetriever,
    StructuredEvidenceRegistryBuilder,
    StructuredPromptBuilder,
)
from .adapters.parsing import (
    HardwareMaskBuilder,
    MqtHardwareCatalog,
    QasmRequestParser,
    RequestSemanticValidator,
)
from .adapters.validation import StructuredRecommendationValidator
from .ports import LlmGateway
from .services import PrototypeService


def build_default_service(
    *,
    device_names: Sequence[str],
    dataset_path: Path,
    llm_gateway: LlmGateway,
    max_llm_attempts: int = 3,
    retrieval_limit: int = 5,
    dataset_required: bool = False,
) -> PrototypeService:
    """Costruisce il servizio lasciando sostituibile il collegamento all'LLM."""
    configuration_catalog = load_catalog()
    hardware_catalog = MqtHardwareCatalog(
        device_names,
        configuration_catalog=configuration_catalog,
    )
    return PrototypeService(
        parser=QasmRequestParser(),
        hardware_catalog=hardware_catalog,
        semantic_validator=RequestSemanticValidator(),
        compatibility_filter=HardwareMaskBuilder(),
        context_retriever=JsonDatasetContextRetriever(
            dataset_path,
            required=dataset_required,
        ),
        prompt_builder=StructuredPromptBuilder(
            configuration_catalog=configuration_catalog,
        ),
        evidence_registry_builder=StructuredEvidenceRegistryBuilder(
            configuration_catalog=configuration_catalog,
        ),
        llm_gateway=llm_gateway,
        validator=StructuredRecommendationValidator(
            configuration_catalog=configuration_catalog,
        ),
        compiler=QiskitDeterministicCompiler(),
        max_llm_attempts=max_llm_attempts,
        retrieval_limit=retrieval_limit,
    )

"""Composition root for the default local prototype."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .adapters.compilation import QiskitDeterministicCompiler
from .adapters.context import JsonDatasetContextRetriever, StructuredPromptBuilder
from .adapters.parsing import (
    MqtHardwareCatalog,
    QasmRequestParser,
    WidthCompatibilityFilter,
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
    """Wire default adapters while keeping the concrete LLM provider injectable."""
    return PrototypeService(
        parser=QasmRequestParser(),
        hardware_catalog=MqtHardwareCatalog(device_names),
        compatibility_filter=WidthCompatibilityFilter(),
        context_retriever=JsonDatasetContextRetriever(
            dataset_path,
            required=dataset_required,
        ),
        prompt_builder=StructuredPromptBuilder(),
        llm_gateway=llm_gateway,
        validator=StructuredRecommendationValidator(),
        compiler=QiskitDeterministicCompiler(),
        max_llm_attempts=max_llm_attempts,
        retrieval_limit=retrieval_limit,
    )

"""Replaceable boundaries of the LLM prototype."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from .models import (
    CompatibilityReport,
    CompilationArtifact,
    HardwareProfile,
    ParsedRequest,
    PromptEnvelope,
    Recommendation,
    RetrievedExample,
    UiSubmission,
    ValidationResult,
)


class RequestParser(Protocol):
    def parse(self, submission: UiSubmission) -> ParsedRequest:
        """Validate the circuit and normalize the UI request."""


class HardwareCatalog(Protocol):
    def list_hardware(self) -> Sequence[HardwareProfile]:
        """Return the hardware currently exposed by the prototype."""


class CompatibilityFilter(Protocol):
    def filter(
        self,
        request: ParsedRequest,
        hardware: Sequence[HardwareProfile],
    ) -> CompatibilityReport:
        """Partition hardware into available and unavailable candidates."""


class ContextRetriever(Protocol):
    def retrieve(
        self,
        request: ParsedRequest,
        compatibility: CompatibilityReport,
        *,
        limit: int,
    ) -> Sequence[RetrievedExample]:
        """Return prompt-safe context from the Dataset or a RAG index."""


class PromptBuilder(Protocol):
    def build(
        self,
        request: ParsedRequest,
        compatibility: CompatibilityReport,
        examples: Sequence[RetrievedExample],
        *,
        validation_errors: Sequence[str] = (),
    ) -> PromptEnvelope:
        """Build a provider-neutral structured prompt."""


class LlmGateway(Protocol):
    def generate(self, prompt: PromptEnvelope) -> Mapping[str, Any]:
        """Return a structured response already decoded from JSON."""


class RecommendationValidator(Protocol):
    def validate(
        self,
        raw_response: Mapping[str, Any],
        request: ParsedRequest,
        compatibility: CompatibilityReport,
    ) -> ValidationResult:
        """Validate schema, compatibility, and executable parameters."""


class DeterministicCompiler(Protocol):
    def compile(
        self,
        request: ParsedRequest,
        recommendation: Recommendation,
    ) -> CompilationArtifact:
        """Compile with deterministic local tools, never with LLM-generated code."""

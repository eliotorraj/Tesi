"""Replaceable boundaries of the LLM prototype."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from .models import (
    CompatibilityView,
    CompilationArtifact,
    HardwareCatalogSnapshot,
    HardwareMaskResult,
    HardwareProfile,
    NormalizedRequest,
    ParsedRequest,
    PromptEnvelope,
    Recommendation,
    RetrievedExample,
    UiSubmission,
    UserRequest,
    ValidationResult,
)


RequestInput = UserRequest | UiSubmission | Mapping[str, Any] | str | bytes


class RequestParser(Protocol):
    def parse(self, submission: RequestInput) -> ParsedRequest:
        """Validate JSON/QASM syntax and derive deterministic circuit data."""


class HardwareCatalog(Protocol):
    def snapshot(self) -> HardwareCatalogSnapshot:
        """Return the immutable catalog shared by every phase."""

    def list_hardware(self) -> Sequence[HardwareProfile]:
        """Backward-compatible device view of the same snapshot."""


class SemanticRequestValidator(Protocol):
    def normalize(
        self,
        request: ParsedRequest,
        catalog: HardwareCatalogSnapshot,
    ) -> NormalizedRequest:
        """Validate catalog-dependent rules and normalize the request."""


class CompatibilityFilter(Protocol):
    def filter(
        self,
        request: NormalizedRequest,
        hardware: HardwareCatalogSnapshot,
    ) -> HardwareMaskResult:
        """Apply all hard constraints to the validated snapshot."""


class ContextRetriever(Protocol):
    def retrieve(
        self,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        *,
        limit: int,
    ) -> Sequence[RetrievedExample]:
        """Return prompt-safe context from the Dataset or a RAG index."""


class PromptBuilder(Protocol):
    def build(
        self,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
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
        request: NormalizedRequest,
        compatibility: CompatibilityView,
    ) -> ValidationResult:
        """Validate schema, compatibility, and executable parameters."""


class DeterministicCompiler(Protocol):
    def compile(
        self,
        request: NormalizedRequest,
        recommendation: Recommendation,
    ) -> CompilationArtifact:
        """Compile with deterministic local tools, never with LLM-generated code."""

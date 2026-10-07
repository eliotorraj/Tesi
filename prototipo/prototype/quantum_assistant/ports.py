'Replaceable interfaces used by prototype components.'

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from .models import (
    CompatibilityView,
    CompilationArtifact,
    EvidenceReference,
    EvidenceRegistry,
    HardwareCatalogSnapshot,
    HardwareMaskResult,
    HardwareProfile,
    LlmOutput,
    NormalizedRequest,
    ParsedRequest,
    PromptEnvelope,
    Recommendation,
    RenderedExplanation,
    RetrievedExample,
    SupportedClaim,
    UiSubmission,
    UserRequest,
    ValidationIssue,
    ValidationResult,
)


RequestInput = UserRequest | UiSubmission | Mapping[str, Any] | str | bytes


class RequestParser(Protocol):
    'Parse and validate an incoming request.'

    def parse(self, submission: RequestInput) -> ParsedRequest:
        'Validate JSON and QASM and derive circuit data.'


class HardwareCatalog(Protocol):
    'Provide the current hardware catalog snapshot.'

    def snapshot(self) -> HardwareCatalogSnapshot:
        'Return the immutable catalog shared by every stage.'

    def list_hardware(self) -> Sequence[HardwareProfile]:
        'Return the device view retained for compatibility.'


class SemanticRequestValidator(Protocol):
    'Check request semantics against the catalog.'

    def normalize(
        self,
        request: ParsedRequest,
        catalog: HardwareCatalogSnapshot,
    ) -> NormalizedRequest:
        'Check catalog rules and normalize the request.'


class CompatibilityFilter(Protocol):
    'Apply hardware constraints to the normalized request.'

    def filter(
        self,
        request: NormalizedRequest,
        hardware: HardwareCatalogSnapshot,
    ) -> HardwareMaskResult:
        'Apply all hard constraints to the validated snapshot.'


class ContextRetriever(Protocol):
    'Retrieve historical circuits closest to the request.'

    def retrieve(
        self,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        *,
        limit: int,
    ) -> Sequence[RetrievedExample]:
        'Return verified context from the Dataset or RAG index.'


class EvidenceRegistryBuilder(Protocol):
    'Build the registry of usable evidence.'

    def build(
        self,
        examples: Sequence[RetrievedExample],
    ) -> EvidenceRegistry:
        'Build the immutable registry for retrieved results.'


class PromptBuilder(Protocol):
    'Prepare the structured request sent to the LLM.'

    def build(
        self,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        examples: Sequence[RetrievedExample],
        *,
        evidence_registry: EvidenceRegistry,
        validation_issues: Sequence[ValidationIssue] = (),
    ) -> PromptEnvelope:
        'Build a provider-independent structured message.'


class LlmGateway(Protocol):
    'Define a replaceable LLM connection.'

    def generate(self, prompt: PromptEnvelope) -> LlmOutput:
        'Return JSON text or an already decoded JSON object.'


class RecommendationValidator(Protocol):
    'Validate an LLM-generated recommendation.'

    def validate(
        self,
        raw_response: LlmOutput,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        catalog: HardwareCatalogSnapshot | None = None,
        *,
        evidence_registry: EvidenceRegistry,
        citation_context=None,
    ) -> ValidationResult:
        'Check schema, compatibility and compilation parameters.'


class ExplanationRenderer(Protocol):
    'Turn validated claims into a readable explanation.'

    def render(
        self,
        claims: Sequence[SupportedClaim],
        evidence_references: Sequence[EvidenceReference],
        evidence_registry: EvidenceRegistry,
    ) -> RenderedExplanation:
        'Describe only validated claims and resolved historical sources.'


class DeterministicCompiler(Protocol):
    'Compile using validated parameters only.'

    def compile(
        self,
        request: NormalizedRequest,
        recommendation: Recommendation,
    ) -> CompilationArtifact:
        'Compile with local tools without executing LLM-generated code.'

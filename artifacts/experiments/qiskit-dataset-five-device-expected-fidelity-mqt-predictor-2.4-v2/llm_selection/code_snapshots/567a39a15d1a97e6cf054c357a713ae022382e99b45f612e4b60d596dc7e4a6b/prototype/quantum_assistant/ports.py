"""Interfacce sostituibili usate dai componenti del prototipo."""

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
    """Interpreta e controlla una richiesta in ingresso."""

    def parse(self, submission: RequestInput) -> ParsedRequest:
        """Controlla JSON e QASM e ricava i dati del circuito."""


class HardwareCatalog(Protocol):
    """Fornisce l'istantanea corrente del catalogo hardware."""

    def snapshot(self) -> HardwareCatalogSnapshot:
        """Restituisce il catalogo immutabile condiviso da tutte le fasi."""

    def list_hardware(self) -> Sequence[HardwareProfile]:
        """Restituisce la vista dei dispositivi mantenuta per compatibilità."""


class SemanticRequestValidator(Protocol):
    """Controlla il significato della richiesta rispetto al catalogo."""

    def normalize(
        self,
        request: ParsedRequest,
        catalog: HardwareCatalogSnapshot,
    ) -> NormalizedRequest:
        """Controlla le regole del catalogo e normalizza la richiesta."""


class CompatibilityFilter(Protocol):
    """Applica i vincoli hardware alla richiesta normalizzata."""

    def filter(
        self,
        request: NormalizedRequest,
        hardware: HardwareCatalogSnapshot,
    ) -> HardwareMaskResult:
        """Applica tutti i vincoli rigidi all'istantanea validata."""


class ContextRetriever(Protocol):
    """Recupera i circuiti storici più vicini alla richiesta."""

    def retrieve(
        self,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        *,
        limit: int,
    ) -> Sequence[RetrievedExample]:
        """Restituisce il contesto sicuro ricavato dal Dataset o dall'indice RAG."""


class EvidenceRegistryBuilder(Protocol):
    """Costruisce il registro delle evidenze utilizzabili."""

    def build(
        self,
        examples: Sequence[RetrievedExample],
    ) -> EvidenceRegistry:
        """Costruisce il registro immutabile per i risultati recuperati."""


class PromptBuilder(Protocol):
    """Prepara la richiesta strutturata da inviare all'LLM."""

    def build(
        self,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        examples: Sequence[RetrievedExample],
        *,
        evidence_registry: EvidenceRegistry,
        validation_issues: Sequence[ValidationIssue] = (),
    ) -> PromptEnvelope:
        """Costruisce un messaggio strutturato indipendente dal fornitore."""


class LlmGateway(Protocol):
    """Definisce il collegamento sostituibile con un LLM."""

    def generate(self, prompt: PromptEnvelope) -> LlmOutput:
        """Restituisce testo JSON oppure un oggetto JSON già decodificato."""


class RecommendationValidator(Protocol):
    """Controlla una raccomandazione prodotta dall'LLM."""

    def validate(
        self,
        raw_response: LlmOutput,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        catalog: HardwareCatalogSnapshot | None = None,
        *,
        evidence_registry: EvidenceRegistry,
    ) -> ValidationResult:
        """Controlla schema, compatibilità e parametri di compilazione."""


class ExplanationRenderer(Protocol):
    """Trasforma claim validati in una spiegazione leggibile."""

    def render(
        self,
        claims: Sequence[SupportedClaim],
        evidence_references: Sequence[EvidenceReference],
        evidence_registry: EvidenceRegistry,
    ) -> RenderedExplanation:
        """Descrive solo claim validati e fonti storiche risolte."""


class DeterministicCompiler(Protocol):
    """Compila usando soltanto parametri già validati."""

    def compile(
        self,
        request: NormalizedRequest,
        recommendation: Recommendation,
    ) -> CompilationArtifact:
        """Compila con strumenti locali, senza eseguire codice generato dall'LLM."""

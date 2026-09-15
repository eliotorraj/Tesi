"""Coordinamento della raccomandazione e della compilazione approvata."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import (
    ApprovedCompilation,
    CompilationArtifact,
    HardwareMaskResult,
    NO_ELIGIBLE_DEVICE_CODE,
    NO_ELIGIBLE_DEVICE_MESSAGE,
    PreparedRequestContext,
    RecommendationResult,
    ValidationIssue,
)
from .ports import (
    CompatibilityFilter,
    ContextRetriever,
    DeterministicCompiler,
    EvidenceRegistryBuilder,
    HardwareCatalog,
    LlmGateway,
    PromptBuilder,
    RecommendationValidator,
    RequestInput,
    RequestParser,
    SemanticRequestValidator,
)


class NoCompatibleHardwareError(RuntimeError):
    """Base mantenuta per i chiamanti delle versioni precedenti."""


class NoEligibleDeviceError(NoCompatibleHardwareError):
    """Segnala che nessun dispositivo soddisfa una richiesta valida."""

    code = NO_ELIGIBLE_DEVICE_CODE
    retryable = False

    def __init__(self, mask_result: HardwareMaskResult) -> None:
        """Conserva la maschera che spiega l'esito negativo."""
        self.mask_result = mask_result
        super().__init__(NO_ELIGIBLE_DEVICE_MESSAGE)

    def to_dict(self) -> dict[str, object]:
        """Restituisce l'errore e la diagnostica in forma strutturata."""
        return {
            "code": self.code,
            "retryable": self.retryable,
            "message": str(self),
            "mask_result": self.mask_result.to_dict(),
        }


class LlmValidationExhaustedError(RuntimeError):
    """Segnala l'esaurimento dei tentativi per output LLM non validi."""

    code = "LLM_OUTPUT_VALIDATION_EXHAUSTED"
    retryable = False

    def __init__(
        self,
        attempts: int,
        issues: tuple[ValidationIssue, ...],
    ) -> None:
        """Conserva il numero di tentativi e gli ultimi errori trovati."""
        if attempts <= 0 or not issues:
            raise ValueError(
                "L'esaurimento richiede tentativi positivi e almeno un errore."
            )
        self.attempts = attempts
        self.issues = tuple(issues)
        self.errors = tuple(issue.message for issue in self.issues)
        super().__init__(
            f"Nessuna risposta LLM valida dopo {attempts} tentativi."
        )

    def to_dict(self) -> dict[str, object]:
        """Restituisce un errore stabile adatto alla UI."""
        return {
            "code": self.code,
            "retryable": self.retryable,
            "message": str(self),
            "attempts": self.attempts,
            "issues": [
                {
                    "code": issue.code,
                    "path": issue.path,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }


class ConfirmationRequiredError(RuntimeError):
    """Segnala che manca la conferma esplicita dell'utente."""


class UnvalidatedRecommendationError(RuntimeError):
    """Rifiuta un risultato che non è stato validato da questo servizio."""

    code = "RECOMMENDATION_NOT_ISSUED"
    retryable = False

    def __init__(self) -> None:
        """Prepara il messaggio stabile restituito al chiamante."""
        super().__init__(
            "La compilazione richiede una raccomandazione validata "
            "dall'istanza corrente del servizio."
        )


def _default_semantic_validator() -> SemanticRequestValidator:
    """Crea il validatore semantico usato in assenza di un sostituto."""
    # L'import locale mantiene la dipendenza dalle porte verso gli adattatori.
    from .adapters.request import RequestSemanticValidator

    return RequestSemanticValidator()


def _default_evidence_registry_builder() -> EvidenceRegistryBuilder:
    """Crea il costruttore predefinito del registro delle evidenze."""
    # L'import locale mantiene la dipendenza dalle porte verso gli adattatori.
    from .adapters.context import StructuredEvidenceRegistryBuilder

    return StructuredEvidenceRegistryBuilder()


@dataclass
class PrototypeService:
    """Coordina i componenti applicativi usati da ogni controllore UI."""

    parser: RequestParser
    hardware_catalog: HardwareCatalog
    compatibility_filter: CompatibilityFilter
    context_retriever: ContextRetriever
    prompt_builder: PromptBuilder
    llm_gateway: LlmGateway
    validator: RecommendationValidator
    compiler: DeterministicCompiler
    max_llm_attempts: int = 3
    retrieval_limit: int = 5
    semantic_validator: SemanticRequestValidator = field(
        default_factory=_default_semantic_validator
    )
    evidence_registry_builder: EvidenceRegistryBuilder = field(
        default_factory=_default_evidence_registry_builder
    )
    _issued_recommendations: list[RecommendationResult] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Controlla i limiti configurati per tentativi e recupero."""
        if self.max_llm_attempts <= 0:
            raise ValueError("max_llm_attempts deve essere positivo.")
        if self.retrieval_limit < 0:
            raise ValueError("retrieval_limit non può essere negativo.")

    def prepare_request(
        self,
        submission: RequestInput,
    ) -> PreparedRequestContext:
        """Prepara richiesta, catalogo e maschera senza chiamare l'LLM."""
        parsed = self.parser.parse(submission)
        catalog = self.hardware_catalog.snapshot()
        request = self.semantic_validator.normalize(parsed, catalog)
        mask_result = self.compatibility_filter.filter(request, catalog)
        return PreparedRequestContext(
            request=request,
            hardware_catalog=catalog,
            mask_result=mask_result,
        )

    def recommend(self, submission: RequestInput) -> RecommendationResult:
        """Recupera il contesto e ripete solo gli output LLM non validi."""
        prepared = self.prepare_request(submission)
        if not prepared.can_recommend:
            raise NoEligibleDeviceError(prepared.mask_result)

        request = prepared.request
        compatibility = prepared.mask_result
        examples = tuple(
            self.context_retriever.retrieve(
                request,
                compatibility,
                limit=self.retrieval_limit,
            )
        )
        evidence_registry = self.evidence_registry_builder.build(examples)
        validation_issues: tuple[ValidationIssue, ...] = ()
        for attempt in range(1, self.max_llm_attempts + 1):
            prompt = self.prompt_builder.build(
                request,
                compatibility,
                examples,
                evidence_registry=evidence_registry,
                validation_issues=validation_issues,
            )
            raw_response = self.llm_gateway.generate(prompt)
            validation = self.validator.validate(
                raw_response,
                request,
                compatibility,
                prepared.hardware_catalog,
                evidence_registry=evidence_registry,
            )
            if validation.is_valid and validation.recommendation is not None:
                result = RecommendationResult(
                    request=request,
                    compatibility=compatibility,
                    retrieved_examples=examples,
                    evidence_registry=evidence_registry,
                    recommendation=validation.recommendation,
                    attempts=attempt,
                )
                self._issued_recommendations.append(result)
                return result
            validation_issues = validation.issues

        raise LlmValidationExhaustedError(
            self.max_llm_attempts,
            validation_issues,
        )

    def compile_approved(
        self,
        command: ApprovedCompilation,
    ) -> CompilationArtifact:
        """Compila solo una raccomandazione validata e confermata."""
        if not command.user_confirmed:
            raise ConfirmationRequiredError(
                "La compilazione richiede una conferma esplicita dell'utente."
            )
        result = command.recommendation_result
        if not any(
            issued_result is result
            for issued_result in self._issued_recommendations
        ):
            raise UnvalidatedRecommendationError()
        return self.compiler.compile(result.request, result.recommendation)

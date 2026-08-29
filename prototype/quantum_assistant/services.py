"""Application orchestration for recommendation and approved compilation."""

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
)
from .ports import (
    CompatibilityFilter,
    ContextRetriever,
    DeterministicCompiler,
    HardwareCatalog,
    LlmGateway,
    PromptBuilder,
    RecommendationValidator,
    RequestInput,
    RequestParser,
    SemanticRequestValidator,
)


class NoCompatibleHardwareError(RuntimeError):
    """Legacy base retained for callers of the previous prototype."""


class NoEligibleDeviceError(NoCompatibleHardwareError):
    """Terminal pre-LLM outcome for a valid but unsatisfiable request."""

    code = NO_ELIGIBLE_DEVICE_CODE
    retryable = False

    def __init__(self, mask_result: HardwareMaskResult) -> None:
        self.mask_result = mask_result
        super().__init__(NO_ELIGIBLE_DEVICE_MESSAGE)

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "retryable": self.retryable,
            "message": str(self),
            "mask_result": self.mask_result.to_dict(),
        }


class LlmValidationExhaustedError(RuntimeError):
    """Raised when every LLM response failed deterministic validation."""

    def __init__(self, attempts: int, errors: tuple[str, ...]) -> None:
        self.attempts = attempts
        self.errors = errors
        super().__init__(
            f"Nessuna risposta LLM valida dopo {attempts} tentativi: "
            + "; ".join(errors)
        )


class ConfirmationRequiredError(RuntimeError):
    """Raised when compilation is requested without explicit user approval."""


def _default_semantic_validator() -> SemanticRequestValidator:
    # Local import preserves the ports/adapters dependency direction.
    from .adapters.request import RequestSemanticValidator

    return RequestSemanticValidator()


@dataclass
class PrototypeService:
    """Facade called by any concrete UI controller."""

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

    def __post_init__(self) -> None:
        if self.max_llm_attempts <= 0:
            raise ValueError("max_llm_attempts deve essere positivo.")
        if self.retrieval_limit < 0:
            raise ValueError("retrieval_limit non può essere negativo.")

    def prepare_request(
        self,
        submission: RequestInput,
    ) -> PreparedRequestContext:
        """Stop after syntax, semantics, catalog snapshot, and hardware mask."""
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
        """Prepare once, then run the unchanged retrieval/LLM/retry boundary."""
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
        validation_errors: tuple[str, ...] = ()
        for attempt in range(1, self.max_llm_attempts + 1):
            prompt = self.prompt_builder.build(
                request,
                compatibility,
                examples,
                validation_errors=validation_errors,
            )
            raw_response = self.llm_gateway.generate(prompt)
            validation = self.validator.validate(
                raw_response,
                request,
                compatibility,
            )
            if validation.is_valid and validation.recommendation is not None:
                return RecommendationResult(
                    request=request,
                    compatibility=compatibility,
                    retrieved_examples=examples,
                    recommendation=validation.recommendation,
                    attempts=attempt,
                )
            validation_errors = validation.errors or (
                "Il validatore ha rifiutato la risposta senza dettagli.",
            )

        raise LlmValidationExhaustedError(
            self.max_llm_attempts,
            validation_errors,
        )

    def compile_approved(
        self,
        command: ApprovedCompilation,
    ) -> CompilationArtifact:
        """Compile only a previously validated recommendation approved by the user."""
        if not command.user_confirmed:
            raise ConfirmationRequiredError(
                "La compilazione richiede una conferma esplicita dell'utente."
            )
        result = command.recommendation_result
        return self.compiler.compile(result.request, result.recommendation)

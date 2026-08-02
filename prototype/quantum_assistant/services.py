"""Application orchestration for recommendation and approved compilation."""

from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ApprovedCompilation,
    CompilationArtifact,
    RecommendationResult,
    UiSubmission,
)
from .ports import (
    CompatibilityFilter,
    ContextRetriever,
    DeterministicCompiler,
    HardwareCatalog,
    LlmGateway,
    PromptBuilder,
    RecommendationValidator,
    RequestParser,
)


class NoCompatibleHardwareError(RuntimeError):
    """Raised when every configured device is unavailable."""


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

    def __post_init__(self) -> None:
        if self.max_llm_attempts <= 0:
            raise ValueError("max_llm_attempts deve essere positivo.")
        if self.retrieval_limit < 0:
            raise ValueError("retrieval_limit non puo essere negativo.")

    def recommend(self, submission: UiSubmission) -> RecommendationResult:
        """Run parse, compatibility, retrieval, LLM, validation, and retry."""
        request = self.parser.parse(submission)
        hardware = self.hardware_catalog.list_hardware()
        compatibility = self.compatibility_filter.filter(request, hardware)
        if not compatibility.available:
            details = ", ".join(
                f"{device}: {', '.join(reasons)}"
                for device, reasons in sorted(compatibility.unavailable.items())
            )
            raise NoCompatibleHardwareError(details or "Nessun device configurato.")

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

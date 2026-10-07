'Coordinate recommendations and approved compilation.'

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
    'Base class retained for callers of earlier versions.'


class NoEligibleDeviceError(NoCompatibleHardwareError):
    'Report that no device satisfies a valid request.'

    code = NO_ELIGIBLE_DEVICE_CODE
    retryable = False

    def __init__(self, mask_result: HardwareMaskResult) -> None:
        'Retain the mask explaining the negative outcome.'
        self.mask_result = mask_result
        super().__init__(NO_ELIGIBLE_DEVICE_MESSAGE)

    def to_dict(self) -> dict[str, object]:
        'Return the error and diagnostics in structured form.'
        return {
            "code": self.code,
            "retryable": self.retryable,
            "message": str(self),
            "mask_result": self.mask_result.to_dict(),
        }


class LlmValidationExhaustedError(RuntimeError):
    'Report exhausted attempts for invalid LLM output.'

    code = "LLM_OUTPUT_VALIDATION_EXHAUSTED"
    retryable = False

    def __init__(
        self,
        attempts: int,
        issues: tuple[ValidationIssue, ...],
    ) -> None:
        'Retain attempt count and the most recent errors.'
        if attempts <= 0 or not issues:
            raise ValueError(
                'Exhaustion requires a positive attempt count and at least one error.'
            )
        self.attempts = attempts
        self.issues = tuple(issues)
        self.errors = tuple(issue.message for issue in self.issues)
        super().__init__(
            f'No valid LLM response after {attempts} attempts.'
        )

    def to_dict(self) -> dict[str, object]:
        'Return a stable UI-suitable error.'
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
    'Report missing explicit user confirmation.'


class UnvalidatedRecommendationError(RuntimeError):
    'Reject a result not validated by this service.'

    code = "RECOMMENDATION_NOT_ISSUED"
    retryable = False

    def __init__(self) -> None:
        'Prepare the stable message returned to the caller.'
        super().__init__(
            'Compilation requires a recommendation validated by this service instance.'
        )


def _default_semantic_validator() -> SemanticRequestValidator:
    'Create the default semantic validator when none is supplied.'
    # The local import retains the dependency from ports to adapters.
    from .adapters.request import RequestSemanticValidator

    return RequestSemanticValidator()


def _default_evidence_registry_builder() -> EvidenceRegistryBuilder:
    'Create the default evidence-registry builder.'
    # The local import retains the dependency from ports to adapters.
    from .adapters.context import StructuredEvidenceRegistryBuilder

    return StructuredEvidenceRegistryBuilder()


@dataclass
class PrototypeService:
    'Coordinate the application components used by each UI controller.'

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
        'Check configured attempt and retrieval limits.'
        if self.max_llm_attempts <= 0:
            raise ValueError('max_llm_attempts must be positive.')
        if self.retrieval_limit < 0:
            raise ValueError('retrieval_limit cannot be negative.')

    def prepare_request(
        self,
        submission: RequestInput,
    ) -> PreparedRequestContext:
        'Prepare request, catalog and mask without calling the LLM.'
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
        'Retrieve context and retry only invalid LLM outputs.'
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
            from prototype.prompting.minimal import citation_context, CONTRACT_VERSION
            context_options = {}
            if prompt.payload.get("response_contract", {}).get("version") == CONTRACT_VERSION:
                context_options["citation_context"] = citation_context(prompt.payload)
            raw_response = self.llm_gateway.generate(prompt)
            validation = self.validator.validate(
                raw_response,
                request,
                compatibility,
                prepared.hardware_catalog,
                evidence_registry=evidence_registry,
                **context_options,
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
        'Compile only a validated, confirmed recommendation.'
        if not command.user_confirmed:
            raise ConfirmationRequiredError(
                'Compilation requires explicit user confirmation.'
            )
        result = command.recommendation_result
        if not any(
            issued_result is result
            for issued_result in self._issued_recommendations
        ):
            raise UnvalidatedRecommendationError()
        return self.compiler.compile(result.request, result.recommendation)

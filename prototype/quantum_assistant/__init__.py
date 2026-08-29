"""LLM-assisted quantum compilation prototype."""

from .controller import PrototypeController
from .factory import build_default_service
from .errors import RequestValidationError
from .models import (
    ApprovedCompilation,
    CircuitInput,
    CompatibilityReport,
    CompatibilityView,
    CompilationArtifact,
    DeviceExclusionDiagnostic,
    DeviceExclusionReason,
    DeviceQubitRange,
    HardwareCatalogSnapshot,
    HardwareConstraints,
    HardwareMaskResult,
    NormalizedRequest,
    PreparedRequestContext,
    Recommendation,
    RecommendationResult,
    UiSubmission,
    UserRequest,
    ValidationIssue,
    ValidationReport,
)
from .services import (
    ConfirmationRequiredError,
    LlmValidationExhaustedError,
    NoCompatibleHardwareError,
    NoEligibleDeviceError,
    PrototypeService,
)

__all__ = [
    "ApprovedCompilation",
    "CircuitInput",
    "CompatibilityReport",
    "CompatibilityView",
    "CompilationArtifact",
    "ConfirmationRequiredError",
    "DeviceExclusionDiagnostic",
    "DeviceExclusionReason",
    "DeviceQubitRange",
    "HardwareCatalogSnapshot",
    "HardwareConstraints",
    "HardwareMaskResult",
    "LlmValidationExhaustedError",
    "NoCompatibleHardwareError",
    "NoEligibleDeviceError",
    "NormalizedRequest",
    "PreparedRequestContext",
    "PrototypeController",
    "PrototypeService",
    "Recommendation",
    "RecommendationResult",
    "RequestValidationError",
    "UiSubmission",
    "UserRequest",
    "ValidationIssue",
    "ValidationReport",
    "build_default_service",
]

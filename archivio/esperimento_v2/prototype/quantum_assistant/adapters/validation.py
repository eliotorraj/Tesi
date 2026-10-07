'Read and check LLM recommendations deterministically.'

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from qiskit_dataset.catalog import V2_CATALOG_PATH, ConfigurationCatalog, load_catalog

from ..models import (
    ClaimParameters,
    CompatibilityView,
    EvidenceReference,
    EvidenceRegistry,
    EvidenceSourceType,
    HardwareCatalogSnapshot,
    HistoricalClaimType,
    LLM_RECOMMENDATION_SCHEMA_VERSION,
    LlmOutput,
    NormalizedRequest,
    QiskitCompilationPlan,
    Recommendation,
    SupportedClaim,
    SupportedClaimType,
    ValidationIssue,
    ValidationResult,
)
from ..ports import ExplanationRenderer
from .explanations import DeterministicExplanationRenderer
from ..schema_validation import (
    decode_json_object,
    load_schema,
    validate_instance,
)


LLM_RECOMMENDATION_SCHEMA = load_schema("llm_recommendation.schema.json")
if (
    LLM_RECOMMENDATION_SCHEMA["properties"]["schema_version"]["const"]
    != LLM_RECOMMENDATION_SCHEMA_VERSION
):
    raise ValueError('Inconsistent recommendation schema version.')
MAX_LLM_OUTPUT_BYTES = 65_536
MAX_FEEDBACK_ISSUES = 12


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    'Create a validation issue with stable code and location.'
    return ValidationIssue(code=code, path=path, message=message)


def _bounded_issues(
    issues: tuple[ValidationIssue, ...] | list[ValidationIssue],
) -> tuple[ValidationIssue, ...]:
    'Limit returned issues while indicating how many remain.'
    values = tuple(issues)
    if len(values) <= MAX_FEEDBACK_ISSUES:
        return values
    retained = values[: MAX_FEEDBACK_ISSUES - 1]
    return retained + (
        _issue(
            "LLM_OUTPUT_ISSUES_TRUNCATED",
            "$",
            (
                f'Omitted issues: {len(values) - len(retained)} additional errors.'
            ),
        ),
    )


def _invalid(
    issues: tuple[ValidationIssue, ...] | list[ValidationIssue],
) -> ValidationResult:
    'Build an invalid outcome with a bounded issue list.'
    return ValidationResult(is_valid=False, issues=_bounded_issues(issues))


def _decode_output(raw_response: LlmOutput) -> Mapping[str, Any] | ValidationResult:
    'Extract one JSON object or describe the format error.'
    if isinstance(raw_response, Mapping):
        return raw_response
    if not isinstance(raw_response, (str, bytes)):
        raise TypeError(
            'The LLM gateway must return JSON text, UTF-8 bytes or an already decoded JSON object.'
        )
    try:
        return decode_json_object(
            raw_response,
            max_bytes=MAX_LLM_OUTPUT_BYTES,
        )
    except ValueError:
        return _invalid(
            (
                _issue(
                    "LLM_OUTPUT_JSON_INVALID",
                    "$",
                    (
                        'The response must contain one valid JSON object without additional text or Markdown blocks.'
                    ),
                ),
            )
        )


class StructuredRecommendationValidator:
    'Check every response value that can affect compilation.'

    def __init__(
        self,
        *,
        configuration_catalog: ConfigurationCatalog | None = None,
        explanation_renderer: ExplanationRenderer | None = None,
    ) -> None:
        'Configure the catalog and final explanation builder.'
        self._configuration_catalog = (
            load_catalog(V2_CATALOG_PATH)
            if configuration_catalog is None
            else configuration_catalog
        )
        self._explanation_renderer = (
            DeterministicExplanationRenderer()
            if explanation_renderer is None
            else explanation_renderer
        )

    def _validate_context(
        self,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        catalog: HardwareCatalogSnapshot | None,
    ) -> None:
        'Verify that request, mask and catalogs use the same data.'
        if catalog is None:
            return
        if request.catalog_snapshot_id != catalog.catalog_snapshot_id:
            raise RuntimeError(
                'The normalized request and hardware catalog belong to different snapshots.'
            )
        mask_snapshot_id = getattr(
            compatibility,
            "catalog_snapshot_id",
            catalog.catalog_snapshot_id,
        )
        if mask_snapshot_id != catalog.catalog_snapshot_id:
            raise RuntimeError(
                'The mask and hardware catalog belong to different snapshots.'
            )
        if (
            self._configuration_catalog.catalog_id
            != catalog.configuration_catalog_id
        ):
            raise RuntimeError(
                'The configuration catalog differs from the one recorded in the hardware snapshot.'
            )
        configuration_ids = tuple(
            configuration.config_id
            for configuration in self._configuration_catalog.configurations
        )
        if configuration_ids != catalog.qiskit_configuration_ids:
            raise RuntimeError(
                'Loaded configurations differ from the hardware snapshot.'
            )

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
        'Validate response structure, content, claims and evidence.'
        self._validate_context(request, compatibility, catalog)
        if citation_context is not None:
            return self._validate_minimal(raw_response, request, compatibility, catalog,
                                          evidence_registry, citation_context)

        decoded = _decode_output(raw_response)
        if isinstance(decoded, ValidationResult):
            return decoded

        schema_issues = validate_instance(
            LLM_RECOMMENDATION_SCHEMA,
            decoded,
            error_code="LLM_OUTPUT_SCHEMA_INVALID",
        )
        if schema_issues:
            return _invalid(schema_issues)

        issues: list[ValidationIssue] = []
        if decoded["request_id"] != request.request_id:
            issues.append(
                _issue(
                    "LLM_OUTPUT_REQUEST_MISMATCH",
                    "$.request_id",
                    'The response does not belong to the current request.',
                )
            )
        if decoded["catalog_snapshot_id"] != request.catalog_snapshot_id:
            issues.append(
                _issue(
                    "LLM_OUTPUT_CATALOG_MISMATCH",
                    "$.catalog_snapshot_id",
                    'The response does not use the current hardware snapshot.',
                )
            )
        if decoded["figure_of_merit"] != request.figure_of_merit:
            issues.append(
                _issue(
                    "LLM_OUTPUT_METRIC_MISMATCH",
                    "$.figure_of_merit",
                    'The response uses a different metric from the requested one.',
                )
            )

        selected_device = decoded["selected_device"]
        selected_profile = (
            catalog.device_by_id.get(selected_device)
            if catalog is not None
            else next(
                (
                    profile
                    for profile in compatibility.available
                    if profile.device_id == selected_device
                ),
                None,
            )
        )
        if catalog is not None and selected_profile is None:
            issues.append(
                _issue(
                    "LLM_OUTPUT_UNKNOWN_DEVICE",
                    "$.selected_device",
                    'The specified device is absent from the current catalog.',
                )
            )
        elif selected_device not in compatibility.available_device_ids:
            issues.append(
                _issue(
                    "LLM_OUTPUT_DEVICE_NOT_ELIGIBLE",
                    "$.selected_device",
                    (
                        'The specified device is unavailable for the current request.'
                    ),
                )
            )

        raw_plan = decoded["qiskit_plan"]
        configuration = self._configuration_catalog.find(
            raw_plan["optimization_level"],
            raw_plan["layout_method"],
            raw_plan["routing_method"],
        )
        if configuration is None:
            issues.append(
                _issue(
                    "LLM_OUTPUT_CONFIGURATION_NOT_ALLOWED",
                    "$.qiskit_plan",
                    (
                        'The configuration is outside the 12 allowed Qiskit configurations.'
                    ),
                )
            )
        elif (
            selected_profile is not None
            and configuration.config_id
            not in selected_profile.allowed_qiskit_configuration_ids
        ):
            issues.append(
                _issue(
                    "LLM_OUTPUT_CONFIGURATION_NOT_SUPPORTED_BY_DEVICE",
                    "$.qiskit_plan",
                    (
                        'The selected device does not support the configuration.'
                    ),
                )
            )

        if (
            selected_profile is not None
            and request.figure_of_merit
            not in selected_profile.supported_figure_of_merit_ids
        ):
            issues.append(
                _issue(
                    "LLM_OUTPUT_METRIC_NOT_SUPPORTED_BY_DEVICE",
                    "$.figure_of_merit",
                    'The device does not support the requested metric.',
                )
            )

        evidence_references = tuple(
            EvidenceReference(
                reference_id=item["reference_id"],
                record_id=item["record_id"],
                source_type=EvidenceSourceType(item["source_type"]),
                source_id=item["source_id"],
                source_claim_id=item.get("source_claim_id"),
            )
            for item in decoded["evidence_refs"]
        )
        claims = tuple(
            SupportedClaim(
                claim_id=item["claim_id"],
                claim_type=SupportedClaimType(item["claim_type"]),
                parameters=ClaimParameters(
                    device_id=item["parameters"].get("device_id"),
                    configuration_id=item["parameters"].get(
                        "configuration_id"
                    ),
                    caveat_id=item["parameters"].get("caveat_id"),
                ),
                evidence_ref_ids=tuple(item["evidence_ref_ids"]),
            )
            for item in decoded["claims"]
        )

        reference_positions: dict[str, int] = {}
        source_positions: dict[tuple[str, str, str, str | None], int] = {}
        resolved_records = {}
        resolved_claims = {}
        for index, reference in enumerate(evidence_references):
            path = f"$.evidence_refs[{index}]"
            if reference.reference_id in reference_positions:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_REFERENCE_ID_DUPLICATE",
                        f"{path}.reference_id",
                        'Every reference must have a unique ID.',
                    )
                )
            else:
                reference_positions[reference.reference_id] = index

            source_key = (
                reference.record_id,
                reference.source_type.value,
                reference.source_id,
                reference.source_claim_id,
            )
            if source_key in source_positions:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_SOURCE_DUPLICATE",
                        path,
                        'The same historical source cannot be declared twice.',
                    )
                )
            else:
                source_positions[source_key] = index

            record = evidence_registry.find_record(reference.record_id)
            if record is None:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_RECORD_UNKNOWN",
                        f"{path}.record_id",
                        (
                            'The record is not among the closest circuits retrieved for this request.'
                        ),
                    )
                )
                continue
            resolved_records[reference.reference_id] = record

            if (
                reference.source_type
                is EvidenceSourceType.HISTORICAL_RESULT
            ):
                if reference.source_claim_id is None:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_SOURCE_CLAIM_REQUIRED",
                            f"{path}.source_claim_id",
                            (
                                'A historical result must identify a source claim from the same record.'
                            ),
                        )
                    )
                    continue
                source_claim = record.find_claim(reference.source_claim_id)
                if source_claim is None:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_SOURCE_CLAIM_UNKNOWN",
                            f"{path}.source_claim_id",
                            (
                                'The source claim does not belong to the specified historical record.'
                            ),
                        )
                    )
                    continue
                resolved_claims[reference.reference_id] = source_claim
                if record.find_evidence(reference.source_id) is None:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_EVIDENCE_UNKNOWN",
                            f"{path}.source_id",
                            (
                                'The evidence does not belong to the specified historical record.'
                            ),
                        )
                    )
                elif reference.source_id not in source_claim.evidence_ids:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_EVIDENCE_LINK_MISMATCH",
                            path,
                            (
                                'The source claim is not linked to the specified evidence.'
                            ),
                        )
                    )
            else:
                if reference.source_claim_id is not None:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_SOURCE_CLAIM_FORBIDDEN",
                            f"{path}.source_claim_id",
                            (
                                'A scientific caveat must not declare a source claim.'
                            ),
                        )
                    )
                if record.find_caveat(reference.source_id) is None:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CAVEAT_UNKNOWN",
                            f"{path}.source_id",
                            (
                                'The caveat does not belong to the specified historical record.'
                            ),
                        )
                    )

        claim_ids: set[str] = set()
        reference_usage = {
            reference_id: 0 for reference_id in reference_positions
        }
        references_by_id = {
            reference_id: evidence_references[index]
            for reference_id, index in reference_positions.items()
        }
        historical_claim_links: set[tuple[str, str]] = set()
        for claim in claims:
            if claim.claim_type not in (
                SupportedClaimType.HISTORICAL_DEVICE_SUPPORT,
                SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT,
            ):
                continue
            for reference_id in claim.evidence_ref_ids:
                reference = references_by_id.get(reference_id)
                if (
                    reference is not None
                    and reference.source_type
                    is EvidenceSourceType.HISTORICAL_RESULT
                    and reference.source_claim_id is not None
                ):
                    historical_claim_links.add(
                        (reference.record_id, reference.source_claim_id)
                    )

        expected_parameters = {
            SupportedClaimType.HISTORICAL_DEVICE_SUPPORT: {"device_id"},
            SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT: {
                "device_id",
                "configuration_id",
            },
            SupportedClaimType.LIVE_COMPATIBILITY: {"device_id"},
            SupportedClaimType.SCIENTIFIC_CAVEAT: {"caveat_id"},
            SupportedClaimType.HISTORICAL_EVIDENCE_UNAVAILABLE: set(),
        }
        for index, (raw_claim, claim) in enumerate(
            zip(decoded["claims"], claims, strict=True)
        ):
            path = f"$.claims[{index}]"
            if claim.claim_id in claim_ids:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_CLAIM_ID_DUPLICATE",
                        f"{path}.claim_id",
                        'Every claim must have a unique ID.',
                    )
                )
            claim_ids.add(claim.claim_id)

            actual_parameters = set(raw_claim["parameters"])
            if actual_parameters != expected_parameters[claim.claim_type]:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_CLAIM_PARAMETERS_INVALID",
                        f"{path}.parameters",
                        (
                            'Parameters do not match the declared claim type.'
                        ),
                    )
                )

            claim_references: list[EvidenceReference] = []
            for reference_index, reference_id in enumerate(
                claim.evidence_ref_ids
            ):
                reference = references_by_id.get(reference_id)
                if reference is None:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_EVIDENCE_REFERENCE_UNKNOWN",
                            (
                                f"{path}.evidence_ref_ids"
                                f"[{reference_index}]"
                            ),
                            (
                                'The claim cites a reference not declared in the response.'
                            ),
                        )
                    )
                    continue
                reference_usage[reference_id] += 1
                claim_references.append(reference)

            if claim.claim_type in (
                SupportedClaimType.HISTORICAL_DEVICE_SUPPORT,
                SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT,
            ):
                cited_by_source_claim: dict[
                    tuple[str, str], set[str]
                ] = {}
                for reference in claim_references:
                    if (
                        reference.source_type
                        is EvidenceSourceType.HISTORICAL_RESULT
                        and reference.source_claim_id is not None
                        and reference.reference_id in resolved_claims
                    ):
                        cited_by_source_claim.setdefault(
                            (
                                reference.record_id,
                                reference.source_claim_id,
                            ),
                            set(),
                        ).add(reference.source_id)
                for source_key, cited_ids in cited_by_source_claim.items():
                    source_reference = next(
                        reference
                        for reference in claim_references
                        if (
                            reference.record_id,
                            reference.source_claim_id,
                        )
                        == source_key
                    )
                    source_claim = resolved_claims[
                        source_reference.reference_id
                    ]
                    if cited_ids != set(source_claim.evidence_ids):
                        issues.append(
                            _issue(
                                "LLM_OUTPUT_SOURCE_EVIDENCE_SET_MISMATCH",
                                f"{path}.evidence_ref_ids",
                                (
                                    "A historical claim must cite all and only its source claim's evidence."
                                ),
                            )
                        )

            if (
                claim.claim_type
                is SupportedClaimType.HISTORICAL_DEVICE_SUPPORT
            ):
                if not claim_references:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_HISTORICAL_EVIDENCE_REQUIRED",
                            f"{path}.evidence_ref_ids",
                            (
                                'Historical device support requires at least one piece of evidence.'
                            ),
                        )
                    )
                if claim.parameters.device_id != selected_device:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CLAIM_DEVICE_MISMATCH",
                            f"{path}.parameters.device_id",
                            (
                                'The claim must concern the recommended device.'
                            ),
                        )
                    )
                for reference in claim_references:
                    record = resolved_records.get(reference.reference_id)
                    source_claim = resolved_claims.get(
                        reference.reference_id
                    )
                    if (
                        reference.source_type
                        is not EvidenceSourceType.HISTORICAL_RESULT
                        or record is None
                        or source_claim is None
                        or source_claim.claim_type
                        is not HistoricalClaimType.SELECTED_DEVICE
                        or record.selected_device_id != selected_device
                    ):
                        issues.append(
                            _issue(
                                "LLM_OUTPUT_DEVICE_EVIDENCE_MISMATCH",
                                path,
                                (
                                    'The reference does not support the historical selection of the recommended device.'
                                ),
                            )
                        )

            elif (
                claim.claim_type
                is SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT
            ):
                if not claim_references:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_HISTORICAL_EVIDENCE_REQUIRED",
                            f"{path}.evidence_ref_ids",
                            (
                                'Historical configuration support requires at least one piece of evidence.'
                            ),
                        )
                    )
                expected_configuration_id = (
                    configuration.config_id
                    if configuration is not None
                    else None
                )
                if (
                    claim.parameters.device_id != selected_device
                    or claim.parameters.configuration_id
                    != expected_configuration_id
                ):
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CONFIGURATION_CLAIM_MISMATCH",
                            f"{path}.parameters",
                            (
                                'The claim must concern the recommended device and configuration.'
                            ),
                        )
                    )
                for reference in claim_references:
                    record = resolved_records.get(reference.reference_id)
                    source_claim = resolved_claims.get(
                        reference.reference_id
                    )
                    historical_configuration = (
                        record.find_configuration(
                            claim.parameters.configuration_id or "",
                            device_id=selected_device,
                        )
                        if record is not None
                        else None
                    )
                    if (
                        reference.source_type
                        is not EvidenceSourceType.HISTORICAL_RESULT
                        or record is None
                        or source_claim is None
                        or source_claim.claim_type
                        is not HistoricalClaimType.RANKED_CONFIGURATION
                        or historical_configuration is None
                        or historical_configuration.claim_id
                        != reference.source_claim_id
                        or historical_configuration.evidence_id
                        != reference.source_id
                    ):
                        issues.append(
                            _issue(
                                "LLM_OUTPUT_CONFIGURATION_EVIDENCE_MISMATCH",
                                path,
                                (
                                    'The reference does not support the recommended configuration.'
                                ),
                            )
                        )

            elif claim.claim_type is SupportedClaimType.LIVE_COMPATIBILITY:
                if claim.evidence_ref_ids:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_LIVE_CLAIM_HAS_EVIDENCE",
                            f"{path}.evidence_ref_ids",
                            (
                                'Current compatibility is checked by the prototype without historical evidence.'
                            ),
                        )
                    )
                if claim.parameters.device_id != selected_device:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CLAIM_DEVICE_MISMATCH",
                            f"{path}.parameters.device_id",
                            (
                                'The claim must concern the recommended device.'
                            ),
                        )
                    )

            elif claim.claim_type is SupportedClaimType.SCIENTIFIC_CAVEAT:
                if not claim_references:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CAVEAT_EVIDENCE_REQUIRED",
                            f"{path}.evidence_ref_ids",
                            (
                                'The caveat must cite at least one scientific source from the registry.'
                            ),
                        )
                    )
                for reference in claim_references:
                    record = resolved_records.get(reference.reference_id)
                    caveat_id = claim.parameters.caveat_id
                    linked = (
                        record is not None
                        and caveat_id == reference.source_id
                        and reference.source_type
                        is EvidenceSourceType.SCIENTIFIC_CAVEAT
                        and any(
                            (
                                record.record_id,
                                source_claim.claim_id,
                            )
                            in historical_claim_links
                            and caveat_id in source_claim.caveat_ids
                            for source_claim in record.source_claims
                        )
                    )
                    if not linked:
                        issues.append(
                            _issue(
                                "LLM_OUTPUT_CAVEAT_EVIDENCE_MISMATCH",
                                path,
                                (
                                    'The caveat is not linked to a historical claim used in the recommendation.'
                                ),
                            )
                        )

            elif (
                claim.claim_type
                is SupportedClaimType.HISTORICAL_EVIDENCE_UNAVAILABLE
                and claim.evidence_ref_ids
            ):
                issues.append(
                    _issue(
                        "LLM_OUTPUT_UNAVAILABLE_CLAIM_HAS_EVIDENCE",
                        f"{path}.evidence_ref_ids",
                        (
                            'An absence-of-historical-evidence claim cannot cite references.'
                        ),
                    )
                )

        for reference_id, count in reference_usage.items():
            reference_index = reference_positions[reference_id]
            if count == 0:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_REFERENCE_UNUSED",
                        f"$.evidence_refs[{reference_index}]",
                        (
                            'Every declared reference must be used by a claim.'
                        ),
                    )
                )
            elif count > 1:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_REFERENCE_REUSED",
                        f"$.evidence_refs[{reference_index}]",
                        (
                            'Each declared reference may support only one claim.'
                        ),
                    )
                )

        claim_types = tuple(claim.claim_type for claim in claims)
        live_claim_count = claim_types.count(
            SupportedClaimType.LIVE_COMPATIBILITY
        )
        if live_claim_count != 1:
            issues.append(
                _issue(
                    "LLM_OUTPUT_LIVE_COMPATIBILITY_REQUIRED",
                    "$.claims",
                    (
                        'Exactly one verified-compatibility claim is required for the current request.'
                    ),
                )
            )

        unavailable_count = claim_types.count(
            SupportedClaimType.HISTORICAL_EVIDENCE_UNAVAILABLE
        )
        if evidence_registry.records:
            if unavailable_count:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_UNAVAILABLE_CONTRADICTED",
                        "$.claims",
                        (
                            'Historical results for the closest circuits are available; do not claim they are absent.'
                        ),
                    )
                )
            device_support_count = claim_types.count(
                SupportedClaimType.HISTORICAL_DEVICE_SUPPORT
            )
            configuration_support_count = claim_types.count(
                SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT
            )
            if (
                device_support_count != 1
                or configuration_support_count != 1
            ):
                issues.append(
                    _issue(
                        "LLM_OUTPUT_HISTORICAL_SUPPORT_INCOMPLETE",
                        "$.claims",
                        (
                            'Exactly one historical device claim and one historical configuration claim are required.'
                        ),
                    )
                )
        else:
            if evidence_references:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_NOT_AVAILABLE",
                        "$.evidence_refs",
                        (
                            'Retrieved circuits provide no citable historical results.'
                        ),
                    )
                )
            forbidden_claims = {
                SupportedClaimType.HISTORICAL_DEVICE_SUPPORT,
                SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT,
                SupportedClaimType.SCIENTIFIC_CAVEAT,
            }
            if unavailable_count != 1 or any(
                claim_type in forbidden_claims for claim_type in claim_types
            ):
                issues.append(
                    _issue(
                        "LLM_OUTPUT_NO_HISTORY_CLAIMS_INVALID",
                        "$.claims",
                        (
                            'Without historical results, only compatibility and unavailability claims are required.'
                        ),
                    )
                )

        if issues:
            return _invalid(issues)

        rendered = self._explanation_renderer.render(
            claims,
            evidence_references,
            evidence_registry,
        )
        return ValidationResult(
            is_valid=True,
            recommendation=Recommendation(
                selected_device=selected_device,
                figure_of_merit=decoded["figure_of_merit"],
                qiskit_plan=QiskitCompilationPlan(
                    optimization_level=raw_plan["optimization_level"],
                    seed_transpiler=raw_plan["seed_transpiler"],
                    layout_method=raw_plan["layout_method"],
                    routing_method=raw_plan["routing_method"],
                ),
                explanation=rendered.explanation,
                evidence=rendered.evidence,
                warnings=rendered.warnings,
                claims=claims,
                evidence_references=evidence_references,
            ),
        )

    def _validate_minimal(self, raw_response, request, compatibility, catalog, registry, context):
        'Check the choice and citation provenance, not the truth of free text.'
        from prototype.prompting.minimal import CitationContext, SCHEMA, CONTRACT_VERSION, digest
        from ..models import ExampleCitation
        if not isinstance(context, CitationContext):
            raise RuntimeError('Citation context is missing or invalid.')
        registry_ids = tuple(record.record_id for record in registry.records)
        if (context.request_id != request.request_id
                or context.catalog_snapshot_id != request.catalog_snapshot_id
                or context.request_sha256 != digest({
                    "qasm2": request.qasm2, "figure_of_merit": request.figure_of_merit,
                    "constraints": request.constraints, "features": dict(request.features)})
                or context.registry_sha256 != digest(registry.to_dict())
                or len(context.record_ids) > 5
                or len(context.record_ids) != len(set(context.record_ids))
                or tuple(r for r in context.record_ids if r in registry_ids) != registry_ids):
            raise RuntimeError('Citation context does not belong to the request or registry.')
        decoded = _decode_output(raw_response)
        if isinstance(decoded, ValidationResult):
            return decoded
        issues = list(validate_instance(SCHEMA, decoded, error_code="LLM_OUTPUT_SCHEMA_INVALID"))
        if issues:
            return _invalid(issues)
        if not decoded["claim"].strip():
            return _invalid([_issue("LLM_OUTPUT_CLAIM_EMPTY", "$.claim",
                                    'Write a non-empty explanation.')])
        device_id = decoded["selected_device"]
        profile = next((p for p in compatibility.available if p.device_id == device_id), None)
        if profile is None:
            issues.append(_issue("LLM_OUTPUT_DEVICE_NOT_ELIGIBLE", "$.selected_device",
                                 'Choose a compatible device.'))
        elif request.figure_of_merit not in profile.supported_figure_of_merit_ids:
            issues.append(_issue("LLM_OUTPUT_METRIC_NOT_SUPPORTED_BY_DEVICE", "$.selected_device",
                                 'The device does not support the requested metric.'))
        configuration = self._configuration_catalog.by_id.get(decoded["config_id"])
        if configuration is None:
            issues.append(_issue("LLM_OUTPUT_CONFIGURATION_NOT_ALLOWED", "$.config_id",
                                 'Choose a catalog configuration.'))
        elif profile is not None and configuration.config_id not in profile.allowed_qiskit_configuration_ids:
            issues.append(_issue("LLM_OUTPUT_CONFIGURATION_NOT_SUPPORTED_BY_DEVICE", "$.config_id",
                                 'The configuration is not allowed for the device.'))
        citations = []
        for index, alias in enumerate(decoded["evidence"]):
            record_id = context.aliases.get(alias)
            if record_id not in registry_ids:
                issues.append(_issue("LLM_OUTPUT_UNKNOWN_EXAMPLE", f"$.evidence[{index}]",
                                     'Cite only a supplied historical example.'))
            else:
                citations.append(ExampleCitation(alias=alias, record_id=record_id))
        if registry_ids and not decoded["evidence"]:
            issues.append(_issue("LLM_OUTPUT_EVIDENCE_REQUIRED", "$.evidence",
                                 'Cite at least one supplied historical example.'))
        if not registry_ids and decoded["evidence"]:
            issues.append(_issue("LLM_OUTPUT_EVIDENCE_NOT_AVAILABLE", "$.evidence",
                                 'Without historical examples, evidence must be empty.'))
        if issues:
            return _invalid(issues)
        return ValidationResult(is_valid=True, recommendation=Recommendation(
            selected_device=device_id, figure_of_merit=request.figure_of_merit,
            qiskit_plan=QiskitCompilationPlan(
                optimization_level=configuration.optimization_level,
                seed_transpiler=self._configuration_catalog.seeds[0],
                layout_method=configuration.layout_method,
                routing_method=configuration.routing_method),
            explanation=decoded["claim"], claim=decoded["claim"],
            evidence=tuple(c.alias for c in citations),
            example_citations=tuple(citations), config_id=configuration.config_id,
            schema_version=CONTRACT_VERSION,
            citation_validation="provided_examples_resolved",
            warnings=(
                'Citations point to the supplied examples. The explanation text is not verified semantically.',
                'Expected fidelity is an estimate on synthetic Targets, not a physical-hardware measurement.',
            )))

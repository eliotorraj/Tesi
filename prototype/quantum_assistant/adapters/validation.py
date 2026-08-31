"""Legge e controlla in modo deterministico le raccomandazioni dell'LLM."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from qiskit_dataset.catalog import ConfigurationCatalog, load_catalog

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
    raise ValueError("Versione dello schema della raccomandazione incoerente.")
MAX_LLM_OUTPUT_BYTES = 65_536
MAX_FEEDBACK_ISSUES = 12


def _issue(code: str, path: str, message: str) -> ValidationIssue:
    """Crea un problema di validazione con codice e posizione stabili."""
    return ValidationIssue(code=code, path=path, message=message)


def _bounded_issues(
    issues: tuple[ValidationIssue, ...] | list[ValidationIssue],
) -> tuple[ValidationIssue, ...]:
    """Limita i problemi restituiti senza perdere l'indicazione dei rimanenti."""
    values = tuple(issues)
    if len(values) <= MAX_FEEDBACK_ISSUES:
        return values
    retained = values[: MAX_FEEDBACK_ISSUES - 1]
    return retained + (
        _issue(
            "LLM_OUTPUT_ISSUES_TRUNCATED",
            "$",
            (
                "Sono stati omessi "
                f"{len(values) - len(retained)} errori aggiuntivi."
            ),
        ),
    )


def _invalid(
    issues: tuple[ValidationIssue, ...] | list[ValidationIssue],
) -> ValidationResult:
    """Costruisce un esito non valido con un numero limitato di problemi."""
    return ValidationResult(is_valid=False, issues=_bounded_issues(issues))


def _decode_output(raw_response: LlmOutput) -> Mapping[str, Any] | ValidationResult:
    """Estrae un solo oggetto JSON oppure descrive l'errore di formato."""
    if isinstance(raw_response, Mapping):
        return raw_response
    if not isinstance(raw_response, (str, bytes)):
        raise TypeError(
            "Il collegamento LLM deve restituire testo JSON, byte UTF-8 "
            "oppure un oggetto JSON già decodificato."
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
                        "La risposta deve contenere un solo oggetto JSON valido, "
                        "senza testo o blocchi Markdown aggiuntivi."
                    ),
                ),
            )
        )


class StructuredRecommendationValidator:
    """Controlla ogni valore della risposta che può influire sulla compilazione."""

    def __init__(
        self,
        *,
        configuration_catalog: ConfigurationCatalog | None = None,
        explanation_renderer: ExplanationRenderer | None = None,
    ) -> None:
        """Configura il catalogo e il costruttore delle spiegazioni finali."""
        self._configuration_catalog = (
            load_catalog()
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
        """Verifica che richiesta, maschera e cataloghi usino gli stessi dati."""
        if catalog is None:
            return
        if request.catalog_snapshot_id != catalog.catalog_snapshot_id:
            raise RuntimeError(
                "La richiesta normalizzata e il catalogo hardware non "
                "appartengono alla stessa istantanea."
            )
        mask_snapshot_id = getattr(
            compatibility,
            "catalog_snapshot_id",
            catalog.catalog_snapshot_id,
        )
        if mask_snapshot_id != catalog.catalog_snapshot_id:
            raise RuntimeError(
                "La maschera e il catalogo hardware non appartengono alla "
                "stessa istantanea."
            )
        if (
            self._configuration_catalog.catalog_id
            != catalog.configuration_catalog_id
        ):
            raise RuntimeError(
                "Il catalogo delle configurazioni non coincide con quello "
                "registrato nell'istantanea hardware."
            )
        configuration_ids = tuple(
            configuration.config_id
            for configuration in self._configuration_catalog.configurations
        )
        if configuration_ids != catalog.qiskit_configuration_ids:
            raise RuntimeError(
                "Le configurazioni caricate non coincidono con l'istantanea "
                "hardware."
            )

    def validate(
        self,
        raw_response: LlmOutput,
        request: NormalizedRequest,
        compatibility: CompatibilityView,
        catalog: HardwareCatalogSnapshot | None = None,
        *,
        evidence_registry: EvidenceRegistry,
    ) -> ValidationResult:
        """Valida struttura, contenuto, claim ed evidenze della risposta."""
        self._validate_context(request, compatibility, catalog)

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
                    "La risposta non appartiene alla richiesta corrente.",
                )
            )
        if decoded["catalog_snapshot_id"] != request.catalog_snapshot_id:
            issues.append(
                _issue(
                    "LLM_OUTPUT_CATALOG_MISMATCH",
                    "$.catalog_snapshot_id",
                    "La risposta non usa l'istantanea hardware corrente.",
                )
            )
        if decoded["figure_of_merit"] != request.figure_of_merit:
            issues.append(
                _issue(
                    "LLM_OUTPUT_METRIC_MISMATCH",
                    "$.figure_of_merit",
                    "La risposta usa una misura diversa da quella richiesta.",
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
                    "Il dispositivo indicato non esiste nel catalogo corrente.",
                )
            )
        elif selected_device not in compatibility.available_device_ids:
            issues.append(
                _issue(
                    "LLM_OUTPUT_DEVICE_NOT_ELIGIBLE",
                    "$.selected_device",
                    (
                        "Il dispositivo indicato non è utilizzabile per la "
                        "richiesta corrente."
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
                        "La configurazione non appartiene alle 12 "
                        "configurazioni Qiskit ammesse."
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
                        "La configurazione non è supportata dal dispositivo "
                        "selezionato."
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
                    "Il dispositivo non supporta la misura richiesta.",
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
                        "Ogni riferimento deve avere un ID univoco.",
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
                        "La stessa fonte storica non può essere dichiarata due volte.",
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
                            "Il record non appartiene ai circuiti più simili "
                            "recuperati per questa richiesta."
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
                                "Un risultato storico deve indicare il claim "
                                "sorgente del medesimo record."
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
                                "Il claim sorgente non appartiene al record "
                                "storico indicato."
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
                                "L'evidenza non appartiene al record storico "
                                "indicato."
                            ),
                        )
                    )
                elif reference.source_id not in source_claim.evidence_ids:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_EVIDENCE_LINK_MISMATCH",
                            path,
                            (
                                "Il claim sorgente non è collegato "
                                "all'evidenza indicata."
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
                                "Un'avvertenza scientifica non deve dichiarare "
                                "un claim sorgente."
                            ),
                        )
                    )
                if record.find_caveat(reference.source_id) is None:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CAVEAT_UNKNOWN",
                            f"{path}.source_id",
                            (
                                "L'avvertenza non appartiene al record storico "
                                "indicato."
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
                        "Ogni claim deve avere un ID univoco.",
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
                            "I parametri non corrispondono al tipo di claim "
                            "dichiarato."
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
                                "Il claim cita un riferimento non dichiarato "
                                "nella risposta."
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
                                    "Un claim storico deve citare tutte e sole "
                                    "le evidenze del claim sorgente."
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
                                "Il sostegno storico del dispositivo richiede "
                                "almeno un'evidenza."
                            ),
                        )
                    )
                if claim.parameters.device_id != selected_device:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CLAIM_DEVICE_MISMATCH",
                            f"{path}.parameters.device_id",
                            (
                                "Il claim deve riguardare il dispositivo "
                                "raccomandato."
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
                                    "Il riferimento non sostiene la scelta "
                                    "storica del dispositivo raccomandato."
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
                                "Il sostegno storico della configurazione "
                                "richiede almeno un'evidenza."
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
                                "Il claim deve riguardare il dispositivo e la "
                                "configurazione raccomandati."
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
                                    "Il riferimento non sostiene la "
                                    "configurazione raccomandata."
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
                                "La compatibilità corrente è verificata dal "
                                "prototipo e non usa evidenze storiche."
                            ),
                        )
                    )
                if claim.parameters.device_id != selected_device:
                    issues.append(
                        _issue(
                            "LLM_OUTPUT_CLAIM_DEVICE_MISMATCH",
                            f"{path}.parameters.device_id",
                            (
                                "Il claim deve riguardare il dispositivo "
                                "raccomandato."
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
                                "L'avvertenza deve citare almeno una fonte "
                                "scientifica del registro."
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
                                    "L'avvertenza non è collegata a un claim "
                                    "storico usato nella raccomandazione."
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
                            "L'assenza di evidenze storiche non può citare "
                            "riferimenti."
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
                            "Ogni riferimento dichiarato deve essere usato da "
                            "un claim."
                        ),
                    )
                )
            elif count > 1:
                issues.append(
                    _issue(
                        "LLM_OUTPUT_EVIDENCE_REFERENCE_REUSED",
                        f"$.evidence_refs[{reference_index}]",
                        (
                            "Ogni riferimento dichiarato può sostenere un solo "
                            "claim."
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
                        "Serve un solo claim di compatibilità verificata per "
                        "la richiesta corrente."
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
                            "Sono disponibili risultati storici dei circuiti "
                            "più simili: non dichiararne l'assenza."
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
                            "Serve un solo claim storico per il dispositivo e "
                            "un solo claim storico per la configurazione."
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
                            "I circuiti recuperati non espongono risultati "
                            "storici citabili."
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
                            "Senza risultati storici servono soltanto il claim "
                            "di compatibilità e quello di indisponibilità."
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

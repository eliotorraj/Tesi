'Build deterministic explanations from validated content.'

from __future__ import annotations

from collections.abc import Sequence

from ..models import (
    ClaimParameters,
    EvidenceReference,
    EvidenceRegistry,
    EvidenceSourceType,
    HistoricalEvidence,
    RenderedExplanation,
    ScientificCaveat,
    SupportedClaim,
    SupportedClaimType,
)


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    'Remove duplicates while retaining first-occurrence order.'
    return tuple(dict.fromkeys(values))


def _required_parameter(
    parameters: ClaimParameters,
    field_name: str,
) -> str:
    'Read a required parameter from an already validated claim.'
    value = getattr(parameters, field_name)
    if value is None:
        raise ValueError(
            f'The validated claim requires parameter {field_name}.'
        )
    return value


class DeterministicExplanationRenderer:
    'Produce user-facing text without accepting free-form LLM prose.'

    def render(
        self,
        claims: Sequence[SupportedClaim],
        evidence_references: Sequence[EvidenceReference],
        evidence_registry: EvidenceRegistry,
    ) -> RenderedExplanation:
        'Convert validated claims and references into a readable explanation.'
        claim_values = tuple(claims)
        reference_values = tuple(evidence_references)
        if not claim_values:
            raise ValueError('At least one validated claim is required for display.')

        claim_ids = tuple(claim.claim_id for claim in claim_values)
        reference_ids = tuple(
            reference.reference_id for reference in reference_values
        )
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError('Validated claims must have unique IDs.')
        if len(reference_ids) != len(set(reference_ids)):
            raise ValueError('Validated references must have unique IDs.')

        references_by_id = {
            reference.reference_id: reference
            for reference in reference_values
        }
        resolved_sources = {}
        for reference in reference_values:
            source = evidence_registry.resolve(reference)
            if source is None:
                raise ValueError(
                    'A validated reference does not belong to the current registry.'
                )
            resolved_sources[reference.reference_id] = source

        claim_priority = {
            SupportedClaimType.HISTORICAL_DEVICE_SUPPORT: 0,
            SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT: 1,
            SupportedClaimType.LIVE_COMPATIBILITY: 2,
            SupportedClaimType.SCIENTIFIC_CAVEAT: 3,
            SupportedClaimType.HISTORICAL_EVIDENCE_UNAVAILABLE: 4,
        }

        def reference_key(reference: EvidenceReference) -> tuple[object, ...]:
            'Create the stable sort key for a reference.'
            record = evidence_registry.find_record(reference.record_id)
            rank = record.rank if record is not None else 10**9
            return (
                rank,
                reference.record_id,
                reference.source_type.value,
                reference.source_claim_id or "",
                reference.source_id,
            )

        def claim_key(claim: SupportedClaim) -> tuple[object, ...]:
            'Create the stable sort key for a claim.'
            source_keys = tuple(
                sorted(
                    reference_key(references_by_id[reference_id])
                    for reference_id in claim.evidence_ref_ids
                    if reference_id in references_by_id
                )
            )
            return (
                claim_priority[claim.claim_type],
                claim.parameters.device_id or "",
                claim.parameters.configuration_id or "",
                claim.parameters.caveat_id or "",
                source_keys,
            )

        claim_values = tuple(sorted(claim_values, key=claim_key))
        explanation_parts: list[str] = []
        evidence_lines: list[str] = []
        warnings: list[str] = []
        used_reference_ids: list[str] = []

        for claim in claim_values:
            try:
                claim_references = tuple(
                    sorted(
                        (
                            references_by_id[reference_id]
                            for reference_id in claim.evidence_ref_ids
                        ),
                        key=reference_key,
                    )
                )
            except KeyError as exc:
                raise ValueError(
                    'A validated claim cites a missing reference.'
                ) from exc
            used_reference_ids.extend(
                reference.reference_id for reference in claim_references
            )
            record_ids = _ordered_unique(
                tuple(reference.record_id for reference in claim_references)
            )
            rendered_records = ", ".join(record_ids)

            if (
                claim.claim_type
                is SupportedClaimType.HISTORICAL_DEVICE_SUPPORT
            ):
                device_id = _required_parameter(
                    claim.parameters,
                    "device_id",
                )
                explanation_parts.append(
                    f'Results for historical circuits {rendered_records} support selecting device {device_id}.'
                )
            elif (
                claim.claim_type
                is SupportedClaimType.HISTORICAL_CONFIGURATION_SUPPORT
            ):
                device_id = _required_parameter(
                    claim.parameters,
                    "device_id",
                )
                configuration_id = _required_parameter(
                    claim.parameters,
                    "configuration_id",
                )
                explanation_parts.append(
                    f'Results for historical circuits {rendered_records} support configuration {configuration_id} for device {device_id}.'
                )
            elif claim.claim_type is SupportedClaimType.LIVE_COMPATIBILITY:
                device_id = _required_parameter(
                    claim.parameters,
                    "device_id",
                )
                explanation_parts.append(
                    f'Device {device_id} satisfies the constraints checked for the current request.'
                )
            elif claim.claim_type is SupportedClaimType.SCIENTIFIC_CAVEAT:
                _required_parameter(claim.parameters, "caveat_id")
                explanation_parts.append(
                    'The recommendation accounts for scientific caveats associated with the historical evidence.'
                )
            elif (
                claim.claim_type
                is SupportedClaimType.HISTORICAL_EVIDENCE_UNAVAILABLE
            ):
                explanation_parts.append(
                    'No usable historical results among the closest retrieved circuits support the recommendation.'
                )
                warnings.append(
                    'The recommendation has no usable historical evidence.'
                )
            else:  # pragma: no cover - the enum is checked earlier.
                raise ValueError('Unsupported validated claim type.')

        if set(used_reference_ids) != set(reference_ids):
            raise ValueError(
                'Every validated reference must be used by a claim.'
            )

        rendered_source_ids: set[
            tuple[str, str, str, str | None]
        ] = set()
        has_historical_results = False
        for reference_id in used_reference_ids:
            reference = references_by_id[reference_id]
            source = resolved_sources[reference_id]
            source_key = (
                reference.record_id,
                reference.source_type.value,
                reference.source_id,
                reference.source_claim_id,
            )
            if source_key in rendered_source_ids:
                continue
            rendered_source_ids.add(source_key)

            if (
                reference.source_type
                is EvidenceSourceType.HISTORICAL_RESULT
            ):
                if not isinstance(source, HistoricalEvidence):
                    raise ValueError(
                        'The historical reference does not resolve to a result.'
                    )
                has_historical_results = True
                sample_text = (
                    f', samples={source.sample_count}'
                    if source.sample_count is not None
                    else ""
                )
                evidence_lines.append(
                    f'Historical circuit {reference.record_id}: device={source.device_id}, configuration={source.configuration_id}, median expected fidelity={source.value:.12g}{sample_text} (evidence {source.evidence_id}).'
                )
                record = evidence_registry.find_record(reference.record_id)
                source_claim = (
                    record.find_claim(reference.source_claim_id)
                    if record is not None
                    and reference.source_claim_id is not None
                    else None
                )
                if source_claim is None:
                    raise ValueError(
                        'The validated result does not retain the source claim.'
                    )
                for caveat_id in source_claim.caveat_ids:
                    caveat = record.find_caveat(caveat_id)
                    if caveat is None:
                        raise ValueError(
                            'The source claim cites a missing caveat.'
                        )
                    warnings.append(caveat.text)
            elif (
                reference.source_type
                is EvidenceSourceType.SCIENTIFIC_CAVEAT
            ):
                if not isinstance(source, ScientificCaveat):
                    raise ValueError(
                        'The scientific reference does not resolve to a caveat.'
                    )
                evidence_lines.append(
                    f'Historical circuit {reference.record_id}: caveat {source.caveat_id}.'
                )
                warnings.append(source.text)

        if has_historical_results:
            warnings.append(
                "The evidence concerns historical compilations of similar circuits and does not measure the current circuit's result."
            )

        return RenderedExplanation(
            explanation=" ".join(explanation_parts),
            evidence=_ordered_unique(tuple(evidence_lines)),
            warnings=_ordered_unique(tuple(warnings)),
        )

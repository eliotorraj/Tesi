"""Costruisce in modo deterministico le spiegazioni già validate."""

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
    """Rimuove i duplicati conservando l'ordine della prima occorrenza."""
    return tuple(dict.fromkeys(values))


def _required_parameter(
    parameters: ClaimParameters,
    field_name: str,
) -> str:
    """Legge un parametro obbligatorio da un claim già validato."""
    value = getattr(parameters, field_name)
    if value is None:
        raise ValueError(
            f"Il claim validato richiede il parametro {field_name}."
        )
    return value


class DeterministicExplanationRenderer:
    """Produce il testo per l'utente senza accettare prosa libera dall'LLM."""

    def render(
        self,
        claims: Sequence[SupportedClaim],
        evidence_references: Sequence[EvidenceReference],
        evidence_registry: EvidenceRegistry,
    ) -> RenderedExplanation:
        """Trasforma claim e riferimenti validati in una spiegazione leggibile."""
        claim_values = tuple(claims)
        reference_values = tuple(evidence_references)
        if not claim_values:
            raise ValueError("Serve almeno un claim validato da mostrare.")

        claim_ids = tuple(claim.claim_id for claim in claim_values)
        reference_ids = tuple(
            reference.reference_id for reference in reference_values
        )
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("I claim validati devono avere ID unici.")
        if len(reference_ids) != len(set(reference_ids)):
            raise ValueError("I riferimenti validati devono avere ID unici.")

        references_by_id = {
            reference.reference_id: reference
            for reference in reference_values
        }
        resolved_sources = {}
        for reference in reference_values:
            source = evidence_registry.resolve(reference)
            if source is None:
                raise ValueError(
                    "Un riferimento validato non appartiene al registro corrente."
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
            """Crea la chiave stabile usata per ordinare un riferimento."""
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
            """Crea la chiave stabile usata per ordinare un claim."""
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
                    "Un claim validato cita un riferimento assente."
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
                    "I risultati dei circuiti storici "
                    f"{rendered_records} sostengono la scelta del dispositivo "
                    f"{device_id}."
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
                    "I risultati dei circuiti storici "
                    f"{rendered_records} sostengono la configurazione "
                    f"{configuration_id} per il dispositivo {device_id}."
                )
            elif claim.claim_type is SupportedClaimType.LIVE_COMPATIBILITY:
                device_id = _required_parameter(
                    claim.parameters,
                    "device_id",
                )
                explanation_parts.append(
                    f"Il dispositivo {device_id} rispetta i vincoli "
                    "verificati per la richiesta corrente."
                )
            elif claim.claim_type is SupportedClaimType.SCIENTIFIC_CAVEAT:
                _required_parameter(claim.parameters, "caveat_id")
                explanation_parts.append(
                    "La raccomandazione tiene conto delle avvertenze "
                    "scientifiche associate alle evidenze storiche."
                )
            elif (
                claim.claim_type
                is SupportedClaimType.HISTORICAL_EVIDENCE_UNAVAILABLE
            ):
                explanation_parts.append(
                    "Tra i circuiti più simili recuperati non sono "
                    "disponibili risultati storici utilizzabili per sostenere "
                    "la raccomandazione."
                )
                warnings.append(
                    "La raccomandazione non dispone di evidenze storiche "
                    "utilizzabili."
                )
            else:  # pragma: no cover - l'enum viene controllata prima.
                raise ValueError("Tipo di claim validato non supportato.")

        if set(used_reference_ids) != set(reference_ids):
            raise ValueError(
                "Ogni riferimento validato deve essere usato da un claim."
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
                        "Il riferimento storico non risolve un risultato."
                    )
                has_historical_results = True
                sample_text = (
                    f", campioni={source.sample_count}"
                    if source.sample_count is not None
                    else ""
                )
                evidence_lines.append(
                    f"Circuito storico {reference.record_id}: "
                    f"dispositivo={source.device_id}, "
                    f"configurazione={source.configuration_id}, "
                    "mediana della fedeltà attesa="
                    f"{source.value:.12g}{sample_text} "
                    f"(evidenza {source.evidence_id})."
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
                        "Il risultato validato non conserva il claim sorgente."
                    )
                for caveat_id in source_claim.caveat_ids:
                    caveat = record.find_caveat(caveat_id)
                    if caveat is None:
                        raise ValueError(
                            "Il claim sorgente cita un'avvertenza assente."
                        )
                    warnings.append(caveat.text)
            elif (
                reference.source_type
                is EvidenceSourceType.SCIENTIFIC_CAVEAT
            ):
                if not isinstance(source, ScientificCaveat):
                    raise ValueError(
                        "Il riferimento scientifico non risolve "
                        "un'avvertenza."
                    )
                evidence_lines.append(
                    f"Circuito storico {reference.record_id}: "
                    f"avvertenza {source.caveat_id}."
                )
                warnings.append(source.text)

        if has_historical_results:
            warnings.append(
                "Le evidenze riguardano compilazioni storiche di circuiti "
                "simili e non misurano il risultato del circuito corrente."
            )

        return RenderedExplanation(
            explanation=" ".join(explanation_parts),
            evidence=_ordered_unique(tuple(evidence_lines)),
            warnings=_ordered_unique(tuple(warnings)),
        )

"""Recupera esempi sicuri dal Dataset e costruisce la richiesta per l'LLM."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Mapping

from qiskit_dataset.catalog import ConfigurationCatalog, load_catalog

from ..models import (
    CompatibilityView,
    EvidenceRecord,
    EvidenceRegistry,
    HistoricalClaim,
    HistoricalClaimType,
    HistoricalConfiguration,
    HistoricalEvidence,
    LLM_RECOMMENDATION_SCHEMA_VERSION,
    ParsedRequest,
    PromptEnvelope,
    RetrievedExample,
    ScientificCaveat,
    ValidationIssue,
)
from ..schema_validation import load_schema


LLM_RECOMMENDATION_SCHEMA = load_schema("llm_recommendation.schema.json")


def _json_ready(value: Any) -> Any:
    """Converte strutture immutabili in valori serializzabili come JSON."""
    if isinstance(value, Mapping):
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


def _feature_distance(
    query: Mapping[str, float],
    candidate: Mapping[str, Any],
) -> float | None:
    """Calcola la distanza media tra caratteristiche tenendo conto della scala."""
    if set(query) - set(candidate):
        return None
    distances: list[float] = []
    for name, query_value in query.items():
        try:
            candidate_value = float(candidate[name])
        except (TypeError, ValueError):
            return None
        if not math.isfinite(candidate_value):
            return None
        scale = 1.0 + max(abs(query_value), abs(candidate_value))
        distances.append(abs(query_value - candidate_value) / scale)
    return sum(distances) / len(distances) if distances else 0.0


def _compact_prompt_input(record_input: Mapping[str, Any]) -> dict[str, Any]:
    """Riduce un vecchio esempio ai soli dati utili per il confronto."""
    circuit = record_input.get("circuit") or {}
    features = circuit.get("features") or {}
    backends = record_input.get("compatible_backends") or []
    return {
        "objective": record_input.get("objective"),
        "circuit": {
            "name": circuit.get("name"),
            "summary": circuit.get("summary"),
            "features": {"by_name": features.get("by_name", {})},
        },
        "compatible_backends": [
            {
                "id": backend.get("id"),
                "num_qubits": backend.get("num_qubits"),
                "operation_names": backend.get("operation_names", []),
            }
            for backend in backends
            if isinstance(backend, dict)
        ],
        "user_constraints": record_input.get("user_constraints", {}),
    }


def _compact_rag_example(record: Mapping[str, Any]) -> dict[str, Any]:
    """Riduce un esempio RAG senza perdere claim ed evidenze necessarie."""
    retrieval_input = record.get("retrieval_input") or {}
    circuit = retrieval_input.get("circuit") or {}
    features = circuit.get("features") or {}
    compatible_devices = retrieval_input.get("compatible_devices") or []
    return {
        "rag_id": record.get("rag_id"),
        "view_scope": record.get("view_scope"),
        "objective": record.get("objective"),
        "input": {
            "circuit": {
                "circuit_id": circuit.get("circuit_id"),
                "benchmark_family": circuit.get("benchmark_family"),
                "generator": circuit.get("generator"),
                "num_qubits": circuit.get("num_qubits"),
                "depth": circuit.get("depth"),
                "size": circuit.get("size"),
                "source_sha256": circuit.get("source_sha256"),
                "features": {"values": features.get("values", {})},
            },
            "compatible_devices": [
                {
                    "device_id": device.get("device_id"),
                    "num_qubits": device.get("num_qubits"),
                    "operation_names": device.get("operation_names", []),
                    "target_sha256": device.get("target_sha256"),
                }
                for device in compatible_devices
                if isinstance(device, Mapping)
            ],
            "user_constraints": retrieval_input.get("user_constraints", {}),
        },
        "label": {
            "selected_device": record.get("selected_device"),
            "top_configurations": record.get("top_configurations", []),
        },
        "claims": record.get("claims", []),
        "evidence": record.get("evidence", []),
        "scientific_caveats": record.get("scientific_caveats", []),
    }


_RAG_REQUIRED_FIELDS = {
    "rag_id": str,
    "retrieval_input": Mapping,
    "objective": Mapping,
    "selected_device": Mapping,
    "top_configurations": (list, tuple),
    "claims": (list, tuple),
    "evidence": (list, tuple),
    "scientific_caveats": (list, tuple),
}


def _is_labeled_rag_record(record: Mapping[str, Any]) -> bool:
    """Riconosce un record che dichiara il formato RAG etichettato."""
    return "rag_id" in record or "retrieval_input" in record


def _validate_labeled_rag_envelope(record: Mapping[str, Any]) -> None:
    """Rifiuta un record RAG incompleto prima che possa essere ignorato."""
    record_id = str(record.get("rag_id", "<missing>"))
    for field_name, expected_type in _RAG_REQUIRED_FIELDS.items():
        value = record.get(field_name)
        if not isinstance(value, expected_type):
            raise EvidenceRegistryDataError(
                "Dataset RAG non valido "
                f"({record_id}, $.{field_name}): campo essenziale assente "
                "o di tipo errato."
            )
    if not record["rag_id"].strip():
        raise EvidenceRegistryDataError(
            "Dataset RAG non valido (<missing>, $.rag_id): ID non valido."
        )


class EvidenceRegistryDataError(ValueError):
    """Errore stabile per un record RAG incompleto o incoerente."""

    code = "EVIDENCE_REGISTRY_DATA_INVALID"
    retryable = False

    def to_dict(self) -> dict[str, object]:
        """Restituisce l'errore nel formato stabile esposto dall'applicazione."""
        return {
            "code": self.code,
            "retryable": self.retryable,
            "message": str(self),
        }


def _registry_mapping(
    value: Any,
    *,
    record_id: str,
    path: str,
) -> Mapping[str, Any]:
    """Richiede un oggetto nel campo indicato del record RAG."""
    if not isinstance(value, Mapping):
        raise EvidenceRegistryDataError(
            f"Dataset RAG non valido ({record_id}, {path}): oggetto atteso."
        )
    return value


def _registry_sequence(
    value: Any,
    *,
    record_id: str,
    path: str,
) -> Sequence[Any]:
    """Richiede una lista nel campo indicato del record RAG."""
    if not isinstance(value, (list, tuple)):
        raise EvidenceRegistryDataError(
            f"Dataset RAG non valido ({record_id}, {path}): lista attesa."
        )
    return value


def _registry_string(
    value: Any,
    *,
    record_id: str,
    path: str,
) -> str:
    """Richiede una stringa non vuota nel campo indicato del record RAG."""
    if not isinstance(value, str) or not value.strip():
        raise EvidenceRegistryDataError(
            f"Dataset RAG non valido ({record_id}, {path}): "
            "stringa non vuota attesa."
        )
    return value


def _registry_optional_string(
    value: Any,
    *,
    record_id: str,
    path: str,
) -> str | None:
    """Legge una stringa facoltativa dal campo indicato del record RAG."""
    if value is None:
        return None
    return _registry_string(value, record_id=record_id, path=path)


def _registry_integer(
    value: Any,
    *,
    record_id: str,
    path: str,
) -> int:
    """Richiede un numero intero nel campo indicato del record RAG."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvidenceRegistryDataError(
            f"Dataset RAG non valido ({record_id}, {path}): intero atteso."
        )
    return value


def _registry_number(
    value: Any,
    *,
    record_id: str,
    path: str,
) -> float:
    """Richiede un numero finito nel campo indicato del record RAG."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise EvidenceRegistryDataError(
            f"Dataset RAG non valido ({record_id}, {path}): numero finito atteso."
        )
    return float(value)


class StructuredEvidenceRegistryBuilder:
    """Costruisce il registro immutabile dai risultati storici recuperati."""

    def __init__(
        self,
        *,
        configuration_catalog: ConfigurationCatalog | None = None,
    ) -> None:
        """Configura il catalogo usato per controllare le evidenze storiche."""
        self._configuration_catalog = (
            load_catalog()
            if configuration_catalog is None
            else configuration_catalog
        )

    def build(
        self,
        examples: Sequence[RetrievedExample],
    ) -> EvidenceRegistry:
        """Costruisce il registro dai soli esempi RAG completi recuperati."""
        records: list[EvidenceRecord] = []
        for rank, example in enumerate(examples, start=1):
            payload = _registry_mapping(
                example.prompt_input,
                record_id=example.record_id,
                path="$",
            )
            evidence_keys = {
                "label",
                "claims",
                "evidence",
                "scientific_caveats",
            }
            present_keys = evidence_keys.intersection(payload)
            if not present_keys:
                if "rag_id" in payload or "retrieval_input" in payload:
                    missing = ", ".join(sorted(evidence_keys))
                    raise EvidenceRegistryDataError(
                        "Dataset RAG non valido "
                        f"({example.record_id}, $): campi mancanti: {missing}."
                    )
                # I vecchi record espongono solo l'ingresso e non possono
                # sostenere claim basati sui risultati storici.
                continue
            if present_keys != evidence_keys:
                missing = ", ".join(sorted(evidence_keys - present_keys))
                raise EvidenceRegistryDataError(
                    "Dataset RAG non valido "
                    f"({example.record_id}, $): campi mancanti: {missing}."
                )
            records.append(self._build_record(example, rank, payload))
        try:
            return EvidenceRegistry(records=tuple(records))
        except ValueError as error:
            raise EvidenceRegistryDataError(
                f"Registro delle evidenze del Dataset non valido: {error}"
            ) from error

    def _build_record(
        self,
        example: RetrievedExample,
        rank: int,
        payload: Mapping[str, Any],
    ) -> EvidenceRecord:
        """Converte un esempio recuperato in un record di evidenze controllato."""
        record_id = example.record_id
        embedded_record_id = _registry_string(
            payload.get("rag_id"),
            record_id=record_id,
            path="$.rag_id",
        )
        if embedded_record_id != record_id:
            raise EvidenceRegistryDataError(
                "Dataset RAG non valido "
                f"({record_id}, $.rag_id): ID diverso dal risultato recuperato."
            )

        label = _registry_mapping(
            payload.get("label"),
            record_id=record_id,
            path="$.label",
        )
        selected_device = _registry_mapping(
            label.get("selected_device"),
            record_id=record_id,
            path="$.label.selected_device",
        )
        selected_device_id = _registry_string(
            selected_device.get("device_id"),
            record_id=record_id,
            path="$.label.selected_device.device_id",
        )
        selected_best_summary_id = _registry_string(
            selected_device.get("best_summary_id"),
            record_id=record_id,
            path="$.label.selected_device.best_summary_id",
        )
        selected_best_configuration_id = _registry_string(
            selected_device.get("best_config_id"),
            record_id=record_id,
            path="$.label.selected_device.best_config_id",
        )
        selected_median_score = _registry_number(
            selected_device.get("median_score"),
            record_id=record_id,
            path="$.label.selected_device.median_score",
        )

        evidence = tuple(
            self._build_evidence(record_id, item, index)
            for index, item in enumerate(
                _registry_sequence(
                    payload.get("evidence"),
                    record_id=record_id,
                    path="$.evidence",
                )
            )
        )
        caveats = tuple(
            self._build_caveat(record_id, item, index)
            for index, item in enumerate(
                _registry_sequence(
                    payload.get("scientific_caveats"),
                    record_id=record_id,
                    path="$.scientific_caveats",
                )
            )
        )
        source_claims = tuple(
            self._build_claim(record_id, item, index)
            for index, item in enumerate(
                _registry_sequence(
                    payload.get("claims"),
                    record_id=record_id,
                    path="$.claims",
                )
            )
        )
        configurations = tuple(
            self._build_configuration(record_id, item, index)
            for index, item in enumerate(
                _registry_sequence(
                    label.get("top_configurations"),
                    record_id=record_id,
                    path="$.label.top_configurations",
                )
            )
        )

        try:
            record = EvidenceRecord(
                record_id=record_id,
                rank=rank,
                distance=example.distance,
                selected_device_id=selected_device_id,
                source_claims=source_claims,
                top_configurations=configurations,
                evidence=evidence,
                caveats=caveats,
            )
        except ValueError as error:
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, $): {error}"
            ) from error
        self._validate_selected_label(
            record,
            best_summary_id=selected_best_summary_id,
            best_configuration_id=selected_best_configuration_id,
            median_score=selected_median_score,
        )
        self._validate_links(record)
        return record

    @staticmethod
    def _build_evidence(
        record_id: str,
        value: Any,
        index: int,
    ) -> HistoricalEvidence:
        """Converte un risultato aggregato del Dataset in evidenza storica."""
        path = f"$.evidence[{index}]"
        item = _registry_mapping(value, record_id=record_id, path=path)
        if item.get("evidence_type") != "offline_seed_aggregate":
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, {path}.evidence_type): "
                "tipo di evidenza non supportato."
            )
        aggregation = _registry_mapping(
            item.get("aggregation"),
            record_id=record_id,
            path=f"{path}.aggregation",
        )
        if aggregation.get("method") != "median":
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, "
                f"{path}.aggregation.method): aggregazione non supportata."
            )
        metric = _registry_string(
            item.get("metric"),
            record_id=record_id,
            path=f"{path}.metric",
        )
        if metric != "median_expected_fidelity_across_seeds":
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, {path}.metric): "
                "misura storica non supportata."
            )
        try:
            return HistoricalEvidence(
                evidence_id=_registry_string(
                    item.get("evidence_id"),
                    record_id=record_id,
                    path=f"{path}.evidence_id",
                ),
                device_id=_registry_string(
                    item.get("device_id"),
                    record_id=record_id,
                    path=f"{path}.device_id",
                ),
                configuration_id=_registry_string(
                    item.get("config_id"),
                    record_id=record_id,
                    path=f"{path}.config_id",
                ),
                metric=metric,
                value=_registry_number(
                    aggregation.get("value"),
                    record_id=record_id,
                    path=f"{path}.aggregation.value",
                ),
                summary_id=_registry_string(
                    item.get("summary_id"),
                    record_id=record_id,
                    path=f"{path}.summary_id",
                ),
                sample_count=_registry_integer(
                    aggregation.get("sample_count"),
                    record_id=record_id,
                    path=f"{path}.aggregation.sample_count",
                ),
            )
        except ValueError as error:
            if isinstance(error, EvidenceRegistryDataError):
                raise
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, {path}): {error}"
            ) from error

    @staticmethod
    def _build_caveat(
        record_id: str,
        value: Any,
        index: int,
    ) -> ScientificCaveat:
        """Converte un'avvertenza scientifica nel modello interno."""
        path = f"$.scientific_caveats[{index}]"
        item = _registry_mapping(value, record_id=record_id, path=path)
        try:
            return ScientificCaveat(
                caveat_id=_registry_string(
                    item.get("caveat_id"),
                    record_id=record_id,
                    path=f"{path}.caveat_id",
                ),
                text=_registry_string(
                    item.get("text"),
                    record_id=record_id,
                    path=f"{path}.text",
                ),
            )
        except ValueError as error:
            if isinstance(error, EvidenceRegistryDataError):
                raise
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, {path}): {error}"
            ) from error

    @staticmethod
    def _build_claim(
        record_id: str,
        value: Any,
        index: int,
    ) -> HistoricalClaim:
        """Converte un claim storico e conserva i suoi collegamenti."""
        path = f"$.claims[{index}]"
        item = _registry_mapping(value, record_id=record_id, path=path)
        try:
            claim_type = HistoricalClaimType(
                _registry_string(
                    item.get("claim_type"),
                    record_id=record_id,
                    path=f"{path}.claim_type",
                )
            )
        except ValueError as error:
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, {path}.claim_type): "
                "tipo di claim non supportato."
            ) from error
        evidence_ids = tuple(
            _registry_string(
                item_id,
                record_id=record_id,
                path=f"{path}.evidence_ids[{item_index}]",
            )
            for item_index, item_id in enumerate(
                _registry_sequence(
                    item.get("evidence_ids"),
                    record_id=record_id,
                    path=f"{path}.evidence_ids",
                )
            )
        )
        caveat_ids = tuple(
            _registry_string(
                item_id,
                record_id=record_id,
                path=f"{path}.caveat_ids[{item_index}]",
            )
            for item_index, item_id in enumerate(
                _registry_sequence(
                    item.get("caveat_ids"),
                    record_id=record_id,
                    path=f"{path}.caveat_ids",
                )
            )
        )
        try:
            return HistoricalClaim(
                claim_id=_registry_string(
                    item.get("claim_id"),
                    record_id=record_id,
                    path=f"{path}.claim_id",
                ),
                claim_type=claim_type,
                evidence_ids=evidence_ids,
                caveat_ids=caveat_ids,
            )
        except ValueError as error:
            if isinstance(error, EvidenceRegistryDataError):
                raise
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, {path}): {error}"
            ) from error

    @staticmethod
    def _build_configuration(
        record_id: str,
        value: Any,
        index: int,
    ) -> HistoricalConfiguration:
        """Converte una configurazione classificata del record storico."""
        path = f"$.label.top_configurations[{index}]"
        item = _registry_mapping(value, record_id=record_id, path=path)
        try:
            return HistoricalConfiguration(
                rank=_registry_integer(
                    item.get("rank"),
                    record_id=record_id,
                    path=f"{path}.rank",
                ),
                device_id=_registry_string(
                    item.get("device_id"),
                    record_id=record_id,
                    path=f"{path}.device_id",
                ),
                configuration_id=_registry_string(
                    item.get("config_id"),
                    record_id=record_id,
                    path=f"{path}.config_id",
                ),
                claim_id=_registry_string(
                    item.get("claim_id"),
                    record_id=record_id,
                    path=f"{path}.claim_id",
                ),
                evidence_id=_registry_string(
                    item.get("evidence_id"),
                    record_id=record_id,
                    path=f"{path}.evidence_id",
                ),
                optimization_level=_registry_integer(
                    item.get("optimization_level"),
                    record_id=record_id,
                    path=f"{path}.optimization_level",
                ),
                layout_method=_registry_optional_string(
                    item.get("layout_method"),
                    record_id=record_id,
                    path=f"{path}.layout_method",
                ),
                routing_method=_registry_optional_string(
                    item.get("routing_method"),
                    record_id=record_id,
                    path=f"{path}.routing_method",
                ),
                summary_id=_registry_string(
                    item.get("summary_id"),
                    record_id=record_id,
                    path=f"{path}.summary_id",
                ),
                median_score=_registry_number(
                    item.get("median_score"),
                    record_id=record_id,
                    path=f"{path}.median_score",
                ),
            )
        except ValueError as error:
            if isinstance(error, EvidenceRegistryDataError):
                raise
            raise EvidenceRegistryDataError(
                f"Dataset RAG non valido ({record_id}, {path}): {error}"
            ) from error

    @staticmethod
    def _validate_selected_label(
        record: EvidenceRecord,
        *,
        best_summary_id: str,
        best_configuration_id: str,
        median_score: float,
    ) -> None:
        """Controlla che l'etichetta scelta coincida con il primo risultato."""
        best_configuration = record.top_configurations[0]
        best_evidence = record.find_evidence(best_configuration.evidence_id)
        if (
            best_evidence is None
            or best_configuration.device_id != record.selected_device_id
            or best_configuration.summary_id != best_summary_id
            or best_configuration.configuration_id
            != best_configuration_id
            or not math.isclose(
                best_configuration.median_score,
                median_score,
                rel_tol=1e-12,
                abs_tol=1e-15,
            )
            or best_evidence.summary_id != best_summary_id
            or best_evidence.configuration_id
            != best_configuration_id
            or not math.isclose(
                best_evidence.value,
                median_score,
                rel_tol=1e-12,
                abs_tol=1e-15,
            )
        ):
            raise EvidenceRegistryDataError(
                "Dataset RAG non valido "
                f"({record.record_id}, $.label.selected_device): "
                "migliore configurazione ed evidenza non coerenti."
            )

    def _validate_links(self, record: EvidenceRecord) -> None:
        """Controlla tutti i legami tra claim, configurazioni ed evidenze."""
        device_claims = tuple(
            claim
            for claim in record.source_claims
            if claim.claim_type is HistoricalClaimType.SELECTED_DEVICE
        )
        if len(device_claims) != 1:
            raise EvidenceRegistryDataError(
                "Dataset RAG non valido "
                f"({record.record_id}, $.claims): serve un solo claim "
                "selected_device."
            )
        ranked_claim_ids = {
            claim.claim_id
            for claim in record.source_claims
            if claim.claim_type
            is HistoricalClaimType.RANKED_CONFIGURATION
        }
        configuration_claim_ids = {
            configuration.claim_id
            for configuration in record.top_configurations
        }
        expected_ranks = tuple(range(1, len(record.top_configurations) + 1))
        configuration_ids = tuple(
            configuration.configuration_id
            for configuration in record.top_configurations
        )
        if (
            ranked_claim_ids != configuration_claim_ids
            or len(configuration_ids) != len(set(configuration_ids))
            or tuple(
                configuration.rank
                for configuration in record.top_configurations
            )
            != expected_ranks
        ):
            raise EvidenceRegistryDataError(
                "Dataset RAG non valido "
                f"({record.record_id}, $.label.top_configurations): "
                "ranghi o claim di configurazione non coerenti."
            )
        if any(
            item.configuration_id
            not in self._configuration_catalog.by_id
            for item in record.evidence
        ):
            raise EvidenceRegistryDataError(
                "Dataset RAG non valido "
                f"({record.record_id}, $.evidence): configurazione fuori catalogo."
            )
        if (
            record.top_configurations[0].evidence_id
            not in device_claims[0].evidence_ids
        ):
            raise EvidenceRegistryDataError(
                "Dataset RAG non valido "
                f"({record.record_id}, $.claims): il claim sul dispositivo "
                "non cita la migliore configurazione storica."
            )
        for configuration in record.top_configurations:
            catalog_configuration = self._configuration_catalog.find(
                configuration.optimization_level,
                configuration.layout_method,
                configuration.routing_method,
            )
            if (
                catalog_configuration is None
                or catalog_configuration.config_id
                != configuration.configuration_id
            ):
                raise EvidenceRegistryDataError(
                    "Dataset RAG non valido "
                    f"({record.record_id}, $.label.top_configurations): "
                    "configurazione fuori catalogo o ID incoerente."
                )
            claim = record.find_claim(configuration.claim_id)
            evidence = record.find_evidence(configuration.evidence_id)
            if (
                claim is None
                or claim.claim_type
                is not HistoricalClaimType.RANKED_CONFIGURATION
                or tuple(claim.evidence_ids) != (configuration.evidence_id,)
            ):
                raise EvidenceRegistryDataError(
                    "Dataset RAG non valido "
                    f"({record.record_id}, $.label.top_configurations): "
                    "legame claim-evidenza non coerente."
                )
            if (
                evidence is None
                or evidence.device_id != configuration.device_id
                or evidence.configuration_id
                != configuration.configuration_id
                or evidence.summary_id != configuration.summary_id
                or not math.isclose(
                    evidence.value,
                    configuration.median_score,
                    rel_tol=1e-12,
                    abs_tol=1e-15,
                )
                or configuration.device_id != record.selected_device_id
            ):
                raise EvidenceRegistryDataError(
                    "Dataset RAG non valido "
                    f"({record.record_id}, $.label.top_configurations): "
                    "configurazione ed evidenza non coerenti."
                )


class JsonDatasetContextRetriever:
    """Recupera gli esempi più vicini da JSON storici o JSONL RAG.

    I vecchi record espongono soltanto l'ingresso. I record RAG di addestramento
    includono anche raccomandazione, claim, evidenze e avvertenze storiche.
    """

    def __init__(self, dataset_path: Path, *, required: bool = False) -> None:
        """Configura il percorso del Dataset e se la sua presenza è obbligatoria."""
        self._dataset_path = Path(dataset_path)
        self._required = required
        self._records: list[dict[str, Any]] | None = None

    def _load(self) -> list[dict[str, Any]]:
        """Carica una volta sola i record da JSON o JSONL."""
        if self._records is not None:
            return self._records
        if not self._dataset_path.is_file():
            if self._required:
                raise FileNotFoundError(
                    f"Dataset LLM non trovato: {self._dataset_path}"
                )
            self._records = []
            return self._records

        text = self._dataset_path.read_text(encoding="utf-8")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            records: list[dict[str, Any]] = []
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"{self._dataset_path}:{line_number}: JSONL non valido."
                    ) from error
                if not isinstance(value, dict):
                    raise ValueError(
                        f"{self._dataset_path}:{line_number}: record non oggetto."
                    )
                records.append(value)
            self._records = records
            return records

        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            self._records = [
                item for item in payload["records"] if isinstance(item, dict)
            ]
        elif isinstance(payload, dict):
            self._records = [payload]
        elif isinstance(payload, list):
            self._records = [item for item in payload if isinstance(item, dict)]
        else:
            raise ValueError(f"Formato Dataset non supportato: {self._dataset_path}.")
        return self._records

    def retrieve(
        self,
        request: ParsedRequest,
        compatibility: CompatibilityView,
        *,
        limit: int,
    ) -> tuple[RetrievedExample, ...]:
        """Ordina gli esempi compatibili per distanza e restituisce i primi."""
        if limit <= 0:
            return ()
        available = set(compatibility.available_device_ids)
        ranked: list[RetrievedExample] = []
        for record in self._load():
            if _is_labeled_rag_record(record):
                _validate_labeled_rag_envelope(record)
            if isinstance(record.get("retrieval_input"), dict):
                retrieval_input = record["retrieval_input"]
                objective = record.get("objective") or {}
                if objective.get("name") != request.figure_of_merit:
                    continue
                circuit = retrieval_input.get("circuit") or {}
                features = (circuit.get("features") or {}).get("values") or {}
                distance = _feature_distance(request.features, features)
                if distance is None:
                    continue
                historical_devices = {
                    str(device.get("device_id"))
                    for device in retrieval_input.get(
                        "compatible_devices", []
                    )
                    if isinstance(device, Mapping)
                }
                selected_device = (
                    record.get("selected_device") or {}
                ).get("device_id")
                if selected_device not in historical_devices:
                    raise EvidenceRegistryDataError(
                        "Dataset RAG non valido "
                        f"({record.get('rag_id', '<missing>')}, "
                        "$.selected_device.device_id): dispositivo non "
                        "presente tra i candidati storici."
                    )
                if not historical_devices.intersection(available):
                    continue
                if selected_device not in available:
                    continue
                ranked.append(
                    RetrievedExample(
                        record_id=str(record.get("rag_id", "<missing>")),
                        distance=distance,
                        prompt_input=_compact_rag_example(record),
                    )
                )
                continue

            record_input = record.get("input")
            if not isinstance(record_input, dict):
                continue
            objective = record_input.get("objective") or {}
            if objective.get("name") != request.figure_of_merit:
                continue
            circuit = record_input.get("circuit") or {}
            features = (circuit.get("features") or {}).get("by_name") or {}
            distance = _feature_distance(request.features, features)
            if distance is None:
                continue
            historical_backends = {
                str(backend.get("id"))
                for backend in record_input.get("compatible_backends", [])
                if isinstance(backend, dict)
            }
            if not historical_backends.intersection(available):
                continue
            ranked.append(
                RetrievedExample(
                    record_id=str(record.get("record_id", "<missing>")),
                    distance=distance,
                    prompt_input=_compact_prompt_input(record_input),
                )
            )
        ranked.sort(key=lambda item: (item.distance, item.record_id))
        return tuple(ranked[:limit])


class StructuredPromptBuilder:
    """Costruisce i dati indipendenti dal servizio che chiamerà l'LLM."""

    def __init__(
        self,
        *,
        configuration_catalog: ConfigurationCatalog | None = None,
    ) -> None:
        """Configura il catalogo delle opzioni che l'LLM può scegliere."""
        self._configuration_catalog = (
            load_catalog()
            if configuration_catalog is None
            else configuration_catalog
        )

    def build(
        self,
        request: ParsedRequest,
        compatibility: CompatibilityView,
        examples: Sequence[RetrievedExample],
        *,
        evidence_registry: EvidenceRegistry,
        validation_issues: Sequence[ValidationIssue] = (),
    ) -> PromptEnvelope:
        """Raccoglie richiesta, hardware, esempi, regole ed errori precedenti."""
        available = [
            {
                "id": profile.device_id,
                "num_qubits": profile.num_qubits,
                "operation_names": profile.operation_names,
                "coupling_edges": profile.coupling_edges,
                "supported_figure_of_merit_ids": (
                    profile.supported_figure_of_merit_ids
                ),
                "allowed_qiskit_configuration_ids": (
                    profile.allowed_qiskit_configuration_ids
                ),
                "target_hash": profile.target_hash,
                "metadata": profile.to_dict()["metadata"],
            }
            for profile in compatibility.available
        ]
        payload = {
            "task": (
                "Recommend one compatible quantum device and an allowlisted "
                "deterministic Qiskit compilation plan."
            ),
            "live_request": {
                "schema_version": request.schema_version,
                "request_id": request.request_id,
                "catalog_snapshot_id": request.catalog_snapshot_id,
                "user_text": request.user_text,
                "figure_of_merit": request.figure_of_merit,
                "constraints": request.constraints,
                "circuit": {
                    "name": request.circuit_name,
                    "format": "OpenQASM 2",
                    "qasm2": request.qasm2,
                    "num_qubits": request.num_qubits,
                    "depth": request.depth,
                    "operation_names": request.operation_names,
                    "features": dict(request.features),
                },
                "compatible_hardware": available,
                "unavailable_hardware": {
                    device_id: list(reasons)
                    for device_id, reasons in compatibility.unavailable.items()
                },
            },
            "retrieved_labeled_examples": [
                {
                    "record_id": example.record_id,
                    "distance": example.distance,
                    "example": _json_ready(example.prompt_input),
                }
                for example in examples
            ],
            "allowed_evidence_registry": evidence_registry.to_dict(),
            "response_contract": {
                "json_schema": json.loads(
                    json.dumps(LLM_RECOMMENDATION_SCHEMA)
                ),
                "required_values": {
                    "schema_version": LLM_RECOMMENDATION_SCHEMA_VERSION,
                    "request_id": request.request_id,
                    "catalog_snapshot_id": request.catalog_snapshot_id,
                    "selected_device": (
                        "one live_request.compatible_hardware[].id"
                    ),
                    "figure_of_merit": request.figure_of_merit,
                    "compiler": "qiskit",
                    "historical_record_ids": [
                        record.record_id
                        for record in evidence_registry.records
                    ],
                    "historical_support_required": bool(
                        evidence_registry.records
                    ),
                },
            },
            "configuration_catalog": {
                "catalog_id": self._configuration_catalog.catalog_id,
                "allowed_configurations": [
                    configuration.to_dict()
                    for configuration
                    in self._configuration_catalog.configurations
                ],
            },
            "previous_validation_errors": [
                {
                    "code": issue.code,
                    "path": issue.path,
                    "message": issue.message,
                }
                for issue in validation_issues
            ],
            "rules": [
                (
                    "Return exactly one JSON object matching the response "
                    "schema, without Markdown or surrounding text."
                ),
                "Never select unavailable hardware.",
                "Use only a configuration allowed by the selected hardware.",
                "Do not invent hardware, scores, pass traces, or measurements.",
                (
                    "Historical labels and evidence are examples, not live "
                    "ground truth."
                ),
                (
                    "Return only structured claims and evidence_refs; do not "
                    "write explanations, evidence text, warnings, scores, or "
                    "measurements."
                ),
                (
                    "Every historical claim must cite only record, source claim, "
                    "and evidence ids from allowed_evidence_registry."
                ),
                (
                    "When historical records are available, support both the "
                    "selected device and the exact Qiskit configuration with "
                    "historical claims, and always include live_compatibility."
                ),
                (
                    "When no historical records are available, use "
                    "historical_evidence_unavailable, no evidence_refs, and "
                    "always include live_compatibility."
                ),
                (
                    "Scientific caveats are resolved and rendered by the "
                    "application from validated source links."
                ),
                (
                    "The final circuit will be produced only by the "
                    "deterministic compiler."
                ),
            ],
        }
        return PromptEnvelope(payload=payload)

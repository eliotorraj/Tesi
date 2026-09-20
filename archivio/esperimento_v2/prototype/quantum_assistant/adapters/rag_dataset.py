"""Fonte RAG unica, provenienza train ed evidenze verificate."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qiskit_dataset.catalog import V2_CATALOG_PATH, load_catalog
from qiskit_dataset.core import dataset_scope_root
from qiskit_dataset.experiment_v2 import source_manifest, stable_sha256
from scripts.mqt_predictor_protocol import (
    EXPERIMENT_ID, EXPERIMENT_ROOT, PROTOCOL_VERSION, SOURCE_MANIFEST_V2,
    FROZEN_TARGET_SHA256, assert_records_belong_to_split, file_sha256,
)
from ..models import RetrievedExample
from ..schema_validation import ensure_supported_schema, validate_instance
from .rag_features import FeatureTransform, RetrievalIntegrityError, transform_unscaled

DEFAULT_DATASET = dataset_scope_root("expected_fidelity", "full", experiment_id=EXPERIMENT_ID) / "global/rag_examples.jsonl"
DEFAULT_RAG_ROOT = EXPERIMENT_ROOT / "rag"
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas/qiskit_rag_example.schema.json"
COLLECTION_NAME = "circuit49_manhattan_v1"
# Impronta del manifest v2 già congelata nel protocollo, non una nuova partizione.
FROZEN_SOURCE_MANIFEST_SHA256 = "c599eab17b6f64528067016e3d175cbfed597334f779ef8e515cf8787a788f53"


def strict_json(text: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            if key in result:
                raise RetrievalIntegrityError(f"Chiave JSON duplicata: {key}.")
            result[key] = value
        return result

    def invalid(value: str) -> None:
        raise RetrievalIntegrityError(f"Numero JSON non finito: {value}.")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def record_features(record: Mapping[str, Any]) -> Mapping[str, Any]:
    return record["retrieval_input"]["circuit"]["features"]["values"]


def point_id(rag_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"{EXPERIMENT_ID}/{COLLECTION_NAME}/{rag_id}"))


def point_payload(record: dict[str, Any]) -> dict[str, Any]:
    circuit = record["retrieval_input"]["circuit"]
    return {
        "rag_id": record["rag_id"], "experiment_id": record["experiment_id"],
        "split": record["split"], "objective": record["objective"]["name"],
        "selected_device_id": record["selected_device"]["device_id"],
        "source_sha256": circuit["source_sha256"], "circuit_id": circuit["circuit_id"],
        "record_sha256": stable_sha256(record),
        "record": record,
    }


def as_example(record: dict[str, Any], distance: float) -> RetrievedExample:
    from .context import _compact_rag_example
    return RetrievedExample(record_id=record["rag_id"], distance=distance, prompt_input=_compact_rag_example(record))


def validate_records(records: list[dict[str, Any]], manifest: Mapping[str, Any]) -> None:
    from .context import StructuredEvidenceRegistryBuilder
    schema = strict_json(SCHEMA_PATH.read_text())
    ensure_supported_schema(schema)
    if not records:
        raise RetrievalIntegrityError("Il Dataset RAG è vuoto.")
    if manifest.get("experiment_id") != EXPERIMENT_ID:
        raise RetrievalIntegrityError("Manifest di un altro esperimento.")
    assert_records_belong_to_split(records, allowed_split="train", manifest=manifest)
    allowed = {(r["source_sha256"], r["circuit_id"]): r for r in manifest["circuits"] if r["split"] == "train"}
    seen_ids, seen_hashes = set(), set()
    registry = StructuredEvidenceRegistryBuilder()
    for record in records:
        issues = validate_instance(schema, record)
        if issues:
            raise RetrievalIntegrityError(f"Schema RAG: {issues[0]}")
        if (record.get("experiment_id") != EXPERIMENT_ID or record.get("protocol_version") != PROTOCOL_VERSION
                or record["split"] != "train" or record["view_scope"] != "global_multi_device"):
            raise RetrievalIntegrityError("Record RAG fuori esperimento, versione, vista o split.")
        circuit = record["retrieval_input"]["circuit"]
        source_hash = circuit["source_sha256"]
        if record["rag_id"] in seen_ids or source_hash in seen_hashes:
            raise RetrievalIntegrityError("Identificativo RAG o hash sorgente duplicato.")
        seen_ids.add(record["rag_id"])
        seen_hashes.add(source_hash)
        original = allowed.get((source_hash, circuit["circuit_id"]))
        if original is None or circuit["num_qubits"] != original["num_qubits"]:
            raise RetrievalIntegrityError("Identità del circuito diversa dal manifest train.")
        expected_ref = f"circuits/train/{original['file_name']}"
        if circuit["source_ref"] != expected_ref:
            raise RetrievalIntegrityError("Riferimento sorgente fuori train o incoerente.")
        features = record_features(record)
        transform_unscaled(features)
        if (circuit["features"].get("dimension") != 49
                or circuit["features"].get("extractor") != "mqt.predictor.ml.helper.create_feature_vector"
                or features["num_qubits"] != circuit["num_qubits"] or features["depth"] != circuit["depth"]):
            raise RetrievalIntegrityError("Metadati delle feature incoerenti.")
        devices = record["retrieval_input"]["compatible_devices"]
        ids = [d["device_id"] for d in devices]
        if len(set(ids)) != len(ids) or record["selected_device"]["device_id"] not in ids:
            raise RetrievalIntegrityError("Dispositivo vincente non presente nei candidati.")
        for device in devices:
            if device["target_sha256"] != FROZEN_TARGET_SHA256.get(device["device_id"]):
                raise RetrievalIntegrityError("Impronta Target incoerente.")
        for evidence in record["evidence"]:
            provenance = evidence["provenance"]
            if (provenance["source_sha256"] != source_hash
                    or provenance["target_sha256"] != FROZEN_TARGET_SHA256.get(evidence["device_id"])):
                raise RetrievalIntegrityError("Provenienza delle evidenze incoerente.")
        registry.build((as_example(record, 0.0),))


@dataclass(frozen=True)
class RagCorpus:
    records: tuple[dict[str, Any], ...]
    transform: FeatureTransform
    source_sha256: str
    provenance: dict[str, str]

    @property
    def transform_artifact(self) -> dict[str, Any]:
        return self.transform.artifact(source_sha256=self.source_sha256, experiment_id=EXPERIMENT_ID)


def load_corpus(dataset_path: Path = DEFAULT_DATASET, *, verify_features: bool = False) -> RagCorpus:
    """Verifica solo train; gli aggregati servono a controllare le evidenze."""
    from qiskit_dataset.views import build_rag_examples
    path = Path(dataset_path).resolve()
    if path != DEFAULT_DATASET.resolve():
        raise RetrievalIntegrityError(f"Fonte RAG non ammessa: usare {DEFAULT_DATASET}.")
    if file_sha256(SOURCE_MANIFEST_V2) != FROZEN_SOURCE_MANIFEST_SHA256:
        raise RetrievalIntegrityError("Manifest sorgente v2 diverso da quello congelato.")
    source_bytes = path.read_bytes()
    records = [strict_json(line) for line in source_bytes.decode("utf-8").splitlines() if line.strip()]
    manifest = source_manifest()
    validate_records(records, manifest)
    catalog = load_catalog(V2_CATALOG_PATH)
    summaries_path = path.with_name("qiskit_configuration_aggregates.jsonl")
    # Nessuna scrittura e nessuna compilazione. Gli score validation non sono usati.
    summaries = []
    with summaries_path.open(encoding="utf-8") as handle:
        for line in handle:
            summary = strict_json(line)
            if summary["split"] == "train":
                summaries.append(summary)
    expected = build_rag_examples(summaries, top_k=3, device_order=catalog.supported_device_ids)
    if sorted(records, key=lambda r: r["rag_id"]) != sorted(expected, key=lambda r: r["rag_id"]):
        raise RetrievalIntegrityError("JSONL incompleto o diverso dalle evidenze train originali.")
    source_hashes = {}
    for record in records:
        circuit = record["retrieval_input"]["circuit"]
        source = path.parent.parent / circuit["source_ref"]
        observed = file_sha256(source)
        if observed != circuit["source_sha256"]:
            raise RetrievalIntegrityError(f"Sorgente train modificato: {source}.")
        source_hashes[circuit["source_ref"]] = observed
        if verify_features:
            from .request import QasmRequestParser
            from ..models import UiSubmission
            parsed = QasmRequestParser().parse(UiSubmission(
                request_id=circuit["circuit_id"], qasm2=source.read_text(),
                user_text="", figure_of_merit="expected_fidelity",
            ))
            if dict(parsed.features) != dict(record_features(record)):
                raise RetrievalIntegrityError(f"Feature diverse dal circuito train: {source}.")
    return RagCorpus(
        records=tuple(records),
        transform=FeatureTransform.fit_train(record_features(r) for r in records),
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        provenance={
            "source_manifest_sha256": file_sha256(SOURCE_MANIFEST_V2),
            "catalog_sha256": file_sha256(V2_CATALOG_PATH),
            "train_summaries_sha256": stable_sha256(summaries),
            "train_sources_sha256": stable_sha256(source_hashes),
            "rag_schema_sha256": file_sha256(SCHEMA_PATH),
        },
    )

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
from qiskit_dataset.experiment_v2 import stable_sha256
from scripts.mqt_predictor_protocol import (
    EXPERIMENT_ID, PROTOCOL_VERSION, FROZEN_TARGET_SHA256, file_sha256,
)
from ..models import RetrievedExample
from ..schema_validation import ensure_supported_schema, validate_instance
from .rag_features import FeatureTransform, RetrievalIntegrityError, transform_unscaled

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET = ROOT / "data/rag_examples.jsonl"
DEFAULT_RAG_ROOT = ROOT / "runtime/rag"

def assert_records_belong_to_split(records, *, allowed_split, manifest):
    if any(r.get("split") != allowed_split for r in records):
        raise RetrievalIntegrityError("Corpus fuori train.")

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
    path=Path(dataset_path).resolve()
    if path != DEFAULT_DATASET.resolve():
        raise RetrievalIntegrityError("Usare esclusivamente il train distribuito col prototipo.")
    seal=strict_json((ROOT/"data/seal.json").read_text())
    for relative, expected in seal["files"].items():
        if file_sha256(ROOT/relative) != expected:
            raise RetrievalIntegrityError(f"File modificato: {relative}")
    records=[strict_json(line) for line in path.read_text().splitlines() if line.strip()]
    if len(records) != 396:
        raise RetrievalIntegrityError("Attesi esattamente 396 esempi train.")
    manifest=strict_json((ROOT/"data/train_manifest.json").read_text())
    validate_records(records,manifest)
    transform=FeatureTransform.fit_train(record_features(r) for r in records)
    source_hash=file_sha256(path)
    artifact=transform.artifact(source_sha256=source_hash, experiment_id=EXPERIMENT_ID)
    if artifact != strict_json((ROOT/"data/transform.json").read_text()):
        raise RetrievalIntegrityError("Divisori diversi dalla trasformazione train originale.")
    if verify_features:
        from .request import QasmRequestParser
        from ..models import UiSubmission
        for record in records:
            c=record["retrieval_input"]["circuit"]
            parsed=QasmRequestParser().parse(UiSubmission(request_id=c["circuit_id"],qasm2=(ROOT/"data"/c["source_ref"]).read_text(),user_text=""))
            if dict(parsed.features) != dict(record_features(record)):
                raise RetrievalIntegrityError("Feature diverse: "+c["circuit_id"])
    return RagCorpus(tuple(records),transform,source_hash,{"portable_seal_sha256":file_sha256(ROOT/"data/seal.json")})

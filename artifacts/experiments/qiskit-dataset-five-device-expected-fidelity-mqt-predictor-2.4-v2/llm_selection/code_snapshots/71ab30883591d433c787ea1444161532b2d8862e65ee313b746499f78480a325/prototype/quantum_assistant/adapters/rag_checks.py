"""Prove tecniche del recupero: nessuna raccomandazione LLM o compilazione."""

from __future__ import annotations

import hashlib
import math
import sys
import time
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qiskit_dataset.experiment_v2 import source_manifest, stable_sha256
from scripts.mqt_predictor_protocol import (
    EXPERIMENT_ID, FROZEN_DEVICES, VALIDATION_CIRCUITS_V2,
    file_sha256, verify_circuit_directory,
)
from .rag_dataset import DEFAULT_RAG_ROOT, RagCorpus, record_features
from .rag_features import FEATURE_ORDER, SCORE_ABS_TOL, SCORE_REL_TOL, RetrievalIntegrityError
from .qdrant_context import expected_manifest


def independent_rank(corpus: RagCorpus, features, devices, *, limit: int):
    """Formula scalare indipendente: non richiama fit/apply/manhattan."""
    def raw(row):
        return [
            math.log1p(row[name]) if name.startswith("gate_count_") or name in ("depth", "num_qubits") else row[name]
            for name in FEATURE_ORDER
        ]
    rows = [raw(record_features(r)) for r in corpus.records]
    divisors = [max(abs(row[i]) for row in rows) or 1 for i in range(49)]
    query = raw(features)
    distances = []
    for record, row in zip(corpus.records, rows, strict=True):
        if record["selected_device"]["device_id"] not in devices:
            continue
        distance = math.fsum(abs(query[i] / divisors[i] - row[i] / divisors[i]) for i in range(49))
        distances.append((distance, record["rag_id"]))
    return sorted(distances)[:limit]


def prepare_prompt(service, qasm_path: Path, *, devices=None) -> dict:
    """Usa parser, maschera, adattatore e costruttori del servizio effettivo."""
    source_bytes = qasm_path.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    forbidden = {r["source_sha256"] for r in source_manifest()["circuits"] if r["split"] == "test"}
    if source_hash in forbidden:
        raise RetrievalIntegrityError("Questa prova tecnica non accede ai circuiti test.")
    snapshot = service.hardware_catalog.snapshot()
    request = {
        "schema_version": "1.0.0",
        "request_id": str(uuid5(NAMESPACE_URL, "rag-validation/" + source_hash)),
        "catalog_snapshot_id": snapshot.catalog_snapshot_id,
        "circuit": {"format": "openqasm2", "name": qasm_path.stem, "source": source_bytes.decode("utf-8")},
        "figure_of_merit_id": "expected_fidelity",
        "hardware_constraints": {"allowed_device_ids": list(devices)} if devices else {},
    }
    prepared = service.prepare_request(request)
    if not prepared.can_recommend:
        return {"status": "NO_ELIGIBLE_DEVICE", "circuit_id": qasm_path.stem, "source_sha256": source_hash}
    started = time.perf_counter()
    examples = service.context_retriever.retrieve(prepared.request, prepared.mask_result, limit=service.retrieval_limit)
    registry = service.evidence_registry_builder.build(examples)
    prompt = service.prompt_builder.build(prepared.request, prepared.mask_result, examples, evidence_registry=registry)
    return {
        "status": "prepared", "circuit_id": qasm_path.stem, "source_sha256": source_hash,
        "features": dict(prepared.request.features),
        "devices": list(prepared.mask_result.available_device_ids),
        "examples": [{"rag_id": r.record_id, "distance": r.distance} for r in examples],
        "registry_count": len(registry.records), "registry_sha256": stable_sha256(registry.to_dict()),
        "prompt_sha256": stable_sha256(prompt.payload), "prompt": dict(prompt.payload),
        "retrieval_and_prompt_seconds": time.perf_counter() - started,
        "query_audit": getattr(service.context_retriever, "last_query_audit", {}),
    }


def validate_validation_report(report: dict, index_manifest: dict, manifest: dict) -> None:
    expected = {(r["circuit_id"], r["source_sha256"]) for r in manifest["circuits"] if r["split"] == "validation"}
    rows = report.get("rows", [])
    if (report.get("status") != "passed" or report.get("experiment_id") != EXPERIMENT_ID
            or report.get("validation_count") != 88 or report.get("k") != 5
            or report.get("index_manifest_sha256") != index_manifest["sha256"]
            or report.get("transform_sha256") != index_manifest["transform_sha256"]
            or report.get("llm_calls") != 0 or report.get("compilations") != 0
            or report.get("test_accessed") is not False
            or not isinstance(rows, list) or len(rows) != 88):
        raise RetrievalIntegrityError("Verifica RAG validation assente o incompatibile.")
    observed = {(r.get("circuit_id"), r.get("source_sha256")) for r in rows}
    if observed != expected:
        raise RetrievalIntegrityError("La verifica non copre gli 88 circuiti validation.")
    for row in rows:
        examples = row.get("examples", [])
        if (row.get("status") != "prepared" or row.get("registry_count") != len(examples)
                or len(examples) > 5 or len({r["rag_id"] for r in examples}) != len(examples)
                or not row.get("prompt_sha256") or not row.get("registry_sha256")):
            raise RetrievalIntegrityError("Riga della verifica validation incompleta.")


def check_validation(corpus: RagCorpus, *, limit: int = 5) -> dict:
    from .llm import UnconfiguredLlmGateway
    from ..factory import build_default_service
    verify_circuit_directory(VALIDATION_CIRCUITS_V2, allowed_splits=("validation",))
    manifest = source_manifest()
    circuits = sorted((r for r in manifest["circuits"] if r["split"] == "validation"), key=lambda r: r["circuit_id"])
    if len(circuits) != 88:
        raise RetrievalIntegrityError("Attesi 88 circuiti validation.")
    service = build_default_service(device_names=FROZEN_DEVICES, llm_gateway=UnconfiguredLlmGateway(), retrieval_limit=limit)
    rows = []
    maximum_error = 0.0
    for position, circuit in enumerate(circuits, start=1):
        path = VALIDATION_CIRCUITS_V2 / circuit["file_name"]
        if file_sha256(path) != circuit["source_sha256"]:
            raise RetrievalIntegrityError("Sorgente validation modificato.")
        row = prepare_prompt(service, path)
        if row["status"] != "prepared":
            raise RetrievalIntegrityError(f"Richiesta non preparata: {circuit['circuit_id']}.")
        expected = independent_rank(corpus, row.pop("features"), row["devices"], limit=limit)
        observed = [(r["distance"], r["rag_id"]) for r in row["examples"]]
        if [r[1] for r in observed] != [r[1] for r in expected]:
            raise RetrievalIntegrityError(f"Ordinamento indipendente diverso: {circuit['circuit_id']}.")
        for (a, _), (b, _) in zip(observed, expected, strict=True):
            maximum_error = max(maximum_error, abs(a - b))
            if not math.isclose(a, b, abs_tol=SCORE_ABS_TOL, rel_tol=SCORE_REL_TOL):
                raise RetrievalIntegrityError("Distanza diversa dal riferimento indipendente.")
        if row["registry_count"] != len(observed):
            raise RetrievalIntegrityError("Registro incompleto.")
        row.pop("prompt")
        rows.append(row)
        if position % 8 == 0:
            print(f"Validation RAG: {position}/88", file=sys.stderr, flush=True)
    return {
        "status": "passed", "experiment_id": EXPERIMENT_ID,
        "scope": "parsing_mask_retrieval_evidence_prompt_only", "validation_count": len(rows),
        "k": limit, "llm_calls": 0, "compilations": 0, "test_accessed": False,
        "index_manifest_sha256": expected_manifest(corpus)["sha256"],
        "transform_sha256": corpus.transform_artifact["sha256"],
        "max_canonical_distance_error": maximum_error,
        "max_qdrant_score_error": max(row["query_audit"]["max_qdrant_score_error"] for row in rows),
        "qdrant_score_abs_tolerance": SCORE_ABS_TOL, "qdrant_score_rel_tolerance": SCORE_REL_TOL,
        "rows": rows,
    }

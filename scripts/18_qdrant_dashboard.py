"""Copia nella dashboard locale i punti dell'indice RAG già verificato."""

from __future__ import annotations

import json
import math
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from qdrant_client import QdrantClient, models

from prototype.quantum_assistant.adapters.qdrant_context import verified_client, expected_manifest
from prototype.quantum_assistant.adapters.rag_dataset import COLLECTION_NAME, DEFAULT_RAG_ROOT, load_corpus
from qiskit_dataset.experiment_v2 import atomic_json_write
from scripts.mqt_predictor_protocol import file_sha256

URL = "http://127.0.0.1:6333"


def index_hashes(index: Path) -> dict[str, str]:
    return {str(p.relative_to(index)): file_sha256(p)
            for p in sorted(index.rglob("*")) if p.is_file() and p.name != ".lock"}


def read_points(client: QdrantClient) -> list[models.Record]:
    result = []
    offset = None
    while True:
        points, offset = client.scroll(
            COLLECTION_NAME, offset=offset, limit=128, with_payload=True, with_vectors=True,
        )
        result.extend(points)
        if offset is None:
            return result


def matching_payload(a: object, b: object, rounding: list[float]) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(matching_payload(a[k], b[k], rounding) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(matching_payload(x, y, rounding) for x, y in zip(a, b))
    if isinstance(a, float) and a != b:
        # Il percorso JSON di Qdrant può arrotondare i punteggi float64.
        # Nessuna tolleranza su interi, testi, identità o impronte di origine.
        delta = abs(a - b)
        accepted = math.isfinite(a) and math.isfinite(b) and delta <= 2 * max(math.ulp(a), math.ulp(b))
        if accepted:
            rounding.append(delta)
        return accepted
    return a == b


def verify_copy(client: QdrantClient, original: list[models.Record]) -> list[float]:
    params = client.get_collection(COLLECTION_NAME).config.params.vectors
    if not isinstance(params, models.VectorParams) or params.size != 49 or params.distance != models.Distance.MANHATTAN:
        raise RuntimeError("La raccolta della dashboard ha dimensione o metrica diversa.")
    actual = read_points(client)
    expected = {str(p.id): p for p in original}
    if len(actual) != len(expected) or {str(p.id) for p in actual} != set(expected):
        raise RuntimeError("La raccolta della dashboard ha punti mancanti o estranei.")
    rounding = []
    for point in actual:
        source = expected[str(point.id)]
        # L'API JSON del server arrotonda la rappresentazione decimale di float32.
        if (not matching_payload(point.payload, source.payload, rounding)
                or not np.array_equal(np.asarray(point.vector, dtype=np.float32),
                                      np.asarray(source.vector, dtype=np.float32))):
            raise RuntimeError(f"Dati diversi nella dashboard: {point.id}")
    return rounding


def main() -> None:
    index = DEFAULT_RAG_ROOT / "index"
    before = index_hashes(index)
    corpus = load_corpus(verify_features=True)
    with verified_client(index, corpus) as local:
        original = read_points(local)
    with closing(QdrantClient(url=URL, timeout=30)) as remote:
        if not remote.collection_exists(COLLECTION_NAME):
            remote.create_collection(
                COLLECTION_NAME,
                vectors_config=models.VectorParams(size=49, distance=models.Distance.MANHATTAN),
                hnsw_config=models.HnswConfigDiff(m=0),
            )
            for start in range(0, len(original), 64):
                remote.upsert(COLLECTION_NAME, wait=True, points=[
                    models.PointStruct(id=p.id, vector=p.vector, payload=p.payload)
                    for p in original[start:start + 64]
                ])
        # Una raccolta esistente è soltanto verificata: nessuna cancellazione.
        rounding = verify_copy(remote, original)
        server_version = remote.info().version
    after = index_hashes(index)
    if before != after:
        raise RuntimeError("I file dell'indice originale sono cambiati durante la copia.")
    report = {
        "status": "verified", "purpose": "dataset_inspection",
        "dashboard_url": URL + "/dashboard/",
        "collection": COLLECTION_NAME, "points": len(original),
        "dimension": 49, "distance": "Manhattan", "split": "train",
        "server_version": server_version,
        "source_manifest_sha256": expected_manifest(corpus)["sha256"],
        "original_index_unchanged": True, "original_index_files": before,
        "retrieval_backend_changed": False,
        "vectors_equal_float32": True,
        "payload_json_rounding_tolerance_ulps": 2,
        "payload_json_rounded_values": len(rounding),
        "payload_json_max_rounding": max(rounding, default=0.0),
    }
    atomic_json_write(DEFAULT_RAG_ROOT / "dashboard" / "verification.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "original_index_files"}, indent=2))


if __name__ == "__main__":
    main()

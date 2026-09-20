"""Qdrant locale persistente: raccolta verificata e ricerca esatta filtrata."""

from __future__ import annotations

import math
import os
import platform
import tomllib
from collections.abc import Mapping, Sequence
from contextlib import closing, contextmanager
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

import numpy as np
from qdrant_client import QdrantClient, models

from qiskit_dataset.experiment_v2 import atomic_json_write, stable_sha256
from scripts.mqt_predictor_protocol import EXPERIMENT_ID, file_sha256
from ..models import CompatibilityView, NormalizedRequest, RetrievedExample
from .rag_dataset import (
    COLLECTION_NAME, DEFAULT_DATASET, DEFAULT_RAG_ROOT, RagCorpus, as_example,
    load_corpus, point_id, point_payload, record_features, strict_json,
)
from .rag_features import RetrievalIntegrityError, SCORE_ABS_TOL, SCORE_REL_TOL, manhattan

INDEX_VERSION = "qdrant-local-circuit49/1"


class RetrievalDatabaseError(RuntimeError):
    """Un guasto del database non è un recupero senza evidenze."""

    code = "RAG_DATABASE_ERROR"
    retryable = False

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "retryable": self.retryable, "message": str(self)}


def _points(corpus: RagCorpus) -> list[models.PointStruct]:
    return [
        models.PointStruct(
            id=point_id(record["rag_id"]),
            vector=np.asarray(corpus.transform.apply(record_features(record)), dtype=np.float32).tolist(),
            payload=point_payload(record),
        )
        for record in sorted(corpus.records, key=lambda r: r["rag_id"])
    ]


def expected_manifest(corpus: RagCorpus) -> dict[str, Any]:
    points = _points(corpus)
    lock_path = Path(__file__).resolve().parents[3] / "requirements.txt"
    pinned = dict(line.split("==") for line in lock_path.read_text().splitlines() if "==" in line and not line.startswith("#"))
    software = {name: version(name) for name in ("qdrant-client", "numpy", "mqt.bench", "qiskit", "portalocker", "networkx")}
    if any(pinned.get(name) != value for name, value in software.items()):
        raise RetrievalIntegrityError("Versioni diverse da requirements.txt.")
    core = {
        "index_version": INDEX_VERSION, "experiment_id": EXPERIMENT_ID,
        "collection": COLLECTION_NAME, "mode": "local_persistent", "search": "exact",
        "distance": "Manhattan", "dimension": 49, "points_count": len(points),
        "source_jsonl_sha256": corpus.source_sha256,
        "transform_sha256": corpus.transform_artifact["sha256"],
        "points_sha256": stable_sha256([p.model_dump() for p in points]),
        "provenance": corpus.provenance,
        "software": software,
        "python": platform.python_version(),
        "requirements_sha256": file_sha256(Path(__file__).resolve().parents[3] / "requirements.txt"),
        "default_k": 5,
    }
    return {**core, "sha256": stable_sha256(core)}


def verify_artifacts(index_dir: Path, corpus: RagCorpus) -> dict[str, Any]:
    """Confronta anche i divisori ricalcolati esclusivamente sul train."""
    expected = expected_manifest(corpus)
    for name, value in (("manifest.json", expected), ("transform.json", corpus.transform_artifact)):
        path = index_dir / name
        if not path.is_file() or stable_sha256(strict_json(path.read_text())) != stable_sha256(value):
            raise RetrievalIntegrityError(f"Artefatto assente o incompatibile: {path}.")
    return expected


def verify_collection(client: QdrantClient, corpus: RagCorpus) -> None:
    names = {c.name for c in client.get_collections().collections}
    if names != {COLLECTION_NAME}:
        raise RetrievalIntegrityError("Raccolta assente o raccolte residue nel database RAG.")
    info = client.get_collection(COLLECTION_NAME)
    params = info.config.params.vectors
    if not isinstance(params, models.VectorParams) or params.size != 49 or params.distance != models.Distance.MANHATTAN:
        raise RetrievalIntegrityError("Dimensione o metrica Qdrant incompatibile.")
    if client.count(COLLECTION_NAME, exact=True).count != len(corpus.records):
        raise RetrievalIntegrityError("Raccolta Qdrant incompleta o con punti residui.")
    expected = {str(p.id): p for p in _points(corpus)}
    seen = set()
    offset = None
    while True:
        points, offset = client.scroll(
            COLLECTION_NAME, limit=128, offset=offset, with_payload=True, with_vectors=True,
        )
        for point in points:
            identifier = str(point.id)
            if identifier in seen or identifier not in expected:
                raise RetrievalIntegrityError("ID Qdrant duplicato o inatteso.")
            seen.add(identifier)
            target = expected[identifier]
            if stable_sha256(point.payload) != stable_sha256(target.payload) or point.vector != target.vector:
                raise RetrievalIntegrityError(f"Vettore o dati associati manomessi: {identifier}.")
        if offset is None:
            break
    if seen != set(expected):
        raise RetrievalIntegrityError("La lettura Qdrant non contiene tutti i punti attesi.")


@contextmanager
def verified_client(index_dir: Path, corpus: RagCorpus) -> Iterator[QdrantClient]:
    verify_artifacts(index_dir, corpus)
    database = index_dir / "qdrant"
    if not (database / "meta.json").is_file():
        raise RetrievalIntegrityError(f"Database persistente assente: {database}.")
    try:
        with closing(QdrantClient(path=str(database))) as client:
            verify_collection(client, corpus)
            yield client
    except (RetrievalIntegrityError, RetrievalDatabaseError):
        raise
    except Exception as error:
        raise RetrievalDatabaseError(f"Qdrant locale: {type(error).__name__}: {error}") from error


def prepare_index(corpus: RagCorpus, rag_root: Path = DEFAULT_RAG_ROOT) -> dict[str, Any]:
    """Crea atomicamente; una raccolta esistente viene solo verificata."""
    rag_root = Path(rag_root)
    index_dir = rag_root / "index"
    if index_dir.exists():
        with verified_client(index_dir, corpus):
            return expected_manifest(corpus)
    rag_root.mkdir(parents=True, exist_ok=True)
    staging = rag_root / f".index-build-{uuid4().hex}"
    staging.mkdir()
    # In caso di errore la directory temporanea resta disponibile per la diagnosi.
    with closing(QdrantClient(path=str(staging / "qdrant"))) as client:
        client.create_collection(
            COLLECTION_NAME, vectors_config=models.VectorParams(size=49, distance=models.Distance.MANHATTAN),
        )
        points = _points(corpus)
        for start in range(0, len(points), 64):
            client.upsert(COLLECTION_NAME, points=points[start:start + 64], wait=True)
        verify_collection(client, corpus)
    atomic_json_write(staging / "transform.json", corpus.transform_artifact)
    atomic_json_write(staging / "manifest.json", expected_manifest(corpus))
    # Riapertura reale prima di rendere disponibile l'indice.
    with verified_client(staging, corpus):
        pass
    os.rename(staging, index_dir)
    return expected_manifest(corpus)


def matching_records(corpus: RagCorpus, *, devices: Sequence[str], objective: str, experiment_id: str) -> tuple[dict[str, Any], ...]:
    allowed = set(devices)
    return tuple(r for r in corpus.records if (
        r["experiment_id"] == experiment_id and r["split"] == "train"
        and r["objective"]["name"] == objective and r["selected_device"]["device_id"] in allowed
    ))


def query_exact(
    client: QdrantClient, corpus: RagCorpus, features: Mapping[str, Any], *,
    devices: Sequence[str], objective: str, limit: int, experiment_id: str = EXPERIMENT_ID,
    audit: dict[str, float] | None = None,
) -> tuple[RetrievedExample, ...]:
    query = corpus.transform.apply(features)
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("k deve essere un intero non negativo.")
    candidates = matching_records(corpus, devices=devices, objective=objective, experiment_id=experiment_id)
    query_filter = models.Filter(must=[
        models.FieldCondition(key="experiment_id", match=models.MatchValue(value=experiment_id)),
        models.FieldCondition(key="split", match=models.MatchValue(value="train")),
        models.FieldCondition(key="objective", match=models.MatchValue(value=objective)),
        models.FieldCondition(key="selected_device_id", match=models.MatchAny(any=list(devices))),
    ])
    # La modalità locale è sempre esatta. SearchParams(exact=True) vi è ignorato.
    # Tutti i candidati filtrati: nessuna parità al confine viene persa.
    results = client.query_points(
        COLLECTION_NAME, query=list(query), query_filter=query_filter,
        limit=max(1, len(corpus.records)), with_payload=True,
    ).points
    expected = {point_id(r["rag_id"]): r for r in candidates}
    if len(results) != len(expected) or {str(p.id) for p in results} != set(expected):
        raise RetrievalIntegrityError("Qdrant ha restituito candidati mancanti o fuori filtro.")
    ranked = []
    max_score_error = 0.0
    for point in results:
        record = expected[str(point.id)]
        if stable_sha256(point.payload) != stable_sha256(point_payload(record)):
            raise RetrievalIntegrityError("Dati del risultato diversi dalla fonte RAG.")
        distance = manhattan(query, corpus.transform.apply(record_features(record)))
        if not math.isfinite(point.score) or not math.isclose(
            point.score, distance, abs_tol=SCORE_ABS_TOL, rel_tol=SCORE_REL_TOL,
        ):
            raise RetrievalIntegrityError(f"Distanza Qdrant fuori tolleranza per {record['rag_id']}.")
        max_score_error = max(max_score_error, abs(point.score - distance))
        # Raffinamento float64 esplicito; nessun arrotondamento o gruppo di quasi-parità.
        ranked.append(as_example(record, distance))
    ranked.sort(key=lambda item: (item.distance, item.record_id))
    if audit is not None:
        audit["max_qdrant_score_error"] = max_score_error
    return tuple(ranked[:limit])


class QdrantContextRetriever:
    def __init__(self, dataset_path: Path = DEFAULT_DATASET, *, rag_root: Path = DEFAULT_RAG_ROOT) -> None:
        self.dataset_path = Path(dataset_path)
        self.rag_root = Path(rag_root)

    def retrieve(self, request: NormalizedRequest, compatibility: CompatibilityView, *, limit: int) -> tuple[RetrievedExample, ...]:
        corpus = load_corpus(self.dataset_path)
        self.last_query_audit: dict[str, float] = {}
        with verified_client(self.rag_root / "index", corpus) as client:
            return query_exact(client, corpus, request.features, devices=compatibility.available_device_ids,
                               objective=request.figure_of_merit, limit=limit, audit=self.last_query_audit)


class DisabledContextRetriever:
    """Variante senza RAG, selezionata esplicitamente prima della richiesta."""

    def __init__(self, dataset_path: Path = DEFAULT_DATASET, *, rag_root: Path = DEFAULT_RAG_ROOT) -> None:
        pass

    def retrieve(self, request: NormalizedRequest, compatibility: CompatibilityView, *, limit: int) -> tuple[RetrievedExample, ...]:
        return ()


class LocalReferenceContextRetriever:
    """Riferimento esaustivo esplicito; usa gli stessi divisori train verificati."""

    def __init__(self, dataset_path: Path = DEFAULT_DATASET, *, rag_root: Path = DEFAULT_RAG_ROOT) -> None:
        self.dataset_path = Path(dataset_path)
        self.rag_root = Path(rag_root)

    def retrieve(self, request: NormalizedRequest, compatibility: CompatibilityView, *, limit: int) -> tuple[RetrievedExample, ...]:
        corpus = load_corpus(self.dataset_path)
        verify_artifacts(self.rag_root / "index", corpus)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise ValueError("k deve essere un intero non negativo.")
        query = corpus.transform.apply(request.features)
        candidates = matching_records(corpus, devices=compatibility.available_device_ids,
                                      objective=request.figure_of_merit, experiment_id=EXPERIMENT_ID)
        ranked = [as_example(r, manhattan(query, corpus.transform.apply(record_features(r)))) for r in candidates]
        return tuple(sorted(ranked, key=lambda x: (x.distance, x.record_id))[:limit])

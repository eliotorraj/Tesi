"""Cinque esempi train uniformi, senza distanze o indice Qdrant."""
from __future__ import annotations
import hashlib
import random
import time
from uuid import uuid4
from common import digest

POLICY = {
    "revision": "random-examples-v1",
    "k": 5,
    "sampling": "uniform_without_replacement",
    "candidate_order": "rag_id_ascending",
    "example_order": "draw_order",
    "filters": "same experiment, train, objective, selected device compatible",
    "distance": "not_computed",
    "registry_distance_placeholder": 0.0,
    "seed_derivation": "sha256 canonical JSON of seed and UTF-8 source sha256",
}

def select_records(corpus, devices, objective, source_sha256, seed):
    from prototype.quantum_assistant.adapters.qdrant_context import matching_records
    from prototype.quantum_assistant.adapters.rag_dataset import EXPERIMENT_ID
    candidates = sorted(matching_records(corpus, devices=devices, objective=objective,
                                        experiment_id=EXPERIMENT_ID), key=lambda r: r["rag_id"])
    if len(candidates) < POLICY["k"]:
        raise ValueError("Servono almeno cinque esempi train compatibili.")
    derived = int(digest({"seed": seed, "source_sha256": source_sha256}), 16)
    chosen = random.Random(derived).sample(candidates, POLICY["k"])
    return chosen, {"seed": seed, "derived_seed": derived, "source_sha256": source_sha256,
                    "candidate_count": len(candidates),
                    "candidate_ids_sha256": digest([r["rag_id"] for r in candidates])}

def prepare_random(qasm, *, seed):
    from qiskit_dataset.catalog import load_catalog
    from prototype.quantum_assistant.adapters.hardware import MqtHardwareCatalog, HardwareMaskBuilder
    from prototype.quantum_assistant.adapters.request import QasmRequestParser, RequestSemanticValidator
    from prototype.quantum_assistant.adapters.context import StructuredEvidenceRegistryBuilder, StructuredPromptBuilder
    from prototype.quantum_assistant.adapters.rag_dataset import load_corpus, as_example
    from prototype.quantum_assistant.models import UiSubmission
    started = time.perf_counter()
    catalog = load_catalog()
    hardware = MqtHardwareCatalog(catalog.supported_device_ids, configuration_catalog=catalog).snapshot()
    parsed = QasmRequestParser().parse(UiSubmission(request_id=str(uuid4()), user_text="", qasm2=qasm))
    request = RequestSemanticValidator().normalize(parsed, hardware)
    mask = HardwareMaskBuilder().filter(request, hardware)
    if not mask.available_device_ids:
        raise ValueError("Nessun dispositivo compatibile.")
    rag_started = time.perf_counter()
    corpus = load_corpus()
    chosen, sampling = select_records(corpus, mask.available_device_ids, request.figure_of_merit,
                                     hashlib.sha256(qasm.encode("utf-8")).hexdigest(), seed)
    # Il registro comune richiede un numero finito: 0.0 e solo un segnaposto.
    # Non viene usato per ordinare e model_input lo omette. Il registro del
    # recupero dichiara distance=null e rende esplicita questa convenzione.
    examples = tuple(as_example(record, 0.0) for record in chosen)
    rag_seconds = time.perf_counter() - rag_started
    registry = StructuredEvidenceRegistryBuilder(configuration_catalog=catalog).build(examples)
    prompt = StructuredPromptBuilder(configuration_catalog=catalog).build(
        request, mask, examples, evidence_registry=registry)
    return request, prompt.payload, {
        "seconds": time.perf_counter()-started, "rag_seconds": rag_seconds,
        "policy": POLICY, **sampling, "dataset_sha256": corpus.source_sha256,
        "records": [{"example_id": f"E{i}", "rag_id": r["rag_id"],
                     "record_sha256": digest(r), "distance": None}
                    for i, r in enumerate(chosen, 1)],
    }

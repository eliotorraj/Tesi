"""Prepara, verifica e prova il recupero RAG senza LLM né compilazioni."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prototype.quantum_assistant.adapters.rag_dataset import DEFAULT_RAG_ROOT, load_corpus
from prototype.quantum_assistant.adapters.qdrant_context import prepare_index, verified_client, expected_manifest
from prototype.quantum_assistant.adapters.rag_checks import check_validation, prepare_prompt
from prototype.quantum_assistant.adapters.llm import UnconfiguredLlmGateway
from prototype.quantum_assistant.factory import build_default_service
from scripts.mqt_predictor_protocol import FROZEN_DEVICES
from qiskit_dataset.experiment_v2 import atomic_json_write


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify", "validation", "query"))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--backend", choices=("qdrant", "reference"), default="qdrant")
    parser.add_argument("--qasm", type=Path)
    parser.add_argument("--devices", nargs="+", choices=FROZEN_DEVICES)
    args = parser.parse_args()
    if args.k < 0:
        parser.error("--k deve essere non negativo.")
    if args.action == "query":
        if args.qasm is None:
            parser.error("query richiede --qasm.")
        service = build_default_service(device_names=FROZEN_DEVICES, llm_gateway=UnconfiguredLlmGateway(),
                                        retrieval_limit=args.k, retrieval_backend=args.backend)
        report = prepare_prompt(service, args.qasm, devices=args.devices)
        print(json.dumps(report, indent=2))
        return 0
    corpus = load_corpus(verify_features=True)
    if args.action == "prepare":
        report = prepare_index(corpus)
    else:
        with verified_client(DEFAULT_RAG_ROOT / "index", corpus):
            report = expected_manifest(corpus)
        if args.action == "validation":
            report = check_validation(corpus, limit=args.k)
            atomic_json_write(DEFAULT_RAG_ROOT / "validation_check.json", report)
        else:
            report = {"status": "verified", "manifest": report}
            atomic_json_write(DEFAULT_RAG_ROOT / "verification.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

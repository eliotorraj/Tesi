"""Ricerca reale Qdrant locale, precisione, persistenza e integrità train."""

from __future__ import annotations

import copy
from contextlib import closing
import json
import math
import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from qdrant_client import QdrantClient, models

from prototype.quantum_assistant.adapters.rag_features import (
    FEATURE_ORDER, FeatureTransform, RetrievalIntegrityError,
)
from prototype.quantum_assistant.adapters.rag_dataset import (
    COLLECTION_NAME, DEFAULT_DATASET, RagCorpus, point_id, record_features,
    strict_json, validate_records,
)
from prototype.quantum_assistant.adapters.qdrant_context import (
    LocalReferenceContextRetriever, QdrantContextRetriever, RetrievalDatabaseError,
    prepare_index, query_exact, verified_client, verify_artifacts, verify_collection,
)
from prototype.quantum_assistant.adapters.rag_checks import independent_rank
from prototype.quantum_assistant.schema_validation import ensure_supported_schema, validate_instance
from qiskit_dataset.experiment_v2 import source_manifest, stable_sha256
from scripts.mqt_predictor_protocol import EXPERIMENT_ID

DEVICE_A = "ibm_falcon_27"
DEVICE_B = "quantinuum_h2_56"


def features(**values):
    return {**dict.fromkeys(FEATURE_ORDER, 0.0), "num_qubits": 1.0, **values}


def corpus_for(rows, devices=None):
    devices = devices or [DEVICE_A] * len(rows)
    records = tuple({
        "rag_id": "rag_" + f"{i:064x}", "experiment_id": EXPERIMENT_ID,
        "split": "train", "view_scope": "global_multi_device",
        "objective": {"name": "expected_fidelity"},
        "retrieval_input": {
            "circuit": {"circuit_id": f"fixture_{i}", "source_sha256": f"{i:064x}", "features": {"values": row}},
            "compatible_devices": [{"device_id": devices[i]}],
        },
        "selected_device": {"device_id": devices[i]},
        "top_configurations": [], "claims": [], "evidence": [], "scientific_caveats": [],
    } for i, row in enumerate(rows))
    return RagCorpus(records, FeatureTransform.fit_train(rows), stable_sha256(records), {"fixture": "synthetic"})


class FeatureTransformTests(unittest.TestCase):
    def test_order_does_not_depend_on_json_keys(self):
        row = features(gate_count_cx=9, depth=4, liveness=0.5)
        transform = FeatureTransform.fit_train([row])
        self.assertEqual(transform.apply(row), transform.apply(dict(reversed(list(row.items())))))
        self.assertEqual(len(FEATURE_ORDER), 49)

    def test_zero_coordinates_constants_and_values_beyond_train(self):
        row = features(gate_count_h=9, depth=3, liveness=0.25)
        transform = FeatureTransform.fit_train([row, row])
        self.assertEqual(transform.divisors[FEATURE_ORDER.index("gate_count_cx")], 1)
        self.assertEqual(transform.apply(row)[FEATURE_ORDER.index("liveness")], 1)
        query = features(gate_count_h=99, depth=15, liveness=1)
        output = transform.apply(query)
        self.assertAlmostEqual(output[FEATURE_ORDER.index("gate_count_h")], 2)
        self.assertAlmostEqual(output[FEATURE_ORDER.index("depth")], 2)
        self.assertEqual(output[FEATURE_ORDER.index("liveness")], 4)
        self.assertEqual(transform.divisors[FEATURE_ORDER.index("liveness")], 0.25)
        self.assertGreater(sum(x*x for x in output), 1)

    def test_missing_extra_nonfinite_and_invalid_domains(self):
        invalid = [
            {k:v for k,v in features().items() if k != "depth"},
            {**features(), "label": 1},
            features(depth=float("nan")), features(depth=float("inf")),
            features(depth=-1), features(depth=0.5), features(depth=True),
            features(num_qubits=0), features(liveness=1.001), features(liveness=-0.1),
            features(gate_count_cx="1"), features(depth=10**400),
        ]
        for row in invalid:
            with self.subTest(row=row), self.assertRaises(RetrievalIntegrityError):
                FeatureTransform.fit_train([row])

    def test_strict_json_and_nullable_schema(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                strict_json(text)
        schema = {"type": "object", "maxProperties": 1,
                  "properties": {"a": {"type": ["number", "null"]}}}
        ensure_supported_schema(schema)
        self.assertFalse(validate_instance(schema, {"a": None}))
        self.assertTrue(validate_instance(schema, {"a": "bad"}))
        self.assertTrue(validate_instance(schema, {"a": 1, "extra": 2}))


class RealLocalQdrantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        rng = random.Random(42)
        rows = [features(depth=rng.randrange(20), gate_count_h=rng.randrange(30),
                         gate_count_cx=rng.randrange(10), liveness=rng.random()) for _ in range(12)]
        self.corpus = corpus_for(rows, [DEVICE_A, DEVICE_B] * 6)
        prepare_index(self.corpus, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def search(self, client, row, **options):
        return query_exact(client, self.corpus, row, devices=options.pop("devices", (DEVICE_A, DEVICE_B)),
                           objective=options.pop("objective", "expected_fidelity"), limit=options.pop("limit", 5), **options)

    def test_exact_results_filters_k_and_independent_distances(self):
        with verified_client(self.root / "index", self.corpus) as client:
            for devices in ((DEVICE_A,), (DEVICE_B,), (DEVICE_A, DEVICE_B)):
                for limit in (0, 1, 5, 99):
                    row = features(depth=100, gate_count_h=90, liveness=0.7)
                    actual = self.search(client, row, devices=devices, limit=limit)
                    expected = independent_rank(self.corpus, row, devices, limit=limit)
                    self.assertEqual([(x.distance, x.record_id) for x in actual], expected)

    def test_zero_candidates_are_not_database_failure(self):
        with verified_client(self.root / "index", self.corpus) as client:
            for options in ({"devices": ()}, {"devices": ("no-device",)},
                            {"objective": "other"}, {"experiment_id": "other"}):
                self.assertEqual(self.search(client, features(), **options), ())

    def test_idempotence_reopening_and_reference_adapter(self):
        before = (self.root / "index/manifest.json").read_bytes()
        prepare_index(self.corpus, self.root)
        self.assertEqual(before, (self.root / "index/manifest.json").read_bytes())
        request = SimpleNamespace(features=features(depth=9), figure_of_merit="expected_fidelity")
        mask = SimpleNamespace(available_device_ids=(DEVICE_A, DEVICE_B))
        with patch("prototype.quantum_assistant.adapters.qdrant_context.load_corpus", return_value=self.corpus):
            qdrant = QdrantContextRetriever(rag_root=self.root)
            reference = LocalReferenceContextRetriever(rag_root=self.root)
            self.assertEqual(qdrant.retrieve(request, mask, limit=5), reference.retrieve(request, mask, limit=5))
            self.assertEqual(qdrant.retrieve(request, mask, limit=5), reference.retrieve(request, mask, limit=5))

    def test_ties_crossing_top_k_use_original_rag_id(self):
        corpus = corpus_for([features(depth=2)] * 9)
        corpus = replace(corpus, records=tuple(reversed(corpus.records)))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_index(corpus, root)
            with verified_client(root / "index", corpus) as client:
                found = query_exact(client, corpus, features(depth=2), devices=(DEVICE_A,), objective="expected_fidelity", limit=5)
            self.assertEqual([x.record_id for x in found], sorted(r["rag_id"] for r in corpus.records)[:5])
            self.assertEqual([x.distance for x in found], [0] * 5)

    def test_float32_near_ties_are_refined_before_top_k(self):
        corpus = corpus_for([features(liveness=0.5 + 1e-9), features(liveness=0.5), features(liveness=1)])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_index(corpus, root)
            with verified_client(root / "index", corpus) as client:
                found = query_exact(client, corpus, features(), devices=(DEVICE_A,), objective="expected_fidelity", limit=1)
            self.assertEqual(found[0].record_id, corpus.records[1]["rag_id"])

    def test_deleted_point_and_repeat_indexing_fail_closed(self):
        with closing(QdrantClient(path=str(self.root / "index/qdrant"))) as client:
            client.delete(COLLECTION_NAME, models.PointIdsList(points=[point_id(self.corpus.records[0]["rag_id"])]))
        with self.assertRaises(RetrievalIntegrityError):
            prepare_index(self.corpus, self.root)

    def test_tampered_vector_payload_and_residual_collection(self):
        for kind in ("vector", "payload", "extra_collection"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                prepare_index(self.corpus, root)
                with closing(QdrantClient(path=str(root / "index/qdrant"))) as client:
                    identifier = point_id(self.corpus.records[0]["rag_id"])
                    if kind == "vector":
                        client.update_vectors(COLLECTION_NAME, [models.PointVectors(id=identifier, vector=[0.1]*49)])
                    elif kind == "payload":
                        client.set_payload(COLLECTION_NAME, {"split": "validation"}, [identifier])
                    else:
                        client.create_collection("residue", vectors_config=models.VectorParams(size=49, distance=models.Distance.MANHATTAN))
                with self.assertRaises(RetrievalIntegrityError):
                    with verified_client(root / "index", self.corpus):
                        pass

    def test_tampered_divisor_even_with_new_self_hash_is_rejected(self):
        path = self.root / "index/transform.json"
        value = json.loads(path.read_text())
        value["divisors"][0] += 1
        value["sha256"] = stable_sha256({k:v for k,v in value.items() if k != "sha256"})
        path.write_text(json.dumps(value))
        with self.assertRaises(RetrievalIntegrityError):
            verify_artifacts(self.root / "index", self.corpus)

    def test_wrong_experiment_manifest_or_source_is_rejected(self):
        path = self.root / "index/manifest.json"
        value = json.loads(path.read_text())
        value["experiment_id"] = "other-experiment"
        path.write_text(json.dumps(value))
        with self.assertRaises(RetrievalIntegrityError):
            verify_artifacts(self.root / "index", self.corpus)

    def test_database_lock_is_an_error_even_with_zero_compatible_examples(self):
        with closing(QdrantClient(path=str(self.root / "index/qdrant"))):
            with self.assertRaises(RetrievalDatabaseError):
                with verified_client(self.root / "index", self.corpus):
                    pass

    def test_wrong_dimension_or_distance_is_rejected(self):
        for dimension, distance in ((48, models.Distance.MANHATTAN), (49, models.Distance.COSINE)):
            with closing(QdrantClient(":memory:")) as client:
                client.create_collection(COLLECTION_NAME, vectors_config=models.VectorParams(size=dimension, distance=distance))
                with self.assertRaises(RetrievalIntegrityError):
                    verify_collection(client, self.corpus)

    def test_corrupt_query_response_fails_instead_of_falling_back(self):
        with verified_client(self.root / "index", self.corpus) as client:
            original = client.query_points
            for mode in ("missing", "distance"):
                def changed(*args, **kwargs):
                    response = original(*args, **kwargs)
                    if mode == "missing":
                        response.points = response.points[:-1]
                    else:
                        response.points[0].score += 1.0
                    return response
                with self.subTest(mode=mode), patch.object(client, "query_points", side_effect=changed):
                    with self.assertRaises(RetrievalIntegrityError):
                        self.search(client, features())

    def test_query_rejects_missing_and_nonfinite_features(self):
        with verified_client(self.root / "index", self.corpus) as client:
            for row in ({}, features(liveness=float("nan"))):
                with self.assertRaises(RetrievalIntegrityError):
                    self.search(client, row)

    def test_runtime_version_must_match_lock(self):
        with patch("prototype.quantum_assistant.adapters.qdrant_context.version", return_value="0.0.0"):
            with self.assertRaisesRegex(RetrievalIntegrityError, "uv.lock"):
                verify_artifacts(self.root / "index", self.corpus)

    def test_missing_database_does_not_create_an_empty_replacement(self):
        database = self.root / "index/qdrant"
        database.rename(self.root / "saved_database")
        with self.assertRaises(RetrievalIntegrityError):
            with verified_client(self.root / "index", self.corpus):
                pass
        self.assertFalse(database.exists())


@unittest.skipUnless(DEFAULT_DATASET.is_file(), "Dataset generato non presente su questa macchina")
class DatasetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with DEFAULT_DATASET.open() as handle:
            cls.record = json.loads(next(handle))
        cls.manifest = source_manifest()

    def test_frozen_manifest_cannot_be_repartitioned(self):
        from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
        with patch("prototype.quantum_assistant.adapters.rag_dataset.file_sha256", return_value="0"*64):
            with self.assertRaisesRegex(RetrievalIntegrityError, "congelato"):
                load_corpus()

    def test_current_record_and_duplicate_source_detection(self):
        validate_records([copy.deepcopy(self.record)], self.manifest)
        duplicate = copy.deepcopy(self.record)
        duplicate["rag_id"] = "rag_" + "f"*64
        with self.assertRaises(RetrievalIntegrityError):
            validate_records([self.record, duplicate], self.manifest)

    def test_validation_test_identity_and_evidence_tampering(self):
        for mode in ("split", "test_hash", "validation_hash", "experiment", "id", "source_ref", "feature", "evidence"):
            row = copy.deepcopy(self.record)
            circuit = row["retrieval_input"]["circuit"]
            if mode == "split": row["split"] = "validation"
            elif mode.endswith("_hash"):
                split = mode.removesuffix("_hash")
                circuit["source_sha256"] = next(x["source_sha256"] for x in self.manifest["circuits"] if x["split"] == split)
            elif mode == "experiment": row["experiment_id"] = "other"
            elif mode == "id": circuit["circuit_id"] = "other"
            elif mode == "source_ref": circuit["source_ref"] = "../test/file.qasm"
            elif mode == "feature": circuit["features"]["values"]["depth"] = float("nan")
            elif mode == "evidence": row["evidence"][0]["aggregation"]["value"] += 0.1
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate_records([row], self.manifest)


class ValidationGateTests(unittest.TestCase):
    def test_report_requires_all_validation_circuits_and_matching_index(self):
        from prototype.quantum_assistant.adapters.rag_checks import validate_validation_report
        circuits = [{"circuit_id": str(i), "source_sha256": f"{i:064x}", "split": "validation"} for i in range(88)]
        report = {
            "status": "passed", "experiment_id": EXPERIMENT_ID, "validation_count": 88,
            "k": 5, "index_manifest_sha256": "index", "transform_sha256": "transform",
            "llm_calls": 0, "compilations": 0, "test_accessed": False,
            "rows": [{**r, "status": "prepared", "examples": [], "registry_count": 0,
                      "prompt_sha256": "prompt", "registry_sha256": "registry"} for r in circuits],
        }
        index = {"sha256": "index", "transform_sha256": "transform"}
        validate_validation_report(report, index, {"circuits": circuits})
        for mode in ("missing", "duplicate", "index", "registry"):
            changed = copy.deepcopy(report)
            if mode == "missing": changed["rows"].pop()
            elif mode == "duplicate": changed["rows"][0] = changed["rows"][1]
            elif mode == "index": changed["index_manifest_sha256"] = "wrong"
            elif mode == "registry": changed["rows"][0]["registry_count"] = 1
            with self.subTest(mode=mode), self.assertRaises(RetrievalIntegrityError):
                validate_validation_report(changed, index, {"circuits": circuits})


if __name__ == "__main__":
    unittest.main()

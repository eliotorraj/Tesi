"""Controlla che la copia di consultazione rilevi modifiche reali ai dati."""
import importlib.util
import math
import unittest
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient, models

spec = importlib.util.spec_from_file_location(
    "qdrant_dashboard", Path(__file__).resolve().parents[1] / "scripts/18_qdrant_dashboard.py",
)
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)


class DashboardCopyTests(unittest.TestCase):
    def test_json_rounding_is_limited_to_two_ulps(self):
        original = 0.9897168798333333
        rounding = []
        self.assertTrue(dashboard.matching_payload(
            {"score": original}, {"score": math.nextafter(original, 0)}, rounding,
        ))
        self.assertEqual(len(rounding), 1)
        self.assertFalse(dashboard.matching_payload(
            {"score": original}, {"score": original + 1e-8}, [],
        ))

    def test_metadata_and_structure_require_exact_match(self):
        a = {"id": "train-1", "count": 3, "values": [0.5]}
        for b in (
            {**a, "id": "test-1"}, {**a, "count": 3.0},
            {**a, "values": []}, {**a, "extra": True},
        ):
            with self.subTest(b=b):
                self.assertFalse(dashboard.matching_payload(a, b, []))

    def test_checks_detect_missing_points_and_payload_or_vector_changes(self):
        with self.subTest("real local collection"):
            client = QdrantClient(":memory:")
            self.addCleanup(client.close)
            client.create_collection(
                dashboard.COLLECTION_NAME,
                vectors_config=models.VectorParams(size=49, distance=models.Distance.MANHATTAN),
            )
            vector = np.full(49, 0.5, dtype=np.float32).tolist()
            payload = {"split": "train", "score": 0.5}
            original = [models.Record(id=1, vector=vector, payload=payload)]
            with self.assertRaises(RuntimeError):
                dashboard.verify_copy(client, original)
            client.upsert(dashboard.COLLECTION_NAME, [models.PointStruct(id=1, vector=vector, payload=payload)])
            self.assertEqual(dashboard.verify_copy(client, original), [])
            client.set_payload(dashboard.COLLECTION_NAME, {"split": "test"}, [1])
            with self.assertRaises(RuntimeError):
                dashboard.verify_copy(client, original)
            client.upsert(dashboard.COLLECTION_NAME, [models.PointStruct(id=1, vector=[0.6] * 49, payload=payload)])
            with self.assertRaises(RuntimeError):
                dashboard.verify_copy(client, original)


if __name__ == "__main__":
    unittest.main()

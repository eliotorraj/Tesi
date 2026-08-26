from __future__ import annotations

import json
import unittest

from qiskit_dataset.aggregation import aggregate_device_datasets
from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.core import dataset_scope_root, sha256_file


class GlobalDatasetAggregationTests(unittest.TestCase):
    @staticmethod
    def _mini_dataset_snapshot(scope_root, device_ids) -> dict[str, str]:
        return {
            str(path.relative_to(scope_root)): sha256_file(path)
            for device_id in device_ids
            for path in sorted((scope_root / device_id).rglob("*"))
            if path.is_file()
        }

    def test_pilot_check_only_reads_every_mini_dataset_without_mutation(
        self,
    ) -> None:
        catalog = load_catalog()
        scope_root = dataset_scope_root("expected_fidelity", "pilot")
        before = self._mini_dataset_snapshot(
            scope_root,
            catalog.supported_device_ids,
        )
        statistics = aggregate_device_datasets(
            "pilot",
            catalog,
            top_k=3,
            require_all_supported=True,
            write=False,
        )
        after = self._mini_dataset_snapshot(
            scope_root,
            catalog.supported_device_ids,
        )

        self.assertEqual(before, after)
        self.assertFalse(statistics["mini_datasets_modified"])
        self.assertEqual(
            statistics["source_device_ids"],
            list(catalog.supported_device_ids),
        )
        self.assertEqual(statistics["counts"]["runs"], 1584)
        self.assertEqual(
            statistics["counts"]["configuration_aggregates"],
            528,
        )
        self.assertEqual(statistics["counts"]["rag_examples"], 6)

    def test_committed_global_rag_links_claims_to_raw_scientific_evidence(
        self,
    ) -> None:
        scope_root = dataset_scope_root("expected_fidelity", "pilot")
        global_root = scope_root / "global"

        def read_jsonl(name: str) -> list[dict[str, object]]:
            return [
                json.loads(line)
                for line in (global_root / name).read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            ]

        runs = read_jsonl("qiskit_runs.jsonl")
        summaries = read_jsonl("qiskit_configuration_aggregates.jsonl")
        examples = read_jsonl("rag_examples.jsonl")
        run_by_id = {str(run["run_id"]): run for run in runs}
        summary_by_id = {
            str(summary["summary_id"]): summary for summary in summaries
        }

        self.assertEqual(len(examples), 6)
        self.assertTrue(
            all(summary["schema_version"] == "2.0.0" for summary in summaries)
        )
        for example in examples:
            self.assertEqual(example["schema_version"], "2.0.0")
            self.assertEqual(example["split"], "train")
            self.assertEqual(len(example["top_configurations"]), 3)
            compatible_ids = {
                device["device_id"]
                for device in example["retrieval_input"]["compatible_devices"]
            }
            selected_device = example["selected_device"]
            self.assertIn(selected_device["device_id"], compatible_ids)
            self.assertTrue(selected_device["selection_reason"])
            self.assertIn(
                selected_device["best_config_id"],
                selected_device["tied_best_config_ids"],
            )

            circuit = example["retrieval_input"]["circuit"]
            source_path = scope_root / circuit["source_ref"]
            self.assertTrue(source_path.is_file())
            self.assertEqual(sha256_file(source_path), circuit["source_sha256"])

            evidence_by_id = {
                str(item["evidence_id"]): item
                for item in example["evidence"]
            }
            for claim in example["claims"]:
                self.assertTrue(str(claim["text"]).strip())
                self.assertLessEqual(
                    set(claim["evidence_ids"]),
                    set(evidence_by_id),
                )
            claims_by_id = {
                str(claim["claim_id"]): claim for claim in example["claims"]
            }
            for configuration in example["top_configurations"]:
                self.assertIn(
                    configuration["config_id"],
                    configuration["tied_score_config_ids"],
                )
                if len(configuration["tied_score_config_ids"]) > 1:
                    self.assertIn(
                        "non dimostra superiorità",
                        claims_by_id[str(configuration["claim_id"])]["text"],
                    )
            for evidence in evidence_by_id.values():
                summary = summary_by_id[str(evidence["summary_id"])]
                self.assertEqual(
                    set(evidence["run_ids"]),
                    set(summary["run_ids"]),
                )
                for observation in evidence["stability"]["observations"]:
                    run = run_by_id[str(observation["run_id"])]
                    self.assertEqual(run["status"], "success")
                    self.assertEqual(
                        observation["seed_transpiler"],
                        run["seed_transpiler"],
                    )
                    self.assertEqual(observation["score"], run["score"])

        statistics = json.loads(
            (global_root / "dataset_statistics.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            statistics["record_schema_versions"],
            {
                "manifest": "2.0.0",
                "run": "1.0.0",
                "configuration_aggregate": "2.0.0",
                "rag_example": "2.0.0",
            },
        )


if __name__ == "__main__":
    unittest.main()

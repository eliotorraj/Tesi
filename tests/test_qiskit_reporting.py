from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from qiskit_dataset.catalog import DEFAULT_CATALOG_PATH, load_catalog
from qiskit_dataset.core import atomic_json_write, atomic_jsonl_write, sha256_file
from qiskit_dataset.reporting import (
    _timeout_sensitivity,
    build_dataset_report,
    build_device_comparison,
    build_pilot_report,
)
from qiskit_dataset.views import build_dataset_views


class QiskitReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        original = load_catalog()
        self.catalog = replace(
            original, seeds=(0,), configurations=original.configurations[:1]
        )

    def make_device(self, device_id: str, *, scope: str = "full", timeout: int = 300, workers: int = 2):
        device_root = self.root / scope / device_id
        circuit = {
            "circuit_id": "example", "split": "train", "benchmark_family": "test",
            "generator": "test", "num_qubits": 2, "depth": 2, "size": 3,
        }
        configuration = self.catalog.configurations[0].to_dict()
        manifest = {
            "dataset_scope": scope, "device_id": device_id, "device_num_qubits": 27,
            "circuits": [circuit], "counts": {"compatible_circuits": 1, "attempts_planned": 1},
            "objective": {"name": "expected_fidelity"},
        }
        run = {
            "run_id": f"run_{device_id}", "circuit": circuit, "configuration": configuration,
            "device": {"device_id": device_id, "num_qubits": 27}, "seed_transpiler": 0,
            "status": "success", "timings_seconds": {"transpilation": 2.0, "total": 3.0},
            "provenance": {"execution_policy": {"workers": workers, "timeout_seconds": timeout}},
        }
        summary = {
            "circuit": circuit, "configuration": configuration, "eligible_for_ranking": True,
            "ranking_score": 0.9, "rank": 1, "attempts": {"complete": True},
            "score_statistics": {"median": 0.9},
        }
        atomic_json_write(device_root / "split_manifest.json", manifest)
        atomic_jsonl_write(device_root / "qiskit_runs.jsonl", [run])
        atomic_jsonl_write(device_root / "qiskit_configuration_aggregates.jsonl", [summary])
        atomic_jsonl_write(device_root / "rag_examples.jsonl", [])
        # The latest invocation can differ from the original cached attempts.
        atomic_json_write(device_root / "generation_status.json", {
            "execution_policy": {"workers": 6, "timeout_seconds": 100}, "cache_hits": 1,
        })
        return device_root, manifest, run, summary

    def test_full_views_write_the_same_report_types_as_pilot(self) -> None:
        device = self.catalog.supported_device_ids[0]
        output_root, manifest, _, summary = self.make_device(device)
        with (
            patch("qiskit_dataset.views.dataset_scope_root", return_value=output_root),
            patch("qiskit_dataset.views.load_manifest", return_value=manifest),
            patch("qiskit_dataset.views._load_target_record", return_value={}),
            patch("qiskit_dataset.views.aggregate_runs", return_value=[summary]),
            patch("qiskit_dataset.views.build_rag_examples", return_value=[]),
        ):
            statistics = build_dataset_views("full", self.catalog, device_id=device)
        for filename in (
            "full_report.md", "full_summary.json", "configuration_statistics.csv",
            "circuit_statistics.csv", "failure_details.csv",
        ):
            self.assertTrue((output_root / "reports" / filename).is_file(), filename)
        self.assertEqual(statistics["outputs"]["full_report"], "reports/full_report.md")
        self.assertTrue((output_root.parent / "device_comparison.csv").is_file())
        self.assertTrue((output_root.parent / "device_comparison.md").is_file())
        report = json.loads((output_root / "reports/full_summary.json").read_text())
        self.assertEqual(report["execution"]["timeout_seconds"], 300)
        self.assertEqual(report["execution"]["workers"], 2)
        self.assertEqual(report["execution"]["last_invocation_policy"]["timeout_seconds"], 100)
        self.assertEqual(report["execution"]["policy_source"], "run_provenance")

    def test_pilot_keeps_original_report_names(self) -> None:
        output_root, _, _, _ = self.make_device(self.catalog.device_id, scope="pilot")
        report = build_pilot_report(output_root, self.catalog)
        self.assertTrue((output_root / "reports/pilot_report.md").is_file())
        self.assertTrue((output_root / "reports/pilot_summary.json").is_file())
        self.assertEqual(report["summary"]["report_type"], "qiskit_pilot")
        self.assertFalse((output_root / "reports/full_report.md").exists())

    def test_comparison_uses_selected_sources_without_mutating_them(self) -> None:
        devices = self.catalog.supported_device_ids[:2]
        first, _, _, _ = self.make_device(devices[0])
        second, _, _, _ = self.make_device(devices[1], timeout=100, workers=6)
        sources = [path for root in (first, second) for path in root.rglob("*") if path.is_file()]
        before = {str(path): sha256_file(path) for path in sources}
        destination = self.root / "full/global/reports"
        result = build_device_comparison(
            self.root / "full", scope="full", catalog=self.catalog,
            device_ids=devices, output_root=destination,
        )
        self.assertEqual(result["devices"], 2)
        self.assertEqual(result["common_circuit_ids"], ["example"])
        with (destination / "device_comparison.csv").open() as handle:
            rows = {row["device_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows[devices[0]]["timeout_seconds"], "300")
        self.assertEqual(rows[devices[1]]["timeout_seconds"], "100")
        self.assertIn("non sono un confronto a parità di condizioni", (destination / "device_comparison.md").read_text())
        self.assertEqual(before, {str(path): sha256_file(path) for path in sources})
        self.assertFalse((first / "reports").exists())
        self.assertFalse((second / "reports").exists())

    def test_mixed_execution_policies_are_not_reported_as_one_timeout(self) -> None:
        output_root, _, run, _ = self.make_device(self.catalog.device_id)
        other = {**run, "run_id": "other", "provenance": {"execution_policy": {"timeout_seconds": 100, "workers": 6}}}
        atomic_jsonl_write(output_root / "qiskit_runs.jsonl", [run, other])
        report = build_dataset_report(output_root, self.catalog)
        execution = report["summary"]["execution"]
        self.assertIsNone(execution["timeout_seconds"])
        self.assertIsNone(execution["workers"])
        self.assertEqual(execution["observed_timeout_seconds"], [100, 300])
        self.assertTrue(execution["mixed_execution_policies"])
        self.assertIn("parametri di esecuzione diversi", (output_root / "reports/full_report.md").read_text())

    def test_timeout_at_100_is_unknown_at_300(self) -> None:
        rows = _timeout_sensitivity([
            {"status": "timeout", "failure": {"timeout_seconds": 100}},
            {"status": "timeout", "failure": {"timeout_seconds": 300}},
            {"status": "success", "timings_seconds": {"total": 150}},
        ])
        by_threshold = {row["threshold_seconds"]: row for row in rows}
        self.assertEqual(by_threshold[100]["lower_bound_timeouts_if_threshold_used"], 3)
        self.assertEqual(by_threshold[300]["lower_bound_timeouts_if_threshold_used"], 1)
        self.assertEqual(by_threshold[300]["timeouts_with_unknown_outcome_at_threshold"], 1)
        self.assertEqual(by_threshold[600]["lower_bound_timeouts_if_threshold_used"], 0)

    def test_cli_full_defaults_to_v2_and_preserves_explicit_catalog(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        for filename in ("09_build_qiskit_dataset_views.py", "10_aggregate_qiskit_dataset.py"):
            with self.subTest(script=filename):
                spec = importlib.util.spec_from_file_location("reporting_cli", project_root / "scripts" / filename)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                with patch("sys.argv", [filename, "--scope", "full"]):
                    args = module.parse_args()
                self.assertEqual(args.catalog, project_root / "configs/qiskit_dataset_configurations_v2.json")
                with patch("sys.argv", [filename, "--scope", "pilot"]):
                    self.assertEqual(module.parse_args().catalog, DEFAULT_CATALOG_PATH)
                with patch("sys.argv", [filename, "--scope", "full", "--catalog", "custom.json"]):
                    self.assertEqual(module.parse_args().catalog, Path("custom.json"))


if __name__ == "__main__":
    unittest.main()

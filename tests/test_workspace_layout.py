from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qiskit_dataset.catalog import DEFAULT_CATALOG_PATH, LEGACY_CATALOG_PATH, load_catalog
from qiskit_dataset.core import dataset_scope_root
from scripts import mqt_predictor_protocol as protocol


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def script_module(filename: str):
    spec = importlib.util.spec_from_file_location("layout_cli", PROJECT_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkspaceLayoutTests(unittest.TestCase):
    def test_all_qiskit_commands_default_to_current_full_experiment(self) -> None:
        self.assertEqual(load_catalog().experiment_id, protocol.EXPERIMENT_ID)
        for filename in (
            "07_prepare_qiskit_dataset.py", "08_generate_qiskit_dataset.py",
            "09_build_qiskit_dataset_views.py", "10_aggregate_qiskit_dataset.py",
        ):
            with self.subTest(filename=filename):
                module = script_module(filename)
                with patch("sys.argv", [filename]):
                    args = module.parse_args()
                self.assertEqual(args.scope, "full")
                self.assertEqual(args.catalog, DEFAULT_CATALOG_PATH)
                with patch("sys.argv", [filename, "--scope", "pilot", "--catalog", str(LEGACY_CATALOG_PATH)]):
                    args = module.parse_args()
                self.assertEqual(args.catalog, LEGACY_CATALOG_PATH)
                self.assertIsNone(load_catalog(args.catalog).experiment_id)

    def test_legacy_and_current_storage_are_separate(self) -> None:
        legacy = dataset_scope_root("expected_fidelity", "full")
        current = dataset_scope_root("expected_fidelity", "full", experiment_id=protocol.EXPERIMENT_ID)
        self.assertTrue(legacy.is_relative_to(PROJECT_ROOT / "archivio"))
        self.assertTrue(current.is_relative_to(PROJECT_ROOT / "datasets" / "experiments"))
        self.assertFalse((PROJECT_ROOT / "datasets" / "expected_fidelity").exists())
        self.assertFalse((PROJECT_ROOT / "artifacts" / "qiskit_dataset_cache").exists())

    def test_frozen_source_references_round_trip_without_rewriting_manifest(self) -> None:
        original_bytes = protocol.LEGACY_SOURCE_MANIFEST.read_bytes()
        source = json.loads(original_bytes)
        record = next(item for item in source["circuits"] if item["split"] == "train")
        logical = "datasets/expected_fidelity/full/" + record["source_ref"]
        resolved = protocol.resolve_source_reference(logical)
        self.assertTrue(resolved.is_relative_to(protocol.LEGACY_DATASET_ROOT))
        self.assertEqual(protocol.file_sha256(resolved), record["source_sha256"])
        self.assertEqual(protocol.frozen_source_reference(resolved), logical)
        self.assertEqual(protocol.resolve_source_reference(resolved.relative_to(PROJECT_ROOT).as_posix()), resolved)
        self.assertEqual(protocol.LEGACY_SOURCE_MANIFEST.read_bytes(), original_bytes)
        self.assertEqual(protocol.file_sha256(protocol.LEGACY_SOURCE_MANIFEST), protocol.LEGACY_SOURCE_MANIFEST_SHA256)

    def test_materialization_reads_archived_sources_and_rejects_modified_copies(self) -> None:
        prepare = script_module("06_prepare_experiment_v2.py")
        source = json.loads(protocol.LEGACY_SOURCE_MANIFEST.read_text())
        record = dict(next(item for item in source["circuits"] if item["split"] == "train"))
        record["source_ref"] = "datasets/expected_fidelity/full/" + record["source_ref"]
        manifest = {"circuits": [record]}
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "train"
            self.assertEqual(prepare.materialize_split(manifest, "train", destination), 1)
            copied = destination / record["file_name"]
            self.assertEqual(protocol.file_sha256(copied), record["source_sha256"])
            self.assertEqual(prepare.materialize_split(manifest, "train", destination), 1)
            copied.write_text("modified")
            with self.assertRaisesRegex(RuntimeError, "incoerente"):
                prepare.materialize_split(manifest, "train", destination)

    def test_relocation_rejects_traversal_and_symlink_escape(self) -> None:
        for reference in ("../outside.qasm", "/tmp/outside.qasm", "datasets/expected_fidelity/../../../outside.qasm"):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                protocol.resolve_source_reference(reference)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "archivio"
            archive.mkdir()
            (root / "outside.qasm").write_text("outside corpus")
            (archive / "escape.qasm").symlink_to(root / "outside.qasm")
            with patch.object(protocol, "PROJECT_ROOT", root), patch.object(protocol, "LEGACY_DATASET_ROOT", archive):
                with self.assertRaises(ValueError):
                    protocol.resolve_source_reference("datasets/expected_fidelity/escape.qasm")


if __name__ == "__main__":
    unittest.main()

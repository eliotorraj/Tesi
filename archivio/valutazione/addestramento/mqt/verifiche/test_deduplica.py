"""Controlli di selezione per contenuto, alias, copertura e array ML."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deduplica import select_unique, validate_training_names, validate_selection_metadata

class DedupTests(unittest.TestCase):
    def test_aliases_are_byte_identical_and_representative_is_stable(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            for name, content in [("z", "same"), ("a", "same"), ("b", "same\n")]:
                (p/f"{name}.qasm").write_text(content)
            sources, selection = select_unique(p, frozen=False)
            self.assertEqual(set(sources), {"a", "b"})
            self.assertEqual(selection["alias_count"], 1)
            self.assertEqual([g["aliases"] for g in selection["groups"] if g["representative"]=="a"], [["z"]])
            self.assertEqual(selection, select_unique(p, frozen=False)[1])
            self.assertEqual(len(list(p.glob("*.qasm"))), 3)
            with self.assertRaises(ValueError):
                select_unique(p)

    def test_arrays_reject_duplicates_aliases_and_missing_rows(self):
        validate_training_names(["b", "a"], ["a", "b"])
        for names in (["a", "a"], ["a"], ["a", "alias"]):
            with self.assertRaises(ValueError):
                validate_training_names(names, ["a", "b"])

    def test_frozen_train_and_compatible_jobs(self):
        import motore_ml as t
        sources, selection = select_unique(t.TRAINING_CIRCUITS_V2)
        self.assertEqual(selection["source_circuit_count"], 422)
        self.assertEqual(len(sources), 396)
        self.assertEqual(selection["alias_count"], 26)
        self.assertEqual(len({g["sha256"] for g in selection["groups"]}), 396)
        with tempfile.TemporaryDirectory() as d:
            jobs, selected = t.build_jobs(t.TRAINING_CIRCUITS_V2, Path(d), list(t.FROZEN_DEVICES), "expected_fidelity")
            self.assertEqual(set(selected), set(sources))
            self.assertEqual(len({j.key for j in jobs}), len(jobs))
            complete, missing = t.coverage_report(jobs, selected, {j.key for j in jobs})
            self.assertEqual(len(complete), 396)
            self.assertEqual(missing, [])
            print(f"VERIFICA: 422 sorgenti, 396 hash, 26 alias, {len(jobs)} coppie compatibili; selezione {selection['sha256']}")
        metadata = dict(training_sample_count=396, training_selection=selection)
        self.assertEqual(validate_selection_metadata(metadata, t.TRAINING_CIRCUITS_V2), [])
        self.assertTrue(validate_selection_metadata({}, t.TRAINING_CIRCUITS_V2))
        metadata["training_sample_count"] = 422
        self.assertTrue(validate_selection_metadata(metadata, t.TRAINING_CIRCUITS_V2))

if __name__ == "__main__":
    unittest.main()

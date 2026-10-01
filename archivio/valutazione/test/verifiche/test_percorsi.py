"""Riorganizzazione: percorsi reali, identita logiche e contratti immutabili."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

AREA = Path(__file__).resolve().parents[1]
EVALUATION = AREA.parent
sys.path.insert(0, str(AREA / "strumenti"))
import gates


class PercorsiTest(unittest.TestCase):
    def load_common(self, name):
        path = EVALUATION / name / "strumenti/common.py"
        spec = importlib.util.spec_from_file_location("paths_" + name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_runtime_and_experimental_paths_are_separate(self):
        for name in ("test", "test_mqt_esplorativo"):
            with self.subTest(area=name):
                common = self.load_common(name)
                self.assertEqual(common.AREA, EVALUATION / name)
                self.assertEqual(common.ROOT, common.REPO / "prototipo")
                self.assertEqual(common.ARCHIVE, common.REPO / "archivio/esperimento_v2")
                self.assertTrue((common.ROOT / "app.py").is_file())
                self.assertTrue(common.PLAN.is_file())
                self.assertTrue(common.SOURCE.is_file())

    def test_hash_keys_preserve_legacy_identity_across_locations(self):
        for name in ("test", "test_mqt_esplorativo"):
            with self.subTest(area=name), tempfile.TemporaryDirectory() as temp:
                common = self.load_common(name)
                repo = Path(temp)
                runtime = repo / "prototipo"
                evaluation = repo / "archivio/valutazione"
                area = evaluation / name
                inputs = {
                    runtime / "app.py": "runtime",
                    runtime / "schemas/request.json": "{}",
                    area / "piano.json": "{}",
                    area / "strumenti/runner.py": "runner",
                    evaluation / "addestramento/mqt/motore_ml.py": "trainer",
                }
                for path, value in inputs.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(value)
                with patch.multiple(common, ROOT=runtime, EVALUATION=evaluation,
                                    AREA=area, PLAN=area / "piano.json"):
                    hashes = common.code_files()
                self.assertEqual(set(hashes), {
                    "app.py", "schemas/request.json", name + "/piano.json",
                    name + "/strumenti/runner.py", "addestramento/mqt/motore_ml.py",
                })
                self.assertEqual(hashes[name + "/strumenti/runner.py"], common.sha(area / "strumenti/runner.py"))

    def test_changed_code_cannot_resume_or_rewrite_frozen_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            area = Path(temp)
            path = area / "preparazione/contratto_congelato.json"
            original = {"code": {"test/strumenti/runner.py": "original"}}
            gates.save(path, original)
            before = path.read_bytes()
            changed = {"code": {"test/strumenti/runner.py": "changed"}}
            with patch.object(gates, "AREA", area), patch.object(gates, "frozen_contract", return_value=changed):
                with self.assertRaisesRegex(ValueError, "Contratto cambiato"):
                    gates.freeze()
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

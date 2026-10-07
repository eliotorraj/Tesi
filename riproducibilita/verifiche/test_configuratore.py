"""Isolated configurator checks without weights, training or a real LLM server.

Run from riproducibilita/: python -B -m unittest discover -s verifiche -p test_configuratore.py -v"""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
from unittest import mock
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comune import configuratore as c
from comune.configuratore_cli import main


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ripro-config-")
        self.root = Path(self.tmp.name)
        self.original = c.KIT
        for relative in ("configurazioni/esperimento.json", "configurazioni/catalogo.json", "modelli_llm/modelli.json"):
            dest = self.root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((self.original / relative).read_bytes())
        self.kit = mock.patch.object(c, "KIT", self.root)
        self.named = mock.patch.object(c, "NAMED", self.root / "configurazioni/esperimenti")
        self.kit.start(); self.named.start()
        self.addCleanup(self.kit.stop); self.addCleanup(self.named.stop); self.addCleanup(self.tmp.cleanup)
        self.run_cli("nuovo", "prova")

    def run_cli(self, *args):
        with redirect_stdout(StringIO()) as out:
            code = main(list(args))
        return code, out.getvalue()

    def test_defaults_are_unchanged_and_profile_and_paths_work(self):
        self.assertEqual((self.original / "configurazioni/esperimento.json").read_bytes(), (self.root / "configurazioni/esperimento.json").read_bytes())
        cfg, cat, registry = c.load("prova")
        active = [m for m in registry["models"] if m["enabled"]]
        self.assertEqual([m["id"] for m in active], ["qwen"])
        self.assertEqual(active[0]["file"], str(self.root / "modelli_llm/qwen/modello.gguf"))
        self.assertEqual(active[0]["server"]["gpu_layers"], 0)
        self.assertEqual(active[0]["context"], 16384)
        self.assertEqual(cat["execution_policy"]["workers"], 1)
        self.run_cli("modelli", "prova", "phi", "qwen")
        self.assertEqual(sum(m["enabled"] for m in c.load("prova")[2]["models"]), 2)

    def test_invalid_edits_are_atomic_and_revisions_survive(self):
        before = c.config_path("prova").read_bytes()
        parent = c.config_path("prova").parent / "revisioni"
        revisions = sorted(parent.iterdir())
        for args in [("sistemi", "prova", "typo"), ("sistemi", "prova", "random", "random"),
                     ("parametri", "prova", "--temperature", "nan"),
                     ("parametri", "prova", "--seed-compilazione", "0", "0", "1"),
                     ("dispositivi", "prova", "missing"), ("risorse", "prova", "--threads", "0"),
                     ("modello", "prova", "qwen", "--contesto", "100"),
                     ("modello", "prova", "qwen", "--url", "http://user:secret@127.0.0.1:8089")]:
            with self.subTest(args=args), self.assertRaises(ValueError): self.run_cli(*args)
            self.assertEqual(before, c.config_path("prova").read_bytes())
            self.assertEqual(revisions, sorted(parent.iterdir()))
        self.run_cli("dispositivi", "prova", "ibm_falcon_27")
        self.assertEqual(len(list(parent.iterdir())), 2)
        self.assertEqual(json.loads(before), c.read(revisions[0] / "esperimento.json"))

    def test_catalog_custom_combinations_and_duplicates(self):
        self.run_cli("compilazioni", "prova", "o2_default_default")
        self.run_cli("aggiungi-compilazione", "prova", "mia", "--ottimizzazione", "3", "--layout", "dense", "--routing", "basic", "--studio", "routing")
        self.assertEqual(len(c.load("prova")[1]["configurations"]), 2)
        with self.assertRaises(ValueError):
            self.run_cli("aggiungi-compilazione", "prova", "duplicata", "--ottimizzazione", "2")
        with self.assertRaises(ValueError):
            self.run_cli("aggiungi-compilazione", "prova", "a" * 65, "--ottimizzazione", "3", "--layout", "sabre")
        self.run_cli("compilazioni", "prova", "mia", "o3_default_default")
        self.assertEqual([x["config_id"] for x in c.load("prova")[1]["configurations"]], ["mia", "o3_default_default"])

    def test_add_model_hash_identity_and_preservation(self):
        path = self.root / 'file with spaces.gguf'; path.write_bytes(b"synthetic fixture, not real GGUF")
        self.run_cli("aggiungi-modello", "prova", "locale", "--file", str(path), "--fonte", "fixture", "--revisione", "fixture-v1", "--precisione", "synthetic")
        self.run_cli("modelli", "prova", "locale")
        local = next(m for m in c.load("prova")[2]["models"] if m["id"] == "locale")
        self.assertEqual(local["sha256"], c.file_hash(path))
        self.assertNotIn("base_repository", local)
        self.run_cli("modelli", "prova", "qwen")
        self.run_cli("modelli", "prova", "locale")
        self.assertEqual(local, next(m for m in c.load("prova")[2]["models"] if m["id"] == "locale"))
        path.write_bytes(b"changed")
        code, output = self.run_cli("verifica", "prova")
        self.assertEqual(code, 2); self.assertIn('registered fingerprint', output)

    def test_freeze_guard_covers_external_output_and_duplication(self):
        config = c.read(c.config_path("prova"))
        work = self.root / "external output/esecuzioni/prova"
        with c.preparation_guard(c.config_path("prova"), config, work):
            with self.assertRaises(ValueError): self.run_cli("sistemi", "prova", "random")
            work.mkdir(parents=True)
            c.write_json(work / "contratto.json", {"fixture": True})
        with self.assertRaises(ValueError): self.run_cli("sistemi", "prova", "random")
        self.run_cli("duplica", "prova", "seconda")
        self.run_cli("sistemi", "seconda", "random")
        self.assertFalse(c.frozen("seconda", c.load("seconda")[0]))
        with self.assertRaises(ValueError):
            with c.preparation_guard(c.config_path("prova"), config, self.root / "other-output"):
                pass

    def test_failed_preparation_without_contract_stays_editable(self):
        cfg = c.read(c.config_path("prova"))
        work = self.root / "outside/esecuzioni/prova"
        with self.assertRaises(ValueError):
            with c.preparation_guard(c.config_path("prova"), cfg, work):
                # Persist the destination before creating the contract.
                self.assertEqual(c.read(c.config_path("prova").parent / ".congelato.json")["work"], str(work))
                raise ValueError("preflight failure")
        self.run_cli("sistemi", "prova", "random")
        self.assertFalse(c.frozen("prova", c.load("prova")[0]))
        # Simulate a contract left by a process that terminated abruptly.
        work.mkdir(parents=True)
        c.write_json(work / "contratto.json", {"fixture": True})
        with self.assertRaises(ValueError): self.run_cli("sistemi", "prova", "llm_rag")

    def test_missing_inputs_are_reported_together(self):
        self.run_cli("circuiti", "prova", "--cartella", str(self.root / 'new circuits'), "--crea")
        code, output = self.run_cli("verifica", "prova")
        self.assertEqual(code, 2)
        self.assertTrue(all(name in output for name in ("train", "validation", "test", 'missing GGUF')))
        self.assertFalse(c.frozen("prova", c.load("prova")[0]))

    def test_concurrent_edit_and_invalid_names_are_rejected(self):
        with c.locked("prova"):
            with self.assertRaises(ValueError): self.run_cli("sistemi", "prova", "random")
        for name in ("../escape", "/absolute", ".", "name with spaces"):
            with self.assertRaises(ValueError): c.config_path(name)

    def test_other_experiments_do_not_change_code_identity(self):
        env = {**os.environ, "RIPRO_CONFIG": str(c.config_path("prova")), "PYTHONDONTWRITEBYTECODE": "1"}
        # Run the real settings.py against an isolated KIT copy without scientific dependencies.
        common = self.root / "comune"; common.mkdir()
        (common / "settings.py").write_bytes((self.original / "comune/settings.py").read_bytes())
        snippet = "import sys,json;sys.path.insert(0,sys.argv[1]);import settings;print(json.dumps(settings.code_identity(),sort_keys=True));print(settings.OUTPUT)"
        def identity():
            return subprocess.check_output([sys.executable, "-B", "-c", snippet, str(common)], env=env, text=True)
        before = identity()
        self.run_cli("nuovo", "seconda", "--profilo", "gpu")
        self.run_cli("risorse", "seconda", "--threads", "2")
        self.assertEqual(before, identity())
        output = self.root / "results with spaces"
        self.run_cli("risorse", "prova", "--risultati", str(output))
        env.pop("RIPRO_OUTPUT", None)
        self.assertEqual(identity().splitlines()[-1], str(output))


if __name__ == "__main__": unittest.main()

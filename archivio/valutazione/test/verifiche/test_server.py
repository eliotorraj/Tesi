"""Verifica server con GGUF sintetico e /props simulato, senza inferenza."""
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "strumenti"))
from common import sha
from runner import verify_server


class TestServer(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.model = Path(self.temp.name) / "model.gguf"
        self.model.write_bytes(b"synthetic model")
        self.artifact = {"size_bytes": self.model.stat().st_size,
                         "gguf_sha256": sha(self.model)}
        self.args = SimpleNamespace(model_path=self.model, url="http://localhost:8089")

    def verify(self, context, *, top_level=False, served=None, wsl=False):
        props = {"model_path": str(served or self.model)}
        if top_level:
            props["n_ctx"] = context
        else:
            props["default_generation_settings"] = {"n_ctx": context}
        with patch("app.CONFIG", {"profile": {"artifact": self.artifact}}), \
             patch("runner.platform.release", return_value="microsoft" if wsl else "Linux"), \
             patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(props).encode())), \
             patch("runner.subprocess.run", return_value=SimpleNamespace(stdout=json.dumps(props).encode())):
            return verify_server(self.args)

    def test_desktop_context_and_padding_are_recorded(self):
        for context in (60000, 60160):
            for top_level in (False, True):
                for wsl in (False, True):
                    with self.subTest(context=context, top_level=top_level, wsl=wsl):
                        result = self.verify(context, top_level=top_level, wsl=wsl)
                        self.assertEqual(result["context_requested"], 60000)
                        self.assertEqual(result["context_reported"], context)
                        self.assertEqual(result["model_sha256"], sha(self.model))

    def test_other_contexts_and_invalid_types_are_rejected(self):
        for context in (16384, 59904, 60001, 60159, 60161, 65536, None, "60160", 60160.0, True):
            with self.subTest(context=context):
                with self.assertRaisesRegex(ValueError, "profilo desktop"):
                    self.verify(context)

    def test_wrong_served_model_is_rejected_even_with_padding(self):
        other = Path(self.temp.name) / "other" / self.model.name
        other.parent.mkdir()
        other.write_bytes(b"different model")
        with self.assertRaisesRegex(ValueError, "GGUF effettivamente"):
            self.verify(60160, served=other)

    def test_wrong_supplied_model_is_rejected(self):
        self.model.write_bytes(b"incorrect model")
        with self.assertRaisesRegex(ValueError, "modello selezionato"):
            self.verify(60160)


if __name__ == "__main__":
    unittest.main()

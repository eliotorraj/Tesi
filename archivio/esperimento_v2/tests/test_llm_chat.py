"""Chat manuale: scelta modello, controlli e isolamento dei processi (avvii simulati)."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from llm_selection import chat
from llm_selection.hardware import DEFAULT_GUARDS


class ManualChatTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.output = self.root / "output"
        for relative in ("llm_selection/serve.ps1", "llm_selection/stop.ps1",
                         "output/runtime/b10930/llama-server.exe"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test fixture")
        for model in chat.MODEL_KEYS:
            directory = self.output / "models" / model
            directory.mkdir(parents=True)
            weight = directory / "fixture.gguf"
            weight.write_text("not real model weights")
            (directory / "Q8_0_manifest.json").write_text(json.dumps({"local_path": str(weight)}))
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(patch.object(chat, "ROOT", self.root))
        self.stack.enter_context(patch.object(chat, "OUTPUT", self.output))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.launch = self.stack.enter_context(patch.object(chat, "launch"))
        self.stop = self.stack.enter_context(patch.object(chat, "stop"))
        self.capture = self.stack.enter_context(patch.object(chat, "capture"))
        self.health = self.stack.enter_context(patch.object(chat, "health", return_value=None))

    def tearDown(self):
        self.stack.close()
        self.temporary.cleanup()

    def test_check_selects_each_model_without_writes_or_server_contact(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        for model in chat.MODEL_KEYS:
            with self.subTest(model=model):
                chat.main(["--model", model, "--check"])
        after = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        self.assertEqual(before, after)
        self.launch.assert_not_called()
        self.stop.assert_not_called()
        self.capture.assert_not_called()
        self.health.assert_not_called()

    def test_default_model_remains_qwen(self):
        with patch.object(chat, "profile_for_model", wraps=chat.profile_for_model) as profile:
            chat.main(["--check"])
        self.assertEqual(profile.call_args.args, ("qwen",))

    def test_actual_launch_and_record_follow_selected_model(self):
        for model in chat.MODEL_KEYS:
            with self.subTest(model=model):
                self.launch.return_value = Mock(returncode=0)
                self.launch.return_value.poll.return_value = 0
                chat.main(["--model", model])
                args = self.launch.call_args.args
                self.assertEqual(args[0], model)
                self.assertEqual(args[1], chat.profile_for_model(model))
                self.assertTrue(args[2].name.startswith(model + "-chat-"))
                request = self.output / "manual_chats" / args[2].name / "request.json"
                record = json.loads(request.read_text())
                self.assertEqual(record["model"], model)
                self.assertEqual(record["profile"], chat.profile_for_model(model))
                self.stop.assert_called_with(args[2], "manual_chat_closed", args[3])

    def test_active_server_is_not_replaced_or_stopped(self):
        self.health.return_value = {"status": "ok"}
        with self.assertRaisesRegex(RuntimeError, "risponde già"):
            chat.main(["--model", "phi", "--label", "occupied-port"])
        self.launch.assert_not_called()
        self.stop.assert_not_called()
        self.assertFalse((self.output / "manual_chats" / "occupied-port").exists())

    def test_missing_selected_model_never_falls_back_to_qwen(self):
        (self.output / "models/phi/Q8_0_manifest.json").unlink()
        with self.assertRaises(FileNotFoundError):
            chat.main(["--model", "phi", "--check"])
        self.launch.assert_not_called()

    def test_context_limits_and_explicit_overrides(self):
        for model in chat.MODEL_KEYS:
            with self.subTest(model=model):
                for invalid in (0, -1, chat.NATIVE_CONTEXT[model] + 1):
                    with self.assertRaises(ValueError):
                        chat.profile_for_model(model, context=invalid)
                profile = chat.profile_for_model(model, precision="BF16", context=8192, cache_type="f16")
                self.assertEqual(profile["context"], 8192)
                self.assertEqual(profile["weight_precision"], "BF16")
                self.assertEqual(profile["cache_type"], "f16")
        changed = chat.profile_for_model("qwen")
        changed["guards"]["maximum_hotspot_c"] = 1
        self.assertEqual(chat.profile_for_model("qwen")["guards"], DEFAULT_GUARDS)

    def test_invalid_cli_fails_before_model_access(self):
        for arguments in (["--model", "unknown"], ["--model", "phi", "--context", "147456"],
                          ["--model", "gemma", "--context", "0"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    chat.main(arguments)
        self.launch.assert_not_called()
        self.health.assert_not_called()


if __name__ == "__main__":
    unittest.main()

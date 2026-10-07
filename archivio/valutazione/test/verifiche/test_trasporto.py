'Server unavailable: preserve the attempt and leave subsequent cases untouched.'
import io
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "strumenti"))
import runner
from common import ROOT, read, save, sha
from app import Http, LlmTransportError


class TestTrasporto(unittest.TestCase):
    def test_native_connection_failure_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "call"
            with patch("app.platform.release", return_value="Linux"), patch(
                "app.urllib.request.urlopen", side_effect=urllib.error.URLError("refused")
            ):
                with self.assertRaises(LlmTransportError):
                    Http("http://localhost:8089")("/completion", {}, folder)
            self.assertEqual(read(folder / "failure.json")["type"], "URLError")
            self.assertTrue((folder / "request.json").exists())

    def test_wsl_reset_preserves_curl_details(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "call"
            with patch("app.platform.release", return_value="microsoft"), \
                 patch("app.subprocess.check_output", return_value="request.json"), \
                 patch("app.shutil.which", return_value="curl.exe"), \
                 patch("app.subprocess.run", return_value=SimpleNamespace(
                     returncode=56, stdout=b"", stderr=b"Connection was reset")):
                with self.assertRaisesRegex(LlmTransportError, "curl transport error: 56"):
                    Http("http://localhost:8089")("/completion", {}, folder)
            self.assertEqual((folder / "stderr.txt").read_text(), "Connection was reset")
            self.assertFalse(read(folder / "failure.json")["completed_logical_attempt"])

    def test_evaluate_saves_failure_before_stopping(self):
        source = ROOT / "examples/bell.qasm"
        row = {"circuit_id": "bell", "source_sha256": sha(source), "technical_source": str(source)}
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            with patch("app.decide", side_effect=LlmTransportError("server down")), \
                 patch("runner.compile_job") as compile_job:
                with self.assertRaises(LlmTransportError):
                    runner.evaluate(row, folder, "llm_senza_rag", "http://localhost:8089", True)
                compile_job.assert_not_called()
            result = read(folder / "esito.json")
            self.assertEqual(result["status"], "failure")
            self.assertEqual(result["error"], "LlmTransportError")
            self.assertIsNone(result["score"])

    def test_cli_stops_after_one_case_and_resume_skips_it(self):
        rows = [{"circuit_id": f"synthetic_{i:03d}", "source_sha256": str(i), "split": "test"}
                for i in range(90)]
        calls = []
        def reader(path):
            return {"circuits": rows} if path == runner.SOURCE else read(path)
        def unavailable(row, folder, *args):
            calls.append(row["circuit_id"])
            save(folder / "esito.json", {"status": "failure", "error": "LlmTransportError"})
            raise LlmTransportError("server down")
        with tempfile.TemporaryDirectory() as temp:
            area = Path(temp)
            with patch.object(runner, "AREA", area), patch.object(runner, "read", side_effect=reader), \
                 patch.object(runner, "preflight", return_value={"ready": True, "checks": {}}), \
                 patch.object(runner, "verify_server", return_value={}), \
                 patch.object(runner, "freeze", return_value="synthetic_contract"), \
                 patch.object(runner, "evaluate", side_effect=unavailable), \
                 patch.object(sys, "argv", ["llm_rag.py", "--esegui"]), \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(runner.cli("llm_rag"), 1)
                self.assertEqual(len(list((area / "risultati/llm_rag/circuiti").iterdir())), 1)
                self.assertEqual(runner.cli("llm_rag"), 1)
            self.assertEqual(calls, ["synthetic_000", "synthetic_001"])


if __name__ == "__main__":
    unittest.main()

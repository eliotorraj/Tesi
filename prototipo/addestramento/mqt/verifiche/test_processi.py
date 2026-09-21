"""Prove sintetiche: connessioni successive, timeout, riavvio e ripresa."""
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motore_ml as trainer


def fake_worker(*args):
    device, metric, jobs, port, queue, log = args[:6]
    trainer._set_parent_death_signal()
    queue.put(dict(type="ready", device=device, pid=os.getpid()))
    job = jobs[0]
    queue.put(dict(type="started", device=device, pid=os.getpid(), key=job.key))
    queue.put(dict(type="phase", device=device, pid=os.getpid(), key=job.key, phase="rl"))
    if job.circuit_name == "blocked":
        job.output.write_text("partial evidence")
        time.sleep(30)
    else:
        queue.put(dict(type="result", device=device, pid=os.getpid(), key=job.key,
                       status="failed", mode="rl", error="synthetic failure", duration_seconds=0.01,
                       model_sha256="model", target_sha256="target", seed=0, rl_max_steps=64,
                       mqt_predictor_version=trainer.package_version("mqt.predictor")))
        queue.put(dict(type="done", device=device, pid=os.getpid()))

class SpawnContext:
    def Queue(self):
        return multiprocessing.get_context("spawn").Queue()
    def Process(self, **kwargs):
        kwargs["target"] = fake_worker
        return multiprocessing.get_context("spawn").Process(**kwargs)

class ProcessTests(unittest.TestCase):
    def test_bqskit_reconnects_without_closed_wrapper(self):
        from mqt.predictor.rl.actions import bqskit_actions as actions
        original = actions.bqskit_compile
        clients = []
        class Client:
            def __init__(self, **kwargs):
                self.closed = False
                clients.append(self)
            def close(self):
                self.closed = True
        def compile_stub(*args, **kwargs):
            self.assertFalse(kwargs["compiler"].closed)
            return kwargs["compiler"]
        try:
            with patch("bqskit.compiler.Compiler", Client), patch("bqskit.compile", compile_stub):
                for i in range(3):
                    client = trainer.configure_shared_bqskit_runtime(123, 0)
                    self.assertIs(actions.bqskit_compile("circuit"), client)
                    client.close()
            self.assertEqual(len(clients), 3)
        finally:
            actions.bqskit_compile = original

    def test_inline_compilation_never_reinitializes_process(self):
        from qiskit import QuantumCircuit
        from qiskit.qasm2 import dump
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0, 1)
        predictor = MagicMock()
        predictor.env.max_steps = 64
        validation = dict(valid=True, terminated=True, truncated=False, termination_reason="terminate")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            dump(circuit, p / "input.qasm")
            with patch.object(trainer, "_set_parent_death_signal", side_effect=AssertionError("setsid called")), \
                 patch.object(trainer, "configure_shared_bqskit_runtime", return_value=MagicMock()), \
                 patch.object(trainer, "run_rl_policy", return_value=(circuit, ["terminate"], True, False, {})), \
                 patch.object(trainer, "validate_rl_compilation", return_value=validation):
                for i in range(2):
                    job = trainer.CompilationJob(p/"input.qasm", p/f"out{i}.qasm", str(i), "device", 2)
                    result = trainer._compile_job_inline(job, None, predictor, None, 1, "rl", 2, 0, "model", "target")
                    self.assertEqual(result["status"], "success")
                    self.assertTrue(job.output.exists())

    def test_supervisor_timeout_restart_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            jobs = [trainer.CompilationJob(p/"in.qasm", p/f"{n}.qasm", n, "device", 2)
                    for n in ("blocked", "following")]
            runtime = MagicMock()
            runtime.server_port = 1
            runtime.is_alive.return_value = True
            kwargs = dict(jobs=jobs, metric="expected_fidelity", rl_max_steps=64, seed=0,
                model_sha256_by_device={"device":"model"}, target_sha256_by_device={"device":"target"},
                num_workers=1, timeout=1, startup_timeout=60, fallback_timeout=1,
                fallback_enabled=False, fallback_optimization_level=2, max_attempts=1,
                manifest_path=p/"manifest.jsonl", log_dir=p/"logs", progress_every=1)
            with patch.object(trainer, "get_context", return_value=SpawnContext()), \
                 patch.object(trainer, "BQSKitRuntime", return_value=runtime), \
                 patch.object(trainer, "ACTIVE_TIMEOUT", 1):
                trainer.compile_resumably(**kwargs)
                rows = [json.loads(x) for x in (p/"manifest.jsonl").read_text().splitlines()]
                final = {r["circuit"]:r for r in rows if r["status"] != "running"}
                self.assertEqual(final["blocked"]["status"], "timeout")
                self.assertEqual(final["following"]["status"], "failed")
                self.assertFalse(jobs[0].output.exists())
                self.assertEqual(len(list((p/"non_verificati").iterdir())), 1)
                before = (p/"manifest.jsonl").read_bytes()
                trainer.compile_resumably(**kwargs)
                self.assertEqual((p/"manifest.jsonl").read_bytes(), before)

if __name__ == "__main__":
    unittest.main()

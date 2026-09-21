"""Un processo nuovo per compilazione, con esito durevole e timeout esterno."""
from __future__ import annotations
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import read, save, now
import time
import traceback

def main(job_path):
    job = read(job_path)
    folder = Path(job_path).parent
    try:
        from qiskit import QuantumCircuit, transpile, qasm2
        from mqt.bench.targets import get_device
        from prototype.quantum_assistant.adapters.compilation import _validate_compiled_circuit
        from score import expected_fidelity
        circuit = QuantumCircuit.from_qasm_file(job["source"])
        passes = []
        choice_seconds = 0.0
        if job["method"] == "mqt_predictor":
            # Stesse due chiamate di qcompile 2.4.0, separate per misurare le fasi.
            from mqt.predictor.ml import predict_device_for_figure_of_merit
            from mqt.predictor.rl import rl_compile
            started = time.perf_counter()
            device = job.get("rl_device") or predict_device_for_figure_of_merit(circuit, figure_of_merit="expected_fidelity")
            device = device.description if hasattr(device, "description") else str(device)
            choice_seconds = time.perf_counter() - started
            started = time.perf_counter()
            compiled, passes = rl_compile(circuit, device=device, figure_of_merit="expected_fidelity")
            seconds = time.perf_counter() - started
            passes = [str(p) for p in passes]
            if not passes or passes[-1] != "terminate":
                raise ValueError("La politica RL non ha terminato.")
        else:
            from qiskit_dataset.catalog import load_catalog
            device = job["decision"]["selected_device"]
            options = load_catalog().by_id[job["decision"]["config_id"]].transpile_kwargs()
            target = get_device(device)
            started = time.perf_counter()
            compiled = transpile(circuit, target=target, seed_transpiler=0,
                                 num_processes=1, **options)
            seconds = time.perf_counter() - started
        target = get_device(device)
        validation = _validate_compiled_circuit(compiled, target)
        if not validation["is_executable_on_target"]:
            raise ValueError("Circuito non eseguibile sul Target: " + str(validation))
        metrics = expected_fidelity(compiled, target)
        qasm2.dump(compiled, folder / "compiled.qasm")
        save(folder / "result.json", dict(status="success", at=now(), device=device,
            compilation_seconds=seconds, choice_seconds=choice_seconds, passes=passes,
            validation=validation, depth=compiled.depth(), size=compiled.size(), **metrics))
    except Exception as exc:
        save(folder / "result.json", dict(status="failure", at=now(), score=None,
             compilation_seconds=None, error=type(exc).__name__, message=str(exc),
             traceback=traceback.format_exc()))
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))

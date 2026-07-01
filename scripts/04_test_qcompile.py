"""Run qcompile and inspect its circuit, pass list, and selected Target."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mqt.bench import BenchmarkLevel, get_benchmark
from mqt.predictor import qcompile
from qiskit.qasm2 import dump


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", default="ghz")
    parser.add_argument("--qubits", type=int, default=5)
    parser.add_argument("--metric", choices=("expected_fidelity", "critical_depth"), default="expected_fidelity")
    return parser.parse_args()


def main() -> int:
    """Compile one target-independent benchmark and persist an inspection report."""
    args = parse_args()
    if args.qubits < 2:
        raise SystemExit("--qubits deve essere almeno 2.")

    source = get_benchmark(args.benchmark, BenchmarkLevel.ALG, args.qubits)
    print(f"Circuito sorgente: {args.benchmark}, qubit={source.num_qubits}, depth={source.depth()}")

    try:
        compiled, compilation_passes, selected_device = qcompile(source, figure_of_merit=args.metric)
    except FileNotFoundError as error:
        print(f"\nModelli mancanti: {error}")
        print("Esegui prima lo smoke training oppure addestra/ripristina tutti i modelli abbinati al selettore.")
        print("Smoke training: python scripts/03_train_smoke_models.py")
        return 2

    if compiled.layout is None:
        raise RuntimeError("Il circuito compilato non contiene un layout fisico.")

    unsupported = set(compiled.count_ops()) - set(selected_device.operation_names) - {"barrier"}
    if unsupported:
        raise RuntimeError("Operazioni non presenti nel Target selezionato: " + ", ".join(sorted(unsupported)))

    output_dir = PROJECT_ROOT / "artifacts" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    qasm_path = output_dir / f"{args.benchmark}_{args.qubits}_{args.metric}.qasm"
    report_path = output_dir / f"{args.benchmark}_{args.qubits}_{args.metric}.json"

    with qasm_path.open("w", encoding="utf-8") as stream:
        dump(compiled, stream)

    report = {
        "benchmark": args.benchmark,
        "figure_of_merit": args.metric,
        "source": {"qubits": source.num_qubits, "depth": source.depth(), "operations": dict(source.count_ops())},
        "compiled": {
            "qubits": compiled.num_qubits,
            "depth": compiled.depth(),
            "operations": dict(compiled.count_ops()),
        },
        "selected_device": {
            "type": f"{type(selected_device).__module__}.{type(selected_device).__qualname__}",
            "description": selected_device.description,
            "num_qubits": selected_device.num_qubits,
        },
        "compilation_passes": compilation_passes,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Device selezionato: {selected_device.description} ({selected_device.num_qubits} qubit)")
    print(f"Tipo restituito:    {report['selected_device']['type']}")
    print(f"Pass RL eseguiti:   {compilation_passes}")
    print(f"Circuito compilato: qubit={compiled.num_qubits}, depth={compiled.depth()}")
    print(f"QASM:               {qasm_path}")
    print(f"Report:             {report_path}")
    print("\nqcompile: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

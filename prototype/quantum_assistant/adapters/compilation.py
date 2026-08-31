"""Compila con Qiskit dopo la conferma esplicita dell'utente."""

from __future__ import annotations

from io import StringIO
from typing import Any

from mqt.bench.targets import get_device
from qiskit import QuantumCircuit, transpile
from qiskit.qasm2 import dump as qasm_dump
from qiskit.transpiler.passes import CheckMap, GatesInBasis

from ..models import CompilationArtifact, ParsedRequest, Recommendation


def _validate_compiled_circuit(
    circuit: QuantumCircuit,
    target: Any,
) -> dict[str, Any]:
    """Controlla che il circuito compilato sia eseguibile sul dispositivo."""
    errors: list[str] = []
    unsupported = sorted(
        set(map(str, circuit.count_ops()))
        - set(map(str, target.operation_names))
        - {"barrier"}
    )
    basis_valid = False
    connectivity_valid = False
    try:
        basis_checker = GatesInBasis(target=target)
        basis_checker(circuit)
        basis_valid = bool(basis_checker.property_set["all_gates_in_basis"])
    except Exception as exc:
        errors.append(f"GatesInBasis:{type(exc).__name__}:{exc}")

    try:
        coupling_map = target.build_coupling_map()
        if coupling_map is None:
            connectivity_valid = True
        else:
            map_checker = CheckMap(coupling_map=coupling_map)
            map_checker(circuit)
            connectivity_valid = bool(map_checker.property_set["is_swap_mapped"])
    except Exception as exc:
        errors.append(f"CheckMap:{type(exc).__name__}:{exc}")

    executable = bool(
        basis_valid
        and connectivity_valid
        and not unsupported
        and not errors
    )
    return {
        "basis_valid": basis_valid,
        "connectivity_valid": connectivity_valid,
        "unsupported_operations": unsupported,
        "validation_errors": errors,
        "is_executable_on_target": executable,
    }


class QiskitDeterministicCompiler:
    """Compila usando solo i parametri già controllati della raccomandazione."""

    def compile(
        self,
        request: ParsedRequest,
        recommendation: Recommendation,
    ) -> CompilationArtifact:
        """Compila il circuito secondo la raccomandazione validata."""
        if recommendation.figure_of_merit != request.figure_of_merit:
            raise ValueError("La recommendation usa una figure of merit diversa.")
        target = get_device(recommendation.selected_device)
        if request.num_qubits > target.num_qubits:
            raise ValueError(
                f"Il circuito usa {request.num_qubits} qubit, "
                f"ma {target.description} ne supporta {target.num_qubits}."
            )

        circuit = QuantumCircuit.from_qasm_str(request.qasm2)
        plan = recommendation.qiskit_plan
        transpile_kwargs: dict[str, Any] = {
            "target": target,
            "optimization_level": plan.optimization_level,
            "seed_transpiler": plan.seed_transpiler,
        }
        if plan.layout_method is not None:
            transpile_kwargs["layout_method"] = plan.layout_method
        if plan.routing_method is not None:
            transpile_kwargs["routing_method"] = plan.routing_method

        compiled = transpile(circuit, **transpile_kwargs)
        validation = _validate_compiled_circuit(compiled, target)
        if not validation["is_executable_on_target"]:
            raise RuntimeError(
                "Qiskit ha prodotto un circuito non valido per il target: "
                f"{validation}"
            )

        stream = StringIO()
        qasm_dump(compiled, stream)
        return CompilationArtifact(
            device_id=recommendation.selected_device,
            qasm2=stream.getvalue(),
            depth=int(compiled.depth()),
            size=int(compiled.size()),
            operation_counts={
                str(name): int(count)
                for name, count in sorted(compiled.count_ops().items())
            },
            validation=validation,
            compiler_metadata={
                "compiler": "qiskit.transpile",
                "optimization_level": plan.optimization_level,
                "seed_transpiler": plan.seed_transpiler,
                "layout_method": plan.layout_method,
                "routing_method": plan.routing_method,
            },
        )

"""Request parsing, hardware catalog, and pre-compilation compatibility."""

from __future__ import annotations

from collections.abc import Sequence

from mqt.bench.targets import get_device
from mqt.predictor.ml.helper import create_feature_vector, get_openqasm_gates
from qiskit import QuantumCircuit

from ..models import (
    SUPPORTED_METRICS,
    CompatibilityReport,
    HardwareProfile,
    ParsedRequest,
    UiSubmission,
)


FEATURE_NAMES = tuple(
    [f"gate_count_{gate}" for gate in get_openqasm_gates()]
    + [
        "num_qubits",
        "depth",
        "program_communication",
        "critical_depth",
        "entanglement_ratio",
        "parallelism",
        "liveness",
    ]
)


class QasmRequestParser:
    """Parse OpenQASM 2 and attach the 49 MQT selector features."""

    def parse(self, submission: UiSubmission) -> ParsedRequest:
        if submission.figure_of_merit not in SUPPORTED_METRICS:
            raise ValueError(
                f"Figure of merit non supportata: {submission.figure_of_merit}."
            )
        if not submission.qasm2.strip():
            raise ValueError("Il circuito OpenQASM 2 e vuoto.")
        try:
            circuit = QuantumCircuit.from_qasm_str(submission.qasm2)
        except Exception as exc:
            raise ValueError(
                f"Circuito OpenQASM 2 non valido: {type(exc).__name__}: {exc}"
            ) from exc

        feature_values = create_feature_vector(circuit)
        if len(feature_values) != len(FEATURE_NAMES):
            raise RuntimeError(
                f"Feature vector inatteso: {len(feature_values)} valori, "
                f"attesi {len(FEATURE_NAMES)}."
            )
        return ParsedRequest(
            request_id=submission.request_id,
            user_text=submission.user_text.strip(),
            circuit_name=submission.circuit_name,
            qasm2=submission.qasm2,
            figure_of_merit=submission.figure_of_merit,
            num_qubits=int(circuit.num_qubits),
            depth=int(circuit.depth()),
            operation_names=tuple(sorted(map(str, circuit.count_ops()))),
            features={
                name: float(value)
                for name, value in zip(FEATURE_NAMES, feature_values, strict=True)
            },
            allowed_devices=tuple(submission.allowed_devices),
            constraints=dict(submission.constraints),
        )


class MqtHardwareCatalog:
    """Expose configured MQT Bench targets as compact profiles."""

    def __init__(self, device_names: Sequence[str]) -> None:
        if not device_names:
            raise ValueError("Configurare almeno un device.")
        self._device_names = tuple(dict.fromkeys(map(str, device_names)))

    def list_hardware(self) -> tuple[HardwareProfile, ...]:
        profiles: list[HardwareProfile] = []
        for device_name in sorted(self._device_names):
            target = get_device(device_name)
            coupling_map = target.build_coupling_map()
            raw_edges = () if coupling_map is None else coupling_map.get_edges()
            profiles.append(
                HardwareProfile(
                    device_id=str(target.description),
                    num_qubits=int(target.num_qubits),
                    operation_names=tuple(sorted(map(str, target.operation_names))),
                    coupling_edges=tuple(
                        sorted((int(source), int(destination)) for source, destination in raw_edges)
                    ),
                    metadata={
                        "all_to_all": coupling_map is None,
                        "source": "mqt.bench.targets.get_device",
                    },
                )
            )
        return tuple(profiles)


class WidthCompatibilityFilter:
    """Apply constraints knowable before target-specific compilation.

    Target-independent gate names are intentionally not compared with native
    target operations here: basis translation is a compilation responsibility.
    """

    def filter(
        self,
        request: ParsedRequest,
        hardware: Sequence[HardwareProfile],
    ) -> CompatibilityReport:
        available: list[HardwareProfile] = []
        unavailable: dict[str, tuple[str, ...]] = {}
        allowed = set(request.allowed_devices)
        catalog_ids = {profile.device_id for profile in hardware}

        for profile in hardware:
            reasons: list[str] = []
            if allowed and profile.device_id not in allowed:
                reasons.append("excluded_by_user")
            if request.num_qubits > profile.num_qubits:
                reasons.append(
                    f"insufficient_qubits:{request.num_qubits}>{profile.num_qubits}"
                )
            if reasons:
                unavailable[profile.device_id] = tuple(reasons)
            else:
                available.append(profile)

        for unknown in sorted(allowed - catalog_ids):
            unavailable[unknown] = ("not_in_hardware_catalog",)

        return CompatibilityReport(
            available=tuple(available),
            unavailable=unavailable,
        )

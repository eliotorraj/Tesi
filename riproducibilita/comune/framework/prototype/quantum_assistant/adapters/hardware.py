'Build the MQT catalog and apply verifiable hardware constraints.'

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from mqt.bench.targets import get_device, get_gateset

from qiskit_dataset.catalog import V2_CATALOG_PATH, ConfigurationCatalog, load_catalog
from scripts.mqt_predictor_protocol import target_payload as _target_payload

from ..models import (
    HARDWARE_CATALOG_SCHEMA_VERSION,
    HARDWARE_MASK_SCHEMA_VERSION,
    CompatibilityReport,
    DeviceExclusionDiagnostic,
    DeviceExclusionReason,
    HardwareCatalogSnapshot,
    HardwareMaskResult,
    HardwareProfile,
    NormalizedRequest,
    ParsedRequest,
    ProviderProfile,
)
from ..schema_validation import load_schema, validate_instance


CATALOG_SCHEMA = load_schema("hardware_catalog.schema.json")
MASK_SCHEMA = load_schema("hardware_mask_result.schema.json")
FINGERPRINT_ALGORITHM = "assistant-hardware-catalog/3"
TARGET_FINGERPRINT_ALGORITHM = "qiskit-dataset-target/2"
TARGET_UNAVAILABILITY_CODE = "TARGET_LOAD_FAILED"


@dataclass(frozen=True)
class DeviceDefinition:
    'Describe expected hardware data for a supported device.'

    provider_id: str
    native_gateset_id: str
    native_gate_ids: tuple[str, ...]
    expected_num_qubits: int


DEVICE_DEFINITIONS: dict[str, DeviceDefinition] = {
    "ibm_falcon_27": DeviceDefinition(
        provider_id="ibm",
        native_gateset_id="ibm_falcon",
        native_gate_ids=("cx", "id", "rz", "sx", "x"),
        expected_num_qubits=27,
    ),
    "ibm_falcon_127": DeviceDefinition(
        provider_id="ibm",
        native_gateset_id="ibm_falcon",
        native_gate_ids=("cx", "id", "rz", "sx", "x"),
        expected_num_qubits=127,
    ),
    "ibm_heron_133": DeviceDefinition(
        provider_id="ibm",
        native_gateset_id="ibm_heron",
        native_gate_ids=("cz", "id", "rz", "sx", "x"),
        expected_num_qubits=133,
    ),
    "ibm_heron_156": DeviceDefinition(
        provider_id="ibm",
        native_gateset_id="ibm_heron",
        native_gate_ids=("cz", "id", "rz", "sx", "x"),
        expected_num_qubits=156,
    ),
    "quantinuum_h2_56": DeviceDefinition(
        provider_id="quantinuum",
        native_gateset_id="quantinuum",
        native_gate_ids=("rx", "ry", "rz", "rzz"),
        expected_num_qubits=56,
    ),
}
PROVIDER_NAMES = {
    "ibm": "IBM",
    "quantinuum": "Quantinuum",
}


def _canonical_json(value: Any) -> str:
    'Convert a value to stable JSON suitable for fingerprinting.'
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    'Compute the SHA-256 fingerprint of canonical JSON.'
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _package_version(distribution: str) -> str:
    'Read the installed version or return a neutral value.'
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "unknown"


def _configuration_material(catalog: ConfigurationCatalog) -> dict[str, Any]:
    'Prepare configuration catalog data for fingerprinting.'
    return {
        "schema_version": catalog.schema_version,
        "catalog_id": catalog.catalog_id,
        "experiment_id": catalog.experiment_id,
        "protocol_version": catalog.protocol_version,
        "required_versions": dict(catalog.required_versions),
        "target_sha256": dict(catalog.target_sha256),
        "target_fingerprint_schema_version": catalog.target_fingerprint_schema_version,
        "execution_policy": dict(catalog.execution_policy),
        "default_device_id": catalog.default_device_id,
        "supported_device_ids": list(catalog.supported_device_ids),
        "objective": dict(catalog.objective),
        "seeds": list(catalog.seeds),
        "fixed_transpile_options": dict(catalog.fixed_transpile_options),
        "configurations": [
            configuration.to_dict()
            for configuration in catalog.configurations
        ],
    }


def _coupling_kind(num_qubits: int, edges: tuple[tuple[int, int], ...]) -> str:
    'Classify an explicit connectivity map.'
    if len(edges) == num_qubits * (num_qubits - 1):
        return "explicit_complete"
    return "sparse_directed"


def _validate_configuration_catalog(catalog: ConfigurationCatalog) -> None:
    'Check that the Qiskit catalog is complete and consistent.'
    objective_name = catalog.objective.get("name")
    if objective_name != "expected_fidelity":
        raise ValueError(
            "The Qiskit catalog must use objective.name='expected_fidelity'."
        )
    if not catalog.configurations:
        raise ValueError('The Qiskit catalog must contain configurations.')
    configuration_ids = tuple(
        configuration.config_id for configuration in catalog.configurations
    )
    if any(not config_id for config_id in configuration_ids):
        raise ValueError('Qiskit configuration IDs cannot be empty.')
    if len(configuration_ids) != len(set(configuration_ids)):
        raise ValueError('The Qiskit catalog contains duplicate config_id values.')
    configuration_keys = tuple(
        configuration.key for configuration in catalog.configurations
    )
    if len(configuration_keys) != len(set(configuration_keys)):
        raise ValueError('The Qiskit catalog contains duplicate Qiskit tuples.')
    supported_devices = tuple(catalog.supported_device_ids)
    if (
        not supported_devices
        or any(not device_id for device_id in supported_devices)
        or len(supported_devices) != len(set(supported_devices))
    ):
        raise ValueError(
            'supported_device_ids must contain unique, nonempty IDs.'
        )
    if catalog.default_device_id not in supported_devices:
        raise ValueError(
            'default_device_id must belong to supported_device_ids.'
        )


def _copy_configuration_catalog(
    catalog: ConfigurationCatalog,
) -> ConfigurationCatalog:
    'Copy the catalog to avoid retaining external mutable structures.'
    return ConfigurationCatalog(
        schema_version=str(catalog.schema_version),
        catalog_id=str(catalog.catalog_id),
        default_device_id=str(catalog.default_device_id),
        supported_device_ids=tuple(map(str, catalog.supported_device_ids)),
        objective=dict(catalog.objective),
        seeds=tuple(catalog.seeds),
        fixed_transpile_options=dict(catalog.fixed_transpile_options),
        configurations=tuple(catalog.configurations),
        experiment_id=catalog.experiment_id,
        protocol_version=catalog.protocol_version,
        required_versions=dict(catalog.required_versions),
        target_sha256=dict(catalog.target_sha256),
        target_fingerprint_schema_version=catalog.target_fingerprint_schema_version,
        execution_policy=dict(catalog.execution_policy),
    )


class HardwareCatalogIntegrityError(RuntimeError):
    'Indicate that declared data do not match the loaded Target.'


def _validated_target_shape(
    device_id: str,
    definition: DeviceDefinition,
    target_payload: dict[str, Any],
) -> tuple[int, tuple[str, ...], tuple[tuple[int, int], ...]]:
    "Check the loaded Target's size, operations and connectivity."
    description = str(target_payload["device_id"])
    if description != device_id:
        raise HardwareCatalogIntegrityError(
            f"Target description {description!r} != {device_id!r}."
        )
    num_qubits = int(target_payload["num_qubits"])
    if num_qubits != definition.expected_num_qubits:
        raise HardwareCatalogIntegrityError(
            f'Target qubits {num_qubits} != {definition.expected_num_qubits}.'
        )
    operation_names = tuple(target_payload["operation_names"])
    if len(operation_names) != len(set(operation_names)):
        raise HardwareCatalogIntegrityError(
            'The Target declares duplicate operation_names.'
        )
    missing_native = sorted(
        set(definition.native_gate_ids) - set(operation_names)
    )
    if missing_native:
        raise HardwareCatalogIntegrityError(
            'Native gates missing from the Target: ' + ", ".join(missing_native)
        )
    edges = tuple(
        (int(source), int(destination))
        for source, destination in target_payload["coupling_edges"]
    )
    if len(edges) != len(set(edges)) or any(
        source < 0
        or destination < 0
        or source >= num_qubits
        or destination >= num_qubits
        for source, destination in edges
    ):
        raise HardwareCatalogIntegrityError(
            'The Target declares invalid or duplicate coupling entries.'
        )
    return num_qubits, operation_names, edges


class MqtHardwareCatalog:
    'Combine MQT Targets and the Qiskit catalog in one stable view.'

    def __init__(
        self,
        device_names: Sequence[str],
        *,
        configuration_catalog: ConfigurationCatalog | None = None,
    ) -> None:
        'Check devices and prepare the configuration catalog.'
        if not device_names:
            raise ValueError('Configure at least one device.')
        self._device_names = tuple(sorted(dict.fromkeys(map(str, device_names))))
        source_catalog = (
            load_catalog(V2_CATALOG_PATH)
            if configuration_catalog is None
            else configuration_catalog
        )
        _validate_configuration_catalog(source_catalog)
        if source_catalog.target_fingerprint_schema_version not in (None, 2):
            raise HardwareCatalogIntegrityError('Unsupported Target fingerprint version.')
        for package, expected in source_catalog.required_versions.items():
            if _package_version(package) != expected:
                raise HardwareCatalogIntegrityError(
                    f'Version {package} differs from the catalog requirement.'
                )
        self._configuration_catalog = _copy_configuration_catalog(
            source_catalog
        )
        unsupported = sorted(
            set(self._device_names) - set(DEVICE_DEFINITIONS)
        )
        if unsupported:
            raise ValueError(
                'Devices without an explicit hardware definition: '
                + ", ".join(unsupported)
            )
        for device_id in self._device_names:
            definition = DEVICE_DEFINITIONS[device_id]
            registered_gates = tuple(
                sorted(map(str, get_gateset(definition.native_gateset_id)))
            )
            declared_gates = tuple(sorted(definition.native_gate_ids))
            if registered_gates != declared_gates:
                raise HardwareCatalogIntegrityError(
                    f'Inconsistent static native gates for {device_id}: declared={declared_gates!r}, MQT={registered_gates!r}.'
                )
        configured = set(
            self._configuration_catalog.supported_device_ids
        )
        outside_configuration_catalog = sorted(
            set(self._device_names) - configured
        )
        if outside_configuration_catalog:
            raise ValueError(
                'Device outside the Qiskit catalog: '
                + ", ".join(outside_configuration_catalog)
            )
        self._snapshot: HardwareCatalogSnapshot | None = None

    def _profile(self, device_id: str) -> HardwareProfile:
        'Build the verified profile of one device.'
        definition = DEVICE_DEFINITIONS[device_id]
        configuration_ids = tuple(
            configuration.config_id
            for configuration in self._configuration_catalog.configurations
        )
        base_metadata = {
            "target_source": "mqt.bench.targets.get_device",
            "native_gateset_id": definition.native_gateset_id,
            "target_fingerprint_algorithm": TARGET_FINGERPRINT_ALGORITHM,
            "calibration_kind": "synthetic_deterministic_target",
            "live_hardware_data": False,
        }
        try:
            target = get_device(device_id)
            target_payload = _target_payload(target)
            num_qubits, operation_names, edges = _validated_target_shape(
                device_id,
                definition,
                target_payload,
            )
            coupling_type = (
                "global_unconstrained"
                if target_payload["all_to_all"]
                else _coupling_kind(num_qubits, edges)
            )
            coupling_hash = _digest(
                {
                    "type": coupling_type,
                    "num_qubits": num_qubits,
                    "edges": edges,
                }
            )
            target_hash = _digest(target_payload)
            expected_hash = self._configuration_catalog.target_sha256.get(device_id)
            if expected_hash is not None and target_hash != expected_hash:
                raise HardwareCatalogIntegrityError(
                    f'Target {device_id} differs from the frozen catalog fingerprint.'
                )
            instruction_properties_hash = _digest(
                target_payload["instructions"]
            )
            return HardwareProfile(
                device_id=device_id,
                provider_id=definition.provider_id,
                num_qubits=num_qubits,
                operation_names=operation_names,
                native_gate_ids=definition.native_gate_ids,
                coupling_edges=edges,
                coupling_type=coupling_type,
                target_hash=target_hash,
                supported_figure_of_merit_ids=("expected_fidelity",),
                allowed_qiskit_configuration_ids=configuration_ids,
                target_available=True,
                metadata={
                    **base_metadata,
                    "target_type": target_payload["target_type"],
                    "coupling_hash": coupling_hash,
                    "instruction_properties_hash": (
                        instruction_properties_hash
                    ),
                },
            )
        except HardwareCatalogIntegrityError:
            raise
        except Exception as exc:
            return HardwareProfile(
                device_id=device_id,
                provider_id=definition.provider_id,
                num_qubits=definition.expected_num_qubits,
                operation_names=(),
                native_gate_ids=definition.native_gate_ids,
                coupling_edges=(),
                coupling_type="unavailable",
                supported_figure_of_merit_ids=("expected_fidelity",),
                allowed_qiskit_configuration_ids=configuration_ids,
                target_available=False,
                metadata={
                    **base_metadata,
                    "unavailability_code": TARGET_UNAVAILABILITY_CODE,
                    "load_error_type": type(exc).__name__,
                },
            )

    def snapshot(self) -> HardwareCatalogSnapshot:
        'Return the immutable snapshot, building it only once.'
        if self._snapshot is not None:
            return self._snapshot

        profiles = tuple(
            self._profile(device_id) for device_id in self._device_names
        )
        provider_ids = tuple(
            sorted({profile.provider_id for profile in profiles})
        )
        providers = tuple(
            ProviderProfile(
                provider_id=provider_id,
                display_name=PROVIDER_NAMES[provider_id],
            )
            for provider_id in provider_ids
        )
        configuration_material = _configuration_material(
            self._configuration_catalog
        )
        configuration_digest = _digest(configuration_material)
        provenance = {
            "fingerprint_algorithm": FINGERPRINT_ALGORITHM,
            "configuration_catalog_digest": configuration_digest,
            "package_versions": {
                "mqt.bench": _package_version("mqt.bench"),
                "mqt.predictor": _package_version("mqt.predictor"),
                "qiskit": _package_version("qiskit"),
            },
        }
        snapshot_material = {
            "schema_version": HARDWARE_CATALOG_SCHEMA_VERSION,
            "source_kind": "synthetic_mqt_target",
            "configuration_catalog_id": (
                self._configuration_catalog.catalog_id
            ),
            "providers": [provider.to_dict() for provider in providers],
            "devices": [profile.to_dict() for profile in profiles],
            "supported_figure_of_merit_ids": ["expected_fidelity"],
            "qiskit_configuration_ids": [
                configuration.config_id
                for configuration in self._configuration_catalog.configurations
            ],
            "provenance": provenance,
        }
        snapshot = HardwareCatalogSnapshot(
            schema_version=HARDWARE_CATALOG_SCHEMA_VERSION,
            catalog_snapshot_id=(
                "hardware_catalog_" + _digest(snapshot_material)
            ),
            source_kind="synthetic_mqt_target",
            configuration_catalog_id=(
                self._configuration_catalog.catalog_id
            ),
            providers=providers,
            devices=profiles,
            supported_figure_of_merit_ids=("expected_fidelity",),
            qiskit_configuration_ids=tuple(
                configuration.config_id
                for configuration in self._configuration_catalog.configurations
            ),
            provenance=provenance,
        )
        issues = validate_instance(
            CATALOG_SCHEMA,
            snapshot.to_dict(),
            error_code="HARDWARE_CATALOG_SCHEMA_INVALID",
        )
        if issues:
            rendered = "; ".join(
                f"{issue.path}: {issue.message}" for issue in issues
            )
            raise RuntimeError(
                f'Invalid canonical hardware catalog: {rendered}'
            )
        self._snapshot = snapshot
        return snapshot

    def list_hardware(self) -> tuple[HardwareProfile, ...]:
        'Expose profiles in the format retained for compatibility.'
        return self.snapshot().devices


def _build_mask(
    request: ParsedRequest,
    profiles: Sequence[HardwareProfile],
    *,
    catalog_snapshot_id: str,
) -> HardwareMaskResult:
    'Apply all constraints and record exclusion reasons.'
    constraints = request.hardware_constraints
    allowed_providers = set(constraints.allowed_provider_ids)
    allowed_devices = set(constraints.allowed_device_ids)
    required_gates = set(constraints.required_native_gate_ids)
    qubit_range = constraints.device_qubits
    minimum = qubit_range.minimum if qubit_range is not None else None
    maximum = qubit_range.maximum if qubit_range is not None else None
    effective_minimum = max(
        request.num_qubits,
        minimum if minimum is not None else request.num_qubits,
    )

    ordered_profiles = tuple(
        sorted(profiles, key=lambda profile: profile.device_id)
    )
    if len(ordered_profiles) != len(
        {profile.device_id for profile in ordered_profiles}
    ):
        raise ValueError('The mask does not accept duplicate device_id values.')

    available: list[HardwareProfile] = []
    diagnostics: list[DeviceExclusionDiagnostic] = []
    mask: list[bool] = []

    for profile in ordered_profiles:
        reasons: list[DeviceExclusionReason] = []
        details: dict[str, Any] = {}

        if (
            allowed_providers
            and profile.provider_id not in allowed_providers
        ):
            reasons.append(DeviceExclusionReason.PROVIDER_NOT_ALLOWED)
            details["actual_provider_id"] = profile.provider_id
            details["allowed_provider_ids"] = sorted(allowed_providers)
        if allowed_devices and profile.device_id not in allowed_devices:
            reasons.append(DeviceExclusionReason.DEVICE_NOT_ALLOWED)
            details["allowed_device_ids"] = sorted(allowed_devices)
        if request.num_qubits > profile.num_qubits:
            reasons.append(
                DeviceExclusionReason.INSUFFICIENT_QUBITS_FOR_CIRCUIT
            )
            details["circuit_num_qubits"] = request.num_qubits
            details["device_num_qubits"] = profile.num_qubits
        if minimum is not None and profile.num_qubits < minimum:
            reasons.append(DeviceExclusionReason.BELOW_USER_MIN_QUBITS)
            details["requested_min_qubits"] = minimum
            details["device_num_qubits"] = profile.num_qubits
        if maximum is not None and profile.num_qubits > maximum:
            reasons.append(DeviceExclusionReason.ABOVE_USER_MAX_QUBITS)
            details["requested_max_qubits"] = maximum
            details["device_num_qubits"] = profile.num_qubits
        missing_gates = tuple(
            sorted(
                required_gates
                - set(profile.selectable_native_gate_ids)
            )
        )
        if missing_gates:
            reasons.append(
                DeviceExclusionReason.MISSING_REQUIRED_NATIVE_GATE
            )
            details["missing_native_gate_ids"] = list(missing_gates)
        if (
            request.figure_of_merit
            not in profile.supported_figure_of_merit_ids
        ):
            reasons.append(
                DeviceExclusionReason.FIGURE_OF_MERIT_NOT_SUPPORTED
            )
            details["figure_of_merit_id"] = request.figure_of_merit
            details["supported_figure_of_merit_ids"] = list(
                profile.supported_figure_of_merit_ids
            )
        if not profile.target_available:
            reasons.append(DeviceExclusionReason.TARGET_NOT_AVAILABLE)
            unavailability_code = profile.metadata.get(
                "unavailability_code"
            )
            if unavailability_code:
                details["target_unavailability_code"] = (
                    unavailability_code
                )
            load_error_type = profile.metadata.get("load_error_type")
            if load_error_type:
                details["target_load_error_type"] = load_error_type

        is_available = not reasons
        mask.append(is_available)
        if is_available:
            available.append(profile)
        else:
            diagnostics.append(
                DeviceExclusionDiagnostic(
                    device_id=profile.device_id,
                    reason_codes=tuple(reasons),
                    details=details,
                )
            )

    result = HardwareMaskResult(
        schema_version=HARDWARE_MASK_SCHEMA_VERSION,
        catalog_snapshot_id=catalog_snapshot_id,
        ordered_device_ids=tuple(
            profile.device_id for profile in ordered_profiles
        ),
        mask=tuple(mask),
        available=tuple(available),
        excluded_devices=tuple(diagnostics),
        effective_min_qubits=effective_minimum,
        normalized_constraints=constraints,
    )
    issues = validate_instance(
        MASK_SCHEMA,
        result.to_dict(),
        error_code="HARDWARE_MASK_SCHEMA_INVALID",
    )
    if issues:
        rendered = "; ".join(
            f"{issue.path}: {issue.message}" for issue in issues
        )
        raise RuntimeError(
            f'Invalid canonical hardware mask: {rendered}'
        )
    return result


class HardwareMaskBuilder:
    'Build the mask from the normalized request and snapshot.'

    def filter(
        self,
        request: NormalizedRequest,
        hardware: HardwareCatalogSnapshot,
    ) -> HardwareMaskResult:
        'Check types and build a mask over the current snapshot.'
        if not isinstance(request, NormalizedRequest):
            raise TypeError(
                'HardwareMaskBuilder requires a NormalizedRequest.'
            )
        if not isinstance(hardware, HardwareCatalogSnapshot):
            raise TypeError(
                'HardwareMaskBuilder requires a HardwareCatalogSnapshot.'
            )
        if request.catalog_snapshot_id != hardware.catalog_snapshot_id:
            raise ValueError(
                'The normalized request and mask use different snapshots.'
            )
        return _build_mask(
            request,
            hardware.devices,
            catalog_snapshot_id=hardware.catalog_snapshot_id,
        )


class WidthCompatibilityFilter(HardwareMaskBuilder):
    """Retain the legacy entry point based on a sequence of profiles.

    The current service uses ``HardwareMaskBuilder``. A sequence still returns
    the earlier ``CompatibilityReport``.
    """

    def filter(
        self,
        request: ParsedRequest,
        hardware: HardwareCatalogSnapshot | Sequence[HardwareProfile],
    ) -> HardwareMaskResult | CompatibilityReport:
        'Use the current flow or adapt the legacy hardware format.'
        if isinstance(hardware, HardwareCatalogSnapshot):
            return super().filter(request, hardware)  # type: ignore[arg-type]

        profiles = tuple(hardware)
        if any(not isinstance(profile, HardwareProfile) for profile in profiles):
            raise TypeError('The legacy filter accepts HardwareProfile only.')
        result = _build_mask(
            request,
            profiles,
            catalog_snapshot_id="ad_hoc_catalog",
        )
        unavailable = dict(result.unavailable)
        profile_ids = {profile.device_id for profile in profiles}
        for unknown_id in sorted(
            set(request.allowed_devices) - profile_ids
        ):
            unavailable[unknown_id] = ("not_in_hardware_catalog",)
        return CompatibilityReport(
            available=result.available,
            unavailable=unavailable,
        )

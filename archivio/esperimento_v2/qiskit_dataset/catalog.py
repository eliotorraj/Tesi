'Define and validate allowed Qiskit Dataset configurations.'

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from scripts.mqt_predictor_protocol import LEGACY_ROOT


PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_CATALOG_PATH = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations_v2.json"
DEFAULT_CATALOG_PATH = V2_CATALOG_PATH
LEGACY_CATALOG_PATH = LEGACY_ROOT / "configs" / "qiskit_dataset_configurations.json"


@dataclass(frozen=True)
class QiskitConfiguration:
    'Represent a Qiskit configuration allowed by the catalog.'

    config_id: str
    study: str
    optimization_level: int
    layout_method: str | None
    routing_method: str | None

    @property
    def key(self) -> tuple[int, str | None, str | None]:
        'Return the three values identifying a configuration.'
        return (self.optimization_level, self.layout_method, self.routing_method)

    def to_dict(self) -> dict[str, Any]:
        'Convert the configuration into a JSON-ready object.'
        return {
            "config_id": self.config_id,
            "study": self.study,
            "optimization_level": self.optimization_level,
            "layout_method": self.layout_method,
            "routing_method": self.routing_method,
        }

    def transpile_kwargs(self) -> dict[str, Any]:
        'Prepare Qiskit options, omitting defaults.'
        kwargs: dict[str, Any] = {"optimization_level": self.optimization_level}
        if self.layout_method is not None:
            kwargs["layout_method"] = self.layout_method
        if self.routing_method is not None:
            kwargs["routing_method"] = self.routing_method
        return kwargs


@dataclass(frozen=True)
class ConfigurationCatalog:
    'Collect experiment devices, configurations and parameters.'

    schema_version: str
    catalog_id: str
    default_device_id: str
    supported_device_ids: tuple[str, ...]
    objective: Mapping[str, Any]
    seeds: tuple[int, ...]
    fixed_transpile_options: Mapping[str, Any]
    configurations: tuple[QiskitConfiguration, ...]
    experiment_id: str | None = None
    protocol_version: str | None = None
    required_versions: Mapping[str, str] = field(default_factory=dict)
    target_sha256: Mapping[str, str] = field(default_factory=dict)
    target_fingerprint_schema_version: int | None = None
    execution_policy: Mapping[str, Any] = field(default_factory=dict)

    @property
    def allowed_keys(self) -> frozenset[tuple[int, str | None, str | None]]:
        'Return the option combinations allowed by the catalog.'
        return frozenset(configuration.key for configuration in self.configurations)

    @property
    def by_id(self) -> dict[str, QiskitConfiguration]:
        'Index configurations by identifier.'
        return {
            configuration.config_id: configuration
            for configuration in self.configurations
        }

    @property
    def device_id(self) -> str:
        'Retain the legacy name for the default device.'
        return self.default_device_id

    def require_device(self, device_id: str | None = None) -> str:
        'Return the requested device only if it belongs to the catalog.'
        selected = self.default_device_id if device_id is None else str(device_id)
        if selected not in self.supported_device_ids:
            allowed = ", ".join(self.supported_device_ids)
            raise ValueError(
                f'Device outside the catalog: {selected!r}. Allowed: {allowed}.'
            )
        return selected

    def find(
        self,
        optimization_level: int,
        layout_method: str | None,
        routing_method: str | None,
    ) -> QiskitConfiguration | None:
        'Find the configuration matching the supplied options.'
        key = (optimization_level, layout_method, routing_method)
        return next(
            (
                configuration
                for configuration in self.configurations
                if configuration.key == key
            ),
            None,
        )

    def require_allowed(
        self,
        optimization_level: int,
        layout_method: str | None,
        routing_method: str | None,
    ) -> QiskitConfiguration:
        'Return an allowed configuration or report an error.'
        configuration = self.find(
            optimization_level,
            layout_method,
            routing_method,
        )
        if configuration is None:
            raise ValueError(
                f'Qiskit configuration outside the catalog: ({optimization_level!r}, {layout_method!r}, {routing_method!r}).'
            )
        return configuration


def _strict_int(value: Any, field: str) -> int:
    'Accept only an actual integer, excluding booleans.'
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f'{field} must be an integer.')
    return value


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> ConfigurationCatalog:
    'Read the catalog and fail immediately if it is invalid.'
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    raw_configurations = raw.get("configurations")
    if not isinstance(raw_configurations, list):
        raise ValueError('configurations must be a list.')
    configurations: list[QiskitConfiguration] = []
    for index, item in enumerate(raw_configurations):
        if not isinstance(item, dict):
            raise ValueError(f'configurations[{index}] must be an object.')
        configurations.append(
            QiskitConfiguration(
                config_id=str(item["config_id"]),
                study=str(item["study"]),
                optimization_level=_strict_int(
                    item["optimization_level"],
                    f"configurations[{index}].optimization_level",
                ),
                layout_method=item.get("layout_method"),
                routing_method=item.get("routing_method"),
            )
        )

    seeds = tuple(_strict_int(value, "seed") for value in raw.get("seeds", ()))
    default_device_id = raw.get("default_device_id", raw.get("device_id"))
    catalog = ConfigurationCatalog(
        schema_version=str(raw["schema_version"]),
        catalog_id=str(raw["catalog_id"]),
        default_device_id=str(default_device_id),
        supported_device_ids=tuple(
            str(value)
            for value in raw.get(
                "supported_device_ids",
                (default_device_id,),
            )
        ),
        objective=dict(raw["objective"]),
        seeds=seeds,
        fixed_transpile_options=dict(raw.get("fixed_transpile_options", {})),
        configurations=tuple(configurations),
        experiment_id=(
            str(raw["experiment_id"])
            if raw.get("experiment_id") is not None
            else None
        ),
        protocol_version=(
            str(raw["protocol_version"])
            if raw.get("protocol_version") is not None
            else None
        ),
        required_versions={
            str(name): str(value)
            for name, value in raw.get("required_versions", {}).items()
        },
        target_sha256={
            str(name): str(value)
            for name, value in raw.get("target_sha256", {}).items()
        },
        target_fingerprint_schema_version=(
            _strict_int(
                raw["target_fingerprint_schema_version"],
                "target_fingerprint_schema_version",
            )
            if raw.get("target_fingerprint_schema_version") is not None
            else None
        ),
        execution_policy=dict(raw.get("execution_policy", {})),
    )
    _validate_catalog(catalog)
    return catalog


def _validate_catalog(catalog: ConfigurationCatalog) -> None:
    'Check that the catalog follows the experimental protocol.'
    if len(catalog.configurations) != 12:
        raise ValueError(
            f'The catalog must contain exactly 12 configurations, not {len(catalog.configurations)}.'
        )
    identifiers = [
        configuration.config_id for configuration in catalog.configurations
    ]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate config_id in the catalog.')
    keys = [configuration.key for configuration in catalog.configurations]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate Qiskit tuples in the catalog.')
    if len(catalog.seeds) != 3 or len(set(catalog.seeds)) != 3:
        raise ValueError('The catalog must define exactly three distinct seeds.')
    if any(seed < 0 or seed > 2**32 - 1 for seed in catalog.seeds):
        raise ValueError('Seeds must be between 0 and 2^32-1.')
    if not catalog.supported_device_ids:
        raise ValueError('The catalog must define at least one device.')
    if len(catalog.supported_device_ids) != len(set(catalog.supported_device_ids)):
        raise ValueError('Duplicate device in the catalog.')
    if catalog.default_device_id not in catalog.supported_device_ids:
        raise ValueError('The default device must be among the supported devices.')
    if catalog.objective.get("name") != "expected_fidelity":
        raise ValueError('This version allows expected_fidelity only.')
    if catalog.experiment_id is not None:
        if re.fullmatch(r"[A-Za-z0-9_.-]+", catalog.experiment_id) is None:
            raise ValueError('experiment_id contains invalid characters.')
        if catalog.protocol_version is None:
            raise ValueError('The v2 catalog must declare protocol_version.')
        missing_versions = sorted(
            {
                "mqt.predictor",
                "mqt.bench",
                "qiskit",
            }
            - set(catalog.required_versions)
        )
        if missing_versions:
            raise ValueError(
                'Required versions missing from the v2 catalog: '
                + ", ".join(missing_versions)
            )
        if set(catalog.target_sha256) != set(catalog.supported_device_ids):
            raise ValueError(
                'The v2 catalog must freeze a Target for every device.'
            )
        if catalog.target_fingerprint_schema_version != 2:
            raise ValueError(
                'The v2 catalog requires target_fingerprint_schema_version=2.'
            )
        if set(catalog.execution_policy) != {"workers", "timeout_seconds"}:
            raise ValueError(
                'The v2 catalog must fix workers and timeout_seconds.'
            )
        workers = catalog.execution_policy["workers"]
        timeout = catalog.execution_policy["timeout_seconds"]
        if isinstance(workers, bool) or not isinstance(workers, int) or workers <= 0:
            raise ValueError('execution_policy.workers must be positive.')
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or timeout <= 0
        ):
            raise ValueError(
                'execution_policy.timeout_seconds must be positive.'
            )

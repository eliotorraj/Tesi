"""Versioned allowlist for the Qiskit Dataset experiment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations.json"


@dataclass(frozen=True)
class QiskitConfiguration:
    """One complete allowlisted Qiskit configuration."""

    config_id: str
    study: str
    optimization_level: int
    layout_method: str | None
    routing_method: str | None

    @property
    def key(self) -> tuple[int, str | None, str | None]:
        return (self.optimization_level, self.layout_method, self.routing_method)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_id": self.config_id,
            "study": self.study,
            "optimization_level": self.optimization_level,
            "layout_method": self.layout_method,
            "routing_method": self.routing_method,
        }

    def transpile_kwargs(self) -> dict[str, Any]:
        """Return user-controlled kwargs; None means Qiskit's default."""
        kwargs: dict[str, Any] = {"optimization_level": self.optimization_level}
        if self.layout_method is not None:
            kwargs["layout_method"] = self.layout_method
        if self.routing_method is not None:
            kwargs["routing_method"] = self.routing_method
        return kwargs


@dataclass(frozen=True)
class ConfigurationCatalog:
    schema_version: str
    catalog_id: str
    default_device_id: str
    supported_device_ids: tuple[str, ...]
    objective: Mapping[str, Any]
    seeds: tuple[int, ...]
    fixed_transpile_options: Mapping[str, Any]
    configurations: tuple[QiskitConfiguration, ...]

    @property
    def allowed_keys(self) -> frozenset[tuple[int, str | None, str | None]]:
        return frozenset(configuration.key for configuration in self.configurations)

    @property
    def by_id(self) -> dict[str, QiskitConfiguration]:
        return {
            configuration.config_id: configuration
            for configuration in self.configurations
        }

    @property
    def device_id(self) -> str:
        """Backward-compatible alias for the default device."""
        return self.default_device_id

    def require_device(self, device_id: str | None = None) -> str:
        selected = self.default_device_id if device_id is None else str(device_id)
        if selected not in self.supported_device_ids:
            allowed = ", ".join(self.supported_device_ids)
            raise ValueError(
                f"Device fuori catalogo: {selected!r}. Ammessi: {allowed}."
            )
        return selected

    def find(
        self,
        optimization_level: int,
        layout_method: str | None,
        routing_method: str | None,
    ) -> QiskitConfiguration | None:
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
        configuration = self.find(
            optimization_level,
            layout_method,
            routing_method,
        )
        if configuration is None:
            raise ValueError(
                "Configurazione Qiskit fuori catalogo: "
                f"({optimization_level!r}, {layout_method!r}, "
                f"{routing_method!r})."
            )
        return configuration


def _strict_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} deve essere un intero.")
    return value


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> ConfigurationCatalog:
    """Load and fail-fast validate the experiment catalog."""
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    raw_configurations = raw.get("configurations")
    if not isinstance(raw_configurations, list):
        raise ValueError("configurations deve essere una lista.")
    configurations: list[QiskitConfiguration] = []
    for index, item in enumerate(raw_configurations):
        if not isinstance(item, dict):
            raise ValueError(f"configurations[{index}] deve essere un oggetto.")
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
    catalog = ConfigurationCatalog(
        schema_version=str(raw["schema_version"]),
        catalog_id=str(raw["catalog_id"]),
        default_device_id=str(
            raw.get("default_device_id", raw.get("device_id"))
        ),
        supported_device_ids=tuple(
            str(value)
            for value in raw.get(
                "supported_device_ids",
                (raw.get("default_device_id", raw.get("device_id")),),
            )
        ),
        objective=dict(raw["objective"]),
        seeds=seeds,
        fixed_transpile_options=dict(raw.get("fixed_transpile_options", {})),
        configurations=tuple(configurations),
    )
    _validate_catalog(catalog)
    return catalog


def _validate_catalog(catalog: ConfigurationCatalog) -> None:
    if len(catalog.configurations) != 12:
        raise ValueError(
            "Il catalogo deve contenere esattamente 12 configurazioni, "
            f"non {len(catalog.configurations)}."
        )
    identifiers = [
        configuration.config_id for configuration in catalog.configurations
    ]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("config_id duplicato nel catalogo.")
    keys = [configuration.key for configuration in catalog.configurations]
    if len(keys) != len(set(keys)):
        raise ValueError("Tuple Qiskit duplicate nel catalogo.")
    if len(catalog.seeds) != 3 or len(set(catalog.seeds)) != 3:
        raise ValueError("Il catalogo deve definire esattamente tre seed distinti.")
    if any(seed < 0 or seed > 2**32 - 1 for seed in catalog.seeds):
        raise ValueError("I seed devono essere compresi tra 0 e 2^32-1.")
    if not catalog.supported_device_ids:
        raise ValueError("Il catalogo deve definire almeno un device.")
    if len(catalog.supported_device_ids) != len(set(catalog.supported_device_ids)):
        raise ValueError("Device duplicato nel catalogo.")
    if catalog.default_device_id not in catalog.supported_device_ids:
        raise ValueError("Il device di default deve essere tra quelli supportati.")
    if catalog.objective.get("name") != "expected_fidelity":
        raise ValueError("Questa versione ammette soltanto expected_fidelity.")

"""Definisce e valida le configurazioni ammesse per il Dataset Qiskit."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "configs" / "qiskit_dataset_configurations.json"


@dataclass(frozen=True)
class QiskitConfiguration:
    """Rappresenta una configurazione Qiskit ammessa dal catalogo."""

    config_id: str
    study: str
    optimization_level: int
    layout_method: str | None
    routing_method: str | None

    @property
    def key(self) -> tuple[int, str | None, str | None]:
        """Restituisce i tre valori che identificano la configurazione."""
        return (self.optimization_level, self.layout_method, self.routing_method)

    def to_dict(self) -> dict[str, Any]:
        """Converte la configurazione in un oggetto pronto per il JSON."""
        return {
            "config_id": self.config_id,
            "study": self.study,
            "optimization_level": self.optimization_level,
            "layout_method": self.layout_method,
            "routing_method": self.routing_method,
        }

    def transpile_kwargs(self) -> dict[str, Any]:
        """Prepara le opzioni da passare a Qiskit, omettendo quelle di default."""
        kwargs: dict[str, Any] = {"optimization_level": self.optimization_level}
        if self.layout_method is not None:
            kwargs["layout_method"] = self.layout_method
        if self.routing_method is not None:
            kwargs["routing_method"] = self.routing_method
        return kwargs


@dataclass(frozen=True)
class ConfigurationCatalog:
    """Raccoglie dispositivi, configurazioni e parametri dell'esperimento."""

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
        """Restituisce le combinazioni di opzioni ammesse dal catalogo."""
        return frozenset(configuration.key for configuration in self.configurations)

    @property
    def by_id(self) -> dict[str, QiskitConfiguration]:
        """Indicizza le configurazioni tramite il loro identificatore."""
        return {
            configuration.config_id: configuration
            for configuration in self.configurations
        }

    @property
    def device_id(self) -> str:
        """Mantiene il vecchio nome usato per il dispositivo predefinito."""
        return self.default_device_id

    def require_device(self, device_id: str | None = None) -> str:
        """Restituisce il dispositivo richiesto solo se è presente nel catalogo."""
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
        """Cerca la configurazione che corrisponde alle opzioni ricevute."""
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
        """Restituisce una configurazione ammessa oppure segnala l'errore."""
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
    """Accetta soltanto un intero vero, escludendo anche i valori booleani."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} deve essere un intero.")
    return value


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> ConfigurationCatalog:
    """Legge il catalogo e interrompe subito il flusso se non è valido."""
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
    """Controlla che il catalogo rispetti il protocollo sperimentale."""
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
    if catalog.experiment_id is not None:
        if re.fullmatch(r"[A-Za-z0-9_.-]+", catalog.experiment_id) is None:
            raise ValueError("experiment_id contiene caratteri non ammessi.")
        if catalog.protocol_version is None:
            raise ValueError("Il catalogo v2 deve dichiarare protocol_version.")
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
                "Versioni richieste mancanti nel catalogo v2: "
                + ", ".join(missing_versions)
            )
        if set(catalog.target_sha256) != set(catalog.supported_device_ids):
            raise ValueError(
                "Il catalogo v2 deve congelare un Target per ogni device."
            )
        if catalog.target_fingerprint_schema_version != 2:
            raise ValueError(
                "Il catalogo v2 richiede target_fingerprint_schema_version=2."
            )
        if set(catalog.execution_policy) != {"workers", "timeout_seconds"}:
            raise ValueError(
                "Il catalogo v2 deve fissare workers e timeout_seconds."
            )
        workers = catalog.execution_policy["workers"]
        timeout = catalog.execution_policy["timeout_seconds"]
        if isinstance(workers, bool) or not isinstance(workers, int) or workers <= 0:
            raise ValueError("execution_policy.workers deve essere positivo.")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or timeout <= 0
        ):
            raise ValueError(
                "execution_policy.timeout_seconds deve essere positivo."
            )

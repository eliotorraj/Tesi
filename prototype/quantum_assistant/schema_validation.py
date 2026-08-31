"""Validazione locale del sottoinsieme JSON Schema usato dal progetto.

Il progetto non dipende da ``jsonschema``. Questo modulo controlla i dati
rispetto agli schemi Draft 2020-12 presenti nel repository e accetta soltanto
le parole chiave necessarie a tali schemi.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from uuid import UUID

from .models import ValidationIssue


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = PROJECT_ROOT / "schemas"
MAX_REQUEST_BYTES = 2_100_000


class _DuplicateKeyError(ValueError):
    """Segnala una chiave ripetuta nello stesso oggetto JSON."""


_SUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "$defs",
        "$id",
        "$ref",
        "$schema",
        "additionalProperties",
        "const",
        "enum",
        "format",
        "items",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "pattern",
        "properties",
        "required",
        "title",
        "type",
        "uniqueItems",
    }
)
_SUPPORTED_TYPES = frozenset(
    {"array", "boolean", "integer", "null", "number", "object", "string"}
)


def ensure_supported_schema(schema: Mapping[str, Any]) -> None:
    """Rifiuta uno schema che usa regole non gestite dal validatore locale."""

    def visit(node: Mapping[str, Any], path: str) -> None:
        """Controlla ricorsivamente un nodo dello schema."""
        unknown = sorted(set(node) - _SUPPORTED_SCHEMA_KEYWORDS)
        if unknown:
            raise ValueError(
                f"Keyword JSON Schema non supportate in {path}: "
                + ", ".join(unknown)
            )
        reference = node.get("$ref")
        if reference is not None:
            if not isinstance(reference, str) or not reference.startswith("#/"):
                raise ValueError(f"$ref non locale o non valido in {path}.")
            if set(node) != {"$ref"}:
                raise ValueError(
                    f"I sibling di $ref non sono supportati in {path}."
                )
            return

        expected_type = node.get("type")
        if expected_type is not None and (
            not isinstance(expected_type, str)
            or expected_type not in _SUPPORTED_TYPES
        ):
            raise ValueError(f"type non supportato in {path}: {expected_type!r}.")
        schema_format = node.get("format")
        if schema_format is not None and schema_format != "uuid":
            raise ValueError(f"format non supportato in {path}: {schema_format!r}.")
        pattern = node.get("pattern")
        if isinstance(pattern, str):
            re.compile(pattern)

        for container_name in ("$defs", "properties"):
            children = node.get(container_name)
            if children is None:
                continue
            if not isinstance(children, Mapping):
                raise ValueError(f"{path}.{container_name} deve essere un oggetto.")
            for name, child in children.items():
                if not isinstance(child, Mapping):
                    raise ValueError(
                        f"{path}.{container_name}.{name} deve essere uno schema."
                    )
                visit(child, f"{path}.{container_name}.{name}")

        item_schema = node.get("items")
        if item_schema is not None:
            if not isinstance(item_schema, Mapping):
                raise ValueError(f"{path}.items deve essere uno schema.")
            visit(item_schema, f"{path}.items")

        additional = node.get("additionalProperties")
        if isinstance(additional, Mapping):
            visit(additional, f"{path}.additionalProperties")
        elif additional is not None and not isinstance(additional, bool):
            raise ValueError(
                f"{path}.additionalProperties deve essere booleano o schema."
            )

    visit(schema, "$")


def load_schema(file_name: str) -> dict[str, Any]:
    """Carica uno schema del progetto e verifica che sia supportato."""
    path = SCHEMA_ROOT / file_name
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError(f"{path} non dichiara JSON Schema Draft 2020-12.")
    ensure_supported_schema(schema)
    return schema


def decode_json_object(
    document: str | bytes,
    *,
    max_bytes: int = MAX_REQUEST_BYTES,
) -> dict[str, Any]:
    """Decodifica un oggetto JSON rifiutando duplicati e numeri non finiti."""
    if isinstance(document, bytes):
        raw_bytes = document
        try:
            text = document.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("La richiesta deve essere UTF-8.") from exc
    else:
        text = document
        raw_bytes = text.encode("utf-8")
    if len(raw_bytes) > max_bytes:
        raise ValueError(
            f"La richiesta supera il limite di {max_bytes} byte."
        )

    def object_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        """Costruisce un oggetto JSON e rileva le chiavi duplicate."""
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise _DuplicateKeyError(f"Chiave JSON duplicata: {key!r}.")
            result[key] = value
        return result

    def parse_constant(value: str) -> Any:
        """Rifiuta le costanti numeriche che JSON non ammette."""
        raise ValueError(f"Costante JSON non finita non ammessa: {value}.")

    try:
        value = json.loads(
            text,
            object_pairs_hook=object_pairs_hook,
            parse_constant=parse_constant,
        )
    except (json.JSONDecodeError, _DuplicateKeyError, ValueError) as exc:
        raise ValueError(f"JSON non valido: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("La richiesta JSON deve essere un oggetto.")
    return value


def _resolve_ref(root: Mapping[str, Any], reference: str) -> Mapping[str, Any]:
    """Risolve un riferimento locale all'interno dello schema."""
    if not reference.startswith("#/"):
        raise ValueError(f"$ref esterno non supportato: {reference}.")
    value: Any = root
    for part in reference[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or key not in value:
            raise ValueError(f"$ref non risolvibile: {reference}.")
        value = value[key]
    if not isinstance(value, Mapping):
        raise ValueError(f"$ref non punta a uno schema: {reference}.")
    return value


def _is_type(instance: Any, expected: str) -> bool:
    """Verifica un valore rispetto a un tipo JSON Schema supportato."""
    if expected == "object":
        return isinstance(instance, Mapping)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return (
            isinstance(instance, (int, float))
            and not isinstance(instance, bool)
            and math.isfinite(float(instance))
        )
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    raise ValueError(f"Tipo JSON Schema non supportato: {expected}.")


def _unique(items: Sequence[Any]) -> bool:
    """Controlla l'unicità di valori JSON anche se non sono hashabili."""
    encoded = [
        json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
        for item in items
    ]
    return len(encoded) == len(set(encoded))


def validate_instance(
    schema: Mapping[str, Any],
    instance: Any,
    *,
    error_code: str = "SCHEMA_INVALID",
) -> tuple[ValidationIssue, ...]:
    """Controlla un valore e restituisce errori stabili del progetto."""
    issues: list[ValidationIssue] = []

    def add(path: str, message: str) -> None:
        """Aggiunge un errore usando il codice richiesto dal chiamante."""
        issues.append(
            ValidationIssue(code=error_code, path=path, message=message)
        )

    def visit(
        current_schema: Mapping[str, Any],
        value: Any,
        path: str,
    ) -> None:
        """Applica ricorsivamente le regole dello schema al valore."""
        reference = current_schema.get("$ref")
        if isinstance(reference, str):
            visit(_resolve_ref(schema, reference), value, path)
            return

        if "const" in current_schema and value != current_schema["const"]:
            add(path, f"Valore atteso: {current_schema['const']!r}.")
            return
        enum = current_schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            add(path, f"Valore non appartenente all'enum: {value!r}.")
            return

        expected_type = current_schema.get("type")
        if isinstance(expected_type, str) and not _is_type(value, expected_type):
            add(path, f"Tipo atteso: {expected_type}.")
            return

        if isinstance(value, Mapping):
            required = current_schema.get("required", [])
            for name in required:
                if name not in value:
                    add(f"{path}.{name}", "Campo obbligatorio mancante.")
            properties = current_schema.get("properties", {})
            if not isinstance(properties, Mapping):
                properties = {}
            additional = current_schema.get("additionalProperties", True)
            for name, child in value.items():
                child_path = f"{path}.{name}"
                property_schema = properties.get(name)
                if isinstance(property_schema, Mapping):
                    visit(property_schema, child, child_path)
                elif additional is False:
                    add(child_path, "Campo sconosciuto non ammesso.")
                elif isinstance(additional, Mapping):
                    visit(additional, child, child_path)
            minimum_properties = current_schema.get("minProperties")
            if (
                isinstance(minimum_properties, int)
                and len(value) < minimum_properties
            ):
                add(path, f"Sono richieste almeno {minimum_properties} proprietà.")

        if isinstance(value, list):
            minimum_items = current_schema.get("minItems")
            maximum_items = current_schema.get("maxItems")
            if isinstance(minimum_items, int) and len(value) < minimum_items:
                add(path, f"Sono richiesti almeno {minimum_items} elementi.")
            if isinstance(maximum_items, int) and len(value) > maximum_items:
                add(path, f"Sono ammessi al massimo {maximum_items} elementi.")
            if current_schema.get("uniqueItems") is True and not _unique(value):
                add(path, "Gli elementi devono essere unici.")
            item_schema = current_schema.get("items")
            if isinstance(item_schema, Mapping):
                for index, child in enumerate(value):
                    visit(item_schema, child, f"{path}[{index}]")

        if isinstance(value, str):
            minimum_length = current_schema.get("minLength")
            maximum_length = current_schema.get("maxLength")
            if isinstance(minimum_length, int) and len(value) < minimum_length:
                add(path, f"Lunghezza minima: {minimum_length}.")
            if isinstance(maximum_length, int) and len(value) > maximum_length:
                add(path, f"Lunghezza massima: {maximum_length}.")
            pattern = current_schema.get("pattern")
            if isinstance(pattern, str) and re.search(pattern, value) is None:
                add(path, "Formato della stringa non valido.")
            if current_schema.get("format") == "uuid":
                try:
                    parsed = UUID(value)
                except (ValueError, AttributeError, TypeError):
                    add(path, "UUID non valido.")
                else:
                    if str(parsed) != value:
                        add(path, "UUID non in forma canonica.")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = current_schema.get("minimum")
            maximum = current_schema.get("maximum")
            if isinstance(minimum, (int, float)) and value < minimum:
                add(path, f"Valore minimo: {minimum}.")
            if isinstance(maximum, (int, float)) and value > maximum:
                add(path, f"Valore massimo: {maximum}.")

    visit(schema, instance, "$")
    return tuple(issues)

"""Local validation of the JSON Schema subset used by the project.

The project does not depend on ``jsonschema``. This module validates data
against the repository's Draft 2020-12 schemas and accepts only the keywords
required by those schemas.
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
from settings import SCHEMAS
SCHEMA_ROOT = SCHEMAS
MAX_REQUEST_BYTES = 2_100_000


class _DuplicateKeyError(ValueError):
    'Report a repeated key in the same JSON object.'


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
        "maxProperties",
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
    'Reject schemas using rules unsupported by the local validator.'

    def visit(node: Mapping[str, Any], path: str) -> None:
        'Recursively validate a schema node.'
        unknown = sorted(set(node) - _SUPPORTED_SCHEMA_KEYWORDS)
        if unknown:
            raise ValueError(
                f'Unsupported JSON Schema keywords in {path}: '
                + ", ".join(unknown)
            )
        reference = node.get("$ref")
        if reference is not None:
            if not isinstance(reference, str) or not reference.startswith("#/"):
                raise ValueError(f'Non-local or invalid $ref in {path}.')
            if set(node) != {"$ref"}:
                raise ValueError(
                    f'$ref siblings are not supported in {path}.'
                )
            return

        expected_type = node.get("type")
        type_names = expected_type if isinstance(expected_type, list) else [expected_type]
        if expected_type is not None and (
            not type_names
            or any(not isinstance(name, str) or name not in _SUPPORTED_TYPES for name in type_names)
        ):
            raise ValueError(f'unsupported type in {path}: {expected_type!r}.')
        schema_format = node.get("format")
        if schema_format is not None and schema_format != "uuid":
            raise ValueError(f'unsupported format in {path}: {schema_format!r}.')
        pattern = node.get("pattern")
        if isinstance(pattern, str):
            re.compile(pattern)

        for container_name in ("$defs", "properties"):
            children = node.get(container_name)
            if children is None:
                continue
            if not isinstance(children, Mapping):
                raise ValueError(f'{path}.{container_name} must be an object.')
            for name, child in children.items():
                if not isinstance(child, Mapping):
                    raise ValueError(
                        f'{path}.{container_name}.{name} must be a schema.'
                    )
                visit(child, f"{path}.{container_name}.{name}")

        item_schema = node.get("items")
        if item_schema is not None:
            if not isinstance(item_schema, Mapping):
                raise ValueError(f'{path}.items must be a schema.')
            visit(item_schema, f"{path}.items")

        additional = node.get("additionalProperties")
        if isinstance(additional, Mapping):
            visit(additional, f"{path}.additionalProperties")
        elif additional is not None and not isinstance(additional, bool):
            raise ValueError(
                f'{path}.additionalProperties must be a boolean or schema.'
            )

    visit(schema, "$")


def load_schema(file_name: str) -> dict[str, Any]:
    'Load a project schema and check that it is supported.'
    path = SCHEMA_ROOT / file_name
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError(f'{path} does not declare JSON Schema Draft 2020-12.')
    ensure_supported_schema(schema)
    return schema


def decode_json_object(
    document: str | bytes,
    *,
    max_bytes: int = MAX_REQUEST_BYTES,
) -> dict[str, Any]:
    'Decode a JSON object, rejecting duplicates and non-finite numbers.'
    if isinstance(document, bytes):
        raw_bytes = document
        try:
            text = document.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError('The request must be UTF-8.') from exc
    else:
        text = document
        raw_bytes = text.encode("utf-8")
    if len(raw_bytes) > max_bytes:
        raise ValueError(
            f'The request exceeds the limit of {max_bytes} bytes.'
        )

    def object_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        'Build a JSON object and detect duplicate keys.'
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise _DuplicateKeyError(f'Duplicate JSON key: {key!r}.')
            result[key] = value
        return result

    def parse_constant(value: str) -> Any:
        'Reject numeric constants not permitted by JSON.'
        raise ValueError(f'Non-finite JSON constant not allowed: {value}.')

    try:
        value = json.loads(
            text,
            object_pairs_hook=object_pairs_hook,
            parse_constant=parse_constant,
        )
    except (json.JSONDecodeError, _DuplicateKeyError, ValueError) as exc:
        raise ValueError(f'Invalid JSON: {exc}') from exc
    if not isinstance(value, dict):
        raise ValueError('The JSON request must be an object.')
    return value


def _resolve_ref(root: Mapping[str, Any], reference: str) -> Mapping[str, Any]:
    'Resolve a local reference within the schema.'
    if not reference.startswith("#/"):
        raise ValueError(f'External $ref not supported: {reference}.')
    value: Any = root
    for part in reference[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or key not in value:
            raise ValueError(f'Cannot resolve $ref: {reference}.')
        value = value[key]
    if not isinstance(value, Mapping):
        raise ValueError(f'$ref does not point to a schema: {reference}.')
    return value


def _is_type(instance: Any, expected: str) -> bool:
    'Check a value against a supported JSON Schema type.'
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
    raise ValueError(f'Unsupported JSON Schema type: {expected}.')


def _unique(items: Sequence[Any]) -> bool:
    'Check uniqueness of JSON values, including unhashable values.'
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
    'Validate a value and return stable project errors.'
    issues: list[ValidationIssue] = []

    def add(path: str, message: str) -> None:
        'Add an error using the caller-specified code.'
        issues.append(
            ValidationIssue(code=error_code, path=path, message=message)
        )

    def visit(
        current_schema: Mapping[str, Any],
        value: Any,
        path: str,
    ) -> None:
        'Recursively apply schema rules to the value.'
        reference = current_schema.get("$ref")
        if isinstance(reference, str):
            visit(_resolve_ref(schema, reference), value, path)
            return

        if "const" in current_schema and value != current_schema["const"]:
            add(path, f"Expected value: {current_schema['const']!r}.")
            return
        enum = current_schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            add(path, f'Value not in enum: {value!r}.')
            return

        expected_type = current_schema.get("type")
        type_names = expected_type if isinstance(expected_type, list) else [expected_type]
        if expected_type is not None and not any(_is_type(value, name) for name in type_names):
            add(path, f'Expected type: {expected_type}.')
            return

        if isinstance(value, Mapping):
            required = current_schema.get("required", [])
            for name in required:
                if name not in value:
                    add(f"{path}.{name}", 'Missing required field.')
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
                    add(child_path, 'Unknown field not allowed.')
                elif isinstance(additional, Mapping):
                    visit(additional, child, child_path)
            minimum_properties = current_schema.get("minProperties")
            if (
                isinstance(minimum_properties, int)
                and len(value) < minimum_properties
            ):
                add(path, f'At least {minimum_properties} properties.')
            maximum_properties = current_schema.get("maxProperties")
            if isinstance(maximum_properties, int) and len(value) > maximum_properties:
                add(path, f'At most {maximum_properties} properties.')

        if isinstance(value, list):
            minimum_items = current_schema.get("minItems")
            maximum_items = current_schema.get("maxItems")
            if isinstance(minimum_items, int) and len(value) < minimum_items:
                add(path, f'At least {minimum_items} items.')
            if isinstance(maximum_items, int) and len(value) > maximum_items:
                add(path, f'At most {maximum_items} items.')
            if current_schema.get("uniqueItems") is True and not _unique(value):
                add(path, 'Items must be unique.')
            item_schema = current_schema.get("items")
            if isinstance(item_schema, Mapping):
                for index, child in enumerate(value):
                    visit(item_schema, child, f"{path}[{index}]")

        if isinstance(value, str):
            minimum_length = current_schema.get("minLength")
            maximum_length = current_schema.get("maxLength")
            if isinstance(minimum_length, int) and len(value) < minimum_length:
                add(path, f'Minimum length: {minimum_length}.')
            if isinstance(maximum_length, int) and len(value) > maximum_length:
                add(path, f'Maximum length: {maximum_length}.')
            pattern = current_schema.get("pattern")
            if isinstance(pattern, str) and re.search(pattern, value) is None:
                add(path, 'Invalid string format.')
            if current_schema.get("format") == "uuid":
                try:
                    parsed = UUID(value)
                except (ValueError, AttributeError, TypeError):
                    add(path, 'Invalid UUID.')
                else:
                    if str(parsed) != value:
                        add(path, 'UUID is not in canonical form.')

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = current_schema.get("minimum")
            maximum = current_schema.get("maximum")
            if isinstance(minimum, (int, float)) and value < minimum:
                add(path, f'Minimum value: {minimum}.')
            if isinstance(maximum, (int, float)) and value > maximum:
                add(path, f'Maximum value: {maximum}.')

    visit(schema, instance, "$")
    return tuple(issues)

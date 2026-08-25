"""Deterministic validation of structured LLM recommendations."""

from __future__ import annotations

from typing import Any, Mapping

from qiskit_dataset.catalog import load_catalog

from ..models import (
    CompatibilityReport,
    ParsedRequest,
    QiskitCompilationPlan,
    Recommendation,
    ValidationResult,
)


QISKIT_CATALOG = load_catalog()


def _strict_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _string_tuple(value: Any, field_name: str, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        errors.append(f"{field_name} deve essere una lista di stringhe non vuote.")
        return ()
    return tuple(item.strip() for item in value)


class StructuredRecommendationValidator:
    """Validate every value that can influence deterministic compilation."""

    def validate(
        self,
        raw_response: Mapping[str, Any],
        request: ParsedRequest,
        compatibility: CompatibilityReport,
    ) -> ValidationResult:
        errors: list[str] = []
        if not isinstance(raw_response, Mapping):
            return ValidationResult(
                is_valid=False,
                errors=("La risposta LLM non e un oggetto JSON.",),
            )

        selected_device = raw_response.get("selected_device")
        if not isinstance(selected_device, str):
            errors.append("selected_device deve essere una stringa.")
            selected_device = ""
        elif selected_device not in compatibility.available_device_ids:
            errors.append(
                f"selected_device non compatibile o sconosciuto: {selected_device}."
            )

        metric = raw_response.get("figure_of_merit")
        if metric != request.figure_of_merit:
            errors.append(
                f"figure_of_merit deve essere {request.figure_of_merit!r}."
            )

        if raw_response.get("compiler") != "qiskit":
            errors.append("compiler deve essere 'qiskit'.")

        raw_plan = raw_response.get("qiskit_plan")
        if not isinstance(raw_plan, Mapping):
            errors.append("qiskit_plan deve essere un oggetto JSON.")
            raw_plan = {}

        optimization_level = _strict_int(raw_plan.get("optimization_level"))
        if optimization_level is None:
            errors.append("optimization_level deve essere un intero.")

        seed_transpiler = _strict_int(raw_plan.get("seed_transpiler"))
        if seed_transpiler is None or not 0 <= seed_transpiler <= 2**32 - 1:
            errors.append(
                "seed_transpiler deve essere un intero tra 0 e 2^32-1."
            )

        layout_method = raw_plan.get("layout_method")
        routing_method = raw_plan.get("routing_method")
        allowed_configuration = (
            None
            if optimization_level is None
            else QISKIT_CATALOG.find(
                optimization_level,
                layout_method,
                routing_method,
            )
        )
        if allowed_configuration is None:
            errors.append(
                "La tupla (optimization_level, layout_method, routing_method) "
                "non appartiene alle 12 configurazioni Qiskit ammesse."
            )

        max_level = request.constraints.get("max_optimization_level")
        if (
            isinstance(max_level, int)
            and optimization_level is not None
            and optimization_level > max_level
        ):
            errors.append(
                f"optimization_level supera il vincolo utente {max_level}."
            )

        explanation = raw_response.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            errors.append("explanation deve essere una stringa non vuota.")
            explanation = ""

        evidence = _string_tuple(raw_response.get("evidence"), "evidence", errors)
        raw_warnings = raw_response.get("warnings", [])
        warnings = _string_tuple(raw_warnings, "warnings", errors)

        if errors:
            return ValidationResult(is_valid=False, errors=tuple(errors))

        assert optimization_level is not None
        assert seed_transpiler is not None
        assert isinstance(metric, str)
        return ValidationResult(
            is_valid=True,
            recommendation=Recommendation(
                selected_device=selected_device,
                figure_of_merit=metric,
                qiskit_plan=QiskitCompilationPlan(
                    optimization_level=optimization_level,
                    seed_transpiler=seed_transpiler,
                    layout_method=layout_method,
                    routing_method=routing_method,
                ),
                explanation=explanation.strip(),
                evidence=evidence,
                warnings=warnings,
            ),
        )

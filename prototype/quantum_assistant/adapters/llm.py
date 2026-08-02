"""Provider-neutral LLM gateway placeholders."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Mapping

from ..models import PromptEnvelope


class UnconfiguredLlmGateway:
    """Fail clearly until a concrete provider adapter is injected."""

    def generate(self, prompt: PromptEnvelope) -> Mapping[str, Any]:
        del prompt
        raise RuntimeError(
            "Nessun LLM gateway configurato. Inietta un adapter che restituisca "
            "un oggetto JSON conforme al response_contract."
        )


class CallableLlmGateway:
    """Small adapter useful for local experiments and tests."""

    def __init__(
        self,
        callback: Callable[[PromptEnvelope], Mapping[str, Any]],
    ) -> None:
        self._callback = callback

    def generate(self, prompt: PromptEnvelope) -> Mapping[str, Any]:
        return self._callback(prompt)

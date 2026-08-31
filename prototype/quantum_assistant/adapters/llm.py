"""Adattatori indipendenti dal servizio usato per chiamare l'LLM."""

from __future__ import annotations

from collections.abc import Callable

from ..models import LlmOutput, PromptEnvelope


class UnconfiguredLlmGateway:
    """Adattatore esplicito usato quando non è configurato alcun LLM."""

    def generate(self, prompt: PromptEnvelope) -> LlmOutput:
        """Interrompe la richiesta perché manca un adattatore concreto."""
        del prompt
        raise RuntimeError(
            "Nessun LLM gateway configurato. Inietta un adapter che restituisca "
            "un oggetto JSON conforme al response_contract."
        )


class CallableLlmGateway:
    """Delega la generazione a una funzione, utile negli esperimenti e nei test."""

    def __init__(
        self,
        callback: Callable[[PromptEnvelope], LlmOutput],
    ) -> None:
        """Salva la funzione che produrrà la risposta dell'LLM."""
        self._callback = callback

    def generate(self, prompt: PromptEnvelope) -> LlmOutput:
        """Passa la richiesta alla funzione configurata e ne restituisce l'esito."""
        return self._callback(prompt)

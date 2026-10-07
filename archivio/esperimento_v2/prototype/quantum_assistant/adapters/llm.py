'Adapters independent of the service used to call the LLM.'

from __future__ import annotations

from collections.abc import Callable

from ..models import LlmOutput, PromptEnvelope


class UnconfiguredLlmGateway:
    'Explicit adapter for use when no LLM is configured.'

    def generate(self, prompt: PromptEnvelope) -> LlmOutput:
        'Stop the request because no concrete adapter is configured.'
        del prompt
        raise RuntimeError(
            'No LLM gateway configured. Inject an adapter returning a JSON object conforming to response_contract.'
        )


class CallableLlmGateway:
    'Delegate generation to a function for experiments and tests.'

    def __init__(
        self,
        callback: Callable[[PromptEnvelope], LlmOutput],
    ) -> None:
        'Store the function that will produce the LLM response.'
        self._callback = callback

    def generate(self, prompt: PromptEnvelope) -> LlmOutput:
        'Pass the request to the configured function and return its result.'
        return self._callback(prompt)

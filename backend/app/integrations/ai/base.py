from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProviderResult:
    response_text: str
    raw_response: dict | None
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None


class AIProvider(Protocol):

    def execute(
        self,
        prompt: str,
        model_id: str,
    ) -> ProviderResult:
        ...

from time import perf_counter

from openai import OpenAI

from app.core.config import settings
from app.integrations.ai.base import ProviderResult


class OpenAIProvider:

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def execute(
        self,
        prompt: str,
        model_id: str,
    ) -> ProviderResult:

        started = perf_counter()

        response = self.client.responses.create(
            model=model_id,
            input=prompt,
        )

        latency_ms = round(
            (perf_counter() - started) * 1000
        )

        usage = getattr(
            response,
            "usage",
            None,
        )

        input_tokens = (
            getattr(
                usage,
                "input_tokens",
                None,
            )
            if usage
            else None
        )

        output_tokens = (
            getattr(
                usage,
                "output_tokens",
                None,
            )
            if usage
            else None
        )

        raw_response = response.model_dump(
            mode="json"
        )

        return ProviderResult(
            response_text=response.output_text or "",
            raw_response=raw_response,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

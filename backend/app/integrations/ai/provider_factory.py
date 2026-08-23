from app.integrations.ai.base import AIProvider
from app.integrations.ai.openai_provider import (
    OpenAIProvider,
)


class ProviderFactory:

    @staticmethod
    def create(
        engine_slug: str,
    ) -> AIProvider:

        providers = {
            "openai": OpenAIProvider,
        }

        provider_class = providers.get(
            engine_slug
        )

        if provider_class is None:
            raise ValueError(
                f"Unsupported AI provider: {engine_slug}"
            )

        return provider_class()

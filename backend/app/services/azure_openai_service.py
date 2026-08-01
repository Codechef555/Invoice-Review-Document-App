from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


def get_azure_openai_client(endpoint: str | None = None, api_key: str | None = None) -> OpenAI:
    endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint or not api_key:
        raise ValueError(
            "Azure OpenAI endpoint and API key must be set as environment variables: "
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY"
        )

    return OpenAI(base_url=endpoint, api_key=api_key)


class AzureOpenAIService:
    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        deployment: str | None = None,
    ):
        self.client = get_azure_openai_client(endpoint, api_key)
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-5.6-terra"

    def create_response(self, prompt: str, **kwargs: Any) -> Any:
        return self.client.responses.create(
            model=self.deployment,
            input=prompt,
            **kwargs,
        )

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field

from app.services.azure_openai_service import get_azure_openai_client


class DocumentClassification(BaseModel):
    document_type: Literal["invoice", "receipt", "unsupported"] = Field(
        description="The classified category of the document."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score of the classification from 0.0 to 1.0.",
    )
    detected_keywords: list[str] = Field(
        default_factory=list,
        description="Key terms detected in document (e.g. 'Tax Invoice', 'VAT ID', 'Receipt').",
    )
    reasoning: str = Field(
        description="Short rationale explaining the classification decision.",
    )


def classify_document_text(
    document_text: str,
    deployment: str | None = None,
) -> DocumentClassification:
    """Classifies document text using Azure OpenAI's native Pydantic structured output."""
    client = get_azure_openai_client()
    model_deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-5.6-terra"

    system_prompt = (
        "You are an automated document classification engine for an accounting app. "
        "Analyze the provided document text, extract key identifying terms, and classify "
        "whether it is an 'invoice', a 'receipt', or 'unsupported'."
    )

    # Explicit Keyword Arguments passed to Azure OpenAI parse API:
    # 1. model: Azure deployment name
    # 2. messages: System and User conversation roles & input text
    # 3. response_format: Pydantic schema class enforcing structured JSON response
    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": document_text},
    ]

    completion = client.beta.chat.completions.parse(
        model=model_deployment,
        messages=messages_payload,
        response_format=DocumentClassification,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Azure OpenAI response did not return a valid parsed structure.")

    return parsed

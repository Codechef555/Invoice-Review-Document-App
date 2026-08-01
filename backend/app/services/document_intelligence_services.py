from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def get_document_intelligence_client(
    endpoint: str | None = None, api_key: str | None = None
) -> DocumentIntelligenceClient:
    endpoint = endpoint or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    api_key = api_key or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
    if not endpoint or not api_key:
        raise ValueError(
            "Azure Document Intelligence endpoint and API key must be set: "
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
        )
    return DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))


class DocumentIntelligenceService:
    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        model_id: str = "prebuilt-invoice",
    ):
        self.client = get_document_intelligence_client(endpoint, api_key)
        self.model_id = model_id

    def analyze_invoice(
        self, invoice_path: Path | str, model_id: str | None = None
    ) -> Any:
        document_path = Path(invoice_path)
        if not document_path.exists():
            raise FileNotFoundError(f"Document file not found: {document_path}")

        target_model = model_id or self.model_id
        with document_path.open("rb") as stream:
            poller = self.client.begin_analyze_document(
                model_id=target_model,
                body=stream,
                content_type="application/octet-stream",
            )
            return poller.result()

    analyze_document = analyze_invoice

    @staticmethod
    def to_dict(analysis: Any) -> dict[str, Any]:
        if hasattr(analysis, "to_dict"):
            return analysis.to_dict()
        if isinstance(analysis, dict):
            return analysis
        return {"result": str(analysis)}

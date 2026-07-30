from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from azure.ai.documentintelligence import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential


@dataclass
class InvoiceAnalysis:
    document_path: Path
    model_id: str
    fields: dict[str, Any]
    content: str


def get_document_intelligence_client(endpoint: str | None = None, api_key: str | None = None) -> DocumentAnalysisClient:
    endpoint = endpoint or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    api_key = api_key or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
    if not endpoint or not api_key:
        raise ValueError(
            "Azure Document Intelligence endpoint and API key must be set as environment variables: "
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
        )
    return DocumentAnalysisClient(endpoint, AzureKeyCredential(api_key))


def normalize_field(field: Any) -> Any:
    if field is None:
        return None

    if hasattr(field, "value") and field.value is not None:
        return field.value

    if hasattr(field, "value_array") and field.value_array is not None:
        return [normalize_field(item) for item in field.value_array]

    if hasattr(field, "value_map") and field.value_map is not None:
        return {key: normalize_field(value) for key, value in field.value_map.items()}

    if hasattr(field, "content") and field.content is not None:
        return field.content

    return None


def analyze_invoice_file(
    invoice_path: Path | str,
    client: DocumentAnalysisClient,
    model_id: str = "prebuilt-invoice",
) -> InvoiceAnalysis:
    invoice_path = Path(invoice_path)
    if not invoice_path.exists():
        raise FileNotFoundError(f"Invoice file not found: {invoice_path}")

    with invoice_path.open("rb") as stream:
        poller = client.begin_analyze_document(model_id, stream)
        analysis_result = poller.result()

    if not analysis_result.documents:
        raise RuntimeError("Document Intelligence returned no analyzed documents.")

    invoice_document = analysis_result.documents[0]
    fields = {name: normalize_field(field) for name, field in invoice_document.fields.items()}
    content = getattr(analysis_result, "content", "") or ""

    return InvoiceAnalysis(document_path=invoice_path, model_id=model_id, fields=fields, content=content)


def print_analysis(analysis: InvoiceAnalysis) -> None:
    print("\n=== Invoice Analysis ===")
    print(f"Document: {analysis.document_path}")
    print(f"Model: {analysis.model_id}\n")
    print("Extracted fields:")
    print(json.dumps(analysis.fields, indent=2, default=str))
    print("\nFull extracted text:\n")
    print(analysis.content)


def get_default_invoice_path() -> Path:
    workspace_root = Path(__file__).resolve().parents[2].parent
    return workspace_root / "samples" / "generated" / "01-en-happy-classic.pdf"


def main() -> None:
    client = get_document_intelligence_client()
    invoice_path = get_default_invoice_path()
    analysis = analyze_invoice_file(invoice_path, client)
    print_analysis(analysis)


if __name__ == "__main__":
    main()

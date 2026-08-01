"""Playground script: demonstrate and test the document processing pipeline chain.

Run from playground/:
    cd playground
    uv run --project ../backend --locked --no-sync python test_pipeline_chain.py [path/to/sample.pdf]
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"

# Ensure backend package is importable from playground
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.pipeline.chain import Pipeline, PipelineContext  # noqa: E402
from app.pipeline.classification import DocumentClassification  # noqa: E402
from app.pipeline.steps import (  # noqa: E402
    MappingStep,
    ValidationStep,
)
from app.schemas.invoice.model import InvoiceExtraction  # noqa: E402

DEFAULT_SAMPLE = PROJECT_ROOT / "samples" / "generated" / "01-en-happy-classic.pdf"


def test_offline_mapping_and_validation() -> None:
    """Offline test of MappingStep and ValidationStep using sample data."""
    print("--- Running Offline Pipeline Verification ---")

    # Mock raw Document Intelligence response payload
    mock_raw_analysis = {
        "documents": [
            {
                "fields": {
                    "vendorName": {"value": "Acme Supplies B.V.", "confidence": 0.98},
                    "vendorVatId": {"value": "NL854502130B01", "confidence": 0.95},
                    "customerName": {"value": "Northstar Facilities B.V.", "confidence": 0.99},
                    "customerVatId": {"value": "NL854502130B01", "confidence": 0.95},
                    "invoiceDate": {"value": "2026-03-15", "confidence": 0.99},
                    "invoiceNumber": {"value": "INV-2026-001", "confidence": 0.99},
                    "subtotal": {"value": 100.00, "confidence": 0.97},
                    "totalTax": {"value": 21.00, "confidence": 0.97},
                    "invoiceTotal": {"value": 121.00, "confidence": 0.98},
                    "currency": {"value": "EUR", "confidence": 0.99},
                    "Items": {
                        "value": [
                            {
                                "value": {
                                    "Description": {"value": "Office Cleaning Kit"},
                                    "Amount": {"value": 100.00},
                                    "Quantity": {"value": 1},
                                    "UnitPrice": {"value": 100.00},
                                }
                            }
                        ]
                    },
                }
            }
        ]
    }

    context = PipelineContext(
        file_path=DEFAULT_SAMPLE,
        classification=DocumentClassification(
            document_type="invoice",
            confidence=0.98,
            detected_keywords=["Tax Invoice", "VAT ID"],
            reasoning="Document contains invoice header and tax details.",
        ),
        raw_analysis=mock_raw_analysis,
    )

    pipeline = Pipeline().add_step(MappingStep()).add_step(ValidationStep())
    result_context = pipeline.execute(context)

    print(f"Extraction Data Type: {type(result_context.extracted_data).__name__}")
    if isinstance(result_context.extracted_data, InvoiceExtraction):
        print(f"Supplier Name: {result_context.extracted_data.vendor_name.value if result_context.extracted_data.vendor_name else None}")
        print(f"Line Items Count: {len(result_context.extracted_data.line_items)}")

    if result_context.validation_results:
        print(f"Validation Is Valid: {result_context.validation_results.is_valid}")
        print(f"Validation Issues Count: {len(result_context.validation_results.issues)}")

    print("Offline verification completed successfully!\n")


def main() -> None:
    sample_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE

    print(f"Running pipeline test on: {sample_path}")
    test_offline_mapping_and_validation()


if __name__ == "__main__":
    main()

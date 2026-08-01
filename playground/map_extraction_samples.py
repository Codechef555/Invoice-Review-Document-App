"""Playground experiment: analyze a sample invoice using Azure Document Intelligence
and map the extraction result into the structured InvoiceExtraction model.

Run from the playground folder:
    cd playground
    uv run --project ../backend --locked --no-sync python map_extraction_samples.py [path/to/invoice]

If no invoice path is provided, it defaults to:
    samples/generated/01-en-happy-classic.pdf
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"

# Ensure backend package is importable from playground
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.schemas.invoice.mapping import map_invoice_fields  # noqa: E402
from app.services.document_intelligence_services import DocumentIntelligenceService  # noqa: E402


DEFAULT_SAMPLE = PROJECT_ROOT / "samples" / "generated" / "01-en-happy-classic.pdf"


def main() -> None:
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE

    if not target_path.exists():
        raise FileNotFoundError(f"Invoice file not found: {target_path}")

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Analyzing file: {target_path}\n")

    # Step 1: Analyze document via Document Intelligence Service
    service = DocumentIntelligenceService()
    analysis_result = service.analyze_invoice(target_path)
    raw_dict = service.to_dict(analysis_result)

    # Step 2: Map raw analysis result to InvoiceExtraction schema
    invoice_extraction = map_invoice_fields(raw_dict)

    # Step 3: Print mapped result as formatted JSON
    print("=== Mapped Invoice Extraction ===")
    print(json.dumps(invoice_extraction.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    main()

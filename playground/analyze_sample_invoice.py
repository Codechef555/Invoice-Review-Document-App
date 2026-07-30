"""Playground experiment: analyze the sample invoice and print the raw Azure Document Intelligence response.

Run from the playground folder:
    cd playground
    uv run --project ../backend --locked --no-sync python analyze_sample_invoice.py

This script is intentionally a playground scratchpad. It imports the app-layer service from backend/app/
and prints the full JSON result for inspection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"
# Ensure the backend package is importable from playground.
sys.path.insert(0, str(BACKEND_PATH))

from app.services.document_intelligence_services import DocumentIntelligenceService

SAMPLE_INVOICE = PROJECT_ROOT / "samples" / "generated" / "01-en-happy-classic.pdf"


def main() -> None:
    if not SAMPLE_INVOICE.exists():
        raise FileNotFoundError(f"Sample invoice not found: {SAMPLE_INVOICE}")

    print(f"Backend path: {BACKEND_PATH}")
    print(f"Sample invoice: {SAMPLE_INVOICE}\n")

    service = DocumentIntelligenceService()
    result = service.analyze_invoice(SAMPLE_INVOICE)
    print(json.dumps(service.to_dict(result), indent=2, default=str))


if __name__ == "__main__":
    main()

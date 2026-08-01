"""Playground experiment: test document classification using Azure OpenAI structured output.

Run from the playground folder:
    cd playground
    uv run --project ../backend --locked --no-sync python classify_sample.py [path/to/sample]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"

# Ensure backend package is importable
sys.path.insert(0, str(BACKEND_PATH))

from app.pipeline.classifier import classify_document_text  # noqa: E402
from app.services.document_intelligence_services import DocumentIntelligenceService  # noqa: E402

DEFAULT_SAMPLE = PROJECT_ROOT / "samples" / "generated" / "01-en-happy-classic.pdf"


def main() -> None:
    sample_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE

    if not sample_path.exists():
        raise FileNotFoundError(f"Sample file not found: {sample_path}")

    print(f"Extracting text from: {sample_path}")
    doc_service = DocumentIntelligenceService()
    analysis = doc_service.analyze_invoice(sample_path)
    raw_dict = doc_service.to_dict(analysis)

    # Combine content or raw fields into text string for classification
    content_lines = []
    if "content" in raw_dict:
        content_lines.append(raw_dict["content"])

    document_text = "\n".join(content_lines) if content_lines else str(raw_dict)

    print("Classifying document using Azure OpenAI Structured Output...\n")
    classification = classify_document_text(document_text)

    print("=== Classification Result ===")
    print(json.dumps(classification.model_dump(), indent=2))


if __name__ == "__main__":
    main()

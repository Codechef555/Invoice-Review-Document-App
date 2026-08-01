from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"

# Ensure backend package is importable from playground
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.services.azure_openai_service import AzureOpenAIService  # noqa: E402

DEFAULT_PROMPT = "What is the capital of Spain?"


def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    service = AzureOpenAIService()
    response = service.create.response(prompt)
    print(response.output[0].content[0].text)


if __name__ == "__main__":
    main()

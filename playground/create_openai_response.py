from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
DEFAULT_PROMPT = "What is the capital of Spain?"

sys.path.insert(0, str[BACKEND_ROOT])

from app.services.azure_openai_service import AzureOpenAIService

def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    service = AzureOpenAIService()
    response = service.create.response(prompt)
    #print(json.dumps(response.model_dump(), index=2, default=str))
    print(response.output[0].content[0].text)

if __name__ == "__main__":
    main()

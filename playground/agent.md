# Playground Path Setup Guide

This guide explains how scripts in the `playground/` directory import backend application modules (`app.*`) without requiring `backend/` to be installed as an editable package.

## Overview

The repository layout places backend code in `backend/app/` and standalone experiment scripts in `playground/`:

```
e2e-invoice-review/
├── backend/
│   └── app/
│       ├── services/
│       └── pipeline/
└── playground/
    ├── analyze_sample_invoice.py
    ├── classify_sample_document.py
    ├── create_openai_response.py
    └── map_extraction_samples.py
```

Because `playground/` is a sibling directory to `backend/`, Python does not automatically include `backend/` in its module search path (`sys.path`).

---

## Standard Path Setup Pattern

Add the following standard snippet at the top of every script in `playground/` before importing any `app` modules:

```python
from pathlib import Path
import sys

# Resolve project root (parent directory of playground/) and backend folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"

# Dynamically prepend backend path to sys.path
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

# Now app module imports work seamlessly
from app.services.document_intelligence_services import DocumentIntelligenceService
from app.pipeline.classifier import classify_document_text
```

---

## Key Mechanism Explained

1. **`Path(__file__).resolve()`**: Gets the absolute normalized path of the executing script.
2. **`.parents[1]`**: Navigates two levels up in the filesystem hierarchy (`playground/script.py` &rarr; `playground/` &rarr; Repository Root).
3. **`PROJECT_ROOT / "backend"`**: Constructs an absolute `Path` pointing to the `backend/` directory.
4. **`sys.path.insert(0, str(BACKEND_PATH))`**: Inserts the backend folder at index `0` of Python's `sys.path`. This prioritizes `backend/app/` modules for all subsequent `from app...` imports.

---

## Running Playground Scripts

Execute playground scripts using `uv` from either the repo root or the `playground/` folder:

```bash
# From playground/
cd playground
uv run --project ../backend --locked --no-sync python analyze_sample_invoice.py

# From repository root
uv run --project backend --locked --no-sync python playground/analyze_sample_invoice.py
```

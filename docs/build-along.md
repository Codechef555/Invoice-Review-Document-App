# Build-along guide

The complete guided build lives at <https://learn.datalumina.com/docs/invoice-review>. This local guide records the first checkpoint represented by the `main` branch.

## Starter outcome

The repository installs reproducibly, starts a minimal FastAPI service and React interface, and includes the business brief plus fictional source documents.

## Why this boundary exists

The starter removes the completed workflow while preserving every prerequisite needed to build it. You begin with the user, the source documents, and explicit service boundaries instead of reverse-engineering a finished application.

## Commands

```bash
cd backend
uv sync --locked

cd ../frontend
pnpm install --frozen-lockfile

cd ..
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
./scripts/dev.sh --check
./scripts/dev.sh
```

## Important locations

- `docs/client-brief.md`: the recurring finance problem and definition of done
- `docs/architecture.md`: the intended boundaries and data flow
- `docs/api-and-pipeline.md`: complete REST API endpoint specification and 5-step pipeline architecture documentation
- `samples/`: the fictional evaluation corpus and manifest
- `playground/agent.md`: standard path setup guide for playground script experiments
- `backend/app/pipeline/chain.py`: pipeline chaining core (`PipelineContext`, `PipelineStep`, `Pipeline`)
- `backend/app/pipeline/gl_categorization.py`: General Ledger (GL) account catalog (10 accounts) & Azure OpenAI structured categorization
- `backend/app/pipeline/steps.py`: pipeline steps for classification, extraction model routing, schema mapping, offline EU VAT validation, and GL categorization
- `backend/app/config.py`: backend settings and AppConfig defaults
- `backend/app/database.py`: SQLAlchemy SQLite database setup
- `backend/app/documents/models.py`: DocumentRecord database entity model
- `backend/app/documents/repository.py`: DocumentRepository SQLite CRUD layer
- `backend/app/documents/service.py`: DocumentService orchestrator
- `backend/app/invoices/validation.py`: pure business validation rules
- `backend/app/documents/routes.py`: REST API endpoints for document upload, listing, review, decisions, and GL overrides
- `backend/app/accounting/routes.py`: REST API endpoint for GL catalog (`/api/accounting/catalog`)
- `backend/app/main.py`: FastAPI app factory (`create_app()`), CORS, router mounts, and SPA static file fallback
- `frontend/src/App.tsx`: the initial interface boundary
- `Dockerfile`: multi-stage Docker build for React SPA static serving + FastAPI backend
- `.dockerignore`: context exclusions for Docker build
- `scripts/deploy-azure.ps1`: PowerShell deployment script for Azure CLI single-container deployment

## What you should observe

- `GET http://localhost:8000/health` returns `{"status":"ok"}`.
- `GET http://localhost:8000/api/accounting/catalog` returns 10 GL catalog accounts.
- `http://localhost:5173` shows the Invoice Review starter screen.
- Running `uv run --project backend --locked --no-sync python playground/test_pipeline_chain.py` successfully executes the document pipeline chain.
- Running `uv run --project backend --locked --no-sync python playground/evaluate_samples.py` evaluates all 13 sample corpus scenarios with 100% pass rate.
- Multi-stage single-container Docker build packages Vite static files and FastAPI backend into a single image.

## Checkpoint

- [x] Locked backend and frontend installs succeed.
- [x] Backend lint passes (`ruff check backend playground`).
- [x] Document processing pipeline chain verified.
- [x] Sample evaluation corpus harness passes 13/13 scenarios with 100% pass rate.
- [x] FastAPI REST API endpoints & SQLite repository initialized.
- [x] Frontend type-check, lint, and production build pass.
- [x] The health endpoint and starter screen load locally.
- [x] Single-container Azure deployment configuration created (`Dockerfile`, `.dockerignore`, `scripts/deploy-azure.ps1`).

Continue with the [online tutorial](https://learn.datalumina.com/docs/invoice-review).

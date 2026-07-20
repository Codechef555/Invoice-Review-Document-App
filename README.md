# Invoice Review

This is the ready-to-build starter for an end-to-end invoice and receipt review application. You will build a workflow for Northstar Facilities B.V. that combines Azure document extraction, deterministic finance rules, SQLite persistence, and a human review interface.

> You are on `main`, the learner starter. Active work is visible on `development`; the reviewed finished application is on `solution`.

Tutorial: <https://learn.datalumina.com/docs/invoice-review>

## What is included

- The client brief and target architecture
- A fictional 13-document multilingual corpus and its generator
- Safe environment templates
- Exact dependency pins and lockfiles
- Minimal FastAPI and React applications
- An install-free development supervisor and readiness check

## Prerequisites

- Python 3.12 or newer
- uv
- Node.js 22 or newer
- pnpm 11

## Install

```bash
cd backend
uv sync --locked

cd ../frontend
pnpm install --frozen-lockfile
```

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`. The placeholders are sufficient for the starter screen; add real Azure values only when the tutorial reaches the provider stages.

## Run

```bash
cd ..
./scripts/dev.sh --check
./scripts/dev.sh
```

Open <http://localhost:5173>. The starter API health endpoint is <http://localhost:8000/health>.

## Verify the starter

```bash
cd backend
uv run --locked --no-sync ruff check app scripts

cd ../frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build

cd ..
./scripts/dev.sh --check
```

## Choose a branch

- `main`: clone this branch to follow the tutorial from the prepared starting point.
- `development`: inspect the public working branch and later experiments.
- `solution`: inspect the reviewed end product.

To switch to the finished application:

```bash
git switch solution
```

Start with [the client brief](docs/client-brief.md), then follow the [complete tutorial](https://learn.datalumina.com/docs/invoice-review).

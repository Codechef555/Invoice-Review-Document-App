#!/usr/bin/env bash
set -euo pipefail

# Ensure environment files exist
if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
  echo "--> Copying backend/.env.example to backend/.env"
  cp backend/.env.example backend/.env
fi

if [ ! -f "frontend/.env" ] && [ -f "frontend/.env.example" ]; then
  echo "--> Copying frontend/.env.example to frontend/.env"
  cp frontend/.env.example frontend/.env
fi

# Resolve pnpm binary or fallback to npx pnpm
PNPM_CMD="pnpm"
if ! command -v pnpm &> /dev/null; then
  PNPM_CMD="npx -y pnpm"
fi

# Run pre-flight checks if --check flag is passed
if [ "${1:-}" = "--check" ]; then
  echo "==> Checking backend (ruff lint)..."
  (cd backend && uv run --locked --no-sync ruff check .)
  echo "==> Checking frontend (typecheck & production build)..."
  (cd frontend && $PNPM_CMD run build)
  echo "==> All checks passed!"
  exit 0
fi

# Clean up background processes on exit/interrupt
cleanup() {
  echo ""
  echo "==> Stopping services..."
  trap - INT TERM EXIT
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
  echo "==> Servers stopped."
}

trap cleanup INT TERM EXIT

echo "==> Starting Backend (FastAPI)..."
(cd backend && uv run --locked --no-sync uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

echo "==> Starting Frontend (Vite)..."
(cd frontend && $PNPM_CMD dev) &
FRONTEND_PID=$!

echo "==> Backend and Frontend are running."
echo "==> Press Ctrl+C to stop both."

wait

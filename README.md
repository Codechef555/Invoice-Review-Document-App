# Invoice Review

<p align="center">
  <img width="900" alt="Invoice Review Application" src="https://github.com/user-attachments/assets/1c47af14-86a7-415f-97e7-dc1b11a12089">
</p>

An end-to-end AI-powered invoice and receipt processing application built with **Azure AI Document Intelligence**, **Azure OpenAI**, **FastAPI**, **Pydantic**, **SQLite**, and **React**.

Throughout this project you'll build an intelligent document review workflow for **Northstar Facilities B.V.** that automatically classifies financial documents, extracts structured data, validates business rules, stores review results, and exposes everything through a clean web interface.

> **This repository is a tutorial starter.** The application code is intentionally omitted so you can build the complete system step-by-step.

---

# What You'll Build

By the end of the tutorial you'll have an application capable of:

- 📄 Classifying invoices vs receipts
- 🤖 Extracting structured data using Azure Document Intelligence
- 🧠 Using Azure OpenAI structured outputs where appropriate
- 🏗️ Mapping extracted data into Pydantic models
- ✅ Validating finance rules and VAT numbers
- 💾 Persisting review results in SQLite
- 🔍 Providing a human review interface
- ⚡ Exposing the workflow through a FastAPI backend
- 🎨 Building a React frontend for document review

---

# Architecture

```
                Uploaded Document
                        │
                        ▼
           Document Classification
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
Invoice Model                 Receipt Model
         │                             │
         └──────────────┬──────────────┘
                        ▼
          Pydantic Data Models
                        │
                        ▼
          Business Rule Validation
                        │
                        ▼
              SQLite Persistence
                        │
                        ▼
            Human Review Interface
```

---

# What's Included

This starter repository contains everything required to follow the tutorial:

- Client brief
- Target architecture
- Fictional multilingual document corpus (13 documents)
- Environment templates
- Dependency lockfiles
- Backend project configuration
- Frontend project configuration

The implementation itself is intentionally absent so you can build each stage yourself.

---

# Tech Stack

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- Azure AI Document Intelligence
- Azure OpenAI
- SQLite
- uv

## Frontend

- React
- Vite
- TypeScript
- pnpm

---

# Prerequisites

Install the following before starting:

- Python 3.12+
- uv
- Node.js 22+
- pnpm 11+

---

# Installation

Clone the repository and install dependencies.

## Backend

```bash
cd backend
uv sync --locked
```

## Frontend

```bash
cd frontend
pnpm install --frozen-lockfile
```

---

# Environment Variables

Copy the example environment files.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

During the tutorial you'll configure:

### Backend

Azure credentials for:

- Azure AI Document Intelligence
- Azure OpenAI

### Frontend

```text
VITE_API_BASE_URL
```

No Azure credentials are required until the provider sections of the tutorial.

---

# Verify Installation

Backend:

```bash
cd backend
uv sync --locked
```

Frontend:

```bash
cd frontend
pnpm install --frozen-lockfile
```

If both complete successfully, you're ready to begin.

---

# Repository Branches

The repository contains multiple branches depending on how you'd like to follow along.

| Branch | Purpose |
|---------|----------|
| **main** | Clean tutorial starter |
| **development** | Public work-in-progress implementation |
| **solution** | Completed application |

Switch to the finished implementation anytime:

```bash
git switch solution
```

---

# Tutorial Roadmap

You'll progressively build:

- Azure Document Intelligence service
- Pydantic data models
- Mapping layer
- Azure OpenAI integration
- Classification pipeline
- Chained processing workflow
- Business rule engine
- FastAPI API
- React frontend
- Human review workflow

---

# Project Structure

```
backend/
    app/
    samples/
    playground/
    tests/

frontend/
    src/

docs/
    client-brief.md
```

---

# Getting Started

1. Read the client brief.

```
docs/client-brief.md
```

2. Follow the complete tutorial.

https://learn.datalumina.com/docs/invoice-review

---

# Learning Outcomes

By completing this project you'll gain practical experience with:

- Azure AI Document Intelligence
- Azure OpenAI
- Structured Outputs
- Pydantic
- FastAPI
- AI pipeline orchestration
- Document processing workflows
- Financial document validation
- React + TypeScript
- Full-stack AI applications

---

Happy building! 🚀

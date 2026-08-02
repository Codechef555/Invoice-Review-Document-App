# API Endpoints & Document Processing Pipeline Specification

This document details the REST API endpoints and the synchronous end-to-end document processing pipeline architecture for the Invoice Review application.

---

## 1. REST API Endpoints Specification

All backend endpoints are built using FastAPI and mounted under `/api/` (except the `/health` endpoint).

### 1.1 System Endpoints

| Method | Endpoint | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health check endpoint | None | `{"status": "ok"}` |

### 1.2 Accounting Endpoints

| Method | Endpoint | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/accounting/catalog` | Retrieves the 10-account General Ledger (GL) catalog | None | `Array<GLAccount>` |

**GL Catalog Accounts**:
- `6000`: Software & SaaS Subscriptions
- `6010`: Office Supplies & Consumables
- `6020`: Professional Services & Consulting
- `6030`: Facility Operations & Utilities
- `6040`: Travel & Transportation
- `6050`: Marketing & Advertising
- `6060`: Cloud Infrastructure & Hosting
- `6070`: Hardware & Equipment
- `6080`: Legal & Compliance
- `6090`: Accounting & Audit Services

---

### 1.3 Document Management Endpoints

| Method | Endpoint | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/documents` | Lists all processed document records | None | `Array<DocumentResponse>` |
| `POST` | `/api/documents` | Uploads and processes a document (PDF, PNG, JPEG <= 4MB) | `multipart/form-data` (`file`) | `DocumentResponse` |
| `GET` | `/api/documents/{document_id}` | Retrieves document record details | None | `DocumentResponse` |
| `GET` | `/api/documents/{document_id}/file` | Streams original binary document file | None | `FileResponse` |
| `DELETE`| `/api/documents/{document_id}` | Deletes document record and stored file | None | `204 No Content` |
| `PUT` | `/api/documents/{document_id}` | Corrects extracted review fields and revalidates | `DocumentCorrectionRequest` (JSON) | `DocumentResponse` |
| `PUT` | `/api/documents/{document_id}/accounting` | Overrides/selects GL account code | `AccountingSelectionRequest` (JSON) | `DocumentResponse` |
| `POST` | `/api/documents/{document_id}/decision` | Submits human decision (`approved` or `rejected`) | `DecisionRequest` (JSON) | `DocumentResponse` |

---

## 2. Document Processing Pipeline Architecture

When a user uploads a document via `POST /api/documents`, the request enters `DocumentService.process()`, which executes a sequential, 5-step pipeline via `Pipeline.execute(context)`.

```
[ Upload File ]
       │
       ▼
 1. ClassificationStep (Azure OpenAI text classifier: invoice vs receipt)
       │
       ▼
 2. ExtractionStep (Azure AI Document Intelligence: prebuilt-invoice / prebuilt-receipt)
       │
       ▼
 3. MappingStep (Normalizes raw extraction payload to Pydantic models)
       │
       ▼
 4. ValidationStep (EU VAT checksum via python-stdnum & Subtotal + Tax math check)
       │
       ▼
 5. GLCategorizationStep (Azure OpenAI GL account suggestion with rationale)
       │
       ▼
 Business Validation & Duplicate Detection (validate_review_data)
       │
       ▼
 Persistence (SQLite Database save_result -> status: ready or action_required)
```

---

### Step-by-Step Breakdown

#### Step 1: `ClassificationStep`
- **Goal**: Classify document text.
- **Provider**: Azure OpenAI Responses API (`classify_document_text`).
- **Output**: Sets `context.classification` (`document_type`: `"invoice"`, `"receipt"`, or `"unsupported"`, confidence score, detected keywords).

#### Step 2: `ExtractionStep`
- **Goal**: Extract key-value fields and line items.
- **Provider**: Azure AI Document Intelligence SDK.
- **Routing**: Automatically selects `prebuilt-receipt` if classification is `"receipt"`, else `prebuilt-invoice`.
- **Output**: Stores raw JSON analysis in `context.raw_analysis`.

#### Step 3: `MappingStep`
- **Goal**: Field normalization.
- **Logic**: Maps raw extracted fields into unified Pydantic schema objects (`InvoiceExtraction` or `ReceiptExtraction`).
- **Output**: Sets `context.extracted_data`.

#### Step 4: `ValidationStep`
- **Goal**: Deterministic offline validation.
- **Checks**:
  1. **EU VAT ID Validation**: Validates supplier and customer VAT numbers using `python-stdnum.eu.vat` format and checksum verification (offline, no live VIES lookup).
  2. **Mathematical Reconciliation**: Verifies if `subtotal + total_tax == invoice_total` (within €0.01 tolerance).
- **Output**: Sets `context.validation_results`.

#### Step 5: `GLCategorizationStep`
- **Goal**: Suggest accounting GL category.
- **Provider**: Azure OpenAI Responses API (`suggest_gl_account`).
- **Logic**: Matches extracted vendor, description, and line items against the 10 catalog accounts. Returns account code, account name, confidence score, and reasoning.
- **Output**: Sets `context.gl_categorization`.

---

## 3. Business Rule Validation & Status Lifecycle

After the 5 pipeline steps complete, `DocumentService` runs `validate_review_data()`:

1. **Customer Verification**: Ensures customer name matches `"Northstar Facilities B.V."` and VAT ID matches `"NL00449544B01"`.
2. **Mandatory Field Checks**: Ensures vendor name, invoice date, invoice number, line items, and totals are present.
3. **Duplicate Detection**: Queries SQLite repository for existing records with matching `(vendor_name, invoice_number)`.
4. **Status Determination**:
   - `action_required`: Assigned if any validation errors, missing fields, or duplicate warnings exist.
   - `ready`: Assigned if all validation checks pass cleanly.
   - `approved` / `rejected`: Assigned when a user submits a decision via `POST /api/documents/{document_id}/decision`. Decided documents are locked against further editing.

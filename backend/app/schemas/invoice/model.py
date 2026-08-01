from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ..common import ExtractedValue


class InvoiceExtraction(BaseModel):
    currency: ExtractedValue | None = None
    customer_name: ExtractedValue | None = None
    customer_vat_id: ExtractedValue | None = None
    document_type: ExtractedValue | None = None
    due_date: ExtractedValue | None = None
    invoice_date: ExtractedValue | None = None
    invoice_number: ExtractedValue | None = None
    invoice_total: ExtractedValue | None = None
    purchase_order: ExtractedValue | None = None
    subtotal: ExtractedValue | None = None
    total_tax: ExtractedValue | None = None
    vendor_name: ExtractedValue | None = None
    vendor_vat_id: ExtractedValue | None = None
    raw_fields: dict[str, Any] = {}

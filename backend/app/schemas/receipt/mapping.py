from __future__ import annotations

from typing import Any

from .model import ReceiptExtraction
from ..common import ExtractedValue


FieldKey = str


def _normalize_analysis(analysis: Any) -> dict[str, Any]:
    if analysis is None:
        return {}

    if isinstance(analysis, dict):
        raw = analysis
    elif hasattr(analysis, "to_dict"):
        raw = analysis.to_dict()
    else:
        return {}

    if "documents" in raw and raw["documents"]:
        document = raw["documents"][0]
        return document.get("fields", {}) or {}

    return raw.get("fields", {}) or {}


def _field_by_key(fields: dict[str, Any], keys: list[FieldKey]) -> Any:
    for key in keys:
        if key in fields:
            return fields[key]
    return None


def _extract_value(fields: dict[str, Any], keys: list[FieldKey]) -> ExtractedValue:
    return ExtractedValue.from_di_field(_field_by_key(fields, keys))


def map_receipt_fields(analysis: Any) -> ReceiptExtraction:
    fields = _normalize_analysis(analysis)

    return ReceiptExtraction(
        currency=_extract_value(fields, ["currency", "receiptCurrency", "currencyCode"]),
        customer_name=_extract_value(fields, ["customerName", "customer_name"]),
        customer_vat_id=_extract_value(fields, ["customerTaxId", "customer_vat_id", "customerVatId"]),
        document_type=_extract_value(fields, ["documentType", "document_type", "documentType"]),
        due_date=_extract_value(fields, ["dueDate", "due_date"]),
        invoice_date=_extract_value(fields, ["invoiceDate", "invoice_date", "transactionDate", "transaction_date"]),
        invoice_number=_extract_value(fields, ["invoiceNumber", "invoice_number", "receiptNumber", "transactionNumber"]),
        invoice_total=_extract_value(fields, ["invoiceTotal", "invoice_total", "total", "receiptTotal"]),
        purchase_order=_extract_value(fields, ["purchaseOrder", "purchase_order"]),
        subtotal=_extract_value(fields, ["subtotal", "subTotal", "sub_total"]),
        total_tax=_extract_value(fields, ["totalTax", "total_tax", "tax", "taxTotal"]),
        vendor_name=_extract_value(fields, ["vendorName", "vendor_name", "supplierName", "merchantName"]),
        vendor_vat_id=_extract_value(fields, ["vendorVatId", "vendor_vat_id", "supplierTaxId", "supplierTaxNumber"]),
        raw_fields=fields,
    )

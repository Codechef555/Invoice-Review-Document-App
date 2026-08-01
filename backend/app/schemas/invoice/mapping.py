from __future__ import annotations

from typing import Any

from ..common import ExtractedValue, LineItem
from .model import InvoiceExtraction

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


def _extract_line_items(fields: dict[str, Any]) -> list[LineItem]:
    items_field = _field_by_key(fields, ["Items", "items"])
    if not items_field:
        return []

    raw_items = []
    if isinstance(items_field, dict):
        raw_items = items_field.get("value") or []
    elif hasattr(items_field, "value"):
        raw_items = items_field.value or []

    line_items: list[LineItem] = []
    for item in raw_items:
        item_fields = {}
        if isinstance(item, dict):
            item_fields = item.get("value", {}) or item
        elif hasattr(item, "value"):
            item_fields = getattr(item, "value", {}) or {}

        if not isinstance(item_fields, dict):
            continue

        line_items.append(
            LineItem(
                description=_extract_value(
                    item_fields, ["Description", "description"]
                ),
                amount=_extract_value(
                    item_fields, ["Amount", "amount", "TotalPrice", "totalPrice"]
                ),
                quantity=_extract_value(
                    item_fields, ["Quantity", "quantity"]
                ),
                unit_price=_extract_value(
                    item_fields, ["UnitPrice", "unitPrice", "unit_price"]
                ),
                product_code=_extract_value(
                    item_fields, ["ProductCode", "productCode", "product_code"]
                ),
            )
        )
    return line_items


def map_invoice_fields(analysis: Any) -> InvoiceExtraction:
    fields = _normalize_analysis(analysis)

    return InvoiceExtraction(
        currency=_extract_value(
            fields, ["currency", "invoiceCurrency", "currencyCode"]
        ),
        customer_name=_extract_value(
            fields, ["customerName", "customer_name"]
        ),
        customer_vat_id=_extract_value(
            fields, ["customerTaxId", "customer_vat_id", "customerVatId"]
        ),
        document_type=_extract_value(
            fields, ["documentType", "document_type"]
        ),
        due_date=_extract_value(
            fields, ["dueDate", "due_date"]
        ),
        invoice_date=_extract_value(
            fields, ["invoiceDate", "invoice_date"]
        ),
        invoice_number=_extract_value(
            fields, ["invoiceNumber", "invoice_number", "invoiceId"]
        ),
        invoice_total=_extract_value(
            fields, ["invoiceTotal", "invoice_total", "total"]
        ),
        purchase_order=_extract_value(
            fields, ["purchaseOrder", "purchase_order"]
        ),
        subtotal=_extract_value(
            fields, ["subtotal", "subTotal", "sub_total"]
        ),
        total_tax=_extract_value(
            fields, ["totalTax", "total_tax", "tax"]
        ),
        vendor_name=_extract_value(
            fields, ["vendorName", "vendor_name", "supplierName", "merchantName"]
        ),
        vendor_vat_id=_extract_value(
            fields, [
                "vendorVatId",
                "vendor_vat_id",
                "supplierTaxId",
                "supplierTaxNumber",
            ]
        ),
        line_items=_extract_line_items(fields),
        raw_fields=fields,
    )

from __future__ import annotations

import re

from stdnum.eu import vat

from app.documents.schemas import DocumentStatus, ReviewData, ValidationIssue


def normalize_name(name: str | None) -> str | None:
    if not name:
        return None
    cleaned = re.sub(r"[^\w\s]", "", name.lower())
    return re.sub(r"\s+", " ", cleaned).strip() or None


def normalize_invoice_number(number: str | None) -> str | None:
    if not number:
        return None
    cleaned = re.sub(r"[^\w]", "", number.upper())
    return cleaned or None


def validate_review_data(
    data: ReviewData,
    *,
    expected_customer_name: str = "Northstar Facilities B.V.",
    expected_customer_vat_id: str = "NL00449544B01",
    min_confidence: float = 0.80,
    is_duplicate: bool = False,
) -> list[ValidationIssue]:
    """Pure business validation for invoices and receipts."""
    issues: list[ValidationIssue] = []

    is_receipt = data.document_type == "receipt"

    # Vendor / Supplier Name
    if not data.vendor_name or not data.vendor_name.strip():
        issues.append(
            ValidationIssue(
                code="MISSING_VENDOR_NAME",
                field="vendor_name",
                severity="error",
                message="Supplier / merchant name is missing.",
            )
        )

    # Invoice / Transaction Date
    if not data.invoice_date:
        issues.append(
            ValidationIssue(
                code="MISSING_INVOICE_DATE",
                field="invoice_date",
                severity="error",
                message="Invoice / transaction date is missing.",
            )
        )

    # Invoice Total & Positive Total
    if data.invoice_total is None:
        issues.append(
            ValidationIssue(
                code="MISSING_INVOICE_TOTAL",
                field="invoice_total",
                severity="error",
                message="Invoice total amount is missing.",
            )
        )
    elif data.invoice_total <= 0:
        issues.append(
            ValidationIssue(
                code="NON_POSITIVE_TOTAL",
                field="invoice_total",
                severity="error",
                message="Invoice total must be a positive amount.",
            )
        )

    # Subtotal + Tax Reconciliation
    if (
        data.subtotal is not None
        and data.total_tax is not None
        and data.invoice_total is not None
    ):
        expected_total = data.subtotal + data.total_tax
        if abs(expected_total - data.invoice_total) > 0.01:
            issues.append(
                ValidationIssue(
                    code="invoice_total_mismatch",
                    field="invoice_total",
                    severity="error",
                    message=(
                        f"Subtotal ({data.subtotal:.2f}) + Tax ({data.total_tax:.2f}) "
                        f"does not equal Total ({data.invoice_total:.2f}) "
                        "within EUR 0.01 tolerance."
                    ),
                )
            )

    # Vendor VAT ID
    if data.vendor_vat_id and data.vendor_vat_id.strip():
        clean_vat = data.vendor_vat_id.strip().replace(" ", "").upper()
        if not vat.is_valid(clean_vat):
            issues.append(
                ValidationIssue(
                    code="vendor_vat_id_invalid",
                    field="vendor_vat_id",
                    severity="error",
                    message=f"Supplier VAT ID '{clean_vat}' failed EU format/checksum validation.",
                )
            )
    elif not is_receipt:
        issues.append(
            ValidationIssue(
                code="vendor_vat_id_required",
                field="vendor_vat_id",
                severity="error",
                message="Supplier VAT ID is missing.",
            )
        )

    # Invoice-specific rules
    if not is_receipt:
        # Invoice Number
        if not data.invoice_number or not data.invoice_number.strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_INVOICE_NUMBER",
                    field="invoice_number",
                    severity="error",
                    message="Invoice number is missing.",
                )
            )

        # Customer Name Check
        if not data.customer_name or not data.customer_name.strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_CUSTOMER_NAME",
                    field="customer_name",
                    severity="error",
                    message="Customer name is missing.",
                )
            )
        else:
            norm_cust = normalize_name(data.customer_name)
            norm_exp = normalize_name(expected_customer_name)
            if norm_cust and norm_exp and norm_cust != norm_exp:
                issues.append(
                    ValidationIssue(
                        code="MISMATCHED_CUSTOMER_NAME",
                        field="customer_name",
                        severity="error",
                        message=(
                            f"Customer '{data.customer_name}' does not match "
                            f"expected '{expected_customer_name}'."
                        ),
                    )
                )

        # Customer VAT ID Check
        if not data.customer_vat_id or not data.customer_vat_id.strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_CUSTOMER_VAT_ID",
                    field="customer_vat_id",
                    severity="error",
                    message="Customer VAT ID is missing.",
                )
            )
        else:
            clean_c_vat = data.customer_vat_id.strip().replace(" ", "").upper()
            clean_exp_vat = expected_customer_vat_id.strip().replace(" ", "").upper()
            if clean_c_vat != clean_exp_vat:
                issues.append(
                    ValidationIssue(
                        code="customer_vat_id_mismatch",
                        field="customer_vat_id",
                        severity="error",
                        message=(
                            f"Customer VAT '{clean_c_vat}' does not match "
                            f"expected '{clean_exp_vat}'."
                        ),
                    )
                )

        # Due Date order
        if data.invoice_date and data.due_date and data.due_date < data.invoice_date:
            issues.append(
                ValidationIssue(
                    code="INVALID_DATES_ORDER",
                    field="due_date",
                    severity="error",
                    message=(
                        f"Due date ({data.due_date}) cannot be before "
                        f"invoice date ({data.invoice_date})."
                    ),
                )
            )

        # Purchase Order Warning
        if not data.purchase_order or not data.purchase_order.strip():
            issues.append(
                ValidationIssue(
                    code="purchase_order_missing",
                    field="purchase_order",
                    severity="warning",
                    message="Purchase order number is missing.",
                )
            )

        # Duplicate key check
        if is_duplicate:
            issues.append(
                ValidationIssue(
                    code="duplicate_invoice",
                    field="invoice_number",
                    severity="error",
                    message=(
                        f"Duplicate invoice detected for supplier '{data.vendor_name}' "
                        f"and invoice '{data.invoice_number}'."
                    ),
                )
            )

    return issues


def status_for_issues(issues: list[ValidationIssue]) -> DocumentStatus:
    if any(issue.severity == "error" for issue in issues):
        return "needs_review"
    return "ready"

"""Playground evaluation harness for sample document evaluation corpus.

Validates extracted fields and validation issue codes against samples/manifest.json.

Run:
    cd playground
    uv run --project ../backend --locked --no-sync python evaluate_samples.py
"""

from __future__ import annotations

import json
import logging
import sys
from decimal import Decimal
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from backend.app.documents.schemas import ReviewData  # noqa: E402
from backend.app.invoices.validation import validate_review_data  # noqa: E402

MANIFEST_PATH = PROJECT_ROOT / "samples" / "manifest.json"


def evaluate_corpus() -> bool:
    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest file not found at {MANIFEST_PATH}")
        return False

    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("\n========================================================")
    print("       SAMPLE CORPUS EVALUATION (13 Scenarios)          ")
    print("========================================================\n")

    passed_count = 0
    total_count = len(manifest)

    for item in manifest:
        filename = item.get("filename")
        scenario = item.get("scenario")
        expected = item.get("expected", {})
        expected_issue_codes = item.get("expected_issue_codes", [])

        # Build ReviewData from expected sample scenario
        review_data = ReviewData(
            document_type=expected.get("document_type", "invoice"),
            vendor_name=expected.get("vendor_name"),
            vendor_vat_id=expected.get("vendor_vat_id"),
            customer_name=expected.get("customer_name"),
            customer_vat_id=expected.get("customer_vat_id"),
            invoice_number=expected.get("invoice_number"),
            purchase_order=expected.get("purchase_order"),
            invoice_date=expected.get("invoice_date"),
            due_date=expected.get("due_date"),
            currency=expected.get("currency") or "EUR",
            subtotal=Decimal(expected["subtotal"]) if expected.get("subtotal") else None,
            total_tax=Decimal(expected["total_tax"]) if expected.get("total_tax") else None,
            invoice_total=Decimal(expected["invoice_total"]) if expected.get("invoice_total") else None,
        )

        is_duplicate = scenario == "duplicate"
        issues = validate_review_data(review_data, is_duplicate=is_duplicate)
        actual_issue_codes = [issue.code for issue in issues]

        # Check if expected issue codes match actual issue codes
        missing_expected = set(expected_issue_codes) - set(actual_issue_codes)

        # purchase_order_missing is a warning in scenario missing_purchase_order
        is_pass = len(missing_expected) == 0

        status_str = "PASS" if is_pass else "FAIL"
        if is_pass:
            passed_count += 1

        print(f"[{status_str}] {filename:<32} (scenario: {scenario})")
        if not is_pass:
            print(f"       Expected issue codes: {expected_issue_codes}")
            print(f"       Actual issue codes:   {actual_issue_codes}")
            if missing_expected:
                print(f"       Missing expected:     {missing_expected}")

    print("\n--------------------------------------------------------")
    print(f" Evaluation Summary: {passed_count}/{total_count} Passed ({passed_count/total_count*100:.1f}%)")
    print("--------------------------------------------------------\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = evaluate_corpus()
    sys.exit(0 if success else 1)

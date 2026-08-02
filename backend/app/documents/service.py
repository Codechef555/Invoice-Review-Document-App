from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import AppConfig
from app.documents.models import DocumentRecord
from app.documents.repository import DocumentRepository
from app.documents.schemas import (
    AccountingCoding,
    AccountingSuggestion,
    DocumentCorrectionRequest,
    ReviewData,
    ReviewLineItem,
)
from app.invoices.validation import status_for_issues, validate_review_data
from app.pipeline.chain import Pipeline, PipelineContext
from app.pipeline.gl_categorization import GL_CATALOG, GLCategorization
from app.pipeline.steps import (
    ClassificationStep,
    ExtractionStep,
    GLCategorizationStep,
    MappingStep,
    ValidationStep,
)


class DocumentNotFoundError(RuntimeError):
    pass


class DocumentProcessingError(RuntimeError):
    pass


class DocumentContentError(RuntimeError):
    pass


class DocumentReviewConflictError(RuntimeError):
    pass


def _parse_date(val: Any) -> date | None:
    if isinstance(val, date):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return date.fromisoformat(val.strip())
        except ValueError:
            return None
    return None


def _parse_decimal(val: Any) -> Decimal | None:
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    if isinstance(val, str) and val.strip():
        try:
            return Decimal(val.strip())
        except Exception:
            return None
    return None


def _extracted_to_review_data(
    context: PipelineContext,
) -> ReviewData:
    data = context.extracted_data
    doc_type = context.classification.document_type if context.classification else "invoice"
    if doc_type == "unsupported":
        doc_type = "invoice"

    if not data:
        return ReviewData(document_type="receipt" if doc_type == "receipt" else "invoice")

    def get_str(field_name: str) -> str | None:
        val_obj = getattr(data, field_name, None)
        if not val_obj:
            return None
        v = getattr(val_obj, "value", None) or getattr(val_obj, "content", None)
        return str(v).strip() if v is not None else None

    def get_date(field_name: str) -> date | None:
        val_obj = getattr(data, field_name, None)
        if not val_obj:
            return None
        v = getattr(val_obj, "value", None) or getattr(val_obj, "content", None)
        return _parse_date(v)

    def get_dec(field_name: str) -> Decimal | None:
        val_obj = getattr(data, field_name, None)
        if not val_obj:
            return None
        v = getattr(val_obj, "value", None) or getattr(val_obj, "content", None)
        return _parse_decimal(v)

    line_items: list[ReviewLineItem] = []
    for item in getattr(data, "line_items", []):
        desc = (
            getattr(item.description, "value", None) or getattr(item.description, "content", None)
            if item.description
            else None
        )
        amt = (
            getattr(item.amount, "value", None) or getattr(item.amount, "content", None)
            if item.amount
            else None
        )
        qty = (
            getattr(item.quantity, "value", None) or getattr(item.quantity, "content", None)
            if item.quantity
            else None
        )
        uprice = (
            getattr(item.unit_price, "value", None) or getattr(item.unit_price, "content", None)
            if item.unit_price
            else None
        )

        line_items.append(
            ReviewLineItem(
                description=str(desc) if desc else None,
                quantity=_parse_decimal(qty),
                unit_price=_parse_decimal(uprice),
                amount=_parse_decimal(amt),
            )
        )

    return ReviewData(
        document_type="receipt" if doc_type == "receipt" else "invoice",
        vendor_name=get_str("vendor_name"),
        vendor_vat_id=get_str("vendor_vat_id"),
        customer_name=get_str("customer_name"),
        customer_vat_id=get_str("customer_vat_id"),
        invoice_number=get_str("invoice_number"),
        purchase_order=get_str("purchase_order"),
        invoice_date=get_date("invoice_date"),
        due_date=get_date("due_date"),
        currency=get_str("currency") or "EUR",
        subtotal=get_dec("subtotal"),
        total_tax=get_dec("total_tax"),
        invoice_total=get_dec("invoice_total"),
        line_items=line_items,
    )


def _accounting_from_gl_categorization(
    gl_cat: GLCategorization | None,
) -> AccountingCoding:
    if gl_cat is None:
        return AccountingCoding(error_message="No GL suggestion was produced.")
    coded = AccountingSuggestion(
        gl_account_code=gl_cat.account_code,
        category=gl_cat.account_name,
        rationale=gl_cat.reasoning,
        confidence=gl_cat.confidence,
    )
    return AccountingCoding(
        suggestion=coded,
        selected_gl_account_code=coded.gl_account_code,
        overridden=False,
    )


class DocumentService:
    def __init__(
        self,
        *,
        repository: DocumentRepository,
        upload_dir: Path,
        expected_customer_name: str = "Northstar Facilities B.V.",
        expected_customer_vat_id: str = "NL00449544B01",
        min_confidence: float = 0.80,
    ) -> None:
        self.repository = repository
        self.upload_dir = upload_dir
        self.expected_customer_name = expected_customer_name
        self.expected_customer_vat_id = expected_customer_vat_id
        self.min_confidence = min_confidence

    def process(
        self,
        *,
        original_filename: str,
        content_type: str,
        content: bytes,
        suffix: str,
    ) -> DocumentRecord:
        record_id = str(uuid4())
        stored_filename = f"{record_id}{suffix}"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        stored_path = self.upload_dir / stored_filename
        stored_path.write_bytes(content)

        self.repository.create_processing(
            record_id=record_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
        )

        try:
            pipeline = (
                Pipeline()
                .add_step(ClassificationStep())
                .add_step(ExtractionStep())
                .add_step(MappingStep())
                .add_step(ValidationStep())
                .add_step(GLCategorizationStep())
            )
            context = PipelineContext(file_path=stored_path)
            context = pipeline.execute(context)
        except Exception as error:
            message = str(error) or error.__class__.__name__
            self.repository.save_failure(record_id, message)
            raise DocumentProcessingError(message) from error

        if context.classification and context.classification.document_type == "unsupported":
            msg = "Document type 'unsupported' cannot be analyzed."
            self.repository.save_failure(record_id, msg)
            raise DocumentContentError(msg)

        review_data = _extracted_to_review_data(context)

        is_duplicate = bool(
            review_data.vendor_name
            and review_data.invoice_number
            and self.repository.duplicate_exists(
                review_data.vendor_name, review_data.invoice_number
            )
        )

        issues = validate_review_data(
            review_data,
            expected_customer_name=self.expected_customer_name,
            expected_customer_vat_id=self.expected_customer_vat_id,
            min_confidence=self.min_confidence,
            is_duplicate=is_duplicate,
        )

        classification_dump = (
            context.classification.model_dump(mode="json")
            if context.classification
            else None
        )
        gl_dump = (
            context.gl_categorization.model_dump(mode="json")
            if context.gl_categorization
            else None
        )
        accounting_coding = _accounting_from_gl_categorization(context.gl_categorization)

        return self.repository.save_result(
            record_id,
            status=status_for_issues(issues),
            classification=classification_dump,
            extraction=context.raw_analysis,
            validation={
                "findings": [issue.model_dump(mode="json") for issue in issues],
                "has_errors": any(issue.severity == "error" for issue in issues),
            },
            gl_suggestion=gl_dump,
            review_data=review_data,
            accounting_coding=accounting_coding,
            issues=issues,
        )

    def get(self, record_id: str) -> DocumentRecord:
        record = self.repository.get(record_id)
        if record is None:
            raise DocumentNotFoundError("Document not found")
        return record

    def list(self) -> list[DocumentRecord]:
        return self.repository.list()

    def revalidate(
        self, record_id: str, corrections: DocumentCorrectionRequest
    ) -> DocumentRecord:
        record = self.repository.get(record_id)
        if record is None:
            raise DocumentNotFoundError("Document not found")
        if record.status in {"approved", "rejected"}:
            raise DocumentReviewConflictError("A decided document cannot be edited.")

        saved_data = ReviewData.model_validate(record.review_data or {})
        corrected_fields = corrections.model_dump(exclude_unset=True)
        data = saved_data.model_copy(update=corrected_fields)

        is_duplicate = bool(
            data.vendor_name
            and data.invoice_number
            and self.repository.duplicate_exists(
                data.vendor_name, data.invoice_number, exclude_id=record_id
            )
        )
        issues = validate_review_data(
            data,
            expected_customer_name=self.expected_customer_name,
            expected_customer_vat_id=self.expected_customer_vat_id,
            min_confidence=self.min_confidence,
            is_duplicate=is_duplicate,
        )
        accounting_coding = AccountingCoding.model_validate(record.accounting_coding or {})
        return self.repository.save_review(
            record_id,
            review_data=data,
            issues=issues,
            status=status_for_issues(issues),
            accounting_coding=accounting_coding,
        )

    def select_gl_account(self, record_id: str, gl_account_code: str) -> DocumentRecord:
        record = self.repository.get(record_id)
        if record is None:
            raise DocumentNotFoundError("Document not found")
        if record.status in {"approved", "rejected"}:
            raise DocumentReviewConflictError("A decided document cannot be edited.")

        valid_codes = {acc["code"] for acc in GL_CATALOG}
        if gl_account_code not in valid_codes:
            raise ValueError(f"Unknown GL account code: {gl_account_code}")

        return self.repository.select_gl_account(record_id, gl_account_code)

    def decide(self, record_id: str, decision: str) -> DocumentRecord:
        record = self.repository.get(record_id)
        if record is None:
            raise DocumentNotFoundError("Document not found")
        if record.status in {"approved", "rejected"}:
            raise DocumentReviewConflictError("This document already has a decision.")
        if record.status in {"processing", "failed"}:
            raise DocumentReviewConflictError("Only a completed review can receive a decision.")

        if decision == "approved" and any(
            issue.get("severity") == "error" for issue in (record.issues or [])
        ):
            raise DocumentReviewConflictError("Resolve all validation errors before approval.")

        coding = AccountingCoding.model_validate(record.accounting_coding or {})
        if decision == "approved" and not coding.selected_gl_account_code:
            raise DocumentReviewConflictError("Select a valid GL account before approval.")

        if decision not in {"approved", "rejected"}:
            raise ValueError(f"Unsupported decision: {decision}")

        return self.repository.set_status(record_id, decision)  # type: ignore[arg-type]

    def delete(self, record_id: str) -> None:
        record = self.repository.get(record_id)
        if record is None:
            raise DocumentNotFoundError(f"Document {record_id} was not found.")
        stored_path = self.upload_dir / Path(record.stored_filename).name
        self.repository.delete(record_id)
        stored_path.unlink(missing_ok=True)


def build_service_from_config(
    repository: DocumentRepository,
    config: AppConfig,
) -> DocumentService:
    return DocumentService(
        repository=repository,
        upload_dir=config.upload_dir,
        expected_customer_name=config.expected_customer_name,
        expected_customer_vat_id=config.expected_customer_vat_id,
        min_confidence=config.min_field_confidence,
    )

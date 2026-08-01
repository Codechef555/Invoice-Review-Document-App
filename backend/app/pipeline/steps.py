from __future__ import annotations

import re
from typing import Any

from stdnum.eu import vat

from app.pipeline.chain import PipelineContext, PipelineStep
from app.pipeline.classification import classify_document_text
from app.schemas.common import ValidationIssue, ValidationResult
from app.schemas.invoice.mapping import map_invoice_fields
from app.schemas.receipt.mapping import map_receipt_fields
from app.services.document_intelligence_services import DocumentIntelligenceService


class ClassificationStep(PipelineStep):
    """Step 1: Classify document as invoice, receipt, or unsupported using Azure OpenAI."""

    def __init__(self, deployment: str | None = None) -> None:
        self.deployment = deployment

    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.document_text:
            context.document_text = f"Sample document from path: {context.file_path.name}"

        try:
            classification = classify_document_text(
                document_text=context.document_text,
                deployment=self.deployment,
            )
            context.classification = classification
        except Exception as err:
            context.errors.append(f"ClassificationStep failed: {err}")

        return context


class ExtractionStep(PipelineStep):
    """Step 2: Route to prebuilt-invoice or prebuilt-receipt model in Document Intelligence."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        doc_service: DocumentIntelligenceService | None = None,
    ) -> None:
        self.doc_service = doc_service or DocumentIntelligenceService(
            endpoint=endpoint, api_key=api_key
        )

    def process(self, context: PipelineContext) -> PipelineContext:
        doc_type = (
            context.classification.document_type
            if context.classification
            else "invoice"
        )

        if doc_type == "unsupported":
            context.errors.append(
                "Document type 'unsupported' cannot be analyzed by Document Intelligence."
            )
            return context

        model_id = "prebuilt-receipt" if doc_type == "receipt" else "prebuilt-invoice"
        context.metadata["selected_model_id"] = model_id

        try:
            raw_result = self.doc_service.analyze_document(
                document_path=context.file_path,
                model_id=model_id,
            )
            context.raw_analysis = self.doc_service.to_dict(raw_result)
        except Exception as err:
            context.errors.append(f"ExtractionStep failed for model '{model_id}': {err}")

        return context


class MappingStep(PipelineStep):
    """Step 3: Map raw Document Intelligence payload into Pydantic Invoice/Receipt models."""

    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.raw_analysis:
            context.errors.append("MappingStep failed: raw_analysis is empty.")
            return context

        doc_type = (
            context.classification.document_type
            if context.classification
            else "invoice"
        )

        if doc_type == "receipt":
            context.extracted_data = map_receipt_fields(context.raw_analysis)
        else:
            context.extracted_data = map_invoice_fields(context.raw_analysis)

        return context


class ValidationStep(PipelineStep):
    """Step 4: Offline EU VAT format/checksum validation & subtotal + VAT reconciliation."""

    @staticmethod
    def _parse_amount(value_obj: Any) -> float | None:
        if not value_obj:
            return None
        val = getattr(value_obj, "value", None)
        if isinstance(val, (int, float)):
            return float(val)
        content = getattr(value_obj, "content", None) or str(val or "")
        clean = re.sub(r"[^\d.-]", "", content)
        try:
            return float(clean) if clean else None
        except ValueError:
            return None

    def process(self, context: PipelineContext) -> PipelineContext:
        data = context.extracted_data
        if not data:
            context.errors.append("ValidationStep failed: extracted_data is empty.")
            return context

        issues: list[ValidationIssue] = []

        # 1. EU VAT Number Validation via python-stdnum (offline structure & checksum check)
        for field_name, label in [
            ("vendor_vat_id", "Supplier VAT ID"),
            ("customer_vat_id", "Customer VAT ID"),
        ]:
            vat_val_obj = getattr(data, field_name, None)
            if vat_val_obj and (vat_val_obj.value or vat_val_obj.content):
                vat_str = str(vat_val_obj.value or vat_val_obj.content)
                raw_vat = vat_str.strip().replace(" ", "").upper()
                if raw_vat:
                    is_valid_vat = vat.is_valid(raw_vat)
                    if not is_valid_vat:
                        issues.append(
                            ValidationIssue(
                                code="INVALID_EU_VAT_FORMAT",
                                severity="error",
                                message=(
                                    f"{label} '{raw_vat}' failed EU VAT format/checksum validation."
                                ),
                                field=field_name,
                            )
                        )

        # 2. Subtotal + Tax Reconciliation (within EUR 0.01 tolerance)
        subtotal = self._parse_amount(getattr(data, "subtotal", None))
        total_tax = self._parse_amount(getattr(data, "total_tax", None))
        total = self._parse_amount(getattr(data, "invoice_total", None))

        if subtotal is not None and total_tax is not None and total is not None:
            expected = subtotal + total_tax
            diff = abs(expected - total)
            if diff > 0.01:
                issues.append(
                    ValidationIssue(
                        code="MATHEMATICAL_RECONCILIATION_MISMATCH",
                        severity="error",
                        message=(
                            f"Financial reconciliation mismatch: subtotal ({subtotal:.2f}) + "
                            f"tax ({total_tax:.2f}) = {expected:.2f}, but total is {total:.2f} "
                            f"(diff: {diff:.2f} EUR)."
                        ),
                        field="invoice_total",
                    )
                )

        has_errors = any(i.severity == "error" for i in issues)
        context.validation_results = ValidationResult(
            is_valid=not has_errors,
            issues=issues,
        )

        return context

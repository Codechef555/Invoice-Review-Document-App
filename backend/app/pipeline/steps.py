from __future__ import annotations

import logging
import re
from typing import Any

from stdnum.eu import vat

from app.pipeline.chain import PipelineContext, PipelineStep
from app.pipeline.classification import classify_document_text
from app.pipeline.gl_categorization import suggest_gl_account
from app.schemas.common import ValidationIssue, ValidationResult
from app.schemas.invoice.mapping import map_invoice_fields
from app.schemas.receipt.mapping import map_receipt_fields
from app.services.document_intelligence_services import DocumentIntelligenceService

logger = logging.getLogger(__name__)


class ClassificationStep(PipelineStep):
    """Step 1: Classify document as invoice, receipt, or unsupported using Azure OpenAI."""

    def __init__(self, deployment: str | None = None) -> None:
        self.deployment = deployment

    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.document_text:
            context.document_text = f"Sample document from path: {context.file_path.name}"

        logger.info(
            "[ClassificationStep] Classifying text (length: %d chars)...",
            len(context.document_text),
        )
        try:
            classification = classify_document_text(
                document_text=context.document_text,
                deployment=self.deployment,
            )
            context.classification = classification
            logger.info(
                "[ClassificationStep] Result: type='%s', confidence=%.2f, keywords=%s",
                classification.document_type,
                classification.confidence,
                classification.detected_keywords,
            )
        except Exception as err:
            logger.error("[ClassificationStep] Error: %s", err)
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
        logger.info(
            "[ExtractionStep] Selecting model for doc_type='%s' (file: '%s')...",
            doc_type,
            context.file_path.name,
        )

        if doc_type == "unsupported":
            msg = "Document type 'unsupported' cannot be analyzed by Document Intelligence."
            logger.warning("[ExtractionStep] %s", msg)
            context.errors.append(msg)
            return context

        model_id = "prebuilt-receipt" if doc_type == "receipt" else "prebuilt-invoice"
        context.metadata["selected_model_id"] = model_id
        logger.info("[ExtractionStep] Analyzing document with model_id='%s'...", model_id)

        try:
            raw_result = self.doc_service.analyze_document(
                document_path=context.file_path,
                model_id=model_id,
            )
            context.raw_analysis = self.doc_service.to_dict(raw_result)
            logger.info("[ExtractionStep] Document Intelligence extraction completed.")
        except Exception as err:
            logger.error("[ExtractionStep] Failed for model '%s': %s", model_id, err)
            context.errors.append(f"ExtractionStep failed for model '{model_id}': {err}")

        return context


class MappingStep(PipelineStep):
    """Step 3: Map raw Document Intelligence payload into Pydantic Invoice/Receipt models."""

    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.raw_analysis:
            logger.error("[MappingStep] raw_analysis is empty.")
            context.errors.append("MappingStep failed: raw_analysis is empty.")
            return context

        doc_type = (
            context.classification.document_type
            if context.classification
            else "invoice"
        )

        logger.info(
            "[MappingStep] Mapping raw analysis into Pydantic model for doc_type='%s'...",
            doc_type,
        )
        if doc_type == "receipt":
            context.extracted_data = map_receipt_fields(context.raw_analysis)
        else:
            context.extracted_data = map_invoice_fields(context.raw_analysis)

        line_count = len(context.extracted_data.line_items) if context.extracted_data else 0
        logger.info(
            "[MappingStep] Successfully mapped fields into %s (%d line items).",
            type(context.extracted_data).__name__,
            line_count,
        )

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
            logger.error("[ValidationStep] extracted_data is empty.")
            context.errors.append("ValidationStep failed: extracted_data is empty.")
            return context

        logger.info(
            "[ValidationStep] Validating extracted data (EU VAT IDs & financial reconciliation)..."
        )
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
                        logger.warning(
                            "[ValidationStep] %s '%s' failed EU VAT validation.", label, raw_vat
                        )
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
                logger.warning(
                    "[ValidationStep] Total mismatch: subtotal(%.2f) + tax(%.2f) != total(%.2f)",
                    subtotal,
                    total_tax,
                    total,
                )
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
        logger.info(
            "[ValidationStep] Validation completed: is_valid=%s, issues_count=%d",
            context.validation_results.is_valid,
            len(issues),
        )

        return context


class GLCategorizationStep(PipelineStep):
    """Step 5: Suggest General Ledger (GL) account code based on extracted document details."""

    def __init__(self, deployment: str | None = None) -> None:
        self.deployment = deployment

    def process(self, context: PipelineContext) -> PipelineContext:
        if not context.extracted_data:
            logger.error("[GLCategorizationStep] extracted_data is empty.")
            context.errors.append("GLCategorizationStep failed: extracted_data is empty.")
            return context

        logger.info("[GLCategorizationStep] Requesting GL account suggestion...")
        try:
            gl_result = suggest_gl_account(
                extracted_data=context.extracted_data,
                deployment=self.deployment,
            )
            context.gl_categorization = gl_result
            logger.info(
                "[GLCategorizationStep] Suggested GL Account: [%s] %s (confidence: %.2f)",
                gl_result.account_code,
                gl_result.account_name,
                gl_result.confidence,
            )
        except Exception as err:
            logger.error("[GLCategorizationStep] Error: %s", err)
            context.errors.append(f"GLCategorizationStep failed: {err}")

        return context

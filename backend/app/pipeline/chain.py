from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.pipeline.classification import DocumentClassification
from app.schemas.common import ValidationResult
from app.schemas.invoice.model import InvoiceExtraction
from app.schemas.receipt.model import ReceiptExtraction

logger = logging.getLogger(__name__)


class PipelineContext(BaseModel):
    file_path: Path
    document_text: str | None = None
    classification: DocumentClassification | None = None
    raw_analysis: dict[str, Any] | None = None
    extracted_data: InvoiceExtraction | ReceiptExtraction | None = None
    validation_results: ValidationResult | None = None
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineStep(ABC):
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process pipeline context and return updated context."""
        pass


class Pipeline:
    def __init__(self, steps: list[PipelineStep] | None = None) -> None:
        self.steps: list[PipelineStep] = steps or []

    def add_step(self, step: PipelineStep) -> Pipeline:
        self.steps.append(step)
        return self

    def execute(self, context: PipelineContext) -> PipelineContext:
        logger.info(
            "Starting pipeline execution for '%s' (%d steps)",
            context.file_path.name,
            len(self.steps),
        )
        for idx, step in enumerate(self.steps, start=1):
            step_name = step.__class__.__name__
            if context.errors:
                logger.warning(
                    "Aborting pipeline at step %d/%d (%s) due to previous errors: %s",
                    idx,
                    len(self.steps),
                    step_name,
                    context.errors,
                )
                break
            logger.info("Executing pipeline step %d/%d: %s", idx, len(self.steps), step_name)
            context = step.process(context)
            logger.info("Completed pipeline step %d/%d: %s", idx, len(self.steps), step_name)

        logger.info(
            "Pipeline execution finished for '%s' (Errors: %d)",
            context.file_path.name,
            len(context.errors),
        )
        return context

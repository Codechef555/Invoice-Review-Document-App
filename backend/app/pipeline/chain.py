from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.pipeline.classification import DocumentClassification
from app.schemas.common import ValidationResult
from app.schemas.invoice.model import InvoiceExtraction
from app.schemas.receipt.model import ReceiptExtraction


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
        for step in self.steps:
            if context.errors:
                break
            context = step.process(context)
        return context

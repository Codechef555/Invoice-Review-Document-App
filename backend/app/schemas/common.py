from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExtractedValue(BaseModel):
    value: Any | None = None
    content: str | None = None
    confidence: float | None = None

    @classmethod
    def from_di_field(cls, field: Any) -> ExtractedValue:
        if field is None:
            return cls()

        if isinstance(field, dict):
            return cls(
                value=field.get("value"),
                content=field.get("content"),
                confidence=field.get("confidence"),
            )

        return cls(
            value=getattr(field, "value", None),
            content=getattr(field, "content", None),
            confidence=getattr(field, "confidence", None),
        )


class LineItem(BaseModel):
    description: ExtractedValue | None = None
    amount: ExtractedValue | None = None
    quantity: ExtractedValue | None = None
    unit_price: ExtractedValue | None = None
    product_code: ExtractedValue | None = None


class ValidationIssue(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"] = "error"
    message: str
    field: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool = True
    issues: list[ValidationIssue] = Field(default_factory=list)

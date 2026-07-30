from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ExtractedValue(BaseModel):
    value: Any | None = None
    content: str | None = None
    confidence: float | None = None

    @classmethod
    def from_di_field(cls, field: Any) -> "ExtractedValue":
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

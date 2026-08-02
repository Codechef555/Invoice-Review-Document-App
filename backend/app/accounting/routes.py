from __future__ import annotations

from fastapi import APIRouter

from app.pipeline.gl_categorization import GL_CATALOG

router = APIRouter(prefix="/api/accounting", tags=["accounting"])


@router.get("/catalog")
def get_accounting_catalog() -> list[dict[str, str]]:
    return GL_CATALOG

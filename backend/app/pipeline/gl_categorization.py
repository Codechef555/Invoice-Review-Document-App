from __future__ import annotations

import logging
import os

from pydantic import BaseModel, Field

from app.schemas.invoice.model import InvoiceExtraction
from app.schemas.receipt.model import ReceiptExtraction
from app.services.azure_openai_service import get_azure_openai_client

logger = logging.getLogger(__name__)

GL_CATALOG: list[dict[str, str]] = [
    {
        "code": "4000",
        "name": "Office Supplies & Stationery",
        "description": "Paper, pens, toner, small office equipment, stationery",
    },
    {
        "code": "4100",
        "name": "Software & IT Services",
        "description": "SaaS subscriptions, IT support, cloud infrastructure, software licenses",
    },
    {
        "code": "4200",
        "name": "Cleaning & Janitorial Services",
        "description": "Facility cleaning, sanitation, waste management, janitorial supplies",
    },
    {
        "code": "4300",
        "name": "Building Maintenance & Repairs",
        "description": "HVAC, plumbing, electrical repairs, facility maintenance",
    },
    {
        "code": "4400",
        "name": "Utilities",
        "description": "Electricity, heating gas, water, telecom, internet services",
    },
    {
        "code": "4500",
        "name": "Professional & Legal Services",
        "description": "Consulting, accounting, legal fees, auditing services",
    },
    {
        "code": "4600",
        "name": "Travel & Transportation",
        "description": "Fuel, vehicle maintenance, parking, public transit, business travel",
    },
    {
        "code": "4700",
        "name": "Equipment Rental & Leasing",
        "description": "Machinery rental, tool leasing, vehicle/equipment hire",
    },
    {
        "code": "4800",
        "name": "Catering & Team Meals",
        "description": "Office meals, team events, food supplies, coffee/catering",
    },
    {
        "code": "4900",
        "name": "Miscellaneous Operating Expenses",
        "description": "General operating expenses not covered by other categories",
    },
]


class GLCategorization(BaseModel):
    account_code: str = Field(
        description="4-digit GL account code matching one of the 10 catalog accounts."
    )
    account_name: str = Field(
        description="The matching GL account name from the catalog."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0.",
    )
    reasoning: str = Field(
        description="Short rationale explaining why this GL account was selected.",
    )


def _format_extracted_summary(data: InvoiceExtraction | ReceiptExtraction) -> str:
    vendor = getattr(data, "vendor_name", None)
    v_val = (vendor.value or vendor.content) if vendor else None
    vendor_str = str(v_val) if v_val else "Unknown"

    total_obj = getattr(data, "invoice_total", None)
    t_val = (total_obj.value or total_obj.content) if total_obj else None
    total_str = str(t_val) if t_val else "Unknown"

    curr_obj = getattr(data, "currency", None)
    c_val = (curr_obj.value or curr_obj.content) if curr_obj else None
    currency_str = str(c_val) if c_val else "EUR"

    line_descriptions = []
    for item in getattr(data, "line_items", []):
        desc = item.description
        if desc and (desc.value or desc.content):
            line_descriptions.append(str(desc.value or desc.content))

    items_str = "; ".join(line_descriptions) if line_descriptions else "N/A"

    return (
        f"Vendor/Supplier: {vendor_str}\n"
        f"Document Total: {total_str} {currency_str}\n"
        f"Line Items: {items_str}"
    )


def suggest_gl_account(
    extracted_data: InvoiceExtraction | ReceiptExtraction,
    deployment: str | None = None,
) -> GLCategorization:
    """Suggests a General Ledger (GL) account code and name from normalized document data."""
    client = get_azure_openai_client()
    model_deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-5.6-terra"

    catalog_formatted = "\n".join(
        [f"- [{acc['code']}] {acc['name']}: {acc['description']}" for acc in GL_CATALOG]
    )

    system_prompt = (
        "You are an automated accounting assistant for Northstar Facilities B.V.\n"
        "Categorize the provided document into EXACTLY ONE General Ledger (GL) account "
        "from this catalog:\n\n"
        f"{catalog_formatted}\n\n"
        "Return the account_code (4 digits), account_name, confidence (0.0 to 1.0), and reasoning."
    )

    doc_summary = _format_extracted_summary(extracted_data)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Document Summary:\n{doc_summary}"},
    ]

    logger.info("Requesting GL categorization from Azure OpenAI structured output...")
    completion = client.beta.chat.completions.parse(
        model=model_deployment,
        messages=messages,
        response_format=GLCategorization,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Azure OpenAI response did not return a valid GLCategorization structure.")

    return parsed

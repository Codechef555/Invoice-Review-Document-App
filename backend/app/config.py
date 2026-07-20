from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    azure_document_intelligence_endpoint: AnyHttpUrl
    azure_document_intelligence_key: str = Field(min_length=1)
    azure_openai_endpoint: AnyHttpUrl
    azure_openai_deployment: str = "gpt-5.6-terra"
    azure_openai_api_key: SecretStr | None = Field(default=None, min_length=1)
    expected_customer_name: str = "Northstar Facilities B.V."
    expected_customer_vat_id: str = "NL00449544B01"
    database_url: str = "sqlite:///./data/invoices.db"
    upload_dir: Path = Path("./data/uploads")
    max_upload_bytes: int = 4 * 1024 * 1024
    min_field_confidence: float = Field(default=0.80, ge=0, le=1)
    allowed_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

# Walk up from backend/app/ to find .env in the project root
_ROOT = Path(__file__).parent.parent.parent
_ENV_FILE = _ROOT / ".env"


class Settings(BaseSettings):
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    dev_auth: bool = False
    anthropic_api_key: str
    secret_key: str = "dev-secret-key-change-in-prod"
    database_url: str = "sqlite:///./app.db"
    pdf_storage_path: str = "./static/pdfs"
    admin_emails: str = ""
    frontend_url: str = "http://localhost:5173"

    @property
    def admin_email_list(self) -> List[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


settings = Settings()

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_config_dir = Path(__file__).resolve().parent
_project_root = _config_dir.parent
_workspace_root = _project_root.parent

# Workspace .env takes priority (user's main config file)
load_dotenv(_project_root / ".env")
load_dotenv(_workspace_root / ".env", override=True)


def _mask_secret(value: str, show: int = 4) -> str:
    """Mask a secret for safe logging."""
    if not value:
        return "(not set)"
    if len(value) <= show * 2:
        return "***"
    return f"{value[:show]}...{value[-show:]}"


def _resolve_database_url(url: str) -> str:
    """Resolve relative sqlite paths against project root."""
    if not url.startswith("sqlite"):
        return url
    path = url.replace("sqlite:///", "").replace("sqlite://", "")
    if not Path(path).is_absolute():
        path = str((_project_root / path).resolve())
    return f"sqlite:///{path.replace(chr(92), '/')}"


class Settings:
    def __init__(self):
        self.zoho_client_id: str = os.getenv("ZOHO_CLIENT_ID", "")
        self.zoho_client_secret: str = os.getenv("ZOHO_CLIENT_SECRET", "")
        self.zoho_redirect_uri: str = os.getenv("ZOHO_REDIRECT_URI", "http://localhost:8002/auth/callback")
        self.zoho_accounts_url: str = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
        self.zoho_api_base: str = os.getenv("ZOHO_API_BASE", "https://projectsapi.zoho.in/restapi")

        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "")
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        self.secret_key: str = os.getenv("SECRET_KEY", "your-secret-key")
        self.algorithm: str = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        self.database_url: str = _resolve_database_url(
            os.getenv("DATABASE_URL", "sqlite:///./zoho_chatbot.db")
        )
        self.frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

        self._env_sources = []
        if (_workspace_root / ".env").exists():
            self._env_sources.append(str(_workspace_root / ".env"))
        if (_project_root / ".env").exists():
            self._env_sources.append(str(_project_root / ".env"))


settings = Settings()


def log_startup_config() -> None:
    """Print loaded configuration at startup with secrets masked."""
    logger.info("=" * 50)
    logger.info("CONFIGURATION (secrets masked)")
    logger.info("=" * 50)
    logger.info(f"  .env sources: {settings._env_sources or ['environment only']}")
    logger.info(f"  ZOHO_CLIENT_ID:      {_mask_secret(settings.zoho_client_id, 8)}")
    logger.info(f"  ZOHO_CLIENT_SECRET:  {_mask_secret(settings.zoho_client_secret)}")
    logger.info(f"  ZOHO_REDIRECT_URI:   {settings.zoho_redirect_uri}")
    logger.info(f"  ZOHO_ACCOUNTS_URL:   {settings.zoho_accounts_url}")
    logger.info(f"  GROQ_API_KEY:        {_mask_secret(settings.groq_api_key)}")
    logger.info(f"  GROQ_MODEL:          {settings.groq_model}")
    logger.info(f"  GROQ_API_KEY set:    {bool(settings.groq_api_key)}")
    logger.info(f"  SECRET_KEY:          {_mask_secret(settings.secret_key)}")
    logger.info(f"  DATABASE_URL:        {settings.database_url}")
    logger.info(f"  FRONTEND_URL:        {settings.frontend_url}")
    logger.info(f"  ALGORITHM:           {settings.algorithm}")
    logger.info(f"  TOKEN_EXPIRE_MINS:   {settings.access_token_expire_minutes}")
    logger.info("=" * 50)

    missing = []
    if not settings.zoho_client_id:
        missing.append("ZOHO_CLIENT_ID")
    if not settings.zoho_client_secret:
        missing.append("ZOHO_CLIENT_SECRET")
    if not settings.groq_api_key:
        missing.append("GROQ_API_KEY")
    if not settings.secret_key or settings.secret_key == "your-secret-key":
        missing.append("SECRET_KEY")

    if missing:
        logger.warning(f"Missing required env vars: {', '.join(missing)}")
    else:
        logger.info("All required env vars are set.")

import httpx
import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode, quote

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from backend.config import settings
from backend.zoho_client import ensure_db_tables, _db_path_from_url

logger = logging.getLogger(__name__)


class ZohoOAuthManager:
    """Manages Zoho OAuth 2.0 Authorization Code Grant flow using aiosqlite storage."""

    @staticmethod
    def get_authorization_url() -> str:
        if not settings.zoho_client_id:
            raise RuntimeError("ZOHO_CLIENT_ID is not configured in .env")
        # Required scopes for Zoho Projects API
        scopes = (
            "AaaServer.profile.READ,"
            "ZohoProjects.portals.READ,"
            "ZohoProjects.projects.READ,ZohoProjects.projects.CREATE,ZohoProjects.projects.UPDATE,"
            "ZohoProjects.tasks.READ,ZohoProjects.tasks.CREATE,ZohoProjects.tasks.UPDATE,ZohoProjects.tasks.DELETE,"
            "ZohoProjects.users.READ"
        )
        auth_url = (
            f"{settings.zoho_accounts_url}/oauth/v2/auth?"
            f"scope={quote(scopes, safe='')}&"
            f"client_id={settings.zoho_client_id}&"
            f"response_type=code&"
            f"redirect_uri={quote(settings.zoho_redirect_uri, safe=':/?&=')}&"
            f"access_type=offline"
        )
        logger.info(f"📋 GENERATED AUTHORIZATION URL:")
        logger.info(f"   Scopes: {scopes}")
        logger.info(f"   URL: {auth_url[:100]}...")
        return auth_url

    @staticmethod
    def parse_user_info(user_info: Dict[str, Any]) -> Dict[str, str]:
        """Normalize Zoho user info field names across API versions."""
        user_id = str(
            user_info.get("user_id")
            or user_info.get("ZUID")
            or user_info.get("zuid")
            or user_info.get("sub")
            or user_info.get("id")
            or ""
        )
        email = (
            user_info.get("email")
            or user_info.get("Email")
            or user_info.get("primary_email")
            or user_info.get("EmailId")
            or ""
        )
        return {"user_id": user_id, "email": email or f"{user_id}@zoho.user"}

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        if not settings.zoho_client_id or not settings.zoho_client_secret:
            raise RuntimeError(
                "Zoho credentials missing. Set ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET in .env"
            )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.zoho_accounts_url}/oauth/v2/token",
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": settings.zoho_client_id,
                    "client_secret": settings.zoho_client_secret,
                    "redirect_uri": settings.zoho_redirect_uri,
                },
                timeout=30.0,
            )
            try:
                data = resp.json()
            except Exception:
                raise RuntimeError(
                    f"Zoho token endpoint returned non-JSON response (HTTP {resp.status_code}): {resp.text[:200]}"
                )
            if resp.status_code >= 400 or data.get("error"):
                error = data.get("error", "unknown_error")
                description = data.get("error_description", resp.text[:200])
                raise RuntimeError(
                    f"Zoho token exchange failed: {error} — {description}. "
                    f"Verify redirect URI in Zoho console matches: {settings.zoho_redirect_uri}"
                )
            if not data.get("access_token"):
                raise RuntimeError(
                    f"Zoho token response missing access_token. Keys returned: {list(data.keys())}"
                )
            return data

    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.zoho_accounts_url}/oauth/user/info",
                headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
                timeout=30.0,
            )
            try:
                data = resp.json()
            except Exception:
                raise RuntimeError(
                    f"Zoho user info returned non-JSON (HTTP {resp.status_code}): {resp.text[:200]}"
                )
            if resp.status_code >= 400 or data.get("error") or data.get("response") == "error":
                cause = data.get("cause") or data.get("error", resp.text[:200])
                hint = ""
                if cause == "INVALID_OAUTHSCOPE":
                    hint = " Re-authorize after adding AaaServer.profile.READ to your app scopes."
                raise RuntimeError(f"Zoho user info failed (HTTP {resp.status_code}): {cause}.{hint}")
            return data

    @staticmethod
    async def store_tokens(user_id: str, tokens_data: Dict[str, Any]) -> None:
        """Store access and refresh tokens in SQLite using aiosqlite."""
        await ensure_db_tables()
        db_path = _db_path_from_url(settings.database_url)
        access_token = tokens_data.get("access_token")
        refresh_token = tokens_data.get("refresh_token", "")
        expires_in = int(tokens_data.get("expires_in", 3600))
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_tokens "
                "(user_id, access_token, refresh_token, expires_at, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, access_token, refresh_token, expires_at.isoformat(), datetime.utcnow().isoformat()),
            )
            await db.commit()

    @staticmethod
    def create_jwt_token(user_id: str, email: str) -> str:
        if not settings.secret_key or settings.secret_key == "your-secret-key":
            logger.warning("Using default SECRET_KEY — set a strong SECRET_KEY in .env for production")
        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        # python-jose may return str or bytes depending on version
        return token if isinstance(token, str) else token.decode("utf-8")

    @staticmethod
    def build_frontend_redirect(jwt_token: str) -> str:
        """Build http://localhost:5173?token=xxx with proper URL encoding."""
        base = settings.frontend_url.rstrip("/")
        # URL-encode the JWT token to handle any special characters
        encoded_token = quote(jwt_token, safe='')
        redirect_url = f"{base}?token={encoded_token}"
        return redirect_url

    @staticmethod
    def verify_jwt_token(token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Verify JWT and return (payload, error_message)."""
        if not token or not token.strip():
            return None, "Token is empty"
        try:
            payload = jwt.decode(token.strip(), settings.secret_key, algorithms=[settings.algorithm])
            if not payload.get("sub"):
                return None, "Token is valid but missing user_id (sub claim)"
            return payload, None
        except ExpiredSignatureError:
            return None, "Token has expired — please log in again"
        except JWTError as exc:
            return None, f"Invalid token: {exc}"
        except Exception as exc:
            return None, f"Token verification failed: {exc}"

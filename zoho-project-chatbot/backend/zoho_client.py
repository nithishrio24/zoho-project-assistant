import httpx
import aiosqlite
import json
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any
from backend.config import settings

logger = logging.getLogger(__name__)


def _db_path_from_url(database_url: str) -> str:
    # Accepts sqlite:///./path or ./path
    if database_url.startswith("sqlite:///"):
        # strip the sqlite:/// prefix to get a filesystem path
        return database_url[len("sqlite:///"):]
    if database_url.startswith("sqlite://"):
        return database_url[len("sqlite://"):]
    return database_url


async def ensure_db_tables() -> None:
    db_path = _db_path_from_url(settings.database_url)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memory (
                user_id TEXT PRIMARY KEY,
                memory_data TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL
            )
            """
        )
        await db.commit()


class ZohoClient:
    """Async HTTP client for Zoho API with automatic token refresh using aiosqlite."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_url = settings.zoho_api_base.rstrip("/")
        self.token_cache: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.db_path = _db_path_from_url(settings.database_url)

    async def _get_token_row(self) -> Optional[Dict[str, Any]]:
        await ensure_db_tables()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT access_token, refresh_token, expires_at FROM user_tokens WHERE user_id = ?", (self.user_id,))
            row = await cur.fetchone()
            await cur.close()
            if not row:
                return None
            return {
                "access_token": row[0],
                "refresh_token": row[1],
                "expires_at": datetime.fromisoformat(row[2]),
            }

    async def _update_token_row(self, access_token: str, refresh_token: str, expires_at: datetime) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_tokens (user_id, access_token, refresh_token, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
                (self.user_id, access_token, refresh_token, expires_at.isoformat(), datetime.utcnow().isoformat()),
            )
            await db.commit()

    async def _get_valid_token(self) -> str:
        # Return cached if valid
        if self.token_cache and self.token_expiry and datetime.utcnow() < self.token_expiry - timedelta(minutes=1):
            return self.token_cache

        row = await self._get_token_row()
        if not row:
            raise Exception(f"No tokens found for user {self.user_id}")

        access_token = row["access_token"]
        refresh_token = row["refresh_token"]
        expires_at = row["expires_at"]

        if datetime.utcnow() >= expires_at - timedelta(seconds=10):
            # refresh
            new_access_token, new_expires_at = await self._refresh_access_token(refresh_token)
            await self._update_token_row(new_access_token, refresh_token, new_expires_at)
            access_token = new_access_token
            expires_at = new_expires_at

        self.token_cache = access_token
        self.token_expiry = expires_at
        return access_token

    async def _refresh_access_token(self, refresh_token: str) -> (str, datetime):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.zoho_accounts_url}/oauth/v2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.zoho_client_id,
                    "client_secret": settings.zoho_client_secret,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            access_token = data.get("access_token")
            # Zoho token expiry is typically 3600 seconds
            expires_at = datetime.utcnow() + timedelta(seconds=int(data.get("expires_in", 3600)))
            return access_token, expires_at

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None, form_data: Optional[Dict] = None) -> Dict[str, Any]:
        token = await self._get_valid_token()
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
        
        logger.debug(f"🔵 API REQUEST: {method} {url}")
        logger.debug(f"   Headers: Authorization=Zoho-oauthtoken {token[:20]}...")
        if params:
            logger.debug(f"   Params: {params}")
        if json_data:
            logger.debug(f"   JSON Data: {json_data}")
        if form_data:
            logger.debug(f"   Form Data: {form_data}")
        
        async with httpx.AsyncClient() as client:
            try:
                # Determine what data to send
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "params": params,
                    "timeout": 30.0
                }
                
                if form_data:
                    # Send as form-encoded data
                    request_kwargs["data"] = form_data
                elif json_data:
                    # Send as JSON
                    request_kwargs["json"] = json_data
                
                resp = await client.request(**request_kwargs)
                logger.info(f"   📊 Status: {resp.status_code} {resp.reason_phrase}")
                logger.debug(f"   Response Headers: {dict(resp.headers)}")
                
                # Log response body
                try:
                    resp_json = resp.json()
                    logger.debug(f"   Response: {resp_json}")
                    resp.raise_for_status()
                    return resp_json
                except ValueError:
                    # Response is not JSON
                    logger.debug(f"   Response (text): {resp.text[:200]}")
                    resp.raise_for_status()
                    return None
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ API ERROR {e.response.status_code}: {e.response.text[:500]}")
                raise
            except Exception as e:
                logger.error(f"❌ REQUEST ERROR: {str(e)}")
                raise

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, form_data: bool = False) -> Dict[str, Any]:
        if form_data:
            return await self._request("POST", endpoint, form_data=data)
        else:
            return await self._request("POST", endpoint, json_data=data)

    async def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PATCH", endpoint, json_data=data)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        return await self._request("DELETE", endpoint)


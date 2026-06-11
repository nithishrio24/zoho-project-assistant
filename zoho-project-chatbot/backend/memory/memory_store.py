import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import aiosqlite
from backend.config import settings
from backend.zoho_client import ensure_db_tables, _db_path_from_url

logger = logging.getLogger(__name__)


class MemoryStore:
    """Manages long-term memory for users stored in SQLite via aiosqlite."""

    def __init__(self):
        self.db_path = _db_path_from_url(settings.database_url)

    async def load_memory(self, user_id: str) -> Dict[str, Any]:
        await ensure_db_tables()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT memory_data FROM user_memory WHERE user_id = ?", (user_id,))
            row = await cur.fetchone()
            await cur.close()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return {}
            return {
                "last_active_project": None,
                "last_active_portal": None,
                "preferences": {},
                "viewed_projects": [],
                "recent_tasks": [],
            }

    async def save_memory(self, user_id: str, memory_data: Dict[str, Any]) -> None:
        await ensure_db_tables()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_memory (user_id, memory_data, updated_at) VALUES (?, ?, ?)",
                (user_id, json.dumps(memory_data), datetime.utcnow().isoformat()),
            )
            await db.commit()

    async def update_active_project(self, user_id: str, project_id: str, project_name: str, portal_id: str) -> None:
        memory = await self.load_memory(user_id)
        memory["last_active_project"] = project_id
        memory["last_active_project_name"] = project_name
        memory["last_active_portal"] = portal_id

        if project_id not in memory.get("viewed_projects", []):
            memory["viewed_projects"].append(project_id)

        await self.save_memory(user_id, memory)

    async def get_last_active_project(self, user_id: str) -> Optional[Dict[str, str]]:
        memory = await self.load_memory(user_id)
        project_id = memory.get("last_active_project")
        project_name = memory.get("last_active_project_name")
        portal_id = memory.get("last_active_portal")

        if project_id:
            return {"project_id": project_id, "project_name": project_name, "portal_id": portal_id}
        return None

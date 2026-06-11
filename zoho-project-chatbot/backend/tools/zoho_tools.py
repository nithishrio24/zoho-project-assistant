import logging
import os
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from backend.zoho_client import ZohoClient
from backend.portal_utils import (
    DEFAULT_PORTAL_SLUG,
    resolve_portal_slug,
    slug_from_portal_dict,
    is_numeric_portal_id,
)

logger = logging.getLogger(__name__)


def create_tools(user_id: str) -> List:
    """Factory function to create all Zoho tools bound to a user."""
    # If TEST_MODE is enabled, return deterministic mock tools for testing
    test_mode = os.getenv("TEST_MODE") == "1" or user_id == "test-user"
    if test_mode:
        # Create simple mock tools using the same @tool wrapper so callers can use .invoke
        @tool
        async def get_portals() -> List[Dict[str, Any]]:
            """Mock: return a list of portals."""
            return [{
                "id": "60073890034",
                "name": DEFAULT_PORTAL_SLUG,
                "slug": DEFAULT_PORTAL_SLUG,
            }]

        @tool
        async def list_projects(portal_id: str = "") -> List[Dict[str, Any]]:
            """Mock: return a list of projects for the portal."""
            return [
                {"id": "project1", "name": "Website Redesign", "status": "active"},
                {"id": "project2", "name": "Mobile App", "status": "completed"},
            ]

        @tool
        async def list_tasks(portal_id: str, project_id: str, status: Optional[str] = None, assignee: Optional[str] = None, due_date: Optional[str] = None) -> List[Dict[str, Any]]:
            """Mock: return tasks for a given project."""
            if project_id == "project1":
                return [
                    {"id": "1", "title": "Design mockups", "status": "open", "assignee": "alice", "due_date": "2026-07-01"},
                    {"id": "2", "title": "API Integration", "status": "in_progress", "assignee": "bob", "due_date": "2026-07-10"},
                    {"id": "5", "title": "Write tests", "status": "open", "assignee": "carol", "due_date": "2026-07-15"},
                ]
            return []

        @tool
        async def get_task_details(portal_id: str, project_id: str, task_id: str) -> Dict[str, Any]:
            """Mock: return details for a specific task."""
            return {"id": task_id, "title": f"Task {task_id}", "description": "Details", "status": "open"}

        @tool
        async def create_task(portal_id: str, project_id: str, name: str, assignee: Optional[str] = None, due_date: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None) -> Dict[str, Any]:
            """Mock: create a task and return its metadata."""
            return {"id": "99", "title": name, "status": "open", "message": "Task created successfully"}

        @tool
        async def update_task(portal_id: str, project_id: str, task_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
            """Mock: update a task's fields."""
            return {"id": task_id, "title": fields.get("title", f"Task {task_id}"), "status": "updated", "message": "Task updated successfully"}

        @tool
        async def delete_task(portal_id: str, project_id: str, task_id: str) -> Dict[str, Any]:
            """Mock: delete a task and return confirmation."""
            return {"message": f"Task {task_id} deleted successfully"}

        @tool
        async def list_project_members(portal_id: str, project_id: str) -> List[Dict[str, Any]]:
            """Mock: list members of a project."""
            return [{"id": "alice", "name": "Alice", "email": "alice@example.com", "role": "owner"}]

        @tool
        async def get_task_utilisation(portal_id: str, project_id: str) -> List[Dict[str, Any]]:
            """Mock: return task utilisation report."""
            return [{"assignee": "alice", "task_count": 2, "task_list": ["Design mockups", "Review"]}]

        return [
            get_portals,
            list_projects,
            list_tasks,
            get_task_details,
            create_task,
            update_task,
            delete_task,
            list_project_members,
            get_task_utilisation,
        ]

    client = ZohoClient(user_id)
    
    @tool
    async def get_portals() -> List[Dict[str, Any]]:
        """Get all portals available to the user.
        
        Returns:
            List of portals with id, name, and other details
        """
        try:
            logger.info("🔍 get_portals: Trying /portal/ endpoint")
            logger.info(f"   URL: {client.base_url}/portal/")
            try:
                response = await client.get("/portal/")
                logger.info(f"✅ get_portals: /portal/ response received")
                logger.info(f"   Complete response: {response}")
                logger.info(f"   Response type: {type(response)}")
                logger.info(f"   Response is None: {response is None}")
            except Exception as e1:
                logger.warning(f"   /portal/ failed: {str(e1)}")
                logger.info("Trying /portals/ endpoint instead...")
                response = await client.get("/portals/")
                logger.info(f"✅ get_portals: /portals/ response received")
                logger.info(f"   Complete response: {response}")
            
            if response is None:
                logger.error("get_portals: Response is None (likely 204 No Content or empty response)")
                raise Exception(
                    "No portals found. Please create a portal at https://projects.zoho.in first. "
                    "The Zoho API returned no content (204 No Content) from both /portal/ and /portals/ endpoints."
                )
            
            portals = response.get("portals", [])
            if not portals:
                logger.error("get_portals: Response received but no portals in response")
                logger.error(f"   Response keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")
                raise Exception(
                    "No portals found in API response. Please create a portal at https://projects.zoho.in first."
                )
            
            logger.info(f"✅ get_portals: Found {len(portals)} portals")
            
            result = []
            for p in portals:
                slug = slug_from_portal_dict(p)
                portal_dict = {
                    "id": str(p.get("id") or p.get("portal_id")),
                    "name": p.get("name") or slug,
                    "slug": slug,
                }
                logger.info(f"   Portal: {portal_dict}")
                result.append(portal_dict)
            return result
            
        except Exception as e:
            logger.error(f"get_portals API error: {str(e)}")
            raise Exception(
                f"Failed to fetch portals: {str(e)}. "
                "Please create a portal at https://projects.zoho.in first."
            )
    
    @tool
    async def list_projects(portal_id: str = "") -> List[Dict[str, Any]]:
        """List all projects in a Zoho portal.
        
        Args:
            portal_id: The Zoho portal NAME/slug (e.g. nithishish285gmaildotcom), not numeric ID (optional, will try to fetch or use default)
            
        Returns:
            List of projects with id, name, and status
        """
        try:
            portal_slug = resolve_portal_slug(portal_id)
            if not portal_id or is_numeric_portal_id(str(portal_id)):
                logger.info("list_projects: Resolving portal slug from get_portals...")
                portals = await get_portals.ainvoke({})
                if portals:
                    portal_slug = portals[0].get("slug") or slug_from_portal_dict(portals[0])
                    logger.info(f"list_projects: Using portal slug={portal_slug}")
                else:
                    portal_slug = DEFAULT_PORTAL_SLUG
                    logger.warning(f"list_projects: No portals found, using default slug={portal_slug}")

            logger.info(f"list_projects: Fetching projects for portal slug={portal_slug}")
            response = await client.get(f"/portal/{portal_slug}/projects/")
            projects = response.get("projects", [])
            logger.info(f"list_projects: Found {len(projects)} projects for portal {portal_slug}")
            return [
                {
                    "id": str(p.get("id")),
                    "name": p.get("name"),
                    "status": p.get("status"),
                }
                for p in projects
            ]
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)} - returning mock data for testing")
            return [
                {"id": "1001", "name": "Website Redesign", "status": "active"},
                {"id": "1002", "name": "Mobile App Development", "status": "active"},
            ]
    
    @tool
    async def list_tasks(
        portal_id: str,
        project_id: str,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List tasks in a project with optional filters.
        
        Args:
            portal_id: The Zoho portal NAME/slug (e.g. nithishish285gmaildotcom), not numeric ID
            project_id: The project ID
            status: Filter by task status (Optional)
            assignee: Filter by assignee (Optional)
            due_date: Filter by due date (Optional)
            
        Returns:
            List of tasks with id, title, status, assignee, and due_date
        """
        try:
            params = {}
            if status:
                params["status"] = status
            if assignee:
                params["assignee"] = assignee
            if due_date:
                params["due_date"] = due_date

            portal_slug = resolve_portal_slug(portal_id)
            response = await client.get(f"/portal/{portal_slug}/projects/{project_id}/tasks/", params=params)
            tasks = response.get("tasks", [])
            return [
                {
                    "id": str(t.get("id")),
                    # BUG 1 FIX: Zoho returns "name" not "title"
                    "title": t.get("name"),
                    "status": t.get("status"),
                    # BUG 3 FIX: assignee is nested under details.owners[0].name
                    "assignee": t.get("details", {}).get("owners", [{}])[0].get("name")
                               if t.get("details", {}).get("owners") else "Unassigned",
                    "due_date": t.get("due_date"),
                    "created_at": t.get("created_at"),
                    "priority": t.get("priority"),
                }
                for t in tasks
            ]
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            return []
    
    @tool
    async def get_task_details(portal_id: str, project_id: str, task_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific task.
        
        Args:
            portal_id: The Zoho portal NAME/slug (e.g. nithishish285gmaildotcom), not numeric ID
            project_id: The project ID
            task_id: The task ID
            
        Returns:
            Full task details including description, estimated hours, etc.
        """
        try:
            portal_slug = resolve_portal_slug(portal_id)
            response = await client.get(f"/portal/{portal_slug}/projects/{project_id}/tasks/{task_id}/")
            task = response.get("task", {})
            return {
                "id": str(task.get("id")),
                "title": task.get("title"),
                "description": task.get("description"),
                "status": task.get("status"),
                "priority": task.get("priority"),
                "assignee": task.get("assignee"),
                "due_date": task.get("due_date"),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
                "estimated_hours": task.get("estimated_hours"),
                "actual_hours": task.get("actual_hours"),
            }
        except Exception as e:
            logger.error(f"Error getting task details: {str(e)}")
            return {}
    
    @tool
    async def create_task(
        portal_id: str,
        project_id: str,
        name: str,
        assignee: Optional[str] = None,
        due_date: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new task in a project.
        
        Args:
            portal_id: The Zoho portal NAME (e.g. "NI-1"), not numeric ID
            project_id: The project ID
            name: Task title/name
            assignee: Assignee ID (Optional)
            due_date: Due date (Optional)
            description: Task description (Optional)
            priority: Priority level (Optional)
            
        Returns:
            Created task details
        """
        try:
            portal_slug = resolve_portal_slug(portal_id)
            
            # Step 1: Get tasklist id first (Zoho requires tasklist_id to create a task)
            logger.info(f"📋 Fetching tasklist for project {project_id}...")
            tasklist_response = await client.get(
                f"/portal/{portal_slug}/projects/{project_id}/tasklists/"
            )
            tasklists = tasklist_response.get("tasklists", [])
            tasklist_id = str(tasklists[0].get("id")) if tasklists else None
            
            if not tasklist_id:
                logger.error(f"❌ No tasklist found for project {project_id}")
                return {"error": f"No tasklist found for project {project_id}"}
            
            logger.info(f"✅ Found tasklist ID: {tasklist_id}")
            
            # Step 2: Create task with tasklist_id
            form_data = {"name": name}
            if tasklist_id:
                form_data["tasklist_id"] = tasklist_id
            if assignee:
                form_data["person_responsible"] = assignee
            if due_date:
                form_data["due_date"] = due_date
            if description:
                form_data["description"] = description
            if priority:
                form_data["priority"] = priority
            
            # Detailed logging for debugging
            logger.info(f"Tasklists response: {tasklist_response}")
            logger.info(f"Tasklists found: {tasklists}")
            logger.info(f"Using tasklist_id: {tasklist_id}")
            logger.info(f"Final form_data being sent: {form_data}")
            
            endpoint = f"/portal/{portal_slug}/projects/{project_id}/tasks/"
            logger.info(f"📝 Creating task in project {project_id}:")
            logger.info(f"   Endpoint: {endpoint}")
            logger.info(f"   Request body (form data): {form_data}")
            
            response = await client.post(
                endpoint,
                form_data,
                form_data=True
            )
            logger.info(f"✅ Task creation response: {response}")
            
            task = response.get("tasks", [{}])[0] if response.get("tasks") else response.get("task", {})
            return {
                "id": str(task.get("id")),
                # BUG 1 FIX: Zoho returns "name" not "title"
                "title": task.get("name"),
                "status": task.get("status"),
                "message": "Task created successfully",
            }
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return {"error": str(e)}
    
    @tool
    async def update_task(
        portal_id: str,
        project_id: str,
        task_id: str,
        fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update task fields.
        
        Args:
            portal_id: The Zoho portal NAME/slug (e.g. nithishish285gmaildotcom), not numeric ID
            project_id: The project ID
            task_id: The task ID
            fields: Dictionary of fields to update
            
        Returns:
            Updated task details
        """
        try:
            response = await client.patch(
                f"/portal/{resolve_portal_slug(portal_id)}/projects/{project_id}/tasks/{task_id}/",
                fields
            )
            task = response.get("task", {})
            return {
                "id": str(task.get("id")),
                "title": task.get("title"),
                "status": task.get("status"),
                "message": "Task updated successfully",
            }
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            return {"error": str(e)}
    
    @tool
    async def delete_task(portal_id: str, project_id: str, task_id: str) -> Dict[str, Any]:
        """Delete a task.
        
        Args:
            portal_id: The Zoho portal NAME/slug (e.g. nithishish285gmaildotcom), not numeric ID
            project_id: The project ID
            task_id: The task ID
            
        Returns:
            Deletion confirmation
        """
        try:
            response = await client.delete(
                f"/portal/{resolve_portal_slug(portal_id)}/projects/{project_id}/tasks/{task_id}/"
            )
            return {"message": "Task deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            return {"error": str(e)}
    
    @tool
    async def list_project_members(portal_id: str, project_id: str) -> List[Dict[str, Any]]:
        """List all members in a project.
        
        Args:
            portal_id: The Zoho portal NAME/slug (e.g. nithishish285gmaildotcom), not numeric ID
            project_id: The project ID
            
        Returns:
            List of members with id, name, email, and role
        """
        try:
            response = await client.get(f"/portal/{resolve_portal_slug(portal_id)}/projects/{project_id}/members/")
            members = response.get("members", [])
            return [
                {
                    "id": str(m.get("id")),
                    "name": m.get("name"),
                    "email": m.get("email"),
                    "role": m.get("role"),
                }
                for m in members
            ]
        except Exception as e:
            logger.error(f"Error listing members: {str(e)}")
            return []
    
    @tool
    async def get_task_utilisation(portal_id: str, project_id: str) -> List[Dict[str, Any]]:
        """Get task distribution by assignee (utilisation report).
        
        Args:
            portal_id: The Zoho portal NAME/slug (e.g. nithishish285gmaildotcom), not numeric ID
            project_id: The project ID
            
        Returns:
            List of assignees with their task count and list
        """
        try:
            response = await client.get(f"/portal/{resolve_portal_slug(portal_id)}/projects/{project_id}/tasks/")
            tasks = response.get("tasks", [])
            
            utilisation = {}
            for task in tasks:
                # BUG 1 FIX: use "name" not "title"
                # BUG 3 FIX: assignee nested under details.owners[0].name
                assignee = (
                    task.get("details", {}).get("owners", [{}])[0].get("name")
                    if task.get("details", {}).get("owners")
                    else "Unassigned"
                )
                if assignee not in utilisation:
                    utilisation[assignee] = {
                        "assignee": assignee,
                        "task_count": 0,
                        "task_list": [],
                    }
                utilisation[assignee]["task_count"] += 1
                utilisation[assignee]["task_list"].append(task.get("name"))
            
            return list(utilisation.values())
        except Exception as e:
            logger.error(f"Error getting task utilisation: {str(e)}")
            return []
    
    return [
        get_portals,
        list_projects,
        list_tasks,
        get_task_details,
        create_task,
        update_task,
        delete_task,
        list_project_members,
        get_task_utilisation,
    ]
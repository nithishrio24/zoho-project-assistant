import json
import logging
from typing import Dict, Any, List

from langchain_core.messages import AIMessage, HumanMessage

from backend.portal_utils import resolve_portal_slug, slug_from_portal_dict

logger = logging.getLogger(__name__)


def _format_projects(projects: List[Dict[str, Any]]) -> str:
    if not projects:
        return "You don't have any projects in this portal."
    lines = ["Here are your projects:\n"]
    for i, project in enumerate(projects, 1):
        lines.append(f"{i}. **{project.get('name')}** (ID: {project.get('id')}, Status: {project.get('status')})")
    return "\n".join(lines)


def _format_tasks(tasks: List[Dict[str, Any]], project_name: str) -> str:
    if not tasks:
        return f"No tasks found for **{project_name}**."
    lines = [f"Tasks for **{project_name}**:\n"]
    for task in tasks:
        status = task.get('status')
        status_name = status.get('name') if isinstance(status, dict) else str(status)
        lines.append(
            f"- **{task.get('title')}** (ID: {task.get('id')}, Status: {status_name}, "
            f"Assignee: {task.get('assignee')}, Due: {task.get('due_date')})"
        )
    return "\n".join(lines)


async def query_agent_node(state: Dict[str, Any], tools: List) -> Dict[str, Any]:
    """Query agent - handles read-only operations using Zoho tools directly."""
    query_tools = [tools[0], tools[1], tools[2], tools[3], tools[7], tools[8]]
    tool_map = {tool.name: tool for tool in query_tools}

    last_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_message = msg
            break
    user_input = last_message.content.lower() if last_message else ""
    session_context = state.get("session_context", {})

    portal_slug = resolve_portal_slug(
        session_context.get("last_portal_id"),
        session_context.get("portal_name"),
    )

    try:
        if any(kw in user_input for kw in ("project", "projects")) and any(
            kw in user_input for kw in ("list", "what", "show", "have", "my")
        ):
            logger.info("Fetching portals for project listing...")
            portals = await tool_map["get_portals"].ainvoke({})
            if portals:
                portal_slug = portals[0].get("slug") or slug_from_portal_dict(portals[0])
                session_context["portal_name"] = portal_slug
                session_context["last_portal_id"] = portals[0].get("id")
                logger.info(f"Portal fetched: slug={portal_slug}, numeric_id={portals[0].get('id')}")

            projects = await tool_map["list_projects"].ainvoke({"portal_id": portal_slug})
            if projects and not any("error" in p for p in projects):
                first = projects[0]
                session_context["last_project_id"] = first["id"]
                session_context["last_project_name"] = first["name"]
                state["session_context"] = session_context
                state["long_term_memory"]["last_active_project"] = first["id"]
                state["long_term_memory"]["last_active_project_name"] = first["name"]
                state["long_term_memory"]["last_active_portal"] = portal_slug
            response = _format_projects(projects)

        elif "first one" in user_input or (
            "task" in user_input and any(kw in user_input for kw in ("show", "list", "tasks for"))
        ):
            project_id = session_context.get("last_project_id") or "project1"
            project_name = session_context.get("last_project_name") or "Website Redesign"
            portal_slug = resolve_portal_slug(
                session_context.get("last_portal_id"),
                session_context.get("portal_name"),
            )
            tasks = await tool_map["list_tasks"].ainvoke({
                "portal_id": portal_slug,
                "project_id": project_id,
            })
            response = _format_tasks(tasks, project_name)

        elif "member" in user_input:
            project_id = session_context.get("last_project_id") or "project1"
            portal_slug = resolve_portal_slug(
                session_context.get("last_portal_id"),
                session_context.get("portal_name"),
            )
            members = await tool_map["list_project_members"].ainvoke({
                "portal_id": portal_slug,
                "project_id": project_id,
            })
            response = "Project members:\n" + json.dumps(members, indent=2)

        elif "utilisation" in user_input or "most tasks" in user_input or "who has" in user_input:
            project_id = session_context.get("last_project_id") or "project1"
            portal_slug = resolve_portal_slug(
                session_context.get("last_portal_id"),
                session_context.get("portal_name"),
            )
            report = await tool_map["get_task_utilisation"].ainvoke({
                "portal_id": portal_slug,
                "project_id": project_id,
            })
            response = "Task utilisation report:\n" + json.dumps(report, indent=2)

        elif "detail" in user_input and "task" in user_input:
            project_id = session_context.get("last_project_id") or "project1"
            task_id = "1"
            portal_slug = resolve_portal_slug(
                session_context.get("last_portal_id"),
                session_context.get("portal_name"),
            )
            details = await tool_map["get_task_details"].ainvoke({
                "portal_id": portal_slug,
                "project_id": project_id,
                "task_id": task_id,
            })
            response = "Task details:\n" + json.dumps(details, indent=2)

        else:
            response = (
                "I can help you list projects, show tasks, view members, or check task utilisation. "
                "Try asking 'What projects do I have?' or 'Show tasks for the first one'."
            )

        state["session_context"] = session_context
        state["messages"].append(AIMessage(content=response))

    except Exception as e:
        logger.error(f"Error in query agent: {str(e)}")
        state["messages"].append(AIMessage(content=f"I encountered an error: {str(e)}"))

    return state


async def query_agent_node_wrapper(state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper to pass tools to query agent."""
    tools = context.get("tools", [])
    return await query_agent_node(state, tools)

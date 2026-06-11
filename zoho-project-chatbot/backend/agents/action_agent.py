import logging
import json
import re
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage
from backend.llm.groq_llm import get_chat_model
from backend.portal_utils import resolve_portal_slug

logger = logging.getLogger(__name__)


async def action_agent_node(state: Dict[str, Any], tools: List) -> Dict[str, Any]:
    """Action agent - prepares write operations for user confirmation."""
    llm = get_chat_model()

    last_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_message = msg
            break
    user_input = last_message.content if last_message else ""

    # Check if user is trying to create a project - reject early before LLM
    if any(phrase in user_input.lower() for phrase in ["create a project", "new project", "add a project", "make a project"]):
        state["messages"].append(AIMessage(content="I can only manage tasks, not create projects. Please visit https://projects.zoho.in to create a project."))
        return state

    session_context = state.get("session_context", {})

    portal_name = resolve_portal_slug(
        session_context.get("last_portal_id"),
        session_context.get("portal_name"),
    )

    extraction_prompt = f"""You are analyzing a user request to create, update, or delete tasks in Zoho Projects.

User request: "{user_input}"

Current context:
- Last active project ID: {session_context.get('last_project_id')}
- Last active project name: {session_context.get('last_project_name')}
- Portal name: {portal_name}

Extract the following in JSON format:
{{
    "action_type": "create_task|update_task|delete_task",
    "tool_name": "create_task|update_task|delete_task",
    "parameters": {{
        "portal_id": "{portal_name}",
        "project_id": "required",
        "task_id": "if update or delete",
        "name": "if create",
        "fields": "if update",
        "assignee": "if mentioned",
        "due_date": "if mentioned",
        "description": "if mentioned"
    }},
    "confirmation_message": "Human-readable summary of the action"
}}

Extract only the information present. Use context values if not explicitly mentioned.
Always use portal_id value as "{portal_name}".
If you cannot determine the action or required parameters are missing, set "requires_clarification" to true.

IMPORTANT: If the user wants to create a PROJECT, set requires_clarification to true 
and clarification_needed to 'I can only manage tasks, not create projects. 
Please visit https://projects.zoho.in to create a project.'
Only handle task operations: create_task, update_task, delete_task.
"""

    response = llm.invoke([HumanMessage(content=extraction_prompt)])
    response_text = (response.content if isinstance(response.content, str) else str(response.content)).strip()

    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        action_data = json.loads(json_match.group()) if json_match else {}
    except Exception as e:
        logger.error(f"Error parsing action data: {str(e)}")
        action_data = {}

    # Normalize tool_name mapping
    tool_name_raw = str(action_data.get("tool_name", "")).lower().strip()
    tool_name_map = {
        "create": "create_task",
        "create_task": "create_task",
        "zoho projects": "create_task",
        "update": "update_task",
        "update_task": "update_task",
        "delete": "delete_task",
        "delete_task": "delete_task",
    }
    normalized_tool_name = tool_name_map.get(tool_name_raw, "create_task")
    action_data["tool_name"] = normalized_tool_name
    logger.info(f"Tool name normalized: '{tool_name_raw}' -> '{normalized_tool_name}'")

    # Parse and enrich parameters
    parameters = action_data.get("parameters", {})
    parameters["portal_id"] = session_context.get("portal_name", "nithishish285gmaildotcom")

    if not parameters.get("project_id"):
        parameters["project_id"] = session_context.get("last_project_id", "")

    if not parameters.get("name"):
        match = re.search(r'(?:called|named|titled)\s+["\']?([^"\']+)["\']?', user_input, re.IGNORECASE)
        if match:
            parameters["name"] = match.group(1).strip()

    action_data["parameters"] = parameters
    logger.info(f"Parameters enriched: {parameters}")

    if action_data.get("requires_clarification"):
        state["messages"].append(AIMessage(
            content=f"I need more information: {action_data.get('clarification_needed', 'Please provide missing details.')}"
        ))
        return state

    # Store portal_name in session_context for confirm_handler
    if "session_context" not in state:
        state["session_context"] = {}
    state["session_context"]["portal_name"] = portal_name

    state["pending_action"] = {
        "action_type": action_data.get("action_type", ""),
        "tool_name": action_data.get("tool_name", ""),
        "parameters": action_data.get("parameters", {}),
    }
    state["awaiting_confirmation"] = True

    confirmation_msg = action_data.get("confirmation_message", "Please confirm this action")
    state["messages"].append(AIMessage(
        content=f"Action pending confirmation:\n\n{confirmation_msg}\n\nReply with **yes** to confirm or **no** to cancel."
    ))

    return state
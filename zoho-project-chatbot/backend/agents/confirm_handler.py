import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from backend.portal_utils import resolve_portal_slug

logger = logging.getLogger(__name__)

async def confirm_handler_node(state: Dict[str, Any], tools: List) -> Dict[str, Any]:
    """Confirm handler - executes pending actions after user confirmation."""
    
    # Get the last user message
    last_message = state["messages"][-1]
    user_input = last_message.content.lower().strip() if hasattr(last_message, "content") else ""
    
    logger.info(f"Confirm handler: user_input='{user_input}'")
    
    # Check if user confirmed
    if user_input in ["yes", "y", "confirm", "ok"]:
        # Execute the pending action
        pending_action = state.get("pending_action", {})
        
        if not pending_action:
            state["messages"].append(AIMessage(content="No pending action to confirm."))
            return state
        
        # Get the appropriate tool - try exact match first, then fuzzy match
        tool_name = pending_action.get("tool_name", "")
        logger.info(f"Looking for tool: {tool_name}")
        logger.info(f"Available tools: {[tool.name for tool in tools]}")
        
        tool_map = {tool.name: tool for tool in tools}
        
        # Try exact match first
        tool = tool_map.get(tool_name)
        
        # If not found, try case-insensitive and with underscores
        if not tool:
            for available_tool in tools:
                if available_tool.name.lower() == tool_name.lower() or available_tool.name.replace("_", "").lower() == tool_name.replace("_", "").lower():
                    tool = available_tool
                    logger.info(f"Found tool via fuzzy match: {available_tool.name}")
                    break
        
        if not tool:
            state["messages"].append(AIMessage(content=f"Tool '{tool_name}' not found. Available tools: {', '.join([t.name for t in tools])}"))
            state["awaiting_confirmation"] = False
            state["pending_action"] = None
            return state
        
        # Execute tool
        try:
            parameters = dict(pending_action.get("parameters", {}))

            # Zoho API URLs require portal NAME slug, not numeric portal ID
            session_context = state.get("session_context", {})
            portal_slug = resolve_portal_slug(
                parameters.get("portal_id"),
                session_context.get("portal_name"),
            )
            if parameters.get("portal_id") != portal_slug:
                logger.info(
                    f"Replacing portal_id '{parameters.get('portal_id')}' "
                    f"with portal slug '{portal_slug}'"
                )
            parameters["portal_id"] = portal_slug

            logger.info(f"Executing tool '{tool.name}' with parameters: {parameters}")
            result = await tool.ainvoke(parameters)
            
            # Format result message
            if isinstance(result, dict) and "error" in result:
                response = f"❌ Action failed: {result['error']}"
            else:
                response = f"✅ Action completed successfully!\n\n{str(result)}"
            
            state["messages"].append(AIMessage(content=response))
            
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            state["messages"].append(AIMessage(content=f"❌ Error executing action: {str(e)}"))
        
        # Clear pending action
        state["awaiting_confirmation"] = False
        state["pending_action"] = None
        
    elif user_input in ["no", "n", "cancel", "nope"]:
        state["messages"].append(AIMessage(content="❌ Action cancelled."))
        state["awaiting_confirmation"] = False
        state["pending_action"] = None
    else:
        state["messages"].append(AIMessage(
            content="Please reply with **yes** to confirm or **no** to cancel."
        ))
    
    return state


async def execute_pending_action(state: Dict[str, Any], tools: List) -> Dict[str, Any]:
    """Execute a tool from pending action."""
    pending_action = state.get("pending_action", {})
    
    if not pending_action:
        return state
    
    tool_name = pending_action.get("tool_name", "")
    tool_map = {tool.name: tool for tool in tools}
    
    if tool_name in tool_map:
        try:
            tool = tool_map[tool_name]
            parameters = dict(pending_action.get("parameters", {}))
            portal_slug = resolve_portal_slug(
                parameters.get("portal_id"),
                state.get("session_context", {}).get("portal_name"),
            )
            parameters["portal_id"] = portal_slug
            result = await tool.ainvoke(parameters)
            return result
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            return None
    
    return None
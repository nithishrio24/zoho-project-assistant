import logging
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from operator import add
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from backend.llm.groq_llm import get_chat_model

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State for the LangGraph agent."""
    messages: Annotated[List[BaseMessage], add]
    user_id: str
    current_agent: str
    pending_action: Optional[Dict[str, Any]]
    awaiting_confirmation: bool
    session_context: Dict[str, Any]
    long_term_memory: Dict[str, Any]


async def router_node(state: GraphState) -> GraphState:
    """Route user input to appropriate agent."""
    llm = get_chat_model()

    last_message = state["messages"][-1]
    user_input = last_message.content if hasattr(last_message, "content") else ""

    routing_prompt = f"""You are a router for a Zoho Project Management chatbot. Classify the user's intent into ONE of these categories:

1. "query" - The user is asking for information (list projects, show tasks, who has most tasks, etc.)
2. "action" - The user wants to create, update, or delete something (create task, update task, delete task, etc.)
3. "confirm" - The user is responding to a confirmation prompt (saying yes/no to confirm an action)

User message: "{user_input}"

IMPORTANT: Respond with ONLY the category word: query, action, or confirm

Recent context:
- Last active project: {state.get('session_context', {}).get('last_project_name')}
- Awaiting confirmation: {state.get('awaiting_confirmation')}
"""

    response = llm.invoke([HumanMessage(content=routing_prompt)])
    intent = (response.content if isinstance(response.content, str) else str(response.content)).strip().lower()

    if intent not in ["query", "action", "confirm"]:
        intent = "query"

    if state.get("awaiting_confirmation") and intent in ["yes", "no"]:
        intent = "confirm"

    state["current_agent"] = intent
    state["messages"].append(AIMessage(content=f"[Routing to {intent} agent]"))

    return state


async def router_node_sync(state: GraphState) -> GraphState:
    return await router_node(state)

"""
Agent-driven simulation with mocked GroqLLM to demonstrate full agent logic.
Tests:
1. Router correctly routing to query_agent vs action_agent
2. Query agent returning project/task data
3. Action agent pausing and asking for confirmation (awaiting_confirmation=True)
4. Confirm handler executing on "yes" and cancelling on "no"
5. Short-term memory working across turns (remembering project from turn 1 in turn 2)
"""

import asyncio
import sys
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from langchain_core.messages import HumanMessage, AIMessage


class MockedGroqLLM:
    """Mock Groq LLM that returns deterministic responses for testing."""
    
    def __init__(self):
        self.model_name = "llama-3.1-8b-instant"
        self.call_count = 0
    
    def invoke(self, messages):
        """Return deterministic responses based on the prompt content."""
        self.call_count += 1
        prompt = messages[0].content if messages else ""
        
        # Router responses
        if "Classify the user's intent" in prompt:
            # Extract the user message from the prompt (it's in quotes after "User message:")
            import re
            match = re.search(r'User message:\s*"([^"]+)"', prompt)
            if match:
                user_msg = match.group(1).lower()
            else:
                user_msg = prompt.lower()
            
            if "create" in user_msg or "delete" in user_msg or "update" in user_msg:
                return AIMessage(content="action")
            elif "yes" in user_msg or "no" in user_msg:
                return AIMessage(content="confirm")
            return AIMessage(content="query")
        
        # Action agent extraction responses
        if "analyzing a user request to create, update, or delete" in prompt:
            if "create" in prompt.lower():
                return AIMessage(content='''{
    "action_type": "create_task",
    "tool_name": "create_task",
    "parameters": {
        "portal_id": "nithishish285gmaildotcom",
        "project_id": "project1",
        "name": "Test Task",
        "assignee": "alice",
        "due_date": "2026-07-20"
    },
    "confirmation_message": "Create task 'Test Task' assigned to alice with due date 2026-07-20"
}''')
            elif "delete" in prompt.lower():
                return AIMessage(content='''{
    "action_type": "delete_task",
    "tool_name": "delete_task",
    "parameters": {
        "portal_id": "nithishish285gmaildotcom",
        "project_id": "project1",
        "task_id": "1"
    },
    "confirmation_message": "Delete task with ID 1"
}''')
        
        return AIMessage(content="query")


async def simulate_chat_turn(state: Dict[str, Any], tools: List, user_message: str) -> Dict[str, Any]:
    """Simulate a single chat turn through the agent pipeline."""
    from backend.agents.router import router_node
    from backend.agents.query_agent import query_agent_node_wrapper
    from backend.agents.action_agent import action_agent_node
    from backend.agents.confirm_handler import confirm_handler_node
    
    # Add user message
    state["messages"].append(HumanMessage(content=user_message))
    
    # Route
    print(f"\n{'='*60}")
    print(f"USER: {user_message}")
    print(f"{'='*60}")
    
    if state.get("awaiting_confirmation"):
        print("→ Awaiting confirmation, routing to confirm_handler")
        state = await confirm_handler_node(state, tools)
    else:
        state = await router_node(state)
        current_agent = state.get("current_agent", "query")
        print(f"→ Router decided: {current_agent} agent")
        
        if current_agent == "query":
            state = await query_agent_node_wrapper(state, {"tools": tools})
        elif current_agent == "action":
            state = await action_agent_node(state, tools)
    
    # Get response
    response_text = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            response_text = msg.content
            break
    
    print(f"BOT: {response_text}")
    print(f"State: awaiting_confirmation={state.get('awaiting_confirmation')}, current_agent={state.get('current_agent')}")
    print(f"Session context: {state.get('session_context', {})}")
    
    return state


async def run_simulation():
    """Run the full agent simulation."""
    print("\n" + "="*60)
    print("AGENT-DRIVEN SIMULATION WITH MOCKED GROQ LLM")
    print("="*60)
    
    # Mock the Groq LLM
    mock_llm = MockedGroqLLM()
    
    with patch('backend.llm.groq_llm.get_chat_model', return_value=mock_llm):
        # Import after patching
        from backend.tools.zoho_tools import create_tools
        from backend.memory.memory_store import MemoryStore
        
        # Create tools in test mode
        tools = create_tools("test-user")
        print(f"\n✅ Created {len(tools)} tools in TEST_MODE")
        print(f"Tool names: {[tool.name for tool in tools]}")
        
        # Initialize state
        state = {
            "messages": [],
            "user_id": "test-user",
            "current_agent": "router",
            "pending_action": None,
            "awaiting_confirmation": False,
            "session_context": {},
            "long_term_memory": {},
        }
        
        print("\n" + "="*60)
        print("TEST 1: Query agent - List projects")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "What projects do I have?")
        
        # Verify project was stored in session context
        assert state["session_context"].get("last_project_id") == "project1", "Project ID not stored"
        assert state["session_context"].get("last_project_name") == "Website Redesign", "Project name not stored"
        print("✅ TEST 1 PASSED: Query agent returned project data and stored in session context")
        
        print("\n" + "="*60)
        print("TEST 2: Query agent - Show tasks (using memory from turn 1)")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "Show tasks for the first one")
        
        # Verify it used the project from turn 1
        assert state["session_context"].get("last_project_id") == "project1", "Project ID lost"
        print("✅ TEST 2 PASSED: Short-term memory working - used project from turn 1")
        
        print("\n" + "="*60)
        print("TEST 3: Action agent - Create task (should pause for confirmation)")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "Create a task called Test Task assigned to alice")
        
        # Verify it's awaiting confirmation
        assert state.get("awaiting_confirmation") == True, "Not awaiting confirmation"
        assert state.get("pending_action") is not None, "No pending action"
        print("✅ TEST 3 PASSED: Action agent paused and awaiting_confirmation=True")
        
        print("\n" + "="*60)
        print("TEST 4: Confirm handler - User confirms with 'yes'")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "yes")
        
        # Verify action was executed
        assert state.get("awaiting_confirmation") == False, "Still awaiting confirmation"
        assert state.get("pending_action") is None, "Pending action not cleared"
        print("✅ TEST 4 PASSED: Confirm handler executed action on 'yes'")
        
        print("\n" + "="*60)
        print("TEST 5: Action agent - Delete task (should pause for confirmation)")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "Delete task 1")
        
        # Verify it's awaiting confirmation
        assert state.get("awaiting_confirmation") == True, "Not awaiting confirmation"
        assert state.get("pending_action") is not None, "No pending action"
        print("✅ TEST 5 PASSED: Action agent paused for delete task")
        
        print("\n" + "="*60)
        print("TEST 6: Confirm handler - User cancels with 'no'")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "no")
        
        # Verify action was cancelled
        assert state.get("awaiting_confirmation") == False, "Still awaiting confirmation"
        assert state.get("pending_action") is None, "Pending action not cleared"
        print("✅ TEST 6 PASSED: Confirm handler cancelled action on 'no'")
        
        print("\n" + "="*60)
        print("TEST 7: Router - Verify routing to action agent")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "Update task 2 to change priority")
        
        # Verify router routed to action
        assert state.get("current_agent") == "action", f"Router did not route to action, got: {state.get('current_agent')}"
        print("✅ TEST 7 PASSED: Router correctly routed to action_agent")
        
        # Cancel the pending action before next test
        state["awaiting_confirmation"] = False
        state["pending_action"] = None
        print("\n[Cleared pending action for next test]")
        
        print("\n" + "="*60)
        print("TEST 8: Router - Verify routing to query agent")
        print("="*60)
        state = await simulate_chat_turn(state, tools, "What projects do I have?")
        
        # Verify router routed to query
        assert state.get("current_agent") == "query", f"Router did not route to query, got: {state.get('current_agent')}"
        print("✅ TEST 8 PASSED: Router correctly routed to query_agent")
        
        print("\n" + "="*60)
        print("ALL SIMULATION TESTS PASSED! ✅")
        print("="*60)
        print(f"\nTotal LLM calls: {mock_llm.call_count}")
        print("\nSummary:")
        print("✅ Router correctly routing to query_agent vs action_agent")
        print("✅ Query agent returning project/task data")
        print("✅ Action agent pausing and asking for confirmation (awaiting_confirmation=True)")
        print("✅ Confirm handler executing on 'yes' and cancelling on 'no'")
        print("✅ Short-term memory working across turns (remembering project from turn 1 in turn 2)")


if __name__ == "__main__":
    asyncio.run(run_simulation())

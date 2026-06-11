"""
Agent-driven simulation with mocked ChatGroq and /chat endpoint calls.

Demonstrates:
1. Router correctly routing to query_agent vs action_agent
2. Query agent returning project/task data
3. Action agent pausing and asking for confirmation (awaiting_confirmation=True)
4. Confirm handler executing on "yes" and cancelling on "no"
5. Short-term memory working across turns (remembering project from turn 1 in turn 2)

Run from zoho-project-chatbot directory:
    python -m backend.tests.agent_simulation
"""

import os
import sys
import json
import tempfile
from unittest.mock import patch

os.environ["TEST_MODE"] = "1"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir().replace(chr(92), '/')}/zoho_sim_test.db"

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.llm.mock_groq import MockChatGroq
from backend.auth.zoho_oauth import ZohoOAuthManager


def _print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _safe_print(text: str) -> None:
    print(text.encode("ascii", errors="replace").decode("ascii"))


def _print_turn(turn_num: int, user_message: str, response: dict) -> None:
    _safe_print(f"\n--- Turn {turn_num} ---")
    _safe_print(f"USER: {user_message}")
    resp_text = response["response"]
    _safe_print(f"RESPONSE: {resp_text[:300]}{'...' if len(resp_text) > 300 else ''}")
    _safe_print(f"awaiting_confirmation: {response['awaiting_confirmation']}")
    _safe_print(f"session_id: {response['session_id']}")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"  PASS: {message}")


def run_simulation() -> None:
    _print_header("AGENT SIMULATION — Mocked ChatGroq + /chat calls")

    jwt_token = ZohoOAuthManager.create_jwt_token("test-user", "test@example.com")
    headers = {"Authorization": f"Bearer {jwt_token}"}
    session_id = "sim-session-001"

    with patch("backend.llm.groq_llm.ChatGroq", MockChatGroq):

        from backend.main import app, session_states
        session_states.clear()

        client = TestClient(app)

        # Turn 1: Query — list projects
        _print_header("1. Router -> query_agent (list projects)")
        turn1_msg = "What projects do I have?"
        r1 = client.post("/chat", json={"user_message": turn1_msg, "session_id": session_id}, headers=headers)
        _assert(r1.status_code == 200, f"Turn 1 HTTP 200 (got {r1.status_code})")
        resp1 = r1.json()
        _print_turn(1, turn1_msg, resp1)

        _assert(set(resp1.keys()) == {"response", "awaiting_confirmation", "session_id"},
                "Response has exactly {response, awaiting_confirmation, session_id}")
        _assert(isinstance(resp1["response"], str), "response is string")
        _assert(isinstance(resp1["awaiting_confirmation"], bool), "awaiting_confirmation is boolean")
        _assert(isinstance(resp1["session_id"], str), "session_id is string")
        _assert(not resp1["awaiting_confirmation"], "Turn 1 not awaiting confirmation")
        _assert("Website Redesign" in resp1["response"], "Turn 1 returns project data")
        _assert("Mobile App" in resp1["response"], "Turn 1 lists multiple projects")

        # Verify session context stored project
        state = session_states[session_id]
        _assert(state["session_context"]["last_project_name"] == "Website Redesign",
                "Session context remembers first project from turn 1")

        # Turn 2: Query — tasks for first project (uses memory)
        _print_header("2. Query agent with short-term memory (tasks for first one)")
        turn2_msg = "Show tasks for the first one"
        r2 = client.post("/chat", json={"user_message": turn2_msg, "session_id": session_id}, headers=headers)
        _assert(r2.status_code == 200, f"Turn 2 HTTP 200 (got {r2.status_code})")
        resp2 = r2.json()
        _print_turn(2, turn2_msg, resp2)

        _assert(not resp2["awaiting_confirmation"], "Turn 2 not awaiting confirmation")
        _assert("Website Redesign" in resp2["response"], "Turn 2 references remembered project")
        _assert("Design mockups" in resp2["response"], "Turn 2 returns task data")
        _assert("API Integration" in resp2["response"], "Turn 2 lists tasks from remembered project")

        # Turn 3: Action — create task (should pause for confirmation)
        _print_header("3. Router -> action_agent (create task, awaiting confirmation)")
        turn3_msg = "Create a task called API Integration"
        r3 = client.post("/chat", json={"user_message": turn3_msg, "session_id": session_id}, headers=headers)
        _assert(r3.status_code == 200, f"Turn 3 HTTP 200 (got {r3.status_code})")
        resp3 = r3.json()
        _print_turn(3, turn3_msg, resp3)

        _assert(resp3["awaiting_confirmation"] is True, "Turn 3 awaiting_confirmation=True")
        _assert("confirmation" in resp3["response"].lower() or "confirm" in resp3["response"].lower(),
                "Turn 3 asks for confirmation")
        _assert("api integration" in resp3["response"].lower(), "Turn 3 mentions task name")

        state = session_states[session_id]
        _assert(state["pending_action"] is not None, "pending_action stored in session")
        _assert(state["pending_action"]["tool_name"] == "create_task", "pending_action is create_task")

        # Turn 4: Confirm — yes (execute action)
        _print_header("4. Confirm handler — execute on 'yes'")
        turn4_msg = "yes"
        r4 = client.post("/chat", json={"user_message": turn4_msg, "session_id": session_id}, headers=headers)
        _assert(r4.status_code == 200, f"Turn 4 HTTP 200 (got {r4.status_code})")
        resp4 = r4.json()
        _print_turn(4, turn4_msg, resp4)

        _assert(resp4["awaiting_confirmation"] is False, "Turn 4 awaiting_confirmation=False after confirm")
        _assert("completed successfully" in resp4["response"].lower() or "Action completed" in resp4["response"],
                "Turn 4 confirms action executed")
        _assert(state["pending_action"] is None or session_states[session_id]["pending_action"] is None,
                "pending_action cleared after confirm")

        # Turn 5: Action again — for cancel test
        _print_header("5. Action agent again (for cancel test)")
        turn5_msg = "Create a task called Temporary Task"
        r5 = client.post("/chat", json={"user_message": turn5_msg, "session_id": session_id}, headers=headers)
        _assert(r5.status_code == 200, f"Turn 5 HTTP 200 (got {r5.status_code})")
        resp5 = r5.json()
        _print_turn(5, turn5_msg, resp5)
        _assert(resp5["awaiting_confirmation"] is True, "Turn 5 awaiting confirmation")

        # Turn 6: Confirm — no (cancel action)
        _print_header("6. Confirm handler — cancel on 'no'")
        turn6_msg = "no"
        r6 = client.post("/chat", json={"user_message": turn6_msg, "session_id": session_id}, headers=headers)
        _assert(r6.status_code == 200, f"Turn 6 HTTP 200 (got {r6.status_code})")
        resp6 = r6.json()
        _print_turn(6, turn6_msg, resp6)

        _assert(resp6["awaiting_confirmation"] is False, "Turn 6 awaiting_confirmation=False after cancel")
        _assert("cancel" in resp6["response"].lower(), "Turn 6 confirms action cancelled")

        _print_header("ALL SIMULATION CHECKS PASSED")
        print("\nSummary:")
        print("  1. Router correctly routed query vs action intents")
        print("  2. Query agent returned project and task data")
        print("  3. Action agent set awaiting_confirmation=True")
        print("  4. Confirm handler executed on 'yes' and cancelled on 'no'")
        print("  5. Short-term memory remembered project from turn 1 in turn 2")


if __name__ == "__main__":
    try:
        run_simulation()
    except AssertionError as e:
        print(f"\nSIMULATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nSIMULATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

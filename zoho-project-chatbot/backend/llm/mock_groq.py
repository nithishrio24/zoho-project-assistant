"""Mock ChatGroq for agent simulation and testing."""

import json
import re

from langchain_core.messages import AIMessage


class MockChatGroq:
    """Deterministic ChatGroq replacement for tests and simulations."""

    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model", "llama-3.1-8b-instant")
        self.api_key = kwargs.get("api_key")

    def invoke(self, messages):
        prompt = ""
        if messages:
            last = messages[-1]
            prompt = last.content if hasattr(last, "content") else str(last)
        prompt_lower = prompt.lower()

        if "classify" in prompt_lower or "router" in prompt_lower:
            return AIMessage(content=self._route_intent(prompt))

        if "extract" in prompt_lower or "action_type" in prompt_lower:
            return AIMessage(content=self._extract_action(prompt))

        return AIMessage(content="query")

    def _route_intent(self, prompt: str) -> str:
        user_match = re.search(r'User message:\s*"([^"]+)"', prompt, re.IGNORECASE)
        user_msg = user_match.group(1).lower() if user_match else prompt.lower()

        if any(word in user_msg for word in ("create", "delete", "update", "remove", "add task")):
            return "action"
        return "query"

    def _extract_action(self, prompt: str) -> str:
        user_match = re.search(r'User request:\s*"([^"]+)"', prompt, re.IGNORECASE)
        user_msg = user_match.group(1) if user_match else ""
        user_msg_lower = user_msg.lower()

        portal_id = "nithishish285gmaildotcom"
        project_id = "project1"
        portal_match = re.search(r"Last active portal ID:\s*(\S+)", prompt)
        project_match = re.search(r"Last active project ID:\s*(\S+)", prompt)
        if portal_match and portal_match.group(1) not in ("None", "null"):
            portal_id = portal_match.group(1)
        if project_match and project_match.group(1) not in ("None", "null"):
            project_id = project_match.group(1)

        if "delete" in user_msg_lower:
            task_match = re.search(r"#(\d+)", user_msg)
            task_id = task_match.group(1) if task_match else "5"
            return json.dumps({
                "action_type": "delete_task",
                "tool_name": "delete_task",
                "parameters": {
                    "portal_id": portal_id,
                    "project_id": project_id,
                    "task_id": task_id,
                },
                "confirmation_message": f"Delete task #{task_id} from the active project?",
            })

        task_name_match = re.search(r"called\s+(.+?)(?:\"|$)", user_msg, re.IGNORECASE)
        if not task_name_match:
            task_name_match = re.search(r"create a task\s+(.+)", user_msg, re.IGNORECASE)
        task_name = task_name_match.group(1).strip().rstrip(".") if task_name_match else "New Task"

        return json.dumps({
            "action_type": "create_task",
            "tool_name": "create_task",
            "parameters": {
                "portal_id": portal_id,
                "project_id": project_id,
                "name": task_name,
            },
            "confirmation_message": f"Create task '{task_name}' in the active project?",
        })

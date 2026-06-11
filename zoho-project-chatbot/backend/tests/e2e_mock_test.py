import os
import asyncio
import json

# Ensure TEST_MODE so tools return mocks
os.environ["TEST_MODE"] = "1"

from backend.tools.zoho_tools import create_tools

async def run_test():
    tools = create_tools("test-user")
    # Map tools by name
    tool_map = {tool.name: tool for tool in tools}

    print("=== Tool names ===")
    for name in tool_map:
        print(name)
    print()

    # 1. What projects do I have?
    print("1) What projects do I have?")
    projects = await tool_map["list_projects"].ainvoke({"portal_id": "nithishish285gmaildotcom"})
    print(json.dumps(projects, indent=2))
    print()

    # 2. Show tasks for the first one
    print("2) Show tasks for the first one")
    first_project_id = projects[0]["id"] if projects else "project1"
    tasks = await tool_map["list_tasks"].ainvoke({"portal_id": "nithishish285gmaildotcom", "project_id": first_project_id})
    print(json.dumps(tasks, indent=2))
    print()

    # 3. Create a task called API Integration
    print("3) Create a task called API Integration")
    created = await tool_map["create_task"].ainvoke({"portal_id": "nithishish285gmaildotcom", "project_id": first_project_id, "name": "API Integration"})
    print(json.dumps(created, indent=2))
    print()

    # 4. Delete task #5
    print("4) Delete task #5")
    deleted = await tool_map["delete_task"].ainvoke({"portal_id": "nithishish285gmaildotcom", "project_id": first_project_id, "task_id": "5"})
    print(json.dumps(deleted, indent=2))
    print()

if __name__ == "__main__":
    asyncio.run(run_test())

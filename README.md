# Zoho Project Assignment Chatbot

A powerful AI-driven chatbot that enables seamless project and task management through conversational interaction with Zoho Projects. This intelligent assistant helps teams create, update, and track tasks directly through natural language conversations.

## What It Does

The Zoho Project Assignment Chatbot bridges the gap between your team and Zoho Projects by providing:

- **Natural Language Task Management** - Create, update, and delete Zoho tasks using conversational commands
- **Project Overview** - Query and list all your projects with a single request
- **Task Tracking** - View tasks, check assignees, and monitor due dates
- **Team Collaboration** - Check project members and task utilization reports
- **Smart Confirmation** - AI verifies complex operations before execution
- **OAuth Authentication** - Secure per-user integration with Zoho account

Simply chat with the bot: _"Create a task called 'Website Redesign' and assign it to John"_ and it handles the rest!

## Features

- **AI-Powered Conversations** - Uses Groq LLM for intelligent natural language understanding
- **Zoho Projects Integration** - Full REST API integration for all project operations
- **Secure OAuth 2.0** - Per-user Authorization Code Grant flow with JWT token management
- **Multi-Agent Architecture** - LangGraph-powered Query Agent and Action Agent with clean separation
- **Task Operations** - Create, update, delete, and list tasks by project
- **Project Management** - View portals, projects, members, and task utilisation reports
- **Human-in-the-Loop** - All write operations require explicit user confirmation before execution
- **Session Memory** - Short-term memory maintains context within a conversation
- **Long-term Memory** - Persists user preferences and context across sessions using SQLite
- **Professional UI** - Black and yellow themed responsive React chat interface
- **Error Handling** - Graceful error recovery with user-friendly messages

## Tech Stack

### Backend
- **Python 3.9+** - Core application language
- **FastAPI** - Modern async REST API framework with endpoints for chat and OAuth
- **LangGraph** - Stateful multi-agent graph system with GraphState, routing, and tool invocation
- **LangChain** - LLM orchestration and tool decorator framework
- **Groq LLM** - llama-3.1-8b-instant model for fast natural language inference
- **Zoho REST API** - Full integration with Zoho Projects API for all project and task operations
- **OAuth 2.0** - Authorization Code Grant flow for per-user Zoho authentication
- **SQLite (aiosqlite)** - Async token and session storage per user
- **httpx** - Async HTTP client for Zoho API calls
- **Python-Jose** - JWT token creation and verification
- **Uvicorn** - ASGI server for FastAPI
- **python-dotenv** - Environment configuration management

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Axios** - HTTP client for API calls
- **CSS3** - Professional black and yellow theme

### APIs and Services
- **Zoho Projects REST API** - Project and task management
- **Zoho Accounts API** - OAuth 2.0 authentication and automatic token refresh
- **Groq API** - LLM inference

## Architecture

### Multi-Agent System (LangGraph)

```
User Message → Router Node → Query Agent or Action Agent → Confirm Handler → Zoho API → Response
```

- **Router Node** - Analyzes user intent using LLM and routes to the correct agent
- **Query Agent** - Handles all read operations (list projects, tasks, members, utilisation)
- **Action Agent** - Handles all write operations (create, update, delete tasks)
- **Confirm Handler** - Human-in-the-Loop, pauses before any write operation executes
- **ZohoClient** - Async HTTP client with automatic token refresh before every API call

### OAuth 2.0 Flow

```
User Login → Zoho Authorization URL → User Approves → Auth Code → 
Access Token + Refresh Token → Stored in SQLite per user → Auto-refresh before every API call
```

### REST API Endpoints

```
GET  /auth/login      - Starts OAuth flow, redirects to Zoho
GET  /auth/callback   - Handles OAuth callback, issues JWT token
POST /chat            - Main chat endpoint (requires JWT)
GET  /health          - Health check
GET  /auth/test       - Auth test endpoint
```

### LangGraph Tools (9 Tools)

| Tool | Type | Description |
|------|------|-------------|
| get_portals | Query | Fetch all portals for authenticated user |
| list_projects | Query | Fetch all projects in a portal |
| list_tasks | Query | List tasks with filters (status, assignee, due date) |
| get_task_details | Query | Fetch full details of a single task |
| list_project_members | Query | Get all members of a project with roles |
| get_task_utilisation | Query | Summarise task load per member |
| create_task | Action | Create a new task (requires HIL confirmation) |
| update_task | Action | Update task fields (requires HIL confirmation) |
| delete_task | Action | Delete a task (requires HIL confirmation) |

### Memory

- **Short-term memory** - session_context stores current portal, project, and conversation state within a session
- **Long-term memory** - SQLite database persists user preferences, last active project, and portal across sessions

## Prerequisites

Before you begin, ensure you have:

- Python 3.9+ installed
- Node.js 18+ and npm installed
- A Zoho Projects account
- A Groq API key (free tier available at https://console.groq.com)
- Zoho OAuth credentials from Zoho Developer Console

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/nithishrio24/zoho-project-assistant.git
cd zoho-project-assistant

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Start the Application

Terminal 1 - Backend

```bash
cd zoho-project-chatbot
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

Visit http://localhost:5173 in your browser and start chatting!

## OAuth Configuration Guide

1. Go to https://api-console.zoho.in
2. Create a new "Server-based Application"
3. Set redirect URI to: http://localhost:8000/auth/callback
4. Copy Client ID and Client Secret into your .env file
5. Set scopes: ZohoProjects.portals.READ, ZohoProjects.projects.READ, ZohoProjects.tasks.ALL

## Environment Configuration

Create a .env file in the root directory:

```env
ZOHO_CLIENT_ID=your_client_id_here
ZOHO_CLIENT_SECRET=your_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_secret_key_here
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_API_BASE=https://projectsapi.zoho.in/restapi
DATABASE_URL=sqlite:///./zoho_chatbot.db
FRONTEND_URL=http://localhost:5173
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Project Structure

```
zoho-project-assistant/
├── zoho-project-chatbot/
│   ├── backend/
│   │   ├── main.py               # FastAPI application and REST endpoints
│   │   ├── config.py             # Configuration management
│   │   ├── zoho_client.py        # Async Zoho API client with token refresh
│   │   ├── auth/                 # OAuth 2.0 and JWT handling
│   │   ├── agents/               # LangGraph multi-agent system
│   │   ├── tools/                # Zoho API LangGraph tools
│   │   ├── llm/                  # Groq LLM integration
│   │   └── memory/               # Short and long-term memory
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── .env.example
├── .gitignore
└── README.md
```

## Example Conversations

```
User: "What projects do I have?"
Bot:  "Here are your projects: 1. TEST PROJECT (Status: active)"

User: "Show tasks for the first one"
Bot:  "Tasks for TEST PROJECT: - Design mockups, - API Integration, - Write tests"

User: "Who has the most tasks this month?"
Bot:  "Task utilisation report: Unassigned (3 tasks)"

User: "Create a task called Fix Login Bug"
Bot:  "Action pending confirmation: Create task 'Fix Login Bug' in TEST PROJECT. Reply yes or no."
User: "yes"
Bot:  "Task created successfully!"
```

## Security

- All credentials stored in .env (never committed to git)
- OAuth 2.0 per-user authentication, no shared tokens
- JWT tokens with 30-minute expiration
- CORS restricted to whitelisted origins
- Automatic token refresh before every Zoho API call

## Known Limitations

- Create task returns 400 error in some cases due to Zoho API requiring tasklist_id
- Task status field returns raw object from Zoho API instead of plain text string
- Only supports single portal per user account
- Task delete and update require exact numeric task ID
- Long-term memory references past project context but does not store full conversation history

## Troubleshooting

**"ZOHO_CLIENT_ID is not configured"**
- Check .env file exists and ZOHO_CLIENT_ID is filled in
- Restart backend server

**OAuth Redirect URI Mismatch**
- Verify redirect URI in .env matches exactly what is set in Zoho Developer Console

**Frontend Cannot Connect to Backend**
- Verify backend is running on port 8000
- Check http://localhost:8000/health

## Quick Reference

| Task | Command |
|------|---------|
| Install backend | pip install -r requirements.txt |
| Install frontend | cd frontend && npm install |
| Start backend | uvicorn backend.main:app --reload |
| Start frontend | cd frontend && npm run dev |
| Configure env | cp .env.example .env |

---

**Version:** 1.0.0
**Last Updated:** June 2026
**Status:** Assessment Build

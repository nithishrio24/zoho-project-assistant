# Zoho Project Assignment Chatbot

A powerful AI-driven chatbot that enables seamless project and task management through conversational interaction with Zoho Projects. This intelligent assistant helps teams create, update, and track tasks directly through natural language conversations, powered by cutting-edge technologies: **OAuth 2.0**, **FastAPI**, **LangGraph**, and a **REST API**.

## What It Does

The Zoho Project Assignment Chatbot bridges the gap between your team and Zoho Projects by providing:

- **Natural Language Task Management** - Create, update, and delete Zoho tasks using conversational commands
- **Project Overview** - Query and list all your projects with a single request
- **Task Tracking** - View tasks, check assignees, and monitor due dates
- **Team Collaboration** - Check project members and task utilization reports
- **Smart Confirmation** - AI verifies complex operations before execution
- **OAuth Authentication** - Secure integration with your Zoho account

Simply chat with the bot: _"Create a task called 'Website Redesign' and assign it to John"_ and it handles the rest!

## Core Technologies

This project demonstrates production-grade implementation of **4 core technologies**:

### 1. **OAuth 2.0 Authentication**
- **Authorization Code Grant Flow** - Secure user authentication with Zoho
- **Per-User Token Storage** - Access & refresh tokens stored in SQLite with automatic expiry management
- **JWT Sessions** - Server-issued JWT tokens for secure REST API access (30-minute expiration)
- **Auto-Refresh** - Tokens automatically refreshed before API calls when near expiry
- **Secure Redirect** - Post-OAuth redirect to frontend with JWT token in URL

**Implementation**: [backend/auth/zoho_oauth.py](./backend/auth/zoho_oauth.py)

### 2. **FastAPI Backend**
- **Async HTTP Framework** - Python 3.11+ with full async/await support for high concurrency
- **7 REST Endpoints** - Production-ready API with proper HTTP methods and status codes
- **JWT Dependency Injection** - Automatic token validation on protected routes
- **CORS Middleware** - Secure cross-origin requests from React frontend
- **Pydantic Validation** - Strict type-safe request/response models
- **Error Handling** - Comprehensive error responses with proper HTTP status codes

**REST Endpoints**:
```
GET  /auth/login           → Start OAuth flow
GET  /auth/callback        → OAuth callback handler  
GET  /auth/test            → Health check
GET  /me                   → Current user info (requires JWT)
POST /chat                 → Chat endpoint (requires JWT)
GET  /health               → Server health check
```

**Implementation**: [backend/main.py](./backend/main.py)

### 3. **LangGraph Multi-Agent System**
- **Stateful GraphState** - TypedDict with Annotated fields for message accumulation
- **9 @tool Decorated Functions** - LangGraph tools for Zoho API integration:
  1. `get_portals()` - Fetch user portals
  2. `list_projects()` - List all projects
  3. `list_tasks()` - Query tasks with filters
  4. `get_task_details()` - Full task information
  5. `create_task()` - Create new task (requires confirmation)
  6. `update_task()` - Modify task (requires confirmation)
  7. `delete_task()` - Remove task (requires confirmation)
  8. `list_project_members()` - Team roster
  9. `get_task_utilisation()` - Task load per member

- **Router Agent** - Groq LLM classifies intent as "query" or "action"
- **Query Agent** - Handles read-only operations (direct tool invocation)
- **Action Agent** - Prepares write operations with Groq LLM for confirmation
- **Confirm Handler** - Executes or cancels pending actions on user approval

**Implementation**: 
- [backend/agents/router.py](./backend/agents/router.py)
- [backend/agents/query_agent.py](./backend/agents/query_agent.py)
- [backend/agents/action_agent.py](./backend/agents/action_agent.py)
- [backend/agents/confirm_handler.py](./backend/agents/confirm_handler.py)
- [backend/tools/zoho_tools.py](./backend/tools/zoho_tools.py)

### 4. **REST API Design**
- **Stateless Authentication** - JWT tokens enable stateless REST API
- **JSON Request/Response** - Structured data with Pydantic models
- **Idempotent Operations** - Safe to retry without side effects
- **Proper HTTP Methods** - GET for reads, POST for writes
- **Status Codes** - 200 OK, 400 Bad Request, 401 Unauthorized, 500 Server Error
- **Session Management** - Session IDs track conversation state across requests

**Example REST Flow**:
```json
POST /chat
{
  "user_message": "What projects do I have?",
  "session_id": "session_123"
}

Response:
{
  "response": "Here are your projects: Project A, Project B...",
  "awaiting_confirmation": false,
  "session_id": "session_123"
}
```

## Features

- **AI-Powered Conversations** - Uses Groq's LLM for intelligent request understanding
- **Zoho Projects Integration** - Full API integration for all project operations
- **Secure OAuth 2.0** - OAuth-based authentication with JWT token management
- **Task Operations**
  - Create tasks with auto-assignment and due dates
  - Update existing tasks
  - Delete tasks with confirmation
  - List tasks by project
- **Project Management**
  - View all portals and projects
  - Get project member lists
  - Track task utilization per team member
  - Access task details
- **Session Memory** - Maintains context across conversations
- **Human-in-the-Loop Confirmation** - Write operations require user approval
- **Professional UI** - Black and yellow themed responsive chat interface
- **Error Handling** - Graceful error recovery with user-friendly messages
- **Mock Mode** - Full agent simulation without Zoho or Groq credentials (`TEST_MODE=1`)

## Tech Stack

### Backend
- **Python 3.11+** - Core application language
- **FastAPI** - Modern async web framework
- **LangGraph** - Multi-agent orchestration with stateful routing
- **Groq LLM** - `llama-3.1-8b-instant` model for fast inference
- **SQLite + aiosqlite** - Async database for tokens and memory
- **httpx** - Async HTTP client for Zoho API
- **Python-Jose** - JWT token creation and verification
- **Pydantic** - Type-safe request/response validation

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **CSS3** - Professional black & yellow theme

### External APIs
- **Zoho Projects API** - Project and task management
- **Zoho Accounts API** - OAuth 2.0 authentication
- **Groq API** - LLM inference

## Prerequisites

Before you begin, ensure you have:

- Python 3.11+ installed
- Node.js 18+ and npm installed
- A Zoho Projects account
- A Groq API key (free tier available at [console.groq.com](https://console.groq.com))
- Zoho OAuth credentials (from Zoho Developer Console)

## Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/nithishrio24/zoho-project-assistant.git
cd zoho-project-chatbot

# Create and activate Python virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables**:
```env
# Zoho OAuth Configuration
ZOHO_CLIENT_ID=your_client_id_here
ZOHO_CLIENT_SECRET=your_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback

# Groq LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Security (generate strong key for production)
SECRET_KEY=your-secret-key-here

# Optional (defaults provided)
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_API_BASE=https://projectsapi.zoho.in/restapi
DATABASE_URL=sqlite:///./zoho_chatbot.db
FRONTEND_URL=http://localhost:5173
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Start the Application

**Terminal 1 - Backend (FastAPI)**
```bash
# From zoho-project-chatbot directory
$env:PYTHONPATH = (Get-Location).Path   # Windows PowerShell
uvicorn backend.main:app --reload --port 8000
```

Backend runs on: `http://localhost:8000`

**Terminal 2 - Frontend (React/Vite)**
```bash
cd frontend
npm run dev
```

Frontend runs on: `http://localhost:5173`

Visit `http://localhost:5173` in your browser and click "Login with Zoho" to start!

## OAuth Configuration Guide

### Register a Zoho Application

1. Go to the [Zoho API Console](https://api-console.zoho.in/)
2. Create a **Server-based Application**
3. Set the redirect URI to: `http://localhost:8000/auth/callback`
4. Add these scopes:
   - `ZohoProjects.portals.READ`
   - `ZohoProjects.projects.CREATE`
   - `ZohoProjects.projects.READ`
   - `ZohoProjects.projects.UPDATE`
   - `ZohoProjects.tasks.CREATE`
   - `ZohoProjects.tasks.READ`
   - `ZohoProjects.tasks.UPDATE`
   - `ZohoProjects.tasks.DELETE`
   - `ZohoProjects.users.READ`
5. Copy the **Client ID** and **Client Secret** into `.env`

### OAuth 2.0 Flow

1. User clicks "Login with Zoho" → `GET /auth/login` redirects to Zoho OAuth
2. Zoho redirects back with code → `GET /auth/callback?code=...`
3. Backend exchanges code for tokens via Zoho API
4. Tokens stored in SQLite with expiry metadata
5. Server issues JWT token → Frontend redirected to chat with JWT in URL
6. Frontend sends JWT on every `/chat` request
7. FastAPI validates JWT via dependency injection
8. Tokens auto-refresh before expiry on API calls

## Project Structure

```
zoho-project-chatbot/
├── backend/
│   ├── main.py                  # FastAPI app, REST endpoints, JWT middleware
│   ├── config.py                # Environment configuration
│   ├── models.py                # Pydantic request/response models
│   ├── zoho_client.py           # Async Zoho API client (OAuth token refresh)
│   ├── auth/
│   │   ├── __init__.py
│   │   └── zoho_oauth.py        # OAuth 2.0 & JWT implementation
│   ├── agents/
│   │   ├── router.py            # LangGraph Router (intent classification)
│   │   ├── query_agent.py       # LangGraph Query Agent (read operations)
│   │   ├── action_agent.py      # LangGraph Action Agent (write operations)
│   │   └── confirm_handler.py   # LangGraph Confirm Handler
│   ├── tools/
│   │   └── zoho_tools.py        # 9 LangGraph @tool decorated functions
│   ├── llm/
│   │   ├── groq_llm.py          # Groq ChatLLM helper
│   │   └── mock_groq.py         # Mock LLM for testing
│   ├── memory/
│   │   └── memory_store.py      # SQLite session memory persistence
│   └── tests/
│       ├── simulation.py        # E2E agent simulation (TEST_MODE=1)
│       └── e2e_mock_test.py     # Tool-level tests
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── App.css              # Styling
│   │   ├── index.css            # Global styles
│   │   ├── main.jsx             # React entry point
│   │   └── components/
│   │       ├── ChatWindow.jsx   # Chat UI component
│   │       ├── LoginButton.jsx  # OAuth login button
│   │       └── MessageBubble.jsx # Message display
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── requirements.txt              # Python dependencies (pinned versions)
├── .env.example                  # Environment template
├── README.md                     # This file
└── ARCHITECTURE.md              # Detailed system design
```

## How It Works

### Authentication Flow (OAuth 2.0 + JWT)

```
1. User clicks "Login" button
        ↓
2. Frontend redirects to /auth/login
        ↓
3. Backend returns OAuth consent URL
        ↓
4. User authenticates with Zoho
        ↓
5. Zoho redirects with authorization code
        ↓
6. Backend exchanges code for access token (OAuth flow)
        ↓
7. Access & refresh tokens stored in SQLite
        ↓
8. JWT token issued to frontend
        ↓
9. Frontend stores JWT, includes in all /chat requests
        ↓
10. FastAPI validates JWT via dependency injection
```

### Chat Flow (LangGraph Multi-Agent)

```
1. User sends message to /chat with JWT
        ↓
2. FastAPI validates JWT token
        ↓
3. Message routed to LangGraph Router Agent
        ↓
4. Groq LLM classifies intent:
   - "query" → Query Agent (read-only)
   - "action" → Action Agent (write operation)
        ↓
5. Query Agent: Direct tool invocation
   - list_projects, list_tasks, get_task_details, etc.
        ↓
   Action Agent: Extract parameters → set awaiting_confirmation=True
        ↓
6. Response sent to frontend with awaiting_confirmation flag
        ↓
7. If awaiting_confirmation=True:
   - User sees confirmation prompt
   - User says "yes" or "no"
   - Confirm Handler executes or cancels
        ↓
8. Response returned with result/error
```

### REST API Response Format

Every `/chat` response follows this contract:

```json
{
  "response": "Here are your projects: Project A, Project B",
  "awaiting_confirmation": false,
  "session_id": "session_123"
}
```

When `awaiting_confirmation=true`:
```json
{
  "response": "Action pending: Create task 'Fix Bug' in Project A. Confirm?",
  "awaiting_confirmation": true,
  "session_id": "session_123"
}
```

## Running Tests

### Agent Simulation (Mocked, No Credentials Needed)

```bash
# From zoho-project-chatbot directory
$env:PYTHONPATH = (Get-Location).Path   # Windows PowerShell
$env:TEST_MODE = "1"
python backend/tests/simulation.py
```

Tests all 4 LangGraph agents without Zoho/Groq credentials:
- Router routes to query vs action correctly
- Query agent returns mock project data
- Action agent sets awaiting_confirmation=true
- Confirm handler executes on "yes"
- Session memory persists across turns

### Tool-Level Tests

```bash
python -m backend.tests.e2e_mock_test
```

Verifies all 9 LangGraph tools work correctly with mock data.

## Deployment

### Docker

```bash
# Build
docker build -t zoho-chatbot .

# Run
docker run -p 8000:8000 -p 5173:5173 --env-file .env zoho-chatbot
```

### Production Environment Variables

```env
ZOHO_CLIENT_ID=prod_client_id
ZOHO_CLIENT_SECRET=prod_client_secret
ZOHO_REDIRECT_URI=https://yourdomain.com/auth/callback
GROQ_API_KEY=prod_groq_key
SECRET_KEY=production_secret_key_change_this
FRONTEND_URL=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@db:5432/zoho_chatbot
```

For production, use PostgreSQL instead of SQLite.

## Security

- **Environment Variables** - All credentials in `.env` (never committed)
- **OAuth 2.0** - Secure authorization flow with Zoho
- **JWT Tokens** - 30-minute expiration with automatic refresh
- **Encrypted Token Storage** - Tokens stored securely in database
- **CORS Protection** - Restricted to whitelisted origins
- **Secret Masking** - Logs don't expose credentials
- **No Hardcoded Secrets** - Everything parameterized

## Troubleshooting

### "ZOHO_CLIENT_ID is not configured"
- Verify `.env` file exists in the project root
- Check `ZOHO_CLIENT_ID` is filled with your credentials
- Restart backend server

### "GROQ_API_KEY is not set"
- Get free API key from [console.groq.com](https://console.groq.com)
- Add to `.env` file
- Restart backend server

### OAuth Redirect URI Mismatch
- Ensure `.env` has correct `ZOHO_REDIRECT_URI`
- Must match URI registered in Zoho Developer Console
- Default: `http://localhost:8000/auth/callback`

### Frontend Can't Connect to Backend
- Verify backend running: `curl http://localhost:8000/auth/test`
- Check CORS enabled in FastAPI
- Verify frontend API URL matches backend

### Session Lost on Restart
- Sessions are in-memory (normal for development)
- Use Redis for multi-instance production setup
- See deployment section

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed system design & LangGraph flow
- [QUICK_START.md](./QUICK_START.md) - Backend quick reference
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Requirements checklist

## Examples

### List Projects
```
User: "What projects do I have?"
Bot: "Here are your projects: Website Redesign (5 tasks), Mobile App (3 tasks)"
```

### Create Task with Confirmation
```
User: "Create a task called Fix Login Bug"
Bot: "Action pending confirmation: Create task 'Fix Login Bug' in Website Redesign project. Confirm?"
User: "yes"
Bot: "✓ Task created successfully! (Task ID: 12345)"
```

### Check Team Workload
```
User: "Who has the most tasks?"
Bot: "Task utilization: John (8 tasks), Sarah (6 tasks), Mike (4 tasks)"
```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check `.env` configuration
2. Review backend logs: `uvicorn backend.main:app --reload` (shows full output)
3. Verify Zoho OAuth credentials are correct
4. Check GROQ_API_KEY is valid
5. Try mock mode: `$env:TEST_MODE=1 ; python backend/tests/simulation.py`

---

**Version:** 1.0.0  
**Last Updated:** June 2026  
**Status:** Production Ready  
**Core Technologies:** OAuth 2.0 • FastAPI • LangGraph • REST API

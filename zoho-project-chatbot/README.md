# Zoho Project Chatbot

An AI-powered chatbot for Zoho Projects. Users manage projects and tasks through natural language, with OAuth authentication, multi-agent routing, and human-in-the-loop confirmation for write operations.

## Features

- **OAuth 2.0 Authentication** — Secure Zoho login with JWT sessions
- **Multi-Agent System** — Router, query agent, action agent, and confirm handler
- **Project Management** — List projects, tasks, members, and utilisation reports
- **Task Operations** — Create, update, and delete tasks with confirmation prompts
- **Session Memory** — Short-term context across turns plus long-term SQLite storage
- **Mock Mode** — Full agent simulation without Zoho or OpenAI credentials (`TEST_MODE=1`)

## Architecture Overview

```
User (React Frontend)
        |
        v
   POST /chat  (JWT auth)
        |
        v
+---------------------------+
|  FastAPI (main.py)        |
|  In-memory session state  |
+---------------------------+
        |
        +-- awaiting_confirmation? --> Confirm Handler --> execute/cancel tool
        |
        +-- else --> Router (ChatOpenAI)
                        |
            +-----------+-----------+
            |                       |
        Query Agent            Action Agent
        (read tools)           (extract action, set pending)
            |                       |
        list_projects            awaiting_confirmation=True
        list_tasks
        get_task_details
        list_project_members
        get_task_utilisation
```

### Agent Flow

| Agent | Role | LLM Used |
|---|---|---|
| **Router** | Classifies intent as `query` or `action` | Groq `llama-3.1-8b-instant` |
| **Query Agent** | Read-only Zoho tool calls | Direct tool invocation |
| **Action Agent** | Extracts write operation JSON, asks for confirmation | Groq `llama-3.1-8b-instant` |
| **Confirm Handler** | Executes or cancels pending action on yes/no | None |

### Session State

Each chat session stores:

- `messages` — conversation history
- `session_context` — last active project/portal (short-term memory)
- `pending_action` — write operation awaiting confirmation
- `awaiting_confirmation` — boolean gate for confirm handler
- `long_term_memory` — persisted to SQLite per user

### `/chat` Response Contract

Every `/chat` response returns exactly:

```json
{
  "response": "string",
  "awaiting_confirmation": false,
  "session_id": "string"
}
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Zoho Developer Account
- Groq API Key ([console.groq.com](https://console.groq.com))

### 1. Clone and create virtual environment

```bash
cd zoho-project-chatbot
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
ZOHO_CLIENT_ID=your_zoho_client_id
ZOHO_CLIENT_SECRET=your_zoho_client_secret
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
SECRET_KEY=your-super-secret-key-change-in-production
FRONTEND_URL=http://localhost:5173
DATABASE_URL=sqlite:///./zoho_chatbot.db
```

### 4. Run the backend

From the `zoho-project-chatbot` directory (project root):

```bash
# Windows PowerShell
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.main:app --reload --port 8000

# macOS/Linux
PYTHONPATH=. uvicorn backend.main:app --reload --port 8000
```

Backend: `http://localhost:8000`

Health check: `GET http://localhost:8000/health`

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

CORS is enabled for `http://localhost:5173` in `backend/main.py`.

## OAuth Configuration Guide

### Register a Zoho Application

1. Go to the [Zoho API Console](https://api-console.zoho.in/) (use `.com` for US accounts).
2. Create a **Server-based Application** or **Self Client**.
3. Set the redirect URI to:
   ```
   http://localhost:8000/auth/callback
   ```
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
5. Copy the **Client ID** and **Client Secret** into `.env`.

### OAuth Flow

1. User clicks Login → `GET /auth/login` redirects to Zoho consent page.
2. Zoho redirects back to `GET /auth/callback?code=...`.
3. Backend exchanges the code for tokens, stores them in SQLite, and issues a JWT.
4. User is redirected to `http://localhost:5173/chat?token=<jwt>`.
5. Frontend sends `Authorization: Bearer <jwt>` on all `/chat` requests.

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/auth/login` | No | Redirect to Zoho OAuth |
| GET | `/auth/callback` | No | OAuth callback, issue JWT |
| GET | `/me` | JWT | Current user info |
| POST | `/chat` | JWT | Send message, get agent response |
| GET | `/health` | No | Health check |

### POST /chat

**Request:**
```json
{
  "user_message": "What projects do I have?",
  "session_id": "session_123"
}
```

**Response:**
```json
{
  "response": "Here are your projects:\n\n1. **Website Redesign** ...",
  "awaiting_confirmation": false,
  "session_id": "session_123"
}
```

## Running Tests / Simulation

### Agent simulation (mocked Groq + Zoho, no credentials needed)

```bash
# From zoho-project-chatbot directory
$env:PYTHONPATH = (Get-Location).Path   # Windows
$env:TEST_MODE = "1"
python backend/tests/simulation.py
```

This runs 8 turns through `/chat` and verifies:

1. Router routes to query vs action agents
2. Query agent returns project/task data
3. Action agent sets `awaiting_confirmation=True`
4. Confirm handler executes on "yes" and cancels on "no"
5. Short-term memory remembers project from turn 1 in turn 2

### Tool-level mock test

```bash
python -m backend.tests.e2e_mock_test
```

## Project Structure

```
zoho-project-chatbot/
├── backend/
│   ├── main.py              # FastAPI app, /chat, CORS, OAuth
│   ├── config.py            # Environment settings
│   ├── models.py            # Pydantic request/response models
│   ├── zoho_client.py       # Async Zoho API client
│   ├── auth/zoho_oauth.py   # OAuth + JWT
│   ├── agents/
│   │   ├── router.py        # Intent classification
│   │   ├── query_agent.py   # Read operations
│   │   ├── action_agent.py  # Write operations (confirmation)
│   │   └── confirm_handler.py
│   ├── tools/zoho_tools.py  # 9 LangChain tools (+ mock mode)
│   ├── llm/
│   │   └── groq_llm.py      # ChatGroq helper
│   ├── memory/memory_store.py
│   └── tests/
│       └── simulation.py
├── frontend/                # React + Vite
├── requirements.txt         # Pinned working versions
└── .env.example
```

## Known Limitations

1. **In-memory sessions** — Session state is lost on server restart. Use Redis for multi-instance deployments.
2. **SQLite storage** — Suitable for development only; use PostgreSQL in production.
3. **Portal ID default** — Mock mode uses `portal1`; live mode requires valid portal IDs from Zoho.
4. **No rate limiting** — Add SlowAPI or similar before production use.
5. **Confirmation timeout** — Pending actions expire only when the session is cleared.
6. **Groq dependency** — Router and action agent require a valid `GROQ_API_KEY`; use `TEST_MODE=1` with mock simulation for offline testing.
7. **LangGraph listed but not used** — Agent orchestration is manual in `main.py`, not a LangGraph StateGraph.
8. **Single-region Zoho** — Defaults to Zoho India (`accounts.zoho.in`); change `ZOHO_ACCOUNTS_URL` for other regions.

## License

MIT

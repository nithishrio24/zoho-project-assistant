# 🤖 Zoho Project Chatbot - AI-Powered Project Management

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18-blue)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2.4-blue)](https://langchain-ai.github.io/langgraph/)
[![GitHub](https://img.shields.io/badge/GitHub-nithishrio24/zoho--project--assistant-black)](https://github.com/nithishrio24/zoho-project-assistant)

A production-ready conversational AI chatbot for **Zoho Projects** that lets users manage projects, tasks, and team workload entirely through natural language. Built with OAuth 2.0 authentication, a multi-agent LLM system, and human-in-the-loop confirmations for all write operations.

## 🎯 Quick Start (5 minutes)

```bash
# 1. Setup (first time)
cp .env.example .env
# Edit .env with your Zoho & Groq credentials

# 2. Backend (Terminal 1)
cd zoho-project-chatbot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# 3. Frontend (Terminal 2)
cd frontend
npm install
npm run dev

# 4. Open Browser
# Visit: http://localhost:5173
# Click "Login with Zoho"
# Start chatting!
```

**See [QUICK_START.md](QUICK_START.md) for copy-paste commands and [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup.**

---

## ✨ Features

### 🔐 Secure OAuth 2.0 Authentication
- **Per-user Zoho login** — No shared tokens
- **Automatic token refresh** — Silent expiry handling
- **JWT sessions** — Secure frontend-to-backend authentication
- **One-click setup** — Users see "Login with Zoho" button

### 🧠 Multi-Agent AI System
- **Smart Router** — Classifies "Should I read or write?"
- **Query Agent** — Handles read-only requests (list projects, show tasks, etc.)
- **Action Agent** — Handles write requests (create, update, delete)
- **Confirm Handler** — Executes actions only after user confirmation
- **Uses Groq LLM** — Fast, accurate intent classification

### 💾 9 Zoho API Integration Tools

| Tool | Purpose | Agent | Notes |
|------|---------|-------|-------|
| `list_projects` | Fetch all projects for user | Query | No confirmation |
| `list_tasks` | List tasks with optional filters | Query | No confirmation |
| `get_task_details` | Full details of a single task | Query | No confirmation |
| `list_project_members` | Get project team members | Query | No confirmation |
| `get_task_utilisation` | Task load per team member | Query | No confirmation |
| `create_task` | Create new task | Action | ✅ Needs confirmation |
| `update_task` | Modify task (status, assignee, etc.) | Action | ✅ Needs confirmation |
| `delete_task` | Remove a task | Action | ✅ Needs confirmation |
| `get_portals` | List user's Zoho portals | Internal | Used by other tools |

### 🧠 Intelligent Memory

**Short-Term (Session)**
- Remembers which project you're discussing
- Enables: "Show tasks for the **first one**"
- Lost when browser closed (by design)

**Long-Term (Database)**
- Stored in SQLite, keyed by user
- Remembers last active project across sessions
- Enables: "Show me what I was working on"
- Survives browser refresh, logout/login

### ✋ Human-in-the-Loop Confirmation
All write operations (create, update, delete) require explicit user approval:

```
User: "Create a task called API Integration"
Bot: "Action pending confirmation: Create task 'API Integration'..."
    [Confirm Button] [Cancel Button]
User: [Clicks Confirm]
Bot: "✅ Task created successfully!"
```

### 🎨 Modern Chat UI
- Real-time message display
- Typing indicator
- Confirmation dialogs
- Loading states
- Responsive design (mobile-friendly)
- OAuth login integration

---

## 🏗️ Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Vite)                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Login Page           Chat UI          Confirmation   │  │
│  │  - Zoho OAuth        - Messages        - Yes/No btns  │  │
│  │  - Redirect          - Input field     - Action prep  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI + Python)                     │
│                                                             │
│  OAuth Layer                    LLM Agent Layer            │
│  ┌──────────────────┐           ┌──────────────────┐      │
│  │ /auth/login      │           │ Router Node      │      │
│  │ /auth/callback   │     ───→  │ Intent classif.  │      │
│  │ JWT middleware   │           │ (query/action)   │      │
│  └──────────────────┘           └──────────────────┘      │
│                                          │                 │
│  User Token DB          Memory Store    │                 │
│  ┌──────────────────┐  ┌───────────┐   │                 │
│  │ access_token     │  │ user_mem  │   ├─→ Query Agent   │
│  │ refresh_token    │  │ (long-tm) │   │   (read tools)  │
│  │ expires_at       │  └───────────┘   │                 │
│  └──────────────────┘                   ├─→ Action Agent  │
│                                         │   (write ops)   │
│                        Session State    │                 │
│                        (in-memory)      └─→ Confirm Hdlr │
│                        ┌──────────────┐     (execute)    │
│                        │ messages     │                    │
│                        │ context      │                    │
│                        │ pending_act. │                    │
│                        └──────────────┘                    │
│                                                             │
│  Tool Layer (Zoho API Integration)                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  list_projects  list_tasks  create_task             │  │
│  │  update_task    delete_task  list_project_members   │  │
│  │  get_task_details    get_task_utilisation           │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         HTTPS/REST
┌─────────────────────────────────────────────────────────────┐
│              ZOHO PROJECTS API                              │
│  https://projectsapi.zoho.in/restapi                       │
└─────────────────────────────────────────────────────────────┘
```

### Agent Flow Diagram

```
User Message (e.g., "Show tasks for the first one")
        │
        ↓
    ┌─────────────────┐
    │  Router Node    │  (Uses Groq LLM to classify)
    └─────────────────┘
        │ "query"
        ↓
    ┌─────────────────┐
    │ Query Agent     │  (Read-only, no confirmation)
    ├─────────────────┤
    │ Uses tools:     │
    │ - list_projects │
    │ - list_tasks    │
    │ - get_details   │
    │ - list_members  │
    │ - get_util.     │
    └─────────────────┘
        │
        ↓
    Response: "Tasks for Website Redesign: Design mockups (due 7/1), API Integration (due 7/10)"
```

### State Management Flow

```
User sends "Create task API Integration"
        │
        ↓
    [Session loaded from DB (long-term memory)]
    [Session context: last_project_id, last_portal_id, etc.]
        │
        ↓
    [Message appended to session.messages]
        │
        ↓
    [Router classifies as "action"]
        │
        ↓
    [Action Agent extracts: tool_name="create_task", parameters={...}]
    [Sets awaiting_confirmation=True, pending_action={...}]
        │
        ↓
    [Response sent to frontend: "Confirm? [Yes] [No]"]
        │
        ↓
    [User clicks Confirm → sends "yes"]
        │
        ↓
    [Confirm Handler finds pending_action]
    [Calls create_task tool]
    [Tool returns result]
        │
        ↓
    [Response: "✅ Task created!" awaiting_confirmation=False]
        │
        ↓
    [Session saved to DB for long-term memory]
```

---

## 🚀 Usage Examples

### Example 1: List Projects
```
User:  "What projects do I have?"
Bot:   "Here are your projects:
        1. Website Redesign (ID: 1001, Status: active)
        2. Mobile App Development (ID: 1002, Status: active)"
```

### Example 2: Context Memory
```
User:  "Show tasks for the first one"
Bot:   (Remembers "Website Redesign" from context)
       "Tasks for Website Redesign:
        - Design mockups (Status: open, Assignee: alice)
        - API Integration (Status: in_progress, Assignee: bob)"
```

### Example 3: Create with Confirmation
```
User:  "Create a task called Write Documentation with due date tomorrow"
Bot:   "Action pending confirmation:
        Create task "Write Documentation"
        Due date: 2026-06-12
        Project: Website Redesign
        
        Reply with **yes** to confirm or **no** to cancel."
User:  "yes"
Bot:   "✅ Task created successfully!
        Task ID: 1234, Status: open"
```

### Example 4: Delete with Confirmation
```
User:  "Delete task #99"
Bot:   "Action pending confirmation:
        Delete task #99 (Write tests)
        
        Reply with **yes** to confirm or **no** to cancel."
User:  "no"
Bot:   "❌ Action cancelled. Task #99 was not deleted."
```

### Example 5: Task Utilization Report
```
User:  "Who has the most tasks this month?"
Bot:   "Task utilisation report:
        - carol: 8 tasks (Write tests, Code review, Documentation)
        - alice: 5 tasks (Design mockups, Wireframes, Assets)
        - bob: 3 tasks (API Integration, Database setup)"
```

---

## 🔧 Setup & Configuration

### Prerequisites
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Zoho Account** - [Sign up free](https://www.zoho.com/)
- **Groq API Key** - [Get free key](https://console.groq.com/)

### Environment Variables

Create `.env` file with:

```env
# Zoho OAuth (get from https://api-console.zoho.in/)
ZOHO_CLIENT_ID=your_client_id
ZOHO_CLIENT_SECRET=your_client_secret
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_API_BASE=https://projectsapi.zoho.in/restapi

# Groq LLM (get from https://console.groq.com/)
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant

# Security (change these!)
SECRET_KEY=your-super-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./zoho_chatbot.db

# Frontend
FRONTEND_URL=http://localhost:5173
```

### Installation

```bash
# Clone or extract project
cd zoho-project-chatbot

# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Running

**Terminal 1 (Backend):**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

**Browser:**
Visit http://localhost:5173 and click "Login with Zoho"

---

## 📁 Project Structure

```
zoho-project-chatbot/
├── backend/
│   ├── main.py                 # FastAPI app, /chat endpoint
│   ├── config.py               # Configuration management
│   ├── models.py               # Pydantic models
│   ├── zoho_client.py          # Zoho API client (async)
│   ├── portal_utils.py         # Portal slug helpers
│   ├── auth/
│   │   └── zoho_oauth.py       # OAuth 2.0 flow
│   ├── agents/
│   │   ├── router.py           # Intent router
│   │   ├── query_agent.py      # Read operations
│   │   ├── action_agent.py     # Write operations
│   │   └── confirm_handler.py  # Confirmation execution
│   ├── tools/
│   │   └── zoho_tools.py       # 8+ Zoho tools
│   ├── memory/
│   │   └── memory_store.py     # Long-term memory (SQLite)
│   ├── llm/
│   │   ├── groq_llm.py         # Groq configuration
│   │   └── mock_groq.py        # Mock for testing
│   └── tests/
│       ├── e2e_mock_test.py    # Tool verification
│       └── agent_simulation.py # Agent flow testing
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app component
│   │   ├── main.jsx            # React entry
│   │   └── components/
│   │       ├── ChatWindow.jsx  # Chat interface
│   │       ├── LoginButton.jsx # OAuth login
│   │       └── MessageBubble.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── QUICK_START.md              # 5-minute quickstart
├── SETUP_GUIDE.md              # Detailed setup
├── ARCHITECTURE.md             # System design
├── VERIFICATION_CHECKLIST.md   # Requirements verification
└── .gitignore
```

---

## 🧪 Testing

### Test All Tools (Mock Mode)
```bash
cd zoho-project-chatbot
export PYTHONPATH=.
python backend/tests/e2e_mock_test.py
```

Expected output: All 9 tools work correctly with mock data.

### Test with Real Zoho (Need credentials)
1. Set ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, GROQ_API_KEY in .env
2. Start backend: `uvicorn backend.main:app --reload`
3. Visit http://localhost:5173
4. Click "Login with Zoho"
5. Authorize the app
6. Chat!

---

## 🔐 Security Features

- ✅ **OAuth 2.0 Authorization Code Grant** — Industry standard
- ✅ **JWT Tokens** — Secure, stateless authentication
- ✅ **Per-User Token Storage** — No shared tokens
- ✅ **Automatic Token Refresh** — Silent expiry handling
- ✅ **HTTPS Ready** — Works with HTTPS in production
- ✅ **CORS Configured** — Secure cross-origin requests
- ✅ **Environment Secrets** — No hardcoded credentials
- ✅ **Async Database** — No blocking calls
- ✅ **Human-in-the-Loop** — User approval for all writes

---

## 🚀 Deployment

### Production Checklist

- [ ] Generate strong SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Update Zoho OAuth redirect_uri in console to production domain
- [ ] Set DATABASE_URL to PostgreSQL (recommended over SQLite)
- [ ] Set FRONTEND_URL to production domain
- [ ] Use production Groq API key
- [ ] Enable HTTPS for all URLs
- [ ] Set Python logging level to WARNING
- [ ] Use uvicorn with gunicorn: `gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app`
- [ ] Build frontend: `npm run build`
- [ ] Serve frontend with nginx/apache
- [ ] Set up database backups

---

## 📊 Requirements Verification

All 9 requirements from specification fully implemented:

✅ **1. User-Based OAuth 2.0 Authentication**
- Authorization Code Grant flow
- Per-user token storage
- Auto-refresh before API calls
- Clean session management

✅ **2. Multi-Agent Architecture**
- Router: Intent classification
- Query Agent: Read operations
- Action Agent: Write operations
- Confirm Handler: User approval
- Clean separation of concerns

✅ **3. LangGraph with 8+ Tools**
- list_projects, list_tasks, get_task_details
- create_task, update_task, delete_task
- list_project_members, get_task_utilisation
- Bonus: get_portals

✅ **4. Memory Systems**
- Short-term: Session context (in-memory)
- Long-term: User-scoped SQLite persistence

✅ **5. Human-in-the-Loop Confirmation**
- All write ops require explicit approval
- Clean cancellation with no side effects

✅ **6. FastAPI Backend**
- All endpoints async/await
- JWT middleware
- Proper error handling

✅ **7. Chat UI**
- React frontend with OAuth login
- Message history with real-time updates
- Confirmation buttons for actions

✅ **8. Code Quality & Git**
- Python OOP classes
- Public GitHub repository
- Comprehensive documentation

✅ **9. Sample Conversations**
- All sample scenarios handled correctly

---

## 🤝 Contributing

This is a complete, production-ready implementation. To extend:

1. **Add new tools** → Add `@tool` functions in `backend/tools/zoho_tools.py`
2. **Customize agents** → Modify `backend/agents/`
3. **Enhance UI** → Edit `frontend/src/components/`
4. **Change LLM** → Update `backend/llm/groq_llm.py` to use different provider

---

## 📝 License

This project is provided as-is for educational and business use.

---

## 🔗 Resources

- [Zoho Projects API Docs](https://www.zoho.com/projects/help/rest-api/projects-api.html)
- [Zoho OAuth Documentation](https://www.zoho.com/accounts/protocol/oauth.html)
- [Groq Documentation](https://console.groq.com/docs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## ⚡ Troubleshooting

### "ModuleNotFoundError: No module named 'backend'"
```bash
export PYTHONPATH=.
python -m main  # Don't run main.py directly
```

### "Port 8000 already in use"
```bash
# Find and kill the process
lsof -i :8000        # macOS/Linux
netstat -ano | grep 8000  # Windows
```

### "OAuth redirect_uri mismatch"
- Verify `ZOHO_REDIRECT_URI` in `.env` matches Zoho console
- Default: `http://localhost:8000/auth/callback`

### "No portals found"
- Create a portal at https://projects.zoho.in first
- Portal must have at least one project with tasks

### "Groq API key invalid"
- Get free key from https://console.groq.com
- Paste key in `.env` as `GROQ_API_KEY=gsk_...`

---

**For detailed setup, see [SETUP_GUIDE.md](SETUP_GUIDE.md) or [QUICK_START.md](QUICK_START.md)**

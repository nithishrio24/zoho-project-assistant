# Architecture & Design - Zoho Project Chatbot

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                       │
│                    ┌──────────────────────────────┐                  │
│                    │  Chat UI Components          │                  │
│                    │  - LoginButton               │                  │
│                    │  - ChatWindow                │                  │
│                    │  - MessageBubble             │                  │
│                    └──────────────────────────────┘                  │
│                                 │                                    │
│                          HTTP/REST API                              │
│                                 │                                    │
├─────────────────────────────────────────────────────────────────────┤
│                  FastAPI Backend (Python)                           │
│                ┌────────────────────────────────────┐               │
│                │     OAuth 2.0 Flow                 │               │
│                │  ┌────────────────────────────────┐│               │
│                │  │ /auth/login                     ││               │
│                │  │ /auth/callback                  ││               │
│                │  │ JWT Token Management            ││               │
│                │  └────────────────────────────────┘│               │
│                └────────────────────────────────────┘               │
│                                 │                                    │
│                ┌────────────────────────────────────┐               │
│                │     LangGraph Agent System         │               │
│                │  ┌────────────────────────────────┐│               │
│                │  │ Router Node                     ││               │
│                │  │ Query Agent Node                ││               │
│                │  │ Action Agent Node               ││               │
│                │  │ Confirm Handler Node            ││               │
│                │  │ Tool Executor Node              ││               │
│                │  └────────────────────────────────┘│               │
│                └────────────────────────────────────┘               │
│                                 │                                    │
│                ┌────────────────────────────────────┐               │
│                │  8 Zoho Integration Tools          │               │
│                │  ┌────────────────────────────────┐│               │
│                │  │ list_projects                   ││               │
│                │  │ list_tasks                      ││               │
│                │  │ get_task_details                ││               │
│                │  │ create_task                     ││               │
│                │  │ update_task                     ││               │
│                │  │ delete_task                     ││               │
│                │  │ list_project_members            ││               │
│                │  │ get_task_utilisation            ││               │
│                │  └────────────────────────────────┘│               │
│                └────────────────────────────────────┘               │
│                                 │                                    │
├─────────────────────────────────────────────────────────────────────┤
│         Data & Service Layer                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ┌─────────────────┐  ┌─────────────────┐ ┌──────────────┐  │  │
│  │ │ SQLite Database │  │ ZohoClient      │ │ MemoryStore  │  │  │
│  │ │                 │  │ (HTTP Client)   │ │              │  │  │
│  │ │ - user_tokens   │  │ - Auto-refresh  │ │ - Short-term │  │  │
│  │ │ - user_memory   │  │ - Token mgmt    │ │ - Long-term  │  │  │
│  │ └─────────────────┘  └─────────────────┘ └──────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                 │                                    │
├─────────────────────────────────────────────────────────────────────┤
│              External Services                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ┌──────────────────┐  ┌──────────────────────────────────┐ │  │
│  │  │ Zoho Projects    │  │ OpenAI GPT-4o-mini               │ │  │
│  │  │ API              │  │ - Conversation Intelligence      │ │  │
│  │  │ (projectsapi     │  │ - Tool Calling                   │ │  │
│  │  │  .zoho.in)       │  │ - Intent Classification          │ │  │
│  │  └──────────────────┘  └──────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 🔄 Request Flow

### Login Flow
```
User clicks "Login with Zoho"
    ↓
GET /auth/login
    ↓
Redirect to Zoho OAuth URL
    ↓
User authorizes on Zoho
    ↓
Zoho redirects to GET /auth/callback?code=xxx
    ↓
Exchange code for tokens
    ↓
Store tokens in SQLite
    ↓
Create JWT token
    ↓
Redirect to frontend with JWT
    ↓
Frontend stores JWT in localStorage
    ↓
User sees chat interface
```

### Chat Flow
```
User sends message
    ↓
Frontend sends POST /chat with JWT
    ↓
Backend loads session state
    ↓
Router Node classifies intent (query/action/confirm)
    ↓
    ├─→ QUERY PATH
    │   ├─ Load query tools (5 tools)
    │   ├─ LLM invokes tools with tool calling
    │   ├─ Tool executor runs Zoho API calls
    │   └─ Return results to user
    │
    ├─→ ACTION PATH
    │   ├─ Extract action details from user message
    │   ├─ Generate confirmation prompt
    │   ├─ Store pending_action in state
    │   ├─ Set awaiting_confirmation = true
    │   └─ Return confirmation prompt to user
    │
    └─→ CONFIRM PATH
        ├─ Check if user said "yes" or "no"
        ├─ If YES:
        │   ├─ Get pending tool from state
        │   ├─ Execute tool with parameters
        │   └─ Return success/error
        └─ If NO:
            └─ Clear pending action, return cancelled message

Backend saves updated state back to session_states dict
    ↓
Save long-term memory to database
    ↓
Return ChatResponse with response text and awaiting_confirmation flag
    ↓
Frontend displays message
    ↓
If awaiting_confirmation=true, show Confirm/Cancel buttons instead of input box
```

## 🤖 LangGraph State Management

### State Structure
```python
{
    "messages": Annotated[List[BaseMessage], add],
    # History of all messages (with operator.add for accumulation)
    
    "user_id": str,
    # Current authenticated user ID
    
    "current_agent": str,
    # Current routing: "router" | "query" | "action" | "confirm"
    
    "pending_action": Optional[Dict],
    # {
    #   "action_type": "create_task|update_task|delete_task",
    #   "tool_name": "create_task|update_task|delete_task",
    #   "parameters": { portal_id, project_id, task_id, etc }
    # }
    
    "awaiting_confirmation": bool,
    # Whether we're waiting for user yes/no response
    
    "session_context": Dict,
    # {
    #   "last_project_id": "proj_123",
    #   "last_project_name": "Backend",
    #   "last_portal_id": "portal_456",
    # }
    
    "long_term_memory": Dict,
    # Loaded from SQLite, persists across sessions
    # {
    #   "last_active_project": "proj_123",
    #   "preferences": {...},
    #   "viewed_projects": [...]
    # }
}
```

## 🛠️ 8 Tools Deep Dive

### Query Tools (Read-Only)

1. **list_projects(portal_id)**
   - Endpoint: GET /portal/{portal_id}/projects/
   - Returns: [{id, name, status}, ...]
   - Used by: Router → Query Agent

2. **list_tasks(portal_id, project_id, status?, assignee?, due_date?)**
   - Endpoint: GET /portal/{portal_id}/projects/{project_id}/tasks/
   - Filters: Optional status, assignee, due_date
   - Returns: [{id, title, status, assignee, due_date, ...}, ...]
   - Used by: Query Agent with optional filtering

3. **get_task_details(portal_id, project_id, task_id)**
   - Endpoint: GET /portal/{portal_id}/projects/{project_id}/tasks/{task_id}/
   - Returns: {id, title, description, status, assignee, due_date, estimated_hours, ...}
   - Used by: Query Agent for detailed views

4. **list_project_members(portal_id, project_id)**
   - Endpoint: GET /portal/{portal_id}/projects/{project_id}/members/
   - Returns: [{id, name, email, role}, ...]
   - Used by: Query Agent for team info

5. **get_task_utilisation(portal_id, project_id)**
   - Endpoint: GET /portal/{portal_id}/projects/{project_id}/tasks/ (aggregated)
   - Returns: [{assignee, task_count, task_list}, ...]
   - Used by: Query Agent for workload distribution

### Action Tools (Write Operations - Confirmation Required)

6. **create_task(portal_id, project_id, name, assignee?, due_date?, description?, priority?)**
   - Endpoint: POST /portal/{portal_id}/projects/{project_id}/tasks/
   - Requires: portal_id, project_id, name
   - Optional: assignee, due_date, description, priority
   - Confirmation: YES required
   - Returns: {id, title, status, message}

7. **update_task(portal_id, project_id, task_id, fields)**
   - Endpoint: PATCH /portal/{portal_id}/projects/{project_id}/tasks/{task_id}/
   - Fields: Any updateable task field
   - Confirmation: YES required
   - Returns: {id, title, status, message}

8. **delete_task(portal_id, project_id, task_id)**
   - Endpoint: DELETE /portal/{portal_id}/projects/{project_id}/tasks/{task_id}/
   - Confirmation: YES required
   - Returns: {message}

## 💾 Database Schema

### user_tokens Table
```sql
CREATE TABLE user_tokens (
    user_id VARCHAR PRIMARY KEY,
    access_token VARCHAR NOT NULL,
    refresh_token VARCHAR NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Purpose**: Store Zoho OAuth tokens with auto-refresh capability

### user_memory Table
```sql
CREATE TABLE user_memory (
    user_id VARCHAR PRIMARY KEY,
    memory_data TEXT NOT NULL DEFAULT '{}',  -- JSON
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Purpose**: Store long-term user preferences and context

**memory_data JSON structure**:
```json
{
  "last_active_project": "proj_123",
  "last_active_project_name": "Backend",
  "last_active_portal": "portal_456",
  "preferences": {
    "timezone": "UTC",
    "language": "en"
  },
  "viewed_projects": ["proj_123", "proj_456"],
  "recent_tasks": ["task_123", "task_456"]
}
```

## 🔐 Authentication & Security

### JWT Token Flow
```
1. User OAuth login → Zoho returns auth_code
2. Backend exchanges code for Zoho tokens
3. Backend creates JWT token with user info
4. Frontend stores JWT in localStorage
5. Every API request includes: Authorization: Bearer <jwt>
6. Backend validates JWT, extracts user_id
7. Backend uses user_id to get Zoho tokens from database
```

### Token Refresh Strategy
```
1. User makes API call
2. ZohoClient._get_valid_token() called
3. Check if cached token still valid
4. If expired: call _refresh_access_token()
5. Exchange refresh_token for new access_token
6. Update database with new token
7. Continue with API call
```

### Security Measures
- JWT with HS256 algorithm
- Tokens stored in database, not in code
- Automatic token refresh before expiry
- CORS validation
- HTTP-only storage recommended for production

## 📊 Session Management

### In-Memory Session Store
```python
session_states: Dict[str, Dict[str, Any]] = {}
# Key: session_id (generated by frontend)
# Value: LangGraph state for that session

# Each session maintained separately
# Allows multiple concurrent users
# State persists across multiple chat turns
```

### State Persistence Strategy
1. **Short-term** (in-state): session_context
2. **Long-term** (SQLite): user_memory
3. **Per-turn**: Updated before/after each chat

## 🚀 Performance Considerations

### Async/Await Architecture
- All I/O operations are non-blocking
- FastAPI with uvicorn for async HTTP
- aiosqlite for async database access
- httpx for async HTTP calls to Zoho

### Scalability Limits
- In-memory session store: Limited by available RAM
- SQLite: Good for development, not for production
- Single instance only: No multi-process support

### Production Recommendations
- Replace session_states dict with Redis
- Use PostgreSQL instead of SQLite
- Add connection pooling
- Implement caching for frequently accessed data
- Use load balancer with multiple backend instances

## 🔄 Agent Decision Logic

### Router Node Logic
```
User Input Analysis:
  ├─ Contains action words (create, update, delete)?
  │  └─ Route to ACTION
  ├─ Is a confirmation response (yes/no)?
  │  └─ Route to CONFIRM (if awaiting_confirmation)
  └─ Otherwise
     └─ Route to QUERY
```

### Query Agent Logic
```
1. Receive user message
2. Load available tools (5 query tools)
3. Create prompt with session context
4. LLM analyzes message and decides which tools to call
5. Tool executor runs tool calls
6. Format results and return to user
7. Update session_context if project mentioned
```

### Action Agent Logic
```
1. Receive user message
2. Extract action requirements:
   - Action type (create/update/delete)
   - Target resource (portal, project, task)
   - Parameters (name, assignee, fields, etc)
3. Store in pending_action
4. Generate human-readable confirmation message
5. Set awaiting_confirmation = true
6. Return confirmation prompt to user
```

### Confirm Handler Logic
```
1. Check user input for yes/no
2. If YES:
   - Retrieve pending_action
   - Get tool from tools list
   - Execute with stored parameters
   - Return success/error message
3. If NO:
   - Clear pending_action
   - Return cancellation message
4. Set awaiting_confirmation = false
5. Continue to next turn
```

## 📈 Memory System

### Short-Term Memory (Session Context)
- Active project ID and name
- Active portal ID
- Carries across turns within same session
- Lost when session ends

### Long-Term Memory (SQLite)
- Last active project
- User preferences
- Viewed projects list
- Recent tasks
- Persists across sessions
- Loaded on session start
- Updated after each turn

### Memory Update Flow
```
Session Start:
  Load long_term_memory from DB
  ↓
  Each Turn:
    Update session_context
    ↓
    Update long_term_memory
    ↓
    Save to database
```

## 🔌 Integration Points

### Zoho API Integration
- Base URL: https://projectsapi.zoho.in/restapi
- Authentication: Zoho OAuth 2.0 tokens
- Rate limits: Check Zoho documentation
- Endpoints: Projects, Tasks, Team, Timesheet APIs

### OpenAI Integration
- Model: GPT-4o-mini
- Uses: Tool calling, intent classification
- Costs: Per-token pricing
- Rate limits: API rate limiting applied

### Frontend-Backend Communication
- REST API on port 8000
- CORS enabled
- JWT authentication required
- Session-based state management

## 📋 Error Handling

### Backend Error Handling
```
Try-Catch Pattern:
  Catch database errors → Log + return 500
  Catch Zoho API errors → Log + return specific error
  Catch LLM errors → Log + return message error
  Catch validation errors → return 400
```

### Frontend Error Handling
```
Display Strategies:
  Network errors → "Connection failed" message
  Auth errors → Redirect to login
  API errors → Show error message bubble
  Tool failures → Display wrapped error from backend
```

## 🔍 Monitoring & Debugging

### Logging Points
- OAuth flow (login, token refresh)
- Agent routing decisions
- Tool execution (name, parameters, results)
- Database operations
- Error events

### Debug Information
- Session state snapshots
- Message history
- Tool call traces
- Performance metrics (response time)

---

**This architecture supports:**
- ✅ Secure OAuth flow
- ✅ Multi-turn conversations with context
- ✅ Confirmation-based write operations
- ✅ Async, non-blocking operations
- ✅ Scalable tool system
- ✅ Long-term memory persistence
- ✅ Production-ready error handling

# Zoho Project Assignment Chatbot

A powerful AI-driven chatbot that enables seamless project and task management through conversational interaction with Zoho Projects. This intelligent assistant helps teams create, update, and track tasks directly through natural language conversations.

## 🎯 What It Does

The Zoho Project Assignment Chatbot bridges the gap between your team and Zoho Projects by providing:

- **Natural Language Task Management** - Create, update, and delete Zoho tasks using conversational commands
- **Project Overview** - Query and list all your projects with a single request
- **Task Tracking** - View tasks, check assignees, and monitor due dates
- **Team Collaboration** - Check project members and task utilization reports
- **Smart Confirmation** - AI verifies complex operations before execution
- **OAuth Authentication** - Secure integration with your Zoho account

Simply chat with the bot: _"Create a task called 'Website Redesign' and assign it to John"_ and it handles the rest!

## ✨ Features

- ✅ **AI-Powered Conversations** - Uses Groq's LLM for intelligent request understanding
- ✅ **Zoho Projects Integration** - Full API integration for all project operations
- ✅ **Secure OAuth 2.0** - OAuth-based authentication with JWT token management
- ✅ **Task Operations**
  - Create tasks with auto-assignment and due dates
  - Update existing tasks
  - Delete tasks with confirmation
  - List tasks by project
- ✅ **Project Management**
  - View all portals and projects
  - Get project member lists
  - Track task utilization per team member
  - Access task details
- ✅ **Session Memory** - Maintains context across conversations
- ✅ **Professional UI** - Black and yellow themed responsive chat interface
- ✅ **Error Handling** - Graceful error recovery with user-friendly messages

## 🛠️ Tech Stack

### Backend
- **Python 3.9+** - Core application language
- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **LangChain** - LLM orchestration framework
- **Groq LLM** - `llama-3.1-8b-instant` model for fast inference
- **SQLite** - Token and session storage
- **httpx** - Async HTTP client for Zoho API
- **Python-Jose** - JWT token creation and verification
- **python-dotenv** - Environment configuration management

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **CSS3** - Professional black & yellow theme

### APIs & Services
- **Zoho Projects API** - Project and task management
- **Zoho Accounts API** - OAuth 2.0 authentication
- **Groq API** - LLM inference

## 📋 Prerequisites

Before you begin, ensure you have:

- Python 3.9+ installed
- Node.js 18+ and npm installed
- A Zoho Projects account
- A Groq API key (free tier available at [console.groq.com](https://console.groq.com))
- Zoho OAuth credentials (from Zoho Developer Console)

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd skysecure-project

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
# See ENV_SETUP_GUIDE.md for detailed instructions
nano .env
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
cd zoho-project-chatbot
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend (React/Vite)**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` in your browser and start chatting!

## ⚙️ Environment Configuration

### Required Variables

Create a `.env` file in the root directory with these values:

```env
# Zoho OAuth Configuration
ZOHO_CLIENT_ID=your_client_id_here
ZOHO_CLIENT_SECRET=your_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback

# Groq LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Security (generate strong key for production)
SECRET_KEY=your_secret_key_here

# Optional - Defaults provided if not specified
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_API_BASE=https://projectsapi.zoho.in/restapi
DATABASE_URL=sqlite:///./zoho_chatbot.db
FRONTEND_URL=http://localhost:5173
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Detailed Setup Guide

For complete configuration instructions including:
- Getting Zoho OAuth credentials
- Obtaining Groq API key
- Generating secure SECRET_KEY
- Multi-environment setup

→ See [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md)

## 📁 Project Structure

```
skysecure-project/
├── zoho-project-chatbot/          # Backend application
│   ├── backend/
│   │   ├── main.py               # FastAPI application
│   │   ├── config.py             # Configuration management
│   │   ├── auth/                 # OAuth & JWT handling
│   │   ├── agents/               # LangChain agents
│   │   ├── tools/                # Zoho API tools
│   │   ├── llm/                  # LLM integration
│   │   ├── memory/               # Session memory
│   │   └── zoho_client.py        # Zoho API client
│   ├── frontend/                 # React UI
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment template
│   └── .gitignore
│
├── frontend/                      # Root frontend (alternative)
│   ├── src/
│   │   ├── App.jsx              # Main component
│   │   ├── App.css              # Styling
│   │   └── index.css            # Global styles
│   ├── package.json
│   └── vite.config.js
│
├── .env                          # ⚠️ NOT COMMITTED (add your credentials)
├── .env.example                  # ✅ COMMITTED (reference)
├── .gitignore                    # Prevents .env from being committed
├── ENV_SETUP_GUIDE.md            # Detailed configuration guide
└── README.md                     # This file
```

## 🔄 How It Works

### 1. User Authentication
- User clicks "Login with Zoho"
- Redirected to Zoho OAuth login
- App receives authorization code
- Backend exchanges code for access token
- JWT token issued to frontend
- User authenticated and ready to chat

### 2. Chat Flow
- User types a message
- Frontend sends message + JWT token to backend
- LangChain router analyzes request:
  - **Query Agent** → Read-only operations (list, show)
  - **Action Agent** → Write operations (create, update, delete)
- LLM generates response/confirmation
- Backend calls Zoho API as needed
- Response returned to frontend
- Chat updated in real-time

### 3. Example Interactions

**List Projects:**
```
User: "What projects do I have?"
Bot: "Here are your projects..."
```

**Create Task:**
```
User: "Create a task called Fix Login Bug for John, due tomorrow"
Bot: "Action pending confirmation: Create task 'Fix Login Bug'..."
User: "yes"
Bot: "✓ Task created successfully!"
```

**Check Workload:**
```
User: "Who has the most tasks?"
Bot: "Task utilisation report: John (5), Sarah (3)..."
```

## 🔐 Security

- ✅ **Environment Variables** - All credentials in `.env` (never committed)
- ✅ **OAuth 2.0** - Secure Zoho authentication flow
- ✅ **JWT Tokens** - 30-minute expiration for sessions
- ✅ **Secret Masking** - Logs show masked credentials
- ✅ **CORS Protection** - Restricted to whitelisted origins
- ✅ **Database Encryption Ready** - Structure supports encrypted token storage

See [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md) for security best practices.

## 🧪 Testing

### Manual Testing with Test Portal API

```bash
cd zoho-project-chatbot
python test_portal_api.py
```

### Backend API Endpoints

```
GET  /                      # Root (redirects to frontend)
GET  /auth/test            # Health check (no auth required)
GET  /auth/login           # Start OAuth flow
GET  /auth/callback        # OAuth callback handler
POST /chat                 # Chat endpoint (requires JWT)
```

## 📦 Deployment

### Docker Support
```bash
# Build Docker image
docker build -t zoho-chatbot .

# Run container
docker run -p 8000:8000 -p 5173:5173 --env-file .env zoho-chatbot
```

### Environment-Specific Configuration
- **Development**: Use `.env` with local credentials
- **Staging**: Use `ZOHO_REDIRECT_URI=https://staging.example.com/auth/callback`
- **Production**: Set environment variables in deployment platform (GitHub Actions, Docker, Vercel, etc.)

Never commit `.env` files to version control.

## 🐛 Troubleshooting

### "ZOHO_CLIENT_ID is not configured"
- Check `.env` file exists in root directory
- Verify `ZOHO_CLIENT_ID` is filled in
- Restart backend server

### "GROQ_API_KEY is not set"
- Add your Groq API key to `.env`
- Get one free at [console.groq.com](https://console.groq.com)
- Restart backend server

### OAuth Redirect URI Mismatch
- Verify redirect URI in `.env` matches Zoho Developer Console
- Default: `http://localhost:8000/auth/callback`
- For production: Update to your domain

### Frontend Can't Connect to Backend
- Verify backend is running on port 8000: `http://localhost:8000/auth/test`
- Check CORS is enabled (should be by default)
- Check frontend `API` constant matches backend URL

## 📚 Documentation

- [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md) - Detailed environment configuration
- [ARCHITECTURE.md](./zoho-project-chatbot/ARCHITECTURE.md) - System design & flow
- [QUICK_START.md](./zoho-project-chatbot/QUICK_START.md) - Backend quick start

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open Pull Request

**Important:** Never commit `.env` files or API keys.

## 📄 License

This project is proprietary. All rights reserved.

## 🆘 Support

For issues, questions, or suggestions:
1. Check the troubleshooting section above
2. Review [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md)
3. Check backend logs: `uvicorn backend.main:app --reload` shows detailed output
4. Verify .env configuration

## 🎉 Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `pip install -r requirements.txt && cd frontend && npm install` |
| Configure environment | `cp .env.example .env && nano .env` |
| Start backend | `cd zoho-project-chatbot && uvicorn backend.main:app --reload` |
| Start frontend | `cd frontend && npm run dev` |
| Run tests | `cd zoho-project-chatbot && python test_portal_api.py` |
| View startup config | Check backend logs for "CONFIGURATION" output |

---

**Version:** 1.0.0  
**Last Updated:** June 2026  
**Status:** ✅ Production Ready

# Quick Start - 5 Minutes to Running

## TL;DR - Copy & Paste Commands

### 1. Setup (First Time Only)

```bash
# Copy environment file
cp .env.example .env

# Edit .env and fill in these 3 variables:
# ZOHO_CLIENT_ID=your_value
# ZOHO_CLIENT_SECRET=your_value  
# OPENAI_API_KEY=your_value
```

### 2. Terminal 1 - Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Terminal 2 - Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Browser

Visit: **http://localhost:5173**

Click **"Login with Zoho"** and start chatting!

---

## What You Need (Before Starting)

✅ Python 3.9+  
✅ Node.js 16+  
✅ Zoho Account + OAuth credentials  
✅ OpenAI API key  

## Getting Zoho Credentials (2 minutes)

1. Go to https://api-console.zoho.in/
2. Create new Web app
3. Add redirect: `http://localhost:8000/auth/callback`
4. Copy Client ID & Secret into `.env`

## Getting OpenAI Key (1 minute)

1. Go to https://platform.openai.com/account/api-keys
2. Create new key
3. Paste into `OPENAI_API_KEY=` in `.env`

## Verify It Works

- Backend running? Check: http://localhost:8000/health
- Frontend running? Check: http://localhost:5173 opens
- Can login? Click button, Zoho redirects back
- Chat works? Try: "What projects do I have?"

## Common Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Activate venv, run `pip install -r ../requirements.txt` |
| Port 8000 in use | `lsof -i :8000` (macOS) or `netstat -ano \| findstr :8000` (Windows) |
| OAuth error | Check `.env` credentials match Zoho console |
| Frontend won't load | Clear cache (Ctrl+Shift+Delete), restart dev server |
| No database | Create with: `python -c "from zoho_client import *"` in backend dir |

## Next Steps

- Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for how it works
- Read [README.md](README.md) for features and deployment

## Environment Template

```env
ZOHO_CLIENT_ID=1000.xxxxx
ZOHO_CLIENT_SECRET=xxxxx
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback
OPENAI_API_KEY=sk-proj-xxxxx
SECRET_KEY=any-random-string-here
DATABASE_URL=sqlite:///./zoho_chatbot.db
FRONTEND_URL=http://localhost:5173
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Sample Chat Messages

```
"What projects do I have?"
"Show tasks in the Backend project"
"Create a task called API Integration"
(System asks for confirmation)
"yes"
"Who has the most tasks?"
```

---

**That's it! Happy coding! 🚀**

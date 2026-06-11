# Environment Configuration Guide

## Overview
This project uses environment variables for sensitive configuration. All credentials, API keys, and secrets are stored in `.env` files and **never committed to version control**.

## Files

### `.env` (Root Directory) - **NEVER COMMIT**
- **Location**: `/` (root of project)
- **Status**: ❌ Ignored by `.gitignore`
- **Purpose**: Stores all sensitive credentials for local development and production
- **Contains**:
  - `ZOHO_CLIENT_ID` - Zoho OAuth app client ID
  - `ZOHO_CLIENT_SECRET` - Zoho OAuth app client secret
  - `GROQ_API_KEY` - Groq LLM API key
  - `SECRET_KEY` - JWT secret key for token signing
  - `DATABASE_URL` - SQLite database path
  - Other configuration values

### `.env.example` (Root Directory) - **ALWAYS COMMIT**
- **Location**: `/` (root of project)
- **Status**: ✅ Committed to GitHub
- **Purpose**: Template showing which environment variables are required
- **Contains**: Same keys as `.env` but with empty values
- **Usage**: `cp .env.example .env` then fill in your credentials

### `zoho-project-chatbot/.env.example` (Backend Directory) - **ALWAYS COMMIT**
- **Location**: `/zoho-project-chatbot/`
- **Status**: ✅ Committed to GitHub
- **Purpose**: Backend-specific .env template
- **Note**: Root `.env` takes priority via `override=True` in config.py

## Setup Instructions

### For New Developers

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd skysecure-project
   ```

2. **Copy the example file**
   ```bash
   cp .env.example .env
   ```

3. **Fill in your credentials**
   ```bash
   # Edit .env and add your actual values:
   ZOHO_CLIENT_ID=your_client_id_here
   ZOHO_CLIENT_SECRET=your_client_secret_here
   GROQ_API_KEY=your_groq_key_here
   SECRET_KEY=your_secret_key_here
   ```

4. **Never commit `.env`**
   - `.gitignore` automatically prevents this
   - Verify: `git status` should NOT show `.env`

### Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ZOHO_CLIENT_ID` | ✅ Yes | OAuth app client ID from Zoho console |
| `ZOHO_CLIENT_SECRET` | ✅ Yes | OAuth app client secret from Zoho console |
| `GROQ_API_KEY` | ✅ Yes | API key for Groq LLM (chat capabilities) |
| `SECRET_KEY` | ✅ Yes | Strong secret for JWT token signing (generate new one for production) |
| `ZOHO_REDIRECT_URI` | No | OAuth callback URL (default: `http://localhost:8000/auth/callback`) |
| `ZOHO_ACCOUNTS_URL` | No | Zoho accounts endpoint (default: `https://accounts.zoho.in`) |
| `ZOHO_API_BASE` | No | Zoho API base URL (default: `https://projectsapi.zoho.in/restapi`) |
| `DATABASE_URL` | No | Database connection string (default: `sqlite:///./zoho_chatbot.db`) |
| `FRONTEND_URL` | No | Frontend URL for CORS (default: `http://localhost:5173`) |

## How It Works

### Configuration Loading Order (from `backend/config.py`)

```python
# 1. Load from backend directory first
load_dotenv(project_root / ".env")

# 2. Load from root directory (overrides backend)
load_dotenv(workspace_root / ".env", override=True)
```

This allows:
- Backend-specific defaults in `zoho-project-chatbot/.env`
- Root `.env` to override for shared projects
- Flexibility in multi-workspace setups

### Safe Logging

The application logs configuration at startup with secrets masked:
```
ZOHO_CLIENT_ID: 1000.ZSK...PRJCO (shows first/last 8 chars)
GROQ_API_KEY: gsk_...KVVWE (shows first/last 4 chars)
SECRET_KEY: *** (completely masked for short keys)
```

## Security Best Practices

✅ **DO:**
- Generate strong `SECRET_KEY` for production: `python -c "import secrets; print(secrets.token_hex(32))"`
- Use unique `ZOHO_CLIENT_SECRET` for each environment
- Rotate API keys regularly
- Use `.env.example` as documentation only
- Keep `.env` in `.gitignore`

❌ **DON'T:**
- Commit `.env` to version control
- Share `.env` files unencrypted
- Use same keys across environments
- Commit real API keys anywhere
- Use weak SECRET_KEY values

## GitHub/Deployment

When pushing to GitHub:
1. `.env` is automatically excluded by `.gitignore` ✅
2. `.env.example` is committed for documentation ✅
3. Environment variables set in CI/CD (GitHub Actions, Docker, etc.)

## Troubleshooting

### Missing Environment Variables

If you see errors like:
```
ZOHO_CLIENT_ID is not configured in .env
GROQ_API_KEY is not set — chat will fail
```

**Solution:**
1. Check `.env` exists: `ls -la .env`
2. Verify all required keys are filled in: `grep "^[A-Z].*=" .env`
3. Restart the application after modifying `.env`

### Changes Not Taking Effect

- **Problem**: Modified `.env` but changes not appearing
- **Solution**: Restart the backend server

```bash
# Kill existing server
Ctrl+C

# Start with reload
uvicorn backend.main:app --reload
```

## Sensitive Data Found and Secured

✅ **Credentials moved to `.env`:**
- ZOHO_CLIENT_ID
- ZOHO_CLIENT_SECRET
- GROQ_API_KEY
- SECRET_KEY
- Database URL

✅ **Configuration Files:**
- Created `/zoho-project-chatbot/.env.example` (already existed)
- Created `/.env.example` (new)
- Created `/.gitignore` (new, comprehensive)
- Updated `zoho-project-chatbot/.gitignore` (already had `.env`)

✅ **Code Implementation:**
- `backend/config.py` uses `os.getenv()` for all sensitive values
- `python-dotenv` loaded and configured
- Automatic secret masking in logs
- Multi-directory .env loading with overrides

## Verification Checklist

- [ ] `.env` file exists and is filled in
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` is committed
- [ ] Backend loads configuration without errors
- [ ] Secrets are masked in startup logs
- [ ] No hardcoded credentials in source code

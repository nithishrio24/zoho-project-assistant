# Setup Guide - Zoho Project Chatbot

This guide walks you through setting up and running the Zoho Project Chatbot application.

## 📋 Prerequisites

Before you start, ensure you have:

- **Python 3.9 or higher**: [Download Python](https://www.python.org/downloads/)
- **Node.js 16 or higher**: [Download Node.js](https://nodejs.org/)
- **Git**: [Download Git](https://git-scm.com/)
- **Zoho Account**: [Zoho Projects](https://www.zoho.com/projects/)
- **OpenAI API Key**: [OpenAI Platform](https://platform.openai.com/)

Verify installations:
```bash
python --version
node --version
npm --version
```

## 🔑 Step 1: Register Zoho OAuth Application

### 1.1 Go to Zoho Developer Console

1. Navigate to [Zoho API Console](https://api-console.zoho.in/)
2. Log in with your Zoho account (create one if needed)

### 1.2 Create a New Application

1. Click on **OAuth 2.0 Applications**
2. Select **Create Application**
3. Choose **Web-based**
4. Fill in the details:
   - **Application Name**: `Zoho Project Chatbot`
   - **Homepage URL**: `http://localhost:5173`
   - **Authorized Redirect URLs**: `http://localhost:8000/auth/callback`

### 1.3 Grant Required Scopes

When creating the application, grant these scopes:
- `ZohoProjects.portals.READ`
- `ZohoProjects.projects.CREATE`
- `ZohoProjects.projects.READ`
- `ZohoProjects.projects.UPDATE`
- `ZohoProjects.tasks.CREATE`
- `ZohoProjects.tasks.READ`
- `ZohoProjects.tasks.UPDATE`
- `ZohoProjects.tasks.DELETE`
- `ZohoProjects.users.READ`

### 1.4 Copy Credentials

After creating the application, copy:
- **Client ID**
- **Client Secret**

Keep these safe - you'll need them next.

## 🔐 Step 2: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Sign up or log in
3. Create a new API key
4. Copy the key (you won't see it again!)

## 📁 Step 3: Clone or Extract Project

If you have the project files, navigate to the root directory:

```bash
cd zoho-project-chatbot
```

## ⚙️ Step 4: Configure Environment Variables

### 4.1 Copy Example File

```bash
cp .env.example .env
```

### 4.2 Edit `.env` File

Open `.env` in your text editor and fill in:

```env
# Zoho OAuth Configuration
ZOHO_CLIENT_ID=your_client_id_from_step_1
ZOHO_CLIENT_SECRET=your_client_secret_from_step_1
ZOHO_REDIRECT_URI=http://localhost:8000/auth/callback
ZOHO_ACCOUNTS_URL=https://accounts.zoho.in
ZOHO_API_BASE=https://projectsapi.zoho.in/restapi

# OpenAI Configuration
OPENAI_API_KEY=your_api_key_from_step_2

# Security (keep these confidential)
SECRET_KEY=your-super-secret-key-change-this-to-something-random

# Database
DATABASE_URL=sqlite:///./zoho_chatbot.db

# Frontend URL
FRONTEND_URL=http://localhost:5173

# JWT Configuration
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Example with dummy values:**
```env
ZOHO_CLIENT_ID=1000.a1b2c3d4e5f6g7h8i9j0
ZOHO_CLIENT_SECRET=abc123def456ghi789jkl012mno345pqr678
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345
SECRET_KEY=my-super-secret-key-12345-change-this
```

## 🔧 Step 5: Install Backend Dependencies

### 5.1 Navigate to Backend Directory

```bash
cd backend
```

### 5.2 Create Python Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 5.3 Install Requirements

```bash
pip install -r ../requirements.txt
```

This may take a few minutes. Wait for it to complete.

### 5.4 Verify Installation

```bash
pip list
```

You should see packages like `fastapi`, `langgraph`, `langchain`, etc.

## 🚀 Step 6: Run Backend Server

While in the `backend` directory with the virtual environment activated:

```bash
uvicorn main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

✅ **Backend is running!** Keep this terminal open.

## 🎨 Step 7: Install Frontend Dependencies

Open a **new terminal** and navigate to the frontend directory:

```bash
cd frontend
npm install
```

This will install React, Vite, Axios, and other frontend dependencies. Wait for it to complete.

## 🖥️ Step 8: Run Frontend Development Server

In the frontend directory:

```bash
npm run dev
```

Expected output:
```
  VITE v5.0.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

✅ **Frontend is running!** Open your browser to `http://localhost:5173`

## 🧪 Step 9: Test the Application

### 9.1 Login

1. Click the **"Login with Zoho"** button
2. You'll be redirected to Zoho's login page
3. Enter your Zoho credentials
4. Authorize the application to access your projects
5. You'll be redirected back to the chat page

### 9.2 Try Sample Queries

Once logged in, try these messages:

**Query Examples:**
```
"What projects do I have?"
"Show me the tasks in the first project"
"Who is assigned the most tasks?"
"List all team members"
```

**Action Examples (with confirmation):**
```
"Create a task called API Integration"
"Update task #5 to high priority"
"Delete task #10"
```

## 📊 Verify Everything Works

### Backend Endpoints

Test the API directly using curl or Postman:

```bash
# Health check
curl http://localhost:8000/health

# Get user info (requires valid JWT token)
curl -H "Authorization: Bearer your_jwt_token" http://localhost:8000/me
```

### Frontend

- Check browser console (F12) for errors
- Verify network requests in DevTools Network tab
- Check backend terminal for request logs

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt
```

### Issue: "Connection refused" or "Cannot reach backend"

**Solution:**
1. Make sure backend is running on port 8000
2. Check if the port is already in use:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # macOS/Linux
   lsof -i :8000
   ```
3. Kill any process using port 8000 and restart

### Issue: OAuth callback shows error

**Solution:**
1. Verify `ZOHO_REDIRECT_URI` in `.env` matches exactly in Zoho console
2. Check that `ZOHO_CLIENT_ID` and `ZOHO_CLIENT_SECRET` are correct
3. Ensure scopes are properly configured in Zoho console

### Issue: "Invalid OpenAI API key"

**Solution:**
1. Verify your OpenAI API key is correct
2. Check that the key has not expired
3. Ensure the key has proper permissions

### Issue: Frontend won't load

**Solution:**
1. Check that `npm run dev` is running
2. Clear browser cache (Ctrl+Shift+Delete)
3. Check browser console for errors (F12)
4. Verify that port 5173 is not in use

### Issue: Database file not created

**Solution:**
1. Ensure write permissions in the backend directory
2. Manually create the database:
   ```bash
   cd backend
   python -c "from zoho_client import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

## 🔒 Security Notes

⚠️ **For Development Only**

These settings are for local development. **Do NOT use in production:**

- Change `SECRET_KEY` to a random string
- Use environment-specific configuration
- Enable HTTPS/TLS
- Use environment variables instead of `.env` files
- Implement rate limiting
- Use a production database (PostgreSQL)
- Add request logging and monitoring

## 📚 API Documentation

Once the backend is running, view the API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🛑 Stopping the Application

To stop either server:

Press `Ctrl+C` in the respective terminal

## 🔄 Restarting

To restart fresh:

1. Stop both servers (Ctrl+C)
2. Delete `zoho_chatbot.db` to clear database
3. Start backend: `uvicorn main:app --reload --port 8000`
4. Start frontend: `npm run dev`

## 📦 Production Deployment

For deploying to production, see the main README.md for:
- Docker containerization
- Cloud deployment (AWS, GCP)
- Database migration (PostgreSQL)
- Performance optimization
- Monitoring and logging

## 🆘 Getting Help

1. Check the [main README.md](README.md) for more information
2. Review error messages in browser console and backend terminal
3. Check Zoho API documentation: https://www.zoho.com/projects/rest-api/
4. Check LangGraph docs: https://langchain-ai.github.io/langgraph/

## ✅ Checklist

Before considering setup complete, verify:

- [ ] Python virtual environment created and activated
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] `.env` file configured with all required values
- [ ] Zoho OAuth application created
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Successfully logged in with Zoho account
- [ ] Sent a test message and received a response
- [ ] Database file created (`zoho_chatbot.db`)

🎉 **Congratulations!** Your Zoho Project Chatbot is now running!

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings, log_startup_config
from backend.portal_utils import resolve_portal_slug
from backend.models import ChatRequest, ChatResponse
from backend.auth.zoho_oauth import ZohoOAuthManager
from backend.memory.memory_store import MemoryStore
from backend.zoho_client import ensure_db_tables

from langchain_core.messages import HumanMessage, AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session_states: Dict[str, Dict[str, Any]] = {}


async def get_current_user(request: Request) -> str:
    """Extract and verify user from JWT Bearer token."""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Send: Authorization: Bearer <token>",
        )

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header. Expected format: Bearer <token>",
        )

    token = auth_header[len("Bearer "):].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token is empty")

    payload, error = ZohoOAuthManager.verify_jwt_token(token)
    if error:
        logger.warning(f"JWT verification failed: {error}")
        raise HTTPException(status_code=401, detail=error)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token valid but missing user_id (sub claim)")

    logger.debug(f"Authenticated user: {user_id}")
    return str(user_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Zoho Project Chatbot")
    log_startup_config()

    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY is not set — chat will fail. Add it to .env")
    else:
        try:
            from backend.llm.groq_llm import get_chat_model
            llm = get_chat_model()
            logger.info(f"Groq LLM ready: model={llm.model_name}")
        except Exception as e:
            logger.error(f"Groq LLM init failed: {e}")

    await ensure_db_tables()
    logger.info("Database tables ready")
    
    # Print all registered routes
    logger.info("=" * 50)
    logger.info("REGISTERED ROUTES:")
    logger.info("=" * 50)
    for route in app.routes:
        methods = ", ".join(route.methods) if hasattr(route, 'methods') else "N/A"
        path = route.path if hasattr(route, 'path') else "N/A"
        logger.info(f"  {path:30} [{methods}]")
    logger.info("=" * 50)
    
    logger.info(f"Server ready — frontend: {settings.frontend_url}")
    yield
    logger.info("Shutting down Zoho Project Chatbot")


app = FastAPI(
    title="Zoho Project Chatbot",
    description="AI-powered chatbot for Zoho Projects",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return RedirectResponse(url=settings.frontend_url)


@app.get("/auth/test")
async def auth_test():
    """No auth required — verify the server is reachable."""
    return {"status": "ok"}


@app.get("/auth/debug")
async def auth_debug():
    """Debug endpoint to verify OAuth configuration."""
    return {
        "frontend_url": settings.frontend_url,
        "redirect_uri": settings.zoho_redirect_uri,
        "client_id_set": bool(settings.zoho_client_id),
        "client_secret_set": bool(settings.zoho_client_secret),
        "authorization_url_sample": ZohoOAuthManager.get_authorization_url()[:100] + "...",
    }


@app.get("/auth/login")
async def login():
    try:
        auth_url = ZohoOAuthManager.get_authorization_url()
        return RedirectResponse(url=auth_url)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/callback")
async def callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handle OAuth callback, issue JWT, redirect to frontend with ?token=xxx."""
    if error:
        raise HTTPException(status_code=400, detail=f"Zoho OAuth error: {error}")

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing authorization code. OAuth callback must include ?code=...",
        )

    try:
        # Step 1: Exchange code for Zoho tokens
        logger.info("OAuth callback: exchanging code for tokens")
        tokens_data = await ZohoOAuthManager.exchange_code_for_tokens(code)
        access_token = tokens_data["access_token"]
        logger.info(f"OAuth callback: got access token (length={len(access_token)})")

        # Step 2: Fetch user info from Zoho
        logger.info("OAuth callback: fetching user info with access token")
        user_info = await ZohoOAuthManager.get_user_info(access_token)
        logger.info(f"OAuth callback: user info received: {list(user_info.keys())}")
        
        parsed = ZohoOAuthManager.parse_user_info(user_info)
        user_id = parsed["user_id"]
        email = parsed["email"]
        logger.info(f"OAuth callback: parsed user_id={user_id}, email={email}")

        if not user_id:
            raise ValueError(
                f"Could not extract user ID from Zoho response. "
                f"Fields received: {list(user_info.keys())}"
            )

        # Step 3: Persist Zoho tokens
        logger.info(f"OAuth callback: storing tokens for user {user_id}")
        await ZohoOAuthManager.store_tokens(user_id, tokens_data)

        # Step 4: Create JWT for frontend session
        logger.info(f"OAuth callback: creating JWT token for user {user_id}")
        jwt_token = ZohoOAuthManager.create_jwt_token(user_id, email)
        if not jwt_token:
            raise ValueError("JWT token generation returned empty string")

        logger.info(f"OAuth callback: JWT created for user {user_id} (length={len(jwt_token)})")

        # Step 5: Initialize long-term memory
        logger.info(f"OAuth callback: loading memory for user {user_id}")
        memory_store = MemoryStore()
        await memory_store.load_memory(user_id)

        # Step 6: Redirect to http://localhost:5173?token=xxx
        logger.info(f"OAuth callback: building redirect URL")
        redirect_url = ZohoOAuthManager.build_frontend_redirect(jwt_token)
        logger.info(f"OAuth callback: redirecting to {settings.frontend_url}?token=<masked>")
        logger.info(f"Full redirect URL: {redirect_url[:100]}...")
        return RedirectResponse(url=redirect_url, status_code=302, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"OAuth callback validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")
    except RuntimeError as e:
        logger.error(f"OAuth callback Zoho API error: {e}")
        raise HTTPException(status_code=502, detail=f"Authentication failed: {e}")
    except Exception as e:
        logger.error(f"OAuth callback unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {type(e).__name__}: {e}",
        )


@app.get("/me")
async def get_user_info(current_user: str = Depends(get_current_user)):
    return {"user_id": current_user}


@app.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
) -> ChatResponse:
    """Process user message. Requires valid JWT in Authorization header."""
    try:
        session_id = request.session_id
        user_message = request.user_message

        logger.info(f"Chat request from user_id={current_user}, session={session_id}")

        if session_id not in session_states:
            memory_store = MemoryStore()
            long_term_memory = await memory_store.load_memory(current_user)

            session_states[session_id] = {
                "messages": [],
                "user_id": current_user,
                "current_agent": "router",
                "pending_action": None,
                "awaiting_confirmation": False,
                "session_context": {
                    "last_project_id": long_term_memory.get("last_active_project"),
                    "last_project_name": long_term_memory.get("last_active_project_name"),
                    "last_portal_id": long_term_memory.get("last_active_portal"),
                    "portal_name": resolve_portal_slug(
                        long_term_memory.get("last_active_portal"),
                        long_term_memory.get("last_active_portal_name"),
                    ),
                },
                "long_term_memory": long_term_memory,
            }

        state = session_states[session_id]
        state["messages"].append(HumanMessage(content=user_message))

        from backend.tools.zoho_tools import create_tools
        from backend.agents.router import router_node
        from backend.agents.query_agent import query_agent_node_wrapper
        from backend.agents.action_agent import action_agent_node
        from backend.agents.confirm_handler import confirm_handler_node

        tools = create_tools(current_user)

        if state.get("awaiting_confirmation"):
            state = await confirm_handler_node(state, tools)
        else:
            state = await router_node(state)
            current_agent = state.get("current_agent", "query")

            if current_agent == "query":
                state = await query_agent_node_wrapper(state, {"tools": tools})
            elif current_agent == "action":
                state = await action_agent_node(state, tools)

        response_text = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage):
                response_text = msg.content
                break

        session_states[session_id] = state

        memory_store = MemoryStore()
        await memory_store.save_memory(current_user, state["long_term_memory"])

        return ChatResponse(
            response=response_text,
            awaiting_confirmation=state.get("awaiting_confirmation", False),
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/test-portal")
async def test_portal(current_user: str = Depends(get_current_user)):
    """Debug endpoint to test both /portal/ and /portals/ endpoints and return raw responses."""
    from backend.zoho_client import ZohoClient
    import httpx
    
    client = ZohoClient(current_user)
    token = await client._get_valid_token()
    
    results = {
        "user_id": current_user,
        "token_prefix": token[:20] + "..." if token else None,
        "base_url": client.base_url,
    }
    
    # Test /portal/ endpoint
    try:
        headers = {"Authorization": f"Zoho-oauthtoken {token}", "Accept": "application/json"}
        url = f"{client.base_url}/portal/"
        logger.info(f"Testing /portal/ endpoint: {url}")
        
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(url, headers=headers, timeout=30.0)
            results["portal_endpoint"] = {
                "url": url,
                "status_code": resp.status_code,
                "reason_phrase": resp.reason_phrase,
                "headers": dict(resp.headers),
                "body": resp.text[:5000] if resp.text else "",
                "body_length": len(resp.text),
            }
            logger.info(f"/portal/ response: status={resp.status_code}, body_length={len(resp.text)}")
    except Exception as e:
        results["portal_endpoint"] = {"error": str(e)}
        logger.error(f"/portal/ error: {str(e)}")
    
    # Test /portals/ endpoint
    try:
        headers = {"Authorization": f"Zoho-oauthtoken {token}", "Accept": "application/json"}
        url = f"{client.base_url}/portals/"
        logger.info(f"Testing /portals/ endpoint: {url}")
        
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(url, headers=headers, timeout=30.0)
            results["portals_endpoint"] = {
                "url": url,
                "status_code": resp.status_code,
                "reason_phrase": resp.reason_phrase,
                "headers": dict(resp.headers),
                "body": resp.text[:5000] if resp.text else "",
                "body_length": len(resp.text),
            }
            logger.info(f"/portals/ response: status={resp.status_code}, body_length={len(resp.text)}")
    except Exception as e:
        results["portals_endpoint"] = {"error": str(e)}
        logger.error(f"/portals/ error: {str(e)}")
    
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

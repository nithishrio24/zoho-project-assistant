"""Groq ChatGroq helper for agents."""

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from backend.config import settings


def get_chat_model() -> ChatGroq:
    """Return a configured ChatGroq instance (llama-3.1-8b-instant by default)."""
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment or settings")
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
    )


def invoke_prompt(prompt: str) -> str:
    """Send a single prompt string to ChatGroq and return the text response."""
    llm = get_chat_model()
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    return content if isinstance(content, str) else str(content)

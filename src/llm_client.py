"""Groq LLM client for question generation and answer evaluation."""
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

_client = None
DEFAULT_MODEL = "qwen/qwen3.8-27b"


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        _client = Groq(api_key=api_key)
    return _client


def chat(prompt: str, system: str = None, model: str = None, max_tokens: int = 600) -> str:
    """Send a prompt to Groq and return the response text."""
    if model is None:
        model = DEFAULT_MODEL

    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    if content is None:
        content = ""
    return content.strip()

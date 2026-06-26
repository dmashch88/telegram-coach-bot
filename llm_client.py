import json
import requests
import asyncio
from config import OLLAMA_HOST, OLLAMA_MODEL

async def generate_response(prompt: str, system_prompt: str = "") -> str:
    """
    Асинхронный вызов Ollama с таймаутом 30 секунд.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "temperature": 0.8,
        "max_tokens": 150
    }
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(url, json=payload, timeout=30)
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "").strip()
        else:
            return ""
    except Exception as e:
        print(f"Ollama error: {e}")
        return ""

import aiohttp
import asyncio
import json
from config import OLLAMA_HOST, OLLAMA_MODEL

async def generate_response(prompt: str, system_prompt: str = None) -> str:
    """Асинхронный вызов Ollama для генерации текста."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "system": system_prompt or "Ты добрый и вдохновляющий коуч."
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "").strip()
                else:
                    return None
    except Exception as e:
        return None
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
MORNING_TIME = os.getenv("MORNING_TIME", "08:00")
EVENING_TIME = os.getenv("EVENING_TIME", "20:00")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

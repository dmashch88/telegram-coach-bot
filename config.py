import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Окна (по локальному времени пользователя)
MORNING_START = 6
MORNING_END = 9
EVENING_START = 21
EVENING_END = 24

# Юбилейные дни и повторения
STATS_DAY_1 = 8
STATS_DAY_2 = 21
STATS_REPEAT_GOAL = 100

DEFAULT_TIMEZONE = "UTC"
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "f2af5ac8f8msh70dddc1bbab9d35p127a5cjsna93739173f0d")
AGRI_NEWS_API_KEY = os.getenv("AGRI_NEWS_API_KEY")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

import os
from dotenv import load_dotenv

# Load .env file
# Load .env file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

class Config:
    # OpenAI/Gemini Config (from .env)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Vertex AI Config
    # Default to None if not found, or relative path if exists
    VERTEX_CREDENTIALS_PATH = os.getenv("VERTEX_CREDENTIALS_PATH") or os.path.join(BASE_DIR, "sys_init", "vertex-credentials.json")
    VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID") or ""
    VERTEX_LOCATION = "us-central1" # Default assumption, can be adjusted if needed
    
    # Models
    # User requested strictly gemini-2.5-pro
    GEMINI_MODEL_PRIMARY = os.getenv("GEMINI_MODEL", "gemini-2.5-pro") 
    GEMINI_MODEL_FALLBACK = "gemini-2.5-flash" # Fallback also locked to 2.5 as requested
    VERTEX_MODEL_FALLBACK = "gemini-2.5-pro" 

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TASKS_DIR = os.path.join(BASE_DIR, "tasks")


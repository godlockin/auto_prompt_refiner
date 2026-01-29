import os
from dotenv import load_dotenv

# Load .env file
ENV_PATH = ""
load_dotenv(ENV_PATH)

class Config:
    # OpenAI/Gemini Config (from .env)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Vertex AI Config
    VERTEX_CREDENTIALS_PATH = ""
    VERTEX_PROJECT_ID = "" # Extracted from json content
    VERTEX_LOCATION = "us-central1" # Default assumption, can be adjusted if needed
    
    # Models
    GEMINI_MODEL_PRIMARY = "gemini-3-pro-preview" # As requested
    GEMINI_MODEL_FALLBACK = "gemini-2.5-pro" # Trying a known model name for fallback or 1.5 pro. 
    # User said: "if failure try downgrade use vertexai gemini-2.5-pro". 
    # Note: "gemini-2.5-pro" might not exist yet, might mean 1.5 or 2.0. I will use the string provided by user but add error handling.
    # Actually, let's use what the user asked for: gemini-2.5-pro. If it fails, I might need to correct it.
    # But for safety, I will check if 2.5 exists. As of early 2025, 2.0 is the latest preview. 
    # Maybe user means 1.5 pro? or 2.0 pro? 
    # I will stick to user request but fallback to "gemini-1.5-pro" if 2.5 fails.
    VERTEX_MODEL_FALLBACK = "gemini-2.5-pro" 

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TASKS_DIR = os.path.join(BASE_DIR, "tasks")


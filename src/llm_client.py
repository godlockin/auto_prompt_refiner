import os
import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
from src.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.primary_broken = False  # Circuit breaker
        self.setup_primary()
        self.setup_fallback()

    def setup_primary(self):
        try:
            if Config.GOOGLE_API_KEY:
                genai.configure(api_key=Config.GOOGLE_API_KEY)
                self.primary_model = genai.GenerativeModel(Config.GEMINI_MODEL_PRIMARY)
                logger.info(f"Primary model setup: {Config.GEMINI_MODEL_PRIMARY}")
            else:
                logger.warning("GOOGLE_API_KEY not found. Primary model disabled.")
                self.primary_model = None
                self.primary_broken = True
        except Exception as e:
            logger.error(f"Failed to setup primary model: {e}")
            self.primary_model = None
            self.primary_broken = True

    def setup_fallback(self):
        try:
            if os.path.exists(Config.VERTEX_CREDENTIALS_PATH):
                credentials = service_account.Credentials.from_service_account_file(Config.VERTEX_CREDENTIALS_PATH)
                vertexai.init(project=Config.VERTEX_PROJECT_ID, location=Config.VERTEX_LOCATION, credentials=credentials)
                # Note: "gemini-2.5-pro" might be invalid. If it fails at runtime, we might need to handle it.
                # For now we just initialize the object.
                self.fallback_model_name = Config.VERTEX_MODEL_FALLBACK
                logger.info(f"Fallback model setup: {self.fallback_model_name}")
            else:
                logger.warning(f"Vertex credentials not found at {Config.VERTEX_CREDENTIALS_PATH}. Fallback model disabled.")
                self.fallback_model_name = None
        except Exception as e:
            logger.error(f"Failed to setup fallback model: {e}")
            self.fallback_model_name = None

    def generate_content(self, prompt: str) -> str:
        """
        Generates content using primary model, falls back to secondary if it fails.
        """
        # Try Primary
        if self.primary_model and not self.primary_broken:
            try:
                logger.info("Attempting generation with Primary Model...")
                response = self.primary_model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Primary model failed: {e}")
                logger.info("Switching to Fallback Model...")
                self.primary_broken = True # Trip the circuit breaker
        
        # Try Fallback
        if self.fallback_model_name:
            try:
                # Vertex AI instantiation happens here to handle model name errors gracefully
                model = GenerativeModel(self.fallback_model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Fallback model failed: {e}")
                
                # Double Fallback: Try a known stable model if 2.5 fails (e.g., gemini-1.5-pro)
                try:
                    logger.info("Attempting generation with Emergency Backup (gemini-1.5-pro-001)...")
                    model = GenerativeModel("gemini-1.5-pro-001")
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as e2:
                    logger.error(f"Emergency backup failed: {e2}")
                    return f"Error: All models failed. Primary Error: {e}\nFallback Error: {e2}"

        return "Error: No models available or configured correctly."


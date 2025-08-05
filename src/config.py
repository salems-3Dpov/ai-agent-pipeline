import os
from dotenv import load_dotenv
import warnings
import logging

logging.getLogger("torch").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*Tried to instantiate class '__path__._path'.*")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

load_dotenv()

class Config:
    """Configuration class for the AI pipeline application."""
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "ai-pipeline-demo")
    
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_documents")
    
    WEATHER_API_BASE_URL = os.getenv("WEATHER_API_BASE_URL", "http://api.openweathermap.org/data/2.5/weather")
    
    @classmethod
    def validate_config(cls, required_services=None):
        """Validate that all required configuration values are present."""
        if required_services is None:
            required_services = ["openai"]
            
        required_keys = []
        
        if "openai" in required_services:
            required_keys.append("OPENAI_API_KEY")
            
        if "weather" in required_services and cls.OPENWEATHERMAP_API_KEY:
            required_keys.append("OPENWEATHERMAP_API_KEY")
        
        if cls.LANGCHAIN_TRACING_V2 and "langchain" in required_services:
            required_keys.append("LANGCHAIN_API_KEY")
        
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            error_msg = f"Missing required environment variables: {', '.join(missing_keys)}\n"
            error_msg += "Please set these in your .env file or environment variables:\n"
            for key in missing_keys:
                error_msg += f"- {key}\n"
            raise ValueError(error_msg)
        
        return True
# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Central configuration for the Telecom Assistant"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Model Configurations
    LLM_MODEL = "gpt-4o"  # or "gpt-3.5-turbo" if you want to save cost
    FAST_LLM_MODEL = "gpt-3.5-turbo"
    
    # File Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DB_PATH = os.path.join(DATA_DIR, "telecom.db")
    DOCS_DIR = os.path.join(DATA_DIR, "documents")
    VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")

    # Validate setup
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        if not os.path.exists(cls.DB_PATH):
            raise FileNotFoundError(f"Database not found at {cls.DB_PATH}")
        if not os.path.exists(cls.DOCS_DIR):
            raise FileNotFoundError(f"Documents folder not found at {cls.DOCS_DIR}")

try:
    Config.validate()
except Exception as e:
    print(f"Warning: Configuration issue - {e}")
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
BACKEND_DIR = Path(__file__).parent
ENV_FILE = BACKEND_DIR / '.env'
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "PaperAI"
    
    # MongoDB (keeping existing for user data if needed)
    MONGO_URL: str
    DB_NAME: str
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "paperai123"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Gemini API
    GEMINI_API_KEY: str
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    LLM_MODEL: str = "gemini-2.0-flash-exp"
    
    # Processing Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CONTEXT_TOKENS: int = 8000
    EMBEDDING_DIMENSION: int = 768
    
    # Storage Configuration
    PDF_STORAGE_PATH: str = "./storage/pdfs"
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True


settings = Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Determine env file: prefer .env, fallback to env.txt (to match your provided file)
BACKEND_DIR = Path(__file__).parent
_env_candidates = [BACKEND_DIR / '.env', BACKEND_DIR / 'env.txt']
ENV_FILE = next((p for p in _env_candidates if p.exists()), _env_candidates[0])


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "PaperAI"
    
    # MongoDB (keeping existing for user data if needed)
    MONGO_URL: str
    DB_NAME: str
    
    # Neo4j Configuration
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "neo4j"
    
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
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
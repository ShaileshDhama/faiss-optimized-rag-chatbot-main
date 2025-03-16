from pydantic_settings import BaseSettings
from typing import Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FinGenius - Your AI CFO"
    PROJECT_DESCRIPTION: str = "Smart Money, Smarter Decisions with FinGenius AI"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "fingenius")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # LLM Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MODEL_NAME: str = "llama2"
    
    # FAISS
    FAISS_INDEX_PATH: str = "data/fingenius_index.faiss"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    
    # Branding
    BRAND_NAME: str = "FinGenius"
    BRAND_TAGLINE: str = "Smart Money, Smarter Decisions"
    BRAND_DESCRIPTION: str = """
    FinGenius is your AI-powered financial assistant, combining advanced market analysis 
    with intelligent conversation to help you make smarter financial decisions.
    """
    TARGET_AUDIENCE: list = [
        "Retail Investors",
        "Finance Professionals",
        "Stock Market Traders",
        "Businesses & CFOs"
    ]
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

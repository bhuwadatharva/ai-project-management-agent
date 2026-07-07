import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # LangSmith / LangChain Tracking
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_TRACING_V2: str = "false"
    LANGSMITH_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./devpilot.db"
    
    # Supabase (Optional)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    
    # AI Models
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-4o-mini"
    
    # API Settings
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "DevPilot AI"
    
    # Configuration load rules
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Gemini AI Configuration (New Gen AI SDK)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Weaviate Configuration
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY", "")
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    
    # AssemblyAI Configuration
    ASSEMBLYAI_API_KEY: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # File Storage
    MEDIA_STORAGE_PATH: str = os.getenv("MEDIA_STORAGE_PATH", "./storage/media")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50000000"))  # 50MB
    
    # AI Processing (Enhanced for Gemini 2.5 Pro)
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "2000000"))  # 2M tokens with Gemini 2.5 Pro
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.35"))
    TOP_P: float = float(os.getenv("TOP_P", "0.95"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "8192"))
    
    # Model Configuration (Updated for Gemini 2.5 Pro)
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-2.5-pro-experimental")
    LONG_CONTEXT_MODEL: str = os.getenv("LONG_CONTEXT_MODEL", "gemini-2.5-pro-experimental")  # Enhanced reasoning for long context
    THINKING_MODEL: bool = os.getenv("THINKING_MODEL", "true").lower() == "true"  # Enable step-by-step thinking
    
    # Memory Management (Enhanced for Gemini 2.5 Pro's capabilities)
    LRU_CACHE_SIZE: int = int(os.getenv("LRU_CACHE_SIZE", "3000"))  # Increased for Gemini 2.5 Pro's enhanced processing
    VECTOR_SEARCH_LIMIT: int = int(os.getenv("VECTOR_SEARCH_LIMIT", "20"))  # More context for advanced reasoning
    GRAPH_TRAVERSE_DEPTH: int = int(os.getenv("GRAPH_TRAVERSE_DEPTH", "4"))  # Deeper reasoning paths
    CONTEXT_MEMORY_LIMIT: int = int(os.getenv("CONTEXT_MEMORY_LIMIT", "50"))  # Leverage 2M token context window
    
    # Advanced Multimodal Processing (Gemini 2.5 Pro capabilities)
    ENABLE_VIDEO_PROCESSING: bool = os.getenv("ENABLE_VIDEO_PROCESSING", "true").lower() == "true"
    ENABLE_AUDIO_NATIVE: bool = os.getenv("ENABLE_AUDIO_NATIVE", "true").lower() == "true"
    ENABLE_LONG_CONTEXT: bool = os.getenv("ENABLE_LONG_CONTEXT", "true").lower() == "true"
    ENABLE_ADVANCED_REASONING: bool = os.getenv("ENABLE_ADVANCED_REASONING", "true").lower() == "true"
    ENABLE_CODE_GENERATION: bool = os.getenv("ENABLE_CODE_GENERATION", "true").lower() == "true"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Webhook Configuration
    WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 
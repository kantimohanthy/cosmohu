import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CosmoHub Intelligence Engine"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Storage settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://cosmohub:cosmohub_secret@localhost:5432/cosmohub_db"
    )
    SQLITE_FALLBACK_DB: str = os.getenv("SQLITE_FALLBACK_DB", "cosmohub_local.db")
    
    # Ingestion & Chunking defaults
    DEFAULT_CHUNK_SIZE_TOKENS: int = int(os.getenv("DEFAULT_CHUNK_SIZE_TOKENS", "800"))
    DEFAULT_CHUNK_OVERLAP_TOKENS: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP_TOKENS", "100"))
    MAX_CRAWL_RESPONSE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    CRAWL_TIMEOUT_SECONDS: int = 15
    
    # Embeddings & LLM
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")  # 'openai', 'local'
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSION: int = 384  # Baseline for local vectorizer / 1536 for OpenAI
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Reranker
    RERANKER_TOP_K: int = 5
    RETRIEVAL_TOP_K: int = 20
    
    # SSRF Protection Blocklist
    BLOCKED_IP_RANGES: list = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "::1/128",
        "fc00::/7",
    ]
    BLOCKED_HOSTNAMES: list = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "metadata.google.internal",
        "169.254.169.254"
    ]

settings = Settings()

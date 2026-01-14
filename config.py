"""
Configuration management for Clinical Document Intelligence Agent.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # GCP Configuration
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"
    gcp_location: str = "us-central1"
    
    # Vertex AI Configuration
    vertex_model: str = "gemini-2.0-flash"
    vertex_embedding_model: str = "text-embedding-004"
    vertex_temperature: float = 0.1
    vertex_max_tokens: int = 2048
    
    # Storage Paths
    faiss_index_path: str = "data/faiss_index"
    upload_dir: str = "data/uploads"
    eval_datasets_dir: str = "data/eval_datasets"
    audit_logs_dir: str = "data/audit_logs"
    
    # Safety Configuration
    grounding_threshold: float = 0.7
    confidence_threshold: float = 0.6
    max_prompt_injection_score: float = 0.8
    
    # RAG Configuration
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 5
    
    # MCP Server Configuration
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 50051
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Evaluation Configuration
    eval_batch_size: int = 10
    eval_synthetic_samples: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def ensure_directories(self):
        """Create necessary data directories if they don't exist."""
        directories = [
            self.faiss_index_path,
            self.upload_dir,
            self.eval_datasets_dir,
            self.audit_logs_dir,
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings

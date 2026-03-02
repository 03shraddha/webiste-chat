from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent  # backend/


class Settings(BaseSettings):
    xai_api_key: str
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-3-mini"
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "models/gemini-2.0-flash"
    chromadb_path: str = str(BASE_DIR / "data" / "chromadb")
    max_pages_default: int = 50
    max_depth_default: int = 3
    chunk_size: int = 500
    chunk_overlap: int = 100
    top_k_chunks: int = 5
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = str(BASE_DIR / ".env")


settings = Settings()
